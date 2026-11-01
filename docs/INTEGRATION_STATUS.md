# Integration status

The [current normalization checkpoint](execution/normalization-review-2026-11-01/README.md) covers Sections 1–8 and Appendix A, with 41 claims in two ledgers and a [fixed exact companion](../experiments/normalizations/README.md). The chapter extraction preserved the expanded manuscript byte-for-byte and all 607 labels before revision. Independent computational review passed 497 weight vectors, 1,491 class samples, 512 SL₂ triples, 195 F-curve probes and all 11 regression tests. These finite checks do not establish general geometric or analytic theorems. The checkpoint records mathematical review and integrated PDF verification separately.

The checkpoint's output paths are `artifacts/normalizations/result.json` and `artifacts/normalization-review-2026-11-01/monograph-working-draft.pdf`, with their generation and verification recorded in its reports. Initial development evidence records its actual dirty tree. Existing Site exports and downloads, prior PDFs and Section 15/30 results remain frozen; they have not been regenerated for this increment.

The [prior Airy and torus checkpoint](execution/monograph-revision-2026-11-01/README.md) corrected evidence descriptions and added finite Airy checks and a length-64 replacement torus computation. The original exact quantum-integral rows and length-8192 torus run remain unreplayed, and both broader chapter reviews remain outstanding. The next substantive review is Sections 12–14 and 16; Section 15's analytic contour/tail review is still required. The optional-dependency full-suite failures and collection errors retain their recorded status. Upload and deployment remain the final publication step after manuscript and local-release verification.

The [computational-status ledger](../book/computational-status.md) and [integration plan](../INTEGRATION_PLAN.md) record the remaining scope. No full-monograph proof review or public Site publication is claimed.

## Preserved import checkpoint

The original toolkit and ipoly histories have been imported under `packages/volume-toolkit` and `research/ipoly`, respectively. Both source heads remain ancestors; exact subtree trees and 953 materialized source files were checked before their import commits. The monograph snapshot and 25-file duplicate map are recorded in provenance.

Original HF and maintenance workflows remain nested historical files and are inactive in this monorepo. The root CI workflow contains tests and integrity checks only. The import step did not create a remote or deployed Site; the later private Site registration and failed preview upload retain their separate recorded status.

The toolkit data-integrity adapter has one necessary path correction: Git LFS reports repository-root paths even when called from the package directory, so the checker now filters to the package prefix and converts to package-relative names. Its existing test also allows new artifacts beyond the historical 407 while requiring unique, materialized, attribute-covered paths. The source currently contains 412 LFS paths.

The subsequent [numerical-correctness checkpoint](execution/numerical-correctness-2026-10-31/README.md) and [Section 9 chapter checkpoint](execution/section9-chapter-2026-10-31/README.md) record their actual checks and dependency limitations. The [barrier checkpoint](execution/section9-barrier-2026-10-31/README.md) separately records the dense solver and export review. These completed local increments do not certify the untouched historical results or the remaining monograph.
