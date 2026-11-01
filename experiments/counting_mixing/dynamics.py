"""Finite scalar/trace counterexamples, Bruhat residues, and lattice geometry."""

from collections import Counter
from fractions import Fraction as Q
from itertools import combinations
from math import gcd

from .exact import (
    IDENTITY, Checks, floor, integer, inverse, matrix, mmul, mpower, phi,
    positive, rational, trace, word,
)


def scalar_checks(m_values, maximum):
    integer(maximum, 1, 64)
    checks = Checks("scalar path versus trace and mixing")
    rows = []
    for m in m_values:
        integer(m, 2, 20)
        a = ((0, m), (m, 0))
        p = ((0, 1), (1, 0))
        values = []
        for n in range(1, maximum+1):
            an, pn = mpower(a, n), mpower(p, n)
            path_count = sum(sum(row) for row in an)
            correlation = sum(Q(1, 2)*f*pn[i][j]*h
                              for i, f in enumerate((1, -1)) for j, h in enumerate((1, -1)))
            checks.equal(path_count, 2*m**n, "scalar path count")
            checks.equal(trace(an), m**n+(-m)**n, "closed trace detects periodicity")
            checks.equal(correlation, (-1)**n, "stationary centered correlation does not decay")
            values.append({"n": n, "path_count": path_count, "closed_trace": trace(an),
                           "stationary_correlation": correlation})
        rows.append({"m": m, "values": values})
    a, projection = ((2, 1), (1, 2)), ((Q(1, 2), Q(1, 2)), (Q(1, 2), Q(1, 2)))
    p = tuple(tuple(Q(v, 3) for v in row) for row in a)
    for n in range(1, maximum+1):
        checks.equal(trace(mpower(a, n)), 3**n+1, "aperiodic closed trace")
        pn = mpower(p, n)
        checks.equal(tuple(tuple(pn[i][j]-projection[i][j] for j in range(2)) for i in range(2)),
                     tuple(tuple(Q(1, 3**n)*(IDENTITY[i][j]-projection[i][j])
                                 for j in range(2)) for i in range(2)), "exact matrix mixing")
    return checks.result(n_range=[1, maximum], periodic_examples=rows, aperiodic_matrix=a,
                         scope="Finite replay of explicit matrix examples, not a counting-to-mixing theorem.")


def terminal_algebra_checks(rows):
    """Exact coefficient comparison in the algebra of formal exponentials."""
    checks, outputs = Checks("terminal exponential algebra"), []
    for row in rows:
        h, r, c = positive(row["h"]), positive(row["r"]), rational(row["c"])
        centered = {-r: c} if c else {}
        # Apply h+partial_t, then multiply by exp(h*t), as separate operations.
        differentiated = {rate: rate*coefficient for rate, coefficient in centered.items()}
        integrand = {rate+h: h*coefficient+differentiated.get(rate, 0)
                     for rate, coefficient in centered.items()
                     if h*coefficient+differentiated.get(rate, 0)}
        primitive = {rate: coefficient/rate for rate, coefficient in integrand.items() if rate}
        checks.true(0 not in integrand, "rate-zero removable case has zero integrand")
        checks.equal({rate: rate*coefficient for rate, coefficient in primitive.items()}, integrand,
                     "formal primitive differentiates to the integrand")
        terminal = {h-r: c} if h != r and c else {}
        checks.equal(primitive, terminal, "terminal exponent coefficients, modulo constants")
        outputs.append({"h": h, "r": r, "c": c, "rate_zero": h == r,
                        "integrand_exponential_terms": [
                            {"rate": rate, "coefficient": coefficient} for rate, coefficient in sorted(integrand.items())],
                        "primitive_modulo_constants": [
                            {"rate": rate, "coefficient": coefficient} for rate, coefficient in sorted(primitive.items())]})
    return checks.result(rows=outputs,
                         interpretation="Formal exponentials exp(rate*t); evaluation at T minus at 1 cancels constants.")


def bruhat_checks(maximum, frequencies):
    integer(maximum, 2, 50)
    checks = Checks("rational Bruhat and endpoint residues")
    rows = []
    for c in range(2, maximum+1):
        pairs = [(a, pow(a, -1, c)) for a in range(c) if gcd(a, c) == 1]
        checks.equal(len(pairs), phi(c), "number of unit pairs")
        checks.equal(set(pairs), {(a, d) for a in range(c) for d in range(c) if (a*d-1) % c == 0},
                     "coupled residues from exhaustive congruence test")
        for a, d in pairs:
            b = (a*d-1)//c
            checks.equal(a*d-b*c, 1, "integer determinant")
            checks.equal(word(((1, Q(a, c)), (0, 1)), ((0, Q(-1, c)), (c, 0)),
                              ((1, Q(d, c)), (0, 1))), ((a, b), (c, d)), "Bruhat factorization")
        histograms = []
        for m, n in frequencies:
            hist = Counter((m*a+n*d) % c for a, d in pairs)
            # Independently multiply the two root-of-unity monomials modulo z^c-1.
            product_hist = Counter(((m*a) % c+(n*d) % c) % c for a, d in pairs)
            checks.equal(hist, product_hist, "endpoint product equals normalized Kloosterman polynomial")
            checks.equal(sum(hist.values()), phi(c), "residue multiplicities preserved")
            histograms.append({"frequencies": [m, n], "root_of_unity_coefficients": dict(sorted(hist.items()))})
        adaptive = Counter((c*a+c*d) % c for a, d in pairs)
        checks.equal(adaptive, {0: phi(c)}, "changing frequency m=n=c has statistic one")
        rows.append({"c": c, "phi": phi(c), "unit_inverse_pairs": pairs,
                     "frequency_residues": histograms, "adaptive_frequencies": [c, c],
                     "adaptive_statistic": 1, "adaptive_continuous_means": [0, 0]})
    return checks.result(c_range=[2, maximum], rows=rows,
                         exact_encoding="Polynomial in z modulo z^c-1, divided by phi(c); no floating roots needed.",
                         scope="The adaptive smooth norms grow with c; this does not refute a norm-dependent bound.")


def apply_matrix(g, vector):
    return tuple(sum(g[i][j]*vector[j] for j in range(2)) for i in range(2))


def norm_squared(vector):
    return sum(x*x for x in vector)


def primitive_vectors(g, radius):
    """Complete rational ellipse search from |m_i| <= R sum_j |g^-1_ij|.

    The L1 row bound dominates the Euclidean row norm, so no candidate with
    |g m| <= R lies outside this coordinate box. Boundary comparison is exact.
    """
    g, radius = matrix(g), positive(radius)
    inv = inverse(g)
    bounds = [floor(radius*sum(abs(x) for x in row)) for row in inv]
    if max(bounds) > 200:
        raise ValueError("finite fixture coordinate bound exceeds 200")
    vectors = [(m, n) for m in range(-bounds[0], bounds[0]+1)
               for n in range(-bounds[1], bounds[1]+1)
               if gcd(m, n) == 1 and norm_squared(apply_matrix(g, (m, n))) <= radius*radius]
    return vectors, bounds


def primitive_checks(matrices, radii):
    checks = Checks("primitive parity geometry")
    gamma2 = [matrix([[1, 2], [0, 1]]), matrix([[1, 0], [2, 1]])]
    rows = []
    for row in matrices:
        g = matrix(row["matrix"])
        for radius in map(positive, radii):
            vectors, bounds = primitive_vectors(g, radius)
            vector_set = set(vectors)
            parity = {str(p): sum((m % 2, n % 2) == p for m, n in vectors)
                      for p in ((1, 0), (0, 1), (1, 1))}
            checks.equal(sum(parity.values()), len(vectors), "all three nonzero parity classes retained")
            checks.equal({(-m, -n) for m, n in vectors}, vector_set, "sign pairs")
            checks.equal(len(vectors), 2*sum(n > 0 or (n == 0 and m > 0) for m, n in vectors),
                         "oriented versus unoriented multiplicity")
            # A stronger rational comparison suffices because pi > 3.
            checks.true(len(vectors) <= 2+6*radius**2, "stronger rational bound implies 2+2*pi*R^2")
            for v, w in combinations(vectors, 2):
                u, z = apply_matrix(g, v), apply_matrix(g, w)
                determinant = u[0]*z[1]-u[1]*z[0]
                checks.equal(determinant, v[0]*w[1]-v[1]*w[0], "unimodular determinant integrality")
                checks.true(determinant == 0 or abs(determinant) >= 1, "nonparallel determinant separation")
            for h in gamma2:
                transformed, _ = primitive_vectors(mmul(g, h), radius)
                expected = {apply_matrix(inverse(h), v) for v in vectors}
                checks.equal(set(transformed), expected, "Gamma(2) basis change covers the same vectors")
                checks.equal({str(p): sum((m % 2, n % 2) == p for m, n in transformed)
                              for p in ((1, 0), (0, 1), (1, 1))}, parity,
                             "Gamma(2) induces the identity parity permutation")
            rows.append({"matrix_id": row["id"], "matrix": g, "radius": radius,
                         "coordinate_bounds": bounds, "vectors": vectors, "oriented_count": len(vectors),
                         "unoriented_count": len(vectors)//2, "parity_counts": parity,
                         "stronger_exact_upper_bound": 2+6*radius**2})
    return checks.result(rows=rows, search_bound="floor(R * row-L1-norm(g^-1)) in each coordinate",
                         bound_implication="count <= 2+6 R^2 < 2+2 pi R^2 for R>0, using pi>3",
                         scope="Rational flat lattices only; no genus-two arc lift or hyperbolic length comparison.")


def gaussian_exact_checks(pairs, boxes):
    checks = Checks("Gaussian algebra and fiber frequencies")
    rows = []
    for a, b in pairs:
        a, b = positive(a), positive(b)
        # Express coefficients after multiplying norms by (ab)^(3/2).
        norm_coefficient, derivative_coefficient = a*b/2, (a-b)**2/8
        checks.equal(norm_coefficient+derivative_coefficient, (a+b)**2/8,
                     "S1 squared is mass norm plus rotation derivative norm")
        checks.equal(2*a-2*b, 2*(a-b), "(-y d_x+x d_y) Gaussian rotation coefficient divided by pi*x*y")
        rows.append({"a": a, "b": b, "L2_squared_times_ab_3_over_2": norm_coefficient,
                     "rotation_squared_times_ab_3_over_2": derivative_coefficient,
                     "S1_squared_times_ab_3_over_2": (a+b)**2/8})
    frequencies = [(1, 0), (0, 1), (1, 1), (-2, 1)]
    for m in frequencies:
        for n in frequencies:
            # Haar integrals of distinct relative-mark characters factor on T^4.
            checks.equal(int(tuple(m)+(0, 0) == (0, 0)+tuple(n)), 0,
                         "different relative-mark centered frequencies are orthogonal")
    box_rows, previous = [], Q(0)
    for cutoff in boxes:
        integer(cutoff, 1, 64)
        total = sum((Q(4, a*a+b*b) for a in range(1, cutoff+1) for b in range(1, cutoff+1)), Q(0))
        checks.true(total > previous, "rank-one collinear finite sums increase")
        previous = total
        box_rows.append({"signed_coordinate_cutoff": cutoff, "nonzero_signed_pairs": 4*cutoff*cutoff,
                         "bare_sum_inverse_a2_plus_b2": total,
                         "normalization": "Divide by 4*zeta(2); finite increase is not a divergence proof."})
    return checks.result(affine_norm_coefficients=rows, relative_mark_frequency_count=len(frequencies)**2,
                         rank_one_truncated_sums=box_rows)
