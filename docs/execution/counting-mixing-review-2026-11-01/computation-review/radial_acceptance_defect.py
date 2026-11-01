"""Frozen-v1 acceptance defect: tiny orbit signals pass despite relative error."""
import hashlib
import json
from pathlib import Path
import sys

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "consolidated"
sys.path.insert(0, str(REPO))
from experiments.counting_mixing import numerics

ctx = numerics.context(60)
alpha, k = 2*ctx.pi*ctx.cosh(2), 3
actual, tail = numerics.orbit_integral(ctx, alpha, k, 20)
expected = ctx.pi**2*ctx.exp(-2*alpha*k)/(alpha*k*ctx.zeta(2))
accepted = []
for name, mutant in (("zero", ctx.mpf(0)), ("wrong_sign", -expected), ("half", expected/2), ("double", 2*expected)):
    checks = numerics.NumericChecks(ctx)
    try:
        checks.close(name, mutant, expected)
    except AssertionError:
        pass
    else:
        accepted.append(name)
low = {"decimal_precision": 60, "observations": {"tiny-orbit": "0"}}
high = {"decimal_precision": 90, "observations": {"tiny-orbit": str(expected)}}
try:
    numerics.precision_comparison(low, high)
    false_precision_agreement = True
except AssertionError:
    false_precision_agreement = False
result = {
    "source_sha256": hashlib.sha256((REPO/"experiments/counting_mixing/numerics.py").read_bytes()).hexdigest(),
    "t": 2, "determinant": 3, "decimal_precision": 60,
    "actual_quadrature": str(actual), "closed_formula": str(expected),
    "absolute_error": str(abs(actual-expected)),
    "relative_error": str(abs(actual-expected)/expected),
    "reported_tail_majorant": str(tail),
    "wrong_mutants_accepted": accepted,
    "zero_low_precision_accepted_against_positive_high_precision": false_precision_agreement,
    "status": "revise" if accepted or false_precision_agreement else "defect no longer reproduced",
    "minimal_repair": "Scale exp(-2*alpha*k) out of radial quadrature; compare/observe the nonzero scaled integral, "
    "or enforce relative checks for this family. Add a small-signal regression rejecting zero, sign, and factor errors.",
}
(OUT/"radial-acceptance-defect-v1.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
