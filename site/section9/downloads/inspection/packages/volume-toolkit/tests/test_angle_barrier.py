"""Independent reference checks and failure contracts for the dense barrier path."""

import json
import math

import mpmath as mp
import numpy as np
import pytest

from ideal_poly_volume_toolkit import angle_barrier as barrier
from ideal_poly_volume_toolkit import variational


def triangle():
    return np.array([[np.pi / 6, np.pi / 3, np.pi / 2]]), np.array([[1., 0.], [0., 1.], [-1., -1.]])


def asymmetric_disk():
    points = np.array([[0., 0.], [4., 0.], [4., 3.], [0., 3.], [1., .5]])
    faces = np.array([[4, 0, 1], [4, 1, 2], [4, 2, 3], [4, 3, 0]])
    return variational.corner_angles(points, faces), variational.leading_trailing_matrix(faces, [4])


def test_log_sine_derivatives_against_independent_multiprecision_diff():
    base = np.array([[np.pi / 5, np.pi / 3, np.pi - np.pi / 5 - np.pi / 3],
                     [np.pi / 4, np.pi / 6, np.pi - np.pi / 4 - np.pi / 6]])
    matrix = np.array([[1., 0.], [0., 1.], [-1., -1.], [0., 2.], [1., 0.], [-1., -2.]])
    u = [.01, -.02]
    value, gradient, hessian = barrier.log_sine_barrier(base, matrix, u)
    old_precision = mp.mp.dps
    with mp.workdps(70):
        angles = list(map(mp.mpf, base.ravel()))
        rows = [list(map(mp.mpf, row)) for row in matrix]

        def oracle(*parameters):
            return -mp.fsum(mp.log(mp.sin(a + mp.fsum(c * x for c, x in zip(row, parameters))))
                            for a, row in zip(angles, rows))

        point = tuple(map(mp.mpf, u))
        expected_value = float(oracle(*point))
        expected_gradient = [float(mp.diff(oracle, point, (1, 0))), float(mp.diff(oracle, point, (0, 1)))]
        expected_hessian = [[float(mp.diff(oracle, point, (2, 0))), float(mp.diff(oracle, point, (1, 1)))],
                            [float(mp.diff(oracle, point, (1, 1))), float(mp.diff(oracle, point, (0, 2)))]]
    assert mp.mp.dps == old_precision
    assert value == pytest.approx(expected_value, abs=2e-14)
    np.testing.assert_allclose(gradient, expected_gradient, rtol=0, atol=2e-13)
    np.testing.assert_allclose(hessian, expected_hessian, rtol=0, atol=2e-12)


def test_full_triangle_tangent_reaches_known_regular_maximum():
    base, matrix = triangle()
    result = barrier.solve_angle_barrier(base, matrix, [-.2, .1])
    with mp.workdps(70):
        regular_volume = float(3 * mp.clsin(2, 2 * mp.pi / 3) / 2)
    assert result.converged and result.status == "converged"
    assert result.centering_steps > 0 and result.path_steps > 0
    assert result.centered and result.target_reached and result.finite_gap_available
    assert result.newton_decrement <= .25
    assert result.t >= result.target_t
    assert result.conservative_gap_bound_estimate <= result.epsilon * (1 + 1e-15)
    assert result.volume == pytest.approx(regular_volume, abs=2e-13)
    np.testing.assert_allclose(result.angles, np.full((1, 3), np.pi / 3), rtol=0, atol=2e-13)
    assert result.certified is False
    assert json.loads(json.dumps(result.to_dict(), allow_nan=False))["converged"] is True


def test_asymmetric_disk_has_nontrivial_center_and_preserves_path_contract():
    base, matrix = asymmetric_disk()
    result = barrier.solve_angle_barrier(base, matrix, [-.1], epsilon=1e-4)
    assert result.converged
    # This independent 80-digit Clausen value uses exact rational coordinates;
    # binary64 angles are a nearby, explicitly numerical problem.
    reference = 3.0062866417470506525050027983572778475653682538807
    assert abs(result.volume - reference) <= result.gap_bound_estimate + 1e-12
    centered_start = [row for row in result.history if row.phase == "centering"][-1]
    # Centering is a decrement neighborhood, not the exact Phi_1 minimizer.
    assert centered_start.newton_decrement <= .25
    assert centered_start.parameters[0] > -.01
    assert max(row.parameters[0] for row in result.history if row.phase == "path") > .02
    assert 0 < result.parameters[0] < 2e-6
    assert result.centering_steps > 0
    multiplier = 1 + 1 / (20 * math.sqrt(base.size))
    previous = None
    for row in result.history:
        angles = (base.ravel() + matrix @ np.asarray(row.parameters)).reshape(base.shape)
        assert np.all(angles > 0) and np.all(angles < np.pi)
        np.testing.assert_allclose(angles.sum(axis=1), np.pi, rtol=0, atol=2e-14)
        if row.phase == "path":
            assert row.decrement_before_step <= 5 / 16
            assert row.newton_decrement <= .25
            assert row.t > previous.t
            assert 1 < row.parameter_multiplier <= multiplier * (1 + 1e-15)
            assert row.step_size == 1
            assert row.relative_linear_residual <= 1e-8
        previous = row
    assert result.base_triangle_sum_residual < 2e-14
    assert result.tangent_sum_relative_residual == 0
    assert result.triangle_sum_residual < 2e-14


def test_closed_boundary_maximum_stops_at_a_strictly_positive_point():
    base = np.array([[np.pi - .1, .05, .05], [.05, 1.05, np.pi - 1.1]])
    matrix = np.array([[-2.], [1.], [1.], [-1.], [1.], [0.]])
    result = barrier.solve_angle_barrier(base, matrix, epsilon=1e-4)
    assert result.converged and result.minimum_angle > 0
    # In s=u+.05, the feasible interval is (0,.1). Strict concavity and
    # V'(0+)=-.745354208... put the closed maximum at s=0. The independent
    # reference is the remaining nonflat triangle's Clausen volume.
    with mp.workdps(70):
        angles = [mp.mpf('.1'), mp.mpf('1'), mp.pi - mp.mpf('1.1')]
        reference = float(mp.fsum(mp.clsin(2, 2 * a) / 2 for a in angles))
    gap = reference - result.volume
    assert 0 < gap < result.gap_bound_estimate
    assert 0 < result.parameters[0] + .05 < 1e-4
    assert result.newton_decrement <= .25


def test_fixed_domain_has_no_path_or_fake_precision_requirement():
    base, _ = triangle()
    result = barrier.solve_angle_barrier(base, np.empty((3, 0)), epsilon=1e-310)
    assert result.status == "fixed_domain" and result.converged
    assert result.parameters == ()
    assert result.path_steps == result.centering_steps == 0
    assert result.t == result.target_t == 1
    assert result.gap_bound_estimate == result.conservative_gap_bound_estimate == 0
    assert result.certified is False


@pytest.mark.parametrize("t0", [1e-310, np.nextafter(0., 1.)])
def test_fixed_domain_zero_gap_is_available_even_when_generic_bound_overflows(t0):
    result = barrier.solve_angle_barrier(np.full((1, 3), np.pi / 3),
                                         np.empty((3, 0)), t0=t0, epsilon=1e-310)
    assert result.status == "fixed_domain" and result.converged
    assert result.finite_gap_available
    assert result.gap_bound_estimate == result.conservative_gap_bound_estimate == 0
    assert result.t == result.target_t == t0
    assert result.centered and result.target_reached
    json.dumps(result.to_dict(), allow_nan=False)


def test_target_rounding_does_not_report_a_bound_above_requested_epsilon():
    epsilon = .00011
    rounded_target = (17 / 12) * 3 / epsilon
    assert (17 / 12) * 3 / rounded_target > epsilon
    _, matrix = triangle()
    result = barrier.solve_angle_barrier(np.full((1, 3), np.pi / 3), matrix,
                                         epsilon=epsilon, t0=rounded_target)
    assert result.converged
    assert result.conservative_gap_bound_estimate <= epsilon
    assert result.target_t > rounded_target


@pytest.mark.parametrize("option,value", [
    ("epsilon", 0), ("epsilon", float("nan")), ("epsilon", True),
    ("t0", float("inf")), ("t0", -1),
    ("condition_limit", .5), ("condition_limit", 1e30),
    ("linear_residual_tolerance", 0), ("linear_residual_tolerance", .1),
    ("max_centering_steps", -1), ("max_centering_steps", True),
    ("max_path_steps", 1.5), ("max_backtracks", 0),
])
def test_invalid_controls_are_rejected(option, value):
    base, matrix = triangle()
    with pytest.raises(ValueError):
        barrier.solve_angle_barrier(base, matrix, **{option: value})


@pytest.mark.parametrize("matrix", [
    np.array([[1.], [0.], [0.]]),
    np.array([[1e-100], [0.], [0.]]),
    np.array([[1., 1.], [0., 0.], [-1., -1.]]),
    np.array([[1.], [float("nan")], [-1.]]),
    np.array([[1j], [0], [-1j]]),
])
def test_bad_affine_spaces_are_not_normalized_or_pseudoinverted(matrix):
    base, _ = triangle()
    with pytest.raises(ValueError):
        barrier.solve_angle_barrier(base, matrix)


def test_bad_initial_angles_and_unrepresentable_target_are_rejected():
    base, matrix = triangle()
    with pytest.raises(ValueError, match="strictly feasible"):
        barrier.solve_angle_barrier(base, matrix, [-1., 0])
    with pytest.raises(ValueError, match="sum to pi"):
        barrier.solve_angle_barrier(base + 1e-12, matrix)
    with pytest.raises(ValueError, match="outside binary64"):
        barrier.solve_angle_barrier(base, matrix, epsilon=1e-320)


def test_budget_limits_retain_last_valid_iterate_without_convergence():
    base, matrix = triangle()
    initial = [-.2, .1]
    centering = barrier.solve_angle_barrier(base, matrix, initial, max_centering_steps=0)
    assert centering.status == "centering_limit" and not centering.converged
    assert centering.parameters == tuple(initial)
    assert centering.centering_steps == 0 and not centering.centered
    path = barrier.solve_angle_barrier(base, matrix, initial, max_path_steps=2)
    assert path.status == "path_limit" and not path.converged
    assert path.centered and path.finite_gap_available and not path.target_reached
    assert path.path_steps == 2
    assert path.parameters == path.history[-1].parameters
    assert path.volume == pytest.approx(variational.angle_volume(base, matrix, path.parameters))


def test_ill_conditioned_slice_returns_explicit_failure():
    base, matrix = triangle()
    matrix[:, 1] *= 1e-4
    result = barrier.solve_angle_barrier(base, matrix, condition_limit=1e4)
    assert result.status == "ill_conditioned" and not result.converged
    assert result.parameters == (0., 0.)
    assert result.newton_decrement is None and not result.finite_gap_available
    assert result.failure_phase == "initial"
    json.dumps(result.to_dict(), allow_nan=False)


def test_bad_linear_solve_cannot_be_reported_as_convergence(monkeypatch):
    base, matrix = triangle()
    original = np.linalg.solve

    def corrupted(a, b):
        return original(a, b) + .1

    monkeypatch.setattr(np.linalg, "solve", corrupted)
    result = barrier.solve_angle_barrier(base, matrix)
    assert result.status == "linear_solve_failure" and not result.converged
    assert result.parameters == (0., 0.)
    assert result.history == ()


def test_final_endpoint_is_recomputed_and_nonfinite_volume_fails(monkeypatch):
    base = np.full((1, 3), np.pi / 3)
    _, matrix = triangle()
    original = variational.angle_volume
    calls = 0

    def fails_after_initial(*args):
        nonlocal calls
        calls += 1
        return original(*args) if calls == 1 else float("nan")

    monkeypatch.setattr(variational, "angle_volume", fails_after_initial)
    result = barrier.solve_angle_barrier(base, matrix, epsilon=100)
    assert calls == 2
    assert result.status == "numerical_failure" and not result.converged
    assert result.failure_phase == "final"
    assert result.centered and result.target_reached
    assert math.isfinite(result.volume)


def test_inputs_and_result_snapshots_do_not_alias():
    base, matrix = triangle()
    old_base, old_matrix = base.copy(), matrix.copy()
    result = barrier.solve_angle_barrier(base, matrix, epsilon=.1)
    np.testing.assert_array_equal(base, old_base)
    np.testing.assert_array_equal(matrix, old_matrix)
    captured = result.angles
    base[:] = 0
    matrix[:] = 0
    payload = result.to_dict()
    payload["volume"] = -123
    assert result.angles == captured
    assert result.volume > 0
