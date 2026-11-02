"""Q3-Q4: half-log peripheral algebra and charge/curvature factors."""

from fractions import Fraction
from hashlib import sha256
import importlib
from pathlib import Path

import sympy as sp

from .common import ExactChecks, NumericChecks, context, mpq, positive, rational, require


ROOT = Path(__file__).resolve().parents[2]


def guarded_surgery_dependency(expected_hashes):
    """Import reviewed helpers only after validating their exact current bytes."""
    required = {"experiments/quantum_surgery/__init__.py", "experiments/quantum_surgery/algebra.py",
                "experiments/quantum_surgery/exact.py"}
    if set(expected_hashes) != required:
        raise ValueError("the exact surgery dependency requires all three declared source guards")
    for path, expected in expected_hashes.items():
        actual = sha256((ROOT/path).read_bytes()).hexdigest()
        require(actual == expected, f"guarded surgery dependency changed: {path}")
    return importlib.import_module("experiments.quantum_surgery.algebra")


def validate_weights(values):
    if not isinstance(values, list) or not 3 <= len(values) <= 8:
        raise ValueError("a finite weight list of length 3 through 8 required")
    weights = list(map(rational, values))
    if any(not 0 < value < 1 for value in weights) or sum(weights) != 2:
        raise ValueError("weights must lie strictly in (0,1) and sum exactly to two")
    return weights


def peripheral_checks(fixture, dependency_hashes):
    old = guarded_surgery_dependency(dependency_hashes)
    checks, rows = ExactChecks(), []
    u, a, hbar = sp.symbols("u a hbar")
    tau, c3, c5 = map(rational, fixture["formal_v_coefficients"])
    v = tau*u+c3*u**3+c5*u**5
    phase = sp.integrate(v/2, u)
    for p, q, rho, sigma in fixture["slopes"]:
        old.validate_slope(p, q, rho, sigma)
        # Coordinate order is (v,u): db_core wedge da = det(M) dv wedge du.
        checks.equal(f"slope {p},{q}: symplectic wedge factor", sp.Integer(p*sigma-q*rho), sp.Integer(1))
        solved_v = (a-p*u)/q
        core = sp.simplify(rho*u+sigma*solved_v)
        kernel = sp.Rational(p, 4*q)*u**2-u*a/(2*q)+sp.Rational(sigma, 4*q)*a**2
        checks.equal(f"slope {p},{q}: dG/du", sp.diff(kernel, u), -solved_v/2)
        checks.equal(f"slope {p},{q}: dG/da", sp.diff(kernel, a), core/2)
        checks.equal(f"slope {p},{q}: stationary equation", sp.diff(phase+kernel, u), (p*u+q*v-a)/(2*q))
        derivative = p+q*sp.diff(v, u)
        checks.equal(f"slope {p},{q}: half-log Hessian", sp.diff(phase+kernel, u, 2), derivative/(2*q))
        checks.equal(f"slope {p},{q}: squared normalized Gaussian dependence",
                     (sp.Rational(1, 2*q))/sp.diff(phase+kernel, u, 2), 1/derivative)
        numeric_coefficients = [Fraction(int(x.p), int(x.q)) for x in (tau, c3, c5)]
        inverse = old.filling_inverse(*numeric_coefficients, p, q)
        formal_inverse = sum(sp.Rational(x.numerator, x.denominator)*a**j for j, x in enumerate(inverse))
        composition = p*formal_inverse+q*v.subs(u, formal_inverse)-a
        checks.equal(f"slope {p},{q}: guarded inverse through degree six",
                     sp.series(composition, a, 0, 7).removeO(), sp.Integer(0))
        rows.append({"basis": [p, q, rho, sigma], "G": kernel, "solved_v": solved_v, "b_core": core,
                     "formal_v": v, "phase_Phi": phase, "Hessian": derivative/(2*q),
                     "D": derivative, "u_in_a_through_degree_six": formal_inverse})
    functions = [sp.Integer(1), u, u**2+2*u-3, sp.exp(sp.Rational(2, 3)*u)]
    for index, function in enumerate(functions):
        left = (sp.exp(u/2)*function).subs(u, u+hbar)
        right = sp.exp(hbar/2)*sp.exp(u/2)*function.subs(u, u+hbar)
        checks.equal(f"shift test {index}: Weyl half factor", sp.expand_power_exp(left), sp.expand_power_exp(right))
    real_phase, volume = sp.symbols("X V", real=True)
    level = sp.Symbol("r", positive=True)
    exponent = (real_phase+sp.I*volume)/(4*sp.pi*sp.I/level)
    checks.equal("closed-filling exponential real part", sp.re(exponent), level*volume/(4*sp.pi))
    return checks.result(rows=rows, shift_functions=functions,
                         coordinates="u,v multiplier logs; m=exp(u/2); l=exp(v/2); Omega=dv wedge du/2; P=v/2",
                         dependency="fresh calls to guarded quantum_surgery.filling_inverse and validate_slope; no old result imported",
                         Gaussian_scope="squared algebraic dependence 1/D only; no branch-independent square-root identity",
                         phase_modulus="|exp((X+iV)/(4*pi*i/r))|=exp(r*V/(4*pi))")


def shift_checks(fixture, digits, guard_digits):
    ctx = context(digits, guard_digits)
    checks = NumericChecks(ctx, digits, guard_digits)
    functions = [lambda x: ctx.mpf(1), lambda x: x, lambda x: x*x+2*x-3,
                 lambda x: ctx.exp(ctx.mpf(2)*x/3)]
    rows = []
    for index, point in enumerate(fixture["shift_points"]):
        u = mpq(ctx, point["u"])
        hbar = ctx.mpc(mpq(ctx, point["hbar"][0]), mpq(ctx, point["hbar"][1]))
        require(ctx.isfinite(u) and ctx.isfinite(hbar), "finite shift coordinates required")
        for j, function in enumerate(functions):
            def multiply(x):
                return ctx.exp(x/2)*function(x)

            left = multiply(u+hbar)
            right_unweighted = ctx.exp(u/2)*function(u+hbar)
            right = ctx.exp(hbar/2)*right_unweighted
            scale = max(abs(left), abs(right))
            require(scale > 0, "selected shift test vanished")
            checks.close(f"point {index}, function {j}: explicit translation", left, right, scale=scale)
            checks.observe(f"point {index}, function {j}: modulus", abs(left), positive_signal=True)
            rows.append({"point_index": index, "function_index": j,
                         "u": point["u"], "hbar": point["hbar"]})
    return checks.result(rows=rows, formula="l_hat*m_hat(f)(u)=exp(hbar/2)*m_hat*l_hat(f)(u)",
                         analytic_tail="none: finite explicit operators")


def charge_checks(fixture):
    checks, rows = ExactChecks(), []
    for item in fixture["weights"]:
        weights = validate_weights(item["mu"])
        for squared_text in fixture["b_squared"]:
            squared = positive(squared_text)
            if squared >= 1:
                raise ValueError("charge specialization requires 0<b^2<1")
            b = sp.sqrt(squared)
            gamma, background = 2*b, b+1/b
            alpha = [weight/(2*b) for weight in weights]
            beta = [weight/b for weight in weights]
            prefix = f"{item['id']}, b^2={squared_text}"
            checks.equal(prefix+": gamma=2b", gamma, 2*b)
            for i, (al, be, weight) in enumerate(zip(alpha, beta, weights)):
                checks.equal(prefix+f": beta_{i}=2alpha_{i}", be, 2*al)
                checks.equal(prefix+f": first-moment singularity exponent {i}", gamma*be, 2*weight)
                checks.truth(prefix+f": extended first moment {i}", 1 < 1+(1-weight)/squared)
                checks.truth(prefix+f": beta_{i}<Q", sp.simplify(background-be) > 0)
            checks.equal(prefix+": screening s=-1", (sum(alpha)-background)/b, sp.Integer(-1))
            checks.equal(prefix+": gamma sum(beta)=4", gamma*sum(beta), sp.Integer(4))
            checks.equal(prefix+": Delta(b)=1", b*(background-b), sp.Integer(1))
            checks.truth(prefix+": first moment 1<b^-2", 1 < 1/squared)
            rows.append({"weights_id": item["id"], "mu": weights, "b_squared": squared, "b_positive": b,
                         "gamma": gamma, "Q": background, "alpha": alpha, "beta": beta, "s": -1,
                         "first_moment_margin_b_inverse_squared": 1/squared-1,
                         "first_moment_insertion_margins": [(1-weight)/squared for weight in weights]})
    area = sp.Symbol("A", positive=True)
    powers = []
    for dimension in (1, 2, 3):
        factor = (2/area)**dimension
        checks.equal(f"dimension {dimension}: WP exterior power", factor*(area/2)**dimension, sp.Integer(1))
        powers.append({"complex_dimension": dimension, "WP_to_CH_top_power_factor": factor,
                       "volume_form_denominator": sp.factorial(dimension)})
    # dz wedge dbar(z)=-2i dx wedge dy and f_zbarz=Delta(f)/4.
    checks.equal("curvature form conversion to real coordinates", (-2*sp.I)*(-2*sp.I)/4, sp.Integer(-1))
    return checks.result(rows=rows, exterior_powers=powers,
                         convention="all marks finite; d^2w=dx*dy; curvature -1; -2*i*partial*barpartial log; (2/A)*omega_WP -> omega_CH",
                         real_coordinate_curvature_factor="-Delta(log potential) dx wedge dy",
                         scope="exact specialization and normalization factors; no GMC construction or moduli integral")
