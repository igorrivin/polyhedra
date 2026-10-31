# H3 optimizer endpoint and result contract

The maintained service is `ideal_poly_volume_toolkit.optimization`. Its CLI
and GUI share `optimization_result_to_dict`; they do not own separate
volume evaluators. Results are numerical evidence on represented binary64
coordinates, without an interval enclosure or a global-optimum certificate.

## Endpoint acceptance

Before a trial can become the best candidate, the service checks that its
parameters are a finite real vector of the expected size, lie within the
declared search bounds, give a finite positive canonical Bloch–Wigner
volume, and admit the complete boundary reconstruction through the existing
triangulation validator. A failure invalidates that candidate and leaves any
earlier valid candidate available.

The volume is recomputed from the endpoint. The optimizer's cached objective
is retained as a diagnostic; it does not supply the reported volume or rank
the candidates. A discrepancy is recorded as
`abs(cached_objective + recomputed_volume)`, since the minimized objective is
negative volume. Nonfinite or malformed cached objectives are represented by
`null` plus their string representation.

For a serial local polish after parallel differential evolution, both the
pre-polish and polished endpoints receive the same checks. The polish must
converge and improve the recomputed volume to replace the original candidate.
For the single-worker path, SciPy owns its built-in polish and the service
checks the final returned endpoint.

## Status and work accounting

Each trial retains the existing fields:

- `success`: the differential-evolution convergence flag. A successful local
  polish does not overwrite a failed DE flag.
- `valid`: whether this record has a usable numerical candidate volume.
- `volume`: the recomputed candidate volume, or `null` after rejection.
- `function_evals`: SciPy's reported function evaluations, including polish
  work accounted for by the service.

Schema v2 adds `verification_evals`, the number of subsequent canonical volume
evaluations attempted during endpoint checking. This excludes structural
checks and should not be interpreted as equivalent to optimizer iterations
or elapsed time. The statistics object sums this separate count. SciPy's
`OptimizeResult` exposes optimizer work and convergence independently of the
solution; see the [SciPy optimization tutorial](https://github.com/scipy/scipy/blob/v1.18.1/doc/source/tutorial/optimize.rst).

The new `validation` object has status `verified`, `rejected`, or
`not_checked`, with a reason and cached-objective diagnostics. `verified`
means the numerical endpoint checks above passed. It does not mean the
stochastic search found a global maximum. A useful candidate from an
iteration-limited run can have `valid=true`, `success=false`, and
`validation.status="verified"`.

Malformed or nonfinite parameter vectors are quarantined as an empty
parameter array, with the original representation in
`validation.invalid_params_repr` and the reason stated explicitly. Finite
vectors with the wrong size or invalid bounds retain their actual values.
Rejected candidates never acquire replacement coordinates. Manually
constructed legacy records without verification evidence are marked
`not_checked`. The shared serializer rejects any remaining NaN/Infinity,
including in manually built records or adapter settings, before either
adapter writes JSON.

Each `trial_callback` receives a detached copy of the trial, including its
parameter array and validation diagnostics. A callback may edit or retain
that snapshot without changing the service's verified history or selected
candidate. This boundary does not make the arrays or mappings in a completed
result immutable; callers remain responsible for their own subsequent edits.

## Schema migration

Current producers emit [`optimization-result-v2.schema.json`](schemas/optimization-result-v2.schema.json).
Existing top-level and valid-candidate keys remain, and the new validation
and work fields are explicit. Consumers that check `schema_version` or use
the closed v1 schema must select v2 for newly produced records.

The historical [`optimization-result-v1.schema.json`](schemas/optimization-result-v1.schema.json)
is unchanged; historical files are not rewritten or reclassified as newly
verified. The small test fixture
[`optimization-result-v1.json`](../tests/fixtures/optimization-result-v1.json)
is a byte-for-byte copy of the integrated baseline artifact
`docs/execution/2026-10-31/tetrahedron-cli.json`, with SHA-256
`f8408759dd9a0b46f047bb4fb58ff9f4f1811a80c5ca22b4277ff66f3d8f8558`.
Both schemas and this contract fixture are ordinary Git files, separate from
the research artifact corpus in Git LFS.

## Threshold API

`volume_threshold` delegates its default special-function evaluation to the
canonical binary64 kernel. `series_terms=None` selects that default;
an explicit positive integer selects the finite Fourier approximation.
Booleans are not accepted as term counts. No path in this module is called
exact arithmetic.

NaN coordinates, multiple infinity entries, and nonfinite/nonreal thresholds
are rejected. A single infinity point is supported, and infinity remains
implicit in finite-only lists under the historical API convention. The
ordinary comparison returned by `volume_exceeds_threshold` is numerical;
it does not certify a near-equality threshold decision without a separately
validated error bound.
