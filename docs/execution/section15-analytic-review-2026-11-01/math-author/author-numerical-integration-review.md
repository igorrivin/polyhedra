# Section 15 numerical and documentation integration

Date: 2026-11-01. This supplements `author-review.md`; the earlier analytic report, snapshots, and manifest are preserved. The independent analytic approval is tied to chapter hash `2688ef6862492f93cd49de4c50017eb33496ad0d1b77cd8f4220150910a2ef1e` and ledger hash `8d5ba46372dda6a108bf913e30b661f87e16b4985b444ed8107d9feefb4c6c3d`. Both exact files were copied to `integration-baseline/book/` before numerical edits. These copies have the approved hashes and required no reconstruction.

## New numerical text

The chapter's only change from the approved analytic bytes is the numerical subsection. The six computed Q entries are taken from the 90-digit, C=1, T=14 rows in `computation/full-v1.json`, SHA-256 `bfb7bf75aa4522e794f2c6000863df786988a67bf92354d41d7075dfcee37a83`. Their six-decimal values are checked automatically against the table. The first is now `0.459086`, from `0.459086488736078952...`; the supplied `0.459087` remains unchanged in the historical JSON. The other five rounded Q values agree. The first-correction column is unchanged.

The three zeta=1 scaled residuals are newly computed as approximately `1.208081684`, `1.211366819`, and `1.208878763`. The supplementary negative point gives `Q_(1/160)(-1)=0.517966671856531...`. Across seven inputs, the recorded 60/90-digit difference is less than `4e-57`, and the contour/order difference is less than `1.3e-91`. These are observed agreements, explicitly not guaranteed digits.

The independent whole-Barnes matrix is `computation-review/independent-whole-q-matrix.json`, SHA-256 `183f963fef33d642a83c771de942acd3ee5c7bcb99874ccb54455743db3e1045`. It uses a combined convergent Barnes-log integral and QUADPACK in ordinary double precision. Its seven values agree with the multiprecision rows within `2e-12`. The chapter identifies this independent formula/backend comparison without treating its internal error estimates as certificates.

The new evaluator uses the exact centered log-S identity, with all five logs combined before exponentiation. A finite cotangent-derivative expansion approximates D_b with a rational uniform truncation bound; it does not substitute an Airy approximation for the quantum integrand. Its upward contour is `v=v_star+lambda*(C+i*t)/3`, with measure `dw/i`, hence C=3c in the proof. The three settings are 60 dps/C=1/T=12; 90 dps/C=1/T=14; and 90 dps/C=5/4/T=14 with two extra D terms. The shorter-cutoff extension is separately recorded. Selected direct D and full-log-S integrals, plus reflection and shift identities, check the special-function evaluation.

The rational bound controls series truncation conditional on the declared centered strip. Propagation uses a numerical absolute-integral estimate. Outer quadrature errors, tail-majorant evaluations and sign checks lack outward rounding. The chapter, ledger and shared documentation expressly exclude a total interval quadrature enclosure. Numerical agreement is finite evidence; the uniform theorem rests on its separately reviewed analytic proof. The original evaluator, raw output and rounding procedure remain unrecovered.

## Integration scope

The ledger adds a separate `s15.quantum_numerics` claim and now has 14 claims. It preserves the distinction between new exact-integrand evidence, the original unrecovered calculation, the frozen finite companion, and the analytic theorem. The six shared documents now recognize the completed bounded analytic review and new evaluator, keep source generation and integrated PDF verification as separate checkpoint records, and direct the next substantive review toward counting/mixing dependencies and the remaining chapters. They preserve the final-upload instruction and do not assert full-book review.

The source allowlist is exactly:

- `book/chapters/15-quantum-airy.tex`
- `book/claims/section15.json`
- `README.md`
- `book/README.md`
- `book/computational-status.md`
- `docs/INTEGRATION_STATUS.md`
- `INTEGRATION_PLAN.md`
- `experiments/section15/README.md`

The separately authored `experiments/section15_quantum/` implementation is outside this author's ownership. The prepared result path is `artifacts/section15_quantum/result.json`, with checkpoint `docs/execution/section15-analytic-review-2026-11-01/README.md`. The full-v1 result supplies the values used here; final approved-code replay, clean source generation, integration/PDF review and commit remain separate gates. No success for those later stages is assigned by this report.

## Preservation and checks

`audit-integrated.py` verifies all 607 labels and their order against the baseline commit; all 21 Section 15 labels and their order against the approved analytic snapshot; complete ledger label coverage; and the exact numerical-only chapter delta. It also checks all six rounded table rows and the two frozen historical file hashes. `git diff --check` passes.

Preserved historical files:

- `experiments/section15/historical-table.json`: `91ecc5703fe0089940825f8e165ab88e0693535067e8ca080736a0895f164011`
- `artifacts/section15/checks.json`: `1b275fb776a7a203cfada670bf37d4a5c428a463e24edafb38ed0e8c258f8404`

Final chapter hash: `efee2c699923ab31e4d7d48eeac57c60bf2ea088ea4ff17e617b9ed97202d6dd`.
Final ledger hash: `2a53176d95601bd09448326a34b203f1e05bd46dc6eee182226af36b24a2fb96`.
All eight final hashes and the explicit allowlist are in `integrated-author-manifest.json`; label and preservation checks are in `integrated-label-coverage.json`. The integration reviewer was notified of the final freeze, including the root-requested correction of two stale references to the prior quantum/surgery increment. No builds, installs, numerical reruns, commits, uploads or original-repository edits were performed by this author during this integration stage.
