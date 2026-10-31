# Independent H3 service, threshold, and schema review

Date: 2026-10-31. Decision: **changes requested** for one reproduced callback
isolation defect. The other reviewed contracts pass the focused checks below.
This report is read-only with respect to implementation, tests, schemas, and
the original repositories; only outer execution evidence was written.

## Blocking finding: callback mutation invalidates verified records

At `ideal_poly_volume_toolkit/optimization.py:636–642`, the service appends its
internal trial to history and passes that same object to `trial_callback` before
copying the winning parameters. The frozen dataclass contains a mutable NumPy
array and mutable `validation` mapping. The array also comes from the checked
endpoint. Thus an otherwise supported callback can change internal state while
`optimize_ideal_polyhedron` is running.

The independent probe returns a regular tetrahedron from a controlled solver,
then its callback changes the second parameter from pi/3 to pi/2 and changes
the validation mapping. The returned result has:

| Field/check | Observed value |
|---|---|
| Reported best volume | 1.0149416064096535 |
| Volume recomputed from returned best parameters | 0.9159655941772191 |
| Volume recomputed from returned finite vertices | 1.0149416064096535 |
| Parameters reconstruct returned vertices | false |
| Serialized trial validation status | `verified` |
| Internal cached objective after callback edit | -999.0 |
| v2 schema accepts the serialized record | true |

The last point is expected of a structural schema; the service must preserve
the numerical invariant before serialization. This probe mutates the callback
argument **during** optimization. It does not mutate a completed result after
return and does not allege that ordinary SciPy produces inconsistent results.

Required correction: give callbacks a detached snapshot, including arrays and
validation/raw-diagnostic mappings, or an equally effective immutable interface.
Preserve the verified internal history and winner. Moving only the winner copy
ahead of the callback would still leave trial evidence mutable through the
callback reference. Add a regression that edits both callback coordinates and
validation evidence, then checks returned best coordinates, vertices, fresh
volume, trial history, and serialized diagnostics. Also retain a callback
reference and exercise it on a later trial to catch delayed aliasing.

The parent was notified and confirmed this correction is required. No
implementation correction was made by this reviewer.

## Verified behavior outside the callback defect

- Endpoint acceptance recomputes the canonical binary64 volume, checks a finite
  real parameter vector with the expected dimension and search bounds, and
  reconstructs the complete boundary. Earlier valid winners survive rejected
  later candidates. Controlled bad candidates cover NaN, infinity, nonnumeric,
  complex, boolean, non-vector, wrong dimension, bounds, degeneracy, and duplicate
  vertices. Malformed values are explicitly quarantined with diagnostics;
  finite rejected vectors retain their coordinates.
- Fresh-volume ranking beats deliberately misleading cached objective values.
  Cached scores remain diagnostics. Valid unconverged candidates retain
  `success=false` alongside `validation.status="verified"`. This is a service
  contract test, not evidence of an ordinary SciPy cache discrepancy.
- Parallel-worker serial polishing checks both endpoint geometries and accepts
  only an improved verified volume from a converged local polish. A controlled
  case with deliberately reversed cached score ordering chooses the geometric
  improvement, keeps raw DE nonconvergence, reports 18 optimizer evaluations
  from 11 + 7, and separately reports two verification evaluations. Rejected
  polish and invalid initial endpoint paths are covered by the focused tests.
- A separate real SciPy run (4 vertices, seed 321, maxiter 5, popsize 4) reports
  volume 1.014941606409507, 60 optimizer evaluations and one verification
  evaluation. It honestly retains the iteration-limit failure flag. Fresh
  recomputation and returned geometry agree; the v2 payload validates.
- The serializer rejects nonstandard JSON NaN/Infinity, including caller settings.
  Legacy manually constructed records without verification evidence get
  `not_checked`. Existing valid-result keys remain present in v2. The historical
  v1 fixture validates, is byte-identical to the original integrated CLI artifact,
  and has SHA-256 `f8408759dd9a0b46f047bb4fb58ff9f4f1811a80c5ca22b4277ff66f3d8f8558`.
  The v1 schema remains at SHA-256
  `7a224b6c08a4380df70309f391d725ec1cb6a1abf0de843f5bbc04f80b5a4511`.
- CLI labels distinguish raw solver convergence from candidate validation.
  Threshold tests reject NaN coordinates, multiple infinity entries, undefined
  or nonreal thresholds, and boolean/nonpositive/noninteger approximation term
  counts. Additional independent probes reject NaN and either sign of infinity
  as term counts. Finite-only and explicit-single-infinity inputs preserve the
  historical convention and agree on the regular tetrahedron.
- Documentation correctly describes the default as binary64 numerical evaluation
  and explicit finite-series evaluation as an approximation. It does not claim
  interval certification, near-threshold rigor, or a global optimum. Boundary
  verification is not represented as an optimality certificate.
- Exception handling is limited to expected data, triangulation, and arithmetic
  failures. No new broad `except Exception`, fabricated convergence, or test
  weakening was found in the reviewed change. Test changes from artificial
  cached scores to actual geometric volume ordering are appropriate for the
  new endpoint contract. Ordinary Git/LFS path exceptions are narrowly scoped
  to the schema and historical contract fixture.

## Independent evidence and provenance

The ten author-owned files from `optimization-service-summary.json` were
reviewed, together with the audit, contract documentation, and schema v1.
Their hashes exactly matched that manifest at the independent probe. The
probe checks the hashes again at its end; they were unchanged. Full hashes,
resolved import paths, interpreter and dependency versions, and all probe
records are in `service-review-probe.json`. The source kernel SHA-256 was
`6b779e418e9a5328404b7cb18be9c2cdf7226a6c480fe5e235df0490cceaa51e`.
Kernel mathematics has a separate independent reviewer; this review checks
the service's use of that kernel.

Commands ran from `consolidated/packages/volume-toolkit` with
`/tmp/polyhedra-baseline-20261031/bin/python` (Python 3.12.11), bytecode disabled,
third-party pytest auto-loading disabled, and the isolated matplotlib cache.
The probe additionally inserts the explicit package source path and records
the resolved imported files, avoiding the stale installed wheel.

- Focused pytest: `tests/test_optimization.py`,
  `tests/test_optimizer_result_contract.py`, `tests/test_correctness_regressions.py`,
  `tests/test_data_integrity.py`: **62 passed in 2.09s**.
  Evidence: `service-review-tests.log`, `service-review-tests.xml`.
- Ruff for the six changed Python files: **all checks passed**.
  Evidence: `service-review-ruff.log`.
- Independent probe: ordinary checks pass; callback invariant fails as described.
  Evidence: `service-review-probe.py`, `service-review-probe.log`,
  `service-review-probe.json`.

The full suite was deliberately not run during this review, as other numerical
work was still in progress and the parent requested a stable-source gate first.
The 62 passing focused tests do not establish a clean full-suite baseline or a
proof of global numerical correctness. Approval of this service increment
requires the callback correction and a bounded independent follow-up.
