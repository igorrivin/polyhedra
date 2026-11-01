"""Independent Gaussian/endpoint formulas in cloned mpmath contexts.

The context, quad, nstr and isfinite usage follows experiments/quantum_surgery/
periods.py. Analytic tail formulas below address exact integrals/series only;
their floating evaluations do not enclose quadrature or roundoff errors.
"""

from fractions import Fraction as Q
from math import gcd

import mpmath

from .exact import divisors, integer, positive, rational, require


def context(digits):
    integer(digits, 40, 120)
    ctx = mpmath.mp.clone()
    ctx.dps = digits
    return ctx


def mpq(ctx, value):
    value = rational(value)
    return ctx.mpf(value.numerator)/value.denominator


def number(ctx, value):
    require(ctx.isfinite(value), "nonfinite numerical output refused")
    return ctx.nstr(value, ctx.dps, strip_zeros=False)


class NumericChecks:
    def __init__(self, ctx):
        self.ctx = ctx
        self.tolerance = ctx.power(10, -(ctx.dps-15))
        self.residuals = []
        self.observations = {}

    def close(self, name, actual, expected, *, analytic_tail_allowance=0):
        ctx = self.ctx
        require(all(ctx.isfinite(value) for value in (actual, expected, analytic_tail_allowance)),
                f"{name}: nonfinite input")
        require(analytic_tail_allowance >= 0, f"{name}: negative tail allowance")
        residual = abs(actual-expected)
        scale = max(1, abs(actual), abs(expected))
        require(residual <= self.tolerance*scale+analytic_tail_allowance, f"{name}: residual {residual}")
        self.residuals.append({"check": name, "absolute_residual": number(ctx, residual),
                               "scaled_residual": number(ctx, residual/scale),
                               "analytic_tail_allowance": number(ctx, analytic_tail_allowance)})

    def observe(self, name, value):
        self.observations[name] = number(self.ctx, value)

    def result(self, **values):
        return {"status": "uncertified floating formula comparisons passed",
                "decimal_precision": self.ctx.dps, "check_count": len(self.residuals),
                "scaled_tolerance": number(self.ctx, self.tolerance),
                "maximum_absolute_residual": number(self.ctx, max(
                    [self.ctx.mpf(row["absolute_residual"]) for row in self.residuals]+[0])),
                "residuals": self.residuals, "observations": self.observations, **values}


class PositiveNumericChecks(NumericChecks):
    """Relative checks for signals known analytically to be strictly positive.

    A tiny positive signal must not be accepted merely because it is below an
    absolute tolerance. The analytic truncation allowance must itself fit the
    relative tolerance budget; it cannot hide a bad quadrature or normalization.
    """

    def close(self, name, actual, expected, *, analytic_tail_allowance=0):
        ctx = self.ctx
        require(all(ctx.isfinite(value) for value in (actual, expected, analytic_tail_allowance)),
                f"{name}: nonfinite input")
        require(actual > 0 and expected > 0, f"{name}: strictly positive values required")
        require(analytic_tail_allowance >= 0, f"{name}: negative tail allowance")
        residual = abs(actual-expected)
        relative = residual/expected
        relative_tail = analytic_tail_allowance/expected
        require(relative_tail <= self.tolerance, f"{name}: analytic tail exceeds relative budget")
        require(relative <= self.tolerance+relative_tail, f"{name}: relative residual {relative}")
        self.residuals.append({"check": name, "absolute_residual": number(ctx, residual),
                               "scaled_residual": number(ctx, relative),
                               "relative_residual": number(ctx, relative),
                               "positive_reference": number(ctx, expected),
                               "analytic_tail_allowance": number(ctx, analytic_tail_allowance),
                               "relative_analytic_tail_allowance": number(ctx, relative_tail)})

    def observe(self, name, value):
        require(self.ctx.isfinite(value) and value > 0, f"{name}: strictly positive observation required")
        super().observe(name, value)

    def result(self, **values):
        return super().result(
            observation_policy="strictly_positive_relative",
            comparison_scaling="abs(actual-expected)/expected, with actual>0 and expected>0",
            maximum_relative_residual=number(self.ctx, max(
                [self.ctx.mpf(row["relative_residual"]) for row in self.residuals]+[0])),
            **values)


def gaussian_moment(ctx, coefficient, moment, cutoff):
    """Integrate x^moment exp(-pi*coefficient*x^2) over [-B,B].

    B=U/sqrt(pi*coefficient). For moment 0, omitted tail <= exp(-U^2)/
    (U sqrt(pi*coefficient)). For moment 2, integration by parts gives
    exp(-U^2)(U+1/(2U))/(pi*coefficient)^(3/2). U is a positive integer.
    """
    require(ctx.isfinite(coefficient) and coefficient > 0, "Gaussian coefficient must be positive and finite")
    if moment not in (0, 2):
        raise ValueError("only Gaussian moments zero and two are implemented")
    integer(cutoff, 2, 50)
    scale = ctx.sqrt(ctx.pi*coefficient)
    boundary = cutoff/scale
    integral = 2*ctx.quad(lambda x: x**moment*ctx.exp(-ctx.pi*coefficient*x*x),
                          [0, boundary/2, boundary], method="tanh-sinh")
    tail = (ctx.exp(-cutoff**2)/(cutoff*scale) if moment == 0 else
            ctx.exp(-cutoff**2)*(cutoff+ctx.mpf(1)/(2*cutoff))/scale**3)
    return integral, tail


def gaussian_checks(ctx, pairs, times):
    checks = NumericChecks(ctx)
    rows, cutoff, cache = [], ctx.dps//3, {}

    def moment(coefficient, order):
        key = (number(ctx, coefficient), order)
        if key not in cache:
            cache[key] = gaussian_moment(ctx, coefficient, order, cutoff)
        return cache[key]

    for index, (a_raw, b_raw) in enumerate(pairs):
        a, b = mpq(ctx, positive(a_raw)), mpq(ctx, positive(b_raw))
        ix, tx = moment(2*a, 0)
        iy, ty = moment(2*b, 0)
        ix2, tx2 = moment(2*a, 2)
        iy2, ty2 = moment(2*b, 2)
        norm = ix*iy
        derivative = 4*ctx.pi**2*(a-b)**2*ix2*iy2
        expected_norm = 1/(2*ctx.sqrt(a*b))
        expected_derivative = (a-b)**2/(8*(a*b)**ctx.mpf("1.5"))
        expected_s1 = (a+b)**2/(8*(a*b)**ctx.mpf("1.5"))
        checks.close(f"pair {index} L2 norm", norm, expected_norm)
        checks.close(f"pair {index} rotation norm", derivative, expected_derivative)
        checks.close(f"pair {index} S1 norm", norm+derivative, expected_s1)
        checks.observe(f"pair-{index}-L2-squared", norm)
        checks.observe(f"pair-{index}-rotation-squared", derivative)
        # The product-tail bounds use exact full Gaussian moments, evaluated here.
        norm_tail = tx/ctx.sqrt(2*b)+ty/ctx.sqrt(2*a)
        derivative_tail = 4*ctx.pi**2*(a-b)**2*(
            tx2/(2*ctx.pi*(2*b)**ctx.mpf("1.5"))+ty2/(2*ctx.pi*(2*a)**ctx.mpf("1.5")))
        correlations = []
        for t_raw in times:
            t = mpq(ctx, t_raw)
            xcoef, ycoef = a*(1+ctx.exp(2*t)), b*(1+ctx.exp(-2*t))
            xvalue, xtail = moment(xcoef, 0)
            yvalue, ytail = moment(ycoef, 0)
            actual = xvalue*yvalue
            expected = 1/(2*ctx.sqrt(a*b)*ctx.cosh(t))
            checks.close(f"pair {index}, t={t_raw} flow covariance", actual, expected)
            checks.observe(f"pair-{index}-covariance-t-{t_raw}", actual)
            correlations.append({"t": t_raw, "quadrature": number(ctx, actual),
                                 "closed_formula": number(ctx, expected),
                                 "analytic_omitted_integral_majorant": number(
                                     ctx, xtail/ctx.sqrt(ycoef)+ytail/ctx.sqrt(xcoef))})
        rows.append({"a": a_raw, "b": b_raw, "L2_squared": number(ctx, norm),
                     "rotation_derivative_squared": number(ctx, derivative),
                     "S1_squared": number(ctx, norm+derivative),
                     "norm_analytic_tail_majorant": number(ctx, norm_tail),
                     "derivative_analytic_tail_majorant": number(ctx, derivative_tail),
                     "correlations": correlations})
    return checks.result(rows=rows, scaled_Gaussian_cutoff_U=cutoff,
                         flow_convention="a_t=diag(exp(t),exp(-t))",
                         backend="mpmath tanh-sinh quadrature versus closed Gaussian formulas",
                         tail_status="Analytic omitted-integral majorants evaluated in floating arithmetic; no interval enclosure or quadrature error bound.")


def series_tail_bounds(q, n):
    """Exact rational evaluation of the two stated analytic majorant formulas."""
    q = rational(q)
    integer(n, 1)
    if not 0 < q < 1:
        raise ValueError("tail formula requires 0<q<1")
    return (q**(n+1)*((n+1)-n*q)/(1-q)**2,
            q**(n+1)/((1-q)*(1-q**(n+1))))


def orbit_integral(ctx, alpha, k, cutoff, *, scaled=False):
    """Independent radial integral after performing the real s-Gaussian integral.

    Haar coordinates give 2*pi*sqrt(pi/alpha)/(k*zeta(2)) times
    integral_0^infinity exp[-alpha(r^2+k^2/r^2)] dr. Before quadrature, factor
    out exp(-2*alpha*k), leaving exp[-alpha*(r-k/r)^2] with peak value one.
    This avoids applying absolute quadrature accuracy to an exponentially tiny
    amplitude. With scaled=True, return the scaled integral and its analytic
    omitted-tail majorant; otherwise restore the amplitude to both quantities.
    The scaled tail above B is bounded by
    exp(2*alpha*k-alpha*B^2)/(2*alpha*B), before the Haar prefactor.
    """
    integer(k, 1, 10)
    integer(cutoff, 2, 50)
    require(ctx.isfinite(alpha) and alpha > 0, "orbit alpha must be finite and positive")
    boundary = cutoff/ctx.sqrt(alpha)
    peak = ctx.sqrt(k)
    require(boundary > peak, "orbit cutoff must exceed radial peak")

    def integrand(r):
        return ctx.mpf(0) if r == 0 else ctx.exp(-alpha*(r-k/r)**2)

    prefactor = 2*ctx.pi*ctx.sqrt(ctx.pi/alpha)/(k*ctx.zeta(2))
    integral = prefactor*ctx.quad(integrand, [0, peak, boundary], method="tanh-sinh")
    tail = prefactor*ctx.exp(2*alpha*k-alpha*boundary**2)/(2*alpha*boundary)
    amplitude = 1 if scaled else ctx.exp(-2*alpha*k)
    return amplitude*integral, amplitude*tail


def rank_two_checks(ctx, times, terms, orbit_k):
    integer(terms, 20, 50)
    checks, rows = PositiveNumericChecks(ctx), []
    for t_raw in times:
        t = mpq(ctx, t_raw)
        c, zeta2 = ctx.cosh(t), ctx.zeta(2)
        alpha = 2*ctx.pi*c
        q = ctx.exp(-4*ctx.pi*c)
        prefactor = ctx.pi/(zeta2*c)
        series = prefactor*sum(mpq(ctx, Q(sum(divisors(k)), k))*q**k for k in range(1, terms+1))
        # log1p retains the small q^n signal instead of subtracting it from one.
        logarithms = -prefactor*sum(ctx.log1p(-q**n) for n in range(1, terms+1))
        # Different determinant orbit formula with both signs and sigma_1(k) multiplicities.
        orbit_sum = 2*sum(sum(divisors(k))*ctx.pi**2*ctx.exp(-2*alpha*k)/(alpha*k*zeta2)
                          for k in range(1, terms+1))
        series_tail = prefactor*q**(terms+1)*((terms+1)-terms*q)/(1-q)**2
        log_tail = prefactor*q**(terms+1)/((1-q)*(1-q**(terms+1)))
        checks.close(f"t={t_raw} determinant orbit sum", orbit_sum, series)
        checks.close(f"t={t_raw} logarithm series", logarithms, series,
                     analytic_tail_allowance=series_tail+log_tail)
        checks.observe(f"rank-two-covariance-t-{t_raw}", series)
        checks.observe(f"rank-two-log-series-t-{t_raw}", logarithms)
        checks.observe(f"rank-two-orbit-sum-t-{t_raw}", orbit_sum)
        orbits = []
        for k in orbit_k:
            cutoff = max(18, ctx.dps//3)
            scaled_actual, scaled_tail = orbit_integral(ctx, alpha, k, cutoff, scaled=True)
            amplitude = ctx.exp(-2*alpha*k)
            actual, tail = amplitude*scaled_actual, amplitude*scaled_tail
            expected = ctx.pi**2*ctx.exp(-2*alpha*k)/(alpha*k*zeta2)
            scaled_expected = ctx.pi**2/(alpha*k*zeta2)
            checks.close(f"t={t_raw}, k={k} scaled radial orbit integral", scaled_actual, scaled_expected,
                         analytic_tail_allowance=scaled_tail)
            checks.close(f"t={t_raw}, k={k} radial orbit integral", actual, expected,
                         analytic_tail_allowance=tail)
            checks.observe(f"orbit-k-{k}-t-{t_raw}", actual)
            checks.observe(f"scaled-orbit-k-{k}-t-{t_raw}", scaled_actual)
            orbits.append({"positive_determinant": k, "quadrature": number(ctx, actual),
                           "closed_integral": number(ctx, expected),
                           "analytic_omitted_radial_tail_majorant": number(ctx, tail),
                           "exponential_amplitude": number(ctx, amplitude),
                           "scaled_quadrature": number(ctx, scaled_actual),
                           "scaled_closed_integral": number(ctx, scaled_expected),
                           "scaled_analytic_omitted_radial_tail_majorant": number(ctx, scaled_tail),
                           "scaled_radial_cutoff_U": cutoff})
        rows.append({"t": t_raw, "q": number(ctx, q), "k_series": number(ctx, series),
                     "log_series": number(ctx, logarithms), "two_sign_orbit_sum": number(ctx, orbit_sum),
                     "analytic_k_tail_majorant": number(ctx, series_tail),
                     "analytic_log_tail_majorant": number(ctx, log_tail), "radial_orbits": orbits})
    return checks.result(rows=rows, series_terms=terms, quadrature_determinants=orbit_k,
                         squared_norm_convention="The t=0 value is the rank-two squared L2 norm; radial rotation derivative is zero.",
                         backend="mpmath divisor series, stable log1p series, closed determinant orbit sum, and exponentially scaled radial tanh-sinh quadrature",
                         tail_status="Analytic positive-series/integral truncation formulas only; evaluated values are not total-error certificates.")


def endpoint_checks(ctx, maximum, frequencies):
    checks = NumericChecks(ctx)
    for c in range(2, maximum+1):
        pairs = [(a, pow(a, -1, c)) for a in range(c) if gcd(a, c) == 1]
        for m, n in frequencies:
            direct = sum(ctx.exp(2*ctx.pi*ctx.j*m*a/c)*ctx.exp(2*ctx.pi*ctx.j*n*d/c)
                         for a, d in pairs)/len(pairs)
            residues = sum(ctx.exp(2*ctx.pi*ctx.j*((m*a+n*d) % c)/c)
                           for a, d in pairs)/len(pairs)
            checks.close(f"c={c}, (m,n)=({m},{n}) endpoint products", direct, residues)
            checks.observe(f"c-{c}-m-{m}-n-{n}-real", ctx.re(residues))
            checks.observe(f"c-{c}-m-{m}-n-{n}-imag", ctx.im(residues))
    return checks.result(c_range=[2, maximum], frequencies=frequencies,
                         backend="Two finite complex exponential forms using the same mpmath context")


def terminal_checks(ctx, rows):
    checks, outputs = NumericChecks(ctx), []
    for index, row in enumerate(rows):
        h, r, end = (mpq(ctx, positive(row[key])) for key in ("h", "r", "T"))
        c, mean = mpq(ctx, row["c"]), mpq(ctx, row["M"])
        require(end >= 1, "terminal integration endpoint must be >=1")
        rate = h-r
        integral = ctx.quad(lambda u: ctx.exp(h*u)*rate*c*ctx.exp(-r*u), [1, end], method="tanh-sinh")
        terminal = (ctx.exp(h*end)*((mean+c*ctx.exp(-r*end))-mean)
                    -ctx.exp(h)*((mean+c*ctx.exp(-r))-mean))
        checks.close(f"terminal identity {index}", integral, terminal)
        if h == r:
            checks.close(f"removable rate-zero identity {index}", integral, 0)
        checks.observe(f"terminal-integral-{index}", integral)
        outputs.append({**row, "rate_zero": h == r, "integral": number(ctx, integral),
                        "terminal_difference": number(ctx, terminal)})
    return checks.result(rows=outputs, backend="Explicit derivative integrand quadrature versus terminal expression",
                         scope="A specified exponential family only; no arbitrary remainder estimate.")


def precision_comparison(low, high):
    require(low["observations"].keys() == high["observations"].keys(), "precision runs cover different observations")
    ctx = context(high["decimal_precision"])
    tolerance = ctx.power(10, -(low["decimal_precision"]-15))
    policy = low.get("observation_policy", "absolute_floor_one")
    require(policy == high.get("observation_policy", "absolute_floor_one"), "precision observation policies disagree")
    require(policy in ("absolute_floor_one", "strictly_positive_relative"), "unknown precision observation policy")
    differences = []
    for key in low["observations"]:
        a, b = ctx.mpf(low["observations"][key]), ctx.mpf(high["observations"][key])
        require(ctx.isfinite(a) and ctx.isfinite(b), "nonfinite precision comparison")
        residual = abs(a-b)
        if policy == "strictly_positive_relative":
            require(a > 0 and b > 0, f"strictly positive precision observations required: {key}")
            scaled = residual/b
        else:
            scaled = residual/max(1, abs(a), abs(b))
        require(scaled <= tolerance, f"precision mismatch: {key}")
        differences.append((key, residual, scaled))
    worst = max(differences, key=lambda row: row[2])
    result = {"status": "uncertified cross-precision agreement", "comparison_count": len(differences),
              "decimal_precisions": [low["decimal_precision"], high["decimal_precision"]],
              "maximum_absolute_difference": number(ctx, max(row[1] for row in differences)),
              "maximum_scaled_difference": number(ctx, worst[2]), "worst_scaled_observation": worst[0],
              "scaled_tolerance": number(ctx, tolerance)}
    if policy == "strictly_positive_relative":
        result.update({"observation_policy": policy, "comparison_scaling": "abs(low-high)/high with low>0 and high>0",
                       "maximum_relative_difference": number(ctx, worst[2])})
    return result
