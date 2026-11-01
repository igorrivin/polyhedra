"""Independent whole-log-S reference; never imports the production companion.

The complete weighted log is integrated from the convergent Barnes integral.
The origin uses its Taylor series, and the explicit algebraic subtraction is
integrated analytically on [1,infinity).  SciPy QUADPACK provides both inner
and outer quadrature, unlike the companion's mpmath Gauss-Legendre quadrature.
All reported errors remain heuristic.  mpmath generates parameters and local
Taylor coefficients, not dilogarithms, cot-polynomial D series, or Airy values.

SciPy API inspected through Context7, /scipy/scipy, 2026-11-01:
https://github.com/scipy/scipy/blob/main/scipy/integrate/_quadpack_py.py
"""

import argparse
import cmath
import hashlib
import json
import math
from pathlib import Path
from time import perf_counter
import warnings

import mpmath as mp
import scipy
from scipy.integrate import IntegrationWarning, quad


WEIGHTS = (4, 3, 1, 2, -6)


def params(t, b_text="1/80", zeta_text="0", c_text="1", dps=45):
    with mp.workdps(dps):
        def rat(s):
            a, slash, b = s.partition("/")
            return mp.mpf(a) / mp.mpf(b) if slash else mp.mpf(a)
        b, zeta, c = rat(b_text), rat(zeta_text), rat(c_text)
        eta_e = mp.acos(mp.mpf(1) / 3)
        lam = mp.root(2 * mp.pi * b**2, 3)
        eta = eta_e - lam**2 * zeta / (6 * mp.sqrt(2))
        w = (4 * mp.pi - 5 * eta_e + lam * (c + 1j * mp.mpf(t)) / 3) / (2 * mp.pi * b)
        alpha, q = (mp.pi - eta) / (2 * mp.pi * b), b + 1 / b
        xs = (w - 3 * alpha, 4 * alpha - w, 2 * q - w, 3 * alpha - b, alpha)
        aa = tuple(b * (q - 2 * x) for x in xs)
        a_sum = 4 * b**2  # algebraic identity from the original Barnes variables
        residual = abs(mp.fsum(k * a for k, a in zip(WEIGHTS, aa)) - a_sum)
        coefficients = []
        for n in range(1, 22):
            sinh_sum = mp.fsum(k * a**(2*n+1) for k, a in zip(WEIGHTS, aa)) / mp.factorial(2*n+1)
            product = mp.fsum(b**(4*j) / (mp.factorial(2*j+1) * mp.factorial(2*(n-j)+1))
                              for j in range(n+1))
            coefficients.append(complex(sinh_sum - a_sum * product))
        return float(b**2), tuple(complex(a) for a in aa), coefficients, mp.nstr(residual, 12)


def csum(items):
    items = tuple(items)
    return complex(math.fsum(x.real for x in items), math.fsum(x.imag for x in items))


def log_reference(t, b="1/80", zeta="0", contour="1", eps=2e-10):
    b2, aa, coefficients, algebra_residual = params(t, b, zeta, contour)

    def origin(s):
        p = 0j
        for coefficient in reversed(coefficients):
            p = coefficient + s*s*p
        if s == 0:
            return p / (2*b2)
        return p / (2*b2 * (math.sinh(s)/s) * (math.sinh(b2*s)/(b2*s)))

    def tail(s):
        denominator = s * (-math.expm1(-2*s)) * (-math.expm1(-2*b2*s))
        return csum(k * (cmath.exp((a-1-b2)*s) - cmath.exp((-a-1-b2)*s))
                    for k, a in zip(WEIGHTS, aa)) / denominator

    def integrate_piece(fn, left, right):
        re, re_error = quad(lambda s: fn(s).real, left, right, epsabs=eps, epsrel=eps, limit=160)
        im, im_error = quad(lambda s: fn(s).imag, left, right, epsabs=eps, epsrel=eps, limit=160)
        return complex(re, im), re_error + im_error

    values, errors = [], []
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", IntegrationWarning)
        value, error = integrate_piece(origin, 0, 1)
        values.append(value)
        errors.append(error)
        edges = (1, 4, 16, 64, 256, 1024, math.inf)
        for left, right in zip(edges, edges[1:]):
            value, error = integrate_piece(tail, left, right)
            values.append(value)
            errors.append(error)
    return csum(values) - 2, math.fsum(errors), [str(w.message) for w in caught], algebra_residual


def whole_q(b="1/80", zeta="0", contour="1", cutoff=8):
    started = perf_counter()
    cache, warnings_seen, algebra_residuals = {}, [], []

    def integrand(t):
        if t not in cache:
            value, estimate, warning_texts, residual = log_reference(t, b, zeta, contour)
            warnings_seen.extend(warning_texts)
            algebra_residuals.append(float(residual))
            cache[t] = (cmath.exp(value), estimate)
        return cache[t][0].real

    values, errors = [], []
    for left in range(cutoff):
        value, estimate = quad(integrand, left, left+1, epsabs=2e-9, epsrel=2e-9, limit=80)
        values.append(value)
        errors.append(estimate)
    norm = 4 / (9*math.pi)
    return {
        "b": b, "zeta": zeta, "contour": contour, "cutoff": cutoff,
        "Q": norm * math.fsum(values),
        "outer_internal_error_estimate": norm * math.fsum(errors),
        "max_inner_log_internal_error_estimate": max(item[1] for item in cache.values()),
        "max_original_argument_linear_identity_residual": max(algebra_residuals),
        "integration_warnings": sorted(set(warnings_seen)),
        "integrand_evaluations": len(cache), "elapsed_seconds": perf_counter()-started,
        "unit_panel_contributions_normalized": [norm*v for v in values],
        "evidence_status": "independent_whole_Barnes_log_QUADPACK_double_precision_not_interval",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--whole", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists")
    started = perf_counter()
    probes = []
    for t in (0, 1, 3, 8):
        tick = perf_counter()
        value, error, warning_texts, residual = log_reference(t)
        probes.append({"t": t, "log": {"real": value.real, "imag": value.imag},
                       "internal_error_estimate": error, "warnings": warning_texts,
                       "original_linear_identity_residual": residual,
                       "elapsed_seconds": perf_counter()-tick})
    result = {"reference_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scipy": scipy.__version__, "mpmath": mp.__version__, "point_probes": probes,
              "limitations": ["No interval enclosure; QUADPACK errors are heuristics.",
                              "Local 21-term Taylor cancellation series is unvalidated floating point.",
                              "Parameters and local coefficients share the mpmath backend with the author.",
                              "No finite-cutoff tail is included in the reported Q value."]}
    if args.whole:
        result["whole_Q"] = [whole_q(), whole_q(contour="5/4")]
    result["elapsed_seconds"] = perf_counter()-started
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
