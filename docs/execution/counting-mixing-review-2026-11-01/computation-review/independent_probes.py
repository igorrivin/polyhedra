"""Reviewer-owned independent finite oracles and adversarial probes.

No canonical file is edited. Numerical checks are observations, not certificates.
"""
from collections import Counter
import copy
from fractions import Fraction as Q
from itertools import combinations_with_replacement, product
import json
from math import gcd, isqrt
from pathlib import Path
import random
import sys
import tempfile

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2] / "consolidated"
sys.path.insert(0, str(REPO))
from experiments.counting_mixing import algebra, arithmetic, dynamics, exact, numerics, run

counts = Counter()
notes = {}


def eq(group, actual, expected):
    assert actual == expected, (group, actual, expected)
    counts[group] += 1


def yes(group, condition):
    assert condition, group
    counts[group] += 1


def rejects(group, function, classes=(ValueError, AssertionError, TypeError)):
    try:
        function()
    except classes:
        counts[group] += 1
    else:
        raise AssertionError((group, "unexpected acceptance"))


def mm(a, b):
    # Independent flat matrices, no companion exact helper calls.
    w, x, y, z = a
    p, q, r, s = b
    return (w*p+x*r, w*q+x*s, y*p+z*r, y*q+z*s)


def mp(a, n):
    result = (Q(1), Q(0), Q(0), Q(1))
    while n:
        if n % 2:
            result = mm(result, a)
        a = mm(a, a)
        n //= 2
    return result


def mi(a):
    w, x, y, z = a
    assert w*z-x*y == 1
    return z, -x, -y, w


def word(*factors):
    result = (Q(1), Q(0), Q(0), Q(1))
    for a in factors:
        result = mm(result, a)
    return result


def tr(a):
    return a[0]+a[3]


def eval_poly(poly, xyz):
    return sum(coefficient*xyz[0]**a*xyz[1]**b*xyz[2]**c
               for (a, b, c), coefficient in poly.items())


def records_poly(rows):
    return {tuple(row["powers_xyz"]): Q(row["coefficient"]) for row in rows}


def polynomial_and_matrix_probes():
    polys = exact.chebyshev(exact.X, 16)
    # 17 distinct x values determine each polynomial through degree 16 exactly.
    for x in range(-8, 9):
        for n, poly in enumerate(polys):
            eq("polynomial_matrix_evaluation", eval_poly(poly, (x, 0, 0)), tr(mp((x, -1, 1, 0), n)))
    for xyz in product((-3, Q(1, 2), 2), repeat=3):
        v = xyz[0]*xyz[1]-xyz[2]
        figures = exact.chebyshev(exact.add(exact.mul(exact.X, exact.Y), exact.scale(exact.Z, -1)), 8)
        for n, poly in enumerate(figures):
            eq("figure_matrix_evaluation", eval_poly(poly, xyz), tr(mp((v, -1, 1, 0), n)))
    weights = algebra.moment_weights(32)
    # Algebraic generating equation D(q) W(q)^2=(2-q)^2 fixes the positive branch.
    square = [sum(weights[j]*weights[n-j] for j in range(n+1)) for n in range(33)]
    for n in range(33):
        value = sum(v*square[n-k] for k, v in ((0, 1), (1, -2), (2, 1), (4, -4)) if k <= n)
        eq("weight_algebraic_equation", value, {0: 4, 1: -4, 2: 1}.get(n, 0))
    eq("weight_normalization", weights[0], 2)
    eq("weight_normalization", algebra.linear_weight(polys[2], weights), -3)
    rng = random.Random(20261101)
    rows, raw = [], []
    for index in range(24):
        a = word((1, Q(rng.randint(-7, 7), 3), 0, 1), (1, 0, Q(rng.randint(-7, 7), 2), 1))
        b = word((1, 0, Q(rng.randint(-7, 7), 3), 1), (1, Q(rng.randint(-7, 7), 2), 0, 1))
        if index % 2:
            a = tuple(-x for x in a)
        raw.append((a, b))
        rows.append({"id": str(index), "A": [[a[0], a[1]], [a[2], a[3]]], "B": [[b[0], b[1]], [b[2], b[3]]]})
    result = algebra.matrix_checks(rows)
    for (a, b), row in zip(raw, result["fixtures"]):
        xyz = tr(a), tr(b), tr(mm(a, b))
        direct = [tr(word(a, a, b, mi(a), mi(b))), tr(word(a, a, a, b, b)), tr(word(a, a, b, a, b))]
        eq("new_SL2_words", row["word_traces"], direct)
        eq("new_SL2_words", [eval_poly(p, xyz) for p in algebra.obstruction_polynomials()], direct)
    notes["polynomial_oracle"] = "Trace of independently multiplied companion matrix at 17 distinct exact x values; no coefficient formula or Chebyshev recurrence in oracle."


def euler_probes():
    result = algebra.euler_checks(20)
    series = {row["length"]: records_poly(row["polynomial"]) for row in result["coefficients_by_length"]}
    logarithm = {row["length"]: records_poly(row["polynomial"]) for row in result["logarithm_by_length"]}
    for xyz in ((0, 0, 0), (1, 1, 1), (-2, 3, 5), (2, -1, 4), (Q(1, 2), Q(2, 3), Q(-1, 3))):
        # Independently invert the scalar denominator, then use F'=F*(log F)'.
        denominator = [Q(1)]+[Q(0)]*20
        for degree, value in ((2, xyz[0]), (3, xyz[1]), (4, xyz[2]), (7, xyz[0]*xyz[1]-xyz[2])):
            prior = denominator[:]
            for n in range(degree, 21):
                denominator[n] -= value*prior[n-degree]
        f, log = [Q(1)], [Q(0)]
        for n in range(1, 21):
            f.append(-sum(denominator[j]*f[n-j] for j in range(1, n+1)))
            log.append((n*f[n]-sum(j*log[j]*f[n-j] for j in range(1, n)))/n)
        for n in range(21):
            eq("Euler_reciprocal_and_derivative", eval_poly(series.get(n, {}), xyz), f[n])
            eq("Euler_reciprocal_and_derivative", eval_poly(logarithm.get(n, {}), xyz), log[n])
    eq("Euler_constant_atom", {n: p.get((0, 0, 0), 0) for n, p in series.items() if p.get((0, 0, 0))}, {0: 1})
    yes("Euler_wrong_Adams", result["wrong_Adams_empty_atoms"] != {0: 1})
    for length in range(5, 21):
        support = algebra.support_checks([2, 4], length, 30)
        one_support = sum(sum(v > 0 for v in triple) == 1 for triple in product(range(length+1), repeat=3)
                          if 0 < sum(v*l for v, l in zip(triple, (2, 3, 4))) <= length)
        eq("support_vs_copies", support["one_support_count"], one_support)
        eq("support_vs_copies", support["one_copy_count"], 3)


def dynamics_probes():
    # Explicit enumeration of every two-state path for small n, retaining edge labels.
    result = dynamics.scalar_checks([2, 4], 6)
    for row in result["periodic_examples"]:
        m = row["m"]
        for values in row["values"]:
            n = values["n"]
            paths, closed, corr = 0, 0, Q(0)
            for start in (0, 1):
                for labels in product(range(m), repeat=n):
                    finish = start
                    for _ in labels:
                        finish = 1-finish
                    paths += 1
                    closed += start == finish
                    corr += Q((-1)**(start+finish), 2*m**n)
            eq("enumerated_periodic_paths", [values["path_count"], values["closed_trace"], values["stationary_correlation"]], [paths, closed, corr])
    bruhat = dynamics.bruhat_checks(37, [[1, 1], [1, -1], [0, 0], [0, 1], [3, 5]])
    for row in bruhat["rows"]:
        c = row["c"]
        pairs = [(a, d) for a in range(c) for d in range(c) if (a*d) % c == 1]
        eq("Bruhat_independent_congruence", row["unit_inverse_pairs"], pairs)
        for freq in row["frequency_residues"]:
            m, n = freq["frequencies"]
            # Exhaustive residue counts including zeros distinguish multiplicity from support.
            expected = {r: sum((m*a+n*d-r) % c == 0 for a, d in pairs) for r in range(c)}
            eq("Bruhat_independent_congruence", freq["root_of_unity_coefficients"], {r: v for r, v in expected.items() if v})
        eq("Bruhat_adaptive_scope", row["adaptive_statistic"], 1)
    yes("Bruhat_adaptive_scope", "norms grow" in bruhat["scope"])
    # Integer unimodular shear permits an independent oracle in physical coordinates.
    for radius in (Q(1), Q(499, 100), Q(5)):
        physical = [(u, v) for u in range(-5, 6) for v in range(-5, 6)
                    if gcd(u, v) == 1 and u*u+v*v <= radius*radius]
        expected = {(u-37*v, v) for u, v in physical}
        actual, bounds = dynamics.primitive_vectors([[1, 37], [0, 1]], radius)
        eq("physical_lattice_oracle", set(actual), expected)
        yes("physical_lattice_oracle", all(abs(v[0]) <= bounds[0] and abs(v[1]) <= bounds[1] for v in expected))
    for values in ([[3, 0], [0, "1/3"]], [[1, "7/3"], [0, 1]], [["3/5", "-4/5"], ["4/5", "3/5"]]):
        g = [[Q(v) for v in row] for row in values]
        # Frobenius inverse norm gives a separately derived square bound.
        norm2 = sum(v*v for row in g for v in row)
        for radius in (Q(1, 3), Q(1), Q(5, 2), Q(5)):
            bound2 = radius*radius*norm2
            bound = isqrt(bound2.numerator//bound2.denominator)+1
            expected = {(m, n) for m in range(-bound, bound+1) for n in range(-bound, bound+1)
                        if gcd(m, n) == 1 and (g[0][0]*m+g[0][1]*n)**2+(g[1][0]*m+g[1][1]*n)**2 <= radius*radius}
            actual, _ = dynamics.primitive_vectors(values, radius)
            eq("independent_ellipse_oracle", set(actual), expected)
            eq("independent_ellipse_oracle", Counter((m % 2, n % 2) for m, n in actual), Counter((m % 2, n % 2) for m, n in expected))


def direct_events(lengths, start):
    # Pairwise indicator-integral expansion, independent of an event sweep or midpoint integration.
    end = 2*start
    terms = [(ell/2, 1) for ell in lengths]+[(ell, -4) for ell in lengths]
    integral = Q(0)
    for (a, av), (b, bv) in product(terms, repeat=2):
        lower = max(start, a, b)
        if lower < end:
            integral += av*bv*(1/lower-1/end)
    points = {start, end} | {p for p, _ in terms if start <= p <= end}
    maximum = Q(0)
    for p in points:
        maximum = max(maximum, abs(sum(v for x, v in terms if x <= p))/p)
        if p > start:
            maximum = max(maximum, abs(sum(v for x, v in terms if x < p))/p)
    return maximum, integral/start


def arithmetic_probes():
    alphabet = (Q(1, 2), Q(1), Q(3, 2), Q(2), Q(4))
    for size in range(5):
        for lengths in combinations_with_replacement(alphabet, size):
            for start in (Q(1, 2), Q(1), Q(3, 2), Q(2)):
                expected = direct_events(lengths, start)
                actual = arithmetic.block_metrics(lengths, start)
                eq("dyadic_pairwise_integral", (actual["M"], actual["Q_squared"]), expected)
    tiny = Q(1, 10**60)
    for lengths in ((2, 2+tiny, 4), (1-tiny, 1, 1+tiny, 2-tiny, 2, 2+tiny), (2, 4, 4)):
        lengths = list(map(Q, lengths))
        actual = arithmetic.block_metrics(lengths, 1)
        eq("dyadic_nearby_and_boundary", (actual["M"], actual["Q_squared"]), direct_events(lengths, Q(1)))
    for n in range(1, 41):
        for a, b in ((Q(-13, 4), Q(17, 3)), (Q(-7), Q(0)), (Q(0), Q(0)), (Q(1, 3), Q(2, 3)), (Q(-2), Q(-2))):
            expected = sum(a <= m <= b and gcd(m, n) == 1 for m in range(-10, 11))
            eq("row_independent_gcd", arithmetic.row_count(a, b, n), expected)
    for numerator in range(1, 31):
        radius = Q(numerator, 3)
        for gauge in ("square", "rational_diamond"):
            actual = arithmetic.lattice_points(radius, gauge)
            def length(m, n):
                return Q(max(abs(m), abs(n))) if gauge == "square" else abs(m)+Q(3, 2)*abs(n)
            expected = {(m, n, length(m, n)) for m in range(-11, 12) for n in range(-11, 12)
                        if (m or n) and length(m, n) <= radius}
            eq("lattice_gauge_independent_box", set(actual), expected)
        if radius >= 1:
            arithmetic.mobius_checks([radius])
            counts["extra_Mobius_fractional_cases"] += 1
    for alpha in (Q(0), Q(1, 3), Q(2, 3), Q(9, 10)):
        for theta in (Q(0), Q(1, 2), Q(7, 8), Q(11, 12)):
            d, kappa = arithmetic.balance(alpha, theta)
            # Solve equality of the two affine functions independently.
            left_slope, right_slope = 1-alpha, theta-2
            expected_d = (2-alpha)/(left_slope-right_slope)
            eq("conditional_balance_intersection", (d, kappa), (expected_d, alpha+left_slope*expected_d))


def numerical_probes():
    ctx = numerics.context(90)
    tolerance = ctx.mpf("1e-65")
    relative_errors = []
    def close(group, actual, expected, relative=False):
        scale = abs(expected) if relative else max(1, abs(expected))
        err = abs(actual-expected)/scale
        yes(group, ctx.isfinite(actual) and err < tolerance)
        relative_errors.append(err)
    # Angular quadrature after radial integration, independent of product quadrature.
    for ar, br in ((Q(1), Q(2)), (Q(2), Q(3)), (Q(2, 5), Q(7, 3))):
        a, b = numerics.mpq(ctx, ar), numerics.mpq(ctx, br)
        result = numerics.gaussian_checks(ctx, [[ar, br]], [Q(-2), Q(-1, 3), Q(0), Q(2)])
        row = result["rows"][0]
        def angular(function):
            return 4*ctx.quad(function, [0, ctx.pi/4, ctx.pi/2])
        norm = angular(lambda u: 1/(a*ctx.cos(u)**2+b*ctx.sin(u)**2))/(4*ctx.pi)
        derivative = (a-b)**2/(2*ctx.pi)*angular(lambda u: ctx.cos(u)**2*ctx.sin(u)**2/(a*ctx.cos(u)**2+b*ctx.sin(u)**2)**3)
        close("polar_Gaussian_oracle", ctx.mpf(row["L2_squared"]), norm)
        close("polar_Gaussian_oracle", ctx.mpf(row["rotation_derivative_squared"]), derivative)
        for corr in row["correlations"]:
            t = numerics.mpq(ctx, corr["t"])
            aa, bb = a*(1+ctx.exp(2*t)), b*(1+ctx.exp(-2*t))
            covariance = angular(lambda u: 1/(aa*ctx.cos(u)**2+bb*ctx.sin(u)**2))/(2*ctx.pi)
            close("polar_Gaussian_oracle", ctx.mpf(corr["quadrature"]), covariance)
    # r=sqrt(k)*exp(s), reflected about s=0, with leading exponential scaled away.
    # This probes tiny original orbit values with a relative criterion.
    orbit_errors = []
    for t in (Q(0), Q(1, 2), Q(1), Q(2)):
        alpha = 2*ctx.pi*ctx.cosh(numerics.mpq(ctx, t))
        for k in (1, 2, 3):
            scaled_radial = 2*ctx.sqrt(k)*ctx.quad(lambda s: ctx.cosh(s)*ctx.exp(-2*alpha*k*(ctx.cosh(2*s)-1)), [0, ctx.mpf("0.25"), 1, 3])
            scaled_oracle = 2*ctx.pi*ctx.sqrt(ctx.pi/alpha)/(k*ctx.zeta(2))*scaled_radial
            actual, _ = numerics.orbit_integral(ctx, alpha, k, 30)
            scaled_actual = actual*ctx.exp(2*alpha*k)
            err = abs(scaled_actual-scaled_oracle)/scaled_oracle
            # Tiny original values reduce the unscaled quadrature's relative accuracy.
            yes("scaled_radial_oracle", err < ctx.mpf("1e-25"))
            orbit_errors.append({"t": str(t), "k": k, "relative_error": str(err)})
            for wrong in (0, -scaled_oracle, scaled_oracle/2, 2*scaled_oracle):
                yes("scaled_radial_mutants_detected", abs(wrong-scaled_oracle)/scaled_oracle > ctx.mpf("0.1"))
    for q in (Q(1, 10), Q(1, 2), Q(9, 10)):
        for n in (1, 3, 7):
            kbound, lbound = numerics.series_tail_bounds(q, n)
            ktail = sum(Q(sum(d for d in range(1, k+1) if k % d == 0), k)*q**k for k in range(n+1, 100))
            ltail = sum(q**(j*m)/m for j in range(n+1, 70) for m in range(1, 70))
            yes("analytic_tail_finite_lower_tests", 0 < ktail < kbound)
            yes("analytic_tail_finite_lower_tests", 0 < ltail < lbound)
    # Log derivative coefficient identity: sum_{d|k}1/d = sigma_1(k)/k.
    for k in range(1, 61):
        eq("log_series_coefficient_identity", sum(Q(1, d) for d in range(1, k+1) if k % d == 0), Q(sum(d for d in range(1, k+1) if k % d == 0), k))
    # Small U exposes tail size, instead of checking only numerically invisible tails.
    for coefficient in (ctx.mpf("0.2"), ctx.mpf(3)):
        for moment in (0, 2):
            actual, tail = numerics.gaussian_moment(ctx, coefficient, moment, 2)
            full = 1/ctx.sqrt(coefficient) if moment == 0 else 1/(2*ctx.pi*coefficient**ctx.mpf("1.5"))
            yes("Gaussian_visible_tail", 0 < full-actual < tail)
    notes["scaled_radial_relative_errors"] = orbit_errors
    notes["maximum_polar_scaled_error"] = str(max(relative_errors))
    notes["numerical_evidence_limit"] = "Transformed independent integrands share mpmath; no interval or quadrature error certification."


def validation_probes():
    fixture = json.loads((run.HERE/"fixture.json").read_text())
    for invalid in (None, True, 1.5, float("nan"), float("inf"), "NaN", "Infinity", "-Infinity", "0/0", "1/0", [], {}):
        rejects("exact_invalid_inputs", lambda invalid=invalid: exact.rational(invalid))
    mutations = [
        ("precisions", [60, 60]), ("precisions", [39, 90]), ("precisions", [60, 121]),
        ("sl2_matrices", [{"id": "bad", "A": [[1, 0], [0, 2]], "B": [[1, 0], [0, 1]]}]),
        ("primitive_radii", [0]), ("gaussian_times", ["NaN"]), ("gaussian_pairs", [[1, -1]]),
        ("endpoint_frequencies", [[1, True]]), ("rank_two_terms", 19), ("rank_one_boxes", [1, 1]),
        ("row_endpoints", [[2, 1]]), ("lattice_cutoffs", [21]), ("balance_thetas", ["1/2"]),
        ("terminal_families", [{"h": 1, "r": 1, "c": "inf", "M": 0, "T": 1}]),
        ("formula_contracts", {}), ("schema_version", True), ("scope", None),
    ]
    for key, value in mutations:
        altered = copy.deepcopy(fixture)
        altered[key] = value
        rejects("fixture_invalid_domains", lambda altered=altered: run.validate_fixture(altered))
    for value in (None, [], {}, {"schema_version": 1}):
        rejects("fixture_invalid_schema", lambda value=value: run.validate_fixture(value))
    for key in fixture:
        altered = copy.deepcopy(fixture)
        del altered[key]
        rejects("fixture_missing_keys", lambda altered=altered: run.validate_fixture(altered))
    ctx = numerics.context(60)
    for a, b, tail in ((ctx.nan, 0, 0), (0, ctx.inf, 0), (0, 0, ctx.nan), (0, 0, -1)):
        rejects("numeric_invalid_inputs", lambda a=a, b=b, tail=tail: numerics.NumericChecks(ctx).close("adversarial", a, b, analytic_tail_allowance=tail))
    for value in (ctx.nan, ctx.inf, -ctx.inf):
        rejects("numeric_invalid_inputs", lambda value=value: numerics.number(ctx, value))
    low = {"decimal_precision": 60, "observations": {"x": "1"}}
    for high in ({"decimal_precision": 90, "observations": {"x": "1.01"}}, {"decimal_precision": 90, "observations": {"x": "nan"}}, {"decimal_precision": 90, "observations": {"y": "1"}}):
        rejects("precision_mismatch", lambda high=high: numerics.precision_comparison(low, high))
    import mpmath
    original = mpmath.mp.dps
    c60, c90 = numerics.context(60), numerics.context(90)
    c60.dps = 41
    eq("context_isolation", (c90.dps, mpmath.mp.dps), (90, original))
    # Exclusive writer also refuses a dangling symlink; serialize before creation.
    with tempfile.TemporaryDirectory(dir=OUT) as directory:
        p = Path(directory)
        target = p/"target.json"
        dangling = p/"dangling.json"
        dangling.symlink_to(target)
        rejects("exclusive_output", lambda: run.write_result(dangling, {"x": 1}), (FileExistsError,))
        yes("exclusive_output", not target.exists())
        for bad in (float("nan"), float("inf"), -float("inf")):
            rejects("serialization_nonfinite", lambda bad=bad: run.write_result(target, {"nested": [bad]}))
            yes("serialization_nonfinite", not target.exists())
        run.write_result(target, {"x": Q(7, 3)})
        before = target.read_bytes()
        rejects("exclusive_output", lambda: run.write_result(target, {"x": 9}), (FileExistsError,))
        eq("exclusive_output", target.read_bytes(), before)


for probe in (polynomial_and_matrix_probes, euler_probes, dynamics_probes, arithmetic_probes, numerical_probes, validation_probes):
    probe()
    print(probe.__name__, "passed", flush=True)
result = {"status": "pass", "assertion_count": sum(counts.values()), "assertions_by_group": dict(counts), "notes": notes}
(OUT/"independent-probes-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": "pass", "assertions": result["assertion_count"]}))
