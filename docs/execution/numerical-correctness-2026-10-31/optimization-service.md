# H3 optimizer service corrections

Date: 31 October 2026. Base HEAD: `285a6cb71473ba1f238983e062662cf890cbba05`. The corrections are uncommitted. The callback defect found in independent review is corrected and ready for independent re-review; see the follow-up below. No original repository, historical research result, Git index or commit was modified by this worker.

The preceding [read-only audit](optimization-audit.md) and [baseline probes](optimization-audit-probes.json) remain unchanged. Those mocked solver-return probes test the service boundary; they are not evidence that ordinary SciPy returns inconsistent scores.

## Corrected behavior

- `optimization.py` checks each endpoint's finite real parameter vector, dimension and search bounds, freshly evaluates canonical binary64 Bloch–Wigner volume, and validates its complete boundary triangulation before ranking the candidate. Malformed and nonfinite parameter data are explicitly quarantined, with their original representation and rejection reason preserved; no dummy valid coordinates are substituted. A bad later candidate cannot erase an earlier usable one.
- The cached solver score is diagnostic, with its discrepancy from the recomputed objective recorded. Malformed/nonfinite cached scores are strings plus `null`, never NaN JSON. A valid but unconverged candidate remains usable with the raw DE convergence flag unchanged.
- Explicit serial polish after parallel DE compares verified pre-/post-polish volumes, including geometric validity, rather than trusting the cached scores. Solver work (`function_evals`) and subsequent canonical evaluation work (`verification_evals`) are separate. SciPy's single-worker built-in polish remains owned by SciPy; the service checks its returned endpoint.
- Shared serialization now emits schema v2, with the existing top-level and valid-candidate keys retained and explicit validation/evaluation diagnostics added. Manually constructed legacy records without validation evidence are marked `not_checked`. The shared serializer enforces strict JSON before CLI or GUI output. The CLI now labels the raw flag `Solver converged` and displays endpoint validation separately.
- `volume_threshold.py` rejects NaN vertices, multiple infinities, nonfinite/nonreal thresholds and boolean/invalid Fourier term counts. It retains the established implicit-infinity convention and canonical kernel delegation. Documentation now states binary64/finite-series numerical scope and does not claim exact or interval-certified threshold decisions.
- The v1 schema is byte-for-byte unchanged. Its baseline CLI fixture was copied exactly from the prior checkpoint, and both v1 and v2 validate under their own schemas. A narrow ordinary-Git exception keeps this small contract fixture outside the existing 412-path research LFS corpus. The integrity tool protects both schemas and this fixture as ordinary Git paths; it has no optimization-payload dispatch to change.

## Ownership and files

Paths are relative to `consolidated/packages/volume-toolkit/`:

1. `ideal_poly_volume_toolkit/optimization.py`
2. `ideal_poly_volume_toolkit/optimization_cli.py`
3. `ideal_poly_volume_toolkit/volume_threshold.py`
4. `tests/test_optimization.py`
5. `tests/test_optimizer_result_contract.py`
6. `tests/fixtures/optimization-result-v1.json`
7. `docs/schemas/optimization-result-v2.schema.json`
8. `docs/optimizer-result-contract.md`
9. `scripts/check_data_integrity.py`
10. `.gitattributes`

Shared architecture/module-index/release/changelog updates remain assigned to the parent documentation worker. In particular, module-index lines 31/200 and release-0.4.0 line 67 should distinguish the current v2 producer from preserved historical v1 artifacts. Historical reports should retain their original schema statements.

## Verification

Supported interpreter: `/tmp/polyhedra-baseline-20261031/bin/python` (3.12.11), working directory `consolidated/packages/volume-toolkit`. This is the isolated copied-dependency snapshot from the preceding checkpoint, not a new online dependency resolution.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 \
/tmp/polyhedra-baseline-20261031/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_optimization.py tests/test_optimizer_result_contract.py \
  tests/test_correctness_regressions.py tests/test_data_integrity.py
```

Initial result before independent review: **62 passed in 2.36 s**. [Captured output](optimization-service-tests.log). The cases cover stale scores, invalid winning candidates, rejected duplicate-vertex geometry, strict JSON, cached complex/NaN scores, retained nonconverged candidates, fresh-value polish acceptance, explicit status in CLI output, v1 preservation and threshold domains.

Ruff passes on the six changed/new Python files (including the CLI and integrity script). `git diff --check` passes on owned tracked code/attribute/test changes. New schema JSON parses and validates; contract Markdown links resolve to existing files.

`scripts/check_data_integrity.py --require-materialized` passes: **412 LFS paths, 354 JSON payloads, two canonical input hashes and two manifest artifacts**; all required payloads are materialized. [Captured output](optimization-service-integrity.log). Both new contract files resolve to ordinary Git attributes.

Current CLI smoke:

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 \
/tmp/polyhedra-baseline-20261031/bin/python -m ideal_poly_volume_toolkit.optimization_cli \
  --vertices 4 --trials 1 --maxiter 30 --popsize 8 --workers 1 --seed 42 \
  --output /Volumes/Lexar/lambda/devel/polyhedra/execution/numerical-correctness-2026-10-31/optimization-service-cli.json
```

The [result](optimization-service-cli.json) validates as v2 and strict JSON. It records volume `1.0149416063712777`, 185 SciPy function evaluations and one separate verification evaluation; the cached/recomputed objective discrepancy is zero. The raw solver converged and endpoint validation passed. [CLI log](optimization-service-cli.log).

The earlier checkpoint's same-command volume was `1.0149416063705312`; the fresh run differs by approximately `7.46514e-13`. This run includes the concurrent canonical-kernel precision correction, so the small change must not be attributed solely to endpoint reevaluation. The earlier artifact is preserved. [Machine summary](optimization-service-summary.json) records source hashes, versions, fixture provenance and both values.

## Independent-review callback correction

The [independent service review](service-review.md) found that `trial_callback`
received the internal trial object. Its frozen dataclass still contained a
mutable parameter array and validation mapping. A controlled callback changed
the regular tetrahedron's second coordinate from pi/3 to pi/2, leaving the
reported volume and returned vertices at `1.0149416064096535` while the returned
parameters recomputed to `0.9159655941772191`. Callback edits also changed the
stored validation evidence. This was mutation during optimization, not an
ordinary SciPy failure or a caller edit after the result was returned.

The service now passes a deep copy of each trial to the callback, including
arrays and diagnostic mappings. Internal history and winning geometry retain
their checked state. The callback signature and trial type are unchanged;
normal reporting callbacks still receive the same values. Completed result
arrays are still mutable, and the contract makes no post-return immutability
claim.

Two new regression cases mutate callback coordinates and validation evidence,
including nested callback diagnostic maps, immediately or through a retained
reference during a later trial. They check best parameters, returned vertices,
fresh volumes, all trial records, raw convergence flags, strict JSON and v2
schema validation. The existing ordinary callback check now compares values
and confirms the callback snapshot is a separate object.

The same focused command above now reports **64 passed in 2.68 s**.
[Captured output](optimization-service-callback-tests.log). Ruff passes on all
six changed Python files using `/opt/anaconda3/bin/ruff`; the supported Python
snapshot does not contain a Ruff module. Scoped `git diff --check` also passes.
[Ruff output](optimization-service-callback-ruff.log).

The author reran the reviewer's exact probe with only its output filename
redirected, preserving the original failure artifact and reviewer script.
The returned parameter and vertex volumes now both equal
`1.0149416064096535`; the callback's `-999.0` cached-objective edit does not reach
the internal record, and the ordinary checks and v2 validation pass.
[Recheck evidence](optimization-service-callback-recheck.json) and
[output](optimization-service-callback-recheck.log). This author-run reproduction
is not independent re-review approval. The machine summary preserves the
pre-fix hashes, records current source hashes and identifies the executed probe
and unchanged original failure artifact by SHA-256.

## Documentation and limits

SciPy documentation was resolved through Context7 `/scipy/scipy/v1.18.1`; the [optimization tutorial](https://github.com/scipy/scipy/blob/v1.18.1/doc/source/tutorial/optimize.rst) confirms that optimizer return objects separately report a solution, work and convergence. No new or undocumented SciPy parameter was introduced.

The checks establish numerical endpoint consistency and explicit reporting. They do not provide a global maximum, a rigorous error bound, an interval certificate, or a fresh full optional-dependency suite. No H4/H5/RL algorithms or historical ipoly source were changed. The v2 schema is an intentional migration: consumers that hardcode the closed v1 schema must select v2 for new outputs.
