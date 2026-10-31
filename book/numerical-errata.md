# Numerical software errata

Date: 31 October 2026. Baseline integrated source:
`285a6cb71473ba1f238983e062662cf890cbba05`. This record accompanies the
[numerical-correctness checkpoint](../docs/execution/numerical-correctness-2026-10-31/README.md)
and the [computational-status ledger](computational-status.md).

These are corrections to maintained software and its result contracts. The
canonical monograph TeX, supplied PDF, historical `ipoly` sources and existing
scientific data corpus retain their original bytes. The bounded computations
below neither audit the entire monograph nor establish a change to one of its
theorems. A printed historical value requires its own identified replay before
being replaced or reclassified.

## Precision and volume evaluation

The [precision contract](../packages/volume-toolkit/docs/numerical-precision.md)
distinguishes binary64 kernels, mpf-returning multiprecision helpers and
high-level float outputs. The legacy `lob_exact`, `exact` and `eval_only`
names describe numerical mpmath evaluation, not exact arithmetic. Existing
`fast` defaults remain truncated Fourier approximations. Maintained final
reporting selects the Bloch–Wigner or mpmath method explicitly.

| Reproduced baseline case | Old behavior | Corrected behavior and scope |
| --- | --- | --- |
| Angle `1e-400`, including `Fraction(1,10**400)` | Initial float conversion returned zero. | MP output remains positive, approximately `9.21340890017e-398`. |
| Decimal angle `0.123456789012345678901234567890123456789` | Float conversion left absolute error about `2.1458e-18` despite 105 working digits. | Independent logarithmic quadrature agrees within `1e-100` in this case. |
| Requested mpmath precision | The changed global setting survived normal calls and errors. | Scoped working precision is restored on success and failure; it is not a thread-local guarantee. |
| Binary64 `D(1e300+1e300j)` / `D(1e308+1e308j)` | Zero / NaN for finite inputs. | About `3.46061050744e-298` / `3.55271391116e-306` after stable argument reduction. |
| Legacy `bloch_wigner_mpmath(0)` | NaN. | `0.0`, retaining the wrapper's float result. |

The [before/after report](../docs/execution/numerical-correctness-2026-10-31/precision.md)
identifies inputs, reference methods and source hashes. The fixed five-finite-
vertex Delaunay case changes from `2.497622683293108` in the old `exact` mode
to `2.4976226832931077` in `mpmath` mode. This is a float-output rounding change;
Qhull and projection still use binary64. It is not a high-precision topology
certificate or a rigorous error bound for other inputs.

## Feasible angle optimization and accurate final values

The [Rivin numerical contract](../packages/volume-toolkit/docs/rivin-numerics.md)
replaces clipping and one-way constraint activation with feasible steps,
actual-volume line search, constraint release and an independent final KKT
audit. All original equality and inequality rows remain in the audit, even
when a numerical rank reduction is used in the step solve. Final volumes use
the canonical binary64 Bloch–Wigner kernel instead of the old 64-term Fourier
report. Exact flat angles remain outside this differentiable solver.

| Bounded replay | Baseline report | Corrected report |
| --- | --- | --- |
| One equilateral triangle / regular ideal tetrahedron | `1.0151497106006686`, success | Approximately `1.0149416064096536`, passing numerical KKT checks |
| Positive near-flat one-triangle start | Unsuccessful candidate; angle-sum residual about `1e-6` after clipping | Converges to the regular value with residual near roundoff |
| Delaunay points, `n=15`, seed `2` | `19.113162627196726`, success | `19.112626012370175`, passing numerical KKT checks |
| Delaunay points, `n=50`, seed `1002` | `76.60339035517823`, success | `76.60379512334639`, passing numerical KKT checks |
| Delaunay points, `n=50`, seed `1007` | `81.45749975621857`, success | `81.45772627160687`, passing numerical KKT checks |

The regular-tetrahedron reference is `1.0149416064096536`, rounded from a
60-digit Clausen calculation. Its old reported excess is about
`2.08104191e-4`. The other rows combine solver and final-evaluation changes;
they are not estimates of the Fourier error alone. The near-flat old run was
already unsuccessful, so it is not an accepted historical optimum being
revised. Inputs, seed construction and values are in the
[implementation report](../docs/execution/numerical-correctness-2026-10-31/angle-solver.md)
and [machine replay](../docs/execution/numerical-correctness-2026-10-31/angle-solver-validation.json).

Strict LP feasibility previously optimized `1000*epsilon+t`, which could
sacrifice the positive-angle minimum to inequality slack and return a false
negative. The corrected finite program maximizes one common angle/dihedral/
boundary margin in units of pi. Measured witness margins and the guaranteed
common slack are reported separately. Failure to verify a positive witness
does not prove exact infeasibility or non-realizability.

For one eight-face fixture, independent rational primal and dual witnesses
prove a common-margin optimum of exactly `1/7`; see the
[independent review](../docs/execution/numerical-correctness-2026-10-31/angle-solver-review.md)
and its preserved probe. This exact certificate concerns that finite angle
program. A bounded 90-input scan corrected 36 old false negatives; it does not
estimate prevalence or classify all triangulations. Seven independent SLSQP
solves with mpmath objectives agreed within `4.23e-13` in final volume.

Interior-only classification now examines the final converged dihedral ties.
Temporary active constraints can be released. The `n=15`, seed-2 legalization
fixture consequently takes two flips instead of one, while retaining the
strict acceptance checks and repeated deterministic path. This is changed
algorithmic work, not evidence of a performance improvement.

These free-angle inequality calculations differ from the fixed-dihedral,
leading–trailing coordinates of monograph Section 9. Numerical KKT checks do
not prove an interval optimum, global geometric embedding, arithmeticity or a
general statement about that section's coordinate space.

## Optimizer results and threshold decisions

The [result contract](../packages/volume-toolkit/docs/optimizer-result-contract.md)
requires fresh canonical endpoint evaluation and complete-boundary checks
before ranking candidates. Invalid later trials cannot erase an earlier
usable result. Raw solver convergence stays separate from candidate validity;
a valid unconverged candidate is retained with both statuses visible.

The baseline service-boundary probe deliberately supplied a cached volume
`100` with regular-tetrahedron parameters whose actual volume is about
`1.01494`. It demonstrates unchecked trust at that boundary, not a claim that
ordinary SciPy produces stale scores. New schema-v2 outputs record validation
and separate verification work, and reject NaN/Infinity in JSON. The v1 schema
and its historical fixture are unchanged.

A fresh bounded CLI replay reports `1.0149416063712777`; the previous
checkpoint's saved value was `1.0149416063705312`, a difference of about
`7.47e-13`. That replay also includes the canonical-kernel correction. It is
not solely evidence for endpoint reevaluation, and the old artifact has not
been overwritten. See the [service report](../docs/execution/numerical-correctness-2026-10-31/optimization-service.md).

Threshold checks now reject NaN vertices/thresholds and boolean series term
counts. A single infinity and the established implicit-infinity convention
remain supported. These are numerical comparisons; near-equality decisions
are not certified without an error enclosure.

## Findings caught before committing this increment

The initial MP implementation mishandled tiny imaginary parts near the
negative real axis: at 120 digits `D(-1+i*1e-150)` was approximately
`-4.727e-125` instead of `+6.931e-151`. The
[original independent review](../docs/execution/numerical-correctness-2026-10-31/precision-review.md)
and reviewed source snapshot are preserved. The author applied a further
argument reduction and compared twenty signed cases with an unreduced
450-digit reference and an analytic real-axis derivative. This was an
uncommitted review finding, not a defect in baseline commit `285a6cb`. The
[independent follow-up](../docs/execution/numerical-correctness-2026-10-31/precision-rereview.md)
approves the correction after all 74 original independent cases and twenty
additional signed negative-axis cases pass.

The [initial service review](../docs/execution/numerical-correctness-2026-10-31/service-review.md)
found that a callback could mutate internal parameters after validation.
Detached deep copies now protect history and winner selection; the
[independent follow-up](../docs/execution/numerical-correctness-2026-10-31/service-review-callback-followup.md)
approves that correction. Completed result arrays remain mutable by their
caller; global post-return immutability is not claimed.

The initial angle review requested corrections to overclaiming feasibility
messages and an undercount of volume evaluations. Its pre-fix report and
counterexample outputs remain evidence for that intermediate source state.
The author follow-up reports 73 passing focused tests and instrumented counts
of 1/1 and 14/14, replacing the old reports of 0/1 and 7/14 actual calls.
The [independent follow-up](../docs/execution/numerical-correctness-2026-10-31/angle-solver-followup-review.md)
approves both corrections and rechecks the numerical references. Consult the
checkpoint for integrated validation status rather than treating a preserved
failing report as the final verdict.

## Remaining publication work

No corpus-wide replay, complete proof audit or release is implied. The
fresh-endpoint contract applies to `optimization.optimize_ideal_polyhedron`;
the separate historical `refine_geometry_for_volume` path still uses a cached
solver objective and has not received this boundary audit. H⁴/H⁵ and Torch
kernels were outside this increment. The Section 9 artifact has been
regenerated from clean corrected source `9188e0624cdf6d9949af1f620336eff67c8b59d7`,
committed as `29440cfbfcdaa23711cfdac4e09bf5f939404273`, and successfully
replayed from its final detached archive; see the
[closeout](../docs/execution/numerical-correctness-2026-10-31/closeout.md).
Older outputs retain their recorded provenance in history and the first
checkpoint. The integrated
available-suite attempt reports 393 passes, with the same four failures and
nine collection errors from unavailable optional dependencies as before.
Optional dependency and platform gates remain outstanding. Airy-table and torus-
diagnostic evidence remains unavailable, and complete monograph conversion,
browser validation, licensing and Sites publication remain future work.
