"""Independent synthetic rejection probes; no monograph science or approval."""
from __future__ import annotations

import contextlib
import copy
from hashlib import sha256
import io
import json
from pathlib import Path
import sys
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SUBJECT = HERE / "subject-v2"
sys.path.insert(0, str(SUBJECT))
import checkpoint_lib as lib  # noqa: E402
import run_clean_replay as replay  # noqa: E402
from test_checkpoint import GateTests, dump  # noqa: E402


def accepted(call):
    try:
        result = call()
    except Exception as exc:
        return {"accepted": False, "exception": type(exc).__name__, "reason": str(exc)}
    return {"accepted": True, "result": result}


def main():
    observations = []
    pairs = [
        ("underflow", '{"signal":1e-999}', '{"signal":0.0}'),
        ("near_one", '{"signal":1.0000000000000001}', '{"signal":1.0}'),
        ("binary64_integer_boundary", '{"signal":9007199254740993.0}',
         '{"signal":9007199254740992.0}'),
        ("boolean_integer", '{"signal":true}', '{"signal":1}'),
        ("string_number", '{"signal":"1"}', '{"signal":1}'),
        ("integer_float", '{"signal":1}', '{"signal":1.0}'),
        ("large_integer_exact", '{"signal":9007199254740993}',
         '{"signal":9007199254740992}'),
    ]
    for name, first, second in pairs:
        outcome = accepted(lambda: lib.strict_equal(lib.parse_json(first), lib.parse_json(second), []))
        observations.append({"id": "json_" + name, "input_a": first, "input_b": second,
                             "expected_acceptance": False, **outcome})

    case = GateTests()
    case.setUp()
    try:
        baseline, spec, reference, candidate = case.fixture(graph_mode="no_entry_point")
        def report_pair(first, second, raw=False):
            a, b = copy.deepcopy(reference), copy.deepcopy(candidate)
            a["independent_scientific_signal"] = first
            b["independent_scientific_signal"] = second
            if raw:
                a = lib.parse_json(json.dumps(a).replace(json.dumps(first), first))
                b = lib.parse_json(json.dumps(b).replace(json.dumps(second), second))
            return a, b
        for name, first, second, raw in [
            ("raw_underflow", "1e-999", "0.0", True),
            ("raw_rounding", "1.0000000000000001", "1.0", True),
            ("string_tiny_positive", "1e-999", "0", False),
            ("boolean_integer", True, 1, False),
            ("string_number", "1", 1, False),
        ]:
            with patch.object(lib, "BASELINE", baseline):
                outcome = accepted(lambda: lib.finite_comparison(*report_pair(first, second, raw), spec))
            if "result" in outcome:
                outcome["result"] = {key: outcome["result"][key] for key in
                                     ("identical_scientific_payload", "excluded_exact_JSON_pointers")}
            observations.append({"id": "report_" + name, "expected_acceptance": False, **outcome})

        wrong_flag = copy.deepcopy(candidate)
        for stage in ("source_before", "source_after"):
            wrong_flag[stage]["live_manuscript_observation"][0]["matches_accepted_snapshot"] = False
        with patch.object(lib, "BASELINE", baseline):
            outcome = accepted(lambda: lib.finite_comparison(reference, wrong_flag, spec))
        observations.append({"id": "forged_manuscript_match", "expected_acceptance": False, **outcome})

        # Independent 46-row schema controls, including otherwise valid stage
        # metadata, so rejection cannot hide behind a wrong Git stage.
        for name in ("missing_row", "reordered_rows", "extra_field", "inactive_hash"):
            bad = copy.deepcopy(candidate)
            for stage in ("source_before", "source_after"):
                rows = bad[stage]["live_tex_source_observations"]
                if name == "missing_row":
                    rows.pop()
                elif name == "reordered_rows":
                    rows[0], rows[1] = rows[1], rows[0]
                elif name == "extra_field":
                    rows[0]["invented_metadata"] = True
                else:
                    next(row for row in rows if "inactive0" in row["path"])["sha256"] = "a" * 64
            with patch.object(lib, "BASELINE", baseline):
                outcome = accepted(lambda: lib.finite_comparison(reference, bad, spec))
            observations.append({"id": "tex_rows_" + name, "expected_acceptance": False, **outcome})

        inactive = "book/figures/inactive0.tex"
        bad_spec = copy.deepcopy(spec)
        bad_spec["reference_tex_observation_sha256"] = dict(spec["reference_tex_observation_sha256"])
        bad_spec["allowed_tex_observation_changes"] = [inactive]
        bad_spec["reference_tex_observation_sha256"][inactive] = "a" * 64
        # Even putting it in the alleged approved source map cannot turn an
        # inactive file into an active-source metadata exception.
        bad_spec["approved_source_sha256"][inactive] = spec["tex_observation_sha256"][inactive]
        with patch.object(lib, "BASELINE", baseline):
            outcome = accepted(lambda: lib.ready_spec(bad_spec))
        observations.append({"id": "inactive_exception_with_claimed_approval", "expected_acceptance": False, **outcome})

        active = "book/input0.tex"
        positive_spec = copy.deepcopy(spec)
        positive_spec["reference_tex_observation_sha256"] = dict(spec["reference_tex_observation_sha256"])
        positive_spec["reference_manuscript_sha256"] = dict(spec["reference_manuscript_sha256"])
        positive_spec["allowed_tex_observation_changes"] = [active]
        positive_spec["allowed_manuscript_changes"] = [active]
        positive_spec["reference_tex_observation_sha256"][active] = "b" * 64
        positive_spec["reference_manuscript_sha256"][active] = "b" * 64
        positive_reference, positive_candidate = copy.deepcopy(reference), copy.deepcopy(candidate)
        for report, is_reference in ((positive_reference, True), (positive_candidate, False)):
            report["fixture"]["accepted_manuscript_sha256"][active] = "b" * 64
            for stage in ("source_before", "source_after"):
                row = report[stage]["live_manuscript_observation"][0]
                row["accepted_contract_source_sha256"] = "b" * 64
                row["current_sha256"] = "b" * 64 if is_reference else spec["manuscript_observation_sha256"][active]
                row["matches_accepted_snapshot"] = is_reference
                if is_reference:
                    next(row for row in report[stage]["live_tex_source_observations"]
                         if row["path"] == active)["sha256"] = "b" * 64
        with patch.object(lib, "BASELINE", baseline):
            outcome = accepted(lambda: lib.finite_comparison(positive_reference, positive_candidate, positive_spec))
        if outcome["accepted"]:
            pointers = outcome["result"]["excluded_exact_JSON_pointers"]
            extra = [p for p in pointers if "/live_tex_source_observations/" in p]
            expected_indices = [i for i, row in enumerate(positive_reference["source_before"]["live_tex_source_observations"])
                                if row["path"] == active]
            expected = {f"/{stage}/live_tex_source_observations/{expected_indices[0]}/sha256"
                        for stage in ("source_before", "source_after")}
            if set(extra) != expected or len(pointers) != 14:
                raise RuntimeError("TeX comparison excludes more than the exact two changed hash fields")
            outcome["result"] = {"excluded_exact_JSON_pointers": pointers,
                                 "only_two_individual_tex_hash_exclusions": True}
        observations.append({"id": "approved_active_tex_delta_exact_fields", "expected_acceptance": True, **outcome})

        escape = case.outer / "outside-link"
        escape.symlink_to(case.root, target_is_directory=True)
        outcome = accepted(lambda: lib.outer_path(case.outer, "outside-link/result.json"))
        observations.append({"id": "symlink_outer_escape", "expected_acceptance": False, **outcome})
        escape.unlink()

        # The intentionally unconnected synthetic fixture has 36 unrelated .tex files
        # and no manuscript entry point. A complete-graph guard must reject it.
        if (case.root / "book/main.tex").exists():
            raise RuntimeError("Independent graph probe requires absent entry point")
        dump(case.outer / "control.json", {"mode": "success"})
        receipt = case.outer / "graph-probe-receipt.json"
        argv = [str(SUBJECT / "run_clean_replay.py"), "--spec", str(case.outer / "spec.json"),
                "--receipt", str(receipt)]
        with patch.object(lib, "BASELINE", baseline), patch.object(sys, "argv", argv), \
                contextlib.redirect_stdout(io.StringIO()):
            outcome = accepted(replay.main)
        receipt_data = lib.parse_json(receipt.read_bytes())
        receipt_name = ("unconnected-graph-command-receipt-optimized.json" if sys.flags.optimize
                        else "unconnected-graph-command-receipt-normal.json")
        with (HERE / receipt_name).open("xb") as handle:
            handle.write(receipt.read_bytes())
        observations.append({"id": "unconnected_36_files_without_entry_point",
                             "expected_acceptance": False,
                             "recorded_TeX_input_count": len(spec["tex_input_sha256"]),
                             "book_main_exists": False, "command_executed": receipt_data["command_executed"],
                             "receipt_checks_passed": receipt_data["checks_passed"], **outcome})
    finally:
        case.tearDown()

    for name, left, right, expected in [
        ("representable_subnormal", "5e-324", "5e-324", True),
        ("lossy_subnormal", "6e-324", "5e-324", False),
        ("decimal_formatting_same_value", "0.1000", "1e-1", True),
        ("negative_underflow", "-1e-999", "-0.0", False),
    ]:
        outcome = accepted(lambda: lib.strict_equal(lib.parse_json(left), lib.parse_json(right), []))
        observations.append({"id": "numeric_" + name, "expected_acceptance": expected, **outcome})
    report = {"scope": "Independent synthetic rejection probes, not a real replay or mathematical check.",
              "subject_code_sha256": {name: sha256((SUBJECT / name).read_bytes()).hexdigest()
                                      for name in ("checkpoint_lib.py", "run_clean_replay.py",
                                                   "compare_replays.py", "verify_checkpoint.py")},
              "probe_count": len(observations),
              "unexpected_acceptance_ids": [row["id"] for row in observations
                                            if row["accepted"] != row["expected_acceptance"]],
              "observations": observations}
    output = HERE / ("independent-probes-optimized.json" if sys.flags.optimize else "independent-probes-normal.json")
    with output.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"probe_count": len(observations),
                      "unexpected_acceptance_ids": report["unexpected_acceptance_ids"], "output": str(output)}))


if __name__ == "__main__":
    main()
