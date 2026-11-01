#!/usr/bin/env python3
"""Execute one authorized clean-source replay, binding inputs before launch.

No staging, commit, canonical evidence copy, metadata cleanup or PDF build occurs.
After a safe exclusive outer receipt is reserved, failures are retained as such.
"""
from argparse import ArgumentParser
import json
from pathlib import Path
import subprocess
import time

from checkpoint_lib import (
    BASELINE, ENV, get_pointer, git, json_snapshot, merge_hashes,
    outer_path, receipt_record, repository, require, require_unchanged, source_state,
)
from source_approval_adapter import approved_source_map


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--kind", choices=("counting", "torus"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    # Parse exactly the bytes whose initial identity is retained. These routing
    # fields must exist before any safe outer receipt can be established.
    spec, spec_identity = json_snapshot(args.spec)
    root, outer = Path(spec["root"]).resolve(), Path(spec["outer"]).resolve()
    require(not outer.is_relative_to(root), "replay evidence must be outside canonical")
    report = {"schema_version": 1, "kind": args.kind, "source_commit": spec.get("source_commit"),
              "spec_identity": spec_identity, "source_approval_identity": None,
              "argv": None, "cwd": str(root), "returncode": None, "command_executed": False,
              "stdout": "", "stderr": "", "source_before": None, "source_after": None,
              "output_path": None, "result": None, "stage": "specification_guards",
              "scope": "Actual command execution with frozen specification/approval and direct clean source HEAD/file guards; not independent scientific approval."}
    with receipt_record(outer, args.receipt, report):
        require(spec["ready"] is True, "replay specification is unfinished")
        require(type(spec.get("unresolved")) is list and spec["unresolved"] == [],
                "replay specification requires explicit empty unresolved list")
        repository(root)
        source = spec["source_commit"]
        require(spec["baseline_commit"] == BASELINE and
                git(root, "rev-list", "--parents", "-n", "1", source).decode().split() == [source, BASELINE],
                "expected final source-only direct-child commit")
        report["stage"] = "approval_guards"
        approval = spec["source_approval"]
        approval_path = outer_path(outer, approval["path"])
        approved, approval_identity = json_snapshot(approval_path)
        report["source_approval_identity"] = approval_identity
        require(approval_identity == approval["identity"], "integration approval identity")
        require(approved_source_map(approved, approval) == spec["approved_source_sha256"],
                "replay source allowlist differs from integration review")
        require(approval["required_values"], "approval decision predicates missing")
        for pointer, value in approval["required_values"].items():
            require(get_pointer(approved, pointer) == value, "source checkpoint not approved: " + pointer)
        changed = set(git(root, "diff", "--no-renames", "--name-only", BASELINE, source).decode().splitlines())
        require(changed == set(spec["approved_source_sha256"]), "source commit changes differ from approval")
        guards = merge_hashes(spec["approved_source_sha256"], spec["pdf_input_sha256"],
                             spec["replays"]["counting"]["runtime_sha256"], spec["replays"]["torus"]["runtime_sha256"])
        require(guards == spec["replay_guard_sha256"] and len(spec["pdf_input_sha256"]) == 26,
                "all reviewed code/manuscript inputs must be guarded")
        report["stage"] = "output_and_preflight_guards"
        task = spec["replays"][args.kind]
        output = outer_path(outer, task["output"])
        require(not output.exists() and not output.is_symlink() and output.parent.is_dir(), "output must be a new outer path")
        command = [spec["python"], "-B", str(root / ("experiments/counting_mixing/run.py" if args.kind == "counting" else "experiments/torus_campaign/run.py"))]
        preflight = None
        if args.kind == "counting":
            command += ["--output", str(output)]
            result_path = output
        else:
            preflight = outer_path(outer, task["accepted_preflight"])
            preflight_data, preflight_identity = json_snapshot(preflight)
            report["preflight_identity"] = preflight_identity
            require(preflight_identity["sha256"] == task["accepted_preflight_sha256"], "approved512 preflight identity")
            require(preflight_data["cutoff"] == 512 and preflight_data["checks_passed"] is True
                    and preflight_data["provenance"]["source_sha256"] == task["runtime_sha256"], "same-source preflight required")
            command += ["--cutoff", "8192", "--preflight", str(preflight), "--phase", "clean_replay", "--output-dir", str(output)]
            result_path = output / "result.json"
        report.update({"argv": command, "output_path": str(result_path), "stage": "prelaunch_source_guards"})
        before = source_state(root, source, guards)
        report["source_before"] = before
        require_unchanged(args.spec, spec_identity, "replay specification")
        require_unchanged(approval_path, approval_identity, "source approval")
        if preflight:
            require_unchanged(preflight, preflight_identity, "preflight")
        report["stage"] = "subprocess_launch"
        tick = time.perf_counter()
        completed = subprocess.run(command, cwd=root, env=ENV, capture_output=True, text=True, check=False)
        report.update({"elapsed_seconds": time.perf_counter() - tick, "returncode": completed.returncode,
                       "command_executed": True, "stdout": completed.stdout, "stderr": completed.stderr,
                       "stage": "postlaunch_identity_guards"})
        # Never replace the retained before identities with hashes calculated
        # after the command. Detect even changes to unused specification fields.
        require_unchanged(args.spec, spec_identity, "replay specification")
        require_unchanged(approval_path, approval_identity, "source approval")
        if preflight:
            require_unchanged(preflight, preflight_identity, "preflight")
        report["source_after"] = source_state(root, source, guards)
        require(report["source_after"] == before, "source changed during replay")
        require(completed.returncode == 0, "replay command failed")
        report["stage"] = "result_guards"
        data, result_identity = json_snapshot(result_path)
        report["result"] = result_identity
        require(data["checks_passed"] is True, "replay result checks failed")
        if args.kind == "counting":
            state = data["source"]
            require(state == data["source_at_completion"] and state["git_commit"] == source
                    and state["git_dirty"] is False and state["git_status_porcelain"] == [], "finite internal source guard")
            require({r["path"]: r["sha256"] for r in state["sources"]} == task["runtime_sha256"], "finite runtime identity")
        else:
            provenance = data["provenance"]
            require(data["phase"] == "clean_replay" and provenance["source_commit"] == source
                    and provenance["repository_dirty_at_start"] is False and provenance["git_status_porcelain_at_start"] == []
                    and data["source_input_immutability_gate_passed"] is True, "torus internal source guard")
            require(provenance["source_sha256"] == task["runtime_sha256"], "torus runtime identity")
        report["stage"] = "final_identity_guards"
        require_unchanged(args.spec, spec_identity, "replay specification")
        require_unchanged(approval_path, approval_identity, "source approval")
        require_unchanged(result_path, result_identity, "result")
        if preflight:
            require_unchanged(preflight, preflight_identity, "preflight")
        require(source_state(root, source, guards) == before, "source changed before receipt completion")
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "receipt": str(args.receipt), "output": report["output_path"]}))


if __name__ == "__main__":
    main()
