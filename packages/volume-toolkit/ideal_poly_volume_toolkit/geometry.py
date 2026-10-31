from decimal import Decimal
from importlib import import_module
from numbers import Integral, Rational

import mpmath as mp
import numpy as np
from scipy.spatial import ConvexHull, Delaunay
from scipy.special import spence


_TORCH_PRIVATE_EXPORTS = frozenset(
    {
        "_LobFn",
        "_angles_for_triangle_torch",
        "_lob_value_series_torch",
    }
)


def _geometry_torch_module():
    """Load the optional differentiable H³ implementation on demand."""
    try:
        return import_module(".geometry_torch", __package__)
    except ModuleNotFoundError as exc:
        if exc.name == "torch":
            raise ImportError(
                "PyTorch-backed geometry requires the 'torch' extra; install it "
                "with `python -m pip install 'ideal_poly_volume_toolkit[torch]'`."
            ) from exc
        raise


def __getattr__(name: str):
    """Preserve the repository's historical private Torch imports lazily."""
    if name in _TORCH_PRIVATE_EXPORTS:
        return getattr(_geometry_torch_module(), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(set(globals()) | _TORCH_PRIVATE_EXPORTS)


def _as_complex_array(values) -> tuple[np.ndarray, bool]:
    """Return a complex128 ndarray and whether the input was scalar."""
    arr = np.asarray(values, dtype=np.complex128)
    return arr, arr.ndim == 0


def lift_to_sphere_with_inf(W: np.ndarray) -> np.ndarray:
    P = np.zeros((W.shape[0], 3), dtype=np.float64)
    is_inf = ~np.isfinite(W.real) | ~np.isfinite(W.imag)
    F = ~is_inf
    w = W[F]
    r2 = w.real**2 + w.imag**2
    denom = r2 + 1.0
    P[F, 0] = 2.0 * w.real / denom
    P[F, 1] = 2.0 * w.imag / denom
    P[F, 2] = (r2 - 1.0) / denom
    P[is_inf] = np.array([0.0, 0.0, 1.0])
    return P


def inverse_stereographic_from_sphere_pts(X: np.ndarray) -> np.ndarray:
    x, y, z = X[:, 0], X[:, 1], X[:, 2]
    denom = 1.0 - z
    return (x / denom) + 1j * (y / denom)


def stereographic_project_from_pole(
    points_sphere: np.ndarray,
    pole_index: int = 0,
) -> tuple[np.ndarray, np.ndarray]:
    """Project points on S² from one of the points to the complex plane.

    ``points_sphere[pole_index]`` is sent to infinity and omitted from the
    returned finite coordinates.  The second return value maps each projected
    coordinate back to its original row index.

    Rows are normalized first, so positive rescaling of sphere representatives
    does not change the result.  Coincident points are rejected explicitly;
    near-coincident but distinct points are projected without adding an
    absolute epsilon to the denominator.
    """
    points = np.asarray(points_sphere, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3:
        raise ValueError("points_sphere must have shape (N, 3)")
    if points.shape[0] < 2:
        raise ValueError("at least two sphere points are required")
    if not np.isfinite(points).all():
        raise ValueError("points_sphere must contain only finite values")

    row_scales = np.max(np.abs(points), axis=1)
    if np.any(row_scales == 0.0):
        raise ValueError("sphere representatives must be nonzero")
    scaled = points / row_scales[:, None]
    unit = scaled / np.linalg.norm(scaled, axis=1)[:, None]

    pole_index = int(pole_index)
    if pole_index < 0:
        pole_index += len(unit)
    if not 0 <= pole_index < len(unit):
        raise IndexError("pole_index is out of range")

    pole = unit[pole_index]

    # Construct the chart directly from a well-conditioned tangent basis at
    # the pole.  A Householder vector proportional to ``pole - north`` loses
    # its longitudinal component when the pole is within roughly sqrt(eps) of
    # the north pole, so the resulting transform need not actually send the
    # pole to north.  Projecting the least-aligned Cartesian axis into the
    # tangent plane keeps the normalization bounded away from zero instead.
    reference = np.eye(3)[int(np.argmin(np.abs(pole)))]
    tangent_real = reference - np.dot(reference, pole) * pole
    tangent_real /= np.linalg.norm(tangent_real)
    tangent_imag = np.cross(pole, tangent_real)
    tangent_imag /= np.linalg.norm(tangent_imag)

    original_indices = np.delete(np.arange(len(unit), dtype=np.int64), pole_index)
    finite = unit[original_indices]

    # For unit vectors this is exactly 1 - <point, pole>, evaluated as a
    # squared distance to avoid cancellation for points close to the pole.
    denominator = 0.5 * np.sum((finite - pole) ** 2, axis=1)
    if np.any(denominator == 0.0):
        raise ValueError("the projection pole is repeated in points_sphere")

    numerator = finite @ tangent_real + 1j * (finite @ tangent_imag)
    projected = numerator / denominator
    return projected.astype(np.complex128, copy=False), original_indices


def hull_tris_projected_back(W: np.ndarray, index_inf: int = 0) -> list:
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
    pts = np.column_stack([z_finite.real, z_finite.imag])
    tri = Delaunay(pts)
    return tri.simplices.astype(np.int64)


def _angles_for_triangle_np(z1, z2, z3):
    def angle_at(a, b, c):
        u = b - a
        v = c - a
        dot = u.real * v.real + u.imag * v.imag
        cross = u.real * v.imag - u.imag * v.real
        return np.arctan2(abs(cross), dot)

    return angle_at(z1, z2, z3), angle_at(z2, z3, z1), angle_at(z3, z1, z2)


def _lob_value_series_np(theta, n: int = 64):
    """Vectorized NumPy evaluation of the truncated Lobachevsky series."""
    if n < 1:
        raise ValueError("n must be a positive integer")
    theta_arr = np.asarray(theta, dtype=np.float64)
    k = np.arange(1, n + 1, dtype=np.float64).reshape((n,) + (1,) * theta_arr.ndim)
    return 0.5 * np.sum(np.sin(2 * k * theta_arr) / (k * k), axis=0)


def lob_fast(theta, n: int = 64):
    """Evaluate the Torch Lobachevsky kernel via the optional ``torch`` extra."""
    return _geometry_torch_module().lob_fast(theta, n)


def _precision_digits(dps):
    if isinstance(dps, bool) or not isinstance(dps, Integral) or dps < 1:
        raise ValueError("dps must be a positive integer")
    return int(dps)


def _finite_mpf(value):
    """Convert supported real scalars without an intermediate binary64 cast."""
    if isinstance(value, Integral):
        value = int(value)
    elif isinstance(value, Rational):
        value = mp.mpf(int(value.numerator)) / int(value.denominator)
    elif isinstance(value, Decimal):
        value = str(value)
    elif isinstance(value, np.floating):
        if not np.isfinite(value):
            raise ValueError("values must be finite and real")
        numerator, denominator = value.as_integer_ratio()
        value = mp.mpf(numerator) / denominator
    value = mp.mpf(value)
    if not mp.isfinite(value):
        raise ValueError("values must be finite and real")
    return value


def _finite_mpc(value):
    """Convert under the caller's precision, without a Python-complex cast."""
    if isinstance(value, (tuple, list)) and len(value) == 2:
        value = mp.mpc(_finite_mpf(value[0]), _finite_mpf(value[1]))
    elif isinstance(value, (complex, np.complexfloating)):
        value = mp.mpc(_finite_mpf(value.real), _finite_mpf(value.imag))
    elif isinstance(value, (Rational, Decimal, np.floating)):
        value = mp.mpc(_finite_mpf(value))
    else:
        value = mp.mpc(value)
    if not mp.isfinite(value):
        raise ValueError("coordinates must be finite")
    return value


def lobachevsky_mp(theta, dps: int = 120):
    """Evaluate Lambda(theta) as an ``mpmath.mpf`` at the requested precision.

    Decimal strings/Decimal, rational and NumPy real scalars, and existing mpf
    inputs are converted inside the precision context without a float cast.
    Python and NumPy floating inputs retain their represented binary values.
    This is arbitrary-precision floating-point evaluation, not exact arithmetic
    or a rigorous enclosure. Precision is restored even when evaluation fails.
    """
    # workdps restores the enclosing context, including on exceptions:
    # https://mpmath.org/doc/current/basics.html#temporarily-changing-the-precision
    # Lambda(theta) = Cl_2(2 theta) / 2:
    # https://mpmath.org/doc/current/functions/zeta.html#clausen-functions
    with mp.workdps(_precision_digits(dps)):
        theta = _finite_mpf(theta)
        return mp.clsin(2, 2 * theta) / 2


def lob_exact(theta, dps: int = 120):
    """Legacy alias for :func:`lobachevsky_mp`; the result is not exact.

    Retains the historical mpf return type while avoiding binary64 input
    conversion and persistent changes to mpmath's working precision.
    """
    return lobachevsky_mp(theta, dps=dps)


# ============================================================================
# Bloch-Wigner dilogarithm approach (faster and more accurate)
# ============================================================================


def bloch_wigner(z):
    """Evaluate the Bloch–Wigner dilogarithm in double precision.

    Parameters
    ----------
    z : complex or array-like of complex
        Finite cross-ratio value(s). Nonfinite inputs are rejected; an infinity
        limit is not inferred from a floating-point overflow.

    Returns
    -------
    float or numpy.ndarray
        A scalar for scalar input and an array of matching shape otherwise.

    Notes
    -----
    SciPy's vectorized complex ``spence`` implementation evaluates
    ``Li₂(z) = spence(1-z)``. The identities ``D(z)=-D(1/z)=-D(1-z)`` reduce
    arguments to ``abs(z)<=1`` and ``real(z)<=1/2`` before this evaluation,
    avoiding cancellation near 1 and infinity. Real-axis values, including
    the removable points 0 and 1, are zero. This remains floating-point
    evaluation, with no rigorous error enclosure.
    """
    z_arr, is_scalar = _as_complex_array(z)
    if not np.all(np.isfinite(z_arr)):
        raise ValueError("Bloch-Wigner inputs must be finite")
    out = np.empty(z_arr.shape, dtype=np.float64)
    real_axis = z_arr.imag == 0.0
    out[real_axis] = 0.0

    regular = ~real_axis
    if np.any(regular):
        zr = z_arr[regular].copy()
        sign = np.ones(zr.shape, dtype=np.float64)
        scale = np.maximum(np.abs(zr.real), np.abs(zr.imag))
        outside_unit = scale > 1.0
        bounded = ~outside_unit
        outside_unit[bounded] = np.hypot(zr[bounded].real, zr[bounded].imag) > 1.0
        if np.any(outside_unit):
            large = zr[outside_unit]
            large_scale = scale[outside_unit]
            real, imag = large.real / large_scale, large.imag / large_scale
            norm_sq = real * real + imag * imag
            # Do not form |z|**2, a + b*(b/a), or scale*norm_sq: each can
            # overflow for finite inputs. Divide by the scale only at the end.
            zr[outside_unit] = (real / norm_sq) / large_scale - 1j * (imag / norm_sq) / large_scale
            sign[outside_unit] = -1.0
        near_one = zr.real > 0.5
        zr[near_one] = 1.0 - zr[near_one]
        sign[near_one] *= -1.0
        li2 = spence(1.0 - zr)
        # This log-hypot form also avoids rounding a subnormal magnitude to 0
        # (or losing its relative precision) before taking its logarithm.
        largest = np.maximum(np.abs(zr.real), np.abs(zr.imag))
        smallest = np.minimum(np.abs(zr.real), np.abs(zr.imag))
        log_abs = np.log(largest) + 0.5 * np.log1p((smallest / largest) ** 2)
        out[regular] = sign * (li2.imag + np.angle(1.0 - zr) * log_abs)

    return float(out) if is_scalar else out


def _bloch_wigner_mp_value(z):
    """Evaluate on the current mp context, including the real-axis limits."""
    if not z.imag:
        return mp.mpf(0)
    sign = 1
    # Reflect first near 1: forming 1 - 1/z there would introduce an avoidable
    # cancellation after rounding the reciprocal at the working precision.
    if z.real > mp.mpf("0.5"):
        z, sign = 1 - z, -sign
    if abs(z) > 1:
        z, sign = 1 / z, -sign
    if z.real < 0:
        # D(z) = -D(z/(z-1)). For |z| <= 1 and Re(z) < 0 this maps
        # into 0 <= Re(w) <= 1/2 and |w| <= 1/sqrt(2). In that region
        # polylog's convergent series preserves a tiny imaginary component;
        # its negative-real-side continuation can lose it to cancellation.
        z, sign = z / (z - 1), -sign
    return sign * (mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z)))


def bloch_wigner_mp(z, dps: int = 120):
    """Evaluate the Bloch--Wigner dilogarithm as an ``mpmath.mpf``.

    Accept finite mpf/mpc values, Python/NumPy real or complex scalars, real
    decimal strings/Decimal, rationals, or a ``(real, imaginary)`` pair of
    supported real inputs. Conversion and arithmetic use ``dps`` digits. Values on the real
    axis, including the removable points 0 and 1, are zero. This is numerical
    arbitrary precision, not an exact value or a validated error enclosure.
    """
    with mp.workdps(_precision_digits(dps)):
        return _bloch_wigner_mp_value(_finite_mpc(z))


def bloch_wigner_mpmath(z: complex, dps: int | None = None) -> float:
    """Binary64-output compatibility wrapper for :func:`bloch_wigner_mp`.

    Omitting ``dps`` retains the caller's current mpmath precision, as in the
    historical API. The final conversion to float limits output precision;
    use ``bloch_wigner_mp`` when arbitrary-precision output is required.
    """
    return float(bloch_wigner_mp(z, dps=mp.mp.dps if dps is None else dps))


def triangle_volume_from_points_mp(z1, z2, z3, dps: int = 120):
    """Volume of ``[z1, z2, z3, infinity]`` with mp input and mpf output.

    Coordinates use the same input forms as :func:`bloch_wigner_mp`. Distinct
    collinear vertices have limiting volume zero; repeated or nonfinite
    vertices are rejected. No binary64 angles, triangulation or projection
    enter this local tetrahedron evaluation. Input accuracy and conditioning
    still limit attainable accuracy; this function supplies no error bound.
    """
    with mp.workdps(_precision_digits(dps)):
        z1, z2, z3 = (_finite_mpc(z) for z in (z1, z2, z3))
        if z1 == z2 or z1 == z3 or z2 == z3:
            raise ValueError("triangle vertices must be distinct at the working precision")
        return abs(_bloch_wigner_mp_value((z1 - z3) / (z2 - z3)))


def bloch_wigner_torch(z_real, z_imag):
    """Evaluate Bloch–Wigner values via the optional ``torch`` extra."""
    return _geometry_torch_module().bloch_wigner_torch(z_real, z_imag)


def cross_ratio_torch(
    z1_real, z1_imag, z2_real, z2_imag, z3_real, z3_imag, z4_real, z4_imag
):
    """Compute a cross ratio via the optional ``torch`` extra."""
    return _geometry_torch_module().cross_ratio_torch(
        z1_real,
        z1_imag,
        z2_real,
        z2_imag,
        z3_real,
        z3_imag,
        z4_real,
        z4_imag,
    )


def triangle_volume_from_points(z1, z2, z3, mode="fast", series_terms=64, dps=120):
    """Evaluate one tetrahedron and return a Python float.

    The legacy default ``fast`` is a truncated Fourier approximation.
    ``mpmath`` evaluates the cross-ratio kernel at ``dps`` digits before the
    final binary64 conversion; ``exact`` and ``eval_only`` are compatibility
    aliases, not exact-arithmetic claims. Use ``triangle_volume_from_points_mp``
    for arbitrary-precision output without a binary64 conversion.
    """
    if mode == "fast":
        a1, a2, a3 = _angles_for_triangle_np(z1, z2, z3)
        value = (
            _lob_value_series_np(a1, series_terms)
            + _lob_value_series_np(a2, series_terms)
            + _lob_value_series_np(a3, series_terms)
        )
        return float(value)
    if mode in ("mpmath", "exact", "eval_only"):
        return float(triangle_volume_from_points_mp(z1, z2, z3, dps=dps))
    raise ValueError("mode must be 'fast', 'mpmath', or the legacy aliases 'exact'/'eval_only'")


def triangle_volume_from_points_torch(z1t, z2t, z3t, series_terms=64):
    """Accumulate one tetrahedron via the optional ``torch`` extra."""
    return _geometry_torch_module().triangle_volume_from_points_torch(
        z1t, z2t, z3t, series_terms
    )


def triangle_volume_bloch_wigner(z1t, z2t, z3t):
    """Compute one BW tetrahedron via the optional ``torch`` extra."""
    return _geometry_torch_module().triangle_volume_bloch_wigner(z1t, z2t, z3t)


def ideal_poly_volume_via_hull_project_back(
    W, index_inf=0, mode="fast", dps=120, series_terms=64
):
    """Volume with binary64 hull/projection and a float result.

    ``fast`` is the legacy truncated-series default. ``mpmath`` (legacy
    aliases ``exact``/``eval_only``) evaluates and sums kernels at ``dps``
    digits on the already rounded geometric decomposition.
    """
    tris = hull_tris_projected_back(W, index_inf=index_inf)
    if mode in ("mpmath", "exact", "eval_only"):
        with mp.workdps(_precision_digits(dps)):
            return float(mp.fsum(
                triangle_volume_from_points_mp(z1, z2, z3, dps=dps)
                for z1, z2, z3 in tris
            ))
    total = 0.0
    for z1, z2, z3 in tris:
        total += triangle_volume_from_points(
            z1, z2, z3, mode=mode, series_terms=series_terms, dps=dps
        )
    return total


def _triangle_cross_ratios(z: np.ndarray, triangles: np.ndarray) -> np.ndarray:
    """Vectorized cross ratios for tetrahedra [z1,z2,z3,infinity]."""
    triangle_points = z[np.asarray(triangles, dtype=np.int64)]
    numerator = triangle_points[:, 0] - triangle_points[:, 2]
    denominator = triangle_points[:, 1] - triangle_points[:, 2]
    if np.any(denominator == 0.0):
        raise ValueError("Delaunay simplex contains coincident vertices")
    return numerator / denominator


def _volume_from_triangles_fast_series(
    z: np.ndarray,
    triangles: np.ndarray,
    series_terms: int,
) -> float:
    triangle_points = z[np.asarray(triangles, dtype=np.int64)]
    a1, a2, a3 = _angles_for_triangle_np(
        triangle_points[:, 0], triangle_points[:, 1], triangle_points[:, 2]
    )
    values = (
        _lob_value_series_np(a1, series_terms)
        + _lob_value_series_np(a2, series_terms)
        + _lob_value_series_np(a3, series_terms)
    )
    return float(np.sum(values))


def _volume_from_triangles_bloch_wigner(
    z: np.ndarray,
    triangles: np.ndarray,
) -> float:
    cross_ratios = _triangle_cross_ratios(z, triangles)
    return float(np.sum(np.abs(bloch_wigner(cross_ratios))))


def ideal_poly_volume_via_delaunay(
    z_finite_complex: np.ndarray,
    mode="fast",
    dps=120,
    series_terms=64,
    use_bloch_wigner=False,
):
    """
    Compute volume of ideal polyhedron using Delaunay triangulation.

    Args:
        z_finite_complex: Array of finite vertices (complex numbers)
        mode: "bloch_wigner"/"bw", "fast" (legacy series default), or "mpmath".
            "exact" and "eval_only" are legacy aliases for "mpmath".
        dps: Decimal working precision for mpmath kernel evaluation and summation
        series_terms: Number of terms for fast mode
        use_bloch_wigner: If True, use the binary64 Bloch-Wigner kernel

    Returns:
        Total volume as float. Input conversion and Qhull topology are always
        binary64, including in mpmath mode; this is not exact geometry or a
        validated volume enclosure. ``triangle_volume_from_points_mp`` is the
        separate arbitrary-precision local tetrahedron entry.
    """
    z_finite_complex = np.asarray(z_finite_complex, dtype=np.complex128)
    if z_finite_complex.ndim != 1:
        raise ValueError("z_finite_complex must be a one-dimensional array")
    if len(z_finite_complex) < 3:
        raise ValueError("at least three finite vertices are required")

    idx_tris = delaunay_triangulation_indices(z_finite_complex)

    if use_bloch_wigner or mode in ("bloch_wigner", "bw"):
        return _volume_from_triangles_bloch_wigner(z_finite_complex, idx_tris)

    if mode == "fast":
        return _volume_from_triangles_fast_series(
            z_finite_complex, idx_tris, series_terms
        )
    if mode in ("mpmath", "exact", "eval_only"):
        with mp.workdps(_precision_digits(dps)):
            return float(mp.fsum(
                triangle_volume_from_points_mp(
                    z_finite_complex[i], z_finite_complex[j], z_finite_complex[k], dps=dps
                )
                for i, j, k in idx_tris
            ))
    raise ValueError(
        "mode must be 'bloch_wigner', 'fast', 'mpmath', or the legacy aliases 'exact'/'eval_only'"
    )


def ideal_poly_volume_from_sphere(
    points_sphere: np.ndarray,
    pole_index: int = 0,
    mode: str = "bloch_wigner",
    series_terms: int = 64,
    dps: int = 120,
) -> float:
    """Volume of an ideal H³ polyhedron from all of its points on S².

    The chosen input vertex is sent to infinity by
    :func:`stereographic_project_from_pole`; unlike a fixed-north projection,
    this is invariant under rotations of the sphere and under changing the
    chosen pole for generic configurations.

    ``mode='bloch_wigner'`` is the accurate vectorized double-precision path.
    ``mode='fast'`` uses the truncated Lobachevsky series. ``'mpmath'`` (legacy
    aliases ``'exact'`` and ``'eval_only'``) evaluates and sums the kernel at
    ``dps`` digits but still uses binary64 sphere projection, input geometry
    and Qhull topology, and returns a float. It is not exact geometry or a
    validated error enclosure.
    """
    projected, _ = stereographic_project_from_pole(points_sphere, pole_index)
    if mode in ("bloch_wigner", "bw"):
        return ideal_poly_volume_via_delaunay(projected, use_bloch_wigner=True)
    if mode in ("fast", "mpmath", "exact", "eval_only"):
        return ideal_poly_volume_via_delaunay(
            projected,
            mode=mode,
            dps=dps,
            series_terms=series_terms,
            use_bloch_wigner=False,
        )
    raise ValueError("mode must be 'bloch_wigner', 'fast', 'mpmath', 'exact', or 'eval_only'")
