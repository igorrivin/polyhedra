"""Independent targeted review of positive-signal R1 repair; preserves all v1 evidence."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent
BASE = REVIEW.parent
REPO = BASE.parent.parent/"consolidated"
AUTHOR = BASE/"computation/revision-v2"
sys.path.insert(0, str(REPO))
from experiments.counting_mixing import numerics

counts = Counter()


def yes(group, condition):
    assert condition, group
    counts[group] += 1


def reject(group, function):
    try:
        function()
    except (AssertionError, ValueError, TypeError):
        counts[group] += 1
    else:
        raise AssertionError("Unexpected acceptance: "+group)


new = json.loads((OUT/"reviewer-result-60-90-v2.json").read_text())
author = json.loads((AUTHOR/"author-result-60-90-v2.json").read_text())
old = json.loads((REVIEW/"reviewer-result-60-90.json").read_text())
freeze = json.loads((AUTHOR/"author-freeze-manifest-v2.json").read_text())
v1_manifest = json.loads((REVIEW/"approved-manifest.json").read_text())
for row in v1_manifest["review_receipts"]:
    yes("v1_receipts_preserved", sha256((REVIEW/row["path"]).read_bytes()).hexdigest() == row["sha256"])
yes("v1_withheld_decision_preserved", v1_manifest["approved"] is False and v1_manifest["decision"] == "revise")
changed = []
for row in freeze["source"]["sources"]:
    canonical = (REPO/row["path"]).read_bytes()
    yes("v2_source_freeze", sha256(canonical).hexdigest() == row["sha256"])
    yes("v2_source_freeze", canonical == (OUT/"frozen-source"/row["path"]).read_bytes())
    if canonical != (REVIEW/"frozen-v1"/row["path"]).read_bytes():
        changed.append(row["path"])
yes("bounded_source_delta", changed == [row["path"] for row in freeze["changed_source_files"]])

exclusions = {"/generated_at_utc", "/elapsed_seconds", "/source/git_dirty", "/source/git_status_porcelain",
              "/source_at_completion/git_dirty", "/source_at_completion/git_status_porcelain"}
excluded, differences = [], []


def compare(a, b, path=""):
    if path in exclusions:
        if a != b:
            excluded.append(path)
        return
    if type(a) is not type(b):
        differences.append(path)
    elif isinstance(a, dict):
        if a.keys() != b.keys():
            differences.append(path+"/KEYS")
        for key in a.keys() & b.keys():
            compare(a[key], b[key], path+"/"+str(key))
    elif isinstance(a, list):
        if len(a) != len(b):
            differences.append(path+"/LENGTH")
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, path+"/"+str(i))
    elif a != b:
        differences.append(path)


compare(author, new)
yes("strict_author_replay_equality", differences == [])
yes("unchanged_fixture_and_exact", old["fixture"] == new["fixture"])
yes("unchanged_fixture_and_exact", old["exact"] == new["exact"])
for key in ("affine_Gaussian", "endpoint_Fourier", "terminal_family"):
    yes("unchanged_other_numerical_families", old["numerical"][key] == new["numerical"][key])

# At 120 digits, evaluate logarithms by the positive double power series,
# and radial integrals in logarithmic coordinates. Neither oracle calls the
# repaired log1p or orbit_integral implementation.
ref = numerics.context(120)
reference_cache = {}
reference_rows = []
mutation_rows = []
for old_run, new_run in zip(old["numerical"]["rank_two_Gaussian"]["runs"], new["numerical"]["rank_two_Gaussian"]["runs"]):
    digits = new_run["decimal_precision"]
    ctx = numerics.context(digits)
    tolerance = ref.power(10, -(digits-15))
    yes("positive_family_policy", new_run["observation_policy"] == "strictly_positive_relative")
    yes("positive_family_policy", len(new_run["observations"]) == 36 and new_run["check_count"] == 32)
    comparisons = []
    for before, row in zip(old_run["rows"], new_run["rows"]):
        yes("unchanged_divisor_and_orbit_series", before["k_series"] == row["k_series"])
        yes("unchanged_divisor_and_orbit_series", before["two_sign_orbit_sum"] == row["two_sign_orbit_sum"])
        time = Fraction(row["t"])
        t = ref.mpf(time.numerator)/time.denominator
        c = (ref.exp(t)+ref.exp(-t))/2
        alpha = 2*ref.pi*c
        q = ref.exp(-4*ref.pi*c)
        prefactor = ref.pi/(ref.zeta(2)*c)
        if row["t"] not in reference_cache:
            log_ref = prefactor*sum(sum((q**n)**m/m for m in range(1, 41)) for n in range(1, 25))
            k_ref = prefactor*sum(ref.mpf(sum(d for d in range(1, k+1) if k % d == 0))/k*q**k for k in range(1, 25))
            reference_cache[row["t"]] = (log_ref, k_ref)
        log_ref, k_ref = reference_cache[row["t"]]
        for field, expected in (("k_series", k_ref), ("log_series", log_ref), ("two_sign_orbit_sum", k_ref)):
            actual = ref.mpf(row[field])
            error = abs(actual-expected)/expected
            yes("independent_positive_series", error < tolerance)
            reference_rows.append({"dps": digits, "t": row["t"], "field": field, "relative_error": str(error)})
        comparisons += [("orbit_sum", row["two_sign_orbit_sum"], row["k_series"], "0"),
                        ("log_series", row["log_series"], row["k_series"],
                         str(ref.mpf(row["analytic_k_tail_majorant"])+ref.mpf(row["analytic_log_tail_majorant"])))]
        for orbit in row["radial_orbits"]:
            k = orbit["positive_determinant"]
            key = (row["t"], k)
            if key not in reference_cache:
                radial = 2*ref.sqrt(k)*ref.quad(lambda s: ref.cosh(s)*ref.exp(-4*alpha*k*ref.sinh(s)**2),
                                              [0, ref.mpf("0.25"), 1, 4])
                reference_cache[key] = 2*ref.pi*ref.sqrt(ref.pi/alpha)/(k*ref.zeta(2))*radial
            scaled_ref = reference_cache[key]
            amplitude = ref.exp(-2*alpha*k)
            unscaled_ref = scaled_ref*amplitude
            for field, expected in (("scaled_quadrature", scaled_ref), ("quadrature", unscaled_ref)):
                error = abs(ref.mpf(orbit[field])-expected)/expected
                yes("independent_transformed_radial", error < tolerance)
                reference_rows.append({"dps": digits, "t": row["t"], "k": k, "field": field, "relative_error": str(error)})
            cutoff = orbit["scaled_radial_cutoff_U"]
            haar = 2*ref.pi*ref.sqrt(ref.pi/alpha)/(k*ref.zeta(2))
            # This expression avoids scaled-tail/amplitude cancellation entirely.
            unscaled_tail_ref = haar*ref.exp(-cutoff**2)/(2*ref.sqrt(alpha)*cutoff)
            for field, expected in (("analytic_omitted_radial_tail_majorant", unscaled_tail_ref),
                                    ("scaled_analytic_omitted_radial_tail_majorant", unscaled_tail_ref/amplitude)):
                yes("independent_tail_accounting", abs(ref.mpf(orbit[field])-expected)/expected < tolerance)
            yes("independent_tail_accounting", ref.mpf(orbit["analytic_omitted_radial_tail_majorant"])/unscaled_ref < tolerance)
            yes("independent_tail_accounting", abs(ref.mpf(orbit["exponential_amplitude"])-amplitude)/amplitude < tolerance)
            comparisons += [("unscaled_radial", orbit["quadrature"], orbit["closed_integral"], orbit["analytic_omitted_radial_tail_majorant"]),
                            ("scaled_radial", orbit["scaled_quadrature"], orbit["scaled_closed_integral"], orbit["scaled_analytic_omitted_radial_tail_majorant"])]
    yes("whole_positive_comparison_coverage", len(comparisons) == new_run["check_count"])
    for name, actual_text, expected_text, tail_text in comparisons:
        expected = ctx.mpf(expected_text)
        factors = (ctx.mpf(0), ctx.mpf(-1), ctx.mpf("0.5"), ctx.mpf(2), 1+ctx.power(10, -(digits-25)))
        for factor in factors:
            reject("positive_formula_mutants", lambda expected=expected, factor=factor, tail_text=tail_text:
                   numerics.PositiveNumericChecks(ctx).close("independent mutant", factor*expected, expected,
                                                           analytic_tail_allowance=ctx.mpf(tail_text)))
        mutation_rows.append({"dps": digits, "kind": name, "five_mutants_rejected": True})
    for residual in new_run["residuals"]:
        yes("reported_tail_budget", ref.mpf(residual["relative_analytic_tail_allowance"]) <= tolerance)
        yes("reported_relative_acceptance", ref.mpf(residual["relative_residual"]) <= tolerance+ref.mpf(residual["relative_analytic_tail_allowance"]))

low, high = new["numerical"]["rank_two_Gaussian"]["runs"]
comparison = numerics.precision_comparison(low, high)
yes("precision_policy", comparison["observation_policy"] == "strictly_positive_relative")
yes("precision_policy", comparison["comparison_count"] == 36)
for side in (0, 1):
    for key in low["observations"]:
        for factor in (ref.mpf(0), ref.mpf(-1), ref.mpf("0.5"), ref.mpf(2), 1+ref.mpf("1e-35")):
            changed = deepcopy([low, high])
            changed[side]["observations"][key] = str(ref.mpf(changed[side]["observations"][key])*factor)
            reject("positive_precision_mutants", lambda changed=changed: numerics.precision_comparison(*changed))
ctx = numerics.context(90)
for actual, expected, tail in ((0, 1, 0), (1, 0, 0), (-1, 1, 0), (1, -1, 0), (ctx.nan, 1, 0),
                               (1, ctx.inf, 0), (1, 1, ctx.inf), (1, 1, ctx.nan), (1, 1, -1)):
    reject("positive_comparison_domains", lambda actual=actual, expected=expected, tail=tail:
           numerics.PositiveNumericChecks(ctx).close("domain", actual, expected, analytic_tail_allowance=tail))
for value in (0, -1, ctx.nan, ctx.inf):
    reject("positive_observation_domains", lambda value=value: numerics.PositiveNumericChecks(ctx).observe("domain", value))
for policy in (None, "unknown", "absolute_floor_one"):
    changed = deepcopy(low)
    changed["observation_policy"] = policy
    reject("cross_precision_policy_domains", lambda changed=changed: numerics.precision_comparison(changed, high))
for alpha, k, cutoff in ((0, 1, 20), (-1, 1, 20), (ctx.nan, 1, 20), (ctx.inf, 1, 20),
                         (2, 0, 20), (2, 11, 20), (2, True, 20), (2, 1, 1), (2, 1, 51), (100, 1, 2)):
    reject("radial_domain_refusal", lambda alpha=alpha, k=k, cutoff=cutoff: numerics.orbit_integral(ctx, alpha, k, cutoff, scaled=True))
# Non-negligible tail: verify direction and size, then ensure its broad bound cannot mask inaccuracy.
scaled, tail = numerics.orbit_integral(ctx, ctx.mpf(2), 1, 3, scaled=True)
full = ctx.pi**2/(2*ctx.zeta(2))
yes("visible_radial_tail", 0 < full-scaled < tail)
reject("tail_budget_enforced", lambda: numerics.PositiveNumericChecks(ctx).close("wide tail", scaled, full, analytic_tail_allowance=tail))
# Directly exercise budget semantics on signals far below any absolute floating tolerance.
tiny = ctx.mpf("1e-1000")
tol = ctx.mpf("1e-75")
checks = numerics.PositiveNumericChecks(ctx)
checks.close("strict budget", tiny*(1+tol/2), tiny)
checks.close("separate analytic budget", tiny*(1+tol*ctx.mpf("1.5")), tiny, analytic_tail_allowance=tiny*tol*ctx.mpf("0.75"))
yes("tail_budget_enforced", len(checks.residuals) == 2)
reject("tail_budget_enforced", lambda: checks.close("oversized allowance", tiny, tiny, analytic_tail_allowance=2*tiny*tol))
reject("tail_budget_enforced", lambda: checks.close("outside both budgets", tiny*(1+3*tol), tiny, analytic_tail_allowance=tiny*tol/2))
# The old genuine-zero behavior is retained.
zeros = []
for digits in (60, 90):
    z = numerics.NumericChecks(numerics.context(digits))
    z.close("zero", 0, 0)
    z.observe("zero", 0)
    zeros.append(z.result())
yes("genuine_zero_policy", numerics.precision_comparison(*zeros)["maximum_scaled_difference"] == "0.0")
# Valid extremes of shipped validation precision and time domains.
for digits in (40, 120):
    edge = numerics.rank_two_checks(numerics.context(digits), [-2, 0, 2], 20, [1, 3])
    yes("bounded_domain_edges", edge["check_count"] == 18 and len(edge["observations"]) == 21)

historical = json.loads((REVIEW/"historical-inventory-before.json").read_text())
for row in historical:
    yes("historical_files_unchanged", sha256((REPO/row["path"]).read_bytes()).hexdigest() == row["sha256"])
result = {
    "decision": "approve", "R1_resolved": True, "assertion_count": sum(counts.values()),
    "assertions_by_group": dict(counts), "changed_source_files": changed if isinstance(changed, list) else [r["path"] for r in freeze["changed_source_files"]],
    "strict_scientific_comparison": {"declared_exclusions": sorted(exclusions), "actual_excluded_differences": excluded, "differences": differences},
    "independent_reference_precision": 120, "independent_reference_rows": reference_rows,
    "whole_positive_family_mutation_rows": mutation_rows,
    "cross_precision_result": comparison,
    "evidence_limit": "Independent transformed quadrature and positive double series share mpmath; no interval or quadrature-error certificate.",
}
(OUT/"independent-delta-results.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"decision": result["decision"], "assertions": sum(counts.values()),
                  "formula_mutants_rejected": counts["positive_formula_mutants"], "precision_mutants_rejected": counts["positive_precision_mutants"],
                  "scientific_differences": len(differences)}))
