"""Numerical acceptance and independent references for Rivin angle solves."""

from types import SimpleNamespace
from fractions import Fraction

import mpmath as mp
import numpy as np
import pytest
from scipy.linalg import null_space
from scipy.optimize import minimize

from ideal_poly_volume_toolkit import rivin_delaunay as rd


FACES = [(2, 4, 3), (2, 7, 1), (5, 2, 3), (2, 5, 7),
         (6, 5, 0), (5, 6, 7), (6, 0, 1), (7, 6, 1)]
START = np.pi*np.array([[.2, .6, .2], [.2, .6, .2], [.4, .4, .2],
                        [.2, .2, .6], [.6, .2, .2], [.2, .6, .2],
                        [.6, .2, .2], [.6, .2, .2]])


def independent_volume(angles):
    with mp.workdps(35):
        return float(mp.fsum(mp.clsin(2, 2*mp.mpf(float(a)))/2
                            for a in np.asarray(angles).ravel()))


def test_regular_triangle_uses_accurate_final_volume():
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)])
    with mp.workdps(60):
        reference = float(3*mp.clsin(2, 2*mp.pi/3)/2)
    assert result["success"] and result["kkt"]["passed"]
    assert result["volume_method"] == "bloch_wigner_binary64"
    assert result["volume"] == pytest.approx(reference, abs=5e-15)
    # The former 64-term value was 1.0151497106006686 (error about 2.08e-4).
    assert abs(result["volume"]-1.0151497106006686) > 2e-4


@pytest.mark.parametrize("angle", [1e-12, np.pi/6, np.pi/3, np.pi/2,
                                   3*np.pi/4, np.pi-1e-12])
def test_lobachevsky_value_matches_independent_high_precision(angle):
    with mp.workdps(60):
        reference = float(mp.clsin(2, 2*mp.mpf(angle))/2)
    assert rd.lobachevsky_function(angle) == pytest.approx(reference, abs=3e-15)


def test_lobachevsky_value_endpoints_and_invalid_domain():
    assert rd.lobachevsky_function(0) == 0
    assert rd.lobachevsky_function(np.pi) == 0
    for angle in [-1e-12, np.pi+1e-12, np.nan, np.inf]:
        with pytest.raises(ValueError):
            rd.lobachevsky_function(angle)


@pytest.mark.parametrize("faces, expected", [([(0, 1, 2)], 1),
                                            ([(0, 1, 2), (0, 2, 3)], 2)])
def test_boundary_only_meshes_have_independent_regular_reference(faces, expected):
    result = rd.optimize_hyperbolic_volume(faces)
    assert result["success"] and result["residuals"]["feasible"]
    np.testing.assert_allclose(result["angles"], np.pi/3, atol=1e-12)
    assert result["volume"] == pytest.approx(expected*independent_volume([np.pi/3]*3), abs=1e-14)


@pytest.mark.parametrize("initial", [[1e-12, np.pi/2, np.pi/2-1e-12],
                                    [1e-12, 1e-12, np.pi-2e-12],
                                    [np.nextafter(0., 1.), np.pi/2, np.pi/2]])
def test_near_flat_positive_start_is_not_clipped(initial):
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], np.array([initial]))
    assert result["success"]
    assert result["residuals"]["max_equality_residual"] < 2e-14
    np.testing.assert_allclose(result["angles"], np.pi/3, atol=2e-12)


@pytest.mark.parametrize("initial, reason", [
    ([[0., np.pi/2, np.pi/2]], "nonpositive_or_flat_initial_angles"),
    ([[-1., 1., np.pi]], "nonpositive_or_flat_initial_angles"),
    ([[1., 1., 1.]], "infeasible_initial_angles"),
])
def test_bad_start_reports_failure_without_silent_repair(initial, reason):
    initial = np.asarray(initial)
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], initial)
    assert not result["success"]
    assert result["termination_reason"] == reason
    assert result["volume"] is None
    np.testing.assert_array_equal(result["angles"], initial)


def test_exhausted_budget_keeps_nonstationary_result_unsuccessful():
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], [[.2, 1., np.pi-1.2]], max_iter=0)
    assert not result["success"]
    assert result["n_iterations"] == 0
    assert result["termination_reason"] == "max_iterations"
    assert not result["kkt"]["passed"]
    assert result["kkt"]["stationarity_residual"] > .1


def test_zero_dimensional_and_zero_budget_newton_preserve_input():
    x = np.array([1e-12, 1e-12, np.pi-2e-12])
    result, iterations, converged, norm = rd._newton_in_nullspace(x, np.zeros((3, 0)), max_iter=0)
    np.testing.assert_array_equal(result, x)
    assert iterations == 0 and converged and norm == 0


def test_kkt_rejects_false_stationarity_in_zero_dimensional_infeasible_problem():
    x = np.full(3, np.pi/3)
    _, result = rd._solve_angle_polytope(
        x, np.eye(3), x, np.array([[1., 0., 0.]]), np.array([.1]),
        max_iter=5, max_active_rounds=5, tolerance=1e-10,
    )
    assert not result["success"]
    assert result["kkt"]["stationarity_residual"] < 1e-14
    assert result["kkt"]["inequality_violation"] > .9


def test_active_set_releases_negative_multiplier_and_recovers_known_maximum():
    x = np.array([.2, (np.pi-.2)/2, (np.pi-.2)/2])
    args = (np.ones((1, 3)), np.array([np.pi]), np.array([[-1., 0., 0.]]), np.array([-.2]))
    optimal, result = rd._solve_angle_polytope(
        x, *args, max_iter=50, max_active_rounds=10, tolerance=1e-10,
    )
    assert result["success"]
    np.testing.assert_allclose(optimal, np.pi/3, atol=2e-12)
    releases = [row for row in result["active_set_history"] if row["action"] == "release"]
    assert releases[0]["multiplier"] < -1.0
    assert result["kkt"]["inequality_multipliers"] == [0.0]
    _, exhausted = rd._solve_angle_polytope(
        x, *args, max_iter=50, max_active_rounds=0, tolerance=1e-10,
    )
    assert not exhausted["success"]
    assert exhausted["termination_reason"] == "max_active_set_changes"


def test_redundant_rows_preserve_all_constraints_and_nonnegative_dual_solution():
    # Symmetry and strict concavity give theta0=pi/6, theta1=theta2=5pi/12.
    A = np.array([[1., 1., 1.], [2., 2., 2.]])
    b = np.array([np.pi, 2*np.pi])
    B = np.array([[1., 0., 0.], [2., 0., 0.]])
    d = np.array([np.pi/6, np.pi/3])
    x = np.array([np.pi/6, 1., 5*np.pi/6-1.])
    optimal, result = rd._solve_angle_polytope(
        x, A, b, B, d, max_iter=50, max_active_rounds=10, tolerance=1e-10,
    )
    assert result["success"] and result["kkt"]["numerical_equality_rank"] == 1
    np.testing.assert_allclose(optimal, [np.pi/6, 5*np.pi/12, 5*np.pi/12], atol=2e-12)
    assert len(result["kkt"]["equality_multipliers"]) == 2
    assert len(result["kkt"]["inequality_multipliers"]) == 2
    assert min(result["kkt"]["inequality_multipliers"]) >= 0
    assert rd._angle_structure_volume(optimal) == pytest.approx(independent_volume(optimal), abs=2e-14)


def test_temporary_dihedral_constraint_does_not_force_final_tie_rejection():
    result = rd.optimize_hyperbolic_volume(FACES, START, require_interior=True)
    assert result["success"] and result["kkt"]["passed"]
    assert not result["rejected_tie"]
    assert result["residuals"]["min_dihedral_margin"] > 1e-3
    released = [result["constraint_labels"][row["constraint_index"]]
                for row in result["active_set_history"] if row["action"] == "release"]
    assert any(label.startswith("dihedral") for label in released)


def test_strict_lp_finds_positive_common_margin_with_exact_rational_witness():
    # The old 1000*epsilon+t objective returned t=0, epsilon=1/3 and declared
    # this complex non-realizable. These supplied rational angles certify a
    # positive witness with common normalized margin 1/7, independently of LP.
    numerator = [[1, 3, 3], [1, 5, 1], [1, 3, 3], [1, 3, 3],
                 [3, 1, 3], [1, 5, 1], [5, 1, 1], [5, 1, 1]]
    witness = [[Fraction(a, 7) for a in row] for row in numerator]
    assert all(sum(row) == 1 and min(row) >= Fraction(1, 7) for row in witness)
    incidence, opposites = {}, {}
    for t, face in enumerate(FACES):
        for k, vertex in enumerate(face):
            incidence.setdefault(vertex, []).append(witness[t][k])
            edge = tuple(sorted(face[j] for j in range(3) if j != k))
            opposites.setdefault(edge, []).append(witness[t][k])
    boundary = {v for edge, values in opposites.items() if len(values) == 1 for v in edge}
    assert all(sum(values) <= Fraction(6, 7)
               for values in opposites.values() if len(values) == 2)
    assert all(sum(values) <= Fraction(6, 7) if vertex in boundary else sum(values) == 2
               for vertex, values in incidence.items())
    result = rd.check_delaunay_realizability(FACES, strict=True)
    assert result["success"] and result["realizable"]
    assert result["strict_objective"] == "max_common_positive_margin"
    assert result["feasibility_status"] == "positive_witness_found"
    assert result["slack"] == pytest.approx(1/7)
    assert result["min_angle"] >= result["slack"]-1e-12
    assert result["measured_min_dihedral_margin"] >= result["slack"]-1e-12
    assert result["measured_min_boundary_margin"] >= result["slack"]-1e-12


def test_final_solution_matches_independent_slsqp_and_clausen_reference():
    faces = np.asarray(FACES)
    # Construct the constraints independently from incidence counts.
    edge_opposites = {}
    for row, face in enumerate(faces):
        for corner in range(3):
            edge = tuple(sorted(np.delete(face, corner)))
            edge_opposites.setdefault(edge, []).append((row, corner))
    boundary = set(v for edge, uses in edge_opposites.items() if len(uses) == 1 for v in edge)
    interior = sorted(set(faces.ravel())-boundary)

    def equations(x):
        angles = x.reshape(-1, 3)
        return np.r_[angles.sum(axis=1)-np.pi,
                     [angles[faces == v].sum()-2*np.pi for v in interior]]

    def margins(x):
        angles = x.reshape(-1, 3)
        return np.array([np.pi-sum(angles[t, c] for t, c in uses)
                         for uses in edge_opposites.values() if len(uses) == 2]
                        + [np.pi-angles[faces == v].sum() for v in sorted(boundary)])

    # SLSQP uses a distinct optimizer and the mpmath Clausen evaluator.
    # https://docs.scipy.org/doc/scipy/tutorial/optimize.html#slsqp
    reference = minimize(
        lambda x: -independent_volume(x), START.ravel(),
        jac=lambda x: np.log(2*np.sin(x)), method="SLSQP",
        bounds=[(1e-8, np.pi-1e-8)]*START.size,
        constraints=[{"type": "eq", "fun": equations},
                     {"type": "ineq", "fun": margins}],
        options={"ftol": 1e-12, "maxiter": 100},
    )
    result = rd.optimize_hyperbolic_volume(FACES, START)
    assert reference.success and result["success"]
    assert np.max(np.abs(equations(reference.x))) < 1e-8
    assert np.min(margins(reference.x)) > -1e-8
    assert result["volume"] == pytest.approx(-reference.fun, abs=2e-10)
    np.testing.assert_allclose(result["angles"].ravel(), reference.x, atol=2e-6)


@pytest.mark.parametrize("candidate", [None, np.array([.2, .2, .2, .2]),
                                       np.array([np.nan, .3, .3, .3])])
def test_lp_status_flag_cannot_override_missing_or_infeasible_primal(monkeypatch, candidate):
    monkeypatch.setattr(rd, "linprog", lambda *args, **kwargs: SimpleNamespace(
        success=True, status=0, message="synthetic successful status", x=candidate
    ))
    result = rd.check_delaunay_realizability([(0, 1, 2)])
    assert result["solver_success"]
    assert not result["success"] and not result["realizable"]
    assert not result["primal_residuals"]["passed"]
    assert result["angles"] is None
    assert not rd.optimize_hyperbolic_volume([(0, 1, 2)])["success"]


def test_lp_failure_never_dereferences_absent_solution(monkeypatch):
    monkeypatch.setattr(rd, "linprog", lambda *args, **kwargs: SimpleNamespace(
        success=False, status=2, message="infeasible", x=None
    ))
    result = rd.check_delaunay_realizability([(0, 1, 2)], verbose=True)
    assert not result["success"] and result["angles_radians"] is None
    assert not rd.optimize_hyperbolic_volume([(0, 1, 2)])["success"]


def test_newton_armijo_preserves_the_original_affine_plane():
    initial = np.array([.05, 1.4, np.pi-1.45])
    optimal, _, success, norm = rd._newton_in_nullspace(initial, null_space(np.ones((1, 3))))
    assert success and norm < 1e-12
    assert abs(optimal.sum()-np.pi) < 2e-14
    assert independent_volume(optimal) > independent_volume(initial)


def test_feasibility_report_does_not_promote_a_witness_to_an_embedding():
    # Positive angle assignments also exist on this disconnected complex;
    # these routines do not check the triangulated-disk hypothesis.
    result = rd.check_delaunay_realizability([(0, 1, 2), (3, 4, 5)])
    assert result["realizable"]
    report = rd.format_realizability_report(result)
    assert "Positive angle witness verified numerically" in report
    assert "Measured min angle" in report
    assert "global embedding" in report and "not certified" in report
    assert "REALIZABLE as Delaunay triangulation" not in report


def test_strict_feasibility_report_describes_the_common_margin_objective():
    result = rd.check_delaunay_realizability(FACES, strict=True)
    report = rd.format_realizability_report(result)
    assert "maximize the common angle/inequality margin" in report
    assert "Guaranteed common margin" in report
    assert "Measured min angle" in report
    assert "Maximum min angle" not in report


def test_feasibility_report_preserves_a_positive_subthreshold_margin():
    # Controlled documented API state, not a claimed naturally occurring
    # small triangulation fixture or an exact infeasibility result.
    result = rd.check_delaunay_realizability([(0, 1, 2)])
    result.update(realizable=False, min_angle=5e-7, min_angle_radians=5e-7*np.pi)
    report = rd.format_realizability_report(result)
    assert "No positive angle witness verified" in report
    assert "5e-07" in report
    assert "1e-06" in report
    assert "≤ 0" not in report and "<= 0" not in report
    assert "NOT REALIZABLE" not in report


def test_feasibility_report_retains_solver_failure_without_infeasibility_claim(monkeypatch):
    monkeypatch.setattr(rd, "linprog", lambda *args, **kwargs: SimpleNamespace(
        success=False, status=1, message="Iteration limit reached", x=None, nit=13
    ))
    result = rd.check_delaunay_realizability([(0, 1, 2)])
    report = rd.format_realizability_report(result)
    assert "No positive angle witness verified" in report
    assert "Iteration limit reached" in report
    assert "exact infeasibility" in report and "not certified" in report
    assert "NOT REALIZABLE" not in report
    assert "Measured min angle" not in report


@pytest.mark.parametrize("state, reason", [
    ("solver_failure", "feasibility_lp_failed"),
    ("audit_failure", "feasibility_lp_audit_failed"),
    ("subthreshold", "no_positive_initial_witness"),
])
def test_optimizer_preserves_lp_context_and_distinguishes_failed_start_causes(monkeypatch, state, reason):
    lp = rd.check_delaunay_realizability([(0, 1, 2)])
    lp.update(realizable=False, feasibility_status="no_positive_witness_verified")
    if state == "solver_failure":
        lp.update(success=False, solver_success=False, status=1,
                  message="Iteration limit reached", angles=None, angles_radians=None)
    elif state == "audit_failure":
        lp.update(success=False, message="Rejected by original-constraint feasibility audit")
        lp["primal_residuals"]["passed"] = False
    else:
        lp.update(min_angle=5e-7, min_angle_radians=5e-7*np.pi)
    monkeypatch.setattr(rd, "check_delaunay_realizability", lambda *args, **kwargs: lp)
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)])
    assert not result["success"] and result["termination_reason"] == reason
    assert result["feasibility_lp"] is lp
    assert result["feasibility_lp"]["min_angle"] == lp["min_angle"]
    assert lp["message"] in result["message"]
    assert result["n_volume_evaluations"] == 0 and result["n_iterations"] == 0
    if state == "subthreshold":
        assert "5e-07" in result["message"]
        assert "LP failed" not in result["message"]


@pytest.mark.parametrize("initial, budget, success, expected_calls", [
    (None, 0, True, 1),
    ([[.2, 1., np.pi-1.2]], 300, True, None),
    ([[.2, 1., np.pi-1.2]], 0, False, 1),
    ([[0., np.pi/2, np.pi/2]], 300, False, 0),
])
def test_volume_evaluation_counter_matches_instrumented_calls(monkeypatch, initial, budget,
                                                            success, expected_calls):
    observed = []
    original = rd._angle_structure_volume

    def counted(x):
        observed.append(np.array(x, copy=True))
        return original(x)

    monkeypatch.setattr(rd, "_angle_structure_volume", counted)
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], initial, max_iter=budget)
    assert result["success"] is success
    assert result["n_volume_evaluations"] == len(observed)
    if expected_calls is not None:
        assert len(observed) == expected_calls
    else:
        assert len(observed) > 1


def test_volume_evaluation_counter_includes_rejected_line_search_values(monkeypatch):
    observed = []
    original = rd._angle_structure_volume

    def reject_moving_candidates(x):
        observed.append(np.array(x, copy=True))
        value = original(x)
        # Force a line-search failure, while preserving the initial and final
        # value of the unchanged point. Every attempted objective still counts.
        return value if np.array_equal(x, observed[0]) else value-1e6

    monkeypatch.setattr(rd, "_angle_structure_volume", reject_moving_candidates)
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], [[.2, 1., np.pi-1.2]])
    assert not result["success"] and result["termination_reason"] == "line_search_failed"
    assert result["n_volume_evaluations"] == len(observed)
    assert len(observed) > 2
    np.testing.assert_array_equal(observed[0], observed[-1])


def test_lp_solver_iterations_remain_separate_from_volume_work(monkeypatch):
    monkeypatch.setattr(rd, "linprog", lambda *args, **kwargs: SimpleNamespace(
        success=True, status=0, message="Synthetic LP iteration count",
        x=np.full(4, 1/3), nit=13
    ))
    result = rd.optimize_hyperbolic_volume([(0, 1, 2)], max_iter=0)
    assert result["success"]
    assert result["feasibility_lp"]["solver_iterations"] == 13
    assert result["n_iterations"] == 0
    assert result["n_volume_evaluations"] == 1

