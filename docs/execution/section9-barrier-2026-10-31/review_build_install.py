"""Offline source-distribution/wheel and separate-target install validation."""
from __future__ import annotations

import email
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import zipfile

EVIDENCE = Path(__file__).resolve().parent
REPO = EVIDENCE.parents[1] / "consolidated"
PACKAGE = REPO / "packages/volume-toolkit"
PYTHON = "/tmp/polyhedra-baseline-20261031/bin/python"
CORE_PYTHON = "/tmp/polyhedra-numerical-core-20261031/bin/python"
OUTPUT = EVIDENCE / "review-package-validation.json"
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")
ROOT = Path(tempfile.mkdtemp(prefix="polyhedra-barrier-review-package-20261031-"))
DIST = ROOT / "dist"
TARGET = ROOT / "installed-target"
WORK = ROOT / "outside-source"
TARGET.mkdir()
WORK.mkdir()
overrides = {"PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INDEX": "1",
             "PIP_DISABLE_PIP_VERSION_CHECK": "1", "COPYFILE_DISABLE": "1"}
env = {key: value for key, value in os.environ.items() if key != "PYTHONPATH"}
env.update(overrides)
report = {"workspace": str(ROOT), "source": str(PACKAGE),
          "environment_overrides": overrides, "removed_environment": ["PYTHONPATH"],
          "scope": "preliminary dirty-source offline build and separate-target wheel install; no dependency resolution or release",
          "commands": []}


def save():
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def run(name, command, cwd, overrides=None):
    start = time.monotonic()
    with (EVIDENCE / f"review-{name}.log").open("w") as log:
        result = subprocess.run(command, cwd=cwd, env={**env, **(overrides or {})},
                                stdout=log, stderr=subprocess.STDOUT, check=False)
    row = {"name": name, "argv": command, "cwd": str(cwd),
           "additional_environment": overrides or {}, "returncode": result.returncode,
           "elapsed_seconds": time.monotonic() - start}
    report["commands"].append(row)
    save()
    if result.returncode:
        raise RuntimeError(f"{name} returned {result.returncode}; see its retained log")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def original_install_hashes():
    # Snapshot package plus dist-info, not the other pre-existing dependencies.
    site = Path(CORE_PYTHON).parent.parent / "lib/python3.12/site-packages"
    directories = sorted(site.glob("ideal_poly_volume_toolkit*"))
    return {str(path.relative_to(site)): digest(path.read_bytes())
            for directory in directories for path in sorted(directory.rglob("*"))
            if path.is_file() and "__pycache__" not in path.parts}


names = ["angle_barrier.py", "variational.py", "geometry.py", "__init__.py"]
source_hashes = {name: digest((PACKAGE / "ideal_poly_volume_toolkit" / name).read_bytes())
                 for name in names}
report["source_hashes_before"] = source_hashes
report["old_core_install_before"] = original_install_hashes()
save()
run("offline-build", [PYTHON, "-m", "build", "--no-isolation", "--outdir", str(DIST), str(PACKAGE)], REPO)

wheel, = DIST.glob("*.whl")
sdist, = DIST.glob("*.tar.gz")
payloads = {}
with zipfile.ZipFile(wheel) as archive:
    payloads["wheel"] = {name: archive.read(name) for name in archive.namelist() if not name.endswith("/")}
with tarfile.open(sdist) as archive:
    payloads["sdist"] = {entry.name: archive.extractfile(entry).read()
                         for entry in archive.getmembers() if entry.isfile()}
inventory = {}
for kind, payload in payloads.items():
    contamination = [name for name in payload if any(part.startswith("._") or part == "__MACOSX"
                                                    for part in Path(name).parts)]
    caches = [name for name in payload if "__pycache__" in name or name.endswith(".pyc")]
    source_matches = {}
    for name in names:
        candidates = [member for member in payload if member.endswith("ideal_poly_volume_toolkit/" + name)]
        assert len(candidates) == 1, (kind, name, candidates)
        actual = digest(payload[candidates[0]])
        source_matches[name] = {"member": candidates[0], "sha256": actual,
                                "matches_source": actual == source_hashes[name]}
        assert actual == source_hashes[name], (kind, name, "wrong source bytes")
    metadata_name, = [name for name in payload if name.endswith(".dist-info/METADATA") or (
        name.count("/") == 1 and name.endswith("/PKG-INFO"))]
    metadata = email.message_from_bytes(payload[metadata_name])
    inventory[kind] = {"archive": str(wheel if kind == "wheel" else sdist),
                       "sha256": digest((wheel if kind == "wheel" else sdist).read_bytes()),
                       "size_bytes": (wheel if kind == "wheel" else sdist).stat().st_size,
                       "file_count": len(payload), "members": sorted(payload),
                       "macos_contamination": contamination, "bytecode": caches,
                       "source_matches": source_matches,
                       "metadata": {key: metadata.get_all(key) for key in (
                           "Name", "Version", "Requires-Python", "Requires-Dist", "Provides-Extra", "License-Expression")}}
    report["inventory"] = inventory
    save()
    assert not contamination, (kind, "macOS metadata found", contamination)
    assert not caches, (kind, "bytecode found", caches)
    assert metadata["Name"] == "ideal_poly_volume_toolkit"
    assert metadata["Version"] == "0.3.0"

run("wheel-target-install", [CORE_PYTHON, "-m", "pip", "install", "--no-index", "--no-deps",
                             "--no-compile", "--target", str(TARGET), str(wheel)], WORK)
probe = WORK / "installed_probe.py"
probe.write_text('''import hashlib, importlib.metadata, importlib.util, json, pathlib, sys
import numpy as np
from ideal_poly_volume_toolkit import angle_barrier as ab
from ideal_poly_volume_toolkit import variational
target = pathlib.Path(sys.argv[1]).resolve()
expected = sys.argv[2]
actual_path = pathlib.Path(ab.__file__).resolve()
assert actual_path.is_relative_to(target), actual_path
actual = hashlib.sha256(actual_path.read_bytes()).hexdigest()
assert actual == expected, (actual, expected)
points = np.array([[0.,0.],[4.,0.],[4.,3.],[0.,3.],[1.,.5]])
faces = np.array([[4,0,1],[4,1,2],[4,2,3],[4,3,0]])
base = variational.corner_angles(points, faces)
C = variational.leading_trailing_matrix(faces, [4])
r = ab.solve_angle_barrier(base, C, [-.1], epsilon=1e-4)
assert r.converged and r.centering_steps > 0 and r.path_steps > 0
assert r.minimum_angle > 0 and r.newton_decrement <= .25
assert r.conservative_gap_bound_estimate <= r.epsilon and not r.certified
assert abs(r.volume - 3.0062866417470506525) < 1e-9
fixed = ab.solve_angle_barrier(np.full((1,3), np.pi/3), np.empty((3,0)), t0=1e-310)
assert fixed.converged and fixed.finite_gap_available and fixed.gap_bound_estimate == 0
json.dumps(r.to_dict(), allow_nan=False)
result = {"module_path": str(actual_path), "module_sha256": actual,
          "python": sys.version, "sys_path": sys.path,
          "dependency_versions": {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "mpmath")},
          "torch_installed": importlib.util.find_spec("torch") is not None,
          "status": r.status, "volume": r.volume, "parameters": r.parameters,
          "centering_steps": r.centering_steps, "path_steps": r.path_steps,
          "newton_decrement": r.newton_decrement,
          "gap_bound_estimate": r.gap_bound_estimate,
          "conservative_gap_bound_estimate": r.conservative_gap_bound_estimate,
          "tiny_t0_fixed_domain_available": fixed.finite_gap_available}
pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2,allow_nan=False)+"\\n")
print(json.dumps(result,indent=2,allow_nan=False))
''')
run("installed-wheel-probe", [CORE_PYTHON, str(probe), str(TARGET), source_hashes["angle_barrier.py"],
                               str(EVIDENCE / "review-installed-wheel-probe.json")], WORK,
    {"PYTHONPATH": str(TARGET)})
report["old_core_install_after"] = original_install_hashes()
report["old_core_install_unchanged"] = report["old_core_install_before"] == report["old_core_install_after"]
report["source_hashes_after"] = {name: digest((PACKAGE / "ideal_poly_volume_toolkit" / name).read_bytes())
                                  for name in names}
report["reviewed_source_unchanged"] = report["source_hashes_before"] == report["source_hashes_after"]
save()
assert report["old_core_install_unchanged"]
assert report["reviewed_source_unchanged"]
report["all_passed"] = True
save()
print(json.dumps({"output": str(OUTPUT), "all_passed": True, "workspace": str(ROOT)}, indent=2))
