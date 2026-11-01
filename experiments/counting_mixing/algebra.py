"""Exact trace, coefficient-filter, and length-convolution fixtures."""

from fractions import Fraction as Q
from itertools import product
from math import comb, factorial

from .exact import (
    ONE, X, Y, Z, ZERO, Checks, add, chebyshev, divisors, identify_cuffs,
    integer, inverse, matrix, mobius, mul, polynomial_records, power, scale,
    trace, word,
)


def factorial_coefficient(k, j):
    return Q((-1)**j*k*factorial(k-j-1), factorial(j)*factorial(k-2*j))


def coefficient_checks(maximum):
    integer(maximum, 2, 20)
    checks = Checks("trace coefficients")
    simple = chebyshev(X, maximum)
    figure = chebyshev(add(mul(X, Y), scale(Z, -1)), maximum)
    for k in range(1, maximum+1):
        expected = {(k-2*j, 0, 0): factorial_coefficient(k, j) for j in range(k//2+1)}
        checks.equal(simple[k], expected, f"factorial coefficients k={k}, including constant")
        for m in range(1, maximum+1):
            value = 0
            if k >= m and (k-m) % 2 == 0:
                h = (k-m)//2
                value = (-1)**h*comb(m+h, h)
                if h:
                    value -= (-1)**(h-1)*comb(m+h-1, h-1)
            checks.equal(simple[k].get((m, 0, 0), 0), value,
                         f"generating series coefficient q^{k}, x^{m}")
        checks.true(all(a == b for a, b, _ in figure[k]), f"equal cuff exponents k={k}")
        for r in range(k+1):
            for m in range(k+1):
                if r+m == 0:
                    continue
                value = Q(0)
                if k >= r+m and (k-r-m) % 2 == 0:
                    j = (k-r-m)//2
                    value = Q((-1)**(j+m)*k*factorial(k-j-1),
                              factorial(j)*factorial(r)*factorial(m))
                checks.equal(figure[k].get((r, r, m), 0), value,
                             f"figure-eight coefficient k={k}, r={r}, m={m}")
        checks.equal(figure[k].get((1, 1, 0), 0)+figure[k].get((0, 0, 1), 0), 0,
                     f"linear crossing cancellation k={k}")
        checks.equal(identify_cuffs(figure[k]), chebyshev(add(power(X, 2), scale(Z, -1)), k)[k],
                     f"collect after cuff identification k={k}")
    checks.equal(identify_cuffs(figure[2]),
                 {(4, 0, 0): Q(1), (2, 0, 1): Q(-2), (0, 0, 2): Q(1), ZERO: Q(-2)},
                 "identified second power has degree four")
    return checks.result(maximum_k=maximum, P0=2, P1="x",
                         simple_polynomials=[polynomial_records(p) for p in simple],
                         identified_P2=polynomial_records(identify_cuffs(figure[2])))


def obstruction_polynomials():
    comm = add(power(X, 2), power(Y, 2), power(Z, 2), scale(mul(mul(X, Y), Z), -1), scale(ONE, -2))
    first = mul(X, add(comm, scale(ONE, -1)))
    second = add(mul(mul(add(power(X, 2), scale(ONE, -1)), Y), Z),
                 scale(mul(X, power(Y, 2)), -1), scale(power(X, 3), -1), scale(X, 3))
    third = add(mul(X, power(Z, 2)), scale(mul(Y, Z), -1), scale(X, -1))
    return first, second, third


def matrix_checks(rows):
    checks = Checks("SL2 words")
    outputs = []
    for row in rows:
        a, b = matrix(row["A"]), matrix(row["B"])
        x, y, z = trace(a), trace(b), trace(word(a, b))
        commutator = trace(word(a, b, inverse(a), inverse(b)))
        checks.equal(commutator, x*x+y*y+z*z-x*y*z-2, "Fricke commutator")
        actual = [trace(word(a, a, b, inverse(a), inverse(b))),
                  trace(word(a, a, a, b, b)), trace(word(a, a, b, a, b))]
        expected = [x*(commutator-1), (x*x-1)*y*z-x*y*y-x**3+3*x, x*z*z-y*z-x]
        for i, (left, right) in enumerate(zip(actual, expected)):
            checks.equal(left, right, f"word {i+1}")
        checks.equal(actual[0]+actual[1]-actual[2], x, "linear-selector obstruction")
        v = trace(word(a, inverse(b)))
        adams_defect = (z*z-2)+(v*v-2)-(x*x-2)*(y*y-2)
        checks.equal(adams_defect, 2*(commutator-2), "Adams is not a trace-ring endomorphism")
        outputs.append({"id": row["id"], "A": a, "B": b, "traces_xyz": [x, y, z],
                        "word_traces": actual, "commutator_trace": commutator,
                        "Adams_defect": adams_defect})
    checks.true(any(row["Adams_defect"] != 0 for row in outputs), "noncommuting obstruction retained")
    first, second, third = obstruction_polynomials()
    checks.equal(add(first, second, scale(third, -1)), X, "formal word relation")
    return checks.result(fixtures=outputs, scope="Rational SL2 identities; no geometric word classification.")


def moment_weights(maximum):
    # S_n(v)=S_(n-1)(v)+v*S_(n-2)(v), followed by the central-binomial moment.
    recurrence = [scale(ONE, 2), ONE]
    for _ in range(1, maximum):
        recurrence.append(add(recurrence[-1], mul(X, recurrence[-2])))
    return [sum(c*comb(p[0], p[0]//2) for p, c in poly.items() if p[0] % 2 == 0)
            for poly in recurrence]


def generating_weights(maximum):
    # Independent binomial expansion: D^(-1/2)=sum binom(2j,j) (1-D)^j/4^j.
    e = {(1, 0, 0): Q(2), (2, 0, 0): Q(-1), (4, 0, 0): Q(4)}
    total, term = {}, ONE
    for j in range(maximum+1):
        total = add(total, scale(term, Q(comb(2*j, j), 4**j)))
        term = {p: c for p, c in mul(term, e).items() if p[0] <= maximum}
    total = mul(add(scale(ONE, 2), scale(X, -1)), total)
    return [total.get((n, 0, 0), Q(0)) for n in range(maximum+1)]


def linear_weight(poly, weights):
    if any(sum(p) >= len(weights) for p in poly):
        raise ValueError("weight table does not cover polynomial degree")
    return sum(c*weights[sum(p)] for p, c in poly.items())


def global_filter_checks(maximum):
    checks = Checks("global moment filter")
    weights = moment_weights(2*maximum)
    checks.equal(weights, generating_weights(2*maximum), "moment and generating definitions")
    checks.equal(weights[:13], [2, 1, 1, 1, 5, 11, 19, 29, 53, 109, 221, 419, 779],
                 "printed weight row")
    figure = chebyshev(add(mul(X, Y), scale(Z, -1)), maximum)
    for k in range(1, maximum+1):
        checks.equal(linear_weight(figure[k], weights), 0, f"one-crossing annihilation k={k}")
        checks.equal(linear_weight(identify_cuffs(figure[k]), weights), 0,
                     f"identified cuffs k={k}")
    simple = [linear_weight(p, weights) for p in chebyshev(X, maximum)[1:]]
    checks.equal(simple[:12], [1, -3, -2, 5, 11, -6, -41, -11, 124, 127, -307, -646],
                 "simple trace filter values")
    obstruction = [linear_weight(p, weights) for p in obstruction_polynomials()]
    checks.equal(obstruction, [-5, 5, -1], "obstruction-word weights")
    checks.true(weights[2] != weights[1]**2 or weights[0] != 1,
                "functional is not a unital algebra homomorphism")
    return checks.result(weights=weights, simple_trace_values=simple, obstruction_values=obstruction,
                         degree_convention="Total multicurve multiplicity, including identified cuffs.")


def support_checks(genera, cutoff, mobius_maximum):
    checks = Checks("finite support and divisor selector")
    rows = []
    for genus in genera:
        integer(genus, 2, 8)
        q = 3*genus-2
        coefficients = [(-1)**n*(n+1) for n in range(q)]
        selector = sum(c for n, c in enumerate(coefficients) if (n-1) % q == 0)
        checks.equal(selector, coefficients[1], "exact roots-of-unity congruence selector")
        checks.equal([int((n-1) % q == 0) for n in range(q)], [0, 1]+[0]*(q-2),
                     "no congruence alias within degree bound")
        rows.append({"genus": genus, "q": q, "degree_bound": q-1,
                     "polynomial_coefficients": coefficients, "selected_linear_coefficient": selector})
    for n in range(1, mobius_maximum+1):
        checks.equal(sum(mobius(d) for d in divisors(n)), int(n == 1), f"divisor inversion n={n}")
    tuples = [v for v in product(range(cutoff//2+1), range(cutoff//3+1), range(cutoff//4+1))
              if 0 < 2*v[0]+3*v[1]+4*v[2] <= cutoff]
    support_histogram = [sum(sum(x > 0 for x in v) == n for v in tuples) for n in range(4)]
    one_support = sum(sum(x > 0 for x in v) == 1 for v in tuples)
    one_copy = sum(sum(v) == 1 for v in tuples)
    checks.equal(support_histogram[1], cutoff//2+cutoff//3+cutoff//4, "single support permits multiples")
    checks.true(one_support != one_copy, "support and multiplicity distinguished")
    return checks.result(selectors=rows, divisor_range=[1, mobius_maximum], formal_lengths=[2, 3, 4],
                         cutoff=cutoff, multicurve_count=len(tuples), support_histogram=support_histogram,
                         one_support_count=one_support, one_copy_count=one_copy)


def convolve(left, right, cutoff):
    result = {}
    for a, pa in left.items():
        for b, pb in right.items():
            if a+b <= cutoff:
                result[a+b] = add(result.get(a+b, {}), mul(pa, pb))
    return {length: poly for length, poly in result.items() if poly}


def series_add(left, right, scalar=1):
    result = dict(left)
    for length, poly in right.items():
        result[length] = add(result.get(length, {}), scale(poly, scalar))
    return {length: poly for length, poly in result.items() if poly}


def coefficient_atoms(series, target):
    return {length: poly[target] for length, poly in sorted(series.items()) if target in poly}


def euler_checks(cutoff):
    integer(cutoff, 14, 20)
    checks = Checks("finite length-valued Euler product")
    generators = [(2, X), (3, Y), (4, Z), (7, add(mul(X, Y), scale(Z, -1)))]
    series = {0: ONE}
    for length, poly in generators:
        series = convolve(series, {m*length: power(poly, m) for m in range(cutoff//length+1)}, cutoff)
    independent = {}
    multisets = 0
    for a, b, c, d in product(range(cutoff//2+1), range(cutoff//3+1),
                              range(cutoff//4+1), range(cutoff//7+1)):
        length = 2*a+3*b+4*c+7*d
        if length > cutoff:
            continue
        multisets += 1
        for m in range(d+1):
            term = {(a+d-m, b+d-m, c+m): Q((-1)**m*comb(d, m))}
            independent[length] = add(independent.get(length, {}), term)
    checks.equal(series, independent, "convolution versus independent multiset/binomial enumeration")
    diagonals = []
    for r, s, m in product(range(cutoff//2+1), range(cutoff//3+1), range(cutoff//4+1)):
        diagonal = 2*r+3*s+4*m
        if diagonal <= cutoff:
            atoms = coefficient_atoms(series, (r, s, m))
            checks.equal(min(atoms), diagonal, "first atom is the formal diagonal")
            checks.equal(atoms[diagonal], 1, "unit first-atom coefficient")
            diagonals.append({"powers_xyz": [r, s, m], "first_length": diagonal, "mass": 1})
    checks.equal(coefficient_atoms(series, (1, 1, 0)), {5: Q(1), 7: Q(1)}, "xy coefficient")
    checks.equal(coefficient_atoms(series, (0, 0, 1)), {4: Q(1), 7: Q(-1)}, "z coefficient")
    checks.equal(coefficient_atoms(series, ZERO), {0: Q(1)}, "empty coefficient")
    nonconstant = {length: poly for length, poly in series.items() if length}
    term, logarithm = {0: ONE}, {}
    for n in range(1, cutoff//2+1):
        term = convolve(term, nonconstant, cutoff)
        logarithm = series_add(logarithm, term, Q((-1)**(n+1), n))
    expected, wrong_adams = {}, {}
    for length, poly in generators:
        trace_powers = chebyshev(poly, cutoff//length)
        for m in range(1, cutoff//length+1):
            expected = series_add(expected, {m*length: power(poly, m)}, Q(1, m))
            wrong_adams = series_add(wrong_adams, {m*length: trace_powers[m]}, Q(1, m))
    checks.equal(logarithm, expected, "convolution logarithm uses ordinary tensor powers")
    checks.true(logarithm != wrong_adams, "Adams replacement deliberately fails")
    checks.equal(coefficient_atoms(wrong_adams, ZERO).get(4), -1,
                 "wrong second power introduces a spurious empty atom")
    checks.equal(3+5, 4+4, "coincident lengths lose the decomposition")
    checks.true(3**2+5**2 != 4**2+4**2, "same scalar sum has distinct sum of squares")
    return checks.result(cutoff=cutoff, generator_lengths=[2, 3, 4, 7], enumerated_multisets=multisets,
                         first_atoms=diagonals, coefficients_by_length=[
                             {"length": length, "polynomial": polynomial_records(poly)}
                             for length, poly in sorted(series.items())],
                         logarithm_by_length=[{"length": length, "polynomial": polynomial_records(poly)}
                                              for length, poly in sorted(logarithm.items())],
                         wrong_Adams_empty_atoms=coefficient_atoms(wrong_adams, ZERO),
                         coincident_length_example={"trace_lists": [[3, 5], [4, 4]],
                                                    "common_sum": 8, "square_sums": [34, 32]})
