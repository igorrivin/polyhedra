"""Reproduce the review's source tests; each mode is an explicit separate run."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[1] / "consolidated"
PYTHON = "/tmp/polyhedra-baseline-20261031/bin/python"
MODE = sys.argv[1]
if MODE not in {"focused", "focused-fixed", "full"}:
    raise SystemExit("choose focused, focused-fixed or full")
environment = {
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONPATH": "packages/volume-toolkit",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "MPLCONFIGDIR": "/tmp/polyhedra-mpl-20261031",
    "GRADIO_ANALYTICS_ENABLED": "False",
}
command = [PYTHON, "-m", "pytest", "-q", "-p", "no:cacheprovider",
           f"--junitxml={EVIDENCE / f'review-{MODE}.xml'}"]
if MODE == "full":
    command += ["--continue-on-collection-errors", "packages/volume-toolkit/tests"]
elif MODE == "focused-fixed":
    command += ["packages/volume-toolkit/tests/test_angle_barrier.py",
                "packages/volume-toolkit/tests/test_variational.py"]
else:
    command += ["packages/volume-toolkit/tests/" + name for name in (
        "test_angle_barrier.py", "test_variational.py", "test_geometry.py",
        "test_geometry_precision.py", "test_correctness_regressions.py")]
watched = ["angle_barrier.py", "variational.py", "geometry.py"]
source_hashes = {
    f"packages/volume-toolkit/ideal_poly_volume_toolkit/{name}": hashlib.sha256(
        (REPO / "packages/volume-toolkit/ideal_poly_volume_toolkit" / name).read_bytes()).hexdigest()
    for name in watched
}
record = {"command": command, "cwd": str(REPO), "environment_overrides": environment,
          "source_hashes": source_hashes, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
record_path = EVIDENCE / f"review-{MODE}-command.json"
if record_path.exists():
    raise SystemExit(f"refusing to overwrite previous run {record_path}")
record_path.write_text(json.dumps(record, indent=2) + "\n")
start = time.monotonic()
with (EVIDENCE / f"review-{MODE}.log").open("w") as output:
    completed = subprocess.run(command, cwd=REPO, env={**os.environ, **environment},
                               stdout=output, stderr=subprocess.STDOUT, check=False)
record.update(returncode=completed.returncode, elapsed_seconds=time.monotonic() - start,
              finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
record_path.write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
raise SystemExit(completed.returncode)
