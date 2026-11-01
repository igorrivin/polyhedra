"""Preserve the parser patch and verify repaired512 scientific equivalence."""
import copy
import difflib
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
CAMPAIGN_EVIDENCE = HERE.parent
WORKSPACE = HERE.parents[3]
SOURCE = WORKSPACE / "consolidated/experiments/torus_campaign"
PYTHON = "/tmp/polyhedra-baseline-20261031/bin/python"


def digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save_json(name, value):
    with (HERE / name).open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


manifest = {}
patch = []
for relative in ("campaign.cpp", "run.py", "README.md", "tests/test_campaign.py"):
    path = SOURCE / relative
    data = path.read_bytes()
    manifest[relative] = sha256(data).hexdigest()
    before = (HERE / "before" / relative).read_text()
    patch.extend(difflib.unified_diff(before.splitlines(keepends=True), data.decode().splitlines(keepends=True),
                 fromfile="a/experiments/torus_campaign/"+relative,
                 tofile="b/experiments/torus_campaign/"+relative))
    target = HERE / "after-final" / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as stream:
        stream.write(data)
with (HERE / "parser-repair-final.patch").open("x") as stream:
    stream.write("".join(patch))
save_json("after-final-source-sha256.json", manifest)

before_cpp = (HERE / "before/campaign.cpp").read_text()
after_cpp = (SOURCE / "campaign.cpp").read_text()
assert before_cpp.split("void write_text(", 1)[0] == after_cpp.split("void write_text(", 1)[0]
assert before_cpp.split("    File identities(", 1)[1] == after_cpp.split("    File identities(", 1)[1]
assert digest(HERE / "before/run.py") == digest(SOURCE / "run.py")

preflight = HERE / "preflight512-v3-final"
commands = [
    [PYTHON, "-m", "unittest", "discover", "-s", str(SOURCE / "tests"), "-v"],
    ["/opt/anaconda3/bin/ruff", "--version"],
    ["/opt/anaconda3/bin/ruff", "check", str(SOURCE / "run.py"), str(SOURCE / "tests/test_campaign.py")],
    [PYTHON, str(SOURCE / "run.py"), "--cutoff", "512", "--output-dir", str(preflight)],
]
receipts = []
for command in commands:
    start = time.perf_counter()
    completed = subprocess.run(command, capture_output=True, text=True)
    receipts.append({"argv": command, "returncode": completed.returncode,
                     "elapsed_seconds": time.perf_counter()-start,
                     "stdout": completed.stdout, "stderr": completed.stderr})
    print(json.dumps({"command": command, "returncode": completed.returncode}), flush=True)
    if completed.returncode:
        break
save_json("verification-final-receipts.json", receipts)
assert all(r["returncode"] == 0 for r in receipts)
assert all(digest(SOURCE / name) == h for name, h in manifest.items())

review = WORKSPACE / "execution/counting-mixing-review-2026-11-01/arithmetic-review"
probes = []
for probe in json.loads((review / "malformed-probes.json").read_text()):
    command = probe["argv"][:]
    command[0] = str(preflight / "torus_campaign")
    output = HERE / ("rejected-"+probe["case"]+".json")
    command[4] = str(output)
    completed = subprocess.run(command, cwd=WORKSPACE, capture_output=True, text=True)
    probes.append({"case": probe["case"], "argv": command, "returncode": completed.returncode,
                   "stdout": completed.stdout, "stderr": completed.stderr, "result_created": output.exists()})
output = HERE / "rejected-directory.json"
command = [str(preflight / "torus_campaign"), "metrics", str(review), "1", str(output), "1e-6", "1"]
completed = subprocess.run(command, capture_output=True, text=True)
probes.append({"case": "directory_input", "argv": command, "returncode": completed.returncode,
               "stdout": completed.stdout, "stderr": completed.stderr, "result_created": output.exists()})
save_json("malformed-probes-final.json", probes)
assert all(p["returncode"] != 0 and not p["result_created"] for p in probes)

old_path = CAMPAIGN_EVIDENCE / "preflight512-v2/result.json"
new_path = preflight / "result.json"
old, new = (json.loads(p.read_text()) for p in (old_path, new_path))


def scientific_report(report):
    normalized = copy.deepcopy(report)
    for key in ("provenance", "command_receipts", "elapsed_seconds"):
        normalized.pop(key)
    for surface in normalized["surfaces"]:
        for key in ("raw_peak_rss", "peak_rss_bytes", "timing_seconds",
                    "validation_and_native_elapsed_seconds", "raw_native_report"):
            surface.pop(key)
        for raw in surface["raw_streams"]:
            raw["path"] = Path(raw["path"]).name
    return normalized


assert scientific_report(old) == scientific_report(new), "scientific preflight field mismatch"
stream_checks = []
for before, after in zip(old["surfaces"], new["surfaces"]):
    native_before = json.loads(Path(before["raw_native_report"]["path"]).read_text())
    native_after = json.loads(Path(after["raw_native_report"]["path"]).read_text())
    for native in (native_before, native_after):
        native.pop("raw_peak_rss")
        native.pop("timing_seconds")
    assert native_before == native_after, "native scientific field mismatch"
    for first, second in zip(before["raw_streams"], after["raw_streams"]):
        assert first["sha256"] == second["sha256"]
        assert digest(Path(first["path"])) == first["sha256"]
        assert digest(Path(second["path"])) == second["sha256"]
        stream_checks.append({"name": Path(first["path"]).name, "sha256": first["sha256"],
                              "v2_and_parser_repair_identical": True})

freeze = CAMPAIGN_EVIDENCE / "v1-v2-comparison-and-author-freeze.json"
assert digest(freeze) == "d2630a4ad4a29facb3b70ff1028fb7e839893c6cfd4cd82e63eeb1dad49e1bb7"
previous = json.loads(freeze.read_text())
for key in ("old_report", "new_report"):
    assert digest(Path(previous[key]["path"])) == previous[key]["sha256"]
assert digest(WORKSPACE / "consolidated/artifacts/section30/result.json") == "762b07184f76893c810f3e9832fd44dc7e4b292c1a64aae61aa26832e02884a1"
summary = {
    "checks_passed": True,
    "scope": "CLI token/flag and input-read rejection only; scientific routines unchanged",
    "all_native_arithmetic_and_traversal_function_source_bytes_unchanged": True,
    "all_native_campaign_enumeration_and_sample_selection_source_bytes_unchanged": True,
    "python_driver_source_bytes_unchanged": True,
    "all_512_scientific_report_fields_identical_to_v2": True,
    "all_512_native_scientific_fields_identical_to_v2": True,
    "allowed_comparison_differences": ["source/compiler provenance", "command/output paths", "timings", "peak RSS"],
    "all_six_review_failure_probes_rejected_without_results": True,
    "tests_passed": 13, "ruff_passed": True,
    "full_v1_v2_reports_and_freeze_unchanged": True,
    "frozen64_result_unchanged": True,
    "new_source_sha256": manifest,
    "v2_preflight": {"path": str(old_path), "sha256": digest(old_path)},
    "repaired_preflight": {"path": str(new_path), "sha256": digest(new_path)},
    "patch_sha256": digest(HERE / "parser-repair-final.patch"),
    "streams": stream_checks,
    "full_replay_status": "not rerun for parser-only repair; final clean-source8192 replay remains required",
}
save_json("verification-final-summary.json", summary)
print(json.dumps({"checks_passed": True, "scientific_fields_identical_to_v2": True,
                  "source_sha256": manifest}), flush=True)
