"""Re-exercise the original independent counterexamples against frozen v2 bytes.

Fixtures are synthetic and reviewer-owned. No scientific replay or real
candidate verification is performed, and the original v1 evidence is untouched.
"""
import contextlib
from datetime import datetime, timezone
import importlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SUBJECT = HERE / "subject"
OUTER = HERE.parent.parent
sys.path.insert(0, str(SUBJECT))
lib = importlib.import_module("checkpoint_lib")
compare = importlib.import_module("compare_replays")
replay = importlib.import_module("run_clean_replay")
probe_spec = importlib.util.spec_from_file_location("original_independent_probes", HERE.parent / "independent_probes_v1.py")
original = importlib.util.module_from_spec(probe_spec)
probe_spec.loader.exec_module(original)
original.HERE = SUBJECT
original.OUTER = OUTER
old_fixture = original.fixture


def adapted_fixture(base):
    result = old_fixture(base)
    result[-1]["unresolved"] = []
    original.dump(result[1] / "replay-spec.json", result[-1])
    return result


original.fixture = adapted_fixture


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def comparison_case(mode):
    with tempfile.TemporaryDirectory(prefix="independent-comparison-v2-", dir=HERE) as temporary:
        outer = Path(temporary)
        data = lib.load_json(OUTER / "computation/revision-v2/author-result-60-90-v2.json")
        reference, candidate = outer / "reference.json", outer / "candidate.json"
        original.dump(reference, data)
        if mode == "mismatch":
            data["check_counts"]["exact"] += 1
        original.dump(candidate, data)
        before = {"reference": lib.identity(reference), "candidate": lib.identity(candidate)}

        def comparison_then_drift(left, right):
            result = lib.counting_comparison(left, right)
            target = reference if mode == "reference_drift" else candidate
            changed = lib.load_json(target)
            changed["check_counts"]["exact"] += 1
            original.dump(target, changed)
            return result

        receipt = outer / "receipt.json"
        argv = ["compare_replays.py", "--kind", "counting", "--outer", str(outer),
                "--reference", str(reference), "--candidate", str(candidate), "--receipt", str(receipt)]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if mode.endswith("_drift"):
                stack.enter_context(patch.object(compare, "counting_comparison", comparison_then_drift))
            outcome = original.rejects(compare.main)
        report = lib.load_json(receipt)
        require(report["checks_passed"] is (mode == "success"), "unexpected comparison outcome")
        require(report["exit_status"] == (0 if mode == "success" else 1), "wrong comparison exit status")
        for key, initial in before.items():
            require({k: report[key][k] for k in initial} == initial, "comparison overwrote initial identity")
        return {"mode": mode, **outcome, "receipt_checks_passed": report["checks_passed"],
                "exit_status": report["exit_status"], "initial_input_identities_retained": True,
                "failure_stage": report.get("failure_stage"), "failure": report.get("failure")}


TORUS_DRIVER = '''from pathlib import Path
import json, subprocess, sys
root=Path.cwd()
output=Path(sys.argv[sys.argv.index("--output-dir")+1])
preflight=Path(sys.argv[sys.argv.index("--preflight")+1])
spec=json.loads((output.parent/"replay-spec.json").read_text())
mode=json.loads((output.parent/"control.json").read_text())["mode"]
if mode == "preflight_drift":
    p=json.loads(preflight.read_text()); p["unused_note"]="changed during synthetic subprocess"
    preflight.write_text(json.dumps(p)+"\\n")
output.mkdir()
head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
data={"checks_passed":True,"phase":"clean_replay","source_input_immutability_gate_passed":True,
      "provenance":{"source_commit":head,"repository_dirty_at_start":False,"git_status_porcelain_at_start":[],
      "source_sha256":spec["replays"]["torus"]["runtime_sha256"]}}
(output/"result.json").write_text(json.dumps(data)+"\\n")
'''


def torus_wrapper_case(mode):
    with tempfile.TemporaryDirectory(prefix="independent-torus-wrapper-v2-", dir=HERE) as temporary:
        root, outer, baseline, _, approved, spec = adapted_fixture(Path(temporary))
        name = "experiments/torus_campaign/run.py"
        driver = root / name
        driver.parent.mkdir(parents=True)
        driver.write_text(TORUS_DRIVER)
        original.git(root, "add", name)
        original.git(root, "commit", "--amend", "--no-edit", "-q")
        source = original.git(root, "rev-parse", "HEAD")
        approved[name] = lib.digest(driver)
        runtime = {name: lib.digest(driver)}
        spec["source_commit"] = source
        spec["approved_source_sha256"] = approved
        spec["replay_guard_sha256"] = approved
        original.dump(outer / "approval.json", {"decision": "approve", "approved_source_sha256": approved})
        spec["source_approval"]["identity"] = lib.identity(outer / "approval.json")
        preflight = outer / "preflight.json"
        original.dump(preflight, {"cutoff": 512, "checks_passed": True, "provenance": {"source_sha256": runtime}, "unused_note": "initial"})
        original_preflight = lib.identity(preflight)
        spec["replays"]["torus"] = {"runtime_sha256": runtime, "output": "torus-output",
                                      "accepted_preflight": "preflight.json", "accepted_preflight_sha256": lib.digest(preflight)}
        original.dump(outer / "replay-spec.json", spec)
        original.dump(outer / "control.json", {"mode": mode})
        receipt = outer / "receipt.json"
        argv = ["run_clean_replay.py", "--spec", str(outer / "replay-spec.json"), "--kind", "torus", "--receipt", str(receipt)]
        with patch.object(replay, "BASELINE", baseline), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            outcome = original.rejects(replay.main)
        report = lib.load_json(receipt)
        require(report["checks_passed"] is (mode == "success"), "unexpected torus fixture result")
        require(report["preflight_identity"] == original_preflight, "preflight identity overwritten")
        if mode == "preflight_drift":
            require("preflight identity changed" in report["failure"], "preflight rejected for wrong reason")
        return {"mode": mode, **outcome, "receipt_checks_passed": report["checks_passed"],
                "command_executed": report["command_executed"], "returncode": report["returncode"],
                "exit_status": report["exit_status"], "initial_preflight_identity_retained": True,
                "failure_stage": report.get("failure_stage"), "failure": report.get("failure"),
                "scope": "Synthetic torus branch: no compiler, enumeration, high-precision work or scientific replay"}


def main():
    wrappers = [original.wrapper_probe(mode) for mode in ("success", "command_failure", "source_drift", "head_drift", "dirty_before", "spec_drift")]
    for row in wrappers:
        require(row["receipt_written"], "missing wrapper receipt: " + row["mode"])
        require(row["receipt_checks_passed"] is (row["mode"] == "success"), "wrong wrapper outcome: " + row["mode"])
        require(row["receipt_spec_identity"] == row["actual_spec_before"], "original spec identity replaced")
    manifest = original.manifest_drift_probe()
    require(manifest["receipt_checks_passed"] is False and manifest["rejected"], "manifest drift accepted")
    require("frozen checkpoint control" in manifest["message"], "manifest rejected for unrelated reason")
    unresolved = original.unresolved_contract_probe()
    require(unresolved["rejected"] and "explicit empty unresolved" in unresolved["message"], "unresolved contract accepted")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "python_optimized": sys.flags.optimize,
        "scope": "Original v1 counterexamples rerun against exact repaired v2 scripts; synthetic fixtures only",
        "fixture_adapter": "Only add the now-required unresolved: [] to otherwise successful v1 replay specifications; redirect temporary files to reviewer-owned subject directory",
        "wrapper_probes": wrappers, "manifest_drift_probe": manifest, "unresolved_contract_probe": unresolved,
        "comparison_probes": [comparison_case(mode) for mode in ("success", "mismatch", "candidate_drift", "reference_drift")],
        "torus_wrapper_probes": [torus_wrapper_case(mode) for mode in ("success", "preflight_drift")],
        "all_expected_controls_and_rejections_observed": True,
    }
    destination = HERE / ("independent-delta-optimized.json" if sys.flags.optimize else "independent-delta-normal.json")
    original.dump(destination, report)
    print(json.dumps({"checks_passed": True, "python_optimized": sys.flags.optimize,
                      "evidence": str(destination), "wrapper_cases": len(wrappers), "comparison_cases": 4,
                      "torus_wrapper_cases": 2, "manifest_drift_rejected": True, "unresolved_rejected": True}))


if __name__ == "__main__":
    main()
