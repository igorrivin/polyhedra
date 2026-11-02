"""Audit the driver-only repair and compare all scientific strings exactly."""

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import re


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[3]/"consolidated"
REVIEW = BASE.parents[1]/"computation-review"


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def write_new(name, value):
    with (BASE/name).open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def string_count(value):
    if isinstance(value, str):
        return 1
    if isinstance(value, dict):
        return sum(string_count(item) for item in value.values())
    if isinstance(value, list):
        return sum(string_count(item) for item in value)
    return 0


def main():
    previous_path = BASE.parent/"full-v1/author-result-70-110.json"
    current_path = BASE/"author-result-70-110.json"
    previous = json.loads(previous_path.read_text())
    current = json.loads(current_path.read_text())
    freeze = json.loads((BASE/"source-freeze.json").read_text())
    review = json.loads((REVIEW/"review-v1.json").read_text())
    if not current["source_before"] == current["source_after"] == freeze["source"]:
        raise ValueError("full before/after source observations do not equal the freeze")
    for row in freeze["preserved_prior_author_evidence"]:
        if digest(ROOT/row["path"]) != row["sha256"]:
            raise ValueError("preserved author evidence changed: "+row["path"])
    reviewer_inventory = json.loads((REVIEW/"review-v1-evidence-manifest.json").read_text())["files"]
    for name, row in reviewer_inventory.items():
        if digest(REVIEW/name) != row["sha256"]:
            raise ValueError("preserved reviewer evidence changed: "+name)
    old_map = {row["path"]: row for row in previous["source_before"]["sources"]
               + previous["source_before"]["guarded_dependencies"]}
    new_map = {row["path"]: row for row in current["source_before"]["sources"]
               + current["source_before"]["guarded_dependencies"]}
    changed = []
    for path in sorted(set(old_map) | set(new_map)):
        if old_map.get(path) != new_map.get(path):
            changed.append({"path": path, "before": old_map.get(path), "after": new_map.get(path)})
    expected_changed = {"experiments/quantum_geodesics/run.py", "experiments/quantum_geodesics/README.md",
                        "experiments/quantum_geodesics/tests/test_validation.py"}
    if {row["path"] for row in changed} != expected_changed:
        raise ValueError("repair changed an unapproved runtime source")
    for path, row in new_map.items():
        if digest(ROOT/path) != row["sha256"]:
            raise ValueError("current runtime bytes differ from completed run: "+path)
    for field in ("fixture", "groups", "check_counts"):
        if canonical(previous[field]) != canonical(current[field]):
            raise ValueError("scientific data changed: "+field)
    per_group = {name: {"canonical_sha256": sha256(canonical(group)).hexdigest(),
                        "strings_compared_exactly": string_count(group)}
                 for name, group in current["groups"].items()}
    counts = {"exact": 0, "numerical_formula_comparisons": 0, "cross_precision_observations": 0}
    for group in current["groups"].values():
        if "exact" in group:
            size = len(group["exact"]["records"])
            if size != group["exact"]["check_count"]:
                raise ValueError("exact record count mismatch")
            counts["exact"] += size
        if "numerical" in group:
            for run in group["numerical"]["runs"]:
                size = len(run["records"])
                if size != run["check_count"]:
                    raise ValueError("floating record count mismatch")
                counts["numerical_formula_comparisons"] += size
            cross = group["numerical"]["cross_precision"]
            if len(cross["records"]) != cross["comparison_count"]:
                raise ValueError("precision record count mismatch")
            counts["cross_precision_observations"] += len(cross["records"])
    if counts != current["check_counts"]:
        raise ValueError("derived counts differ from report")
    # Enumerate allowed metadata differences, then require every other field to agree.
    old_rest, new_rest = deepcopy(previous), deepcopy(current)
    differences = []
    paths = [("generated_at_utc",), ("runtime", "elapsed_seconds")]
    for stage in ("source_before", "source_after"):
        paths += [(stage, field) for field in ("sources", "source_set_sha256", "git_status_porcelain")]
    for path in paths:
        left, right = old_rest, new_rest
        for key in path[:-1]:
            left, right = left[key], right[key]
        old_value, new_value = left.pop(path[-1]), right.pop(path[-1])
        if canonical(old_value) != canonical(new_value):
            row = {"path": "/"+"/".join(path)}
            if path[-1] == "sources":
                row.update(before_entries=len(old_value), after_entries=len(new_value),
                           detail="exact per-file before/after identities are recorded in changed_runtime_files")
            else:
                row.update(before=old_value, after=new_value)
            differences.append(row)
    if canonical(old_rest) != canonical(new_rest):
        raise ValueError("an unenumerated scientific or metadata field changed")
    fixture_path = "experiments/quantum_geodesics/fixture.json"
    comparison = {
        "status": "author CR01/CR02 repair comparison passed; targeted independent recheck still required",
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "previous_result_sha256": digest(previous_path), "current_result_sha256": digest(current_path),
        "source_freeze_sha256": digest(BASE/"source-freeze.json"),
        "source_set_sha256": current["source_before"]["source_set_sha256"],
        "scientific_fixture_and_all_groups_exactly_equal": True,
        "scientific_comparison_method": "Canonical JSON bytes and every nested string compared exactly; huge-exponent strings are never numerically parsed or rounded.",
        "fixture_file_sha256_unchanged": new_map[fixture_path]["sha256"],
        "scientific_profile_sha256": freeze["scientific_profile_sha256"],
        "provenance_profile_sha256": freeze["provenance_profile_sha256"],
        "per_group": per_group, "derived_check_counts": counts,
        "all_other_result_fields_equal_after_enumerated_metadata_removal": True,
        "enumerated_result_differences": differences, "changed_runtime_files": changed,
        "runtime_file_count_before": len(old_map), "runtime_file_count_after": len(new_map),
        "all_mathematical_modules_and_local_provenance_copies_unchanged": True,
        "all_guarded_existing_dependency_files_unchanged": True,
        "full_source_before_after_freeze_equal": True,
        "preserved_prior_author_and_reviewer_evidence_unchanged": True,
        "reused_alternate_oracle_evidence": {
            "status": "v1 independent evidence preserved and eligible for reuse by unchanged fixture/math hashes; not a fresh oracle run",
            "script_sha256": review["independent_oracles"]["script"]["sha256"],
            "result_sha256": review["independent_oracles"]["result"]["sha256"],
            "exact_checks": review["independent_oracles"]["exact"],
            "numerical_checks": review["independent_oracles"]["numerical"]}}
    write_new("scientific-comparison.json", comparison)
    write_new("runtime-file-map.json", {"status": "full-v2 runtime identity; independent acceptance separate",
              "source_set_sha256": current["source_before"]["source_set_sha256"],
              "file_count": len(new_map), "files": {path: row["sha256"] for path, row in new_map.items()}})
    tests = {}
    for filename in ("tests.log", "tests-optimized.log"):
        content = (BASE/filename).read_text()
        match = re.search(r"Ran (\d+) tests", content)
        if not match or not content.rstrip().endswith("OK"):
            raise ValueError("test log does not record success: "+filename)
        tests[filename] = int(match.group(1))
    commands = [
        {"argv": ["/tmp/polyhedra-baseline-20261031/bin/python", "-m", "unittest", "discover", "-s", "experiments/quantum_geodesics/tests", "-v"],
         "cwd": str(ROOT), "exit_code": 0, "log": "tests.log"},
        {"argv": ["/tmp/polyhedra-baseline-20261031/bin/python", "-O", "-m", "unittest", "discover", "-s", "experiments/quantum_geodesics/tests", "-v"],
         "cwd": str(ROOT), "exit_code": 0, "log": "tests-optimized.log"},
        {"argv": ["/opt/anaconda3/bin/ruff", "check", "experiments/quantum_geodesics"], "cwd": str(ROOT), "exit_code": 0, "log": "ruff.log"},
        {"argv": ["/tmp/polyhedra-baseline-20261031/bin/python", "-O", str(ROOT/"experiments/quantum_geodesics/run.py"), "--output", str(current_path)],
         "cwd": "/private/tmp", "exit_code": 0, "log": "author-run.log"}]
    write_new("command-receipts.json", {"status": "author driver repair tests and fresh full run passed; no independent approval claimed",
              "recorded_at_utc": datetime.now(timezone.utc).isoformat(), "commands": commands,
              "tests_from_logs": tests, "check_counts_from_records": counts, "runtime": current["runtime"],
              "source_set_sha256": current["source_before"]["source_set_sha256"],
              "result_sha256": digest(current_path), "comparison_sha256": digest(BASE/"scientific-comparison.json")})
    print(json.dumps({"result_sha256": digest(current_path), "comparison_sha256": digest(BASE/"scientific-comparison.json"),
                      "runtime_file_map_sha256": digest(BASE/"runtime-file-map.json"),
                      "command_receipts_sha256": digest(BASE/"command-receipts.json"), "runtime_files": len(new_map),
                      "tests": tests, "changed_runtime_paths": sorted(expected_changed),
                      "enumerated_difference_paths": [row["path"] for row in differences]}, indent=2))


if __name__ == "__main__":
    main()
