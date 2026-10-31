# Independent H³ precision review

Reviewed source: `geometry.py` SHA-256 `6b779e418e9a5328404b7cb18be9c2cdf7226a6c480fe5e235df0490cceaa51e`, based on integrated HEAD `285a6cb71473ba1f238983e062662cf890cbba05` with the uncommitted precision patch. Imports were confirmed from `consolidated/packages/volume-toolkit/ideal_poly_volume_toolkit/geometry.py`. This reviewer changed no implementation, test, documentation, Git index or original source repository. Only these outer review artifacts were written.

**Disposition: one blocking numerical finding in the new mpmath Bloch–Wigner path.** The binary64 correction, scalar conversion, scoped-precision contract and compatibility documentation pass the checks below. The MP failure needs correction and an independent rerun before this patch is accepted.

## Blocking finding: spurious MP values near the negative real axis

`_bloch_wigner_mp_value` reduces near zero, one and infinity but can still send an argument extremely close to the negative real axis to `mp.polylog`. Its complex continuation loses the small imaginary component at the requested working precision. This is observable as a wrong sign and a much larger spurious volume:

| Input and working precision | Current MP result | Independent reference |
| --- | --- | --- |
| `('-1', '1e-150')`, 120 digits | `-4.7272850523062967197e-125` | `+6.9314718055994530942e-151` |
| `('-1', '1e-300')`, 120 digits | `-4.7272850523062967197e-125` | `+6.9314718055994530942e-301` |

The references use the direct definition `Im(polylog(2,z)) + arg(1-z)*log(abs(z))` at 450 digits, without the implementation's reciprocal/reflection reductions. They also agree with the independent first-order limit `D(-1+i*y) = y*log(2) + O(y^3)`. These represented inputs retain a nonzero imaginary component; the issue is not input underflow. The negative result for a point in the upper half-plane is decisive even though the API correctly disclaims a uniform error guarantee. The compatibility float wrapper would expose the spurious magnitude; taking an absolute value in the local-tetrahedron wrapper would hide the sign but not repair the magnitude.

Reproduction:

```python
from ideal_poly_volume_toolkit.geometry import bloch_wigner_mp
print(bloch_wigner_mp(("-1", "1e-150"), dps=120))
```

See [targeted evidence](precision-review-negative-axis.json) and the negative-axis cases in [independent comparison evidence](precision-review-checks.json). A stable additional identity such as `D(z)=-D(z/(z-1))` can map reduced negative-real-side arguments to a positive-real neighborhood; adaptive precision or another stable evaluation is also possible. The author should establish the chosen behavior with independent tiny-imaginary references and preserve precision restoration. No implementation remedy was applied by this reviewer.

## Independent numerical checks

The [review probe](precision-review-probe.py) evaluates 74 cases using the raw MP definition at 450 digits, increased to 1100 digits for extremely skewed huge arguments. It includes seeded radial samples across exponents -308 through 308, maximum finite components, minimum subnormals, values on both sides of one, conjugates, and reduction boundaries. It does not call the new MP kernel to construct its reference.

- All 74 binary64 comparisons pass the declared `8 output ulps + 4e-14 relative` criterion. The largest observed relative discrepancy among the 62 cases with normal binary64 reference values is approximately `4.08e-16`. Subnormal and correctly underflowed outputs are assessed in output ulps; they do not have the same relative-accuracy interpretation.
- Scalar and reshaped-array binary64 results match exactly. The bounded reciprocal and scaled log-magnitude avoid overflow/invalid/division-by-zero errors in these finite cases.
- Finite real-axis values, including 0 and 1, return zero. Nonfinite arguments are rejected explicitly. No infinity limit is silently substituted for an overflow.
- Direct scaled logarithmic quadrature independently verifies `Fraction(1,10**400)`, `Decimal`, NumPy integer, binary32 and local `longdouble` scalar conversion. All five meet the review's relative target of `1e-112` at 120 working digits. On this ARM64 host, `longdouble` has no extra mantissa precision; other platforms were not tested.
- Precision is restored after malformed numeric input, nonfinite input and repeated-vertex errors. Existing tests also verify restoration after a simulated special-function exception.

The probe's `all_passed=false` includes the blocking negative-axis MP cases and a separate stringent accuracy-target miss for arguments just above one with an imaginary component of `1e-300`: their MP relative difference is about `7.18e-112` at 120 working digits, versus a probe target of `1e-112`. This latter difference is **not classified as a blocker**: the documented contract promises working precision rather than a uniform number of correct output digits, and it explicitly discusses conditioning. It is retained in the evidence rather than hidden. The negative-axis wrong-sign values require correction independently of that target.

These checks establish bounded numerical evidence, not a rigorous error enclosure or accuracy guarantee for all finite arguments.

## Contract and code review

The scope statements correctly separate binary64 evaluation, mpmath arithmetic, binary64 Qhull/projection topology, exact algebraic claims and interval certification. Existing fast defaults remain explicit fixed-term approximations. The legacy `lob_exact` alias retains its historical MP return type; `bloch_wigner_mpmath` retains float output and the ambient-precision default. `mpmath`, `exact` and `eval_only` high-level modes keep float outputs and document their binary64 geometric decomposition. Rational/decimal/NumPy conversions avoid broad float fallback; translated local tetrahedra have a separate MP input/output entry. The precision context is explicitly not claimed to be thread-local.

No other blocking implementation or contract finding was identified. Shared index, architecture, README and changelog updates are assigned to the parent documentation pass and were not treated as omissions in this worker's owned-file review.

## Verification commands

From `consolidated/packages/volume-toolkit`, using the isolated copied-local-dependency Python 3.12.11 environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 \
/tmp/polyhedra-baseline-20261031/bin/python -m pytest \
  tests/test_geometry_precision.py tests/test_geometry.py tests/test_variational.py \
  -q -p no:cacheprovider
```

Result: **49 passed in 15.06 seconds**; [log](precision-review-tests.log), [JUnit](precision-review-tests.xml). Ruff on `geometry.py` and `test_geometry_precision.py`, and whitespace checks on the three owned files, pass. The independent probe exits 1 because of the recorded MP findings; its [log](precision-review-probe.log) is retained. A full suite, fresh dependency resolution, all-platform validation, final packaging and artifact regeneration were not attempted by this reviewer.
