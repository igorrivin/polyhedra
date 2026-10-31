"""Regression cases found during the monograph/toolkit integration audit."""

from fractions import Fraction
import math

import numpy as np
import pytest

from ideal_poly_volume_toolkit.geometric_realization import realize_from_angles_rigid
from ideal_poly_volume_toolkit.rivin_delaunay import (
    lobachevsky_gradient,
    lobachevsky_hessian,
)
from ideal_poly_volume_toolkit.rivin_holonomy import (
    check_arithmeticity,
    triangulation_from_faces,
)


TETRAHEDRON = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]


@pytest.mark.parametrize("sign", [-1, 1])
def test_nonzero_rational_underflow_is_not_an_exact_zero_certificate(sign):
    triangulation, _ = triangulation_from_faces(TETRAHEDRON)
    declared = {edge: Fraction(sign, 10**400) for edge in triangulation.Ori}
    assert all(value != 0 and float(value) == 0 for value in declared.values())

    result = check_arithmeticity(TETRAHEDRON, shears=declared)

    assert result["passes_zero_shear_diagnostic"]  # float diagnostic only
    assert not result["has_exact_zero_shears"]
    assert not result["is_arithmetic"]
    assert not result["is_arithmetic_certified"]
    assert result["arithmeticity_status"] == "not_certified"


def test_declared_exact_rational_zero_still_certifies():
    triangulation, _ = triangulation_from_faces(TETRAHEDRON)
    declared = {edge: Fraction(0) for edge in triangulation.Ori}

    result = check_arithmeticity(TETRAHEDRON, shears=declared)

    assert result["has_exact_zero_shears"]
    assert result["is_arithmetic_certified"]
    assert result["arithmeticity_status"] == "certified_declared_exact_zero_shear"


def angles_from_points(points, faces):
    result = []
    for face in faces:
        row = []
        for k in range(3):
            a = points[face[(k + 1) % 3]] - points[face[k]]
            b = points[face[(k + 2) % 3]] - points[face[k]]
            row.append(math.atan2(abs(a[0] * b[1] - a[1] * b[0]), float(a @ b)))
        result.append(row)
    return np.asarray(result)


@pytest.mark.parametrize("rotations", [(0, 0), (0, 1), (1, 2), (2, 1)])
def test_rigid_realization_preserves_cyclic_face_orientation(rotations):
    points = np.array([[0., 0.], [1., 0.], [-.3, 1.2], [1., .8]])
    faces = [(0, 1, 3), (0, 3, 2)]
    rotated = [face[k:] + face[:k] for face, k in zip(faces, rotations)]

    result = realize_from_angles_rigid(rotated, angles_from_points(points, rotated))

    assert result["success"]
    np.testing.assert_allclose(result["points"], points, atol=2e-14)
    assert result["orientation_consistent"]
    assert result["max_angle_error"] < 1e-14
    assert result["evidence_status"] == "numerical_development"
    assert not result["embedding_checked"]


def test_rigid_realization_anchors_an_actual_edge_under_arbitrary_relabeling():
    points = np.array([[0., 0.], [1., 0.], [-.3, 1.2], [1., .8]])
    faces = [(0, 1, 3), (0, 3, 2)]
    labels = {0: 100, 1: -5, 2: -6, 3: 200}  # smallest two labels share no edge
    relabeled = [tuple(labels[v] for v in face) for face in faces]
    result = realize_from_angles_rigid(relabeled, angles_from_points(points, faces))

    assert result["success"]
    z = {label: complex(*point) for label, point in zip(result["vertex_list"], result["points"])}
    normalized = np.array([(z[labels[i]] - z[100]) / (z[-5] - z[100]) for i in range(4)])
    np.testing.assert_allclose(normalized, points[:, 0] + 1j * points[:, 1], atol=2e-14)


def test_rigid_realization_rejects_incompatible_cycle_after_placing_every_vertex():
    points = np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.], [.5, .5]])
    faces = [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)]
    angles = angles_from_points(points, faces)
    control = realize_from_angles_rigid(faces, angles)
    assert control["success"]
    angles[0, 0] += .1
    angles[0, 2] -= .1  # still strictly positive, with triangle sum pi

    result = realize_from_angles_rigid(faces, angles)

    assert result["points"].shape == (5, 2)
    assert not result["success"]
    assert result["relative_closure_error"] > result["residual_tolerance"]
    assert result["max_angle_error"] > result["residual_tolerance"]


def test_rigid_realization_reports_disconnected_faces():
    result = realize_from_angles_rigid([(0, 1, 2), (3, 4, 5)], np.full((2, 3), np.pi / 3))

    assert not result["success"]
    assert result["points"] is None
    assert "disconnected" in result["message"]


@pytest.mark.parametrize("bad_angles", [
    [[0., np.pi / 2, np.pi / 2]],
    [[np.nan, 1., 1.]],
    [[1., 1., 1.]],
    [[1., 2.]],
])
def test_rigid_realization_validates_angle_data(bad_angles):
    with pytest.raises(ValueError):
        realize_from_angles_rigid([(0, 1, 2)], bad_angles)


def test_rigid_realization_rejects_incoherent_face_winding():
    with pytest.raises(ValueError, match="coherent"):
        realize_from_angles_rigid([(0, 1, 2), (0, 1, 3)], np.full((2, 3), np.pi / 3))


@pytest.mark.parametrize("theta", [1e-11, 0.3, math.pi / 2, math.pi - 1e-11])
def test_lobachevsky_derivatives_match_independent_high_precision_formula(theta):
    import mpmath as mp

    with mp.workdps(60):
        t = mp.mpf(theta)
        expected_gradient = float(-mp.log(2 * mp.sin(t)))
        expected_hessian = float(-mp.cos(t) / mp.sin(t))
    assert lobachevsky_gradient(theta) == pytest.approx(expected_gradient, rel=1e-14, abs=1e-15)
    assert lobachevsky_hessian(theta) == pytest.approx(expected_hessian, rel=1e-14, abs=1e-15)


@pytest.mark.parametrize("theta", [0., math.pi, -1., 4., math.inf, math.nan])
def test_lobachevsky_derivatives_reject_values_outside_the_open_domain(theta):
    for derivative in (lobachevsky_gradient, lobachevsky_hessian):
        with pytest.raises(ValueError, match="strictly"):
            derivative(theta)
