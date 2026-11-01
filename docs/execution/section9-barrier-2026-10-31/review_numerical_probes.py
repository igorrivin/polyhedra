"""Independent Section 9 solver probes, outside the maintained test suite.

High-precision derivatives come from differentiating a Clausen-sum objective,
not from calling the toolkit derivative or Newton-evaluation helpers. These
are finite checks, not interval bounds or completeness claims.
"""
from __future__ import annotations

from dataclasses import FrozenInstanceError
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

import mpmath as mp
import numpy as np

from ideal_poly_volume_toolkit import angle_barrier as ab

EVIDENCE = Path(__file__).resolve().parent
OUTPUT = EVIDENCE / "review-independent-probes.json"
if OUTPUT.exists():
    raise SystemExit(f"refusing to overwrite {OUTPUT}")

report = {
    "python": sys.version,
    "command": [sys.executable, str(Path(__file__).resolve())],
    "cwd": os.getcwd(),
    "pythonpath": os.environ.get("PYTHONPATH"),
    "module_path": ab.__file__,
    "module_sha256": hashlib.sha256(Path(ab.__file__).read_bytes()).hexdigest(),
    "mp_dps": 80,
    "scope": "finite independently differentiated numerical checks; no interval certification",
    "probes": {},
}


def record(name, function):
    try:
        detail = function()
        report["probes"][name] = {"passed": True, "detail": detail}
    except Exception as error:
        report["probes"][name] = {
            "passed": False, "error": repr(error), "traceback": traceback.format_exc()}
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")


def compact(result):
    return {key: result.to_dict()[key] for key in (
        "status", "converged", "parameters", "angles", "volume", "t",
        "newton_decrement", "gap_bound_estimate", "conservative_gap_bound_estimate",
        "finite_gap_available", "centered", "target_reached", "target_t",
        "centering_steps", "path_steps", "backtracks", "evaluations",
        "condition_estimate", "relative_linear_residual", "failure_phase",
        "failure_at_t", "certified")}


with mp.workdps(80):
    exact_base = [[mp.pi / 4, mp.pi / 5, 11 * mp.pi / 20],
                  [3 * mp.pi / 20, 7 * mp.pi / 20, mp.pi / 2]]
base = np.array([[float(a) for a in row] for row in exact_base])
C = np.array([[1., 0.], [0., 1.], [-1., -1.], [1., -2.], [0., 1.], [-1., 1.]])
u0 = np.array([-.07, .04])


def objectives(base_mp, matrix):
    flat = [a for row in base_mp for a in row]
    rows = [[mp.mpf(float(c)) for c in row] for row in matrix]

    def angles(*u):
        return [a + mp.fsum(c * x for c, x in zip(row, u))
                for a, row in zip(flat, rows)]

    def barrier(*u):
        return -mp.fsum(mp.log(mp.sin(a)) for a in angles(*u))

    def volume(*u):
        return mp.fsum(mp.clsin(2, 2 * a) / 2 for a in angles(*u))

    return angles, barrier, volume


def differentiate(function, point):
    n = len(point)
    gradient = []
    hessian = []
    for i in range(n):
        order = [0] * n
        order[i] = 1
        gradient.append(mp.diff(function, tuple(point), tuple(order)))
        row = []
        for j in range(n):
            second = order.copy()
            second[j] += 1
            row.append(mp.diff(function, tuple(point), tuple(second)))
        hessian.append(row)
    return mp.matrix(gradient), mp.matrix(hessian)


def independent_multidimensional_reference():
    result = ab.solve_angle_barrier(base, C, u0, epsilon=1e-5)
    assert result.converged
    details = {"solver": compact(result)}
    with mp.workdps(80):
        lifted = [[mp.mpf(float(a)) for a in row] for row in base]
        _, exact_f, exact_v = objectives(exact_base, C)
        lifted_angles, lifted_f, lifted_v = objectives(lifted, C)
        point = [mp.mpf(float(v)) for v in u0]
        f, g, h = ab.log_sine_barrier(base, C, u0)
        ref_g, ref_h = differentiate(lifted_f, point)
        errors = {"value": abs(mp.mpf(f) - lifted_f(*point)),
                  "gradient_max_abs": max(abs(mp.mpf(g[i]) - ref_g[i]) for i in range(2)),
                  "hessian_max_abs": max(abs(mp.mpf(h[i, j]) - ref_h[i, j])
                                           for i in range(2) for j in range(2))}
        assert errors["value"] < mp.mpf("1e-13")
        assert errors["gradient_max_abs"] < mp.mpf("1e-12")
        assert errors["hessian_max_abs"] < mp.mpf("1e-11")
        details["barrier_derivative_errors"] = {k: mp.nstr(v, 20) for k, v in errors.items()}

        def exact_gradient(x, y):
            return (mp.diff(exact_v, (x, y), (1, 0)), mp.diff(exact_v, (x, y), (0, 1)))

        stationary = mp.findroot(exact_gradient, (.1, .1), tol=mp.mpf("1e-65"))
        ref_angles, _, _ = objectives(exact_base, C)
        assert all(0 < a < mp.pi for a in ref_angles(*stationary))
        stationary_residual = max(abs(v) for v in exact_gradient(*stationary))
        assert stationary_residual < mp.mpf("1e-60")
        endpoint = [mp.mpf(float(v)) for v in result.parameters]
        exact_gap = exact_v(*stationary) - exact_v(*endpoint)
        source_shift = abs(exact_v(*endpoint) - lifted_v(*endpoint))
        value_error = abs(mp.mpf(result.volume) - lifted_v(*endpoint))
        assert -mp.mpf("1e-60") < exact_gap < result.gap_bound_estimate
        assert value_error < mp.mpf("2e-13")
        details.update(stationary_parameters=[mp.nstr(v, 65) for v in stationary],
                       stationary_residual=mp.nstr(stationary_residual, 20),
                       reference_maximum=mp.nstr(exact_v(*stationary), 65),
                       mathematical_gap=mp.nstr(exact_gap, 35),
                       exact_vs_binary64_lift_value_shift=mp.nstr(source_shift, 20),
                       binary64_value_error_vs_lifted_clausen=mp.nstr(value_error, 20))

        rows = [result.history[0], next(row for row in result.history if row.phase == "path"),
                result.history[len(result.history) // 2], result.history[-1]]
        independent_trace = []
        for row in rows:
            u = tuple(mp.mpf(float(v)) for v in row.parameters)
            t = mp.mpf(row.t)
            phi = lambda *x: lifted_f(*x) - t * lifted_v(*x)
            gradient, hessian = differentiate(phi, u)
            step = mp.lu_solve(hessian, -gradient)
            decrement = mp.sqrt(-(gradient.T * step)[0])
            absolute_error = abs(decrement - row.newton_decrement)
            assert absolute_error < mp.mpf("2e-8")
            if row.phase == "path":
                assert decrement < mp.mpf(1) / 4
            assert all(0 < a < mp.pi for a in lifted_angles(*u))
            independent_trace.append({"iteration": row.iteration, "phase": row.phase,
                                      "t": row.t, "reported_decrement": row.newton_decrement,
                                      "independent_decrement": mp.nstr(decrement, 30),
                                      "absolute_error": mp.nstr(absolute_error, 20)})
        details["independently_differentiated_trace"] = independent_trace
    details["evidence_limit"] = "The stationary solve and comparisons use 80-digit arithmetic, not interval enclosures."
    return details


def coordinate_changes():
    baseline = ab.solve_angle_barrier(base, C, u0, epsilon=1e-3)
    assert baseline.converged
    details = []
    transforms = {"mixing": np.array([[2., 1.], [-1., 3.]]),
                  "scale_small": np.eye(2) * 1e-60, "scale_large": np.eye(2) * 1e60}
    for name, transform in transforms.items():
        result = ab.solve_angle_barrier(base, C @ transform, np.linalg.solve(transform, u0), epsilon=1e-3)
        assert result.converged
        angle_error = float(np.max(np.abs(np.array(result.angles) - np.array(baseline.angles))))
        assert angle_error < 3e-13
        assert result.centering_steps == baseline.centering_steps
        assert result.path_steps == baseline.path_steps
        details.append({"name": name, "angle_max_abs_error": angle_error, "solver": compact(result)})
    for scale in (1e-200, 1e200):
        result = ab.solve_angle_barrier(base, C * scale)
        assert not result.converged and result.status in {"ill_conditioned", "numerical_failure"}
        assert not result.finite_gap_available and result.volume is None
        details.append({"name": f"unrepresentable_derivatives_scale_{scale}", "solver": compact(result)})
    return details


def failure_flags_and_ownership():
    regular = np.full((1, 3), np.pi / 3)
    tangent = np.array([[1., 0.], [0., 1.], [-1., -1.]])
    cases = {}
    finite_unconverged = ab.solve_angle_barrier(regular, tangent, [.15, -.05], max_centering_steps=0)
    assert finite_unconverged.status == "centering_limit"
    assert .25 < finite_unconverged.newton_decrement < 1
    assert finite_unconverged.finite_gap_available and not finite_unconverged.centered
    assert finite_unconverged.conservative_gap_bound_estimate is None
    cases["finite_uncentered_budget_limit"] = compact(finite_unconverged)
    path_limit = ab.solve_angle_barrier(regular, tangent, max_path_steps=0)
    assert path_limit.centered and path_limit.finite_gap_available
    assert path_limit.status == "path_limit" and not path_limit.target_reached
    cases["centered_unfinished_target"] = compact(path_limit)
    uncentered_target = ab.solve_angle_barrier(regular, tangent, [.15, -.05],
                                               t0=1e5, max_centering_steps=0)
    assert uncentered_target.target_reached and not uncentered_target.converged
    assert uncentered_target.status == "centering_limit"
    cases["target_reached_not_centered"] = compact(uncentered_target)
    fixed = []
    for t0 in (1., 1e-310, np.nextafter(0., 1.)):
        result = ab.solve_angle_barrier(regular, np.empty((3, 0)), t0=t0, epsilon=1e-310)
        assert result.status == "fixed_domain" and result.converged
        assert result.finite_gap_available and result.centered and result.target_reached
        assert result.gap_bound_estimate == result.conservative_gap_bound_estimate == 0
        fixed.append(compact(result))
    cases["fixed_domain_tiny_t0_corrected"] = fixed

    b, c, initial = base.copy(), C.copy(), u0.copy()
    for array in (b, c, initial):
        array.flags.writeable = False
    original_bytes = [a.tobytes() for a in (b, c, initial)]
    result = ab.solve_angle_barrier(b, c, initial, epsilon=.1)
    assert result.converged
    assert original_bytes == [a.tobytes() for a in (b, c, initial)]
    detached = result.to_dict()
    detached["history"][0]["parameters"] = (1e5, 1e5)
    assert result.history[0].parameters == tuple(u0)
    try:
        result.converged = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError("result should be immutable")
    cases["readonly_inputs_and_detached_snapshot"] = True
    return cases


def malformed_slices():
    rejected = []
    cases = {
        "empty_domain": (np.empty((0, 3)), np.empty((0, 0))),
        "no_tangent": (base, np.full((6, 1), 1e-250)),
        "numerically_dependent": (base, np.column_stack((C[:, 0], C[:, 0] + 1e-17 * C[:, 1]))),
        "zero_column": (base, np.column_stack((C[:, 0], np.zeros(6)))),
        "impossible_rank_dimension": (base, np.zeros((6, 5))),
        "complex_data": (base, C.astype(complex)),
        "wrong_sum": (base + 1e-11, C),
    }
    for name, (b, c) in cases.items():
        try:
            ab.solve_angle_barrier(b, c)
        except ValueError as error:
            rejected.append({"name": name, "exception": str(error)})
        else:
            raise AssertionError(f"accepted {name}")
    return rejected


def source_precision_boundary():
    # Neither this accepted binary64 triple nor any other finite float triple
    # sums exactly to mathematical pi. Near a boundary, two volume extensions
    # differ visibly; the solver's documentation does not enclose that effect.
    from ideal_poly_volume_toolkit.variational import angle_volume
    flat = np.array([[np.pi - 2e-12, 1e-12, 1e-12]])
    c = np.zeros((3, 0))
    result = ab.solve_angle_barrier(flat, c)
    assert result.converged and not result.certified
    with mp.workdps(80):
        angles = [mp.mpf(float(a)) for a in flat[0]]
        z = mp.sin(angles[1]) / mp.sin(angles[2]) * mp.exp(1j * angles[0])
        direct_bw = mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z))
        clausen = mp.fsum(mp.clsin(2, 2 * a) / 2 for a in angles)
        evaluated = angle_volume(flat, c, [])
        assert abs(mp.mpf(evaluated) - direct_bw) < mp.mpf("2e-15")
        return {"angles": flat.tolist(), "reported_volume": evaluated,
                "lifted_triangle_sum_minus_real_pi": mp.nstr(mp.fsum(angles) - mp.pi, 35),
                "lifted_clausen_volume": mp.nstr(clausen, 35),
                "independent_bw_volume": mp.nstr(direct_bw, 35),
                "clausen_vs_bw_discrepancy": mp.nstr(clausen - direct_bw, 25),
                "scope": "documents accepted source-rounding sensitivity; not a solver certificate or a new defect"}


for name, function in (
    ("independent_multidimensional_reference", independent_multidimensional_reference),
    ("coordinate_changes", coordinate_changes),
    ("failure_flags_and_ownership", failure_flags_and_ownership),
    ("malformed_slices", malformed_slices),
    ("source_precision_boundary", source_precision_boundary),
):
    record(name, function)
report["all_passed"] = all(row["passed"] for row in report["probes"].values())
OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
print(json.dumps({"output": str(OUTPUT), "all_passed": report["all_passed"],
                  "probes": {k: v["passed"] for k, v in report["probes"].items()}}, indent=2))
raise SystemExit(0 if report["all_passed"] else 1)
