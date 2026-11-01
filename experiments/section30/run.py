"""Bounded replacement for the unreplayed Section 30 torus experiment.

The floating log-trace traversal is checked against exact Q(sqrt(11))
trace polynomials on an independently enumerated primitive-slope box.
Decimal lengths and event metrics are numerical, never interval certificates.
Only the two fixed manuscript fixtures and length cutoff 64 are supported.
"""

from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from functools import cache
from hashlib import sha256
import json
import math
from pathlib import Path
import platform
import subprocess
import time


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


@dataclass(frozen=True)
class Quadratic:
    """Exact a + b sqrt(11), with rational coefficients."""

    a: Fraction
    b: Fraction = Fraction(0)

    def __add__(self, other):
        return Quadratic(self.a + other.a, self.b + other.b)

    def __sub__(self, other):
        return Quadratic(self.a - other.a, self.b - other.b)

    def __mul__(self, other):
        return Quadratic(self.a * other.a + 11 * self.b * other.b,
                         self.a * other.b + self.b * other.a)

    def sign(self):
        """Compare an algebraic real with zero without numerical evaluation."""
        if self.b == 0:
            return (self.a > 0) - (self.a < 0)
        if self.a == 0 or (self.a > 0) == (self.b > 0):
            return 1 if self.b > 0 else -1
        delta = self.a * self.a - 11 * self.b * self.b
        return ((delta > 0) - (delta < 0)) * (1 if self.a > 0 else -1)

    def decimal(self):
        a = Decimal(self.a.numerator) / Decimal(self.a.denominator)
        b = Decimal(self.b.numerator) / Decimal(self.b.denominator)
        if self.a*self.b < 0:
            # Rationalize before numerical evaluation. The norm is exact,
            # while the conjugate denominator adds terms of the same sign.
            norm = self.a*self.a - 11*self.b*self.b
            numerator = Decimal(norm.numerator) / Decimal(norm.denominator)
            return numerator / (a-b*Decimal(11).sqrt())
        return a + b * Decimal(11).sqrt()

    def json(self):
        return {"rational": str(self.a), "sqrt11": str(self.b)}


ZERO = Quadratic(Fraction(0))
TWO = Quadratic(Fraction(2))


def canonical_slope(p, q):
    """Primitive unoriented slopes: q>0, or the single root (1,0)."""
    if math.gcd(p, q) != 1:
        raise ValueError("a slope must be primitive")
    if q < 0 or (q == 0 and p < 0):
        p, q = -p, -q
    return p, q


def fixture_roots(record):
    roots = tuple(Quadratic(Fraction(a), Fraction(b))
                  for a, b in record["traces_qsqrt11"])
    x, y, z = roots
    if x*x + y*y + z*z - x*y*z != ZERO:
        raise ValueError("the exact root Markoff equation failed")
    if any((a-TWO).sign() <= 0 for a in roots):
        raise ValueError("root traces must exceed two")
    if (y-x).sign() < 0 or (z-y).sign() < 0 or (x*y-z-z).sign() < 0:
        raise ValueError("the root must be reduced: 2<x<=y<=z<=xy/2")
    return roots


def length_from_log(log_trace):
    """2 acosh(trace/2), avoiding exponentiation of a large trace."""
    if not math.isfinite(log_trace) or log_trace <= math.log(2):
        raise ValueError("a finite hyperbolic log trace is required")
    return 2 * (log_trace + math.log(
        (1 + math.sqrt(1 - 4 * math.exp(-2 * log_trace))) / 2))


def log_spectrum(roots, cutoff):
    """Three disjoint outward sectors; retain curve, not trace, multiplicity."""
    with localcontext() as ctx:
        ctx.prec = 100
        x, y, z = (math.log(float(a.decimal())) for a in roots)
    root_rows = [((1, 0), x), ((0, 1), y), ((1, 1), z)]
    rows = {slope: length_from_log(value) for slope, value in root_rows
            if length_from_log(value) <= cutoff}
    # Raw signed endpoints are retained during recursion. The negative sector
    # uses (1,0),(0,-1); canonicalization happens only when recording a curve.
    stack = [((1, 0), (0, -1), x, y, z),
             ((1, 0), (1, 1), x, z, y),
             ((0, 1), (1, 1), y, z, x)]
    visited = pruned = 0
    max_ratio = 0.0
    while stack:
        p, q, a, b, opposite = stack.pop()
        visited += 1
        ratio = math.exp(opposite-a-b)
        if ratio > 0.5 + 8 * math.ulp(0.5):
            raise ArithmeticError("outward subtraction ratio exceeded one half")
        max_ratio = max(max_ratio, ratio)
        c = a+b+math.log1p(-ratio)
        if c <= max(a, b):
            raise ArithmeticError("outward trace failed strict monotonicity")
        length = length_from_log(c)
        if length > cutoff:
            pruned += 1
            continue
        raw = p[0]+q[0], p[1]+q[1]
        slope = canonical_slope(*raw)
        if slope in rows:
            raise ArithmeticError("duplicate curve from the sector traversal")
        rows[slope] = length
        stack.append((p, raw, a, c, b))
        stack.append((raw, q, c, b, a))
    return rows, {"visited_outward_nodes": visited, "pruned_nodes": pruned,
                  "maximum_subtraction_ratio": max_ratio}


def exact_trace_function(roots):
    """Evaluate a given slope using Euclidean Farey parents, without pruning.

    For p/q>0, p*q1=1 (mod q) gives the two Farey parents summing
    to (p,q). Their difference is the opposite curve in the trace identity.
    Negative slopes use the second diagonal xy-z. This is a different
    enumeration from the outward binary traversal.
    """
    x, y, z = roots

    @cache
    def positive(p, q, negative):
        if q == 0:
            return x
        if p == 0:
            return y
        if (p, q) == (1, 1):
            return x*y-z if negative else z
        if q == 1:
            p1, q1 = 1, 0
        else:
            q1 = pow(p, -1, q)
            p1 = (p*q1-1)//q
        p2, q2 = p-p1, q-q1
        r, s = canonical_slope(p1-p2, q1-q2)
        if r < 0:
            raise ArithmeticError("positive Farey parent difference left its sector")
        return (positive(p1, q1, negative)*positive(p2, q2, negative)
                - positive(r, s, negative))

    def evaluate(p, q):
        p, q = canonical_slope(p, q)
        return positive(abs(p), q, p < 0)

    return evaluate


def decimal_length(trace):
    """Numerical length of an exact algebraic trace at current precision."""
    x = trace.decimal()
    return 2 * ((x + (x*x-4).sqrt()) / 2).ln()


def box_spectrum(roots, cutoff, dps):
    """Independent finite-box enumeration, with an explicit analytic bound.

    Both fixtures have min root trace >=5/2. On each outward sector,
    v=log(trace/2) satisfies v_child>=v_left+v_right, and each root
    v>=log(5/4)>1/5. For sector weight F, length=2 acosh(exp(v))>2F/5.
    Since F>=max(abs(p),q), length<=64 implies max(abs(p),q)<160.
    Length comparisons below use Decimal arithmetic, not certified bounds.
    """
    if any((a-Quadratic(Fraction(5, 2))).sign() < 0 for a in roots):
        raise ValueError("the finite-box proof needs root traces at least 5/2")
    bound = math.ceil(5*cutoff/2)
    evaluate = exact_trace_function(roots)
    with localcontext() as ctx:
        ctx.prec = dps
        half = Decimal(cutoff)/2
        threshold = half.exp() + (-half).exp()
        rows = {}
        tested = 0
        nearest_trace_margin = None
        candidates = [(1, 0)]
        candidates.extend((p, q) for q in range(1, bound+1)
                          for p in range(-bound, bound+1) if math.gcd(p, q) == 1)
        for slope in candidates:
            trace = evaluate(*slope)
            tested += 1
            margin = abs(trace.decimal()-threshold)
            if nearest_trace_margin is None or margin < nearest_trace_margin:
                nearest_trace_margin = margin
            if trace.decimal() <= threshold:
                rows[slope] = (trace, decimal_length(trace))
    return rows, {"box_coordinate_bound": bound, "primitive_slopes_tested": tested,
                  "minimum_cutoff_trace_margin": str(nearest_trace_margin)}


def block_metrics(lengths, start):
    """Event sweep with N(L)=#{length<=L}; M includes both one-sided limits.

    Numerically equal events are grouped exactly as supplied; different
    rounded event locations are never merged by an arbitrary tolerance.
    """
    lengths = sorted(lengths)
    if start <= 0 or not math.isfinite(start):
        raise ValueError("a block needs a positive finite start")
    if any(length <= 0 or not math.isfinite(length) for length in lengths):
        raise ValueError("event lengths must be positive and finite")
    end = 2*start
    events = defaultdict(int)
    for length in lengths:
        events[length/2] += 1
        events[length] -= 4
    d = bisect_right(lengths, 2*start) - 4*bisect_right(lengths, start)
    maximum = abs(d)/start
    terms = []
    previous = start
    count = 0
    for position in sorted(x for x in events if start < x <= end):
        terms.append(d*d*(1/previous-1/position))
        maximum = max(maximum, abs(d)/position)  # left limit
        d += events[position]  # apply every simultaneous event together
        maximum = max(maximum, abs(d)/position)  # value and right limit
        previous = position
        count += 1
    terms.append(d*d*(1/previous-1/end))
    maximum = max(maximum, abs(d)/end)
    return {"T": start, "M": maximum, "Q": math.sqrt(math.fsum(terms)/start),
            "event_positions_in_block": count}


def direct_block_metrics(lengths, start):
    """Independent oracle: direct integer counts on each open event interval."""
    lengths = sorted(lengths)
    end = 2*start
    points = sorted({start, end} | {x for ell in lengths for x in (ell, ell/2)
                                  if start < x < end})
    maximum = 0.0
    terms = []
    for point in points:
        right = bisect_right(lengths, 2*point) - 4*bisect_right(lengths, point)
        maximum = max(maximum, abs(right)/point)
        if point > start:
            left = bisect_left(lengths, 2*point) - 4*bisect_left(lengths, point)
            maximum = max(maximum, abs(left)/point)
    for a, b in zip(points, points[1:]):
        middle = a+(b-a)/2
        if not a < middle < b:
            # No representable midpoint: counts immediately to the right of a.
            d = bisect_right(lengths, 2*a) - 4*bisect_right(lengths, a)
        else:
            d = bisect_right(lengths, 2*middle) - 4*bisect_right(lengths, middle)
        terms.append(d*d*(1/a-1/b))
    return {"T": start, "M": maximum, "Q": math.sqrt(math.fsum(terms)/start)}


def conditional_maximum_bounds(lengths, start, radius):
    """Exact rational M bounds assuming each supplied length has error <=radius.

    This concerns the supplied finite list with fixed curve membership.
    Applying it to a complete spectrum also requires that no omitted curve
    can enter a block threshold. Neither that hypothesis nor the length
    radius is certified here. Independent intervals allow unknown order.
    """
    start, radius = Fraction(start), Fraction(radius)
    if start <= 0 or radius < 0:
        raise ValueError("positive block start and nonnegative radius required")
    exact = [Fraction.from_float(float(x)) for x in lengths]
    if any(x <= radius for x in exact):
        raise ValueError("length intervals must remain positive")
    lower = sorted(x-radius for x in exact)
    upper = sorted(x+radius for x in exact)
    end = 2*start
    points = {start, end}
    for length in lower+upper:
        for event in (length, length/2):
            if start < event < end:
                points.add(event)
    low_max = high_max = Fraction(0)
    for point in sorted(points):
        selectors = [bisect_right] if point == start else [bisect_left, bisect_right]
        for select in selectors:
            lo = select(upper, 2*point)-4*select(lower, point)
            hi = select(lower, 2*point)-4*select(upper, point)
            low_abs = 0 if lo <= 0 <= hi else min(abs(lo), abs(hi))
            high_abs = max(abs(lo), abs(hi))
            low_max = max(low_max, low_abs/point)
            high_max = max(high_max, high_abs/point)
    return {"length_error_radius_assumed": str(radius),
            "scope": "supplied_finite_curve_list_with_fixed_membership",
            "omitted_curves_cannot_enter_thresholds_assumed": True,
            "lower_exact_rational": str(low_max), "upper_exact_rational": str(high_max),
            "lower_approx": float(low_max), "upper_approx": float(high_max),
            "width_approx": float(high_max-low_max), "error_assumption_certified": False}


def provenance(fixture_path):
    paths = [Path(__file__), fixture_path, HERE / "tests/test_diagnostic.py",
             ROOT / "book/chapters/30-sharp-diagnostics.tex"]
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"],
                                   text=True).strip()
    status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"],
                                     text=True).splitlines()
    return {"source_commit": head, "repository_dirty_at_start": bool(status),
            "git_status_porcelain_at_start": status,
            "source_sha256": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
                              for p in paths},
            "python": platform.python_version(), "platform": platform.platform(),
            "generated_at_utc": datetime.now(timezone.utc).isoformat()}


def build_report():
    fixture_path = HERE / "fixture.json"
    fixture = json.loads(fixture_path.read_text())
    cutoff, blocks = fixture["length_cutoff"], fixture["block_starts"]
    if cutoff != 64 or blocks != [4, 8, 16]:
        raise ValueError("this reviewed replacement is fixed to length64 and T=4,8,16")
    result = {"schema_version": "1.0", "experiment_id": fixture["experiment_id"],
              "provenance": provenance(fixture_path), "fixture": fixture,
              "evidence_status": "bounded_replacement_numerical_check",
              "certified": False,
              "scope": ["Unoriented essential simple curves, with slope multiplicities.",
                        "Exact algebraic traces; Decimal lengths are numerical.",
                        "No reproduction of the reported length8192 campaign.",
                        "No inferred asymptotic remainder or rigorous event-location bounds."],
              "checks_passed_scope": [
                  "Exact input Markoff equations and reduced-root inequalities.",
                  "Identical slope sets from binary64 traversal and two decimal finite-box evaluations.",
                  "Decimal length differences <=1e-90; binary64 log length differences <=1e-10.",
                  "Event sweep versus direct-count M/Q differences <=1e-12 for oracle-rounded lengths."
              ],
              "diagnostic_only": [
                  "Log versus exact-trace M/Q discrepancies are reported, not a certification of event order.",
                  "Conditional M bounds assume their stated length-error radius; that radius is not certified."
              ],
              "surfaces": []}
    begun = time.perf_counter()
    for record in fixture["surfaces"]:
        started = time.perf_counter()
        roots = fixture_roots(record)
        floating, work = log_spectrum(roots, cutoff)
        reference, box = box_spectrum(roots, cutoff, fixture["reference_decimal_digits"])
        higher, higher_box = box_spectrum(roots, cutoff, fixture["check_decimal_digits"])
        same_slopes = floating.keys() == reference.keys() == higher.keys()
        if not same_slopes:
            raise ArithmeticError("log traversal and independent box slope sets disagree")
        with localcontext() as ctx:
            ctx.prec = fixture["check_decimal_digits"]
            precision_residual = max(abs(reference[s][1]-higher[s][1]) for s in reference)
            log_residual = max(abs(Decimal.from_float(floating[s])-higher[s][1])
                               for s in reference)
        oracle_lengths = [float(v[1]) for v in higher.values()]
        log_lengths = list(floating.values())
        metrics = []
        for start in blocks:
            event = block_metrics(oracle_lengths, start)
            direct = direct_block_metrics(oracle_lengths, start)
            log_event = block_metrics(log_lengths, start)
            errors = {name: abs(event[name]-direct[name]) for name in ("M", "Q")}
            if max(errors.values()) > 1e-12:
                raise ArithmeticError("event sweep disagrees with direct counting")
            metrics.append({**event, "direct_count_oracle": direct,
                            "direct_count_absolute_residual": errors,
                            "log_trace_metrics": log_event,
                            "conditional_M_bounds": conditional_maximum_bounds(
                                oracle_lengths, start, fixture["sensitivity_radius"]),
                            "log_vs_exact_trace_absolute_residual": {
                                name: abs(event[name]-log_event[name]) for name in ("M", "Q")}})
        if precision_residual > Decimal("1e-90") or log_residual > Decimal("1e-10"):
            raise ArithmeticError("declared numerical comparison tolerance failed")
        curves = [{"slope": list(s), "trace_qsqrt11": higher[s][0].json(),
                   "length_decimal": str(higher[s][1]), "length_log_binary64": floating[s]}
                  for s in sorted(reference)]
        result["surfaces"].append({"id": record["id"], "curve_count": len(reference),
            "exact_root_markoff_residual": {"rational": "0", "sqrt11": "0"},
            "all_slope_sets_equal": same_slopes,
            "maximum_decimal_length_precision_difference": str(precision_residual),
            "maximum_log_vs_decimal_length_difference": str(log_residual),
            "maximum_log_vs_exact_trace_metric_difference": {
                name: max(row["log_vs_exact_trace_absolute_residual"][name] for row in metrics)
                for name in ("M", "Q")},
            "log_work": work, "reference_box": box, "higher_precision_box": higher_box,
            "blocks": metrics, "curves": curves,
            "elapsed_seconds": time.perf_counter()-started})
    result["elapsed_seconds"] = time.perf_counter()-begun
    result["checks_passed"] = True
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON evidence file; existing files are never overwritten")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new path to preserve prior evidence")
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"output": str(args.output), "checks_passed": True,
                      "counts": {s["id"]: s["curve_count"] for s in report["surfaces"]}}))


if __name__ == "__main__":
    main()
