"""Independent preparation probes, confined to reviewer-owned disposable files.

No test is a scientific replay or a verification of a real checkpoint candidate.
The verifier drift probe substitutes unrelated scientific/preservation functions
while retaining the actual main control flow, Git gates and copy/manifest gates.
"""
from __future__ import annotations

import contextlib
import copy
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from unittest.mock import patch
from urllib.parse import unquote, urlsplit

import checkpoint_lib as lib
import run_clean_replay as replay
import verify_checkpoint as verifier

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent
PREP = OUTER / "checkpoint-prep"
CANONICAL = OUTER.parent.parent / "consolidated"
PYTHON = "/tmp/polyhedra-baseline-20261031/bin/python"
FIXTURE_ENV = {
    **os.environ,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_AUTHOR_NAME": "Independent checkpoint fixture",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Independent checkpoint fixture",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, env=FIXTURE_ENV, text=True).strip()


def rejects(operation):
    try:
        operation()
    except Exception as exc:
        return {"rejected": True, "exception": type(exc).__name__, "message": str(exc)}
    return {"rejected": False}


DRIVER = '''from pathlib import Path
from hashlib import sha256
import json, os, subprocess, sys
root=Path.cwd()
output=Path(sys.argv[sys.argv.index("--output")+1])
outer=output.parent
control=json.loads((outer/"control.json").read_text())
if control["mode"] == "command_failure":
    sys.exit(7)
head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
status=subprocess.check_output(["git","status","--porcelain=v1","--untracked-files=all"],text=True).splitlines()
name="experiments/counting_mixing/run.py"
source={"git_commit":head,"git_dirty":bool(status),"git_status_porcelain":status,
        "sources":[{"path":name,"sha256":sha256((root/name).read_bytes()).hexdigest()}]}
if control["mode"] == "source_drift":
    (root/"book/input0.tex").write_text("changed during command\\n")
if control["mode"] == "head_drift":
    env={**os.environ,"GIT_AUTHOR_NAME":"Fixture","GIT_AUTHOR_EMAIL":"fixture@example.invalid",
         "GIT_COMMITTER_NAME":"Fixture","GIT_COMMITTER_EMAIL":"fixture@example.invalid"}
    subprocess.run(["git","commit","--allow-empty","-qm","same tree changed HEAD"],check=True,env=env)
if control["mode"] == "spec_drift":
    path=outer/"replay-spec.json"
    spec=json.loads(path.read_text())
    spec["python"]="/not-the-interpreter-that-executed-this-command"
    path.write_text(json.dumps(spec,indent=2)+"\\n")
output.write_text(json.dumps({"checks_passed":True,"source":source,"source_at_completion":source})+"\\n")
'''


def fixture(base):
    root, outer = base / "repo", base / "evidence"
    root.mkdir()
    outer.mkdir()
    git(root, "init", "-q")
    (root / "README.md").write_text("Synthetic fixture; no real evidence.\n")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "fixture baseline")
    baseline = git(root, "rev-parse", "HEAD")
    driver = root / "experiments/counting_mixing/run.py"
    driver.parent.mkdir(parents=True)
    driver.write_text(DRIVER)
    inputs = {}
    for i in range(26):
        name = f"book/input{i}.tex"
        path = root / name
        path.parent.mkdir(exist_ok=True)
        path.write_text(f"synthetic manuscript input {i}\n")
        inputs[name] = lib.digest(path)
    runtime = {str(driver.relative_to(root)): lib.digest(driver)}
    approved = {**inputs, **runtime}
    git(root, "add", ".")
    git(root, "commit", "-qm", "fixture source")
    source = git(root, "rev-parse", "HEAD")
    approval = outer / "approval.json"
    dump(approval, {"decision": "approve", "approved_source_sha256": approved})
    spec = {
        "schema_version": 1, "ready": True, "root": str(root), "outer": str(outer),
        "python": PYTHON, "baseline_commit": baseline, "source_commit": source,
        "source_approval": {"path": "approval.json", "identity": lib.identity(approval),
                            "source_sha256_pointer": "/approved_source_sha256",
                            "required_values": {"/decision": "approve"}},
        "approved_source_sha256": approved, "pdf_input_sha256": inputs,
        "replay_guard_sha256": approved,
        "replays": {"counting": {"output": "result.json", "runtime_sha256": runtime},
                    "torus": {"runtime_sha256": {}}},
    }
    dump(outer / "replay-spec.json", spec)
    return root, outer, baseline, source, approved, spec


def wrapper_probe(mode):
    with tempfile.TemporaryDirectory(prefix="independent-wrapper-", dir=HERE) as temporary:
        root, outer, baseline, _, _, _ = fixture(Path(temporary))
        dump(outer / "control.json", {"mode": mode})
        if mode == "dirty_before":
            (root / "untracked.txt").write_text("dirty before execution\n")
        spec_path, receipt = outer / "replay-spec.json", outer / "receipt.json"
        before = lib.identity(spec_path)
        argv = ["run_clean_replay.py", "--spec", str(spec_path), "--kind", "counting", "--receipt", str(receipt)]
        with patch.object(replay, "BASELINE", baseline), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            outcome = rejects(replay.main)
        report = lib.load_json(receipt) if receipt.exists() else None
        return {
            "mode": mode, **outcome, "receipt_written": receipt.exists(),
            "receipt_checks_passed": report["checks_passed"] if report else None,
            "actual_spec_before": before, "actual_spec_after": lib.identity(spec_path),
            "receipt_spec_identity": report.get("spec_identity") if report else None,
            "receipt_failure": report.get("failure") if report else None,
            "source_before_after_equal": report["source_before"] == report["source_after"] if report else None,
        }


def unresolved_contract_probe():
    with tempfile.TemporaryDirectory(prefix="independent-unresolved-", dir=HERE) as temporary:
        root, _, baseline, source, approved, _ = fixture(Path(temporary))
        pins = []
        for role in ("algebra", "dynamics", "arithmetic", "counting", "integration"):
            path = root / lib.REL / (role + ".json")
            dump(path, {"decision": "approve", "approved_source_sha256": approved})
            pin = {"role": role, "path": role + ".json", "identity": lib.identity(path),
                   "required_values": {"/decision": "approve"}}
            if role == "integration":
                pin["source_sha256_pointer"] = "/approved_source_sha256"
            pins.append(pin)
        config = {"schema_version": 1, "ready": True, "baseline_commit": baseline,
                  "source_commit": source, "approved_source_sha256": approved,
                  "approval_pins": pins, "unresolved": ["Independent final PDF review is still required"]}
        with patch.object(verifier, "BASELINE", baseline):
            return {"unresolved": config["unresolved"], **rejects(lambda: verifier.approved_contract(root, config))}


def manifest_drift_probe():
    with tempfile.TemporaryDirectory(prefix="independent-manifest-", dir=HERE) as temporary:
        root, outer, baseline, source, approved, _ = fixture(Path(temporary))
        config = {"pdf": {"input_sha256": {}}, "replays": {"counting": {"runtime_sha256": {}},
                   "torus": {"runtime_sha256": {}}}, "replay_guard_sha256": approved}
        payloads = {verifier.CONTRACT: json.dumps(config).encode(),
                    lib.PDF: b"synthetic PDF identity fixture; no visual claims\n",
                    **{path: b"{}\n" for path in lib.RESULTS.values()},
                    lib.REL + "/note.txt": b"version one\n"}
        for name, value in payloads.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)

        def remake_manifests():
            copies = []
            for i, name in enumerate(payloads):
                destination = outer / "copies" / str(i)
                destination.parent.mkdir(exist_ok=True)
                destination.write_bytes((root / name).read_bytes())
                copies.append({"path": name, "outer_source": str(destination.relative_to(outer)), **lib.identity(destination)})
            dump(root / verifier.COPY_MANIFEST, {"baseline_commit": baseline, "source_commit": source,
                                                "omissions": ["Synthetic fixture only"], "files": copies})
            files = {name: lib.identity(root / name) for name in [*payloads, verifier.COPY_MANIFEST]}
            dump(root / verifier.MANIFEST, {"baseline_commit": baseline, "source_commit": source, "files": files})

        remake_manifests()
        before = lib.identity(root / verifier.MANIFEST)

        def mutate_during_scientific_gate(*_args):
            (root / lib.REL / "note.txt").write_text("version two while verifier is running\n")
            remake_manifests()
            return {"scope": "Synthetic hook; no scientific validation performed"}

        receipt = outer / "verification.json"
        argv = ["verify_checkpoint.py", "--root", str(root), "--outer", str(outer), "--candidate", "--receipt", str(receipt)]
        with contextlib.ExitStack() as stack:
            for name, value in {
                "BASELINE": baseline,
                "approved_contract": lambda *_: (source, approved),
                "source_checkpoint_receipts": lambda *_: None,
                "preservation": lambda *_: {"synthetic_fixture": True},
                "scientific_results": mutate_during_scientific_gate,
                "manuscript_pdf_links": lambda *_: {"synthetic_fixture": True},
                "fsck": lambda *_: {"synthetic_fixture": True},
            }.items():
                stack.enter_context(patch.object(verifier, name, value))
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            outcome = rejects(verifier.main)
        result = lib.load_json(receipt) if receipt.exists() else None
        return {**outcome, "scope": "Actual main/Git/artifact-copy-manifest gates; unrelated scientific, preservation and approval functions substituted in synthetic fixture",
                "manifest_before": before, "manifest_after": lib.identity(root / verifier.MANIFEST),
                "receipt_written": receipt.exists(), "receipt_checks_passed": result["checks_passed"] if result else None,
                "receipt_manifest_sha256": result.get("candidate_manifest_sha256") if result else None}


def mismatch_receipt_probe():
    with tempfile.TemporaryDirectory(prefix="independent-mismatch-", dir=HERE) as temporary:
        outer = Path(temporary)
        before = lib.load_json(OUTER / "computation/revision-v2/author-result-60-90-v2.json")
        after = copy.deepcopy(before)
        after["check_counts"]["exact"] += 1
        dump(outer / "reference.json", before)
        dump(outer / "candidate.json", after)
        receipt = outer / "mismatch.json"
        command = [PYTHON, "-B", str(HERE / "compare_replays.py"), "--kind", "counting", "--outer", str(outer),
                   "--reference", "reference.json", "--candidate", "candidate.json", "--receipt", str(receipt)]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        return {"returncode": completed.returncode, "receipt_written": receipt.exists(),
                "rejection_message_present": "scientific JSON differs" in completed.stderr}


def curation_audit():
    plan = lib.load_json(PREP / "curation-plan.json")
    rows = plan["planned_existing_exact_copies"]
    selected = {row["path"] for row in rows}
    failures, links = [], []
    for row in rows:
        source = lib.outer_path(OUTER, row["outer_source"])
        expected = {"sha256": row["sha256"], "bytes": row["bytes"]}
        if lib.identity(source) != expected:
            failures.append(row["outer_source"])
        if row["path"].endswith(".md"):
            virtual = CANONICAL / row["path"]
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", source.read_text()):
                parsed = urlsplit(target.strip("<>"))
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                destination = (virtual.parent / unquote(parsed.path)).resolve()
                covered = destination.exists() or (destination.is_relative_to(CANONICAL) and str(destination.relative_to(CANONICAL)) in selected)
                links.append({"source": row["outer_source"], "target": target, "covered_by_existing_or_planned": covered})
    exclusions = lib.load_json(PREP / "comparison-exclusions.json")
    return {"rows": len(rows), "bytes": sum(row["bytes"] for row in rows),
            "identity_failures": failures, "duplicate_destinations": len(rows) - len(selected),
            "torus_pointer_list_matches_code": exclusions["torus"] == lib.torus_pointers(),
            "counting_pointer_list_matches_code": exclusions["counting"] == ["/generated_at_utc", "/elapsed_seconds", "/source", "/source_at_completion"],
            "markdown_links": links, "uncovered_markdown_links": [row for row in links if not row["covered_by_existing_or_planned"]]}


def raw_tamper_probe():
    with tempfile.TemporaryDirectory(prefix="independent-raw-", dir=HERE) as temporary:
        outer = Path(temporary)
        streams = []
        for name in ("surface.lengths.f64le", "surface.slopes.i32le"):
            (outer / name).write_bytes(b"12345678")
            streams.append({"path": name, **lib.identity(outer / name)})
        native_path = outer / "surface.native.json"
        dump(native_path, {"raw_peak_rss": 1, "timing_seconds": {key: 0.0 for key in lib.TIMING_KEYS}, "count": 1})
        surface = {"raw_native_report": {"path": native_path.name, "sha256": lib.digest(native_path)}, "raw_streams": streams}
        report = {"surfaces": [surface]}
        valid = rejects(lambda: lib.torus_raw_comparison(report, report, outer))
        (outer / streams[0]["path"]).write_bytes(b"12345679")
        changed = rejects(lambda: lib.torus_raw_comparison(report, report, outer))
        return {"original_control": valid, "same_size_one_byte_raw_tamper": changed}


def main():
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Independent preparation probes only; synthetic Git repositories and driver outputs do not represent scientific evidence or a final candidate.",
              "python_optimized": sys.flags.optimize,
              "wrapper_probes": [wrapper_probe(mode) for mode in ("success", "command_failure", "source_drift", "head_drift", "dirty_before", "spec_drift")],
              "unresolved_contract_probe": unresolved_contract_probe(),
              "manifest_drift_probe": manifest_drift_probe(),
              "mismatch_receipt_probe": mismatch_receipt_probe(),
              "raw_tamper_probe": raw_tamper_probe(),
              "curation_audit": curation_audit()}
    destination = HERE / ("independent-probes-optimized-v1.json" if sys.flags.optimize else "independent-probes-normal-v1.json")
    dump(destination, report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
