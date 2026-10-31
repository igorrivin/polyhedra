# Initial integration status

The original toolkit and ipoly histories have been imported under `packages/volume-toolkit` and `research/ipoly`, respectively. Both source heads remain ancestors; exact subtree trees and 953 materialized source files were checked before their import commits. The monograph snapshot and 25-file duplicate map are recorded in provenance.

Original HF and maintenance workflows remain nested historical files and are inactive in this monorepo. The root CI workflow contains tests and integrity checks only. A remote and deployed Site have not been created by this step.

The toolkit data-integrity adapter has one necessary path correction: Git LFS reports repository-root paths even when called from the package directory, so the checker now filters to the package prefix and converts to package-relative names. Its existing test also allows new artifacts beyond the historical 407 while requiring unique, materialized, attribute-covered paths. The source currently contains 412 LFS paths.

Numerical correctness fixes and the Section 9 worked example are separate changes after these source-import checkpoints. The first increment's verification report will record their actual test results and remaining dependency limitations.
