"""Retain the v1/v2 comparison and mutation receipts without changing old evidence."""

from copy import deepcopy
from datetime import datetime, timezone
from difflib import unified_diff
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path("/Volumes/Lexar/lambda/devel/polyhedra/consolidated")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from experiments.counting_mixing import numerics, run  # noqa: E402


def write_new(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


baseline = json.loads((HERE/"baseline.json").read_text())
old_path = HERE.parent/"author-result-60-90.json"
new_path = HERE/"author-result-60-90-v2.json"
old = json.loads(old_path.read_text())
new = json.loads(new_path.read_text())
current = run.source_state()
run.verify_source_unchanged(new["source"], current)
for record in baseline["preserved_evidence"]:
    assert digest(Path(record["path"])) == record["sha256"], record["path"]

assert old["fixture"] == new["fixture"]
assert old["exact"] == new["exact"]
unaffected = sorted(set(old["numerical"])-{"rank_two_Gaussian"})
for name in unaffected:
    assert old["numerical"][name] == new["numerical"][name], name

patch, changes = [], []
for record in current["sources"]:
    relative = record["path"]
    before = HERE/"source-before"/relative
    after = ROOT/relative
    target = HERE/"source-after"/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("xb") as handle:
        handle.write(after.read_bytes())
    if before.read_bytes() != after.read_bytes():
        changes.append({"path": relative, "before_sha256": digest(before), "after_sha256": digest(after)})
        patch.extend(unified_diff(before.read_text().splitlines(keepends=True), after.read_text().splitlines(keepends=True),
                                  fromfile="a/"+relative, tofile="b/"+relative))
with (HERE/"source-before-after.patch").open("x") as handle:
    handle.writelines(patch)

ctx = numerics.context(120)
orbit_rows, log_rows = [], []
comparison_mutants_rejected = 0
for old_run, new_run in zip(old["numerical"]["rank_two_Gaussian"]["runs"], new["numerical"]["rank_two_Gaussian"]["runs"]):
    digits = new_run["decimal_precision"]
    check_ctx = numerics.context(digits)
    comparisons = []
    for before, after in zip(old_run["rows"], new_run["rows"]):
        assert before["t"] == after["t"]
        assert before["k_series"] == after["k_series"]
        assert before["two_sign_orbit_sum"] == after["two_sign_orbit_sum"]
        expected = ctx.mpf(after["k_series"])
        log_rows.append({"decimal_precision": digits, "t": after["t"],
                         "v1_log_series": before["log_series"], "v2_log_series": after["log_series"],
                         "divisor_series_unchanged": after["k_series"],
                         "v1_relative_residual": numerics.number(ctx, abs(ctx.mpf(before["log_series"])-expected)/expected),
                         "v2_relative_residual": numerics.number(ctx, abs(ctx.mpf(after["log_series"])-expected)/expected)})
        comparisons.extend([
            (f"t={after['t']} orbit sum", after["two_sign_orbit_sum"], after["k_series"], "0"),
            (f"t={after['t']} log series", after["log_series"], after["k_series"],
             numerics.number(ctx, ctx.mpf(after["analytic_k_tail_majorant"])+ctx.mpf(after["analytic_log_tail_majorant"]))),
        ])
        for previous, corrected in zip(before["radial_orbits"], after["radial_orbits"]):
            expected = ctx.mpf(corrected["closed_integral"])
            orbit_rows.append({"decimal_precision": digits, "t": after["t"],
                               "positive_determinant": corrected["positive_determinant"],
                               "v1_quadrature": previous["quadrature"], "v2_quadrature": corrected["quadrature"],
                               "closed_integral": corrected["closed_integral"],
                               "v1_relative_residual": numerics.number(ctx, abs(ctx.mpf(previous["quadrature"])-expected)/expected),
                               "v2_relative_residual": numerics.number(ctx, abs(ctx.mpf(corrected["quadrature"])-expected)/expected),
                               "scaled_quadrature": corrected["scaled_quadrature"],
                               "exponential_amplitude": corrected["exponential_amplitude"],
                               "scaled_analytic_tail_majorant": corrected["scaled_analytic_omitted_radial_tail_majorant"]})
            comparisons.extend([
                (f"t={after['t']} k={corrected['positive_determinant']} radial", corrected["quadrature"],
                 corrected["closed_integral"], corrected["analytic_omitted_radial_tail_majorant"]),
                (f"t={after['t']} k={corrected['positive_determinant']} scaled radial", corrected["scaled_quadrature"],
                 corrected["scaled_closed_integral"], corrected["scaled_analytic_omitted_radial_tail_majorant"]),
            ])
    assert len(comparisons) == new_run["check_count"]
    for label, actual, expected, tail in comparisons:
        for name, factor in (("zero", 0), ("half", check_ctx.mpf("0.5")), ("sign", -1), ("double", 2)):
            try:
                numerics.PositiveNumericChecks(check_ctx).close(
                    label, factor*check_ctx.mpf(actual), check_ctx.mpf(expected), analytic_tail_allowance=check_ctx.mpf(tail))
            except AssertionError:
                comparison_mutants_rejected += 1
            else:
                raise AssertionError(f"accepted {name} mutant: {digits} digits, {label}")

low, high = new["numerical"]["rank_two_Gaussian"]["runs"]
precision_mutants_rejected = 0
for side in ("low", "high"):
    for key in low["observations"]:
        for name, factor in (("zero", 0), ("half", ctx.mpf("0.5")), ("sign", -1), ("double", 2)):
            left, right = deepcopy(low), deepcopy(high)
            target = left if side == "low" else right
            target["observations"][key] = numerics.number(ctx, factor*ctx.mpf(target["observations"][key]))
            try:
                numerics.precision_comparison(left, right)
            except AssertionError:
                precision_mutants_rejected += 1
            else:
                raise AssertionError(f"accepted {name} precision mutant: {side}, {key}")

report = {
    "status": "author correction checks passed; independent delta review pending",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "preserved_v1_evidence_hashes_verified": baseline["preserved_evidence"],
    "fixture_strictly_identical": old["fixture"] == new["fixture"],
    "all_exact_groups_strictly_identical": old["exact"] == new["exact"],
    "strictly_identical_non_rank_two_groups": unaffected,
    "all_rank_two_divisor_and_closed_orbit_series_strings_unchanged": True,
    "changed_source_files": changes,
    "old_check_counts": old["check_counts"], "new_check_counts": new["check_counts"],
    "positive_comparison_mutants_rejected": comparison_mutants_rejected,
    "positive_cross_precision_mutants_rejected": precision_mutants_rejected,
    "positive_rank_two_comparisons": sum(row["check_count"] for row in new["numerical"]["rank_two_Gaussian"]["runs"]),
    "positive_rank_two_cross_precision_observations": len(low["observations"]),
    "orbit_rows": orbit_rows, "logarithm_cancellation_rows": log_rows,
    "rank_two_precision_comparison": new["numerical"]["rank_two_Gaussian"]["precision_comparison"],
    "coverage": "Relative acceptance and stable evaluation repair only; analytic tails remain distinct from uncertified quadrature and roundoff.",
}
write_new(HERE/"numerical-correction-evidence.json", report)
manifest = {
    "status": "author revision v2 frozen; independent delta review pending",
    "source": current, "source_before": baseline["source"],
    "result_path": str(new_path), "result_sha256": digest(new_path),
    "source_patch_sha256": digest(HERE/"source-before-after.patch"),
    "correction_evidence_sha256": digest(HERE/"numerical-correction-evidence.json"),
    "command_receipts_sha256": digest(HERE/"command-receipts.json"),
    "audit_source_sha256": digest(Path(__file__)), "changed_source_files": changes,
    "check_counts": new["check_counts"], "manuscript_hash_freeze_claimed": False,
}
write_new(HERE/"author-freeze-manifest-v2.json", manifest)
print(json.dumps({"source_set_sha256": current["source_set_sha256"], "result_sha256": manifest["result_sha256"],
                  "check_counts": new["check_counts"], "comparison_mutants_rejected": comparison_mutants_rejected,
                  "cross_precision_mutants_rejected": precision_mutants_rejected,
                  "strictly_identical_non_rank_two_groups": unaffected}, sort_keys=True))
