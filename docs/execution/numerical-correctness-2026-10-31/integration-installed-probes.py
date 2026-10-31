"""Check selected corrected paths through an installed wheel, outside checkout.

Run in a minimal core environment; this driver never adds a source path.
Independent MP references use the unreduced dilogarithm definition.
"""

import argparse
from fractions import Fraction
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import site
import sys
from types import SimpleNamespace
from unittest.mock import patch

import mpmath as mp
import numpy as np

from ideal_poly_volume_toolkit import geometry as g
from ideal_poly_volume_toolkit import optimization as opt
from ideal_poly_volume_toolkit import rivin_delaunay as rd
from ideal_poly_volume_toolkit import rivin_holonomy as rh
from ideal_poly_volume_toolkit.geometric_realization import realize_from_angles_rigid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    paths = {m.__name__: str(Path(m.__file__).resolve()) for m in (g, opt, rd, rh)}
    assert all('/site-packages/' in p for p in paths.values()), paths
    assert not site.ENABLE_USER_SITE
    absent = {name: importlib.util.find_spec(name) is None for name in
              ('torch', 'gymnasium', 'gradio', 'pytest', 'hypothesis',
               'pynauty', 'matplotlib', 'networkx')}
    assert all(absent.values()), absent
    assert all(name not in sys.modules for name in absent)
    report = {'imports': paths, 'source_sha256': {
        name: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for name, path in paths.items()}, 'optional_modules_absent': absent,
        'versions': {d.metadata['Name']: d.version
                     for d in importlib.metadata.distributions()}}

    start_dps = mp.mp.dps
    tiny = g.lobachevsky_mp(Fraction(1, 10**400), dps=120)
    value = g.bloch_wigner_mp(('-1', '1e-300'), dps=120)
    triangle = g.triangle_volume_from_points_mp('0', '1', ('-1', '1e-300'), dps=120)
    with mp.workdps(450):
        x = mp.mpf('1e-400')
        tiny_ref = x*(1-mp.log(2*x))
        z = mp.mpc('-1', '1e-300')
        ref = mp.im(mp.polylog(2, z)) + mp.arg(1-z)*mp.log(abs(z))
        tiny_error = abs(tiny/tiny_ref-1)
        bw_error = abs(value/ref-1)
        triangle_error = abs(triangle/ref-1)
        assert tiny_error < mp.mpf('1e-115')
        assert bw_error < mp.mpf('1e-115')
        assert triangle_error < mp.mpf('1e-115')
        regular_ref = float(3*mp.clsin(2, 2*mp.pi/3)/2)
        huge = complex(1e308, 1e308)
        z = mp.mpc(huge.real, huge.imag)
        huge_ref = float(mp.im(mp.polylog(2, z))+mp.arg(1-z)*mp.log(abs(z)))
    huge_value = float(g.bloch_wigner(huge))
    assert np.isfinite(huge_value) and huge_value > 0
    assert abs(huge_value/huge_ref-1) < 2e-14
    assert mp.mp.dps == start_dps
    try:
        g.lobachevsky_mp(float('nan'), dps=73)
    except ValueError:
        pass
    else:
        raise AssertionError('NaN accepted')
    assert mp.mp.dps == start_dps
    report['precision'] = {'tiny_lobachevsky_nonzero': bool(tiny > 0),
        'tiny_lobachevsky_relative_error': str(tiny_error),
        'negative_axis_relative_error': str(bw_error),
        'triangle_relative_error': str(triangle_error),
        'huge_binary64': huge_value, 'huge_reference': huge_ref,
        'scoped_precision_restored': True}

    regular = rd.optimize_hyperbolic_volume([(0, 1, 2)])
    assert regular['success'] and regular['kkt']['passed']
    assert abs(regular['volume']-regular_ref) < 5e-15
    exhausted = rd.optimize_hyperbolic_volume(
        [(0, 1, 2)], [[.2, 1., np.pi-1.2]], max_iter=0)
    assert not exhausted['success'] and not exhausted['kkt']['passed']
    assert exhausted['termination_reason'] == 'max_iterations'
    faces = [(2, 4, 3), (2, 7, 1), (5, 2, 3), (2, 5, 7),
             (6, 5, 0), (5, 6, 7), (6, 0, 1), (7, 6, 1)]
    lp = rd.check_delaunay_realizability(faces, strict=True)
    assert lp['success'] and lp['realizable']
    assert lp['strict_objective'] == 'max_common_positive_margin'
    assert abs(lp['slack']-1/7) < 1e-12
    assert lp['primal_residuals']['passed']
    report['angle_solver'] = {'regular_volume': regular['volume'],
        'reference': regular_ref, 'regular_kkt': regular['kkt'],
        'regular_residuals': regular['residuals'],
        'strict_common_margin': lp['slack'], 'lp_residuals': lp['primal_residuals'],
        'nonstationary_exhaustion_unsuccessful': True}

    parameters = np.array([np.pi/2, np.pi/3])

    def corrupt_callback(trial):
        trial.params[:] = np.nan
        trial.validation.clear()

    fake = SimpleNamespace(x=parameters.copy(), fun=-100., success=False,
                           message='controlled endpoint contract probe', nit=1, nfev=7)
    with patch.object(opt, 'differential_evolution', return_value=fake):
        result = opt.optimize_ideal_polyhedron(
            4, n_trials=1, maxiter=1, popsize=1, trial_callback=corrupt_callback)
    assert abs(result.best_volume-regular_ref) < 2e-14
    assert result.trials[0].success is False
    assert result.trials[0].validation['status'] == 'verified'
    assert result.trials[0].verification_evals == 1
    np.testing.assert_array_equal(result.best_params, parameters)
    controlled = opt.optimization_result_to_dict(result, source='installed-wheel-controlled-probe')
    json.dumps(controlled, allow_nan=False)
    assert controlled['schema_version'] == 2
    args.output.with_name('integration-installed-controlled-v2.json').write_text(
        json.dumps(controlled, indent=2, allow_nan=False)+'\n')
    real = opt.optimize_ideal_polyhedron(4, n_trials=1, maxiter=1, popsize=4, seed=42)
    assert real.trials[0].success is False
    assert real.trials[0].validation['status'] == 'verified'
    assert abs(real.best_volume + opt.negative_volume_objective(real.best_params, 4)) < 1e-15
    report['optimization_service'] = {'controlled_cached_volume': 100.,
        'fresh_volume': result.best_volume, 'unconverged_candidate_valid': True,
        'callback_isolation': True, 'strict_json_v2': True,
        'real_scipy_volume': real.best_volume,
        'real_scipy_trial': real.trials[0].as_dict()}

    tetra = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]
    triangulation, _ = rh.triangulation_from_faces(tetra)
    underflow = rh.check_arithmeticity(
        tetra, shears={e: Fraction(1, 10**400) for e in triangulation.Ori})
    exact = rh.check_arithmeticity(
        tetra, shears={e: Fraction(0) for e in triangulation.Ori})
    assert not underflow['is_arithmetic_certified'] and exact['is_arithmetic_certified']
    points = np.array([[0., 0.], [1., 0.], [-.3, 1.2], [1., .8]])
    faces = [(1, 3, 0), (2, 0, 3)]
    angles = []
    for face in faces:
        row = []
        for i in range(3):
            a = points[face[(i+1) % 3]]-points[face[i]]
            b = points[face[(i+2) % 3]]-points[face[i]]
            row.append(np.arctan2(abs(a[0]*b[1]-a[1]*b[0]), a@b))
        angles.append(row)
    development = realize_from_angles_rigid(faces, angles)
    assert development['success'] and development['orientation_consistent']
    np.testing.assert_allclose(development['points'], points, atol=2e-14)
    assert rd.lobachevsky_hessian(np.pi-1e-11) > 0
    report['prior_core_regressions'] = {'underflow_not_exact_zero': True,
        'declared_exact_zero_certifies': True, 'cyclic_face_development': True,
        'near_pi_hessian_positive': True}
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'checks': 'passed', 'output': str(args.output)}))


if __name__ == '__main__':
    main()
