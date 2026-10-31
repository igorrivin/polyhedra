"""Optimization services for ideal hyperbolic polyhedra in H^3.

This module owns the reusable, non-UI part of the general H^3 optimizer.
Command-line and GUI entry points should adapt these functions rather than
maintaining independent objectives.

The parameterization fixes three ideal vertices at ``0``, ``1``, and
``infinity``.  Each remaining vertex is represented by spherical
``(theta, phi)`` coordinates and stereographically projected to the complex
plane.  Volume evaluation uses the vectorized Bloch--Wigner implementation in
``geometry``; SciPy's differential-evolution driver does not benefit from
building Torch autograd graphs.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from functools import partial
import json
from numbers import Real
from typing import Callable, Iterable, Mapping

import numpy as np
from scipy.optimize import differential_evolution, minimize
from scipy.spatial import QhullError

from .geometry import (
    delaunay_triangulation_indices,
    ideal_poly_volume_via_delaunay,
)


OBJECTIVE_PENALTY = 1_000.0


def spherical_to_complex(theta, phi):
    """Stereographically project spherical coordinates to the complex plane."""
    return np.tan(np.asarray(theta) / 2.0) * np.exp(1j * np.asarray(phi))


def parameters_to_complex(params: Iterable[float], n_vertices: int) -> np.ndarray:
    """Build the finite vertices for an ``n_vertices`` ideal polyhedron.

    The returned array contains ``0``, ``1``, and the ``n_vertices - 3`` free
    vertices.  The final vertex at infinity is implicit.
    """
    if n_vertices < 4:
        raise ValueError("n_vertices must be at least 4")

    values = np.asarray(params, dtype=np.float64)
    expected = 2 * (n_vertices - 3)
    if values.ndim != 1 or values.size != expected:
        raise ValueError(
            f"expected {expected} parameters for {n_vertices} vertices; "
            f"received shape {values.shape}"
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("optimization parameters must be finite")

    free = spherical_to_complex(values[0::2], values[1::2]).astype(
        np.complex128, copy=False
    )
    if not np.all(np.isfinite(free.real)) or not np.all(np.isfinite(free.imag)):
        raise ValueError("stereographic projection produced a non-finite vertex")
    return np.concatenate((np.array([0.0j, 1.0 + 0.0j]), free))


def negative_volume_objective(params: Iterable[float], n_vertices: int) -> float:
    """Return negative H^3 volume, or a finite penalty when triangulation fails."""
    try:
        vertices = parameters_to_complex(params, n_vertices)
        volume = ideal_poly_volume_via_delaunay(
            vertices,
            mode="bloch_wigner",
        )
    except (
        QhullError,
        ValueError,
        FloatingPointError,
        OverflowError,
        ZeroDivisionError,
    ):
        return OBJECTIVE_PENALTY

    if not np.isfinite(volume) or volume <= 0.0:
        return OBJECTIVE_PENALTY
    return -float(volume)


def _serially_polish_differential_evolution_result(
    result,
    objective: Callable[[np.ndarray], float],
    bounds: list[tuple[float, float]],
    *,
    n_vertices: int,
) -> tuple[_EndpointCheck, int, str]:
    """Apply SciPy's differential-evolution polish semantics without a pool.

    Recent SciPy versions pass the differential-evolution worker map into
    L-BFGS-B polishing.  That is useful for expensive objectives, but the H^3
    objective is fine-grained enough that repeated process dispatch dominates
    the finite-difference evaluations.  Running the same minimizer directly
    keeps polishing serial. Both endpoints are checked afresh before accepting
    an improvement. The returned verification count is separate from SciPy's
    reported function-evaluation count. ``result.success`` retains the DE
    convergence status even if a local polish improves the candidate.
    """
    initial = _check_endpoint(result.x, n_vertices, bounds)
    if initial.volume is None:
        return initial, initial.verification_evals, "Not run: invalid DE endpoint"
    polished = minimize(
        objective,
        np.copy(result.x),
        method="L-BFGS-B",
        bounds=bounds,
    )
    result.nfev += polished.nfev
    candidate = _check_endpoint(polished.x, n_vertices, bounds)
    evaluations = initial.verification_evals + candidate.verification_evals
    if (
        candidate.volume is not None
        and candidate.volume > initial.volume
        and polished.success
    ):
        result.fun = polished.fun
        result.x = polished.x
        result.jac = polished.jac
        return candidate, evaluations, "Accepted: verified volume improved"
    if candidate.volume is None:
        return initial, evaluations, f"Rejected: {candidate.reason}; parameters={repr(polished.x)}"
    if not polished.success:
        return initial, evaluations, "Rejected: local solver did not converge"
    return initial, evaluations, "Rejected: verified volume did not improve"


def _canonical_edge(u: int, v: int) -> tuple[int, int]:
    return (u, v) if u < v else (v, u)


def complete_boundary_triangulation(
    finite_triangulation: np.ndarray,
    n_finite_vertices: int,
) -> np.ndarray:
    """Close a planar Delaunay disk by adding the fan at infinity.

    ``finite_triangulation`` consists of the faces not incident to infinity.
    Edges occurring once form its boundary; coning each of them to the
    implicit vertex ``n_finite_vertices`` yields the full triangulated sphere.
    """
    if int(n_finite_vertices) != n_finite_vertices or n_finite_vertices < 3:
        raise ValueError("n_finite_vertices must be an integer at least 3")
    n_finite_vertices = int(n_finite_vertices)
    triangles = np.asarray(finite_triangulation, dtype=np.int64)
    if triangles.ndim != 2 or triangles.shape[1] != 3:
        raise ValueError("finite_triangulation must have shape (n_faces, 3)")
    if not len(triangles):
        raise ValueError("finite_triangulation must contain at least one face")
    if triangles.min() < 0 or triangles.max() >= n_finite_vertices:
        raise ValueError("triangulation contains an out-of-range vertex index")
    if any(len(set(map(int, triangle))) != 3 for triangle in triangles):
        raise ValueError("triangulation faces must contain three distinct vertices")
    if set(map(int, triangles.ravel())) != set(range(n_finite_vertices)):
        raise ValueError("every finite vertex must occur in the triangulation")

    # Record both face incidence and the direction in which each input face
    # traverses an edge.  The latter lets us orient mixed-winding input before
    # adding the fan at infinity.
    edge_faces: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for face_index, (i, j, k) in enumerate(triangles):
        for u, v in ((int(i), int(j)), (int(j), int(k)), (int(k), int(i))):
            edge = _canonical_edge(u, v)
            direction = 1 if (u, v) == edge else -1
            edge_faces.setdefault(edge, []).append((face_index, direction))

    if any(len(incidences) > 2 for incidences in edge_faces.values()):
        raise ValueError("a triangulation edge cannot belong to more than two faces")

    boundary_edges = sorted(
        edge for edge, incidences in edge_faces.items() if len(incidences) == 1
    )
    boundary_adjacency: dict[int, set[int]] = {}
    for u, v in boundary_edges:
        boundary_adjacency.setdefault(u, set()).add(v)
        boundary_adjacency.setdefault(v, set()).add(u)
    if not boundary_adjacency or any(
        len(neighbours) != 2 for neighbours in boundary_adjacency.values()
    ):
        raise ValueError("finite triangulation boundary must be a simple cycle")
    seen = set()
    pending = [next(iter(boundary_adjacency))]
    while pending:
        vertex = pending.pop()
        if vertex in seen:
            continue
        seen.add(vertex)
        pending.extend(boundary_adjacency[vertex] - seen)
    if seen != set(boundary_adjacency):
        raise ValueError("finite triangulation boundary must be one connected cycle")

    # A connected triangulated disk has Euler characteristic one.  This rules
    # out, for example, a punctured torus whose boundary is also one simple
    # cycle and whose edge multiplicities otherwise look valid.
    finite_euler = n_finite_vertices - len(edge_faces) + len(triangles)
    if finite_euler != 1:
        raise ValueError("finite triangulation must have the topology of a disk")

    # Check the local manifold condition.  The link of an interior vertex is
    # one cycle; the link of a boundary vertex is one path.
    boundary_vertices = set(boundary_adjacency)
    for vertex in range(n_finite_vertices):
        link_adjacency: dict[int, set[int]] = {}
        link_edges: set[tuple[int, int]] = set()
        for triangle in triangles:
            if vertex not in triangle:
                continue
            opposite = [int(item) for item in triangle if item != vertex]
            link_edge = _canonical_edge(*opposite)
            if link_edge in link_edges:
                raise ValueError("finite triangulation has a non-manifold vertex link")
            link_edges.add(link_edge)
            u, v = link_edge
            link_adjacency.setdefault(u, set()).add(v)
            link_adjacency.setdefault(v, set()).add(u)

        link_seen: set[int] = set()
        link_pending = [next(iter(link_adjacency))]
        while link_pending:
            neighbour = link_pending.pop()
            if neighbour in link_seen:
                continue
            link_seen.add(neighbour)
            link_pending.extend(link_adjacency[neighbour] - link_seen)
        if link_seen != set(link_adjacency):
            raise ValueError("finite triangulation has a disconnected vertex link")

        link_degrees = [len(neighbours) for neighbours in link_adjacency.values()]
        if vertex in boundary_vertices:
            if link_degrees.count(1) != 2 or any(
                degree not in (1, 2) for degree in link_degrees
            ):
                raise ValueError("finite triangulation has a non-manifold boundary")
        elif any(degree != 2 for degree in link_degrees):
            raise ValueError("finite triangulation has a non-manifold interior")

    # Propagate a coherent orientation across the finite disk.  Two incident
    # faces must traverse their shared edge in opposite directions.
    face_signs = np.zeros(len(triangles), dtype=np.int8)
    face_signs[0] = 1
    face_pending = [0]
    face_neighbours: dict[int, list[tuple[int, int, int]]] = {
        face_index: [] for face_index in range(len(triangles))
    }
    for incidences in edge_faces.values():
        if len(incidences) != 2:
            continue
        (first_face, first_direction), (second_face, second_direction) = incidences
        face_neighbours[first_face].append(
            (second_face, first_direction, second_direction)
        )
        face_neighbours[second_face].append(
            (first_face, second_direction, first_direction)
        )

    while face_pending:
        face = face_pending.pop()
        for neighbour, face_direction, neighbour_direction in face_neighbours[face]:
            required_sign = (
                -int(face_signs[face]) * face_direction * neighbour_direction
            )
            if face_signs[neighbour] == 0:
                face_signs[neighbour] = required_sign
                face_pending.append(neighbour)
            elif face_signs[neighbour] != required_sign:
                raise ValueError("finite triangulation is not orientable")
    if np.any(face_signs == 0):
        raise ValueError("finite triangulation faces must be edge-connected")

    oriented_triangles = triangles.copy()
    flipped = face_signs == -1
    oriented_triangles[flipped] = oriented_triangles[flipped][:, [0, 2, 1]]

    infinity = n_finite_vertices
    infinity_faces = []
    for edge in boundary_edges:
        face_index, input_direction = edge_faces[edge][0]
        oriented_direction = input_direction * int(face_signs[face_index])
        u, v = edge if oriented_direction == 1 else tuple(reversed(edge))
        # Reverse the disk's directed boundary edge in the adjacent fan face.
        infinity_faces.append((v, u, infinity))
    return np.vstack((oriented_triangles, np.asarray(infinity_faces, dtype=np.int64)))


def analyze_ideal_polyhedron_structure(
    finite_vertices: np.ndarray,
    finite_triangulation: np.ndarray | None = None,
) -> dict:
    """Describe the full spherical boundary, including the implicit infinity."""
    vertices = np.asarray(finite_vertices, dtype=np.complex128)
    if vertices.ndim != 1:
        raise ValueError("finite_vertices must be a one-dimensional complex array")
    triangles = (
        delaunay_triangulation_indices(vertices)
        if finite_triangulation is None
        else np.asarray(finite_triangulation, dtype=np.int64)
    )
    boundary = complete_boundary_triangulation(triangles, len(vertices))

    edges: set[tuple[int, int]] = set()
    for i, j, k in boundary:
        edges.update(
            {
                _canonical_edge(int(i), int(j)),
                _canonical_edge(int(j), int(k)),
                _canonical_edge(int(k), int(i)),
            }
        )

    n_vertices = len(vertices) + 1
    degrees = [0] * n_vertices
    for u, v in edges:
        degrees[u] += 1
        degrees[v] += 1

    n_faces = len(boundary)
    n_edges = len(edges)
    return {
        "n_vertices": n_vertices,
        "n_finite_vertices": len(vertices),
        "implicit_infinity_index": len(vertices),
        "n_faces": n_faces,
        "n_finite_faces": len(triangles),
        "n_infinity_faces": n_faces - len(triangles),
        "n_edges": n_edges,
        "euler_characteristic": n_vertices - n_edges + n_faces,
        "vertex_degrees": sorted(degrees),
        "boundary_triangulation": boundary,
    }


@dataclass(frozen=True)
class OptimizationTrial:
    """One run; solver convergence and endpoint validation are independent.

    ``function_evals`` is SciPy's reported work (including its polish).
    ``verification_evals`` counts subsequent canonical volume evaluations.
    Legacy manually constructed records have no fresh validation evidence.
    """

    trial: int
    volume: float | None
    params: np.ndarray
    success: bool
    message: str
    iterations: int
    function_evals: int
    verification_evals: int = 0
    validation: Mapping[str, object] | None = None

    def as_dict(self) -> dict:
        return {
            "trial": self.trial,
            "volume": self.volume,
            "valid": self.volume is not None,
            "params": self.params.tolist(),
            "success": self.success,
            "message": self.message,
            "iterations": self.iterations,
            "function_evals": self.function_evals,
            "verification_evals": self.verification_evals,
            "validation": dict(self.validation) if self.validation is not None else {
                "status": "not_checked",
                "reason": "No endpoint verification evidence was supplied",
                "cached_objective": None,
                "cached_objective_repr": None,
                "objective_difference": None,
                "invalid_params_repr": None,
                "polish": None,
            },
        }


@dataclass(frozen=True)
class _EndpointCheck:
    params: np.ndarray
    volume: float | None = None
    finite_vertices: np.ndarray | None = None
    triangulation: np.ndarray | None = None
    structure: dict | None = None
    verification_evals: int = 0
    reason: str = ""
    invalid_params_repr: str | None = None


def _check_endpoint(raw_params, n_vertices: int, bounds) -> _EndpointCheck:
    """Validate an endpoint before it can displace an earlier valid trial."""
    empty = np.empty(0, dtype=np.float64)
    try:
        raw_array = np.asarray(raw_params)
        if raw_array.dtype.kind not in "fiu":
            raise ValueError("parameters must contain real numeric values, not strings, booleans or complex values")
        params = raw_array.astype(np.float64, copy=True)
    except (TypeError, ValueError, OverflowError) as exc:
        return _EndpointCheck(
            empty, reason=f"Invalid parameter data: {exc}",
            invalid_params_repr=repr(raw_params),
        )
    if params.ndim != 1 or not np.all(np.isfinite(params)):
        return _EndpointCheck(
            empty, reason="Parameters must be a finite one-dimensional array",
            invalid_params_repr=repr(raw_params),
        )
    if params.size != len(bounds):
        return _EndpointCheck(params, reason=f"Expected {len(bounds)} parameters")
    limits = np.asarray(bounds, dtype=np.float64)
    if np.any(params < limits[:, 0]) or np.any(params > limits[:, 1]):
        return _EndpointCheck(params, reason="Parameters lie outside the search bounds")

    evaluations = 0
    try:
        vertices = parameters_to_complex(params, n_vertices)
        evaluations += 1
        volume = float(ideal_poly_volume_via_delaunay(vertices, mode="bloch_wigner"))
        if not np.isfinite(volume) or volume <= 0:
            return _EndpointCheck(
                params, verification_evals=evaluations,
                reason="Canonical endpoint volume must be finite and positive",
            )
        triangles = delaunay_triangulation_indices(vertices)
        structure = analyze_ideal_polyhedron_structure(vertices, triangles)
    except (QhullError, ValueError, FloatingPointError, OverflowError, ZeroDivisionError) as exc:
        return _EndpointCheck(
            params, verification_evals=evaluations,
            reason=f"Endpoint geometry failed: {type(exc).__name__}: {exc}",
        )
    return _EndpointCheck(
        params, volume, vertices, triangles, structure, evaluations,
        "Canonical volume and complete boundary reconstruction passed",
    )


def _cached_objective_record(value) -> tuple[float | None, str | None]:
    """Retain malformed/nonfinite cached scores as diagnostics, never JSON NaN."""
    try:
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise ValueError("cached objective is not a real scalar")
        number = float(value)
        if np.isfinite(number):
            return number, None if value == number else repr(value)
    except (TypeError, ValueError, OverflowError):
        pass
    return None, repr(value)


@dataclass(frozen=True)
class PolyhedronOptimizationResult:
    """Best configuration and all trial summaries."""

    n_vertices: int
    best_volume: float
    best_params: np.ndarray
    finite_vertices: np.ndarray
    finite_triangulation: np.ndarray
    structure: dict
    trials: tuple[OptimizationTrial, ...]

    @property
    def boundary_triangulation(self) -> np.ndarray:
        return self.structure["boundary_triangulation"]


def optimization_result_to_dict(
    result: PolyhedronOptimizationResult,
    *,
    source: str,
    timestamp: str | None = None,
    settings: Mapping[str, object] | None = None,
) -> dict:
    """Serialize an optimization result using shared CLI/GUI schema v2.

    ``source`` identifies the adapter that initiated the run. Additional run
    settings are nested under ``metadata.settings`` so callers cannot replace
    schema-owned fields accidentally.
    """
    if not source or not source.strip():
        raise ValueError("source must be a nonempty string")

    structure = {
        key: value
        for key, value in result.structure.items()
        if key != "boundary_triangulation"
    }
    finite = result.finite_triangulation.astype(int, copy=False).tolist()
    boundary = result.boundary_triangulation.astype(int, copy=False).tolist()
    volumes = [
        float(trial.volume) for trial in result.trials if trial.volume is not None
    ]
    run_settings = dict(settings or {})
    metadata = {
        "timestamp": timestamp or datetime.now().isoformat(),
        "n_vertices": int(result.n_vertices),
        "objective": "vectorized_scipy_bloch_wigner",
        "implicit_infinity_index": int(len(result.finite_vertices)),
        "settings": run_settings,
    }
    # Preserve the nested settings namespace and the legacy adapter aliases.
    # Invalid diagnostic coordinates are quarantined before trial creation;
    # the final strict-JSON check also rejects invalid manually built records.
    for legacy_key in ("n_trials", "maxiter", "popsize", "workers", "seed_base"):
        if legacy_key in run_settings:
            metadata[legacy_key] = run_settings[legacy_key]
    payload = {
        "schema_version": 2,
        "source": source.strip(),
        "metadata": metadata,
        "best": {
            "volume": float(result.best_volume),
            "params": result.best_params.tolist(),
            "vertices_real": result.finite_vertices.real.tolist(),
            "vertices_imag": result.finite_vertices.imag.tolist(),
            "structure": structure,
            # Historical consumers used ``triangulation`` for the finite disk.
            "triangulation": finite,
            "finite_delaunay_triangulation": finite,
            "boundary_triangulation": boundary,
        },
        "statistics": {
            "n_vertices": int(result.n_vertices),
            "n_faces": int(structure["n_faces"]),
            "n_finite_faces": int(structure["n_finite_faces"]),
            "best_volume": float(result.best_volume),
            "mean_volume": float(np.mean(volumes)),
            "std_volume": float(np.std(volumes)),
            "all_volumes": volumes,
            "n_valid_trials": len(volumes),
            "n_invalid_trials": len(result.trials) - len(volumes),
            "verification_evals": sum(trial.verification_evals for trial in result.trials),
        },
        "all_trials": [trial.as_dict() for trial in result.trials],
    }
    # Both adapters use this owner. Reject undefined values before either can
    # emit permissive, nonstandard JSON through a default json.dump call.
    json.dumps(payload, allow_nan=False)
    return payload


def optimize_ideal_polyhedron(
    n_vertices: int,
    *,
    n_trials: int = 10,
    maxiter: int = 200,
    popsize: int = 15,
    seed: int = 42,
    workers: int = 1,
    trial_callback: Callable[[OptimizationTrial], None] | None = None,
) -> PolyhedronOptimizationResult:
    """Maximize ideal-polyhedron volume with repeated differential evolution.

    ``popsize`` retains SciPy's meaning: it is a multiplier of the parameter
    dimension, not an absolute population count.  ``workers=-1`` uses every
    available CPU; values greater than one use that many worker processes for
    differential evolution.  L-BFGS-B polishing remains serial because this
    fine-grained objective costs less than repeated process dispatch.

    Every candidate is re-evaluated and its boundary validated before ranking.
    A valid candidate from an unconverged run remains usable with
    ``trial.success=False``. No global-optimum certificate is implied.
    Each callback receives a detached snapshot, including its parameter array
    and validation diagnostics; edits to it do not alter verified results.
    """
    if n_vertices < 4:
        raise ValueError("n_vertices must be at least 4")
    if n_trials < 1:
        raise ValueError("n_trials must be at least 1")
    if maxiter < 1:
        raise ValueError("maxiter must be at least 1")
    if popsize < 1:
        raise ValueError("popsize must be at least 1")
    if workers == 0 or workers < -1:
        raise ValueError("workers must be -1 or a positive integer")

    n_free = n_vertices - 3
    bounds = [(0.1, np.pi - 0.1), (0.0, 2.0 * np.pi)] * n_free
    objective = partial(negative_volume_objective, n_vertices=n_vertices)

    trials: list[OptimizationTrial] = []
    best_volume = -np.inf
    best_params: np.ndarray | None = None
    best_endpoint: _EndpointCheck | None = None
    for trial_index in range(n_trials):
        serial_polish = workers != 1
        result = differential_evolution(
            objective,
            bounds,
            maxiter=maxiter,
            popsize=popsize,
            seed=seed + trial_index,
            polish=not serial_polish,
            disp=False,
            workers=workers,
            updating="deferred" if workers != 1 else "immediate",
        )
        if serial_polish:
            endpoint, verification_evals, polish = _serially_polish_differential_evolution_result(
                result,
                objective,
                bounds,
                n_vertices=n_vertices,
            )
        else:
            endpoint = _check_endpoint(result.x, n_vertices, bounds)
            verification_evals = endpoint.verification_evals
            polish = None  # SciPy's built-in polish is inside the returned DE result.
        objective_value, objective_repr = _cached_objective_record(result.fun)
        objective_difference = None
        if endpoint.volume is not None and objective_value is not None:
            difference = abs(objective_value + endpoint.volume)
            objective_difference = difference if np.isfinite(difference) else None
        trial = OptimizationTrial(
            trial=trial_index + 1,
            volume=endpoint.volume,
            params=endpoint.params,
            success=bool(result.success),
            message=str(result.message),
            iterations=int(result.nit),
            function_evals=int(result.nfev),
            verification_evals=verification_evals,
            validation={
                "status": "verified" if endpoint.volume is not None else "rejected",
                "reason": endpoint.reason,
                "cached_objective": objective_value,
                "cached_objective_repr": objective_repr,
                "objective_difference": objective_difference,
                "invalid_params_repr": endpoint.invalid_params_repr,
                "polish": polish,
            },
        )
        trials.append(trial)
        if trial_callback is not None:
            trial_callback(deepcopy(trial))
        if trial.volume is not None and trial.volume > best_volume:
            best_volume = trial.volume
            best_params = trial.params.copy()
            best_endpoint = endpoint

    if best_params is None or not np.isfinite(best_volume) or best_volume <= 0.0:
        raise RuntimeError("optimization did not produce a valid configuration")

    assert best_endpoint is not None
    return PolyhedronOptimizationResult(
        n_vertices=n_vertices,
        best_volume=best_volume,
        best_params=best_params,
        finite_vertices=best_endpoint.finite_vertices,
        finite_triangulation=best_endpoint.triangulation,
        structure=best_endpoint.structure,
        trials=tuple(trials),
    )


__all__ = [
    "OBJECTIVE_PENALTY",
    "OptimizationTrial",
    "PolyhedronOptimizationResult",
    "analyze_ideal_polyhedron_structure",
    "complete_boundary_triangulation",
    "negative_volume_objective",
    "optimize_ideal_polyhedron",
    "optimization_result_to_dict",
    "parameters_to_complex",
    "spherical_to_complex",
]
