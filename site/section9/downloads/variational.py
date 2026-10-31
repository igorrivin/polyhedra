"""Small dense operators for the monograph's planar angle coordinates.

For a positively oriented face (a, b, c), the angle at a changes by
u_b - u_c, and cyclically. Boundary values of u are fixed to zero. These
are leading--trailing coordinates, not vertex positions or log lengths.

The routines evaluate finite-dimensional identities; they do not certify
disk topology, an embedding, global optimality, or interval enclosures.
The caller must supply the geometric/domain hypotheses of Section 9.
Dense matrices deliberately target small worked examples, not large solves.
"""

from __future__ import annotations

import numpy as np


def _faces(triangles):
    raw = np.asarray(triangles)
    if raw.ndim != 2 or raw.shape[1] != 3 or not len(raw):
        raise ValueError("triangles must be a nonempty (m, 3) integer array")
    if not np.issubdtype(raw.dtype, np.integer) or np.any(raw < 0):
        raise ValueError("triangle labels must be nonnegative integers")
    if np.any(raw > np.iinfo(np.int64).max):
        raise ValueError("triangle labels must be representable as signed int64")
    faces = raw.astype(np.int64, copy=False)
    if any(len(set(t)) != 3 for t in faces):
        raise ValueError("a triangle must have three distinct vertices")
    if len({tuple(sorted(t)) for t in faces}) != len(faces):
        raise ValueError("duplicate triangles are not allowed")
    return faces


def _angles(values, shape):
    angles = np.asarray(values, dtype=float)
    if angles.shape != shape or not np.all(np.isfinite(angles)):
        raise ValueError("angles must be a finite array with one row per face")
    if np.any(angles <= 0) or np.any(angles >= np.pi):
        raise ValueError("all corner angles must lie strictly between 0 and pi")
    if not np.allclose(angles.sum(axis=1), np.pi, rtol=0, atol=1e-10):
        raise ValueError("the angles in each triangle must sum to pi")
    return angles


def _mesh(points, triangles):
    points = np.asarray(points, dtype=float)
    faces = _faces(triangles)
    if points.ndim != 2 or points.shape[1] != 2 or not np.all(np.isfinite(points)):
        raise ValueError("points must be a finite (n, 2) array")
    if np.max(faces) >= len(points):
        raise ValueError("triangle label lies outside the point array")
    p = points[faces]
    first, second = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]
    double_areas = first[:, 0] * second[:, 1] - first[:, 1] * second[:, 0]
    if np.any(double_areas <= 0) or not np.all(np.isfinite(double_areas)):
        raise ValueError("faces must be nondegenerate and counterclockwise")
    return points, faces, double_areas


def corner_angles(points, triangles):
    """Return binary64 geometric angles in the vertex order of each face."""
    points, faces, _ = _mesh(points, triangles)
    p = points[faces]
    angles = np.empty(faces.shape, dtype=float)
    for k in range(3):
        a = p[:, (k + 1) % 3] - p[:, k]
        b = p[:, (k + 2) % 3] - p[:, k]
        cross = a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]
        angles[:, k] = np.arctan2(cross, np.sum(a * b, axis=1))
    return _angles(angles, faces.shape)


def leading_trailing_matrix(triangles, interior_vertices):
    """Return C with alpha(u).ravel() = alpha(0).ravel() + C @ u.

    Interior vertex order determines column order. Edge incidence and winding
    are checked, but this routine is not a complete disk-topology validator.
    """
    faces = _faces(triangles)
    interior = np.asarray(interior_vertices)
    if interior.ndim != 1 or (interior.size and not np.issubdtype(interior.dtype, np.integer)):
        raise ValueError("interior_vertices must be a one-dimensional integer list")
    if interior.size and (np.any(interior < 0) or np.any(interior > np.iinfo(np.int64).max)):
        raise ValueError("interior vertex labels must be representable as nonnegative signed int64")
    interior = interior.astype(np.int64)
    if len(set(interior)) != len(interior):
        raise ValueError("interior vertex labels must be distinct")
    edges = {}
    for face in faces:
        for k in range(3):
            a, b = int(face[k]), int(face[(k + 1) % 3])
            edges.setdefault(tuple(sorted((a, b))), []).append((a, b))
    boundary = set()
    for edge, uses in edges.items():
        if len(uses) == 1:
            boundary.update(edge)
        elif len(uses) != 2 or uses[0] != uses[1][::-1]:
            raise ValueError("edge incidence must be manifold and coherently oriented")
    expected = set(faces.ravel()) - boundary
    if set(interior) != expected:
        raise ValueError("interior_vertices must be exactly the nonboundary vertices")
    index = {int(v): j for j, v in enumerate(interior)}
    matrix = np.zeros((faces.size, len(interior)))
    for t, face in enumerate(faces):
        for k in range(3):
            for vertex, sign in ((face[(k + 1) % 3], 1), (face[(k + 2) % 3], -1)):
                if vertex in index:
                    matrix[3 * t + k, index[vertex]] = sign
    return matrix


def deformed_angles(base_angles, incidence, u):
    """Apply a leading--trailing increment and reject the nonpositive domain."""
    base = np.asarray(base_angles, dtype=float)
    if base.ndim != 2 or base.shape[1] != 3:
        raise ValueError("base_angles must have shape (m, 3)")
    base = _angles(base, base.shape)
    c = np.asarray(incidence, dtype=float)
    u = np.asarray(u, dtype=float)
    if c.ndim != 2 or c.shape[0] != base.size or u.shape != (c.shape[1],):
        raise ValueError("incidence and parameter dimensions are incompatible")
    if not np.all(np.isfinite(c)) or not np.all(np.isfinite(u)):
        raise ValueError("incidence and parameters must be finite")
    return _angles((base.ravel() + c @ u).reshape(base.shape), base.shape)


def angle_volume(base_angles, incidence, u):
    """Evaluate sum Lambda(alpha) using the canonical binary64 BW kernel.

    Each positive angle triple defines a tetrahedral shape in the upper half
    plane, even when the complete angle structure has not geometrically closed.
    This is a floating-point evaluation, not an exact or interval volume.
    """
    from .geometry import bloch_wigner

    angles = deformed_angles(base_angles, incidence, u)
    a, b, c = angles.T
    shapes = np.sin(b) / np.sin(c) * np.exp(1j * a)
    if not np.all(np.isfinite(shapes)):
        raise ValueError("tetrahedral shape is outside the binary64 evaluation range")
    return float(np.sum(bloch_wigner(shapes)))


def angle_volume_derivatives(base_angles, incidence, u):
    """Return gradient and Hessian with respect to the supplied u coordinates."""
    angles = deformed_angles(base_angles, incidence, u).ravel()
    c = np.asarray(incidence, dtype=float)
    gradient = c.T @ (-np.log(2 * np.sin(angles)))
    hessian = -(c.T @ ((1 / np.tan(angles))[:, None] * c))
    return gradient, hessian


def cotangent_stiffness(n_vertices, triangles, angles):
    """Assemble full L from one half cotangent per opposite corner.

    L may have negative individual edge weights on a non-Delaunay mesh.
    Its finite-element interpretation requires geometrically realized angles.
    """
    faces = _faces(triangles)
    if isinstance(n_vertices, bool) or not isinstance(n_vertices, (int, np.integer)):
        raise ValueError("n_vertices must be an integer")
    if n_vertices <= int(np.max(faces)):
        raise ValueError("n_vertices does not cover all triangle labels")
    angles = _angles(angles, faces.shape)
    matrix = np.zeros((n_vertices, n_vertices))
    for face, alpha in zip(faces, angles):
        for k in range(3):
            i, j = face[(k + 1) % 3], face[(k + 2) % 3]
            weight = 0.5 / np.tan(alpha[k])
            matrix[i, i] += weight
            matrix[j, j] += weight
            matrix[i, j] -= weight
            matrix[j, i] -= weight
    return matrix


def fem_stiffness(points, triangles):
    """Independently assemble integral grad(phi_i).grad(phi_j) on the mesh."""
    points, faces, double_areas = _mesh(points, triangles)
    matrix = np.zeros((len(points), len(points)))
    for face, double_area in zip(faces, double_areas):
        p = points[face]
        gradients = np.array([
            [p[(k + 1) % 3, 1] - p[(k + 2) % 3, 1],
             p[(k + 2) % 3, 0] - p[(k + 1) % 3, 0]]
            for k in range(3)
        ]) / double_area
        local = (double_area / 2) * (gradients @ gradients.T)
        matrix[np.ix_(face, face)] += local
    return matrix


def schur_complement(matrix, eliminate):
    """Eliminate selected indices by a linear solve, keeping the others in order.

    This is dense floating-point linear algebra. Singular eliminated blocks
    raise numpy.linalg.LinAlgError rather than being silently regularized.
    """
    matrix = np.asarray(matrix, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] != matrix.shape[1] or not np.all(np.isfinite(matrix)):
        raise ValueError("matrix must be finite and square")
    if not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-12):
        raise ValueError("matrix must be symmetric")
    eliminate = np.asarray(eliminate)
    if eliminate.ndim != 1 or (eliminate.size and not np.issubdtype(eliminate.dtype, np.integer)):
        raise ValueError("eliminate must be a one-dimensional integer list")
    if eliminate.size and (np.any(eliminate < 0) or np.any(eliminate > np.iinfo(np.int64).max)):
        raise ValueError("elimination labels must be representable as nonnegative signed int64")
    eliminate = eliminate.astype(np.int64)
    if len(set(eliminate)) != len(eliminate) or np.any(eliminate < 0) or np.any(eliminate >= len(matrix)):
        raise ValueError("elimination indices must be distinct and within the matrix")
    retained = np.array([i for i in range(len(matrix)) if i not in set(eliminate)], dtype=int)
    result = matrix[np.ix_(retained, retained)].copy()
    if not len(eliminate):
        return result
    # NumPy documents multi-RHS solve directly; do not form an explicit inverse:
    # https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html
    coupling = matrix[np.ix_(eliminate, retained)]
    return result - coupling.T @ np.linalg.solve(matrix[np.ix_(eliminate, eliminate)], coupling)
