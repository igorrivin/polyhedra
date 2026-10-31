# H³ volume precision

`geometry.py` owns the H³ volume kernels. The supported numerical choices
have different input, arithmetic and output contracts:

| Entry | Input and geometry | Arithmetic and output |
| --- | --- | --- |
| `bloch_wigner` | Binary64 complex scalars or arrays | Vectorized binary64 SciPy kernel; float or NumPy array |
| `lobachevsky_mp`, `bloch_wigner_mp` | mpf/mpc, ordinary numeric inputs, or decimal strings at the requested precision | mpmath arithmetic; mpf output |
| `triangle_volume_from_points_mp` | Three finite planar vertices, converted at the requested precision; no Qhull or projection | mpmath cross-ratio and volume; mpf output |
| `triangle_volume_from_points(..., mode="mpmath")` | Local tetrahedron evaluated at the requested precision | Float output after high-precision evaluation |
| Polyhedron entry points with `mode="mpmath"` | Binary64 sphere/hull projection and Qhull triangulation | High-precision kernel evaluation and summation on that represented geometry, followed by float output |
| Existing `mode="fast"` paths | Binary64 geometry | Fixed-term Fourier approximation, including their unchanged legacy defaults |

`dps` is a positive integer giving decimal working precision. It is not a
bound on the error. Input accuracy, cancellation and geometric conditioning
still matter. These functions do not provide exact algebraic values, interval
enclosures, validated topology or a proof of geometric existence.

The legacy `lob_exact` name delegates to `lobachevsky_mp`, preserving its
historical mpf return type. Modes `"exact"` and `"eval_only"` remain aliases
for `"mpmath"`; they do not claim exact computation. The historical
`bloch_wigner_mpmath` entry retains a float result, and uses the caller's
current precision unless an explicit `dps` is supplied. New code needing mpf
output should call `bloch_wigner_mp` instead.

All mpmath conversion and arithmetic use a scoped `workdps` context, which
restores the enclosing precision on success and failure. This is not a
thread-local precision guarantee. Decimal strings and `Decimal` values avoid
the information loss of first constructing Python floats. `Fraction`/rational
inputs are converted from their numerator and denominator at the requested
precision. NumPy integers are converted to Python integers; NumPy binary
floating scalars use their integer ratios, including extended precision where
that platform supports it. There is no generic fallback through `float(value)`.
Complex coordinates can be supplied as `(real, imaginary)` pairs of supported
real values, NumPy complex scalars, or mpc values created at sufficient
precision. Passing a binary64 value to a high-precision function cannot recover
digits already lost before the call. Arbitrary custom objects that merely
implement `__float__` are not a supported high-precision input contract.

The binary64 Bloch--Wigner kernel and the mp kernel both use the identities
`D(z)=-D(1/z)` and `D(z)=-D(1-z)` to reduce to `abs(z)<=1` and
`real(z)<=1/2`. This avoids the large cancellation in the direct dilogarithm
formula near infinity and one. The binary64 reciprocal scales real and
imaginary components before squaring, and divides by the scale last; neither
the squared original magnitude nor an overflowing complex denominator is
formed. A scaled log-magnitude calculation also supports subnormal reduced
arguments. Both APIs reject NaN and infinite inputs rather than treating an
overflow as a valid infinity limit. Finite real-axis inputs return zero.

The mp kernel reflects near one before taking any reciprocal, avoiding the
avoidable cancellation in `1-1/z` at the working precision. It additionally
applies `D(z)=-D(z/(z-1))` whenever the reduced
real part is negative. For `abs(z)<=1` and `real(z)<0`, the new argument has
`0<=real(w)<=1/2` and `abs(w)<=1/sqrt(2)`. This avoids loss of tiny imaginary
components in mpmath's continuation near the negative real axis. The tests
compare such cases with the unreduced direct formula at 450 digits and an
independent real-axis derivative. This is a stability correction for the
observed failure, not a uniform guarantee of relative output accuracy.

For example, `triangle_volume_from_points_mp("0", "1", ("0", "1"), dps=100)`
returns Catalan's constant numerically as an mpf. Distinct collinear vertices
have limiting volume zero. Repeated vertices, nonfinite inputs and an invalid
precision are rejected. Coordinates that become indistinguishable at the
requested precision also trigger the distinctness check.

The public fast defaults are retained for compatibility. Maintained optimizer
reporting and monograph computations must select the Bloch--Wigner or mpmath
path explicitly and record the method. Historical Fourier outputs remain
historical approximations; changing precision does not revalidate an old run.

The focused regressions in `tests/test_geometry_precision.py` compare with
independent logarithmic quadrature, known special values and degeneration
asymptotics; exercise sixfold/conjugation identities; and check that input and
output retain information beyond binary64. These are numerical validations,
not certified error bounds for all possible inputs.
