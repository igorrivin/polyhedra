"""Dense numerical barrier path for an explicitly supplied affine angle slice.

The coordinates are ``alpha = base_angles + incidence @ u``, flattened by
triangle.  This module implements Section 9's finite-centering schedule.  Its
gap bounds are floating-point estimates of a theorem in exact arithmetic,
not interval certificates or geometric-realization claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import math

import numpy as np

from . import variational


_CENTERED = 0.25
_PRE_STEP = 5.0 / 16.0
_ANGLE_SUM_TOL = 64 * np.finfo(float).eps * np.pi
_SCOPE = (
    "binary64 computation on the supplied affine angle slice",
    "gap estimates assume the chapter's exact-arithmetic hypotheses",
    "numerical rank, derivatives, norms and linear residuals are not certified",
    "no feasibility LP, topology, embedding, peripheral or nearly-linear solver",
)


@dataclass(frozen=True)
class BarrierIteration:
    """An accepted, freshly evaluated point; rejected trials are not iterates."""

    phase: str
    iteration: int
    t: float
    parameters: tuple[float, ...]
    volume: float
    barrier: float
    newton_decrement: float
    minimum_angle: float
    maximum_angle: float
    condition_estimate: float
    relative_linear_residual: float
    step_size: float | None
    decrement_before_step: float | None
    parameter_multiplier: float | None
    triangle_sum_residual: float


@dataclass(frozen=True)
class BarrierResult:
    """Numerical outcome, including a last feasible point on unsuccessful runs.

    ``converged`` requires a fresh centered endpoint and the conservative
    target parameter, except for the explicitly reported zero-dimensional
    ``fixed_domain`` case.  A finite gap estimate can exist on a failed run.
    ``certified`` is always false: floating evaluation error is not enclosed.
    """

    status: str
    converged: bool
    message: str
    parameters: tuple[float, ...]
    angles: tuple[tuple[float, ...], ...]
    volume: float | None
    t: float
    newton_decrement: float | None
    minimum_angle: float
    maximum_angle: float
    gap_bound_estimate: float | None
    conservative_gap_bound_estimate: float | None
    finite_gap_available: bool
    centered: bool
    target_reached: bool
    epsilon: float
    target_t: float
    corner_count: int
    centering_steps: int
    path_steps: int
    backtracks: int
    evaluations: int
    condition_estimate: float | None
    relative_linear_residual: float | None
    failure_phase: str | None
    failure_at_t: float | None
    base_triangle_sum_residual: float
    tangent_sum_relative_residual: float
    triangle_sum_residual: float
    history: tuple[BarrierIteration, ...]
    schema_version: int = 1
    certified: bool = False
    arithmetic: str = "IEEE-754 binary64; dense NumPy Cholesky and linear solves"
    scope: tuple[str, ...] = _SCOPE

    def to_dict(self):
        """Return a detached JSON-compatible dictionary; reject nonfinite data."""
        result = asdict(self)
        # Tuples serialize as JSON arrays. This also validates every nested
        # diagnostic rather than silently emitting JavaScript NaN/Infinity.
        json.dumps(result, allow_nan=False)
        return result


@dataclass
class _State:
    parameters: np.ndarray
    angles: np.ndarray
    t: float
    volume: float
    barrier: float
    objective: float
    decrement: float
    step: np.ndarray
    condition: float
    residual: float


class _NumericalFailure(ArithmeticError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def _real_array(value, name):
    if np.iscomplexobj(value):
        raise ValueError(f"{name} must be real")
    try:
        result = np.array(value, dtype=float, copy=True)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite real array") from error
    if not np.all(np.isfinite(result)):
        raise ValueError(f"{name} must be finite")
    return result


def _check_angles(angles):
    if (angles.ndim != 2 or angles.shape[1] != 3 or len(angles) == 0
            or not np.all(np.isfinite(angles))):
        raise ValueError("angles must be a nonempty finite (M, 3) array")
    if np.any(angles <= 0) or np.any(angles >= np.pi):
        raise ValueError("angles must lie strictly between 0 and pi")
    if not np.allclose(angles.sum(axis=1), np.pi, rtol=0, atol=_ANGLE_SUM_TOL):
        raise ValueError("each triangle's angles must sum to pi within binary64 roundoff")


def _prepare(base_angles, incidence, initial_u):
    base = _real_array(base_angles, "base_angles")
    _check_angles(base)
    matrix = _real_array(incidence, "incidence")
    if matrix.ndim != 2 or matrix.shape[0] != base.size:
        raise ValueError("incidence must have shape (base_angles.size, n)")
    if matrix.shape[1] > 2 * len(base):
        raise ValueError("independent triangle-angle tangents have at most 2*M coordinates")
    blocks = matrix.reshape(len(base), 3, matrix.shape[1])
    # A relative per-triangle/column test rejects even tiny non-tangent
    # columns. An absolute tolerance would incorrectly accept scaled errors.
    scale = np.max(np.abs(blocks), axis=1, initial=0)
    scaled_blocks = np.divide(blocks, scale[:, None, :], out=np.zeros_like(blocks),
                              where=scale[:, None, :] != 0)
    tangent_error = np.abs(np.sum(scaled_blocks, axis=1))
    if np.any(tangent_error > 32 * np.finfo(float).eps * np.sum(np.abs(scaled_blocks), axis=1)):
        raise ValueError("incidence columns must sum to zero in every triangle")
    n = matrix.shape[1]
    # This is a numerical SVD rank test, not an exact independence proof.
    # https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html
    if n:
        matrix_scale = float(np.max(np.abs(matrix)))
        try:
            rank = np.linalg.matrix_rank(matrix / matrix_scale) if matrix_scale else 0
        except np.linalg.LinAlgError as error:
            raise ValueError("incidence numerical rank could not be evaluated") from error
        if rank != n:
            raise ValueError("incidence must have numerically independent columns")
    u = np.zeros(n) if initial_u is None else _real_array(initial_u, "initial_u")
    if u.shape != (n,):
        raise ValueError("initial_u has the wrong coordinate dimension")
    try:
        with np.errstate(over="raise", invalid="raise"):
            angles = (base.ravel() + matrix @ u).reshape(base.shape)
        _check_angles(angles)
    except (ValueError, FloatingPointError) as error:
        raise ValueError("initial_u must give finite strictly feasible triangle angles") from error
    return base, matrix, u, angles


def _barrier_terms(angles, matrix):
    sine = np.sin(angles.ravel())
    value = float(-np.sum(np.log(sine)))
    gradient = -(matrix.T @ (1 / np.tan(angles.ravel())))
    scaled = matrix / sine[:, None]
    hessian = scaled.T @ scaled
    if not (math.isfinite(value) and np.all(np.isfinite(gradient))
            and np.all(np.isfinite(hessian))):
        raise FloatingPointError("nonfinite log-sine barrier evaluation")
    return value, gradient, hessian


def log_sine_barrier(base_angles, incidence, u):
    """Return F, gradient and Hessian for F=-sum(log(sin(alpha))).

    Inputs obey the same full-rank affine-slice contract as the solver.
    Derivatives are with respect to ``u``, in radians, and use binary64.
    Invalid data raise ValueError; unrepresentable arithmetic raises
    FloatingPointError. No input angle is clipped or normalized.
    """
    _, matrix, _, angles = _prepare(base_angles, incidence, u)
    with np.errstate(over="raise", divide="raise", invalid="raise"):
        return _barrier_terms(angles, matrix)


def _norm(vector):
    # math.hypot scales its sum, unlike directly squaring very large values.
    return math.hypot(*(float(value) for value in vector))


def _shift(parameters, step, size=1.0):
    try:
        with np.errstate(over="raise", invalid="raise"):
            candidate = parameters + size * step
        if not np.all(np.isfinite(candidate)):
            raise FloatingPointError("nonfinite trial parameters")
        return candidate
    except FloatingPointError as error:
        raise _NumericalFailure("numerical_failure", str(error)) from error


def _evaluate(base, matrix, u, t, condition_limit, residual_tolerance):
    try:
        with np.errstate(over="raise", divide="raise", invalid="raise"):
            angles = variational.deformed_angles(base, matrix, u)
            _check_angles(angles)
            barrier, fg, fh = _barrier_terms(angles, matrix)
            volume = variational.angle_volume(base, matrix, u)
            vg, vh = variational.angle_volume_derivatives(base, matrix, u)
            gradient = fg - t * vg
            hessian = fh - t * vh
            objective = barrier - t * volume
            if not (math.isfinite(volume) and math.isfinite(objective)
                    and np.all(np.isfinite(gradient)) and np.all(np.isfinite(hessian))):
                raise FloatingPointError("nonfinite barrier objective or derivatives")
            if not len(u):
                return _State(u.copy(), angles, t, volume, barrier, objective,
                              0.0, u.copy(), 1.0, 0.0)
            # Multiplication can introduce a small antisymmetric rounding part.
            # Check it before explicitly taking the symmetric numerical form.
            if np.max(np.abs(hessian - hessian.T)) > 64 * np.finfo(float).eps * np.max(np.abs(hessian)):
                raise _NumericalFailure("numerical_failure", "Hessian lost numerical symmetry")
            hessian = 0.5 * hessian + 0.5 * hessian.T
            condition = float(np.linalg.cond(hessian))
            if not math.isfinite(condition) or condition > condition_limit:
                raise _NumericalFailure("ill_conditioned",
                                        f"Hessian condition estimate {condition:g} exceeds limit {condition_limit:g}")
            # NumPy documents L L.T=H and solving L y=g, then L.T d=-y.
            # https://numpy.org/doc/stable/reference/generated/numpy.linalg.cholesky.html
            factor = np.linalg.cholesky(hessian)
            dual_gradient = np.linalg.solve(factor, gradient)
            step = -np.linalg.solve(factor.T, dual_gradient)
            decrement = _norm(dual_gradient)
            linear_residual = hessian @ step + gradient
            dual_residual = np.linalg.solve(factor, linear_residual)
            residual_norm = _norm(dual_residual)
            if decrement == 0 and residual_norm != 0:
                raise _NumericalFailure("linear_solve_failure", "Nonzero linear residual at zero computed decrement")
            residual = residual_norm / decrement if decrement else 0.0
            if not (np.all(np.isfinite(step)) and math.isfinite(decrement)
                    and math.isfinite(residual)):
                raise FloatingPointError("nonfinite Newton step or diagnostic")
            if residual > residual_tolerance:
                raise _NumericalFailure("linear_solve_failure",
                                        f"Relative dual-norm linear residual {residual:g} exceeds limit {residual_tolerance:g}")
            return _State(u.copy(), angles, t, volume, barrier, objective,
                          decrement, step, condition, residual)
    except _NumericalFailure:
        raise
    except (FloatingPointError, np.linalg.LinAlgError, ValueError, OverflowError) as error:
        raise _NumericalFailure("numerical_failure", str(error)) from error


def _positive_scalar(value, name):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be a finite positive real number")
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError(f"{name} must be a finite positive real number") from error
    if not math.isfinite(result) or result <= 0:
        raise ValueError(f"{name} must be a finite positive real number")
    return result


def _budget(value, name, minimum=0):
    if (isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer))
            or value < minimum):
        raise ValueError(f"{name} must be an integer at least {minimum}")
    return int(value)


def solve_angle_barrier(base_angles, incidence, initial_u=None, *, epsilon=1e-4,
                        t0=1.0, max_centering_steps=100, max_path_steps=5000,
                        max_backtracks=60, condition_limit=1e12,
                        linear_residual_tolerance=1e-8):
    """Numerically maximize ideal volume on a supplied affine angle slice.

    First center F-t0*V by safeguarded damped Newton steps. Then use the
    chapter's multiplier 1+1/(20*sqrt(m)), m=base_angles.size, and one full
    Newton step per parameter change. Success requires a freshly evaluated
    decrement <=1/4 and t>=17*m/(12*epsilon). Centering work is counted
    separately. A zero-dimensional slice returns ``fixed_domain`` and zero
    gap estimate without a path; its target_t is t0.

    Linear solves are dense binary64 Cholesky solves. Their relative dual-norm
    residual and the Hessian's SVD condition estimate are numerical diagnostics,
    not exact energy-error guarantees. No angle clipping, pseudoinverse,
    regularization, LP feasibility search or unreported recovery is performed.

    Invalid inputs raise ValueError. Budget exhaustion, arithmetic failure or
    a violated path invariant returns a nonconverged result at the last accepted
    point, with an explicit reason. The trace contains only accepted points.
    """
    epsilon = _positive_scalar(epsilon, "epsilon")
    t0 = _positive_scalar(t0, "t0")
    condition_limit = _positive_scalar(condition_limit, "condition_limit")
    residual_tolerance = _positive_scalar(linear_residual_tolerance, "linear_residual_tolerance")
    if not 1 <= condition_limit <= 1 / np.finfo(float).eps:
        raise ValueError("condition_limit must lie between 1 and 1/binary64_epsilon")
    if residual_tolerance > 0.01:
        raise ValueError("linear_residual_tolerance must not exceed 0.01")
    max_centering_steps = _budget(max_centering_steps, "max_centering_steps")
    max_path_steps = _budget(max_path_steps, "max_path_steps")
    max_backtracks = _budget(max_backtracks, "max_backtracks", 1)
    base, matrix, u, initial_angles = _prepare(base_angles, incidence, initial_u)
    m = base.size
    base_sum_residual = float(np.max(np.abs(base.sum(axis=1) - np.pi)))
    blocks = matrix.reshape(len(base), 3, matrix.shape[1])
    scale = np.max(np.abs(blocks), axis=1, initial=0)
    scaled = np.divide(blocks, scale[:, None, :], out=np.zeros_like(blocks),
                       where=scale[:, None, :] != 0)
    tangent_residual = float(np.max(np.abs(scaled.sum(axis=1)), initial=0))
    target_t = t0 if not len(u) else (17.0 / 12.0) * m / epsilon
    if not math.isfinite(target_t):
        raise ValueError("requested stopping parameter is outside binary64 range")
    # Round the numerical target upward if division back to the reported
    # conservative estimate would otherwise exceed the requested epsilon.
    while len(u) and (17.0 / 12.0) * m / target_t > epsilon:
        target_t = math.nextafter(target_t, math.inf)
        if not math.isfinite(target_t):
            raise ValueError("requested stopping parameter is outside binary64 range")
    multiplier = 1 + 1 / (20 * math.sqrt(m))
    history = []
    centering_steps = path_steps = backtracks = evaluations = 0
    state = None

    def evaluate(point, parameter):
        nonlocal evaluations
        evaluations += 1
        return _evaluate(base, matrix, point, parameter, condition_limit, residual_tolerance)

    def record(current, phase, step_size=None, before=None, ratio=None):
        history.append(BarrierIteration(
            phase, len(history), current.t, tuple(map(float, current.parameters)),
            current.volume, current.barrier, current.decrement,
            float(current.angles.min()), float(current.angles.max()),
            current.condition, current.residual, step_size, before, ratio,
            float(np.max(np.abs(current.angles.sum(axis=1) - np.pi)))))

    def finish(status, message, phase=None, attempted_t=None):
        current_u = state.parameters if state is not None else u
        angles = state.angles if state is not None else initial_angles
        parameter = state.t if state is not None else t0
        decrement = state.decrement if state is not None else None
        centered = decrement is not None and decrement <= _CENTERED
        finite_gap = decrement is not None and decrement < 1
        sharper = conservative = None
        if finite_gap:
            sharper = (m + (math.sqrt(m) + decrement) * decrement / (1 - decrement)) / parameter
            if not math.isfinite(sharper):
                sharper = None
                finite_gap = False
        if centered:
            conservative = (17.0 / 12.0) * m / parameter
            if not math.isfinite(conservative):
                conservative = None
        if status == "fixed_domain":
            sharper = conservative = 0.0
            finite_gap = True
        converged = status in ("converged", "fixed_domain")
        return BarrierResult(
            status, converged, message, tuple(map(float, current_u)),
            tuple(tuple(map(float, row)) for row in angles),
            state.volume if state is not None else None, parameter, decrement,
            float(angles.min()), float(angles.max()), sharper, conservative,
            finite_gap, centered, parameter >= target_t, epsilon, target_t, m,
            centering_steps, path_steps, backtracks, evaluations,
            state.condition if state is not None else None,
            state.residual if state is not None else None,
            phase, attempted_t, base_sum_residual, tangent_residual,
            float(np.max(np.abs(angles.sum(axis=1) - np.pi))), tuple(history))

    try:
        state = evaluate(u, t0)
    except _NumericalFailure as error:
        return finish(error.status, str(error), "initial", t0)
    record(state, "initial")
    if not len(u):
        return finish("fixed_domain", "The supplied affine slice consists of one point.")

    while state.decrement > _CENTERED:
        if centering_steps >= max_centering_steps:
            return finish("centering_limit", "Initial centering step budget exhausted.", "centering", state.t)
        step_size = 1 / (1 + state.decrement)
        previous = state
        accepted = None
        last_failure = None
        for attempt in range(max_backtracks):
            try:
                candidate = _shift(previous.parameters, previous.step, step_size)
                if np.array_equal(candidate, previous.parameters):
                    return finish("stagnation", "Centering step does not change the parameters.", "centering", previous.t)
                trial = evaluate(candidate, previous.t)
                # Damped self-concordant Newton is a descent method; use a
                # conventional Armijo check as a floating-point safeguard.
                decrease = 0.01 * (step_size * previous.decrement) * previous.decrement
                if trial.objective <= previous.objective - decrease:
                    accepted = trial
                    break
            except _NumericalFailure as error:
                last_failure = error
            if attempt + 1 < max_backtracks:
                step_size *= 0.5
                backtracks += 1
        if accepted is None:
            detail = f" Last trial: {last_failure}" if last_failure else ""
            return finish("centering_failed", "No acceptable feasible centering step." + detail,
                          "centering", previous.t)
        state = accepted
        centering_steps += 1
        record(state, "centering", step_size, previous.decrement, 1.0)

    while state.t < target_t:
        if path_steps >= max_path_steps:
            return finish("path_limit", "Short-step path budget exhausted.", "path", state.t)
        next_t = min(state.t * multiplier, target_t)
        if not math.isfinite(next_t) or next_t <= state.t:
            return finish("stagnation", "Barrier parameter cannot advance in binary64.", "path", state.t)
        previous = state
        try:
            before = evaluate(previous.parameters, next_t)
            if before.decrement > _PRE_STEP:
                return finish("path_invariant_failed", "New-parameter decrement exceeds 5/16.", "path", next_t)
            candidate = _shift(before.parameters, before.step)
            trial = evaluate(candidate, next_t)
            if trial.decrement > _CENTERED:
                return finish("path_invariant_failed", "Full Newton step did not restore decrement <=1/4.", "path", next_t)
        except _NumericalFailure as error:
            return finish(error.status, str(error), "path", next_t)
        state = trial
        path_steps += 1
        record(state, "path", 1.0, before.decrement, next_t / previous.t)

    # This is a fresh evaluation at the actual returned parameters and t,
    # independent of the previously cached stopping diagnostics.
    try:
        final = evaluate(state.parameters, state.t)
    except _NumericalFailure as error:
        return finish(error.status, str(error), "final", state.t)
    state = final
    if (state.decrement > _CENTERED or state.t < target_t
            or (17.0 / 12.0) * m / state.t > epsilon):
        return finish("path_invariant_failed", "Fresh endpoint did not meet the stopping conditions.", "final", state.t)
    return finish("converged", "Fresh centered endpoint reached the conservative gap target.")
