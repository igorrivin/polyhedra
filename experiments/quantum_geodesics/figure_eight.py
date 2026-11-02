"""Q1: finite figure-eight products with an independent branch-safe oracle."""

import sympy as sp

from .common import ExactChecks, NumericChecks, context, integer, number, require


def positive_sum(ctx, n):
    integer(n, 2, 500)
    logs = [ctx.mpf(0)]
    for k in range(1, n):
        factor = 4*ctx.sin(ctx.pi*k/n)**2
        require(ctx.isfinite(factor) and factor > 0, "positive product factor lost")
        logs.append(logs[-1]+ctx.log(factor))
    maximum = max(logs)
    log_sum = maximum+ctx.log(ctx.fsum(ctx.exp(value-maximum) for value in logs))
    return log_sum, logs


def habiro_le_sum(ctx, n):
    integer(n, 2, 500)
    product, terms = ctx.mpc(1), [ctx.mpc(1)]
    for k in range(1, n):
        # Do not take principal fractional powers of the already rounded q.
        lower = ctx.exp(ctx.pi*ctx.j*(n-k)/n)
        upper = ctx.exp(ctx.pi*ctx.j*(n+k)/n)
        product *= (lower-1/lower)*(upper-1/upper)
        terms.append(product)
    return ctx.fsum(terms)


def exact_checks(ns):
    checks, rows = ExactChecks(), []
    z = sp.Symbol("z")
    for n in ns:
        integer(n, 2, 500)
        quotient = sp.Poly.from_list([1]*n, z)
        checks.equal(f"N={n}: cyclotomic quotient identity",
                     (z-1)*quotient.as_expr(), z**n-1)
        checks.equal(f"N={n}: quotient at one", quotient.eval(1), sp.Integer(n))
        rows.append({"N": n, "quotient_coefficients_descending": quotient.all_coeffs(),
                     "quotient_at_one": quotient.eval(1)})
    return checks.result(formula="(z-1)*sum(z^j,j=0..N-1)=z^N-1", rows=rows)


def numerical_checks(ns, digits, guard_digits):
    ctx = context(digits, guard_digits)
    checks, rows = NumericChecks(ctx, digits, guard_digits), []
    for n in ns:
        log_j, logs = positive_sum(ctx, n)
        j_value = ctx.exp(log_j)
        oracle = habiro_le_sum(ctx, n)
        checks.positive(f"N={n}: Habiro-Le real part", ctx.re(oracle), j_value)
        checks.close(f"N={n}: Habiro-Le imaginary part", ctx.im(oracle), 0, scale=j_value)
        checks.positive(f"N={n}: final product N^2", ctx.exp(logs[-1]), ctx.mpf(n*n))
        index = 5*n//6
        candidates = [index-1, index] if n % 6 == 0 else [index]
        log_scale = max(ctx.mpf(1), abs(logs[index]))
        found = [j for j, value in enumerate(logs)
                 if abs(value-max(logs)) <= checks.tolerance*log_scale]
        require(found == candidates, f"N={n}: maximum locations {found} != {candidates}")
        for candidate in candidates:
            checks.close(f"N={n}: maximum at j={candidate}", logs[candidate], max(logs), scale=log_scale)
        checks.bounded(f"N={n}: Pmax<=J lower violation", min(ctx.mpf(0), log_j-max(logs)), log_scale)
        checks.bounded(f"N={n}: J<=N*Pmax upper violation",
                       max(ctx.mpf(0), log_j-max(logs)-ctx.log(n)), log_scale)
        checks.observe(f"N={n}: J", j_value, positive_signal=True)
        checks.observe(f"N={n}: Pmax", ctx.exp(max(logs)), positive_signal=True)
        rows.append({"N": n, "positive_log_sum": number(ctx, log_j), "positive_sum": number(ctx, j_value),
                     "oracle_real": number(ctx, ctx.re(oracle)), "oracle_imaginary": number(ctx, ctx.im(oracle)),
                     "imaginary_residual_over_positive_sum": number(ctx, abs(ctx.im(oracle))/j_value),
                     "maximum_indices": found, "log_maximum_product": number(ctx, max(logs)),
                     "log_lower_slack": number(ctx, log_j-max(logs)),
                     "log_upper_slack": number(ctx, ctx.log(n)+max(logs)-log_j),
                     "finite_growth_illustration_2pi_logJ_over_N": number(ctx, 2*ctx.pi*log_j/n)})
    return checks.result(rows=rows, coordinate="q=exp(2*pi*i/N); q half-powers defined before exponentiation",
                         formulas={"positive": "J_N=sum_j exp(sum_{k<=j} log(4*sin(pi*k/N)^2))",
                                   "oracle": "sum_j product_k (exp(pi*i*(N-k)/N)-exp(-pi*i*(N-k)/N))*(exp(pi*i*(N+k)/N)-exp(-pi*i*(N+k)/N))"},
                         analytic_tail="none: both sums are finite", oracle_status="independent finite expression, same mpmath backend")
