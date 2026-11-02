"""G4-G5/G8-G9: local hyperbolic formulas and independent matrix references."""

from itertools import product

from .common import NumericChecks, context, mpq, number, require


def real_domain(ctx, *values):
    if any(not ctx.isfinite(value) or ctx.im(value) != 0 for value in values):
        raise ValueError("finite real coordinates required")


def acosh_real(ctx, value):
    real_domain(ctx, value)
    if value < 1:
        raise ValueError("real acosh requires argument at least one; no clamping")
    return ctx.acosh(value)


def local_distance(ctx, d, u, v):
    real_domain(ctx, d, u, v)
    if d <= 0:
        raise ValueError("local endpoint distance requires d>0")
    p = [ctx.cosh(u), ctx.sinh(u), ctx.mpf(0)]
    q = [ctx.cosh(d)*ctx.cosh(v), ctx.sinh(v), ctx.sinh(d)*ctx.cosh(v)]
    z = p[0]*q[0]-p[1]*q[1]-p[2]*q[2]
    return acosh_real(ctx, z)


def distance_data(ctx, d, u, v):
    real_domain(ctx, d, u, v)
    if d <= 0:
        raise ValueError("local endpoint distance requires d>0")
    C, cu, su, cv, sv = ctx.cosh(d), ctx.cosh(u), ctx.sinh(u), ctx.cosh(v), ctx.sinh(v)
    z = C*cu*cv-su*sv
    if z <= 1:
        raise ValueError("strict endpoint-distance domain was lost")
    S = ctx.sqrt((z-1)*(z+1))
    gradient = [(C*su*cv-cu*sv)/S, (C*cu*sv-su*cv)/S]
    factor = ctx.sinh(d)**2/S**3
    hessian = [[factor*z*cv*cv, -factor*cu*cv], [-factor*cu*cv, factor*z*cu*cu]]
    determinant = ctx.sinh(d)**4*cu**2*cv**2/S**4
    return z, gradient, hessian, determinant


def distance_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows = NumericChecks(ctx, digits, guards), []
    for d_text in fixture["distances"]:
        d = mpq(ctx, d_text)
        checks.positive(f"d={d_text}: minimum distance", local_distance(ctx, d, 0, 0), d)
        for index, pair in enumerate(fixture["endpoints"]):
            u, v = [mpq(ctx, value) for value in pair]
            z, gradient, hessian, determinant = distance_data(ctx, d, u, v)
            D = local_distance(ctx, d, u, v)
            prefix = f"d={d_text},pair={index}"
            checks.positive(prefix+": Lorentz distance", D, acosh_real(ctx, z))
            for i, order in enumerate(((1, 0), (0, 1))):
                actual = ctx.diff(lambda x, y: local_distance(ctx, d, x, y), (u, v), order)
                checks.close(prefix+f": gradient {i}", actual, gradient[i], scale=ctx.mpf(1))
            for i, j, order in ((0, 0, (2, 0)), (1, 1, (0, 2)), (0, 1, (1, 1))):
                actual = ctx.diff(lambda x, y: local_distance(ctx, d, x, y), (u, v), order)
                if i == j:
                    checks.positive(prefix+f": Hessian {i}{j}", actual, hessian[i][j])
                else:
                    checks.close(prefix+": Hessian mixed", actual, hessian[i][j], scale=abs(hessian[i][j]))
            numeric_det = hessian[0][0]*hessian[1][1]-hessian[0][1]*hessian[1][0]
            checks.positive(prefix+": Hessian determinant", numeric_det, determinant)
            reversed_orientation = acosh_real(ctx, ctx.cosh(d)*ctx.cosh(u)*ctx.cosh(v)+ctx.sinh(u)*ctx.sinh(v))
            checks.positive(prefix+": v orientation reversal", local_distance(ctx, d, u, -v), reversed_orientation)
            checks.observe(prefix+": D", D, positive_signal=True)
            checks.observe(prefix+": determinant", determinant, positive_signal=True)
            rows.append({"d": d_text, "u_v": pair, "D": number(ctx, D),
                         "gradient": [number(ctx, x) for x in gradient],
                         "Hessian": [[number(ctx, x) for x in row] for row in hessian],
                         "positive_determinant": number(ctx, determinant)})
    return checks.result(rows=rows, labels=["eq:localdistance", "eq:localdistancehessian"],
                         coordinates="curvature -1 hyperboloid, Lorentz signature -++; oriented endpoint coordinates u,v",
                         oracle="numerical derivatives of independent Lorentz distance; same mpmath backend",
                         exact_algebra="separate G4 exact records reduce hyperbolic polynomial identities")


def torus_delta(ctx, a, b):
    real_domain(ctx, a, b)
    if a <= 0 or b < 0:
        raise ValueError("torus cuff requires a>0 and boundary b>=0")
    delta = (1+ctx.cosh(b/2))/(2*ctx.sinh(a/2)**2)
    require(ctx.isfinite(delta) and delta > 0, "positive delta was lost")
    return delta


def torus_length(ctx, a, b, tau):
    real_domain(ctx, tau)
    delta = torus_delta(ctx, a, b)
    return 2*ctx.asinh(ctx.sqrt(delta+(1+delta)*ctx.sinh(tau/2)**2))


def torus_matrices(ctx, a, b, tau):
    real_domain(ctx, tau)
    delta = torus_delta(ctx, a, b)
    A = ctx.sqrt(1+delta)
    X = ctx.matrix([[ctx.exp(a/2), 0], [0, ctx.exp(-a/2)]])
    base = ctx.matrix([[A, ctx.sqrt(delta)], [ctx.sqrt(delta), A]])
    twist = ctx.matrix([[ctx.exp(tau/2), 0], [0, ctx.exp(-tau/2)]])
    return X, twist*base


def trace(matrix):
    return matrix[0, 0]+matrix[1, 1]


def matrix_length(ctx, a, b, tau):
    _, matrix = torus_matrices(ctx, a, b, tau)
    return 2*acosh_real(ctx, abs(trace(matrix))/2)


def seam_distance(ctx, a, b, c):
    real_domain(ctx, a, b, c)
    if a <= 0 or b <= 0 or c < 0:
        raise ValueError("ordinary seams require a,b>0 and c>=0")
    cosine = (ctx.cosh(c/2)+ctx.cosh(a/2)*ctx.cosh(b/2))/(ctx.sinh(a/2)*ctx.sinh(b/2))
    return acosh_real(ctx, cosine)


def holonomy_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, seams, rows, minima = NumericChecks(ctx, digits, guards), [], [], []
    for index, item in enumerate(fixture["seams"]):
        a, b, c = [mpq(ctx, value) for value in item]
        d = seam_distance(ctx, a, b, c)
        lhs = ctx.cosh(d)*ctx.sinh(a/2)*ctx.sinh(b/2)
        rhs = ctx.cosh(c/2)+ctx.cosh(a/2)*ctx.cosh(b/2)
        checks.positive(f"seam {index}: rearranged hexagon", lhs, rhs)
        X = ctx.matrix([[ctx.exp(a/2), 0], [0, ctx.exp(-a/2)]])
        J = ctx.matrix([[ctx.cosh(d/2), ctx.sinh(d/2)], [ctx.sinh(d/2), ctx.cosh(d/2)]])
        Y = J*ctx.matrix([[ctx.exp(-b/2), 0], [0, ctx.exp(b/2)]])*J**-1
        target = -2*ctx.cosh(c/2)
        checks.close(f"seam {index}: independent matrix trace", trace(X*Y), target, scale=abs(target))
        checks.observe(f"seam {index}: d", d, positive_signal=True)
        seams.append({"a_b_c": item, "d": number(ctx, d), "matrix_trace_XY": number(ctx, trace(X*Y))})
    cases = [(a, b, tau, False) for a, b, tau in product(fixture["cuffs"], fixture["boundaries"], fixture["twists"])]
    cases += [(fixture["small_cuff"], b, tau, True) for b, tau in product(fixture["small_boundaries"], fixture["small_twists"])]
    for index, (a_text, b_text, tau_text, small) in enumerate(cases):
        a, b, tau = [mpq(ctx, value) for value in (a_text, b_text, tau_text)]
        delta = torus_delta(ctx, a, b)
        A = ctx.sqrt(1+delta)
        X, B = torus_matrices(ctx, a, b, tau)
        commutator = X*B*X**-1*B**-1
        target = -2*ctx.cosh(b/2)
        checks.positive(f"torus {index}: determinant", ctx.det(B), ctx.mpf(1))
        checks.close(f"torus {index}: commutator trace", trace(commutator), target, scale=abs(target))
        checks.positive(f"torus {index}: trace", trace(B), 2*A*ctx.cosh(tau/2))
        length = torus_length(ctx, a, b, tau)
        checks.positive(f"torus {index}: stable length versus matrix", length, matrix_length(ctx, a, b, tau))
        Q = delta+(1+delta)*ctx.sinh(tau/2)**2
        first = A*ctx.sinh(tau/2)/ctx.sqrt(Q)
        second = A*delta*ctx.cosh(tau/2)/(2*Q**ctx.mpf("1.5"))
        checks.close(f"torus {index}: first derivative", ctx.diff(lambda t: matrix_length(ctx, a, b, t), tau), first, scale=ctx.mpf(1))
        checks.positive(f"torus {index}: second derivative", ctx.diff(lambda t: matrix_length(ctx, a, b, t), tau, 2), second)
        require(abs(first) < 1 and second > 0, "finite torus derivative inequalities failed")
        loss_budget = max(0, 4*int(ctx.ceil(-ctx.log10(a))))+10
        require(ctx.dps-loss_budget > digits-15, "matrix reference has insufficient declared cancellation budget")
        checks.observe(f"torus {index}: length", length, positive_signal=True)
        checks.observe(f"torus {index}: second derivative", second, positive_signal=True)
        rows.append({"a": a_text, "b": b_text, "tau": tau_text, "small_cuff_fixture": small,
                     "delta": number(ctx, delta), "length": number(ctx, length),
                     "first_derivative": number(ctx, first), "second_derivative": number(ctx, second),
                     "matrix_reference_actual_digits": ctx.dps, "estimated_cancellation_digit_budget": loss_budget,
                     "estimated_reference_digits_after_cancellation": ctx.dps-loss_budget,
                     "reference_limit_status": "conditioning budget and observed residual, not certified accuracy"})
    for raw in fixture["large_cuff_minima"]:
        a = mpq(ctx, raw)
        length = torus_length(ctx, a, ctx.mpf(0), ctx.mpf(0))
        q = ctx.exp(-a/2)
        independent = 2*(ctx.log1p(q)-ctx.log1p(-q))
        checks.positive(f"large cuff {raw}: retained minimum", length, independent)
        direct = matrix_length(ctx, a, ctx.mpf(0), ctx.mpf(0))
        checks.observe(f"large cuff {raw}: minimum", length, positive_signal=True)
        minima.append({"a": raw, "b": "0", "tau": "0", "stable_length": number(ctx, length),
                       "direct_matrix_acosh_length": number(ctx, direct),
                       "direct_route_status": "cancellation-limited; not accepted as a relative reference"})
    return checks.result(seams=seams, torus_rows=rows, large_cuff_minima=minima,
                         labels=["eq:seam", "eq:Atwist", "eq:torustwist", "eq:torustwistderivatives"],
                         coordinates="signed displacement twist; fixed crossing length is not periodic; cusp boundary b=0 allowed",
                         conditioning="small-cuff matrix commutators use declared extra guards; estimates are not error enclosures")


def matching_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows = NumericChecks(ctx, digits, guards), []
    for item in fixture["stationarity"]:
        d, e, u, v, tau, x = [mpq(ctx, item[key]) for key in ("d", "e", "u", "v", "tau", "x")]
        actual = ctx.diff(lambda y: local_distance(ctx, d, u, y)+local_distance(ctx, e, y+tau, v), x)
        gradient1 = distance_data(ctx, d, u, x)[1]
        gradient2 = distance_data(ctx, e, x+tau, v)[1]
        expected = gradient1[1]+gradient2[0]
        checks.close(item["id"]+": endpoint stationarity derivative", actual, expected, scale=ctx.mpf(2))
        if item["stationary"]:
            checks.close(item["id"]+": orthogonal stationary derivative", expected, 0, scale=ctx.mpf(2))
        else:
            require(abs(expected) > checks.tolerance*2, "shifted matched point must be nonstationary")
        checks.observe(item["id"]+": derivative", expected, scale=ctx.mpf(2))
        rows.append({**item, "derivative": number(ctx, expected), "positions_can_match": True,
                     "directions_match_at_declared_point": item["stationary"]})
    return checks.result(rows=rows, labels=["eq:endpointmatch", "eq:momentummatch"],
                         formula="S(x)=D_d(u,x)+D_e(x+tau,v)", scope="local demonstration, not closed-curve reconstruction")


def cusp_numerics(fixture, digits, guards):
    from .kernels import h_trace

    ctx = context(digits, guards)
    checks, rows, torus = NumericChecks(ctx, digits, guards), [], []
    for q_text, ta_text, tb_text, H_text in product(fixture["parabolic_q"], fixture["pants_traces"],
                                                  fixture["pants_traces"], fixture["horocycles"]):
        q, ta, tb, H = [mpq(ctx, value) for value in (q_text, ta_text, tb_text, H_text)]
        if min(q, ta, tb, H) <= 0:
            raise ValueError("positive cusp data required")
        c, Y = (ta+tb)/q, q/H
        image_top = 1/(c*c*Y)
        actual = ctx.log(Y/image_top)
        expected = 2*ctx.log((ta+tb)/H)
        prefix = f"q={q_text},ta={ta_text},tb={tb_text},H={H_text}"
        checks.close(prefix+": signed vertical separation", actual, expected, scale=1+abs(expected))
        checks.positive(prefix+": lambda", ctx.exp(actual/2), (ta+tb)/H)
        rows.append({"q": q_text, "t_a": ta_text, "t_b": tb_text, "H": H_text,
                     "Y": number(ctx, Y), "image_horocycle_top": number(ctx, image_top), "signed_length": number(ctx, actual)})
    for t_text, H_text in product(fixture["simple_traces"], fixture["horocycles"]):
        t, H = mpq(ctx, t_text), mpq(ctx, H_text)
        if H <= 0 or t <= 2:
            raise ValueError("positive H and t>2 required")
        lam = 2*t/H
        d = 2*ctx.log(lam)
        z = 16*ctx.exp(-d)/(H*H)
        weight = z/(1+ctx.sqrt(1-z))
        prefix = f"t={t_text},H={H_text}"
        checks.positive(prefix+": lambda exp(d/2)", ctx.exp(d/2), lam)
        checks.positive(prefix+": cusp weight", weight, h_trace(ctx, t))
        checks.positive(prefix+": direct well-conditioned cusp weight", 1-ctx.sqrt(1-z), weight)
        for k_text in fixture["decoration_rescalings"]:
            k = mpq(ctx, k_text)
            if k <= 0:
                raise ValueError("decoration rescaling must be positive")
            new_d = 2*ctx.log(2*t/(k*H))
            checks.close(prefix+f": rescaling k={k_text}", new_d, d-2*ctx.log(k), scale=1+abs(d)+2*abs(ctx.log(k)))
            new_z = 16*ctx.exp(-new_d)/(k*H)**2
            checks.positive(prefix+f": invariant weight k={k_text}", new_z/(1+ctx.sqrt(1-new_z)), weight)
        checks.observe(prefix+": lambda", lam, positive_signal=True)
        torus.append({"t": t_text, "H": H_text, "lambda": number(ctx, lam), "signed_length": number(ctx, d),
                      "weight": number(ctx, weight), "decoration_status": "formal signed truncation; large H not claimed embedded"})
    return checks.result(cusp_rows=rows, torus_rows=torus, labels=["eq:cusplambda", "eq:toruscusplambda", "eq:cusporthoidentity"],
                         convention="lambda=exp(d/2), no sqrt(2); signed truncated lengths permit overlap")
