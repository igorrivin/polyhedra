"""Strict exact inputs and scale-aware, uncertified numerical comparisons."""

from fractions import Fraction

import mpmath
import sympy as sp


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def integer(value, minimum=0, maximum=10000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"integer in [{minimum},{maximum}] required")
    return value


def rational(value):
    """Parse exact fixture text without accepting binary floats or expressions."""
    if type(value) is not str:
        raise ValueError("rational inputs must be strings")
    try:
        parsed = Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("finite rational input required") from error
    return sp.Rational(parsed.numerator, parsed.denominator)


def positive(value):
    parsed = rational(value)
    if parsed <= 0:
        raise ValueError("strictly positive rational input required")
    return parsed


def context(digits, guard_digits=0):
    integer(digits, 40, 150)
    integer(guard_digits, 0, 100)
    ctx = mpmath.mp.clone()
    ctx.dps = digits + guard_digits
    return ctx


def mpq(ctx, value):
    value = rational(value) if isinstance(value, str) else value
    if not isinstance(value, (sp.Rational, Fraction)):
        raise ValueError("exact rational value required")
    return ctx.mpf(int(value.numerator))/int(value.denominator)


def number(ctx, value):
    require(ctx.isfinite(value), "nonfinite numerical output refused")
    return ctx.nstr(value, ctx.dps, strip_zeros=False)


def json_exact(value):
    if isinstance(value, dict):
        return {key: json_exact(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_exact(item) for item in value]
    if isinstance(value, sp.Basic):
        require(not value.has(sp.nan, sp.oo, -sp.oo, sp.zoo), "nonfinite exact output")
        return str(value)
    if isinstance(value, Fraction):
        return str(value)
    return value


class ExactChecks:
    def __init__(self):
        self.records = []

    def equal(self, name, actual, expected):
        residual = sp.simplify(actual - expected)
        require(residual == 0, f"{name}: exact identity failed: {residual}")
        self.records.append({"check": name, "actual": actual, "expected": expected,
                             "exact_residual": residual})

    def truth(self, name, condition):
        require(bool(condition), f"{name}: exact inequality or condition failed")
        self.records.append({"check": name, "exact_condition": True})

    def result(self, **values):
        return {"status": "finite exact algebra checks passed", "check_count": len(self.records),
                "records": self.records, **values}


class NumericChecks:
    """Every comparison supplies a meaningful scale; positive signals stay positive.

    Analytic truncation bounds are reported separately. They may enter an
    absolute residual identity only with an explicitly chosen scale; they are
    never silently added to a positive relative comparison budget.
    """

    def __init__(self, ctx, requested_digits, guard_digits=0):
        integer(requested_digits, 40, 150)
        integer(guard_digits, 0, 100)
        if ctx.dps != requested_digits + guard_digits:
            raise ValueError("actual precision disagrees with requested and guard digits")
        self.ctx = ctx
        self.requested_digits = requested_digits
        self.guard_digits = guard_digits
        self.tolerance = ctx.power(10, -(requested_digits-15))
        self.records = []
        self.observations = {}

    def close(self, name, actual, expected, *, scale, positive_signal=False):
        ctx = self.ctx
        require(all(ctx.isfinite(x) for x in (actual, expected, scale)), f"{name}: nonfinite input")
        require(ctx.im(scale) == 0 and scale > 0, f"{name}: finite positive scale required")
        if positive_signal:
            require(ctx.im(actual) == 0 and ctx.im(expected) == 0 and actual > 0 and expected > 0,
                    f"{name}: strictly positive real signals required")
            require(scale == expected, f"{name}: positive signal scale must be its reference")
        residual = abs(actual-expected)
        relative = residual/scale
        require(ctx.isfinite(relative) and relative <= self.tolerance,
                f"{name}: scaled residual {relative} exceeds {self.tolerance}")
        self.records.append({"check": name, "absolute_residual": number(ctx, residual),
                             "scale": number(ctx, scale), "scaled_residual": number(ctx, relative),
                             "positive_signal": positive_signal})

    def positive(self, name, actual, expected):
        self.close(name, actual, expected, scale=expected, positive_signal=True)

    def bounded(self, name, signed_residual, scale, analytic_bound=0):
        """Check |residual| <= analytic bound + explicit floating budget."""
        ctx = self.ctx
        require(all(ctx.isfinite(x) for x in (signed_residual, scale, analytic_bound)),
                f"{name}: nonfinite bound input")
        require(scale > 0 and analytic_bound >= 0, f"{name}: invalid bound or scale")
        numerical_budget = self.tolerance*scale
        require(abs(signed_residual) <= analytic_bound+numerical_budget,
                f"{name}: residual exceeds separate analytic and numerical budgets")
        self.records.append({"check": name, "absolute_residual": number(ctx, abs(signed_residual)),
                             "scale": number(ctx, scale),
                             "scaled_residual": number(ctx, abs(signed_residual)/scale),
                             "analytic_bound": number(ctx, analytic_bound),
                             "uncertified_floating_budget": number(ctx, numerical_budget),
                             "positive_signal": False})

    def observe(self, name, value, *, positive_signal=False, scale=None):
        ctx = self.ctx
        require(ctx.isfinite(value) and ctx.im(value) == 0, f"{name}: finite real observation required")
        if positive_signal:
            require(value > 0, f"{name}: strictly positive observation required")
        if scale is None:
            require(positive_signal, "signed or zero observations require an explicit positive scale")
            scale = value
        require(ctx.isfinite(scale) and scale > 0, f"{name}: invalid observation scale")
        if name in self.observations:
            raise ValueError("duplicate observation name")
        self.observations[name] = {"value": number(ctx, value), "scale": number(ctx, scale),
                                   "positive_signal": positive_signal}

    def result(self, **values):
        return {"status": "uncertified finite floating comparisons passed",
                "requested_decimal_digits": self.requested_digits,
                "guard_digits": self.guard_digits, "actual_decimal_digits": self.ctx.dps,
                "scaled_tolerance": number(self.ctx, self.tolerance),
                "check_count": len(self.records), "records": self.records,
                "observations": self.observations, **values}


def precision_comparison(low, high):
    """An observation, never an independent formula oracle or an interval bound."""
    lo, hi = low["requested_decimal_digits"], high["requested_decimal_digits"]
    if lo >= hi or set(low["observations"]) != set(high["observations"]):
        raise ValueError("matching observations at two increasing precisions required")
    ctx = context(hi, high["guard_digits"])
    checks = NumericChecks(ctx, hi, high["guard_digits"])
    checks.tolerance = ctx.power(10, -(lo-15))
    for name, row in low["observations"].items():
        other = high["observations"][name]
        if row["positive_signal"] != other["positive_signal"]:
            raise ValueError("precision observation policy changed")
        actual, expected = ctx.mpf(row["value"]), ctx.mpf(other["value"])
        if row["positive_signal"]:
            checks.positive(name, actual, expected)
        else:
            checks.close(name, actual, expected, scale=ctx.mpf(other["scale"]))
    return {"status": "cross-precision observations only", "lower_requested_digits": lo,
            "higher_requested_digits": hi, "comparison_count": len(checks.records),
            "scaled_tolerance": number(ctx, checks.tolerance), "records": checks.records}
