#!/usr/bin/env python3
"""Execute ONE actually authorized clean-source replay into new outer evidence.

Run only after the independently approved source-only commit. This driver does
not stage, commit, copy canonical evidence, perform metadata cleanup, or build a
PDF. An unsuccessful command/source guard leaves an explicit failure receipt.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time

from checkpoint_lib import (
    BASELINE, ENV, digest, get_pointer, git, identity, load_json, merge_hashes, outer_path,
    repository, require, source_state,
)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--kind", choices=("counting", "torus"), required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    spec = load_json(args.spec)
    require(spec["ready"] is True, "replay specification is unfinished")
    root, outer = repository(spec["root"]), Path(spec["outer"]).resolve()
    require(not outer.is_relative_to(root), "replay evidence must be outside canonical")
    source = spec["source_commit"]
    require(spec["baseline_commit"] == BASELINE and
            git(root, "rev-list", "--parents", "-n", "1", source).decode().split() == [source, BASELINE],
            "expected final source-only direct-child commit")
    approval = spec["source_approval"]
    approval_path = outer_path(outer, approval["path"])
    require(identity(approval_path) == approval["identity"], "integration approval identity")
    approved = load_json(approval_path)
    require(get_pointer(approved, approval["source_sha256_pointer"]) == spec["approved_source_sha256"],
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
    receipt = outer_path(outer, str(args.receipt.resolve()))
    require(receipt.parent.is_dir() and not receipt.exists() and not receipt.is_symlink(), "receipt must be a new outer path")
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
        require(digest(preflight) == task["accepted_preflight_sha256"], "approved512 preflight identity")
        p = load_json(preflight)
        require(p["cutoff"] == 512 and p["checks_passed"] is True
                and p["provenance"]["source_sha256"] == task["runtime_sha256"], "same-source preflight required")
        command += ["--cutoff", "8192", "--preflight", str(preflight), "--phase", "clean_replay", "--output-dir", str(output)]
        result_path = output / "result.json"
    before = source_state(root, source, guards)
    started = datetime.now(timezone.utc).isoformat()
    tick = time.perf_counter()
    completed = subprocess.run(command, cwd=root, env=ENV, capture_output=True, text=True, check=False)
    report = {"schema_version": 1, "kind": args.kind, "source_commit": source,
              "spec_identity": identity(args.spec), "source_approval_identity": identity(approval_path),
              "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
              "elapsed_seconds": time.perf_counter() - tick, "argv": command, "cwd": str(root),
              "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr,
              "source_before": before, "source_after": None, "output_path": str(result_path),
              "result": None, "checks_passed": False, "scope": "Actual command execution with direct clean source HEAD/file guards before and after; not independent scientific approval."}
    error = None
    try:
        report["source_after"] = source_state(root, source, guards)
        require(report["source_after"] == before, "source changed during replay")
        require(completed.returncode == 0, "replay command failed")
        if preflight:
            require(digest(preflight) == task["accepted_preflight_sha256"], "preflight changed during replay")
        data = load_json(result_path)
        require(data["checks_passed"] is True, "replay result checks failed")
        if args.kind == "counting":
            state = data["source"]
            require(state == data["source_at_completion"] and state["git_commit"] == source
                    and state["git_dirty"] is False and state["git_status_porcelain"] == [], "finite internal source guard")
            require({r["path"]: r["sha256"] for r in state["sources"]} == task["runtime_sha256"], "finite runtime identity")
        else:
            p = data["provenance"]
            require(data["phase"] == "clean_replay" and p["source_commit"] == source
                    and p["repository_dirty_at_start"] is False and p["git_status_porcelain_at_start"] == []
                    and data["source_input_immutability_gate_passed"] is True, "torus internal source guard")
            require(p["source_sha256"] == task["runtime_sha256"], "torus runtime identity")
        report["result"] = identity(result_path)
        report["checks_passed"] = True
    except Exception as exc:
        error = exc
        report["failure"] = type(exc).__name__ + ": " + str(exc)
    with receipt.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"checks_passed": report["checks_passed"], "receipt": str(receipt), "output": str(result_path)}))
    if error:
        raise error


if __name__ == "__main__":
    main()
