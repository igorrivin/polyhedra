# Section 9 independent re-review — 2026-10-31

Verdict: the three findings in `section9-review.md` are closed. Runtime and mathematical review passes, subject to the import-order lint cleanup and planned clean-commit artifact regeneration below. No new blocking mathematical, provenance, or packaging issue was found. This review did not edit implementation files, regenerate production artifacts, or commit changes.

## Corrections verified

1. **External and installed sources:** `source_provenance` now records stable source roles, project-relative or external locations, and hashes of actual source files. Required missing files raise a named error. Optional book files are explicitly recorded as unavailable. Regression tests verify external fixture/module hashes and a missing `geometry.py` failure. The package-verification agent independently confirmed an actual installed-wheel run using an external fixture, with `PYTHONPATH` unset and working directory outside the repository.

2. **Detached reproduction:** the generated ZIP contains the complete experiment driver, template, fixture, maintained numerical module subset (`variational.py` and `geometry.py`), a clearly labeled subset initializer, pinned dependency requirements, the toolkit MIT license and a payload manifest. Individual Python links now say they are inspection copies. The runner detects the explicit detached manifest and loads the bundled numerical subset. Missing book assets no longer prevent computation or rendering and are not offered as broken links. A focused subprocess test extracts the ZIP outside the checkout, removes `PYTHONPATH`, runs from another directory, and verifies the result and absent-book status.

3. **Unsigned-label overflow:** face, interior-vertex and elimination-index validation now rejects values outside signed-int64 range before conversion. The original `uint64(2**64-1)` vertex-alias probe is covered by the passing regression test.

The fixture-specific contract is also explicit. An external fixture must have the same parsed contents as the supplied rectangle fixture; changed off-origin parameters are rejected rather than being rendered with hardcoded prose for another experiment.

## Mathematical and provenance assessment

The mathematical operators and fixture identities are unchanged by these corrections. The sign convention, factor two, independent rational FEM construction, determinant 60, fifteen rooted forests, Schur factor 15/2, and independent 50-digit derivative comparison remain consistent with the canonical Section 9 statements. The wording still limits conclusions to this finite example and distinguishes numerical checks from exact arithmetic and a whole-chapter proof audit.

Detached execution records `source_commit=null` and `repository_dirty_at_start=null`, rather than treating the absence of Git metadata as a clean checkout. Original provenance is retained separately in the bundle manifest. Payload hash comparison is a separate provenance status: `bundle_payload_hashes_match` and `bundle_payload_mismatches`. `all_checks_passed` and the process exit status summarize the exact/numerical experiment checks, not payload integrity. A consumer auditing authenticity must inspect the separate payload-integrity status; this review does not conflate it with mathematical correctness. Current payloads all match their manifest hashes.

The package-verification agent separately reports successful corrected-wheel and detached-ZIP replays in `/tmp/polyhedra-core-verification-20261031`, containing only pip, NumPy, SciPy and mpmath. Its wheel run imported from the environment's `site-packages`; its ZIP run imported the project-relative bundled modules, reported matching payload hashes and explicitly absent optional book assets. Those are separate packaging-verification results, not additional full-suite executions by this reviewer.

## Executed source-tree checks

Used `/tmp/polyhedra-baseline-20261031/bin/python` (CPython 3.12.11), with bytecode writes, pytest cache and automatic plugin loading disabled. The import evidence confirms all four reviewed modules resolved under `consolidated/packages/volume-toolkit/ideal_poly_volume_toolkit/`, not the older wheel present in the baseline environment.

- Focused Section 9 suite: **11 passed in 11.73 seconds**.
- Full available suite, run once with collection errors continued: **279 passed, 18 skipped, 4 failed, 9 collection errors, 2 warnings in 41.75 seconds**.
- Every remaining failure was inspected through JUnit evidence: all four failures and eight collection errors are `ModuleNotFoundError: gymnasium`; the ninth collection error is missing `hypothesis`.
- The two existing quadrature warnings remain at `rivin_delaunay.py:760`, in the Penner–Rivin and legalization tests. They are not new failures.
- Compared with the original baseline of 242 passed and five failures, the final available suite includes 36 new passing tests and the corrected LFS inventory assertion. The remaining optional-dependency failures are unchanged. This is **not** a clean full-suite pass or a fresh online dependency-resolution result.
- Current HTML: all twelve local/anchor links resolve, with no duplicate IDs; extracted JavaScript passes `node --check`.
- Current ZIP: ten members, nine manifest-hashed payloads, no payload mismatch. Both maintained modules and the runner/template/fixture byte-match the current source files.
- Current result uses schema version 2, reports all exact/numerical checks passing, and has seven explicit source records. Every available source record's SHA-256 matches its current file.

Evidence files in this directory:

- `section9-focused.log`, `section9-focused.xml`
- `final-suite.log`, `final-suite.xml`
- `rereview-import-paths.json`
- `rereview-test-execution.json`

## Remaining boundaries

The parent independently found four Ruff E402 findings at `experiments/section9/run.py:31,32,33,35`, caused by deliberate bundle-path setup before the numerical imports. Resolve the import ordering or add a narrowly documented exception for the necessary delayed imports before committing. This lint cleanup was still pending when this runtime/math re-review ended. Recheck lint and the affected runner tests afterward; another complete suite run is unnecessary if the change only documents the existing delayed-import requirement.

The current generated outputs remain preliminary artifacts from a modified tree. Commit reviewed source, regenerate from that clean source commit, and commit generated outputs separately before claiming a clean reproducible release snapshot.

Browser interaction and visual layout remain unverified under the previously documented sandbox/browser restrictions. This re-review did not retry those operations. Static link and syntax checks are not browser QA, and the monograph has not received a complete proof audit or publication pass.
