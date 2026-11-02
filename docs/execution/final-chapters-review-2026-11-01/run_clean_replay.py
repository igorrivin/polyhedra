#!/usr/bin/env python3
"""Execute the approved finite companion once, outside the canonical checkout.

No staging, commit, PDF build, evidence copy or metadata cleanup occurs.
An unready specification fails before launch and retains a failure receipt.
"""
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import time

from checkpoint_lib import (
    DRIVER, ENV, approved_spec, identity, json_snapshot, outer_path, ready_spec,
    receipt_record, recheck, require, source_state, validate_report,
)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    spec, frozen_spec = json_snapshot(args.spec)
    root, outer = Path(spec["root"]).resolve(), Path(spec["outer"]).resolve()
    require(not outer.is_relative_to(root) and not root.is_relative_to(outer),
            "canonical and outer evidence directories must be disjoint")
    report = {"schema_version": 1, "source_commit": spec.get("source_commit"),
              "spec_identity": frozen_spec, "frozen_input_identities": {}, "cwd": str(root),
              "argv": None, "command_executed": False, "returncode": None,
              "stdout": "", "stderr": "", "source_before": None, "source_after": None,
              "result": None, "output_path": None, "stage": "specification_guards",
              "scope": "Actual finite command execution with clean source, input and result identity guards; not independent mathematical or implementation approval."}
    with receipt_record(outer, args.receipt, report):
        ready_spec(spec)
        report["stage"] = "approval_guards"
        root, outer, _, frozen = approved_spec(spec)
        frozen[str(args.spec.resolve())] = frozen_spec
        report["frozen_input_identities"] = dict(frozen)
        report["stage"] = "output_guards"
        output = outer_path(outer, spec["output"])
        require(not output.exists() and not output.is_symlink() and output.parent.is_dir(),
                "output must be a new outer file with an existing parent")
        require(not output.resolve().is_relative_to(root), "result may not be written inside canonical")
        command = [spec["python"], "-B", str(root / DRIVER), "--output", str(output)]
        report.update({"argv": command, "output_path": str(output), "stage": "prelaunch_source_guards"})
        before = source_state(root, spec["source_commit"], spec["replay_guard_sha256"])
        report["source_before"] = before
        recheck(frozen)
        report["stage"] = "subprocess_launch"
        started = time.perf_counter()
        completed = subprocess.run(command, cwd=root, env=ENV, capture_output=True, text=True, check=False)
        report.update({"elapsed_seconds": time.perf_counter() - started, "returncode": completed.returncode,
                       "command_executed": True, "stdout": completed.stdout, "stderr": completed.stderr,
                       "stage": "postlaunch_identity_guards"})
        recheck(frozen)
        report["source_after"] = source_state(root, spec["source_commit"], spec["replay_guard_sha256"])
        require(report["source_after"] == before, "source changed during replay")
        require(completed.returncode == 0, "finite companion command failed")
        report["stage"] = "result_guards"
        result, frozen_result = json_snapshot(output)
        report["result"] = frozen_result
        validate_report(result, spec, clean=True)
        for row in result["source_before"]["sources"] + result["source_before"]["guarded_dependencies"]:
            require(identity(root / row["path"]) == {"sha256": row["sha256"], "bytes": row["bytes"]},
                    "result runtime byte count differs")
        frozen[str(output)] = frozen_result
        report["stage"] = "final_identity_guards"
        recheck(frozen)
        require(source_state(root, spec["source_commit"], spec["replay_guard_sha256"]) == before,
                "source changed before receipt completion")
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "receipt": str(args.receipt), "output": str(output)}))


if __name__ == "__main__":
    main()
