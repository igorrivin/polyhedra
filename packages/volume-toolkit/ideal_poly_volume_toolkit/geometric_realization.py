"""Numerical planar development of compatible, oriented triangle angles.

Angle feasibility alone does not imply closure or an embedded convex surface.
"""

from collections import deque
from numbers import Integral
from typing import Dict, List, Optional, Set, Tuple

import numpy as np


def realize_from_angles_rigid(
    triangles: List[Tuple[int, int, int]],
    angles: np.ndarray,
    boundary_vertices: Optional[Set[int]] = None,
    verbose: bool = False,
) -> Dict:
    """Develop coherently oriented triangles by the law of sines.

    ``angles[t, k]`` is the angle at ``triangles[t][k]``, in radians. The
    triangle complex must be connected across edges, with at most two faces
    per edge and opposite directions on a shared edge. Vertex labels may be
    arbitrary integers. ``boundary_vertices`` is retained for API compatibility;
    the development itself uses the supplied faces and angles.

    Anchor the lexicographically first actual edge at 0 and 1, and choose the
    orientation of every new triangle from its cyclic vertex order. Success
    requires finite distinct vertices, positive face orientations, angle
    residuals and relative developing-map closure residuals below 1e-8.
    These are floating-point local checks, not a global embedding, Delaunay,
    convexity, or exact-existence certificate. The returned ``vertex_list``
    determines the row order of ``points`` even for nonconsecutive labels.

    Invalid face/angle data raise ValueError. Disconnected or incompatible
    development returns ``success=False`` with a diagnostic message.
    """
    faces = []
    for face in triangles:
        if len(face) != 3 or any(
            not isinstance(v, Integral) or isinstance(v, (bool, np.bool_))
            for v in face
        ):
            raise ValueError("each triangle must contain three integer labels")
        face = tuple(map(int, face))
        if len(set(face)) != 3:
            raise ValueError("each triangle must contain three distinct vertices")
        faces.append(face)
    if not faces:
        raise ValueError("triangles must be nonempty")
    if len({tuple(sorted(face)) for face in faces}) != len(faces):
        raise ValueError("triangles must not contain duplicate faces")
    angles = np.asarray(angles, dtype=float)
    if angles.shape != (len(faces), 3):
        raise ValueError("angles must have shape (n_triangles, 3)")
    if not np.all(np.isfinite(angles)) or np.any(angles <= 0) or np.any(angles >= np.pi):
        raise ValueError("angles must be finite and strictly between zero and pi")
    if not np.allclose(angles.sum(axis=1), np.pi, rtol=0, atol=1e-10):
        raise ValueError("each triangle's angles must sum to pi")

    edge_faces = {}
    for tid, face in enumerate(faces):
        for k in range(3):
            a, b = face[k], face[(k + 1) % 3]
            key = tuple(sorted((a, b)))
            incidences = edge_faces.setdefault(key, [])
            if len(incidences) == 2:
                raise ValueError("an edge must have at most two incident faces")
            if incidences and incidences[0][1:] == (a, b):
                raise ValueError("shared edges require coherent face orientations")
            incidences.append((tid, a, b))

    vertex_list = sorted({v for face in faces for v in face})
    positions = {}
    anchor_a, anchor_b = min(edge_faces)
    seed = min(
        (tid for tid, _, _ in edge_faces[(anchor_a, anchor_b)]),
        key=lambda tid: tuple(sorted(faces[tid])),
    )
    positions[anchor_a], positions[anchor_b] = 0j, 1 + 0j

    def third_position(tid, a, b, c):
        face = faces[tid]
        angle_a = angles[tid, face.index(a)]
        angle_b = angles[tid, face.index(b)]
        angle_c = angles[tid, face.index(c)]
        sign = 1 if face[(face.index(a) + 1) % 3] == b else -1
        # Multiplying the known edge by this complex ratio supplies both scale
        # and orientation; cyclically rotating a face leaves the ratio unchanged.
        ratio = np.sin(angle_b) / np.sin(angle_c)
        rotation = complex(np.cos(angle_a), sign * np.sin(angle_a))
        return positions[a] + (positions[b] - positions[a]) * ratio * rotation

    seed_c = next(v for v in faces[seed] if v not in (anchor_a, anchor_b))
    positions[seed_c] = third_position(seed, anchor_a, anchor_b, seed_c)
    queue = deque([seed])
    developed = {seed}
    closure_error = 0.0
    relative_closure_error = 0.0
    while queue:
        tid = queue.popleft()
        face = faces[tid]
        for k in range(3):
            a, b = face[k], face[(k + 1) % 3]
            for other, _, _ in edge_faces[tuple(sorted((a, b)))]:
                if other in developed:
                    continue
                c = next(v for v in faces[other] if v not in (a, b))
                candidate = third_position(other, a, b, c)
                if c in positions:
                    error = abs(candidate - positions[c])
                    scale = max(abs(positions[b] - positions[a]), abs(candidate - positions[a]))
                    closure_error = max(closure_error, error)
                    relative_closure_error = max(
                        relative_closure_error, error / scale if scale > 0 else np.inf
                    )
                else:
                    positions[c] = candidate
                developed.add(other)
                queue.append(other)

    if len(developed) != len(faces):
        return {
            "success": False,
            "points": None,
            "vertex_list": vertex_list,
            "placed": sorted(positions),
            "remaining": sorted(set(vertex_list) - positions.keys()),
            "message": "Triangle complex is disconnected across edges",
            "evidence_status": "numerical_development",
            "embedding_checked": False,
        }

    points = np.array([[positions[v].real, positions[v].imag] for v in vertex_list])
    finite = bool(np.all(np.isfinite(points)))
    distinct = finite and len(np.unique(points, axis=0)) == len(points)
    max_angle_error = np.inf
    orientation_consistent = False
    if finite:
        errors = []
        oriented_areas = []
        for tid, face in enumerate(faces):
            z = [positions[v] for v in face]
            cross = ((z[1] - z[0]).conjugate() * (z[2] - z[0])).imag
            oriented_areas.append(cross)
            for k in range(3):
                product = (z[(k + 1) % 3] - z[k]).conjugate() * (z[(k + 2) % 3] - z[k])
                measured = np.arctan2(abs(product.imag), product.real)
                errors.append(abs(measured - angles[tid, k]))
        max_angle_error = float(max(errors))
        orientation_consistent = bool(all(area > 0 for area in oriented_areas))
    tolerance = 1e-8
    success = bool(
        finite and distinct and orientation_consistent
        and max_angle_error <= tolerance and relative_closure_error <= tolerance
    )
    message = (
        "Numerical angle development passed local residual checks"
        if success else "Numerical angle development failed local residual checks"
    )
    if verbose:
        print(f"{message}; max angle error={max_angle_error:.3e}, "
              f"relative closure error={relative_closure_error:.3e}")
    return {
        "success": success,
        "points": points,
        "vertex_list": vertex_list,
        "message": message,
        "max_angle_error": max_angle_error,
        "max_angle_error_degrees": float(np.degrees(max_angle_error)),
        "closure_error": float(closure_error),
        "relative_closure_error": float(relative_closure_error),
        "orientation_consistent": orientation_consistent,
        "vertices_distinct": bool(distinct),
        "residual_tolerance": tolerance,
        "evidence_status": "numerical_development",
        "embedding_checked": False,
    }
