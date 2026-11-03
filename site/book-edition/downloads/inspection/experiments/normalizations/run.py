"""Fixed rational normalization checks; no numerical or geometric solver.

Volumes use a=A/pi, WP/pi^(2d), and curvature -1 CH/pi^d. The
intersection calculations are conditional on the stated Mbar_0,4 and
Mbar_0,5 relations. Finite agreement does not prove a global theorem.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations, permutations
import json
from math import factorial, isqrt
from pathlib import Path
import platform
import subprocess
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def rational(value):
    """Fixtures must preserve decimal/rational strings, never binary floats."""
    if type(value) is not str:
        raise ValueError("rational fixture inputs must be strings")
    return Q(value)


def check(condition, message):
    """Remain active with python -O; a failed check must stop the driver."""
    if not condition:
        raise ArithmeticError(message)


def validate_weights(weights, *, flat=False):
    if len(weights) not in (4, 5, 6):
        raise ValueError("only the fixed n=4,5,6 companion is supported")
    if any(not isinstance(w, Q) or not 0 < w <= 1 for w in weights):
        raise ValueError("weights must be exact fractions in (0,1]")
    if flat:
        if any(w == 1 for w in weights) or sum(weights) != 2:
            raise ValueError("flat weights require 0<mu_i<1 and sum(mu)=2")
    elif sum(weights) < 2:
        raise ValueError("the formal genus-zero class requires sum(weights)>=2")


def boundaries(n):
    """Stable unordered bipartitions, each represented by its smaller side."""
    if n not in (4, 5, 6):
        raise ValueError("only n=4,5,6 is supported")
    marks = frozenset(range(n))
    keys = set()
    for size in range(2, n-1):
        for side in combinations(range(n), size):
            complement = tuple(sorted(marks.difference(side)))
            keys.add(min(side, complement, key=lambda s: (len(s), s)))
    return tuple(sorted(keys))


def wall_data(weights):
    """Strictly light sides and balanced boundaries, without complement copies."""
    validate_weights(weights)
    n = len(weights)
    light, balanced = {}, []
    for key in boundaries(n):
        other = tuple(i for i in range(n) if i not in key)
        sums = [sum(weights[i] for i in side) for side in (key, other)]
        active = [side for side, total in zip((key, other), sums) if total < 1]
        check(len(active) <= 1, "complementary sides cannot both be light")
        if active:
            light[key] = active[0]
        if 1 in sums:
            balanced.append(key)
    return light, tuple(balanced)


def psi_class(n, i, auxiliary=None):
    """Standard boundary relation using two fixed marks away from i."""
    choices = list(combinations([j for j in range(n) if j != i], 2))
    j, k = choices[0] if auxiliary is None else auxiliary
    if i in (j, k) or j == k or any(mark not in range(n) for mark in (i, j, k)):
        raise ValueError("psi relation needs three distinct valid marks")
    result = {}
    for key in boundaries(n):
        side = set(key) if i in key else set(range(n)).difference(key)
        result[key] = Q(j not in side and k not in side)
    return result


def average_psi(n, i):
    """Independent closed coefficients from averaging all auxiliary pairs."""
    denominator = Q((n-1)*(n-2), 2)
    return {key: Q((n-len(key))*(n-len(key)-1), 2)/denominator
            if i in key else Q(len(key)*(len(key)-1), 2)/denominator
            for key in boundaries(n)}


def classes(n, *, averaged=False):
    psi = [(average_psi if averaged else psi_class)(n, i) for i in range(n)]
    kappa = {key: sum(p[key] for p in psi)-1 for key in boundaries(n)}
    return psi, kappa


def pairing(left, right):
    """Mbar_0,5 intersection matrix in its ten pair-boundary generators."""
    if set(left) != set(boundaries(5)) or set(right) != set(left):
        raise ValueError("the pairing is only defined for all ten n=5 boundaries")
    return sum(left[a]*right[b]*(-1 if a == b else int(set(a).isdisjoint(b)))
               for a in left for b in right)


def top_intersection(divisor, n):
    if n == 4 and set(divisor) == set(boundaries(4)):
        return sum(divisor.values())
    if n == 5:
        return pairing(divisor, divisor)
    raise ValueError("top intersections are only implemented for n=4,5")


def beta_class(weights, *, averaged=False):
    """AMN class divided by 2*pi^2, including strict light-side corrections.

    sum(weights)=2 is a formal boundary value, not a hyperbolic metric.
    """
    validate_weights(weights)
    n = len(weights)
    psi, kappa = classes(n, averaged=averaged)
    light, _ = wall_data(weights)
    return {key: kappa[key]-sum((1-w)**2*psi[i][key]
                               for i, w in enumerate(weights))
            + ((1-sum(weights[i] for i in light[key]))**2 if key in light else 0)
            for key in boundaries(n)}


def flat_classes(mu):
    validate_weights(mu, flat=True)
    n, D = len(mu), len(mu)-2
    psi, _ = classes(n)
    light, _ = wall_data(mu)
    B, Xi = {}, {}
    for key in boundaries(n):
        total = sum(mu[i] for i in key)
        B[key] = (-sum(w*psi[i][key] for i, w in enumerate(mu))
                  + min(total, 2-total))/2
        Xi[key] = (-sum((1-w)**2*psi[i][key] for i, w in enumerate(mu))
                   + (sum(1-mu[i] for i in light[key])**2 if key in light else 0))
        Xi[key] /= 2*D*D
    return B, Xi


def final_chamber(mu):
    """Physical epsilon<=1, and a strict inequality at every positive wall."""
    validate_weights(mu, flat=True)
    light, _ = wall_data(mu)
    bounds = [(1-sum(mu[i] for i in side))/sum(1-mu[i] for i in side)
              for side in light.values()]
    wall = min(bounds) if bounds else None
    upper = min(Q(1), wall) if wall is not None else Q(1)
    return upper, wall is not None and wall <= 1


def in_final_chamber(mu, epsilon):
    if not isinstance(epsilon, Q):
        raise ValueError("epsilon must be an exact fraction")
    upper, strict = final_chamber(mu)
    return 0 < epsilon < upper if strict else 0 < epsilon <= upper


def wp_polynomial(mu):
    """Coefficients of a=A/pi for WP/pi^(2d), in the final chamber only."""
    B, Xi = flat_classes(mu)
    if len(mu) == 4:
        return {1: 2*sum(B.values()), 2: sum(Xi.values())}
    if len(mu) == 5:
        return {2: 2*pairing(B, B), 3: 2*pairing(B, Xi),
                4: pairing(Xi, Xi)/2}
    raise ValueError("volume polynomials are only implemented for n=4,5")


def evaluate_polynomial(coefficients, a):
    return sum(coefficient*a**power for power, coefficient in coefficients.items())


def wp_from_weights(weights):
    """Direct piecewise class evaluation, with the d! volume denominator."""
    if len(weights) not in (4, 5) or sum(weights) <= 2:
        raise ValueError("hyperbolic checks require n=4,5 and sum(weights)>2")
    d = len(weights)-3
    omega = {key: 2*value for key, value in beta_class(weights).items()}
    return top_intersection(omega, len(weights))/factorial(d)


def set_partitions(items):
    """Each unordered set partition once; no intersection-ring code here."""
    if not items:
        yield ()
        return
    first, *rest = items
    for partition in set_partitions(rest):
        yield ((first,),)+partition
        for j in range(len(partition)):
            yield partition[:j]+((first,)+partition[j],)+partition[j+1:]


def mcmullen_volume(mu):
    """Curvature -1 CH/pi^d from the finite set-partition formula."""
    validate_weights(mu, flat=True)
    d = len(mu)-3
    terms = {k: Q(0) for k in range(3, len(mu)+1)}
    counts = {k: 0 for k in terms}
    for partition in set_partitions(tuple(range(len(mu)))):
        k = len(partition)
        if k < 3:
            continue
        value = Q((-1)**(k+1)*factorial(k-3))
        for block in partition:
            value *= max(1-sum(mu[i] for i in block), Q(0))**(len(block)-1)
        terms[k] += value
        counts[k] += 1
    return Q((-4)**d, factorial(d+1))*sum(terms.values()), terms, counts


def f_curve_pairings(n, parts):
    """Finite probes only: standard boundary/psi pairings with one F-curve."""
    flat = [i for part in parts for i in part]
    if len(parts) != 4 or any(not p for p in parts) or sorted(flat) != list(range(n)):
        raise ValueError("an F-curve needs a partition into four nonempty parts")
    sets = tuple(frozenset(p) for p in parts)
    psi = [Q(any(part == {i} for part in sets)) for i in range(n)]
    delta = {}
    for key in boundaries(n):
        side = frozenset(key)
        other = frozenset(range(n)).difference(side)
        if side in sets or other in sets:
            delta[key] = Q(-1)
        elif any(side == a.union(b) for a, b in combinations(sets, 2)):
            delta[key] = Q(1)
        else:
            delta[key] = Q(0)
    return psi, delta


def f_curve_probe(mu, parts):
    validate_weights(mu, flat=True)
    psi, delta = f_curve_pairings(len(mu), parts)
    kappa = sum(psi)-sum(delta.values())
    light, _ = wall_data(mu)
    beta_zero = kappa-sum((1-mu[i])**2*psi[i] for i in range(len(mu)))
    beta_zero += sum((1-sum(mu[i] for i in side))**2*delta[key]
                     for key, side in light.items())
    linear = 2*sum((1-mu[i])**2*psi[i] for i in range(len(mu)))
    linear -= 2*sum((1-sum(mu[i] for i in side))*sum(1-mu[i] for i in side)*delta[key]
                    for key, side in light.items())
    B = (-sum(mu[i]*psi[i] for i in range(len(mu)))
         + sum(min(sum(mu[i] for i in key), 2-sum(mu[i] for i in key))*value
               for key, value in delta.items()))/2
    check(kappa == 1 and beta_zero == 0 and linear == 2*(len(mu)-2)*B,
          "finite F-curve normalization probe failed")
    return {"kappa_pairing": kappa, "beta_at_zero_pairing": beta_zero,
            "beta_epsilon_linear_pairing": linear, "B_pairing": B}


def determinant(matrix):
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError("a square matrix is required")
    result = Q(0)
    for p in permutations(range(n)):
        inversions = sum(p[i] > p[j] for i in range(n) for j in range(i+1, n))
        term = Q((-1)**inversions)
        for i, j in enumerate(p):
            term *= matrix[i][j]
        result += term
    return result


def normalization_checks():
    perimeter = ((1, 1, 1, 0, 0, 0), (1, 0, 0, 1, 1, 0),
                 (0, 1, 0, 1, 0, 1), (0, 0, 1, 0, 1, 1))
    minor = tuple(tuple(row[i] for i in (2, 3, 4, 5)) for row in perimeter)
    det = determinant(minor)
    a, b = Q(3, 4), Q(2, 3)
    edges = (a, b, 2-a-b, 2-a-b, b, a)
    check(det == -2 and all(sum(x*y for x, y in zip(row, edges)) == 2
                           for row in perimeter), "tetrahedral perimeter check failed")
    interior = (1-a, 1-b, a+b-1)
    check(all(x > 0 for x in interior) and sum(interior) == 1,
          "tetrahedral interior-angle domain check failed")
    area = abs(determinant(((1, 0), (0, 1))))/2
    one_sheet = area/abs(det)
    total_wp = 2*one_sheet*4
    check(total_wp == 2, "the two-sheet WP normalization failed")
    ratios = []
    for square in (Q(0), Q(1, 9), Q(9, 4), Q(-1, 4)):
        sphere = 2+2*square
        torus_stack = (4*square+4)/48
        check(sphere == 24*torus_stack and sphere == 12*(2*torus_stack),
              "sphere/torus stack-effective normalization failed")
        ratios.append({"signed_boundary_square_over_pi2": square,
                       "V04_over_pi2": sphere, "V11_stack_over_pi2": torus_stack,
                       "V11_effective_over_pi2": 2*torus_stack})
    cone_weights = (Q(1), Q(1), Q(1, 4), Q(1, 4))
    cone_volume = wp_from_weights(cone_weights)
    check(cone_volume == Q(1, 4), "large-cone wall correction fixture failed")
    return {"perimeter_minor": minor, "perimeter_minor_determinant": det,
            "eliminated_edge_fixture_over_pi": edges, "angle_triangle_area_over_pi2": area,
            "disintegrated_one_sheet_over_pi2": one_sheet,
            "disintegrated_two_sheets_over_pi2": 2*one_sheet,
            "WP_two_sheets_over_pi2": total_wp, "base_volume_fixtures": ratios,
            "large_cone_example": {"opening_angles_over_pi": [Q(0), Q(0), Q(3, 2), Q(3, 2)],
                                   "naive_over_pi2": Q(-1, 4),
                                   "wall_correction_over_pi2": Q(1, 2),
                                   "corrected_over_pi2": cone_volume}}


def rational_sqrt(value):
    if value < 0:
        raise ValueError("only nonnegative rational squares are supported")
    a, b = isqrt(value.numerator), isqrt(value.denominator)
    if a*a != value.numerator or b*b != value.denominator:
        raise ValueError("this fixed identity needs a rational square root")
    return Q(a, b)


def gram_pfaffian_checks():
    q = Q(2)
    gram = tuple(tuple(Q(1) if i == j else -q for j in range(4)) for i in range(4))
    cosh_b = (q*q+q)/(q*q-1)
    cosh_3a = 4*q**3-3*q
    kernel_inverse = rational_sqrt((cosh_3a-1)/(q-1))
    D = 3*q*q+2*q**3-1
    coth_times_sqrt_D = rational_sqrt((cosh_3a+1)/(cosh_3a-1)*D)
    density_a = 2*kernel_inverse
    density_q = 2/(q*q+q-coth_times_sqrt_D)
    check(determinant(gram) == -135 and cosh_b == q and D == 27,
          "fixed symmetric Gram identity failed")
    check(density_a == 10 and density_q == Q(10, 3)
          and density_q*(q*q-1) == density_a, "arc/Gram density conversion failed")
    skew = ((0, 1, 2, 3), (-1, 0, 5, 7), (-2, -5, 0, 11), (-3, -7, -11, 0))
    pf = skew[0][1]*skew[2][3]-skew[0][2]*skew[1][3]+skew[0][3]*skew[1][2]
    check(pf == 12 and determinant(skew) == pf*pf, "four-dimensional Pfaffian check failed")
    return {"uniform_q": q, "gram_determinant": determinant(gram), "D": D,
            "kernel": 1/kernel_inverse, "arc_density_coefficient": density_a,
            "gram_density_coefficient": density_q, "skew_matrix": skew,
            "pfaffian": pf, "skew_determinant": determinant(skew),
            "inverse_poisson_density_coefficient": Q(1, abs(pf))}


def matmul(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2))
                 for i in range(2))


def trace(matrix):
    return matrix[0][0]+matrix[1][1]


def fricke_fixture(record):
    matrices = [tuple(tuple(rational(x) for x in row) for row in record[name])
                for name in ("A", "B", "C")]
    if any(len(m) != 2 or any(len(row) != 2 for row in m) or determinant(m) != 1
           for m in matrices):
        raise ValueError("Fricke fixtures require 2x2 determinant-one matrices")
    A, B, C = matrices
    X, AC, BC = matmul(A, B), matmul(A, C), matmul(B, C)
    ABC = matmul(X, C)
    D = ((ABC[1][1], -ABC[0][1]), (-ABC[1][0], ABC[0][0]))
    a, b, c, d = (trace(m) for m in (A, B, C, D))
    x, y, z = (trace(m) for m in (X, AC, BC))
    phi = (x*x+y*y+z*z+x*y*z-(a*b+c*d)*x-(a*c+b*d)*y-(a*d+b*c)*z
           +a*a+b*b+c*c+d*d+a*b*c*d-4)
    phi_z = 2*z+x*y-a*d-b*c
    commutator = tuple(tuple(u-v for u, v in zip(r, s))
                       for r, s in zip(matmul(X, C), matmul(C, X)))
    numerator = trace(matmul(A, commutator))
    check(matmul(ABC, D) == ((1, 0), (0, 1)), "ABCD identity failed")
    check(phi == 0 and numerator == -phi_z, "Fricke/twist trace identity failed")
    check(trace(matmul(A, ABC)) == a*d-z and trace(matmul(AC, X)) == x*y-b*c+z,
          "separate Cayley-Hamilton trace reductions failed")
    check((phi_z != 0) is record["chart_nondegenerate"], "unexpected twist chart degeneracy")
    return {"id": record["id"], "D": D, "traces": dict(zip("abcdxyz", (a, b, c, d, x, y, z))),
            "Fricke_residual": phi, "Phi_z": phi_z, "twist_numerator": numerator,
            "chart_nondegenerate": phi_z != 0,
            "scope": "Algebraic SL2 fixture; no global hyperbolic surface realization is asserted."}


def intersection_checks():
    psi4, kappa4 = classes(4)
    check(all(sum(p.values()) == 1 for p in psi4) and sum(kappa4.values()) == 1,
          "Mbar_0,4 intersection fixture failed")
    psi, kappa = classes(5)
    averaged, averaged_kappa = classes(5, averaged=True)
    for i in range(5):
        for j in range(5):
            check(pairing(psi[i], psi[j]) == (1 if i == j else 2), "psi intersections failed")
        difference = {key: psi[i][key]-averaged[i][key] for key in boundaries(5)}
        check(all(pairing(difference, {k: Q(k == key) for k in boundaries(5)}) == 0
                  for key in boundaries(5)), "fixed and averaged psi representatives disagree")
        check(pairing(kappa, psi[i]) == 3, "kappa/psi intersection failed")
    check(pairing(kappa, kappa) == 5 and pairing(averaged_kappa, averaged_kappa) == 5,
          "kappa square intersection failed")
    return {"n4_integral_psi_i": 1, "n4_integral_kappa": 1,
            "n5_integral_psi_i_squared": 1, "n5_integral_psi_i_psi_j_distinct": 2,
            "n5_integral_kappa_psi_i": 3, "n5_integral_kappa_squared": 5,
            "fixed_vs_averaged_psi_numerically_equivalent": True}


def flat_fixture(record):
    mu = tuple(rational(w) for w in record["mu"])
    validate_weights(mu, flat=True)
    n, d, D = len(mu), len(mu)-3, len(mu)-2
    B, Xi = flat_classes(mu)
    ch_intersection = Q(4**d, factorial(d))*top_intersection(B, n)
    ch_partition, terms, counts = mcmullen_volume(mu)
    check(ch_intersection == ch_partition, "McMullen/intersection normalization mismatch")
    zero = beta_class(mu)
    if n == 4:
        check(sum(zero.values()) == 0, "flat beta class did not vanish")
    else:
        check(all(pairing(zero, {k: Q(k == key) for k in boundaries(n)}) == 0
                  for key in boundaries(n)), "flat beta class did not vanish numerically")
    coefficients = wp_polynomial(mu)
    epsilon_upper, strict = final_chamber(mu)
    samples = []
    for epsilon in (epsilon_upper/3, 2*epsilon_upper/3):
        a = 2*D*epsilon
        weights = tuple(w+epsilon*(1-w) for w in mu)
        direct = wp_from_weights(weights)
        predicted = evaluate_polynomial(coefficients, a)
        check(in_final_chamber(mu, epsilon) and direct == predicted,
              "direct AMN/final-chamber polynomial mismatch")
        samples.append({"epsilon": epsilon, "a": a, "weights": weights,
                        "direct_WP_over_pi_2d": direct,
                        "polynomial_WP_over_pi_2d": predicted})
    light, balanced = wall_data(mu)
    return {"id": record["id"], "mu": mu, "complex_dimension": d,
            "light_sides": [{"boundary": key, "side": side,
                             "weight": sum(mu[i] for i in side)} for key, side in light.items()],
            "balanced_boundaries": balanced, "epsilon_upper": epsilon_upper,
            "epsilon_upper_is_strict": strict, "a_upper": 2*D*epsilon_upper,
            "CH_over_pi_d_from_intersections": ch_intersection,
            "CH_over_pi_d_from_partitions": ch_partition,
            "partition_signed_sums_by_block_count": terms, "partition_counts": counts,
            "WP_over_pi_2d_polynomial_in_a": coefficients,
            "intersection_values": ({"B": sum(B.values()), "Xi": sum(Xi.values())} if n == 4
                                    else {"B_squared": pairing(B, B), "B_Xi": pairing(B, Xi),
                                          "Xi_squared": pairing(Xi, Xi)}),
            "direct_piecewise_class_samples": samples}


def source_state():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).rstrip("\n")
    paths = [Path(__file__), HERE/"fixture.json", HERE/"README.md", HERE/"tests/test_normalizations.py",
             ROOT/"book/polyhedral_volumes_and_geodesic_identities.tex"]
    paths += sorted((ROOT/"book/chapters").glob("0[1-8]-*.tex"))
    paths += [ROOT/"book/chapters/appendix-a-fricke.tex"]
    status = git("status", "--porcelain", "--untracked-files=all")
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(status),
            "git_status_porcelain": status.splitlines(),
            "sources": [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path.read_bytes()).hexdigest(),
                         "bytes": path.stat().st_size} for path in paths]}


def json_exact(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(key): json_exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_exact(item) for item in value]
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new JSON path; existing files are refused")
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error("refusing to overwrite existing evidence")
    started = time.perf_counter()
    fixture = json.loads((HERE/"fixture.json").read_text())
    result = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "arithmetic": "Exact finite rational arithmetic (fractions.Fraction); no floating precision parameter.",
              "units": {"area_variable": "a=A/pi", "WP": "V_WP/pi^(2d)", "CH": "V_CH/pi^d, curvature -1"},
              "python_version": platform.python_version(), "source": source_state(),
              "tetrahedron_base_and_cone": normalization_checks(),
              "gram_pfaffian": gram_pfaffian_checks(), "intersection_relations": intersection_checks(),
              "flat_fixtures": [flat_fixture(row) for row in fixture["flat_weights"]],
              "f_curve_probes": [{"id": row["id"], "mu": row["mu"], "parts": row["parts"],
                                  **f_curve_probe(tuple(rational(w) for w in row["mu"]), row["parts"])}
                                 for row in fixture["f_curve_probes"]],
              "sl2_fixtures": [fricke_fixture(row) for row in fixture["sl2_fixtures"]],
              "coverage_limits": [
                  "The stated intersection relations and source theorems are inputs, not computer-proved geometry.",
                  "Top intersections cover only n=4,5; three n=6 F-curve probes do not prove a general divisor identity.",
                  "No numerical quadrature, all-genus volume engine, hyperideal cell solver, or global surface realization.",
                  "Finite cohomology agreement does not prove local metric, measure, or pointwise convergence.",
                  "Balanced walls use strict light subsets; each final polynomial is restricted to its stated chamber."
              ], "checks_passed": True}
    result["elapsed_seconds"] = time.perf_counter()-started
    with args.output.open("x") as handle:
        json.dump(json_exact(result), handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(f"All fixed exact checks passed; wrote {args.output}")


if __name__ == "__main__":
    main()
