"""Fresh-working-directory entry points, portable pins, and refusal paths."""
import contextlib
import copy
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest.mock import patch

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "consolidated"
sys.path.insert(0, str(REPO))
from experiments.counting_mixing import run

PYTHON = "/tmp/polyhedra-baseline-20261031/bin/python"
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(REPO))
receipts = []


def command(argv, cwd):
    started = time.perf_counter()
    p = subprocess.run(argv, cwd=cwd, env=env, text=True, capture_output=True)
    receipt = {"argv": argv, "cwd": str(cwd), "returncode": p.returncode,
               "elapsed_seconds": time.perf_counter()-started, "stdout": p.stdout, "stderr": p.stderr,
               "env_overrides": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(REPO)}}
    receipts.append(receipt)
    return p


def refused(output):
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            run.main(["--output", str(output)])
        except SystemExit as exc:
            assert exc.code == 2
            return
    raise AssertionError("invalid output accepted")


with tempfile.TemporaryDirectory(dir=OUT) as directory:
    cwd = Path(directory)
    p = command([PYTHON, "-c", "import experiments.counting_mixing.run"], cwd)
    assert p.returncode == 0 and not p.stdout and not p.stderr
    assert list(cwd.iterdir()) == []
    output = OUT/"reviewer-module-result-60-90.json"
    # Audit hook proves external author specification paths are not opened at runtime.
    script = '''import runpy, sys
def audit(event, args):
    if event == "open" and isinstance(args[0], (str, bytes)):
        path = str(args[0])
        if any(piece in path for piece in ("algebra-author", "dynamics-author", "arithmetic-author")):
            raise AssertionError("External author contract opened: " + path)
sys.addaudithook(audit)
sys.argv = ["experiments.counting_mixing.run", "--output", sys.argv[1]]
runpy.run_module("experiments.counting_mixing.run", run_name="__main__")
'''
    p = command([PYTHON, "-c", script, str(output)], cwd)
    assert p.returncode == 0, p.stderr
    for bad in (cwd/"missing-parent/output.json", run.HERE/"reviewer-must-never-create.json"):
        assert not bad.exists()
        refused(bad)
        assert not bad.exists()
    existing = cwd/"existing.json"
    existing.write_text("reviewer sentinel\n")
    refused(existing)
    assert existing.read_text() == "reviewer sentinel\n"
    target, dangling = cwd/"target.json", cwd/"dangling.json"
    dangling.symlink_to(target)
    refused(dangling)
    assert not target.exists()
    baseline = run.source_state()
    drift_outcomes = []
    for field in ("source", "fixture", "HEAD"):
        changed = copy.deepcopy(baseline)
        if field == "HEAD":
            changed["git_commit"] = "f"*40
        else:
            index = next(i for i, row in enumerate(changed["sources"])
                         if row["path"].endswith("fixture.json" if field == "fixture" else "numerics.py"))
            changed["sources"][index]["sha256"] = "f"*64
        destination = cwd/("drift-"+field+".json")
        with patch.object(run, "source_state", side_effect=[baseline, changed]), patch.object(run, "calculate", return_value={}):
            try:
                run.main(["--output", str(destination)])
            except AssertionError:
                pass
            else:
                raise AssertionError("drift accepted")
        assert not destination.exists()
        drift_outcomes.append({"simulated_drift": field, "successful_output_refused": True})

module = json.loads((OUT/"reviewer-module-result-60-90.json").read_text())
absolute = json.loads((OUT/"reviewer-result-60-90.json").read_text())
excluded = ["generated_at_utc", "elapsed_seconds"]
for data in (module, absolute):
    for key in excluded:
        data.pop(key)
    for key in ("source", "source_at_completion"):
        data[key].pop("git_status_porcelain")
        data[key].pop("git_dirty")
assert module == absolute, "Module and absolute-path scientific results differ"
historical_before = json.loads((OUT/"historical-inventory-before.json").read_text())
historical_checks = []
for row in historical_before:
    data = (REPO/row["path"]).read_bytes()
    historical_checks.append({"path": row["path"], "unchanged": sha256(data).hexdigest() == row["sha256"] and len(data) == row["bytes"]})
assert all(row["unchanged"] for row in historical_checks)
result = {"status": "pass", "fresh_import_no_output_or_working_directory_writes": True,
          "guarded_module_replay_no_author_contract_runtime_reads": True,
          "module_and_absolute_scientific_equality": True,
          "output_refusals": ["missing parent", "inside source", "existing file", "dangling symlink"],
          "main_drift_fault_injections": drift_outcomes,
          "historical_file_checks": historical_checks, "commands": receipts}
(OUT/"runtime-probes-result.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"status": "pass", "historical_files_unchanged": len(historical_checks),
                  "module_replay": "pass", "main_drift_fault_injections": len(drift_outcomes)}))
