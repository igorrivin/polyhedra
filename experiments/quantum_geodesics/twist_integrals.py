"""G6: finite direct/coarea quadratures with analytic tails kept separate."""

from itertools import product

from .common import NumericChecks, context, integer, mpq, number, require
from .geometry import acosh_real, matrix_length, real_domain, torus_delta, torus_length


def twist_integrals(ctx, a, b, s, cutoff):
    real_domain(ctx, a, b, s, cutoff)
    if s <= 0 or cutoff <= 0:
        raise ValueError("twist integrals require s>0 and cutoff>0")
    delta = torus_delta(ctx, a, b)
    A = ctx.sqrt(1+delta)
    # Evaluate the length-side expression independently of the direct length formula.
    direct, direct_error = ctx.quad(lambda u: 2*ctx.cosh(torus_length(ctx, a, b, u)/2)**(-s),
                                    [0, cutoff/2, cutoff], error=True)
    # y=A*v factors out the amplitude. Geometric splits resolve the long finite y interval.
    endpoint = ctx.sinh(cutoff/2)
    subdivisions = [ctx.mpf(0)]
    step = 2
    while ctx.mpf(step) < cutoff/2:
        subdivisions.append(ctx.sinh(step))
        step += 2
    subdivisions.append(endpoint)
    coarea_scaled, coarea_error_scaled = ctx.quad(
        lambda v: 4*(1+v*v)**(-(s+1)/2), subdivisions, error=True)
    amplitude = A**(-s)
    coarea, coarea_error = amplitude*coarea_scaled, amplitude*coarea_error_scaled
    total = 2*ctx.sqrt(ctx.pi)*ctx.gamma(s/2)/(A**s*ctx.gamma((s+1)/2))
    tail = ctx.power(2, s+2)*amplitude*ctx.exp(-s*cutoff/2)/s
    require(all(ctx.isfinite(v) and v > 0 for v in (direct, coarea, total, tail)),
            "positive integral or analytic tail signal was lost")
    return {"A": A, "direct": direct, "coarea": coarea, "total": total, "analytic_tail": tail,
            "direct_error_estimate": direct_error, "coarea_error_estimate": coarea_error,
            "y_upper": A*endpoint, "coarea_scaled_subdivisions": subdivisions}


def sublevel_width(ctx, a, b, R):
    real_domain(ctx, R)
    r0 = torus_length(ctx, a, b, ctx.mpf(0))
    if R <= r0:
        return ctx.mpf(0)
    A = ctx.sqrt(1+torus_delta(ctx, a, b))
    return 4*acosh_real(ctx, ctx.cosh(R/2)/A)


def integral_checks(fixture, digits, guards):
    ctx = context(digits, guards)
    checks, rows, sublevels = NumericChecks(ctx, digits, guards), [], []
    for index, (pair, s_text, cutoff) in enumerate(product(fixture["pairs"], fixture["powers"], fixture["cutoffs"])):
        integer(cutoff, 1, 100)
        a, b, s = [mpq(ctx, value) for value in (*pair, s_text)]
        values = twist_integrals(ctx, a, b, s, ctx.mpf(cutoff))
        prefix = f"pair={pair},s={s_text},U={cutoff}"
        checks.positive(prefix+": direct versus coarea", values["direct"], values["coarea"])
        checks.bounded(prefix+": direct quadrature heuristic error", values["direct_error_estimate"], values["direct"])
        checks.bounded(prefix+": coarea quadrature heuristic error", values["coarea_error_estimate"], values["coarea"])
        gap = values["total"]-values["direct"]
        checks.bounded(prefix+": total formula with analytic tail", gap, values["total"], values["analytic_tail"])
        checks.bounded(prefix+": finite integral exceeds total violation", min(ctx.mpf(0), gap), values["total"])
        row = {"a_b": pair, "s": s_text, "U": cutoff,
               **{key: number(ctx, value) for key, value in values.items() if key != "coarea_scaled_subdivisions"},
               "coarea_scaled_subdivisions": [number(ctx, value) for value in values["coarea_scaled_subdivisions"]],
               "total_minus_direct": number(ctx, gap),
               "uncertified_floating_budget": number(ctx, checks.tolerance*values["total"]),
               "tail_resolution": "below declared floating budget" if values["analytic_tail"] < checks.tolerance*values["total"] else "above declared floating budget"}
        if s == 2:
            exact_finite = 4*ctx.tanh(ctx.mpf(cutoff)/2)/values["A"]**2
            exact_tail_stable = 8/(values["A"]**2*(1+ctx.exp(cutoff)))
            checks.positive(prefix+": exact finite s2 integral", values["direct"], exact_finite)
            checks.positive(prefix+": exact stable s2 tail", 4*(1-ctx.tanh(ctx.mpf(cutoff)/2))/values["A"]**2,
                            exact_tail_stable)
            checks.close(prefix+": s2 finite plus tail", exact_finite+exact_tail_stable, 4/values["A"]**2, scale=4/values["A"]**2)
            row["exact_s2_finite"] = number(ctx, exact_finite)
            row["exact_s2_tail_stable"] = number(ctx, exact_tail_stable)
        checks.observe(f"integral {index}: direct", values["direct"], positive_signal=True)
        checks.observe(f"integral {index}: coarea", values["coarea"], positive_signal=True)
        rows.append(row)
    for pair in fixture["pairs"]:
        a, b = [mpq(ctx, value) for value in pair]
        r0 = torus_length(ctx, a, b, ctx.mpf(0))
        levels = [("below", r0/2), ("equal", r0)]
        levels += [("offset="+offset, r0+mpq(ctx, offset)) for offset in fixture["sublevel_offsets"]]
        for label, R in levels:
            width = sublevel_width(ctx, a, b, R)
            prefix = f"pair={pair},sublevel={label}"
            if label in ("below", "equal"):
                checks.close(prefix+": zero measure", width, 0, scale=ctx.mpf(1))
                if label == "equal":
                    checks.positive(prefix+": minimum matrix length", matrix_length(ctx, a, b, 0), R)
            else:
                require(width > 0, "positive sublevel width lost")
                for sign in (-1, 1):
                    checks.positive(prefix+f": endpoint sign={sign}", matrix_length(ctx, a, b, sign*width/2), R)
            sublevels.append({"a_b": pair, "case": label, "r0": number(ctx, r0), "R": number(ctx, R),
                              "width": number(ctx, width), "endpoint_twists": [number(ctx, -width/2), number(ctx, width/2)]})
    return checks.result(rows=rows, sublevels=sublevels,
                         labels=["eq:toruscoarea", "eq:betaintegral", "eq:torusintegraltail", "eq:sublevel"],
                         coordinates="direct u in [-U,U]; coarea y=sqrt(cosh(r/2)^2-A^2), then v=y/A",
                         quadrature="tanh-sinh with distinct direct and geometric coarea subdivisions; per-method heuristic estimates and two-precision convergence observations",
                         error_status="no certified quadrature or total-error bound; analytic tails bound the exact omitted integrals only")
