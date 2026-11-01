"""Audit every shipped positive rank-two comparison and precision observation."""
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]/"consolidated"
sys.path.insert(0, str(REPO))
from experiments.counting_mixing import numerics

data = json.loads((OUT/"reviewer-result-60-90.json").read_text())
ctx = numerics.context(120)
records = []
for run in data["numerical"]["rank_two_Gaussian"]["runs"]:
    dps = run["decimal_precision"]
    comparison_context = numerics.context(dps)
    tolerance = ctx.mpf(run["scaled_tolerance"])
    for row in run["rows"]:
        tests = [("determinant orbit sum", row["two_sign_orbit_sum"], row["k_series"]),
                 ("logarithm series", row["log_series"], row["k_series"])]
        tests.extend(("radial k="+str(orbit["positive_determinant"]), orbit["quadrature"], orbit["closed_integral"])
                     for orbit in row["radial_orbits"])
        for name, actual_text, expected_text in tests:
            actual, expected = ctx.mpf(actual_text), ctx.mpf(expected_text)
            assert expected > 0
            accepted = []
            for mutant_name, factor in (("zero", 0), ("sign", -1), ("half", ctx.mpf("0.5")), ("double", 2)):
                expected_low = comparison_context.mpf(expected_text)
                try:
                    numerics.NumericChecks(comparison_context).close(mutant_name, expected_low*factor, expected_low)
                except AssertionError:
                    pass
                else:
                    accepted.append(mutant_name)
            records.append({"dps": dps, "t": row["t"], "check": name, "positive_signal": expected_text,
                            "actual_relative_error": str(abs(actual-expected)/expected),
                            "relative_threshold_without_tail": str(tolerance*max(1, abs(actual), expected)/expected),
                            "wrong_mutants_accepted": accepted})
low, high = data["numerical"]["rank_two_Gaussian"]["runs"]
cross = []
for name, low_text in low["observations"].items():
    a, b = ctx.mpf(low_text), ctx.mpf(high["observations"][name])
    assert b > 0
    cross.append({"observation": name, "relative_difference": str(abs(a-b)/b),
                  "relative_threshold": str(ctx.mpf("1e-45")*max(1, abs(a), abs(b))/b)})
result = {"status": "revise", "comparisons_audited": len(records), "positive_cross_precision_observations": len(cross),
          "comparison_rows": records, "cross_precision_rows": cross,
          "findings": [
              "Only the 60-dps t=2 k=3 radial comparison accepts zero, sign, half and double mutants.",
              "The 60-dps t=2 k=2 radial threshold is about 9.14e-4 relative despite a much smaller actual error.",
              "All divisor/log/orbit-sum covariance rows reject these gross mutants at both precisions; the smallest covariance is about 1.49e-21, leaving about 24 relative decimal digits at 60 dps.",
              "Apply the repaired scaled or relative acceptance to all positive orbit and covariance observations; retain absolute handling of genuine zeros such as endpoint imaginary parts and removable terminal cases.",
          ]}
(OUT/"positive-signal-audit-v1.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"comparisons": len(records), "cross_precision": len(cross),
                  "rows_accepting_wrong_mutants": [r for r in records if r["wrong_mutants_accepted"]]}, indent=2))
