"""Strict provenance/scientific comparison for the later clean-source full run.

Only rows[*].elapsed_seconds and independent_double_sine_checks[*].elapsed_seconds
are omitted inside scientific result sections. Shared check records must match
exactly by name. The one added direct-D record is validated separately.
Run metadata is compared or reported explicitly, not generically discarded.
"""

import argparse
import copy
from fractions import Fraction
import hashlib
import json
from pathlib import Path

import mpmath as mp


ADDED_CHECK = "D_alternate_method_and_panels_argument_3"


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--approved", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite")
    old, new, approved = [json.loads(path.read_text()) for path in
                          (args.baseline, args.candidate, args.approved)]
    require(set(old) == set(new), "unexpected added or removed top-level field")
    require(old["status"] == new["status"] == "all_declared_checks_passed", "run status")
    require(old["profile"] == new["profile"] == "full", "both profiles must be full")
    require(len(old["rows"]) == len(new["rows"]) == 21, "21 rows required")
    require(len(old["comparisons"]) == len(new["comparisons"]) == 7, "7 comparisons required")
    old_rows, new_rows = copy.deepcopy(old["rows"]), copy.deepcopy(new["rows"])
    for rows in (old_rows, new_rows):
        for row in rows:
            del row["elapsed_seconds"]
    require(old_rows == new_rows, "scientific rows differ after excluding only elapsed_seconds")
    require(old["comparisons"] == new["comparisons"], "precision/contour comparisons differ")

    shared_counts, added = [], []
    old_checks = {x["working_dps"]: x for x in old["independent_double_sine_checks"]}
    new_checks = {x["working_dps"]: x for x in new["independent_double_sine_checks"]}
    require(set(old_checks) == set(new_checks) == {40, 60}, "40/60 dps component checks required")
    with mp.workdps(110):
        for dps in (40, 60):
            before, after = old_checks[dps], new_checks[dps]
            require(set(before) == set(after), "component container fields changed")
            require(before["evidence_status"] == after["evidence_status"], "component evidence status differs")
            by_name = {x["name"]: x for x in after["records"]}
            require(len(by_name) == len(after["records"]) == 28, "new check names must be unique")
            require(len(before["records"]) == 27, "baseline needs27 shared records")
            require(set(by_name) == {x["name"] for x in before["records"]} | {ADDED_CHECK},
                    "unexpected added or removed check")
            for record in before["records"]:
                require(record == by_name[record["name"]], "shared check differs: " + record["name"])
            extra = by_name[ADDED_CHECK]
            threshold = mp.mpf(extra["threshold"])
            residual = mp.mpf(extra["absolute_residual"])
            details = extra["details"]
            error = mp.mpf(details["quadrature_error_estimate"])
            require(all(mp.isfinite(x) for x in (threshold, residual, error)), "nonfinite new check")
            require(0 <= residual < threshold and 0 <= error < threshold, "new check threshold")
            require(details["method"] == "tanh-sinh", "new method")
            require(details["integration_domain"] == ["0", "infinity"], "new integration domain")
            require(details["panels"] == [0, "1/2"] + [2**k for k in range(15)] + ["infinity"],
                    "new panel layout")
            require(details["tail_cutoff"] == 8192 and details["tail_strip_epsilon_exact"] == "1/50",
                    "new tail specification")
            require("not an omitted-tail error" in details["tail_bound_role"], "new tail role")
            expected_bound = Fraction(1, 80)**2 / (6*Fraction(1, 50)*2**327)
            require(Fraction(details["direct_D_tail_bound_exact"]) == expected_bound, "new exact tail bound")
            real_z = mp.mpf(details["z"]["real"])
            require(min(real_z, 1-real_z) > mp.mpf(1)/50, "new numerical strip check")
            shared_counts.append({"dps": dps, "identical_named_records": 27})
            added.append(extra)

    # Every unchanged top-level scientific convention remains byte-for-byte equal.
    old_conventions, new_conventions = dict(old["conventions"]), dict(new["conventions"])
    direct_convention = new_conventions.pop("direct_D_quadrature")
    require(old_conventions == new_conventions, "existing conventions differ")
    for key in ("schema_version", "runtime", "sources", "limitations"):
        require(old[key] == new[key], "unexpected top-level change: " + key)
    start, finish = new["source_at_start"], new["source_at_finish"]
    require(set(start) == set(finish) == {"commit", "dirty_status", "sha256"}, "source snapshot fields")
    require(set(start["sha256"]) == set(old["source_at_start"]["sha256"]), "declared source set changed")
    require(start["commit"] == finish["commit"], "candidate HEAD drift")
    require(start["sha256"] == finish["sha256"], "candidate source drift")
    require(start["dirty_status"] == finish["dirty_status"] == "", "candidate source run is not clean")
    for name, digest in approved["approved_code_sha256"].items():
        require(start["sha256"][name] == digest, "candidate code not at approved hash: " + name)
    for name in ("experiments/section15/historical-table.json", "book/chapters/14-normalized-quantum-comparison.tex"):
        require(start["sha256"][name] == old["source_at_start"]["sha256"][name], "preserved source changed")
    require(start["sha256"]["book/chapters/15-quantum-airy.tex"] ==
            approved["review_context_sha256"]["book/chapters/15-quantum-airy.tex"], "chapter source differs")
    report = {
        "status": "clean_full_run_scientific_comparison_passed",
        "input_sha256": {"baseline": sha(args.baseline), "candidate": sha(args.candidate), "approval": sha(args.approved)},
        "candidate_commit": start["commit"], "candidate_sources_clean_and_stable": True,
        "identical_scientific_rows": 21, "identical_comparisons": 7,
        "shared_component_checks": shared_counts, "added_component_checks_validated_separately": added,
        "excluded_scientific_JSON_paths": ["rows[*].elapsed_seconds", "independent_double_sine_checks[*].elapsed_seconds"],
        "expected_metadata_changes": {
            "created_at_utc": {"baseline": old["created_at_utc"], "candidate": new["created_at_utc"]},
            "elapsed_seconds": {"baseline": old["elapsed_seconds"], "candidate": new["elapsed_seconds"]},
            "source_at_start_and_finish": "candidate clean, stable, and matched to approved code/chapter hashes; baseline retained separately",
            "conventions.direct_D_quadrature": direct_convention,
        },
        "limitations": "Exact equality of these finite numerical records is not an interval certificate or a proof of the global asymptotic.",
        "comparison_script_sha256": sha(Path(__file__)),
    }
    with args.output.open("x") as output:
        output.write(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({k: report[k] for k in ("status", "candidate_commit", "identical_scientific_rows", "identical_comparisons", "shared_component_checks")}, indent=2))


if __name__ == "__main__":
    main()
