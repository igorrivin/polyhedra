# Independent Section 32 and Appendix B review

Decision: **one targeted source correction required (CV01)**. All 66 claims were reviewed: 15 research questions, 43 convention rows covering all 28 original rows, and eight narrative/source statements. No canonical source was edited.

The reviewed author freeze is `ad43dfcb8eb18fa04a3f60ec88186066f873e132c0e9884459f1e91f18a84025`. Its subject files are:

| File | SHA-256 |
| --- | --- |
| `book/chapters/32-open-questions.tex` | `c831bf85ab0c6cb7f5ed46509212ce5dc1549c05c5723be3c035c928a409fc21` |
| `book/chapters/appendix-b-conventions.tex` | `b57a96b3f141e0d372b26dbb710d1ec0fa8e8a4a8ac8f0dd04b4ce0432f99a74` |
| `book/claims/section32-appendixb.json` | `0bf0a62df0e81ae502d0408935cb1fee80b0db9a85be8e0d58c73367773dfd5a` |

## Required correction

**CV01 — Question 1's positive-boundary comparison has an origin-cusp locator.** At Section 32 lines 20–22, the question about four strictly positive geodesic boundary lengths points to `eq:treevolume`. That displayed BMZ formula has domain `M_{0,m}(0,lengths)` and explicitly requires an origin cusp (Section 4, lines 213–234). The relevant positive-boundary result is the following Zonneveld paragraph (lines 236–245): a selected pair has `L1<L2`; equal-length volume values follow by continuity.

Point the comparison to that positive-boundary extension and retain those scope distinctions. Keep the requested direct hyperideal integration open, and keep the distinction between spine/tree cells and hyperideal angle cells. Update the corresponding `s32.q01` locator/wording and source hashes without adding labels. A targeted paragraph/ledger/hash recheck is sufficient if the remaining material stays unchanged.

## Mathematical and exposition coverage

`claim-coverage.json` records an individual disposition and actual source locations for every claim. The other 65 claims have no required finding. In particular:

- The Airy theorem remains the pole-cleared equal-label family with bounded real transition parameter and additive error. Finite screened periods, spectral continuation with a tail input, fixed-shape root-of-unity results and the stricter refined label sequence are not merged into a general joint degeneration theorem.
- Local filling coefficients and torsion identities do not become an unconditional quantum surgery result. The cited hypotheses retain the nonzero net geometric sector, competing contributions, smooth-filling domain and endpoint limits.
- The weighted mixing statement keeps both endpoints and the reciprocal Jacobian. Preserving the exponent requires the derivative terminal test `(h+V)G` with the stated function domains and `0<delta<=h`. Nonlinear extraction stability, noncompact tails and the distinct marked-torus measure remain separate.
- The norm-ball target keeps the supporting-row compatibility condition. Counts retain signs and boundary membership; converting campaign hyperbolic lengths to the normalized gauge requires division by the systole. Finite data do not determine the all-scale geometric modulus.
- Positive geometric traces remain distinct from signed character traces. The two N labels and one H label per simple torus class retain equal-length multiplicity. Cusp truncation, the no-geodesic-boundary gap scope, cuff direction matching and Basmajian's oriented/unoriented factors agree with the frozen geodesic definitions.
- FN/Beltrami form scale, ineffective stabilizers, two tetrahedral sheets, signed lambda lengths, quantum parameter squares, half-log peripheral variables, charge labels and torsion rescaling agree with their actual chapter definitions. The source paragraph correctly inherits the bounded Mondello/CDE/Budd statement audits.

The questions do not declare their own resolution a publication requirement, and neither finite evidence nor an author snapshot is promoted to independent approval. Rendered longtable layout remains a later build/visual check.

## Independent verification and limits

`verify_scope.py` is an independent standard-library checker, not the author's checker. `independent-static-verification.json` passes 98 hash/size pins; all 34 exact earlier approved source/ledger files; 155 claim-dependency occurrences (127 unique pointers) and inherited statuses; all 36 declared existing-result fields; and the exact 97-path metadata delta. The initial author evidence remains unchanged, both chapter files are unchanged by revision v2, and each geodesic observation differs from its final author source only by one removed EOF blank line.

Expansion from `book/main.tex` has 36 files: wrapper, main manuscript and 34 chapter units. Against Git baseline `151673b1817e66aae493eb7da1be5ddf49adfe0f`, all 607 original labels remain in order, with only the six declared geodesic additions, for 613 unique labels. There are 129 bibliography keys; the owned references and citations resolve. Both owned labels, all question titles/order and the 28 original convention-row mappings/order are preserved.

Quantum source acceptance is inherited from exact record `c631f5ed63513246adf7bbec958c3298ab577861ee02f1d359ff6ca25b7c4dd9`, including its external-source access limits. Geodesic conventions were compared with author freeze `38994ff43e952ff42ccafb4d56c44e51c385a0092d156e3d35cdbcf1041d7eec`; this review does not assign the pending geodesic approval. The seven result records were read and hashed, not numerically replayed. The frozen handoff's 14 groups remain planned-contract entries; later implementation/review/result binding belongs to integration.

This review reuses explicitly hash-bound primary-source statement reviews within their recorded scopes. It is not a new complete audit of external proofs or source-PDF bytes. No numerical solver, numerical campaign, PDF marker/build, rendering, installation, staging, commit or upload occurred.
