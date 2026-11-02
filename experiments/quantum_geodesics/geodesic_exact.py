"""Exact finite trace, telescoping, Hessian and decoration identities."""

from itertools import product

import sympy as sp

from .common import ExactChecks, integer, positive, rational


def unfolding_factors():
    checks = ExactChecks()
    checks.equal("stack unfolding factor", sp.Rational(1, 2)*(sp.pi**2/12)/(sp.pi**2/12), sp.Rational(1, 2))
    return checks.result(labels=["eq:torusunfold", "eq:recoverconstant"],
                         scope="rational factor given the stack WP convention")


def trace_checks(fixture):
    checks, matrices, rows = ExactChecks(), [], []
    for index, seed in enumerate(fixture["shear_seeds"]):
        u, v = map(rational, seed[:2])
        sign = integer(seed[2], -1, 1)
        if u == 0 or v == 0 or sign == 0:
            raise ValueError("nonzero shear parameters and sign +/-1 required")
        matrix = sign*sp.Matrix([[1+u*v, u], [v, 1]])
        checks.equal(f"matrix {index}: determinant", matrix.det(), sp.Integer(1))
        matrices.append(matrix)
    if len(matrices) < 6 or not any(m.trace() < 0 for m in matrices) or not any(m.trace() > 0 for m in matrices):
        raise ValueError("at least six matrices with both trace signs required")
    for index, left in enumerate(matrices):
        right = matrices[(index+1) % len(matrices)]
        checks.equal(f"matrix pair {index}: trace polarization", (left*right.inv()).trace(),
                     left.trace()*right.trace()-(left*right).trace())
        rows.append({"A": left.tolist(), "B": right.tolist(), "signed_trace_A": left.trace(),
                     "signed_trace_B": right.trace(), "signed_trace_AB": (left*right).trace()})
    ta, tb, tc = sp.symbols("t_a t_b t_c", positive=True)
    checks.equal("compatible pants sign", ta*tb-(-tc), ta*tb+tc)
    first, second = 2*ta+tb, ta+2*tb
    checks.equal("inverse first pants trace", (2*first-second)/3, ta)
    checks.equal("inverse second pants trace", (2*second-first)/3, tb)
    torus = []
    for raw in fixture["simple_traces"]:
        trace = positive(raw)
        if trace <= 2:
            raise ValueError("hyperbolic simple trace must exceed two")
        values = [2*trace+trace, trace+2*trace, trace*trace+2]
        for label, actual, expected in zip(("N_left", "N_right", "H"), values, (3*trace, 3*trace, trace**2+2)):
            checks.equal(f"t={raw}: {label}", actual, expected)
        torus.append({"simple_trace": trace, "curves": [
            {"topological_label": name, "trace": value} for name, value in zip(("N_left", "N_right", "H"), values)]})
    return checks.result(matrix_pairs=rows, torus_blocks=torus, labels=["eq:figuretrace", "eq:twofigures", "eq:doublepants"],
                         scope="signed matrix algebra separated from compatible pants lifts and declared topological labels")


def kernel_telescope(depths):
    checks, rows = ExactChecks(), []
    for n in depths:
        integer(n, 1, 200)
        # Each h(x_j/3) is an independent formal symbol. No numerical recurrence enters.
        coefficients = [sp.Integer(0)]*(n+1)
        for j in range(n):
            coefficients[j] += sp.Rational((-1)**j, 2**j)
            coefficients[j+1] += sp.Rational((-1)**j, 2**(j+1))
        coefficients[0] -= 1
        for j, value in enumerate(coefficients):
            expected = sp.Rational((-1)**(n-1), 2**n) if j == n else sp.Integer(0)
            checks.equal(f"N={n}: independent symbol h_{j}", value, expected)
        rows.append({"N": n, "remaining_symbol_index": n, "remaining_coefficient": coefficients[-1]})
    return checks.result(rows=rows, labels=["eq:figurefiniteidentity", "eq:figurekerneltail"],
                         scope="exact finite coefficients; no floating cancellation or infinite limit")


def hessian_checks():
    checks = ExactChecks()
    C, cu, cv, sd, su, sv = sp.symbols("C cu cv sd su sv")
    z = C*cu*cv-su*sv
    zu, zv, zuv = C*su*cv-cu*sv, C*cu*sv-su*cv, C*su*sv-cu*cv
    relations = sp.groebner([C*C-sd*sd-1, cu*cu-su*su-1, cv*cv-sv*sv-1], C, cu, cv, sd, su, sv)
    numerators = [z*(z*z-1)-z*zu*zu, z*(z*z-1)-z*zv*zv, zuv*(z*z-1)-z*zu*zv]
    expected = [sd*sd*z*cv*cv, sd*sd*z*cu*cu, -sd*sd*cu*cv]
    for label, actual, target in zip(("uu", "vv", "uv"), numerators, expected):
        checks.equal("Hessian numerator "+label, relations.reduce(sp.expand(actual-target))[1], sp.Integer(0))
    determinant_numerator = expected[0]*expected[1]-expected[2]**2
    checks.equal("Hessian determinant numerator",
                 relations.reduce(sp.expand(determinant_numerator-sd**4*cu**2*cv**2*(z*z-1)))[1], sp.Integer(0))
    return checks.result(labels=["eq:localdistance", "eq:localdistancehessian"],
                         substitutions="C=cosh(d),sd=sinh(d),cu=cosh(u),su=sinh(u),cv=cosh(v),sv=sinh(v)",
                         exact_relations=[C*C-sd*sd-1, cu*cu-su*su-1, cv*cv-sv*sv-1])


def reduce_twist(a_text, tau_text):
    a, tau = positive(a_text), rational(tau_text)
    winding = int(sp.floor(tau/a+sp.Rational(1, 2)))
    reduced = tau-winding*a
    if not -a/2 <= reduced < a/2:
        raise ArithmeticError("exact twist reduction failed")
    return reduced, winding


def uniform_window(a, u):
    if not isinstance(a, sp.Rational) or not isinstance(u, sp.Rational) or a <= 0:
        raise ValueError("positive rational width and rational center required")
    return max(sp.Integer(0), min(sp.Integer(1), u+a/2)-max(sp.Integer(-1), u-a/2))/2


def partition_checks(fixture):
    checks, rows = ExactChecks(), []
    for n in fixture["depths"]+[fixture["large_partition"]["N"]]:
        integer(n, 0, 200)
        coefficients = {}
        for k in range(-n, n+1):
            coefficients[2*k+1] = coefficients.get(2*k+1, 0)+sp.Rational(1, 2)
            coefficients[2*k-1] = coefficients.get(2*k-1, 0)-sp.Rational(1, 2)
        for index, value in coefficients.items():
            expected = sp.Rational(1, 2) if index == 2*n+1 else -sp.Rational(1, 2) if index == -2*n-1 else 0
            checks.equal(f"N={n}: tanh symbol {index}/2", value, sp.sympify(expected))
    for item in fixture["uniform_windows"]:
        a, tau = positive(item["a"]), rational(item["tau"])
        radius = int(sp.ceiling((1+abs(tau)+a/2)/a))+1
        terms = [{"n": n, "mass": uniform_window(a, tau+n*a)} for n in range(-radius, radius+1)]
        checks.equal(f"uniform a={a},tau={tau}: partition", sum(row["mass"] for row in terms), sp.Integer(1))
        checks.equal(f"uniform a={a}: endpoint contact", uniform_window(a, 1+a/2), sp.Integer(0))
        rows.append({"a": a, "tau": tau, "finite_coordinate_bound": radius, "terms": terms})
    return checks.result(uniform_windows=rows, labels=["eq:Hkernel", "eq:Hpartialsumtail"],
                         scope="finite telescoping and exact rational uniform-density windows; only nonnegativity is general")


def position_checks(fixture):
    checks, rows = ExactChecks(), []
    for item in fixture["endpoint_lists"]:
        a = positive(item["circumference"])
        left, right = [list(map(rational, item[key])) for key in ("left", "right")]
        if len(left) != len(right) or len(left) < 2:
            raise ValueError("equal endpoint list lengths at least two required")
        windings = [item[key] for key in ("left_windings", "right_windings")]
        for endpoint_list, lifts in zip((left, right), windings):
            if len(lifts) != len(endpoint_list) or any(not 0 <= x < a for x in endpoint_list):
                raise ValueError("base endpoints in [0,a) and one winding per point required")
            for lift in lifts:
                integer(lift, -10, 10)
        shifts = [(v-u) % a for u, v in zip(left, right)]
        matches = all(value == shifts[0] for value in shifts)
        checks.truth(item["id"]+": expected position condition", matches == item["expected_match"])
        lifted = [[x+k*a for x, k in zip(points, lifts)] for points, lifts in zip((left, right), windings)]
        spacing = [[(points[(i+1) % len(points)]-points[i]) % a for i in range(len(points))]
                   for points in (left, right)]
        rows.append({"id": item["id"], "circumference": a, "base_endpoints": [left, right], "windings": windings,
                     "lifted_endpoints": lifted, "cyclic_spacings": spacing, "shifts_mod_circumference": shifts,
                     "positions_match": matches})
    return checks.result(rows=rows, labels=["eq:endpointmatch", "eq:momentummatch"],
                         scope="prescribed endpoint correspondence and winding data; no reconstruction solver")


def cusp_checks(fixture):
    checks, rows, triangles = ExactChecks(), [], []
    for q_text, ta_text, tb_text in product(fixture["parabolic_q"], fixture["pants_traces"], fixture["pants_traces"]):
        q, ta, tb = map(positive, (q_text, ta_text, tb_text))
        c = (ta+tb)/q
        P = sp.Matrix([[1, q], [0, 1]])
        A = sp.Matrix([[ta/2, ((ta/2)**2-1)/c], [c, ta/2]])
        B = A.inv()*P
        prefix = f"q={q},t_a={ta},t_b={tb}"
        checks.equal(prefix+": det A", A.det(), sp.Integer(1))
        checks.equal(prefix+": det B", B.det(), sp.Integer(1))
        checks.equal(prefix+": AB=P", (A*B-P).norm(), sp.Integer(0))
        checks.equal(prefix+": tr A", A.trace(), ta)
        checks.equal(prefix+": tr B", B.trace(), -tb)
        checks.equal(prefix+": qc_A", q*c, ta+tb)
        rows.append({"q": q, "t_a": ta, "t_b": tb, "c_A": c, "A": A.tolist(), "B": B.tolist(), "P": P.tolist()})
    for item in fixture["triangle_lambdas"]:
        u, v, w = map(positive, item)
        H = 2*(u*u+v*v+w*w)/(u*v*w)
        x, y, z = H*u/2, H*v/2, H*w/2
        flipped = (v*v+w*w)/u
        flipped_H = 2*(flipped**2+v*v+w*w)/(flipped*v*w)
        checks.equal(f"triangle {item}: Markov", x*x+y*y+z*z, x*y*z)
        checks.equal(f"triangle {item}: flip H", flipped_H, H)
        triangles.append({"lambda_lengths": [u, v, w], "H": H, "traces": [x, y, z], "flipped_u": flipped})
    return checks.result(cusp_matrices=rows, triangles=triangles,
                         labels=["eq:cuspray", "eq:cusplambda", "eq:toruscusplambda"],
                         scope="exact decoration and trace algebra; no completeness or embedded-decoration certificate")


def shadow_factor():
    checks = ExactChecks()
    log_coth = sp.Symbol("log_coth")
    checks.equal("two endpoint shadows per unoriented arc", 2*(2*log_coth), 4*log_coth)
    return checks.result(labels=["eq:basmajian"], convention="one shadow=2log(coth(d/2)); unoriented arc has two endpoint shadows")
