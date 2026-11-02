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
SUBJECT = HERE / "subject-v1"
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
        baseline, spec, reference, candidate = case.fixture()
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
            a, b = report_pair(first, second, raw)
            with patch.object(lib, "BASELINE", baseline):
                outcome = accepted(lambda: lib.finite_comparison(a, b, spec))
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

        escape = case.outer / "outside-link"
        escape.symlink_to(case.root, target_is_directory=True)
        outcome = accepted(lambda: lib.outer_path(case.outer, "outside-link/result.json"))
        observations.append({"id": "symlink_outer_escape", "expected_acceptance": False, **outcome})
        escape.unlink()

        # The author's synthetic positive fixture has 36 unrelated .tex files
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
