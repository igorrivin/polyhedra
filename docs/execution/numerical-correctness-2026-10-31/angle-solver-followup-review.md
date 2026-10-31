# Independent follow-up review: Rivin numerical corrections

**Approved for the reviewed numerical/reporting scope. No remaining blocker
was found.** Both correction groups in `angle-solver-review.md` are resolved.
This approval is tied to the exact source bytes below, not to later edits.

Final SHA-256, verified before and after the independent replay:

- `rivin_delaunay.py`:
  `65a388fc0682a32370c2ad886ef807852ae68df07f1a00d7f7b3a587f066f053`
- `geometry.py`:
  `eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73`

## Reporting corrections verified

The module header and public formatter now describe a numerical angle
witness, distinguish the strict common-margin objective from a measured
minimum angle, preserve the positive value `5e-7` in readable output, and do
not promote either an unsuccessful run to exact infeasibility or an angle
assignment on a disconnected complex to a disk embedding.

The initial-LP failure path now distinguishes solver failure, failed residual
audit, and an audited result below the positive-witness threshold using
`feasibility_lp_failed`, `feasibility_lp_audit_failed`, and
`no_positive_initial_witness`. The last path no longer says that a successful
LP failed. All three retain the original LP result, including the numerical
margin, raw status/message, threshold, audit, and LP iteration count. These
early failures remain unsuccessful, report zero angle-optimizer iterations
and zero objective evaluations, and have `evidence_status=not_verified`.
All three complete results serialize with `allow_nan=False` after NumPy
conversion. The rare failure-state tests are explicitly controlled API-state
probes, not invented naturally occurring mesh fixtures.

The numerical-contract document now explicitly distinguishes this free-angle
inequality optimization from Section 9's prescribed-dihedral,
leading-trailing coordinate family. Its witness, rank, KKT, and geometric
scope statements are consistent with the implementation.

## Work-count corrections verified

An independent wrapper measured actual `_angle_structure_volume` calls:

| Case | Reported | Observed | Outcome |
| --- | ---: | ---: | --- |
| Stationary LP start, zero budget | 1 | 1 | Numerical KKT passed |
| Nonstationary feasible start | 14 | 14 | Numerical KKT passed |
| Nonstationary start, zero budget | 1 | 1 | Unsuccessful, budget exhausted |
| Nonpositive initial angles | 0 | 0 | Explicit initial-state failure |
| Infeasible initial angles | 0 | 0 | Explicit initial-state failure |
| Forced rejected line-search trials | 57 | 57 | Explicit line-search failure |

The counter includes line-search starting values, accepted/rejected candidate
values, and final reported volume. LP iterations remain a separate field.
The new product tests meaningfully instrument calls rather than restating a
counter formula, and exercise both zero-work failures and rejected trials.

## Numerical invariants replayed

The independent seven-case MP/SLSQP comparison from the first review was
rerun against these final bytes in a separate evidence directory. It again
covered ordinary boundary meshes, the actual constraint-release fixture,
and small random meshes. All toolkit/reference solves succeeded. Maximum
objective difference was `4.23e-13`; maximum original equality residual
was `1.78e-15`; no positive inequality violation was measured; maximum
reported full stationarity residual was `7.09e-13`. The full original
constraint reconstruction did not use toolkit matrix/topology helpers.

The independent exact rational primal and dual verification again proves
common-margin optimum `1/7` for the fixed finite LP. All eight 400-digit
Clausen endpoint/value probes passed. Constraint release, forced singular
curvature recovery, visible line-search failure, zero-budget failure, and
strict JSON metadata checks remained valid. The corrected reporting/count
paths do not loosen the primal/KKT acceptance gates or final-only dihedral
tie classification.

## Crosscutting anti-pattern checks

- No coordinate clipping in the corrected angle optimizer: positive-domain
  steps preserve the affine problem, and invalid initial states fail visibly.
- No truncated Fourier final values: the corrected optimizer and Lobachevsky
  helper use the canonical binary64 kernel, with independent MP checks.
- No omission of dependent/original rows from final acceptance: rank-reduced
  solves are followed by full original primal and KKT residual checks.
- No unconditional realizability/embedding or exact infeasibility status in
  the corrected public witness report or module scope statement.
- No success created by budget exhaustion: a nonstationary zero-budget state
  fails; an already stationary state succeeds only through its numerical KKT
  and original-constraint audit.

The legacy `refine_geometry_for_volume` cached `result.fun` reporting behavior
is outside this corrected angle-optimizer contract and this follow-up review.
It has not been silently promoted to the new evaluation-accounting or
final-recomputation guarantees, and no extra fix to it was made here.

## Validation and preservation

- **73 focused tests passed in 2.00 seconds**, using the source package cwd
  and `/tmp/polyhedra-baseline-20261031/bin/python`, with bytecode generation,
  pytest cache, and plugin autoload disabled as requested.
- **Ruff passed** on the Rivin module and three changed test files using the
  existing `/opt/anaconda3/bin/ruff` 0.12.0 executable.
- **`git diff --check` passed.** No full-suite run was attempted by this
  reviewer; integration and the separate geometry/service review remain
  the parent's responsibility.
- Hash checks confirm that the prior report, probe script/JSON, and original
  test log/XML were preserved unchanged. No product source, original
  repository, commit, or remote was changed by this reviewer.

Final evidence is in `angle-independent-followup/`: the independent
numerical replay and `final-contract-probes.py/.json/.log`, plus hashes of
the preserved prior evidence. Focused outputs are `angle-followup-tests.log`,
`angle-followup-tests.xml`, and `angle-followup-ruff.log` beside this report.

This is bounded implementation validation, not exhaustive mesh coverage,
global classification, a topology/embedding certificate, an interval proof,
or a new review of the multiprecision geometry kernel.
