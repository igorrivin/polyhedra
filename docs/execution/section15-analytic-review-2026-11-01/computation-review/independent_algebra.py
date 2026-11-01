"""Finite symbolic reference checks, without importing author code."""

import hashlib
import json
from fractions import Fraction
from math import factorial
from pathlib import Path

import sympy as sp


b, w, alpha, q, s, a, lam = sp.symbols("b w alpha q s a lambda", positive=True)
weights = (4, 3, 1, 2, -6)
xs = (w - 3*alpha, 4*alpha-w, 2*q-w, 3*alpha-b, alpha)
aa = [sp.expand(b*(q-2*x)).subs(q, b+1/b).expand() for x in xs]
linear = sp.factor(sum(k*x for k, x in zip(weights, aa)))
assert linear == 4*b**2
normalization = sp.simplify(4*b/(3*lam) * lam/(6*sp.pi*b))
assert normalization == 2/(9*sp.pi)

c1, c2, c3, u = sp.symbols("c1 c2 c3 u")
denominator = (1+c1**2*u)*(1+c2**2*u)*(1+c3**2*u)
psi_prime = 4*c1/(1+c1**2*u) + 3*c2/(1+c2**2*u) + c3/(1+c3**2*u)
tail_numerator = sp.Poly(sp.cancel(psi_prime*denominator), u)

origin_kernel = (sp.sinh(a*s)/(2*sp.sinh(s)*sp.sinh(b**2*s)) - a/(2*b**2*s))/s
origin_limit = sp.simplify(sp.limit(origin_kernel, s, 0))
assert sp.simplify(origin_limit - a*(a**2-1-b**4)/(12*b**2)) == 0
tail_subtraction = sp.integrate(-a/(2*b**2*s**2), (s, 16, sp.oo))
assert tail_subtraction == -a/(32*b**2)

x, c = sp.symbols("x c")
csch_series = sp.series(1/sp.sinh(x)-1/x, x, 0, 17).removeO()
csch_coefficients, cot_derivatives = [], []
for k in range(1, 9):
    actual = sp.expand(csch_series).coeff(x, 2*k-1)
    analytic = sp.simplify(2*(-1)**k*(1-sp.Integer(2)**(1-2*k))*sp.zeta(2*k)/sp.pi**(2*k))
    assert actual == analytic
    derivative = sp.diff(sp.cot(x), x, 2*k-2).expand().subs(sp.cot(x), c).expand()
    csch_coefficients.append(str(actual))
    cot_derivatives.append([str(v) for v in sp.Poly(derivative, c).all_coeffs()])

def independent_bound(bf, eps, k):
    # Substitute the analytic inequalities before simplifying; no float enters.
    h = eps**(-2*k-1) + eps**(-2*k)/(2*k)
    return bf**(4*k+2) * Fraction(2, 3**(2*k+2)) * Fraction(factorial(2*k), 2**(2*k+1)) * (2*h)

bounds = []
for k in (1, 2, 15, 22):
    bound = independent_bound(Fraction(1,80), Fraction(1,100), k)
    bounds.append({"K": k, "full_log_bound": str(16*bound),
                   "b_halving_scale": str(Fraction(1,2)**(4*k+2))})

result = {
    "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "sympy_version": sp.__version__,
    "weighted_linear_identity": str(linear), "normalization": str(normalization),
    "origin_limit": str(origin_limit), "tail_subtraction_from_16": str(tail_subtraction),
    "tail_psi_prime_numerator_coefficients_descending": [str(v) for v in tail_numerator.all_coeffs()],
    "csch_series_coefficients_1_through_8": csch_coefficients,
    "cot_even_derivative_polynomials": cot_derivatives,
    "exact_rational_log_bounds": bounds,
    "status": "all_finite_symbolic_checks_passed",
    "scope": "Finite identities and rational inequality substitutions only; no global quadrature proof.",
}
path = Path(__file__).with_name("independent-algebra-result.json")
with path.open("x") as output:
    output.write(json.dumps(result, indent=2)+"\n")
print(json.dumps(result, indent=2))
