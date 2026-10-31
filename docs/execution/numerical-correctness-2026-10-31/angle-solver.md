# Rivin numerical correctness implementation

Baseline: integrated commit `285a6cb71473ba1f238983e062662cf890cbba05`.
Only the maintained checkout was edited. No staging, commits, original
repository edits, or historical-result replacements were performed.

## Implemented contracts

- Replaced final 64-term Fourier reporting with canonical binary64
  Bloch-Wigner evaluation; the largest-sine denominator keeps shapes bounded.
- Replaced the value helper's cutoff quadrature with the canonical
  Bloch-Wigner/Clausen identity on `[0,pi]`. Endpoints are explicit zero;
  nonfinite/out-of-domain input rejects. Existing reconstruction algorithms
  were not otherwise changed.
- Replaced clipping and feasibility-only Newton stepping with feasible
  projected Newton/gradient ascent and an actual-volume Armijo line search.
  Curvature overflow uses a gradient direction; angles are never clipped.
- Added blocker activation and negative-multiplier release, rank-aware
  affine/null-space solves, bounded iteration/working-set controls, and
  an independent KKT audit against all original constraints. Numerical rank
  does not remove rows from the acceptance audit. Nonnegative least squares
  handles redundant binding constraints in the dual check.
- `require_interior` now classifies a final converged tie, allowing temporary
  constraints to release. Premature activation is not a boundary-optimum
  certificate. Global-optimality/arithmeticity and fixed iteration-count
  claims were removed from the optimizer docstring.
- LP candidates now require finite correctly sized output, successful solver
  status and an independent original-constraint/bound audit. Solver failure
  or missing candidates cannot be dereferenced or accepted.
- Corrected strict LP's weighted objective. Maximizing a common positive
  angle/dihedral/boundary margin (`t=epsilon`) prevents a slack objective from
  driving an angle to zero and causing a false negative. Normalized units,
  guaranteed slack, measured margins and the numerical evidence boundary
  are documented separately.

## Concrete before/after evidence

The [replay driver](angle-validation.py) reads the baseline source from Git
into a temporary directory, imports the maintained current source explicitly,
and writes [machine evidence](angle-solver-validation.json). It records source
hashes and dependency versions. No baseline file is altered.

| Case | Baseline reported value/status | Corrected value/status |
| --- | --- | --- |
| One equilateral triangle | `1.0151497106006686`, success | `1.0149416064096537`, passing KKT |
| Positive near-flat triangle start | Returned `4.743890901200666e-6` candidate, **failure**; angle-sum residual about `1e-6` after clipping | Converges to regular value `1.0149416064096535`; angle-sum residual near machine roundoff |
| 15 points, seed 2 | `19.113162627196726`, success | `19.112626012370175`, passing KKT |
| 50 points, seed 1002 | `76.60339035517823`, success | `76.60379512334639`, passing KKT |
| 50 points, seed 1007 | `81.45749975621857`, success | `81.45772627160687`, passing KKT |

The equilateral value has an independent 60-digit Clausen reference in the
machine report. Its old error was approximately `2.081041910149e-4`.
The near-flat row compares an unsuccessful old candidate with a successful
new solve; it is not an accepted historical optimum being revised.

The fixed eight-face strict LP counterexample formerly returned minimum
angle zero, slack `1/3`, and `realizable=False`. A supplied rational witness
with denominator 7 satisfies all normalized triangle sums, interior vertex
sums, positive-angle bounds, boundary inequalities and opposite-edge
inequalities exactly, with common margin `1/7`. The new LP finds that
positive margin. The exact statement is about this supplied witness, not
general exact LP solving or an embedding certificate.

A bounded scan of point counts `{8,15,30}` and seeds `0..29` found 36 old
strict false negatives among 90 generic Delaunay inputs. The new LP returns
audited positive witnesses for all 90. This is a deterministic regression
scan, not a prevalence estimate or global classification. A separate
30-seed, 15-point check found no additional old KKT failures among the
baseline-successful candidates; the release mechanism is instead directly
tested with a known constrained-triangle optimum and a fixed actual mesh
whose temporary dihedral constraint must be released.

Final-only tie selection changes legalization of the 15-point seed-2
fixture from one flip to two. Both executions reach the accepted strict
solution. The updated regression checks bounded nonzero work, state/count
consistency, repeated-run identical paths and the original final strict
residual thresholds. This is an algorithm-work change, not a speed claim.

## Validation

Working directory: `consolidated/packages/volume-toolkit`.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 \
/tmp/polyhedra-baseline-20261031/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_rivin_numerical_contracts.py tests/test_penner_rivin_regression.py \
  tests/test_rivin_legalization.py tests/test_rivin_solver_comparison.py
```

Final focused result: **60 passed in 1.76 seconds**, no warnings. The two
previous quadrature warnings disappear with the value-helper correction.
The tests include an independent SLSQP optimization using mpmath Clausen
values, a closed-form constrained maximum with redundant rows, bad solver
output, exhausted budgets, zero-dimensional null spaces, bad starts,
near-flat starts down to the smallest positive binary64 subnormal, rational
strict-feasibility evidence, and final-only tie classification.

Ruff and authored whitespace checks pass on the owned Python changes.
The interpreter imports the consolidated module, not the old installed
baseline wheel. This environment uses the already documented copied local
dependency snapshot; no fresh dependency resolution, full optional suite,
performance benchmark, or interval proof is claimed by this worker.

## Files and compatibility

Paths relative to `consolidated/packages/volume-toolkit`:

- `ideal_poly_volume_toolkit/rivin_delaunay.py`
- `tests/test_rivin_numerical_contracts.py`
- `tests/test_penner_rivin_regression.py` (approved final-tie contract update)
- `tests/test_rivin_legalization.py` (approved bounded-work assertion update)
- `docs/rivin-numerics.md`

Existing entry names, positional arguments and principal result keys remain.
New keyword-only budgets/tolerance and diagnostic fields are additive.
The boundary-vertex declaration must match the triangle-complex boundary.
`n_active_constraints` describes final near-binding inequalities; working-set
history/indices are separate. Exact flat angles are explicitly outside the
differentiable optimizer domain. Strict LP slack now means a common margin;
the legacy maximum-dihedral fields are its guaranteed upper bounds, while
actual measured margins are supplied separately. Historical outputs were
not relabeled or overwritten.

The parent owns shared architecture/changelog/module-index and book errata
updates. Independent review and final integrated checks remain with the
parent before committing.

## Documentation consulted

Context7 `/scipy/scipy/v1.18.1` supplied current constrained-optimization and
LP residual guidance, including SLSQP dictionary constraints and the removal
of the obsolete `nnls(atol=...)` argument. Installed SciPy docstrings verified
the actual `nnls(A,b,maxiter=...)` and `null_space(A,rcond=...)` signatures.
Primary sources: [SciPy optimization tutorial](https://docs.scipy.org/doc/scipy/tutorial/optimize.html),
[NNLS](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.nnls.html),
[null space](https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.null_space.html).

## Reporting corrections after independent review

The original independent review and its probe outputs remain preserved in
`angle-solver-review.md` and `angle-review-*`. The review found no additional
mathematical acceptance blocker, but requested corrections to public
feasibility language and objective-work counts. Thirteen added regression
cases failed before these corrections (`angle-reporting-before.log`).

The module header and formatter now describe numerical angle witnesses,
not an unconditional embedding or infeasibility conclusion. Strict mode
labels the common-margin objective and the separately measured minimum.
A positive subthreshold minimum of `5e-7` remains visible as positive and
below the documented `1e-6` acceptance threshold. An unsuccessful LP retains
its status and message without displaying an invented measured witness.

The public optimizer distinguishes a failed LP solver, a rejected LP
residual audit, and an audited result with no verified positive start.
The last case returns `no_positive_initial_witness`, including the measured
minimum and threshold, rather than saying the LP failed after successful
termination. The full initial LP result is retained as `feasibility_lp`;
its `solver_iterations` are separate from angle-optimizer `n_iterations`.
The legalizer's existing `lp_failure` termination vocabulary is preserved,
while its message now describes the absence of a verified positive start.

`n_volume_evaluations` now counts the starting value of each line search,
every attempted candidate value, and the final reported value. Instrumented
checks report **1/1** calls for an already stationary triangle and **14/14**
for the ordinary triangle start, correcting the former **0/1** and **7/14**.
Additional tests count rejected line-search values, a stationary zero-budget
run, a nonstationary zero-budget run, and an early failure with zero calls.
The counter correction does not alter the objective, steps or KKT gates.

The new focused output `angle-reporting-focused.log` records **73 passed in
1.85 seconds**, without warnings. Ruff and authored whitespace checks pass.
The numerical-contract document also explicitly distinguishes this free
corner-angle family from Section 9's prescribed-dihedral leading–trailing
coordinates.

`angle-reporting-review-probes.py` is a copy of the original reviewer driver
with a new output path/stage label and additional reporting/count assertions;
its numerical probes are unchanged. The original driver's SHA is recorded
in `angle-reporting-review-probes.json`. This owner-run recheck passed all
seven independent MP/SLSQP comparisons (largest value difference
`4.227729277772596e-13`), the exact rational primal/dual `1/7` check, eight
endpoint comparisons, the release fixture, and forced failure/fallback
checks. This is a rerun of the reviewer probes, not independent reapproval.

Fresh replay evidence is in `angle-solver-validation-after-reporting.json`,
produced by `angle-validation-after-reporting.py`. All five before/after
cases and the bounded 90-case strict-feasibility scan retain their previous
outcomes. Original evidence files were not overwritten by this correction.
Both fresh JSON reports record the final source hashes:

- Rivin: `65a388fc0682a32370c2ad886ef807852ae68df07f1a00d7f7b3a587f066f053`
- Geometry: `eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73`

No staging, commits, shared-document changes, or original-repository edits
were made. Independent re-review and integrated validation remain with the
parent.
