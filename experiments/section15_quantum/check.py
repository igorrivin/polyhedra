#!/usr/bin/env python3
"""Run separately auditable checks and a fresh Section 15 quantum quadrature."""

import argparse
import hashlib
import json
import math
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import mpmath as mp

if __package__:
    from .evaluate import (ClearedIntegrand, DoubleSine, Parameters, cot_polynomials,
                           d_tail_bound, direct_correction, direct_log_sine, finite,
                           integrate, lobachevsky, rational)
else:
    from evaluate import (ClearedIntegrand, DoubleSine, Parameters, cot_polynomials,
                          d_tail_bound, direct_correction, direct_log_sine, finite,
                          integrate, lobachevsky, rational)


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HISTORY = ROOT / 'experiments/section15/historical-table.json'
SOURCE_PATHS = (
    'experiments/section15_quantum/evaluate.py',
    'experiments/section15_quantum/check.py',
    'experiments/section15_quantum/test_evaluate.py',
    'experiments/section15_quantum/README.md',
    'experiments/section15/historical-table.json',
    'book/chapters/14-normalized-quantum-comparison.tex',
    'book/chapters/15-quantum-airy.tex',
)


def encode(value, digits):
    if isinstance(value, dict):
        return {str(k): encode(v, digits) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encode(v, digits) for v in value]
    if isinstance(value, mp.mpc):
        finite(value)
        return {'real': mp.nstr(value.real, digits), 'imag': mp.nstr(value.imag, digits)}
    if isinstance(value, mp.mpf):
        return mp.nstr(finite(value), digits)
    if isinstance(value, float) and not math.isfinite(value):
        raise ArithmeticError('nonfinite native float in output')
    return value


def source_snapshot():
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()

    return {
        'commit': git('rev-parse', 'HEAD'),
        'dirty_status': git('status', '--porcelain=v1', '--untracked-files=all'),
        'sha256': {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
                   for name in SOURCE_PATHS},
    }


def validate_source_stability(initial, final):
    if initial['commit'] != final['commit']:
        raise RuntimeError('HEAD changed during the computation')
    for name in SOURCE_PATHS:
        if initial['sha256'][name] != final['sha256'][name]:
            raise RuntimeError(f'declared scientific source changed during run: {name}')


def independent_checks(digits):
    start = perf_counter()
    with mp.workdps(digits):
        tol = mp.mpf(10) ** (-(digits - 12))
        sb = DoubleSine('1/80', digits + 5)
        model = ClearedIntegrand(Parameters('1/80', '0', '1', 12, digits))
        records = []

        def check(name, residual, details=None):
            residual = abs(finite(residual))
            if residual >= tol:
                raise ArithmeticError(f'{name} residual {residual} exceeds {tol}')
            records.append({'name': name, 'absolute_residual': residual,
                            'threshold': tol, 'details': details or {}})

        if cot_polynomials(3) != [(1, 0), (2, 0, 2, 0), (24, 0, 40, 0, 16, 0)]:
            raise ArithmeticError('integer cot-derivative polynomial check failed')
        check('first_D_coefficient', sb.coefficients[0] + mp.pi * sb.b ** 2 / 24)
        check('Lobachevsky_midpoint', lobachevsky(mp.mpf('0.5')))
        probe = mp.mpc(mp.mpf('0.2'), mp.mpf('0.03'))
        check('Lobachevsky_derivative',
              mp.diff(lobachevsky, probe) + mp.pi * mp.log(2 * mp.sin(mp.pi * probe)))
        arguments = model.arguments(mp.mpf(3))
        for index, z in enumerate(arguments):
            direct, estimate = direct_correction('1/80', z)
            check(f'D_real_integral_argument_{index + 1}', sb.correction(z) - direct,
                  {'z': z, 'direct_value': direct, 'quadrature_error_estimate': estimate,
                   'series_log_bound_for_one_factor_exact': str(sb.log_bound / 16)})
            if finite(estimate) >= tol:
                raise ArithmeticError('direct D quadrature estimate exceeds threshold')
            check(f'S_reflection_argument_{index + 1}', sb.log(z) + sb.log(1 - z))
            check(f'S_b_shift_argument_{index + 1}',
                  mp.exp(sb.log(z + sb.b ** 2) - sb.log(z))
                  / (2 * mp.sin(mp.pi * (z + sb.b ** 2 / 2))) - 1)
        z = arguments[2]
        if min(mp.re(z), 1 - mp.re(z)) <= rational('1/50'):
            raise ArithmeticError('direct D tail bound centered-strip hypothesis failed')
        alternate, estimate = direct_correction('1/80', z, method='tanh-sinh', finer=True)
        check('D_alternate_method_and_panels_argument_3', sb.correction(z) - alternate,
              {'z': z, 'method': 'tanh-sinh', 'direct_value': alternate,
               'panels': [0, '1/2'] + [2 ** k for k in range(15)] + ['infinity'],
               'integration_domain': ['0', 'infinity'],
               'quadrature_error_estimate': estimate, 'tail_cutoff': 8192,
               'tail_strip_epsilon_exact': '1/50',
               'tail_bound_role': 'separate bound for the exact [8192,infinity) tail, '
                                  'which is included in quadrature; not an omitted-tail error',
               'direct_D_tail_bound_exact': str(d_tail_bound('1/80', '1/50', 8192))})
        if finite(estimate) >= tol:
            raise ArithmeticError('alternate direct D error estimate exceeds threshold')
        for index, z in enumerate((probe, arguments[2])):
            direct, estimate = direct_log_sine('1/80', z)
            check(f'full_log_S_real_integral_{index + 1}', sb.log(z) - direct,
                  {'z': z, 'direct_value': direct, 'quadrature_error_estimate': estimate})
            if finite(estimate) >= tol:
                raise ArithmeticError('full log S quadrature estimate exceeds threshold')
        check('integrand_conjugation', model.log(-mp.mpf(3)) - mp.conj(model.log(mp.mpf(3))))
        # Check all five centered arguments against the original Barnes variables.
        w = (model.v_star + model.lam * (1 + 3j) / 3) / (2 * mp.pi * model.b)
        alpha = (mp.pi - model.eta) / (2 * mp.pi * model.b)
        q = model.b + 1 / model.b
        original = (w - 3 * alpha, 4 * alpha - w, 2 * q - w,
                    3 * alpha - model.b, alpha)
        for index, (x, z) in enumerate(zip(original, arguments)):
            check(f'original_to_centered_argument_{index + 1}',
                  model.b * x - model.b ** 2 / 2 - z)
        # Additional terms must agree within their small component bounds plus rounding.
        refined = DoubleSine('1/80', digits + 5, extra_terms=2)
        check('D_series_extra_terms', refined.correction(arguments[2]) - sb.correction(arguments[2]))
        return encode({'working_dps': digits, 'records': records,
                       'elapsed_seconds': perf_counter() - start,
                       'evidence_status': 'independent_formulas_same_mpmath_backend_not_intervals'}, digits)


def run(profile):
    start = perf_counter()
    initial = source_snapshot()
    historical = json.loads(HISTORY.read_text())
    print('Independent double-sine checks', flush=True)
    checks = []
    for digits in ((30,) if profile == 'smoke' else (40, 60)):
        checks.append(independent_checks(digits))
        print(f'  {digits} dps: {len(checks[-1]["records"])} checks passed; '
              f'{checks[-1]["elapsed_seconds"]:.2f}s', flush=True)
    inputs = [(r['b'], r['zeta']) for r in historical['rows']]
    inputs += [('1/160', '-1')]
    settings = [('60dps_C1_T12', 60, '1', 12, 0),
                ('90dps_C1_T14', 90, '1', 14, 0),
                ('90dps_C5over4_T14_Kplus2', 90, '5/4', 14, 2)]
    if profile == 'smoke':
        inputs, settings = inputs[:1], [('40dps_C1_T12', 40, '1', 12, 0)]
    rows, raw = [], {}
    for b, zeta in inputs:
        for label, digits, contour, cutoff, extra in settings:
            result = integrate(Parameters(b, zeta, contour, cutoff, digits, extra))
            result['setting'] = label
            rows.append(encode(result, digits))
            raw[(b, zeta, label)] = result
            print(f'  b={b} zeta={zeta} {label}: Q={mp.nstr(result["Q"], 24)} '
                  f'({result["elapsed_seconds"]:.2f}s)', flush=True)
    comparisons = []
    if profile == 'full':
        with mp.workdps(100):
            for b, zeta in inputs:
                a, c, d = [raw[(b, zeta, item[0])] for item in settings]
                precision_delta = abs(finite(a['Q'] - c['Q']))
                contour_delta = abs(finite(d['Q'] - c['Q']))
                if precision_delta >= mp.mpf('1e-40') or contour_delta >= mp.mpf('1e-70'):
                    raise ArithmeticError('precision/contour comparison failed')
                item = {'b': b, 'zeta': zeta,
                        'low_high_precision_absolute_difference': precision_delta,
                        'low_high_acceptance_threshold': '1e-40',
                        'changed_contour_and_D_terms_absolute_difference': contour_delta,
                        'changed_contour_acceptance_threshold': '1e-70'}
                previous = next((r for r in historical['rows']
                                 if (r['b'], r['zeta']) == (b, zeta)), None)
                if previous is not None:
                    difference = finite(c['Q'] - rational(previous['reported_Q']))
                    item.update({'historical_reported_Q': previous['reported_Q'],
                                 'new_minus_historical': difference,
                                 'compatible_with_nearest_six_decimal_rounding':
                                     abs(difference) <= mp.mpf('0.0000005'),
                                 'rounding_caveat': 'historical rounding convention is unknown'})
                comparisons.append(encode(item, 90))
    final = source_snapshot()
    validate_source_stability(initial, final)
    return {
        'schema_version': '1.0',
        'profile': profile,
        'status': 'all_declared_checks_passed',
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'runtime': {'python': sys.version, 'executable': sys.executable,
                    'platform': platform.platform(), 'mpmath': mp.__version__},
        'source_at_start': initial, 'source_at_finish': final,
        'conventions': {
            'Q': '4*b/(3*lambda) * cleared_R; h=2*pi*b^2; lambda=h^(1/3)',
            'eta': 'acos(1/3)-lambda^2*zeta/(6*sqrt(2))',
            'contour': 'v=4*pi-5*acos(1/3)+lambda*(C+i*t)/3; upward; C>0',
            'measure': 'dw/i; Q=4/(9*pi)*integral_0^infinity Re(F(t)) dt',
            'F': 'S_b(w-3*alpha)^4*S_b(4*alpha-w)^3*S_b(2*Q_barnes-w)'
                 '*S_b(3*alpha-b)^2/S_b(alpha)^6',
            'centered_log_S': '-Lambda(pi*z)/(pi*b^2)+D_b(z), x=z/b+b/2',
            'branches': 'principal Li2 pair on 0<Re(z)<1; primitive vanishes at z=1/2; '
                        'log S fixed by convergent real integral; all factors combined before exp',
            'outer_quadrature': 'mpmath Gauss-Legendre on explicit panels, real half-contour',
            'direct_D_quadrature': 'Gauss-Legendre panels 0,1,4,16,64,256,1024,2048,4096,'
                                   '8192,infinity; nearest-strip check also uses tanh-sinh '
                                   'with 0,1/2,powers of 2 through16384,infinity',
            'Airy_use': 'comparison column only, never used in the quantum integrand',
        },
        'sources': [
            {'url': 'https://arxiv.org/abs/1202.4698v3',
             'scope': 'equation 2.27 and Appendix A; linear subtraction corrected as in README'},
            {'url': 'https://dlmf.nist.gov/4.36.E5',
             'scope': 'csch partial fractions, retrieved 2026-11-01'},
        ],
        'independent_double_sine_checks': checks,
        'rows': rows, 'comparisons': comparisons,
        'elapsed_seconds': perf_counter() - start,
        'limitations': [
            'No interval arithmetic or outward-rounded quadrature was performed.',
            'The exact rational D bound controls the series truncation in the log, conditional '
            'on the declared centered strip; it does not bound floating-point evaluation error.',
            'Propagated D error uses a numerical absolute-integral estimate.',
            'Quadrature error estimates, tail formula evaluations, and sign checks are '
            'numerical diagnostics, not certificates.',
            'Agreement between precisions, contours, cutoffs, and independent formulas is '
            'finite numerical evidence and does not prove the asymptotic theorem.',
            'Historical values retain their original provenance and unknown rounding convention.',
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', choices=('smoke', 'full'), default='full')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.exists():
        parser.error(f'refusing to overwrite {output}')
    if not output.parent.is_dir():
        parser.error(f'output parent does not exist: {output.parent}')
    result = run(args.profile)
    serialized = json.dumps(result, indent=2, allow_nan=False) + '\n'
    with output.open('x') as handle:
        handle.write(serialized)
    print(f'Wrote {output}', flush=True)


if __name__ == '__main__':
    main()
