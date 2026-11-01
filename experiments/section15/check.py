#!/usr/bin/env python3
"""Check Section 15's finite algebra and Airy column, not its quantum integral."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
import json
from math import factorial
from pathlib import Path
import platform
import re
import subprocess
import time

import mpmath as mp


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHAPTER = ROOT / "book/chapters/15-quantum-airy.tex"
FIXTURE = HERE / "historical-table.json"


@dataclass(frozen=True)
class Q2:
    """An exact element a + b sqrt(2), with rational coefficients."""

    a: Fraction = Fraction(0)
    b: Fraction = Fraction(0)

    @staticmethod
    def coerce(value):
        if isinstance(value, Q2):
            return value
        if isinstance(value, (int, Fraction)) and not isinstance(value, bool):
            return Q2(Fraction(value))
        raise TypeError("Q2 accepts only exact integers, rationals, or Q2 values")

    def __add__(self, other):
        other = self.coerce(other)
        return Q2(self.a + other.a, self.b + other.b)

    __radd__ = __add__

    def __neg__(self):
        return Q2(-self.a, -self.b)

    def __sub__(self, other):
        return self + -self.coerce(other)

    def __rsub__(self, other):
        return self.coerce(other) + -self

    def __mul__(self, other):
        other = self.coerce(other)
        return Q2(self.a * other.a + 2 * self.b * other.b,
                  self.a * other.b + self.b * other.a)

    __rmul__ = __mul__

    def __truediv__(self, other):
        other = self.coerce(other)
        norm = other.a**2 - 2 * other.b**2
        if not norm:
            raise ZeroDivisionError("division by zero in Q(sqrt(2))")
        return self * Q2(other.a / norm, -other.b / norm)

    def __rtruediv__(self, other):
        return self.coerce(other) / self

    def __pow__(self, power):
        if not isinstance(power, int) or power < 0:
            raise ValueError("only nonnegative integer powers are used")
        answer = Q2(Fraction(1))
        for _ in range(power):
            answer = answer * self
        return answer

    def record(self):
        return {"rational": str(self.a), "sqrt2_coefficient": str(self.b)}


SQRT2 = Q2(Fraction(0), Fraction(1))


def polynomial_product(left, right):
    result = [Fraction(0)] * (len(left) + len(right) - 1)
    for i, x in enumerate(left):
        for j, y in enumerate(right):
            result[i + j] += x * y
    return result


def algebra_checks():
    """Differentiate the five affine-angle terms, using Lambda'=-log(2sin)."""
    # Derive the fold cotangents from cos(eta_E)=1/3 and sin(eta_E)>0.
    eta_cos, eta_sin = Q2(Fraction(1, 3)), 2*SQRT2/3
    half_cot = (1 + eta_cos)/eta_sin

    def multiple_cot(cot, multiple):
        result = cot
        for _ in range(1, multiple):
            result = (result*cot - 1)/(result + cot)
        return result

    cotangents = (eta_sin/eta_cos, half_cot, multiple_cot(half_cot, 5),
                  1/half_cot, 1/multiple_cot(half_cot, 3))
    # (coefficient in G, angle_v, angle_eta, cot(angle) at the fold).
    terms = [
        (-8, Fraction(1, 2), Fraction(3, 2), cotangents[0]),
        (-6, Fraction(-1, 2), Fraction(-2), cotangents[1]),
        (-2, Fraction(-1, 2), Fraction(0), cotangents[2]),
        (12, Fraction(0), Fraction(-1, 2), cotangents[3]),
        (-4, Fraction(0), Fraction(-3, 2), cotangents[4]),
    ]

    def derivative(v_order, eta_order):
        order = v_order + eta_order
        result = Q2()
        for weight, av, ae, cot in terms:
            if order == 2:
                kernel = -cot
            elif order == 3:
                kernel = 1 + cot**2
            elif order == 4:
                kernel = -2 * cot * (1 + cot**2)
            else:
                raise ValueError("this check uses derivatives of orders two to four")
            result += weight * kernel * av**v_order * ae**eta_order
        return result

    checks = []

    def check(name, actual, expected):
        actual, expected = Q2.coerce(actual), Q2.coerce(expected)
        checks.append({"name": name, "actual": actual.record(),
                       "expected": expected.record(), "passed": actual == expected})

    for name, actual, expected in zip(("theta1", "theta2", "theta3", "s", "3s"),
                                      cotangents,
                                      (2*SQRT2, SQRT2, -11*SQRT2, SQRT2/2, -5*SQRT2/2)):
        check(f"cot({name}) at fold", actual, expected)
    # Positive sines fix the signs; squared identities avoid sqrt(3) arithmetic.
    sine2 = []
    for name, cot, expected in zip(("theta1", "theta2", "theta3"), cotangents,
                                    (Fraction(1, 9), Fraction(1, 3), Fraction(1, 243))):
        value = 1/(1+cot**2)
        check(f"sin({name}) squared at fold", value, expected)
        sine2.append(value.a)
    sine_ratio = 1/(3-4/(1+cotangents[3]**2))
    check("sin(s)/sin(3s) at fold", sine_ratio, 3)
    check("exp(2 G_v) positive-sine ratio", (4*sine2[0])**4 /
          ((4*sine2[1])**3 * (4*sine2[2])), 1)
    check("exp(G_eta/6) positive-sine ratio", sine2[0]/sine2[1] * sine_ratio, 1)
    amplitude_squared = (4*sine2[0])**-2 * Fraction(1, 9)**3 * 3**6
    check("A_star squared; A_star positive", amplitude_squared, Fraction(81, 16))
    log_amplitude_v = -2*terms[0][3]/2 + Fraction(3, 4)*terms[1][3] \
        - Fraction(3, 4)*terms[2][3]
    check("(log A)_v", log_amplitude_v, 7*SQRT2)
    expected = {(2, 0): 0, (3, 0): 54, (1, 1): 18*SQRT2,
                (0, 2): 36*SQRT2, (4, 0): -648*SQRT2, (2, 1): -18}
    for orders, value in expected.items():
        check(f"G derivative v^{orders[0]} eta^{orders[1]}", derivative(*orders), value)

    # Clear the three denominators in Psi'(r)/sqrt(2), as a polynomial in u=r^2.
    denominators = ([1, 8], [1, 2], [1, 242])
    numerator = [Fraction(0)] * 3
    for i, coefficient in enumerate((8, 3, -11)):
        pair = [denominators[j] for j in range(3) if j != i]
        for j, value in enumerate(polynomial_product(*pair)):
            numerator[j] += coefficient * value
    for i, value in enumerate((0, 864*3, 864*11)):
        check(f"Psi derivative numerator coefficient u^{i}", numerator[i], value)

    # Weighted substitution x=lambda Y/3, t=lambda^2 zeta/(6 sqrt(2)).
    check("leading Y^3", derivative(3, 0)/factorial(3)/27, Fraction(1, 3))
    check("leading zeta Y", -derivative(1, 1)/(18*SQRT2), -1)
    correction = {
        "Y": log_amplitude_v / 3,
        "Y4": derivative(4, 0) / factorial(4) / 81,
        "zetaY2": -derivative(2, 1) / (108*SQRT2),
        "zeta2": derivative(0, 2) / 144,
    }
    for name, value in {"Y": 7*SQRT2/3, "Y4": -SQRT2/3,
                        "zetaY2": 1/(6*SQRT2), "zeta2": SQRT2/4}.items():
        check(f"correction coefficient {name}", correction[name], value)
    # Integral Y^k=(-1)^k Ai^(k); Ai''=zeta Ai and Ai''''=2 Ai'+zeta^2 Ai.
    check("integrated Ai prime coefficient", -correction["Y"] + 2*correction["Y4"],
          -3*SQRT2)
    check("integrated zeta^2 Ai cancellation", correction["Y4"] +
          correction["zetaY2"] + correction["zeta2"], 0)
    check("coefficient of lambda/b after oriented Airy integral", Fraction(9, 4)/3,
          Fraction(3, 4))
    return {"arithmetic": "exact rational pairs a+b*sqrt(2)", "checks": checks,
            "all_passed": all(row["passed"] for row in checks),
            "not_checked": ["G_star=0 Lobachevsky identity", "double-sine integral",
                            "uniform remainders and contour deformation",
                            "global transition theorem"]}


def airy_series(z, terms):
    """Airy ODE series, independent of airyai; only used at z=0 or z=1.

    DLMF 9.2.1, 9.2.3-4 and 9.4.1 supply the ODE and initial values.
    The numerical gamma values are shared mpmath primitives, not a second library.
    """
    if z not in (0, 1):
        raise ValueError("this bounded oracle is only intended for z=0 and z=1")
    coefficients = [1/(mp.power(3, mp.mpf(2)/3)*mp.gamma(mp.mpf(2)/3)),
                    -1/(mp.power(3, mp.mpf(1)/3)*mp.gamma(mp.mpf(1)/3)), mp.mpf(0)]
    for k in range(3, terms):
        coefficients.append(coefficients[k-3]/(k*(k-1)))
    value = mp.fsum(coefficients[k]*z**k for k in range(terms))
    derivative = mp.fsum(k*coefficients[k]*z**(k-1) for k in range(1, terms))
    return value, derivative


def approximation_checks(fixture):
    """Recompute the asymptotic column; historical Q_b is input, never output."""
    runs = []
    # workdps context: https://github.com/mpmath/mpmath/blob/master/docs/basics.rst
    # airyai(..., derivative=1): installed mpmath 1.3.0 airyai docstring.
    for digits in (80, 120):
        with mp.workdps(digits):
            rows = []
            tolerance = mp.power(10, -(digits-10))
            for original in fixture["rows"]:
                b, zeta = mp.mpf(original["b"]), mp.mpf(original["zeta"])
                h = 2*mp.pi*b*b
                lam = mp.root(h, 3)
                ai, aip = mp.airyai(zeta), mp.airyai(zeta, derivative=1)
                ai_series, aip_series = airy_series(zeta, 2*digits)
                approximation = ai - 3*mp.sqrt(2)*lam*aip
                series_approximation = ai_series - 3*mp.sqrt(2)*lam*aip_series
                residual = abs(approximation-series_approximation)
                rounded_error = abs(approximation-mp.mpf(original["printed_Q1"]))
                # These are arithmetic diagnostics of rounded historical inputs.
                # They do not reconstruct original quadrature precision or errors.
                scaled = (mp.mpf(original["reported_Q"])-approximation)/lam**2
                half_width = mp.mpf("0.0000005")/lam**2
                rows.append({**original,
                    "computed_Q1": mp.nstr(approximation, digits),
                    "ode_series_Q1": mp.nstr(series_approximation, digits),
                    "series_terms": 2*digits,
                    "series_comparison_absolute_residual": mp.nstr(residual, digits),
                    "printed_column_absolute_residual": mp.nstr(rounded_error, digits),
                    "printed_Q1_agrees_to_six_decimal_places": bool(rounded_error <= mp.mpf("0.0000005")),
                    "series_comparison_passed": bool(residual < tolerance),
                    "scaled_difference_from_rounded_reported_Q": mp.nstr(scaled, 30),
                    "scaled_half_width_if_reported_Q_was_rounded_to_nearest": mp.nstr(half_width, 30),
                    "quantum_integral_replayed": False})
            runs.append({"working_decimal_digits": digits,
                         "series_comparison_absolute_tolerance": mp.nstr(tolerance, 10),
                         "rows": rows})
    with mp.workdps(130):
        stability = [abs(mp.mpf(a["computed_Q1"])-mp.mpf(b["computed_Q1"]))
                     for a, b in zip(runs[0]["rows"], runs[1]["rows"])]
        stable = all(value < mp.mpf("1e-70") for value in stability)
        differences = [mp.nstr(value, 20) for value in stability]
    passed = stable and all(row["series_comparison_passed"] and
                            row["printed_Q1_agrees_to_six_decimal_places"]
                            for run in runs for row in run["rows"])
    return {"runs": runs, "precision_stability_absolute_differences": differences,
            "precision_stability_absolute_tolerance": "1e-70", "all_passed": passed,
            "arithmetic": "mpmath numerical approximation; no interval arithmetic",
            "historical_quantum_integral_replayed": False}


def chapter_table_matches(fixture):
    pattern = r"\$(\d+\.\d+)\$&\$([01])\$&\$(\d+\.\d+)\$&\$(\d+\.\d+)\$"
    rows = re.findall(pattern, CHAPTER.read_text())
    expected = [(row["b"], row["zeta"], row["reported_Q"], row["printed_Q1"])
                for row in fixture["rows"]]
    return rows == expected


def provenance():
    files = [Path(__file__).resolve(), FIXTURE, CHAPTER]
    commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).splitlines()
    return {"source_commit": commit, "repository_dirty_at_start": bool(status),
            "git_status_porcelain_at_start": status,
            "source_sha256": {str(path.relative_to(ROOT)): sha256(path.read_bytes()).hexdigest()
                              for path in files},
            "python": platform.python_version(), "mpmath": mp.__version__,
            "generated_at_utc": datetime.now(timezone.utc).isoformat()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="JSON report destination")
    args = parser.parse_args()
    start = time.perf_counter()
    source = provenance()
    fixture = json.loads(FIXTURE.read_text())
    exact = algebra_checks()
    numerical = approximation_checks(fixture)
    matches = chapter_table_matches(fixture)
    result = {"schema_version": "1.0", "operation": "section15_finite_checks",
              "evidence_status": "exact_finite_algebra_and_numerical_asymptotic_column",
              "conventions": {"h": "2*pi*b^2", "lambda": "h^(1/3)",
                              "eta": "acos(1/3)-h^(2/3)*zeta/(6*sqrt(2))",
                              "contour_orientation_in_algebra": "upward; dw/i"},
              "provenance": source, "historical_table_provenance": fixture["provenance"],
              "chapter_retains_historical_rows": matches,
              "algebra": exact, "approximation": numerical,
              "quantum_integral_replayed": False, "uniform_theorem_verified": False,
              "runtime_seconds": time.perf_counter()-start,
              "all_checks_passed": exact["all_passed"] and numerical["all_passed"] and matches}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"all_checks_passed": result["all_checks_passed"],
                      "exact_checks": len(exact["checks"]),
                      "approximation_rows": len(fixture["rows"]),
                      "quantum_integral_replayed": False, "output": str(args.output)}))
    return 0 if result["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
