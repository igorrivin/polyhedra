# First integration checkpoint

Date: 31 October 2026. This checkpoint implements the first bounded increment of the [accepted plan](../../../INTEGRATION_PLAN.md): preserve/import the sources, record the baseline, repair the reproduced core defects, and build one Section 9 computational companion. The full cleanup, monograph review, conversion and publication phases remain in progress.

## What is preserved and integrated

The single research checkout contains the toolkit at `packages/volume-toolkit`, historical scripts at `research/ipoly`, and unchanged canonical text at `book`. Both original Git histories remain reachable. Import verification covered all 953 original tracked files, all 396 unique LFS payloads, both Git bundles and all 39 monograph ZIP members. The [source map](../../../provenance/source-map.json), [backup manifest](../../../provenance/backup-manifest.json) and [independent integration review](integration-review.md) identify the source and import commits.

Original heads are toolkit `cc6b689652ce735f2098bb0a3235089210d764df` and ipoly `30ef40e23005509bd94d26f27dc48ea778832a50`. The independently reviewed import baseline is `c53387221dc6d000ac46c0b1ce44232c50f02a3c`. The original worktrees were preserved. Root CI enables checks only; the imported nested HF force-push workflow is inactive. The consolidated checkout has no configured remote, and this checkpoint makes no push or deployment claim.

## Correctness and computation work

- Exact-zero shear certification checks the original validated inputs, so rational values that underflow during float conversion cannot acquire an exact certificate.
- Rigid triangle development uses coherent orientation and actual-edge anchoring, checks numerical closure and angles, and explicitly reports its local numerical scope.
- Public Lobachevsky derivative helpers evaluate the correct formulas throughout the open angle interval and reject its endpoints.
- The Section 9 [guide](../../../experiments/section9/README.md), [HTML companion](../../../site/section9/index.html), [runnable reproduction archive](../../../site/section9/downloads/section9-reproduction.zip) and [result](../../../artifacts/section9/result.json) connect the text to a small checked example. Its exact Hessian determinant is 60, rooted-forest sum is 15, and Schur complement is 15/2.

The [core implementation report](core-defect-fixes.md) and [independent review](core-review.md) record the correction scope. The [initial Section 9 review](section9-review.md) preserves the three defects found in the preliminary implementation; the [implementation record](section9-implementation.md) and [independent re-review](section9-rereview.md) record their correction and subsequent verification. The separate [package review](package-verification.md) verifies installed-wheel and detached-archive behavior. These are dated review records and retain the results of the particular source state they examined. The generated result's source commit, dirty flag and hashes identify its own run.

The re-review's import-order lint follow-up is closed: the [final implementation record](section9-implementation.md) documents the narrow driver cleanup and eleven subsequent passing focused tests; the [final Ruff check](final-lint.log) passes for all seven changed/new Python files. This changes the driver hash but no mathematical operator or wheel module. The package review records its bounded final two-mode replay separately from the earlier full-suite run.

## Verification evidence and limits

| Check | Recorded evidence |
| --- | --- |
| Original full-suite attempt | [Baseline](baseline.md): 242 passed, 18 skipped, 5 failed, 9 collection errors. One real stale LFS-count assertion; all other failures/errors require unavailable Gymnasium or Hypothesis. |
| Consolidated suite at independent core review | [Review](core-review.md): 275 passed, 18 skipped, 4 failed, 9 collection errors. All 32 then-new tests pass; the LFS-count assertion is corrected. This is not a fully passing optional-dependency suite. |
| Available suite after Section 9 corrections, before import-order cleanup | [Re-review](section9-rereview.md): **279 passed, 18 skipped, 4 failed, 9 collection errors**, with two existing warnings. The 36 new tests and corrected LFS assertion pass. Every remaining failure/error is due to unavailable Gymnasium or Hypothesis. Focused Section 9 suite: 11 passed. |
| Final import-order cleanup | [Eleven focused tests](section9-implementation.md) pass again after the driver-only change; [Ruff](final-lint.log) passes on all seven changed/new Python files. The full suite was not repeated for that import-order-only change. |
| Integrity | 11 focused tests; 412 materialized LFS paths, 354 JSON payloads, two canonical input hashes and two manifest artifacts validated. |
| Packaging and CLI | [Corrected wheel and sdist](package-verification.md) built; all 47 package Python-file hashes match source, copy, distributions and installed wheel. Minimal installed-wheel imports and defect probes pass; installed CLI produces schema-valid tetrahedron volume 1.0149416063705312. The sdist was inspected, not separately installed. |
| Section 9 mathematics | Exact rational matrix/forest checks and twelve numerical checks pass for the fixed grid. Independent off-origin numerical Hessian discrepancy is approximately 1.78e-15. |
| Section 9 reproduction | [Minimal installed-wheel and detached ZIP replays](package-verification.md) each pass all twelve numerical and exact checks outside the source tree. External fixture/module provenance works; detached Git state and optional book absence are explicit, and bundle payload hashes match. |
| PDF sample | Four pages (1, 28, 29, 168) visually inspected. A font/CMap warning on three samples requires release-PDF investigation; the complete PDF has not been visually audited. |
| Browser/site | Source, JavaScript and download checks are recorded separately. Browser layout and interaction remain unverified: the sandbox rejects a localhost listener and the browser URL policy rejects local-file URLs. No Site was published. |

The Python 3.12 test environment was isolated but populated from existing local dependency snapshots after PyPI DNS resolution failed. [Exact versions](requirements-snapshot.txt) and [copy provenance](local-package-copy.json) are retained. The separate [minimal installed environment](package-verification-environment.json) contains only pip, NumPy, SciPy, mpmath and the corrected toolkit; optional GUI/RL/graph libraries remain absent. These checks establish execution on copied local snapshots, not a fresh dependency-resolution result. A complete development install, unavailable optional modules, GUI construction and the supported-Python/platform CI matrix remain outstanding. Existing quadrature warnings remain visible in the reports.

The [evidence inventory](evidence-files.json) records every copied report/log hash and any link-only adaptation. Its `force_add_paths` lists copied logs ignored by root Git rules so the commit step can add those exact evidence files without adding AppleDouble sidecars. Distribution artifacts and temporary environments remain outside the repository; their hashes and locations are recorded in the baseline and package evidence.

## Continuation order

1. Complete the final static checks and clean-source artifact sequence: reviewed code commit, regeneration with `dirty=false`, separate output commit, and comparison of recorded hashes against the actual runner, modules, fixture and text. The corrected installed wheel and detached archive have already passed independent runtime verification; retain that evidence and check the final generated bundle's payload identities. The final code/artifact commits must be identified in the continuation record. Clean-commit regeneration is still pending in this pre-commit checkpoint.
2. Finish Phase 2's remaining precision, solver failure, final-value and KKT/feasibility contracts. The current three fixes cover only part of that phase. Preserve historical output classifications and record any changed scientific values.
3. Expand Phase 3 from this dense finite example to the maintained companion algorithms, rank/constraint cases and optional SnapPy isolation. Keep the historical scripts unchanged and replace source-splicing only in new supported workflows.
4. Continue the [computational-status ledger](../../../book/computational-status.md), focused proof review and source modularization while preserving all theorem/equation labels. Reconcile the identified companion contradictions explicitly.
5. Recover or replace the missing Airy and torus evidence. The [local recovery report](evidence-recovery.md) found neither in the supplied material or reachable code history. Correct availability wording before publication if recovery remains unsuccessful.
6. Complete a full LaTeX-to-HTML conversion pilot, browser equation/navigation/accessibility checks, release-PDF review and reproducible computation downloads. Then settle authorship, text/companion licensing, canonical remote/visibility and source-download policy before a tested Sites release.

None of these local checks constitutes a general proof audit, rigorous interval certificate, complete fresh-install validation or public release. The plan's phase gates remain the release criteria.
