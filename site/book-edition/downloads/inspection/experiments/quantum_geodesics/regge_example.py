#!/usr/bin/env python3
"""Finite equilateral Wigner 6j illustration for monograph Section 10.1.

Copyright 2026 Igor Rivin. SPDX-License-Identifier: MIT
See LICENSES/new-companions-MIT.txt for the scoped license.

The Racah sum is exact rational arithmetic. The Ponzano--Regge term and
angle deficit use mpmath at two precisions, without an interval enclosure.
This deliberately does not evaluate arbitrary or root-of-unity 6j-symbols.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from math import factorial
from pathlib import Path
import platform

import mpmath


SPINS = (10, 20, 40)
PRECISIONS = (80, 120)


def equilateral_symbol(n: int) -> Fraction:
    """Racah's finite sum with all six spins equal to the integer n."""
    if type(n) is not int or n < 0:
        raise ValueError("equal spin must be a nonnegative integer")
    prefactor = Fraction(factorial(n) ** 6, factorial(3 * n + 1) ** 2)
    return prefactor * sum(
        (Fraction((-1) ** z * factorial(z + 1),
                  factorial(z - 3 * n) ** 4 * factorial(4 * n - z) ** 3)
         for z in range(3 * n, 4 * n + 1)),
        Fraction(0),
    )


def evaluate(digits: int) -> dict:
    ctx = mpmath.mp.clone()
    ctx.dps = digits
    fmt = lambda x: ctx.nstr(x, digits)
    theta = ctx.acos(ctx.mpf(1) / 3)
    exterior = ctx.pi - theta
    rows = []
    for n in SPINS:
        rational = equilateral_symbol(n)
        exact_decimal = ctx.mpf(rational.numerator) / rational.denominator
        length = ctx.mpf(n) + ctx.mpf(1) / 2
        volume = length ** 3 / (6 * ctx.sqrt(2))
        phase = 6 * length * exterior + ctx.pi / 4
        leading = ctx.cos(phase) / ctx.sqrt(12 * ctx.pi * volume)
        error = abs(exact_decimal - leading)
        if not all(ctx.isfinite(x) for x in (exact_decimal, volume, phase, leading, error)):
            raise ArithmeticError("nonfinite example value")
        rows.append({
            "spin": n,
            "exact_rational": {"numerator": str(rational.numerator), "denominator": str(rational.denominator)},
            "exact_decimal": fmt(exact_decimal),
            "edge_length": fmt(length),
            "volume": fmt(volume),
            "phase": fmt(phase),
            "leading_term": fmt(leading),
            "absolute_difference": fmt(error),
            "table": {
                "exact": ctx.nstr(exact_decimal, 6, strip_zeros=False),
                "leading": ctx.nstr(leading, 6, strip_zeros=False),
                "absolute_difference": ctx.nstr(error, 3, strip_zeros=False),
            },
        })
    return {"decimal_digits": digits, "interior_angle": fmt(theta),
            "exterior_angle": fmt(exterior), "five_tetrahedra_deficit": fmt(2 * ctx.pi - 5 * theta),
            "rows": rows}


def result() -> dict:
    source = Path(__file__).resolve().read_bytes()
    runs = [evaluate(digits) for digits in PRECISIONS]
    ctx = mpmath.mp.clone()
    ctx.dps = max(PRECISIONS)
    residuals = []
    for low, high in zip(runs[0]["rows"], runs[1]["rows"], strict=True):
        if low["exact_rational"] != high["exact_rational"] or low["table"] != high["table"]:
            raise ArithmeticError("exact value or displayed rounding differs between precisions")
        for field in ("exact_decimal", "leading_term", "absolute_difference"):
            difference = abs(ctx.mpf(low[field]) - ctx.mpf(high[field]))
            if difference > ctx.mpf("1e-70"):
                raise ArithmeticError("cross-precision absolute difference exceeds 1e-70")
            residuals.append({"spin": low["spin"], "quantity": field,
                              "absolute_difference": ctx.nstr(difference, 35)})
    return {
        "schema_version": 1,
        "evidence_status": "exact finite Racah values and uncertified floating illustration",
        "source_sha256": hashlib.sha256(source).hexdigest(),
        "software": {"python": platform.python_version(), "mpmath": mpmath.__version__},
        "conventions": {
            "symbol": "ordinary symmetric Wigner 6j, q=1, six equal integer spins N",
            "lengths": "dimensionless L=N+1/2 on every edge",
            "angles": "interior acos(1/3); phase uses exterior acos(-1/3)",
            "volume": "Euclidean L^3/(6*sqrt(2))",
            "leading_term": "cos(6*L*exterior+pi/4)/sqrt(12*pi*volume)",
            "exact_source": "https://dlmf.nist.gov/34.4.E2",
            "asymptotic_source": "https://arxiv.org/abs/math-ph/9812013",
        },
        "runs": runs,
        "cross_precision": {"criterion": "absolute difference <= 1e-70; displayed table entries agree",
                            "residuals": residuals},
        "limits": "Two precisions are an internal consistency check, not an independent oracle or an interval bound. Finite examples do not prove the asymptotic theorem or its error order.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True,
                        help="new JSON file in an existing directory")
    args = parser.parse_args()
    encoded = json.dumps(result(), indent=2, allow_nan=False) + "\n"
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(encoded)


if __name__ == "__main__":
    main()
