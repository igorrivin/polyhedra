"""G1/G3/G7/G10: finite integrals, stable positive kernels and analytic tails."""

from itertools import product

import sympy as sp

from .common import NumericChecks, context, integer, mpq, number, require
from .geodesic_exact import reduce_twist
from .geometry import real_domain, torus_delta, torus_length


def fermi_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows, sums = NumericChecks(ctx, digits, guards), [], []
    target = ctx.pi**2/12
    for m in fixture["alternating_depths"]:
        integer(m, 1, 2000)
        exact = sum(sp.Rational((-1)**(k-1), k*k) for k in range(1, m+1))
        actual = mpq(ctx, exact)
        tail = ctx.mpf(1)/(m+1)**2
        residual = target-actual
        checks.bounded(f"Dirichlet M={m}: alternating remainder", residual, target, tail)
        require((-1)**m*residual > 0, "alternating remainder sign failed")
        sums.append({"M": m, "exact_rational_sum": str(exact), "sum": number(ctx, actual),
                     "signed_remainder": number(ctx, residual), "remainder_sign": (-1)**m,
                     "analytic_tail_bound": number(ctx, tail)})
    for cutoff in fixture["cutoffs"]:
        integer(cutoff, 1, 100)
        integral, estimated = ctx.quad(lambda x: x/(1+ctx.exp(x)), [0, cutoff/2, cutoff], error=True)
        tail = (cutoff+1)*ctx.exp(-cutoff)
        residual = target-integral
        require(integral > 0 and residual > 0, "finite Fermi integral or omitted tail lost positivity")
        checks.bounded(f"R={cutoff}: Fermi total and finite tail", residual, target, tail)
        checks.bounded(f"R={cutoff}: quadrature heuristic error", estimated, integral)
        for row in sums:
            checks.bounded(f"R={cutoff},M={row['M']}: finite integral versus finite sum",
                           integral-ctx.mpf(row["sum"]), target, tail+ctx.mpf(row["analytic_tail_bound"]))
        checks.observe(f"R={cutoff}: finite Fermi integral", integral, positive_signal=True)
        rows.append({"R": cutoff, "finite_integral": number(ctx, integral), "pi_squared_over_12": number(ctx, target),
                     "signed_omitted_integral": number(ctx, residual), "analytic_integral_tail_bound": number(ctx, tail),
                     "quadrature_error_estimate_uncertified": number(ctx, estimated)})
    return checks.result(rows=rows, alternating_sums=sums, labels=["eq:torusunfold", "eq:recoverconstant"],
                         formula="I_R=integral_0^R x/(1+exp(x)) dx; total=pi^2/12",
                         tail_status="analytic integral and alternating-series tails are separate from heuristic quadrature estimates and floating budget")


def h_trace(ctx, t):
    real_domain(ctx, t)
    if t <= 2:
        raise ValueError("h requires a hyperbolic trace t>2")
    inverse = 4/(t*t)
    result = inverse/(1+ctx.sqrt(1-inverse))
    require(ctx.isfinite(result) and result > 0, "stable h lost its positive signal")
    return result


def kernel_partial(ctx, x, n):
    real_domain(ctx, x)
    integer(n, 1, 200)
    if x <= 6:
        raise ValueError("universal kernel input must exceed six")
    total = ctx.mpf(0)
    current = x
    for j in range(n):
        total += ctx.mpf((-1)**j)/2**(j+1)*h_trace(ctx, current/3)
        current = current*current/9+2
    tail_h = h_trace(ctx, current/3)
    tail = tail_h/2**(n+1)
    log_tail = -(n+1)*ctx.log(2)+ctx.log(tail_h)
    require(total > 0 and tail > 0 and ctx.isfinite(log_tail), "kernel partial or tail lost positivity")
    return total, tail, log_tail, current


def kernel_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows, blocks = NumericChecks(ctx, digits, guards), [], []
    for x_text, n in product(fixture["inputs"], fixture["depths"]):
        x = mpq(ctx, x_text)
        partial, tail, log_tail, iterate = kernel_partial(ctx, x, n)
        shifted = kernel_partial(ctx, x*x/9+2, n)[0]
        h = h_trace(ctx, x/3)
        left = 2*partial+shifted-h
        right = (-1)**(n-1)*2*tail
        prefix = f"x={x_text},N={n}"
        cancellation_limited = abs(right) <= checks.tolerance*h
        if cancellation_limited:
            checks.close(prefix+": finite residual at source scale", left, right, scale=h)
            status = "cancellation-limited; not a relative verification of the tiny nonzero right-hand side"
        else:
            require(left*right > 0, "resolved finite residual has wrong sign or is zero")
            checks.close(prefix+": resolved finite residual", left, right, scale=abs(right))
            status = "finite residual resolved relative to its nonzero right-hand side"
        checks.positive(prefix+": stable scaled h at final iterate", (iterate/3)**2*h_trace(ctx, iterate/3),
                        4/(1+ctx.sqrt(1-4/(iterate/3)**2)))
        checks.positive(prefix+": tail logarithm reconstruction", ctx.exp(log_tail), tail)
        checks.bounded(prefix+": tail <=2^(-N-1) violation", max(ctx.mpf(0), tail-ctx.mpf(1)/2**(n+1)), ctx.mpf(1)/2**(n+1))
        lower = partial-tail if n % 2 else partial
        upper = partial if n % 2 else partial+tail
        checks.bounded(prefix+": F lower bound violation", min(ctx.mpf(0), lower-h/4), h)
        checks.bounded(prefix+": F upper bound violation", max(ctx.mpf(0), upper-h/2), h)
        direct_h = 1-ctx.sqrt(1-4/(x/3)**2)
        checks.positive(prefix+": well-conditioned direct h", direct_h, h)
        checks.observe(prefix+": F_N", partial, positive_signal=True)
        # Log tails are more meaningful across rapidly growing iterates than printing an enormous exponent alone.
        checks.observe(prefix+": log B_N", log_tail, scale=abs(log_tail))
        rows.append({"x": x_text, "N": n, "F_N": number(ctx, partial), "positive_B_N": number(ctx, tail),
                     "log_B_N": number(ctx, log_tail), "remainder_sign": (-1)**n,
                     "finite_residual_left": number(ctx, left), "finite_residual_right": number(ctx, right),
                     "source_scale_h": number(ctx, h), "uncertified_source_rounding_budget": number(ctx, checks.tolerance*h),
                     "residual_status": status, "analytic_interval_lower": number(ctx, lower), "analytic_interval_upper": number(ctx, upper),
                     "x_squared_F_N_asymptotic_illustration": number(ctx, x*x*partial)})
    for t_text, n in product(fixture["simple_traces"], fixture["depths"]):
        t = mpq(ctx, t_text)
        first, tail1, _, _ = kernel_partial(ctx, 3*t, n)
        second, tail2, _, _ = kernel_partial(ctx, t*t+2, n)
        target = h_trace(ctx, t)
        allowance = 2*tail1+tail2
        residual = 2*first+second-target
        checks.bounded(f"simple trace {t_text},N={n}: three-curve block", residual, target, allowance)
        blocks.append({"simple_trace": t_text, "N": n, "labels": ["N_left", "N_right", "H"],
                       "partial_block_sum": number(ctx, 2*first+second), "h_simple_trace": number(ctx, target),
                       "absolute_residual": number(ctx, abs(residual)), "analytic_tail_allowance": number(ctx, allowance),
                       "uncertified_floating_budget": number(ctx, checks.tolerance*target)})
    return checks.result(rows=rows, three_curve_blocks=blocks,
                         labels=["eq:universalkernel", "eq:figurekerneltail", "eq:figurefiniteidentity", "eq:fbound"],
                         formulas="x_next=x^2/9+2; F_N=sum((-1)^n*2^(-n-1)*h(x_n/3)); B_N=2^(-N-1)*h(x_N/3)",
                         rounding_policy="100 extra guard digits protect iterates through N=180; finite residual cancellation is still classified separately",
                         scope="single kernel and finite complete three-curve blocks; no whole-surface sum")


def h_twist(ctx, a, u):
    real_domain(ctx, a, u)
    if a <= 0:
        raise ValueError("twist kernel requires positive cuff length")
    e = ctx.exp(-abs(u))
    result = 2*ctx.sinh(a/2)*e/(1+2*ctx.cosh(a/2)*e+e*e)
    require(result > 0 and ctx.isfinite(result), "twist kernel lost positivity")
    return result


def partition_tail(ctx, a, tau, n):
    real_domain(ctx, a, tau)
    integer(n, 0, 10000)
    if a <= 0 or abs(tau) > a/2:
        raise ValueError("positive a and reduced |tau|<=a/2 required")
    length = (ctx.mpf(n)+ctx.mpf(1)/2)*a
    # z>=0 includes boundary equality at n=0.
    q1, q2 = ctx.exp(-(length+tau)), ctx.exp(-(length-tau))
    tail = q1/(1+q1)+q2/(1+q2)
    require(tail > 0 and ctx.isfinite(tail), "positive logistic tail was lost")
    return tail, length


def twist_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, terms, partitions = NumericChecks(ctx, digits, guards), [], []
    for a_text in fixture["cuffs"]:
        a = mpq(ctx, a_text)
        inputs = [str(sp.Rational(a_text)*sp.Rational(ratio)) for ratio in fixture["twist_ratios"]]+fixture["large_twists"]
        for u_text in inputs:
            u = mpq(ctx, u_text)
            stable = h_twist(ctx, a, u)
            hyperbolic = ctx.sinh(a/2)/(ctx.cosh(u)+ctx.cosh(a/2))
            checks.positive(f"a={a_text},u={u_text}: stable versus hyperbolic H", stable, hyperbolic)
            direct = (ctx.tanh((u+a/2)/2)-ctx.tanh((u-a/2)/2))/2
            resolved = stable > 100*ctx.eps/checks.tolerance
            if resolved:
                checks.positive(f"a={a_text},u={u_text}: resolved tanh difference", direct, stable)
            for b_text in fixture["boundaries"]:
                b = mpq(ctx, b_text)
                A2 = 1+torus_delta(ctx, a, b)
                r = torus_length(ctx, a, b, u)
                K = A2*ctx.sinh(a/2)/(ctx.cosh(r)+1+A2*(ctx.cosh(a/2)-1))
                checks.positive(f"a={a_text},u={u_text},b={b_text}: K(length)=H", K, stable)
            checks.observe(f"a={a_text},u={u_text}: H", stable, positive_signal=True)
            terms.append({"a": a_text, "u": u_text, "stable_H": number(ctx, stable), "tanh_difference": number(ctx, direct),
                          "tanh_route_status": "relative comparison passed" if resolved else "cancellation-limited; not a relative reference"})
    cases = [(a, str(sp.Rational(a)*sp.Rational(ratio)), n)
             for a, ratio, n in product(fixture["cuffs"], fixture["twist_ratios"], fixture["depths"])]
    large = fixture["large_partition"]
    cases.append((large["a"], large["tau"], large["N"]))
    for index, (a_text, tau_text, n) in enumerate(cases):
        reduced, winding = reduce_twist(a_text, tau_text)
        a, tau = mpq(ctx, a_text), mpq(ctx, reduced)
        tail, length = partition_tail(ctx, a, tau, n)
        partial = ctx.fsum(h_twist(ctx, a, tau+k*a) for k in range(-n, n+1))
        endpoint = (ctx.tanh((tau+length)/2)-ctx.tanh((tau-length)/2))/2
        checks.positive(f"partition {index}: finite endpoint formula", partial, endpoint)
        e = ctx.exp(-length)
        independent_tail = 2*e*(ctx.cosh(tau)+e)/(1+2*ctx.cosh(tau)*e+e*e)
        checks.positive(f"partition {index}: stable logistic versus rational tail", tail, independent_tail)
        bound = 2*ctx.cosh(tau)*e
        checks.bounded(f"partition {index}: analytic tail inequality violation", max(ctx.mpf(0), tail-bound), bound)
        checks.close(f"partition {index}: finite sum plus tail", partial+tail, 1, scale=ctx.mpf(1))
        direct_tail = 1-partial
        resolved = tail > 100*ctx.eps/checks.tolerance
        if resolved:
            checks.positive(f"partition {index}: resolved complement", direct_tail, tail)
        checks.observe(f"partition {index}: positive tail", tail, positive_signal=True)
        partitions.append({"a": a_text, "original_tau": tau_text, "reduced_tau_exact": str(reduced),
                           "integer_relabeling": winding, "N": n, "L_N": number(ctx, length),
                           "finite_partial_sum": number(ctx, partial), "positive_logistic_tail": number(ctx, tail),
                           "analytic_tail_bound": number(ctx, bound), "direct_1_minus_partial": number(ctx, direct_tail),
                           "complement_route_status": "relative comparison passed" if resolved else "cancellation-limited; retained logistic tail is the reference"})
    return checks.result(terms=terms, partitions=partitions, labels=["eq:Hkernel", "eq:Kkernel", "eq:Hpartialsumtail"],
                         coordinates="signed displacement twist reduced modulo a with integer relabeling; finite N only",
                         tail_status="positive logistic tail and analytic bound evaluated without outward rounding")


def shadow(ctx, d):
    real_domain(ctx, d)
    if d <= 0:
        raise ValueError("orthogeodesic distance must be strictly positive")
    q = ctx.exp(-d)
    value = 2*ctx.log1p(2*q/(1-q))
    require(value > 0 and ctx.isfinite(value), "boundary shadow lost positivity")
    return value


def shadow_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows = NumericChecks(ctx, digits, guards), []
    for d_text in fixture["distances"]:
        d = mpq(ctx, d_text)
        stable = shadow(ctx, d)
        q = ctx.exp(-d)
        z = 2*q/(1+q*q)
        independent = ctx.log1p(z)-ctx.log1p(-z)
        checks.positive(f"d={d_text}: two stable shadows", stable, independent)
        checks.positive(f"d={d_text}: scaled shadows", stable/(4*q), independent/(4*q))
        center, radius = ctx.coth(d), ctx.csch(d)
        low, high = center-radius, center+radius
        direct = ctx.log(high/low)
        resolved = stable > 100*ctx.eps/checks.tolerance
        if resolved:
            checks.positive(f"d={d_text}: independent circle endpoints", direct, stable)
            checks.positive(f"d={d_text}: lower endpoint", low, ctx.tanh(d/2))
            checks.positive(f"d={d_text}: upper endpoint", high, ctx.coth(d/2))
            checks.positive(f"d={d_text}: unoriented factor", 2*direct, 4*ctx.log(ctx.coth(d/2)))
        checks.observe(f"d={d_text}: positive shadow", stable, positive_signal=True)
        rows.append({"d": d_text, "positive_shadow": number(ctx, stable), "shadow_over_4_exp_minus_d": number(ctx, stable/(4*q)),
                     "unoriented_arc_two_shadows": number(ctx, 2*stable), "circle_endpoint_shadow": number(ctx, direct),
                     "direct_route_status": "relative comparison passed" if resolved else "cancellation-limited; zero or inaccurate positive shadow rejected as a relative reference"})
    return checks.result(rows=rows, labels=["eq:basmajian"],
                         formulas="one shadow=2log(coth(d/2)); unoriented arc contributes two shadows",
                         scope="finite boundary shadows only; no orthospectrum approximation or interval enclosure")
