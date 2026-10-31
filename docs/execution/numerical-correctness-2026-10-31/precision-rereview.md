# H³ precision correction: independent follow-up review

**Disposition: approved for integration within the reviewed H³ scope; no remaining blockers found.** The negative-axis failure and the two near-one target misses from [the original review](precision-review.md) are resolved. This follow-up preserves all original failure artifacts and writes new evidence files.

## Source and scope

The actual imported module is `/Volumes/Lexar/lambda/devel/polyhedra/consolidated/packages/volume-toolkit/ideal_poly_volume_toolkit/geometry.py`, with SHA-256 `eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73`. The preserved prior snapshot has SHA-256 `6b779e418e9a5328404b7cb18be9c2cdf7226a6c480fe5e235df0490cceaa51e`.

A byte-derived diff against that snapshot changes only `_bloch_wigner_mp_value`: reflection precedes inversion, and a negative reduced real part triggers `z/(z-1)` with a sign reversal. The binary64 kernel and all conversion, precision-context, compatibility, and output contracts are unchanged. Production code was not edited during this review. Other workers' optimizer and Delaunay changes were outside this review; no full suite was run.

## Mathematical inspection

The three identities used are `D(1-z)=-D(z)`, `D(1/z)=-D(z)`, and `D(z/(z-1))=-D(z)`. Every applied map flips the accumulated sign once; conjugation changes the final sign. Reflection before inversion avoids forming a cancellation-prone `1-1/z` near one.

After the first two reductions, `|z|<=1` and `Re(z)<=1/2`. For `x=Re(z)<0` and `t=|z|²<=1`, the additional map has real part `(t-x)/(t-2x+1)` in `[0,1/2]` and squared magnitude `t/(t-2x+1)<=1/2`. Thus its claimed region and signs are correct. The real-axis short circuit retains the removable limits at zero and one. The reduction is a numerical stability correction, not a certified error bound.

## Independent numerical evidence

[The replay](precision-rereview-probe.py) is the original review probe with only its output filename changed. Its reference directly evaluates `Im(polylog(2,z)) + arg(1-z)*log(abs(z))` at 450 digits, or 1100 digits for highly skewed extreme inputs. It does not reuse any implementation argument map. All **74 cases pass** for both binary64 and MP120 in [the new machine results](precision-rereview-checks.json).

- The original MP failure at `-1 ± i*min_subnormal` now has relative discrepancy about `1.01e-121`, versus about `1.38e199` before correction.
- Both near-one cases at the next binary64 value above one with height `±1e-300` improve from approximately `7.18e-112` to `2.63e-122`. They now meet the probe's `1e-112` target, which is a finite comparison criterion rather than an API guarantee.
- The maximum MP120 relative discrepancy over all 74 cases is approximately `2.05e-121`.
- Every observed binary64 output is unchanged. The maximum relative discrepancy among the 62 cases with normal binary64 outputs remains approximately `4.08e-16`. The other cases use absolute/ULP comparisons appropriate to underflow and subnormals; no relative accuracy claim is inferred for them.
- Scalar and reshaped-array binary64 results agree exactly. The replay also passes independent logarithmic-quadrature checks for Fraction inputs as small as `1e-400`, Decimal, NumPy integer, float32, and longdouble inputs; nonfinite rejection, removable real-axis values, and restoration of enclosing precision after exceptions pass.

[An additional independent probe](precision-rereview-negative-axis-probe.py) tests negative real values `-1e-6`, `-0.25`, `-1`, `-4`, and `-1e6`, both imaginary signs, and heights `1e-150` and `1e-300`. All **20 cases pass** against the unreduced 450-digit definition and the analytic first-order real-axis coefficient. MP120 values and local triangle volumes have maximum relative discrepancy about `1.34e-121`; all float-wrapper outputs equal the rounded independent reference. The maximum direct-reference discrepancy from the first-order term is about `6.18e-142`. [Results](precision-rereview-negative-axis.json) include signs and each wrapper outcome.

In particular, the original concrete blocker now gives approximately `+6.931471805599453e-151` at `-1+i*1e-150` and `+6.931471805599453e-301` at `-1+i*1e-300`, with relative discrepancies approximately `1.15e-122` and `4.00e-122`. Their conjugates have the correct negative signs.

## Focused checks and contract review

Using `/tmp/polyhedra-baseline-20261031/bin/python` from the package directory, with `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, and the isolated matplotlib configuration:

```sh
python -m pytest tests/test_geometry_precision.py tests/test_geometry.py \
  tests/test_variational.py -q -p no:cacheprovider
```

Result: **60 passed in 17.74 seconds**. See [log](precision-rereview-tests.log) and [JUnit XML](precision-rereview-tests.xml). Ruff on `geometry.py` and `test_geometry_precision.py`, and `git diff --check` on those files plus `docs/numerical-precision.md`, both pass.

The precision documentation accurately distinguishes MP working precision, represented input accuracy, MP versus float outputs, binary64 Qhull/projection, and unchanged legacy fixed-term defaults. It explicitly disclaims exact values, interval enclosures, validated topology, and a general error bound; scoped mpmath precision is not described as thread-local. Fraction/Decimal conversion and NumPy ratio conversion remain intact. This platform's longdouble does not provide additional mantissa precision, so another platform's extended-precision execution remains untested here.

The review supports the local numerical correction and its stated contracts. It does not certify global geometry, every possible input, optional accelerators, platform portability, or monograph proofs. Artifact hashes, commands and observed statuses are recorded in [the follow-up manifest](precision-rereview-manifest.json).
