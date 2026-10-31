"""
Self-contained module for checking if ideal polyhedron volume exceeds threshold.

Given finite complex vertices, with infinity explicit or implicit, determines
whether the volume of the associated ideal hyperbolic polyhedron is greater
than a specified threshold.

The default uses the toolkit's canonical binary64 Bloch-Wigner kernel.
An explicit Fourier term count selects a truncated approximation. Neither
path provides an exact value or a rigorous enclosure for threshold decisions.

Usage:
    from ideal_poly_volume_toolkit.volume_threshold import volume_exceeds_threshold

    vertices = [0+0j, 1+0j, 0.5+0.5j]  # 0, 1, ∞ implicit
    result = volume_exceeds_threshold(vertices, threshold=1.0)
    # Returns: True if volume > threshold, False otherwise
"""

import numpy as np
from numbers import Real
from scipy.spatial import ConvexHull, Delaunay

if __package__:
    from .geometry import bloch_wigner
else:  # pragma: no cover - direct-script compatibility
    from geometry import bloch_wigner


def _validated_vertices(vertices):
    """Validate the API's finite complex vertices and optional infinity point."""
    values = np.asarray(vertices, dtype=np.complex128)
    if values.ndim != 1:
        raise ValueError("vertices must be a one-dimensional complex array")
    if np.any(np.isnan(values.real)) or np.any(np.isnan(values.imag)):
        raise ValueError("vertices must not contain NaN")
    infinite = np.isinf(values.real) | np.isinf(values.imag)
    if np.count_nonzero(infinite) > 1:
        raise ValueError("at most one vertex at infinity is allowed")
    if np.count_nonzero(~infinite) < 3:
        raise ValueError("at least three finite vertices are required")
    return values


def _validated_series_terms(series_terms):
    if series_terms is not None and (
        isinstance(series_terms, (bool, np.bool_))
        or not isinstance(series_terms, (int, np.integer))
        or series_terms < 1
    ):
        raise ValueError("series_terms must be a positive integer or None")
    return series_terms


# ============================================================================
# Stereographic projection utilities
# ============================================================================

def lift_to_sphere_with_inf(W: np.ndarray) -> np.ndarray:
    """
    Lift complex points to the unit sphere via inverse stereographic projection.

    Maps C ∪ {∞} → S² where:
    - Finite points w → (2Re(w)/(|w|²+1), 2Im(w)/(|w|²+1), (|w|²-1)/(|w|²+1))
    - ∞ → (0, 0, 1) (north pole)

    Args:
        W: Complex numpy array of vertices

    Returns:
        N x 3 array of points on unit sphere
    """
    P = np.zeros((W.shape[0], 3), dtype=np.float64)
    is_inf = ~np.isfinite(W.real) | ~np.isfinite(W.imag)
    F = ~is_inf
    w = W[F]
    r2 = (w.real**2 + w.imag**2)
    denom = r2 + 1.0
    P[F, 0] = 2.0 * w.real / denom
    P[F, 1] = 2.0 * w.imag / denom
    P[F, 2] = (r2 - 1.0) / denom
    P[is_inf] = np.array([0.0, 0.0, 1.0])
    return P


def inverse_stereographic_from_sphere_pts(X: np.ndarray) -> np.ndarray:
    """
    Project points from sphere back to complex plane via stereographic projection.

    Maps S² → C via w = (x + iy)/(1 - z)

    Args:
        X: N x 3 array of points on sphere

    Returns:
        Complex numpy array
    """
    x, y, z = X[:, 0], X[:, 1], X[:, 2]
    denom = (1.0 - z)
    return (x / denom) + 1j * (y / denom)


# ============================================================================
# Triangulation methods
# ============================================================================

def hull_tris_projected_back(W: np.ndarray, index_inf: int = 0) -> list:
    """
    Compute triangulation by lifting to sphere, taking convex hull, projecting back.

    This handles vertices including ∞ by working on the sphere where all points
    are finite. Triangles containing ∞ are excluded from the result.

    Args:
        W: Complex array of all vertices (including ∞)
        index_inf: Index of the vertex at infinity

    Returns:
        List of triangles, each a tuple of 3 complex numbers
    """
    P3 = lift_to_sphere_with_inf(W)
    hull = ConvexHull(P3)
    tris = []
    for f in hull.simplices:
        if index_inf in f:
            continue
        X = P3[np.asarray(f)]
        tri = tuple(inverse_stereographic_from_sphere_pts(X))
        tris.append(tri)
    return tris


def delaunay_triangulation_indices(z_finite: np.ndarray) -> np.ndarray:
    """
    Compute Delaunay triangulation of finite complex points.

    Args:
        z_finite: Complex array of finite vertices (no ∞)

    Returns:
        M x 3 array of triangle vertex indices
    """
    pts = np.column_stack([z_finite.real, z_finite.imag])
    tri = Delaunay(pts)
    return tri.simplices.astype(np.int64)


# ============================================================================
# Lobachevsky function (Λ) and triangle volume
# ============================================================================

def _lob_value_series(theta: float, n: int = 64) -> float:
    """
    Compute Lobachevsky function Λ(θ) via series expansion.

    Λ(θ) = -∫₀^θ log|2sin(t)| dt = (1/2) Σₖ₌₁^∞ sin(2kθ)/k²

    Args:
        theta: Angle in radians
        n: Number of terms in the finite approximation (default 64)

    Returns:
        Λ(θ) value
    """
    total = 0.0
    for k in range(1, n + 1):
        total += np.sin(2 * k * theta) / (k * k)
    return 0.5 * total


def _angles_for_triangle(z1, z2, z3):
    """
    Compute the three interior angles of a Euclidean triangle.

    Args:
        z1, z2, z3: Complex coordinates of triangle vertices

    Returns:
        Tuple of three angles (a1, a2, a3) in radians
    """
    def angle_at(a, b, c):
        u = np.array([(b - a).real, (b - a).imag])
        v = np.array([(c - a).real, (c - a).imag])
        dot = (u * v).sum()
        cross = u[0] * v[1] - u[1] * v[0]
        return np.arctan2(abs(cross), dot)

    return (angle_at(z1, z2, z3),
            angle_at(z2, z3, z1),
            angle_at(z3, z1, z2))


def triangle_volume(z1, z2, z3, series_terms=None):
    """
    Compute volume of ideal hyperbolic tetrahedron from base triangle.

    For a triangle with vertices z1, z2, z3 in the complex plane, the volume
    of the ideal tetrahedron with base vertices at z1, z2, z3 and apex at ∞
    is given by the sum of Lobachevsky functions at the three interior angles:

    V = Λ(α₁) + Λ(α₂) + Λ(α₃)

    Args:
        z1, z2, z3: Complex coordinates of triangle vertices
        series_terms: Number of terms in the Lobachevsky series. If None
            (the default), use the accurate Bloch-Wigner closed form.

    Returns:
        Volume of the ideal tetrahedron
    """
    _validated_series_terms(series_terms)
    if series_terms is None:
        denominator = z2 - z3
        if denominator == 0:
            return 0.0
        shape = (z1 - z3) / denominator
        return abs(bloch_wigner(shape))

    a1, a2, a3 = _angles_for_triangle(z1, z2, z3)
    return (_lob_value_series(a1, int(series_terms)) +
            _lob_value_series(a2, int(series_terms)) +
            _lob_value_series(a3, int(series_terms)))


# ============================================================================
# Volume computation strategies
# ============================================================================

def compute_volume_hull_method(vertices: np.ndarray, index_inf: int = None,
                               series_terms=None) -> float:
    """
    Compute polyhedron volume using convex hull method.

    This method:
    1. Lifts all vertices to sphere (including ∞ → north pole)
    2. Computes convex hull on sphere
    3. Projects triangles back to complex plane (excluding those containing ∞)
    4. Sums volumes of all triangles

    Args:
        vertices: Complex array of all vertices
        index_inf: Index of vertex at infinity (if None, searches for inf)

    Returns:
        Total volume
    """
    vertices = _validated_vertices(vertices)
    _validated_series_terms(series_terms)
    if index_inf is None:
        # Find infinity vertex
        is_inf = ~np.isfinite(vertices.real) | ~np.isfinite(vertices.imag)
        if not np.any(is_inf):
            raise ValueError("No vertex at infinity found")
        index_inf = np.where(is_inf)[0][0]

    tris = hull_tris_projected_back(vertices, index_inf=index_inf)
    total = 0.0
    for (z1, z2, z3) in tris:
        total += triangle_volume(z1, z2, z3, series_terms=series_terms)
    return total


def compute_volume_delaunay_method(vertices: np.ndarray, series_terms=None) -> float:
    """
    Compute polyhedron volume using Delaunay triangulation.

    This method:
    1. Takes only finite vertices
    2. Computes Delaunay triangulation in the plane
    3. Sums volumes of all triangles (implicitly with ∞ as apex)

    Note: This assumes ∞ is one of the vertices. All finite vertices
    are triangulated and each triangle forms a tetrahedron with ∞.

    Args:
        vertices: Complex array of all vertices (including ∞)

    Returns:
        Total volume
    """
    vertices = _validated_vertices(vertices)
    _validated_series_terms(series_terms)
    # Infinity is implicit when this direct helper receives only finite points.
    is_finite = np.isfinite(vertices.real) & np.isfinite(vertices.imag)
    z_finite = vertices[is_finite]

    if len(z_finite) < 3:
        raise ValueError("Need at least 3 finite vertices for triangulation")

    idx_tris = delaunay_triangulation_indices(z_finite)
    total = 0.0
    for (i, j, k) in idx_tris:
        z1, z2, z3 = z_finite[i], z_finite[j], z_finite[k]
        total += triangle_volume(z1, z2, z3, series_terms=series_terms)
    return total


# ============================================================================
# Main API
# ============================================================================

def compute_volume(vertices, method="auto", series_terms=None):
    """
    Compute volume of ideal hyperbolic polyhedron from vertex coordinates.

    The polyhedron is determined by vertices in C ∪ {∞}. The volume is
    computed by triangulating the finite vertices and summing the volumes
    of the resulting ideal tetrahedra.

    Args:
        vertices: Array-like of complex numbers and/or np.inf
                 Can include 0, 1, ∞, and additional points
        method: "auto", "hull", or "delaunay"
               - "auto": Use Delaunay if ∞ present, else hull
               - "hull": Lift to sphere, convex hull, project back
               - "delaunay": Delaunay triangulation; requires explicit ∞
        series_terms: Number of terms in the Lobachevsky series. If None
            (the default), use the accurate Bloch-Wigner closed form.

    Returns:
        Binary64 numerical volume. In auto/hull mode, infinity is implicit if
        omitted from the input; this API does not interpret a finite-only list as a
        different polyhedron without that infinity vertex.

    Examples:
        >>> # Tetrahedron with vertices at 0, 1, i, ∞
        >>> vertices = [0+0j, 1+0j, 1j, np.inf]
        >>> vol = compute_volume(vertices)

        >>> # Polyhedron with 7 vertices (0, 1, i, ∞ + 3 random)
        >>> vertices = [0+0j, 1+0j, 1j, np.inf, 0.5+0.3j, -0.2+0.7j, 0.8-0.1j]
        >>> vol = compute_volume(vertices)
    """
    vertices = _validated_vertices(vertices)
    _validated_series_terms(series_terms)

    # Check if infinity is present
    has_inf = np.any(~np.isfinite(vertices.real) | ~np.isfinite(vertices.imag))

    # Choose method
    if method == "auto":
        method = "delaunay" if has_inf else "hull"

    if method == "delaunay":
        if not has_inf:
            raise ValueError("Delaunay method requires vertex at infinity")
        return compute_volume_delaunay_method(vertices, series_terms=series_terms)
    elif method == "hull":
        if not has_inf:
            # Add infinity if not present
            vertices = np.append(vertices, np.inf)
        return compute_volume_hull_method(vertices, series_terms=series_terms)
    else:
        raise ValueError(f"Unknown method: {method}")


def volume_exceeds_threshold(vertices, threshold, series_terms=None):
    """
    Check if ideal polyhedron volume exceeds a threshold.

    This is the main API function. Given vertices (which implicitly or
    explicitly include ∞), compute the volume and check if
    it exceeds the given threshold.

    Args:
        vertices: Array-like of complex numbers (and optionally np.inf)
                 Infinity can be explicit or implicit; finite vertices are
                 used as supplied (0 and 1 are not inserted automatically).
        threshold: Real number to compare against

    Returns:
        The ordinary numerical comparison, not an interval-certified decision.
        Values near the threshold require a separately validated error bound.

    Examples:
        >>> # Check if tetrahedron volume > 1.0
        >>> vertices = [0+0j, 1+0j, 1j, np.inf]
        >>> result = volume_exceeds_threshold(vertices, 1.0)
        >>> print(result)  # True or False

        >>> # With additional vertices
        >>> vertices = [0+0j, 1+0j, 1j, np.inf, 0.5+0.5j, -0.3+0.8j]
        >>> result = volume_exceeds_threshold(vertices, 2.5)
    """
    if (
        isinstance(threshold, (bool, np.bool_))
        or not isinstance(threshold, Real)
        or not -float("inf") < threshold < float("inf")
    ):
        raise ValueError("threshold must be a finite real number")
    volume = compute_volume(vertices, series_terms=series_terms)
    if not np.isfinite(volume):
        raise ValueError("volume evaluation must be finite before comparison")
    return bool(volume > threshold)


def get_volume(vertices, series_terms=None):
    """
    Convenience function to get a binary64 numerical volume value.

    Args:
        vertices: Array-like of complex numbers (and optionally np.inf)

    Returns:
        Volume as a float

    Examples:
        >>> vertices = [0+0j, 1+0j, 1j, np.inf]
        >>> vol = get_volume(vertices)
        >>> print(f"Volume: {vol:.6f}")
    """
    return compute_volume(vertices, series_terms=series_terms)
