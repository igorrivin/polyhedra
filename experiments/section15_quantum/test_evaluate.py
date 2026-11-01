"""Focused regression checks for component bounds and result-contract failures."""

from fractions import Fraction
import os
from pathlib import Path
import subprocess
import sys

import mpmath as mp
import pytest

import check as driver
from evaluate import (DoubleSine, Parameters, cot_polynomials, d_remainder_bound,
                      d_tail_bound, finite, integrate)


def test_exact_bound_and_cot_derivatives():
    assert cot_polynomials(3) == [(1, 0), (2, 0, 2, 0), (24, 0, 40, 0, 16, 0)]
    bound = d_remainder_bound(Fraction(1, 80), Fraction(1, 100), 15)
    assert isinstance(bound, Fraction)
    assert 0 < 16 * bound < Fraction(1, 10 ** 45)
    assert d_remainder_bound('1/160', '1/100', 15) == bound / 2 ** 62


@pytest.mark.parametrize('value', [mp.nan, mp.inf, -mp.inf, mp.mpc(0, mp.nan)])
def test_nonfinite_fails_closed(value):
    with pytest.raises(ArithmeticError):
        finite(value)


@pytest.mark.parametrize('b,epsilon,k', [('0', '1/100', 3), ('-1', '1/100', 3),
                                      ('1/80', '0', 3), ('1/80', '3/4', 3),
                                      ('1/80', '1/100', 0)])
def test_invalid_bound_inputs(b, epsilon, k):
    with pytest.raises(ValueError):
        d_remainder_bound(b, epsilon, k)


def test_centered_strip_is_not_replaced_by_original_strip():
    with mp.workdps(40):
        sb = DoubleSine('1/80', 45)
        with pytest.raises(ValueError):
            sb.correction(mp.mpf('0.999'))
        assert abs(sb.correction(mp.mpf('0.5'))) < mp.mpf('1e-40')


def test_bad_quadrature_parameters_fail_before_running():
    with pytest.raises(ValueError):
        integrate(Parameters('1/80', '0', '1', 12, 10))
    with pytest.raises(ValueError):
        integrate(Parameters('1/80', '0', '1', 1, 40))
    with pytest.raises(ValueError):
        integrate(Parameters('1/80', '0', '-1', 12, 40))


def test_odd_cutoff_decomposes_the_entire_integral():
    result = integrate(Parameters('1/80', '0', '2', 5, 30))
    comparison = result['cutoff_comparison']
    assert comparison['shorter_cutoff'] == 3
    assert 3 in result['panels']
    with mp.workdps(40):
        residual = (comparison['Q_at_shorter_cutoff']
                    + comparison['extension_contribution'] - result['Q'])
        assert abs(residual) < mp.mpf('1e-28')


def test_direct_D_tail_bound_is_exact_and_has_expected_scaling():
    value = d_tail_bound('1/80', '1/50', 8192)
    assert isinstance(value, Fraction)
    assert value == Fraction(1, 80) ** 2 / (6 * Fraction(1, 50) * 2 ** 327)
    assert d_tail_bound('1/160', '1/50', 8192) == value / 4
    with pytest.raises(ValueError):
        d_tail_bound('1/80', '1/50', 0)


@pytest.mark.parametrize('changed', ['commit', *driver.SOURCE_PATHS])
def test_all_source_and_HEAD_drift_fails_closed(changed):
    before = {'commit': 'head', 'sha256': {p: 'hash' for p in driver.SOURCE_PATHS}}
    after = {'commit': 'head', 'sha256': dict(before['sha256'])}
    if changed == 'commit':
        after['commit'] = 'changed'
    else:
        after['sha256'][changed] = 'changed'
    with pytest.raises(RuntimeError):
        driver.validate_source_stability(before, after)


def test_source_gate_accepts_unchanged_sources():
    snapshot = {'commit': 'head', 'sha256': {p: 'hash' for p in driver.SOURCE_PATHS}}
    driver.validate_source_stability(snapshot, snapshot)


def test_output_refuses_overwrite_before_computing(tmp_path, monkeypatch):
    output = tmp_path / 'existing.json'
    output.write_text('preserved')

    def unexpected_run(profile):
        pytest.fail('computation ran before existing-output refusal')

    monkeypatch.setattr(driver, 'run', unexpected_run)
    with pytest.raises(SystemExit) as exception:
        driver.main(['--profile', 'smoke', '--output', str(output)])
    assert exception.value.code == 2
    assert output.read_text() == 'preserved'


def test_package_import_from_another_CWD_has_no_output_or_file_writes(tmp_path):
    env = dict(os.environ)
    env['PYTHONPATH'] = str(Path(__file__).resolve().parents[2])
    result = subprocess.run([sys.executable, '-c',
                             'import experiments.section15_quantum.check'],
                            cwd=tmp_path, env=env, text=True, capture_output=True, check=True)
    assert result.stdout == result.stderr == ''
    assert list(tmp_path.iterdir()) == []


def test_integer_polynomial_failure_does_not_depend_on_assert(monkeypatch):
    monkeypatch.setattr(driver, 'cot_polynomials', lambda terms: [])
    with pytest.raises(ArithmeticError, match='polynomial'):
        driver.independent_checks(30)
