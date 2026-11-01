"""Exact finite Möbius, dyadic, multiplicity, row, and power-balance checks."""

from collections import defaultdict
from fractions import Fraction as Q
from math import gcd

from .exact import Checks, ceil, divisors, floor, integer, mobius, phi, positive, rational


def lattice_points(radius, gauge):
    radius = positive(radius)
    if gauge == "square":
        bounds = [floor(radius), floor(radius)]

        def length(m, n):
            return Q(max(abs(m), abs(n)))
    elif gauge == "rational_diamond":
        bounds = [floor(radius), floor(2*radius/3)]

        def length(m, n):
            return abs(m)+Q(3, 2)*abs(n)
    else:
        raise ValueError("unknown rational lattice gauge")
    if max(bounds) > 100:
        raise ValueError("finite lattice fixture bound exceeds 100")
    return [(m, n, length(m, n)) for m in range(-bounds[0], bounds[0]+1)
            for n in range(-bounds[1], bounds[1]+1)
            if (m or n) and length(m, n) <= radius]


def mertens(n):
    integer(n)
    return sum(mobius(d) for d in range(1, n+1))


def square_a(radius):
    radius = positive(radius)
    k = floor(radius)
    return 4*k*(k+1)


def mobius_checks(cutoffs):
    checks = Checks("finite square and diamond Mobius inversion")
    rows, tail_rows = [], []
    for cutoff in map(positive, cutoffs):
        if cutoff > 20:
            raise ValueError("Möbius fixture cutoff exceeds 20")
        expected = 8*sum(phi(n) for n in range(1, floor(cutoff)+1))
        weighted = sum(mobius(d)*square_a(cutoff/d) for d in range(1, floor(cutoff)+1))
        square = lattice_points(cutoff, "square")
        checks.equal(len(square), square_a(cutoff), "unit square shell formula")
        checks.equal(weighted, expected, "square Mobius sum equals totient formula")
        checks.equal(sum(gcd(m, n) == 1 for m, n, _ in square), expected, "direct primitive square points")
        rows.append({"L": cutoff, "all_nonzero_square_vectors": len(square),
                     "primitive_signed_square_vectors": expected})
        for gauge in ("square", "rational_diamond"):
            for dmax in range(1, floor(cutoff)+1):
                direct_tail = sum(mobius(d)*len(lattice_points(cutoff/d, gauge))
                                  for d in range(dmax+1, floor(cutoff)+1))
                points = lattice_points(cutoff/dmax, gauge)
                contributions = [mertens(floor(cutoff/r))-mertens(dmax) for _, _, r in points]
                checks.equal(direct_tail, sum(contributions), "finite Mertens-tail lattice identity")
                boundary = [i for i, (_, _, r) in enumerate(points) if r == cutoff/dmax]
                checks.true(all(contributions[i] == 0 for i in boundary), "cutoff boundary retains zero summands")
                tail_rows.append({"gauge": gauge, "L": cutoff, "D": dmax,
                                  "tail": direct_tail, "lattice_terms": len(points),
                                  "zero_terms": contributions.count(0), "boundary_zero_terms": len(boundary)})
    return checks.result(square_rows=rows, tail_rows=tail_rows,
                         gauge_definitions={"square": "max(|m|,|n|)",
                                            "rational_diamond": "|m|+(3/2)|n|"},
                         area_density_status="Area/zeta(2) is not evaluated or certified by rational fixtures.")


def block_metrics(lengths, start):
    """Exact finite right-continuous event sweep, including interior left limits."""
    lengths, start = [positive(ell) for ell in lengths], positive(start)
    end = 2*start
    events = defaultdict(lambda: {"half": 0, "full": 0})
    for ell in lengths:
        events[ell/2]["half"] += 1
        events[ell]["full"] += 1
    d = sum(ell <= 2*start for ell in lengths)-4*sum(ell <= start for ell in lengths)
    candidates = [{"position": start, "side": "actual", "D": d, "normalized_abs": abs(d)/start}]
    previous, integral, groups, segments = start, Q(0), [], []
    for position in sorted(x for x in events if start < x <= end):
        integral += d*d*(1/previous-1/position)
        segments.append({"left": previous, "right": position, "D": d})
        candidates.append({"position": position, "side": "left_limit", "D": d,
                           "normalized_abs": abs(d)/position})
        before = d
        d += events[position]["half"]-4*events[position]["full"]
        candidates.append({"position": position, "side": "actual", "D": d,
                           "normalized_abs": abs(d)/position})
        groups.append({"position": position, **events[position], "D_left": before, "D_actual": d})
        previous = position
    if previous < end:
        integral += d*d*(1/previous-1/end)
        segments.append({"left": previous, "right": end, "D": d})
        candidates.append({"position": end, "side": "actual", "D": d,
                           "normalized_abs": abs(d)/end})
    maximum = max(row["normalized_abs"] for row in candidates)
    return {"T": start, "M": maximum, "Q_squared": integral/start,
            "event_groups": groups, "segments": segments,
            "maximizers": [row for row in candidates if row["normalized_abs"] == maximum],
            "boundary_convention": "N(u)=#{ell<=u}; no external left limit at T; both sides at 2T."}


def direct_block_metrics(lengths, start):
    """Independent direct counts at endpoints and exact interval midpoints."""
    lengths, start = [positive(ell) for ell in lengths], positive(start)
    points = sorted({start, 2*start} | {x for ell in lengths for x in (ell, ell/2) if start < x < 2*start})
    values, integral = [], Q(0)
    for point in points:
        actual = sum(ell <= 2*point for ell in lengths)-4*sum(ell <= point for ell in lengths)
        values.append(abs(actual)/point)
        if point > start:
            left = sum(ell < 2*point for ell in lengths)-4*sum(ell < point for ell in lengths)
            values.append(abs(left)/point)
    for a, b in zip(points, points[1:]):
        middle = (a+b)/2
        d = sum(ell <= 2*middle for ell in lengths)-4*sum(ell <= middle for ell in lengths)
        integral += d*d*(1/a-1/b)
    return {"M": max(values), "Q_squared": integral/start}


def dyadic_checks(lengths, starts, depths):
    checks = Checks("finite dyadic identity and event arithmetic")
    lengths = [positive(v) for v in lengths]
    rows = []
    for start in map(positive, starts):
        actual = block_metrics(lengths, start)
        expected = direct_block_metrics(lengths, start)
        checks.equal(actual["M"], expected["M"], "sweep/direct maximum")
        checks.equal(actual["Q_squared"], expected["Q_squared"], "sweep/direct exact integral")
        rows.append(actual)
    special = block_metrics([2, 2, 4, 5, 8], 2)
    checks.equal(special["M"], Q(5, 2), "printed finite-list maximum")
    checks.equal(special["Q_squared"], Q(49, 20), "printed finite-list square mean")
    telescopes = []
    for cutoff in (Q(3, 2), Q(2), Q(7, 3)):
        c, b, d = Q(3, 2), Q(-2), Q(5)

        def polynomial(u):
            return c*u*u+b*u+d

        def count(u):
            return sum(ell <= u for ell in lengths)

        checks.equal(polynomial(2*cutoff)-4*polynomial(cutoff), -2*b*cutoff-3*d,
                     "quadratic main term cancels with correct linear and constant coefficients")
        for depth in depths:
            integer(depth, 1, 10)
            for name, func in (("polynomial", polynomial), ("finite_list", count)):
                lhs = func(cutoff)-c*cutoff**2
                rhs = Q(1, 4**depth)*(func(2**depth*cutoff)-c*(2**depth*cutoff)**2)
                rhs -= sum(Q(1, 4**(j+1))*(func(2**(j+1)*cutoff)-4*func(2**j*cutoff))
                           for j in range(depth))
                checks.equal(lhs, rhs, "finite dyadic telescope")
                telescopes.append({"model": name, "L": cutoff, "depth": depth, "E": lhs})
    multiples = []
    for cutoff in (Q(4), Q(11, 2), Q(10)):
        # Each index is a primitive class: equal lengths remain different classes.
        explicit = [(index, sign, m) for index, ell in enumerate(lengths) for sign in (-1, 1)
                    for m in range(1, floor(cutoff/ell)+1)]
        expected = 2*sum(floor(cutoff/ell) for ell in lengths)
        checks.equal(len(explicit), expected, "signed positive multiples preserve curve multiplicity")
        multiples.append({"L": cutoff, "signed_multiples": len(explicit)})
    return checks.result(lengths=lengths, block_rows=rows, printed_fixture=special,
                         telescoping_rows=telescopes, signed_multiples=multiples,
                         shortest_primitive_formal_length=min(lengths),
                         length_units="Formal primitive lengths; no hyperbolic or shortest-vector unit identification.")


def row_count(a, b, n):
    a, b, n = rational(a), rational(b), integer(n, 1)
    if a > b:
        raise ValueError("row endpoints must satisfy a<=b")
    return sum(mobius(d)*(floor(b/d)-ceil(a/d)+1) for d in divisors(n))


def balance(alpha, theta):
    alpha, theta = rational(alpha), rational(theta)
    if not 0 <= alpha < 2 or not 0 <= theta < 1:
        raise ValueError("balance fixture requires 0<=alpha<2 and 0<=theta<1")
    denominator = 3-alpha-theta
    return (2-alpha)/denominator, (2-alpha*theta)/denominator


def row_balance_checks(rows, n_values, thetas):
    checks = Checks("row divisor identity and conditional exponent balance")
    results = []
    for a, b in rows:
        a, b = rational(a), rational(b)
        for n in n_values:
            actual = row_count(a, b, n)
            expected = sum(gcd(m, n) == 1 for m in range(ceil(a), floor(b)+1))
            checks.equal(actual, expected, "row Mobius selector equals direct gcd count")
            results.append({"a": a, "b": b, "n": n, "coprime_integer_count": actual})
    balances = []
    expected_exponents = {Q(1, 2): Q(10, 11), Q(7, 8): Q(34, 35), Q(11, 12): Q(50, 51)}
    for theta in map(rational, thetas):
        alpha = Q(2, 3)
        d, kappa = balance(alpha, theta)
        checks.equal(kappa, expected_exponents[theta], "printed exact conditional exponent")
        checks.equal(alpha+d*(1-alpha), 2-d*(2-theta), "geometric and arithmetic powers meet")
        checks.equal(kappa, alpha+d*(1-alpha), "balanced exponent")
        checks.true(0 < d < 1, "admissible split power")
        balances.append({"alpha": alpha, "theta": theta, "split_power_d": d, "kappa": kappa})
    return checks.result(row_cases=results, balance_cases=balances,
                         scope="Finite identities and conditional algebra; no Mertens bound or sharp remainder theorem.")
