"""Independent small mathematical oracles for Section 9's coordinate contract."""

from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import mpmath as mp
import numpy as np
import pytest

from ideal_poly_volume_toolkit import variational as var

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT = ROOT / "experiments/section9"
FIXTURE = json.loads((EXPERIMENT / "fixture.json").read_text())
POINTS = np.array(FIXTURE["points"])
FACES = np.array(FIXTURE["triangles"])
INTERIOR = FIXTURE["interior_vertices"]
BOUNDARY = FIXTURE["boundary_vertices"]


def experiment_module():
    spec = importlib.util.spec_from_file_location("section9_fixture_oracle", EXPERIMENT / "run.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_integer_mesh_fem_and_volume_hessian():
    base = var.corner_angles(POINTS, FACES)
    incidence = var.leading_trailing_matrix(FACES, INTERIOR)
    gradient, hessian = var.angle_volume_derivatives(base, incidence, [0, 0])
    fem = var.fem_stiffness(POINTS, FACES)
    cot = var.cotangent_stiffness(len(POINTS), FACES, base)
    expected = np.array([[4., -1.], [-1., 4.]])
    np.testing.assert_allclose(fem[np.ix_(INTERIOR, INTERIOR)], expected, atol=1e-14, rtol=0)
    np.testing.assert_allclose(cot, fem, atol=1e-14, rtol=0)
    np.testing.assert_allclose(-hessian, 2*expected, atol=1e-14, rtol=0)
    np.testing.assert_allclose(gradient, 0, atol=1e-14, rtol=0)
    assert var.angle_volume(base, incidence, [0, 0]) == pytest.approx(float(12*mp.catalan), abs=1e-12)


def test_off_origin_hessian_against_high_precision_volume_derivative():
    base = var.corner_angles(POINTS, FACES)
    incidence = var.leading_trailing_matrix(FACES, INTERIOR)
    u = FIXTURE["off_origin_parameters"]
    alpha = var.deformed_angles(base, incidence, u)
    # Preserve both kinds of affine constraints, without asserting realization.
    np.testing.assert_allclose(alpha.sum(axis=1), np.pi, atol=1e-14, rtol=0)
    sums = [{}, {}]
    for values, total in zip((base, alpha), sums):
        for face, angles in zip(FACES, values):
            for k in range(3):
                edge = tuple(sorted((face[(k+1) % 3], face[(k+2) % 3])))
                total[edge] = total.get(edge, 0.) + angles[k]
    for edge in sums[0]:
        assert sums[0][edge] == pytest.approx(sums[1][edge], abs=1e-14)
    _, hessian = var.angle_volume_derivatives(base, incidence, u)
    previous_precision = mp.mp.dps
    oracle = experiment_module().high_precision_hessian(POINTS, FACES, incidence, u)
    assert mp.mp.dps == previous_precision
    np.testing.assert_allclose(hessian, oracle, atol=1e-11, rtol=0)


def test_exact_rational_matrix_tree_and_schur_identities():
    experiment = experiment_module()
    matrix = experiment.rational_fem(FIXTURE["points"], FIXTURE["triangles"])
    grounded = [[matrix[i][j] for j in INTERIOR] for i in INTERIOR]
    assert grounded == [[Fraction(4), Fraction(-1)], [Fraction(-1), Fraction(4)]]
    assert experiment.rooted_forest_sum(matrix, BOUNDARY) == (Fraction(15), 15)
    effective = var.schur_complement(2*np.array(grounded, dtype=float), [0])
    np.testing.assert_allclose(effective, [[7.5]], atol=0, rtol=0)
    assert 8*effective[0, 0] == 60


def test_dirichlet_response_against_linear_harmonic_function():
    matrix = var.fem_stiffness(POINTS, FACES)
    response = var.schur_complement(matrix, INTERIOR)
    boundary_voltage = POINTS[BOUNDARY, 0] / 3
    grounded = matrix[np.ix_(INTERIOR, INTERIOR)]
    voltage = -np.linalg.solve(grounded, matrix[np.ix_(INTERIOR, BOUNDARY)] @ boundary_voltage)
    np.testing.assert_allclose(voltage, [1/3, 2/3], atol=1e-14, rtol=0)
    np.testing.assert_allclose(response @ np.ones(len(BOUNDARY)), 0, atol=1e-14, rtol=0)
    np.testing.assert_allclose(response, response.T, atol=1e-14, rtol=0)
    for scale in (-2., 0., 1.5):
        v = scale*boundary_voltage
        assert v @ response @ v == pytest.approx(2*scale**2/3, abs=1e-13)
    assert np.linalg.eigvalsh(response).min() >= -1e-14


def test_cyclic_face_order_and_vertex_relabeling_preserve_fem():
    rotated = np.roll(FACES, 1, axis=1)
    np.testing.assert_allclose(var.fem_stiffness(POINTS, rotated), var.fem_stiffness(POINTS, FACES))
    incidence = var.leading_trailing_matrix(rotated, INTERIOR)
    _, hessian = var.angle_volume_derivatives(var.corner_angles(POINTS, rotated), incidence, [0, 0])
    np.testing.assert_allclose(-hessian, [[8, -2], [-2, 8]], atol=1e-14, rtol=0)
    permutation = np.array([5, 3, 9, 0, 11, 1, 7, 2, 10, 6, 4, 8])
    new_points = np.empty_like(POINTS)
    new_points[permutation] = POINTS
    relabeled = var.fem_stiffness(new_points, permutation[FACES])
    np.testing.assert_allclose(relabeled[np.ix_(permutation, permutation)], var.fem_stiffness(POINTS, FACES))


def test_zero_dimensional_single_triangle_is_supported():
    faces = np.array([[0, 1, 2]])
    points = np.array([[0., 0.], [1., 0.], [0., 1.]])
    base = var.corner_angles(points, faces)
    incidence = var.leading_trailing_matrix(faces, [])
    gradient, hessian = var.angle_volume_derivatives(base, incidence, [])
    assert incidence.shape == (3, 0)
    assert gradient.shape == (0,)
    assert hessian.shape == (0, 0)
    assert var.angle_volume(base, incidence, []) == pytest.approx(float(mp.catalan), abs=1e-13)
    matrix = var.fem_stiffness(points, faces)
    np.testing.assert_array_equal(var.schur_complement(matrix, []), matrix)


def test_bad_domains_and_singular_elimination_are_explicit_failures():
    base = var.corner_angles(POINTS, FACES)
    incidence = var.leading_trailing_matrix(FACES, INTERIOR)
    with pytest.raises(ValueError, match="strictly between"):
        var.deformed_angles(base, incidence, [10, 0])
    with pytest.raises(ValueError, match="finite"):
        var.deformed_angles(base, incidence, [float('nan'), 0])
    with pytest.raises(ValueError, match="nonboundary"):
        var.leading_trailing_matrix(FACES, [0, 5, 6])
    with pytest.raises(ValueError, match="counterclockwise"):
        var.corner_angles(POINTS, FACES[:, ::-1])
    with pytest.raises(ValueError, match="distinct"):
        var.schur_complement(np.eye(3), [1, 1])
    with pytest.raises(np.linalg.LinAlgError):
        var.schur_complement(np.zeros((2, 2)), [0])


def test_unsigned_label_overflow_cannot_alias_the_last_vertex():
    oversized = np.array([[0, 1, 2**64-1]], dtype=np.uint64)
    with pytest.raises(ValueError, match="representable"):
        var.corner_angles([[0, 0], [1, 0], [0, 1]], oversized)
    with pytest.raises(ValueError, match="representable"):
        var.leading_trailing_matrix(FACES, np.array([5, 2**64-1], dtype=np.uint64))
    with pytest.raises(ValueError, match="representable"):
        var.schur_complement(np.eye(2), np.array([2**64-1], dtype=np.uint64))


def test_external_fixture_and_installed_module_provenance(tmp_path, monkeypatch):
    experiment = experiment_module()
    external_fixture = tmp_path / "external-fixture.json"
    shutil.copyfile(EXPERIMENT / "fixture.json", external_fixture)
    external_package = tmp_path / "site-packages/ideal_poly_volume_toolkit"
    external_package.mkdir(parents=True)
    for name in ("variational.py", "geometry.py"):
        shutil.copyfile(Path(var.__file__).with_name(name), external_package / name)
    monkeypatch.setattr(experiment, "var", SimpleNamespace(__file__=str(external_package / "variational.py")))
    report = experiment.source_provenance(external_fixture)
    records = {row['role']: row for row in report['source_files']}
    for role, path in [('experiment.fixture', external_fixture),
                       ('toolkit.variational', external_package / 'variational.py'),
                       ('toolkit.geometry', external_package / 'geometry.py')]:
        assert records[role]['location_kind'] == 'external'
        assert records[role]['sha256'] == sha256(path.read_bytes()).hexdigest()
        assert report['source_sha256'][role] == records[role]['sha256']
    (external_package / 'geometry.py').unlink()
    with pytest.raises(FileNotFoundError, match="toolkit.geometry"):
        experiment.source_provenance(external_fixture)


def test_detached_bundle_runs_outside_checkout_without_book(tmp_path):
    experiment = experiment_module()
    origin = experiment.source_provenance(EXPERIMENT / 'fixture.json')
    archive_path = tmp_path / 'reproduction.zip'
    experiment.create_reproduction_bundle({'provenance': origin}, EXPERIMENT / 'fixture.json', archive_path)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(tmp_path / 'extracted')
    bundle = tmp_path / 'extracted/section9-reproduction'
    arbitrary_cwd = tmp_path / 'elsewhere'
    arbitrary_cwd.mkdir()
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env.pop('PYTHONPATH', None)
    completed = subprocess.run([sys.executable, str(bundle / 'experiments/section9/run.py')],
                               cwd=arbitrary_cwd, env=env, text=True, capture_output=True, timeout=60)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    report = json.loads((bundle / 'artifacts/section9/result.json').read_text())
    assert report['all_checks_passed']
    provenance = report['provenance']
    assert provenance['execution_context'] == 'detached-bundle'
    assert provenance['source_commit'] is None
    assert provenance['repository_dirty_at_start'] is None
    assert provenance['bundle_payload_hashes_match'] is True
    records = {row['role']: row for row in provenance['source_files']}
    assert records['toolkit.variational']['path'] == 'packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py'
    assert records['book.tex']['available'] is False
    assert records['book.reference_pdf']['available'] is False
    assert (bundle / 'LICENSES/volume-toolkit-MIT.txt').is_file()
    requirements = (bundle / 'requirements.txt').read_text().splitlines()
    assert {line.split('==')[0] for line in requirements} == {'numpy', 'scipy', 'mpmath'}
    page = (bundle / 'site/section9/index.html').read_text()
    assert 'Monograph source and PDF are not included' in page
    assert 'href="downloads/polyhedral_volumes_and_geodesic_identities.pdf"' not in page


def test_external_fixture_contract_rejects_a_changed_experiment(tmp_path):
    experiment = experiment_module()
    changed = dict(FIXTURE)
    changed['off_origin_parameters'] = [0.01, 0.02]
    path = tmp_path / 'changed.json'
    path.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="not a general mesh experiment"):
        experiment.build_report(path)
