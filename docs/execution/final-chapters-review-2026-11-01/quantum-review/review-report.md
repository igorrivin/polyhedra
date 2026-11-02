# Independent review of Sections 10–11

The mathematical text and repaired claim ledger are accepted at the exact hashes below. All 61 ledger claims and all 48 preserved labels have been reviewed. The sole required finding, QR01, was repaired by adding two direct dependency hashes. A final independent byte comparison verified that these are the only ledger changes, all 11 dependency pins match the live files, and both chapter texts are unchanged. No required findings remain. No mathematical source-text repair was needed.

| Subject | Reviewed SHA256 |
| --- | --- |
| `book/chapters/10-quantum-introduction.tex` | `010a50a8f5205255bef2417f76515fff8962a443ea835c30bfcee02846c5ebfb` |
| `book/chapters/11-quantum-degeneration.tex` | `5a62080dbc2320f57efec073aa803cdff20dd06c05529dc7e064346cf0f47db9` |
| Final `book/claims/sections10-11.json` | `34dbb6255dc468cb796bb3a129eeaf37ac0c5f4dc358abfd73030e64331b3539` |

The accepted author revision-v2 manifest hash is `f043f6943bd124638802bfdb5d5e7505269143f54046eea93d298345191c0620`. The original ledger hash `ea22e86c4399d4d3fcf83c938144373c89367cb7f9ce1a074b866499000ce1cb`, original author manifest hash `107eda60080662c39b747bfa98fbbca765c2e3fa18b6d161960057128dfe1456` and original handoff-evidence manifest hash `ac70f770daa0912a229c77c3a66491cb4170b27d77f8dfcf264d6d2e356cd270` remain preserved under `initial-author-freeze/`. The accepted bytes are copied under `final-author-freeze/` and identified in `final-acceptance.json`. The review used the approved pure-extraction snapshot based on commit `151673b1817e66aae493eb7da1be5ddf49adfe0f` for its own chapter diffs. The chapter heading sequences and all 48 labels, including their order, are unchanged.

## Evidence and coverage

`claim-coverage.json` gives a separate assessment for each of the 61 claims, including its hypotheses and scope. `label-coverage.json` maps every preserved label to source lines and ledger claims. `initial-identity-check.json` records the frozen subjects, initial dependency checks and label comparison; `independent-structure-check.json` and the two independent `.diff` files record the extraction comparison.

The reviewer read both complete chapters, all ledger entries, both author revision diffs, the computational specification and relevant dependencies in Chapters 8 and 12–16. The nine initially pinned dependency files matched their declared hashes. The review checked consistency with the prior WP scaling, normalized quantum comparison, Airy and Dehn-filling conclusions without extending their claims. It did not rerun their prior computational artifacts.

The local analytic arguments were checked independently. The separate numerical and exact-algebra probes were written from the formulas and independent comparison constructions; the author scratch program was not used as a verifier or oracle. Successful finite probes supplement these analytic checks and are not substitutes for proofs of limiting statements.

## Main mathematical checks

The figure-eight product argument has the right maximum, including the adjacent tie when six divides the color. The initial decreasing segment does not create a larger maximum: the final cyclotomic product is `N^2`, exceeding the empty product. Subtracting the endpoint logarithm and using Stirling justifies the improper Riemann sum. The maximum-versus-sum gap is at most `log(N)/N`, and the Lobachevsky symmetries give the displayed figure-eight volume with the stated `2*pi/N` normalization. The finite half-power convention is consistent with the reduced Jones normalization.

For the compact-disk q-product expansion, the scalar remainder divided by its argument extends continuously at zero and stays bounded on the positive axis. Thus the termwise error is bounded by a constant times `epsilon*sum rho^m`, uniformly on `|z|<=rho<1`. This does not continue the estimate automatically to roots of unity or onto the unit circle. The quantum shape equation has the correct sign because differentiating `Li2(exp(-Z))` gives `log(1-exp(-Z))`.

The stationary-phase paragraph has the required local assumptions: a holomorphic phase, a nondegenerate critical point, an oriented descent cycle along a fixed parameter ray, controlled amplitude derivatives and a separately controlled complement. Its determinant factor is local; the text does not infer a global cycle decomposition. The torsion passage accurately identifies Conjecture 1.8 in the cited Dimofte–Garoufalidis source, and says the identification is not proved here. It makes no blanket claim about everything remaining open in 2026. The established Wong–Yang special case remains explicit.

The Chern–Simons variation, the multiplier half-log convention and the boundary symplectic factor agree. Translation by `hbar` gives the Weyl factor `exp(hbar/2)`. Differentiating the filling generating function gives `dG=b_core*da/2-v*du/2`; the combined Hessian is `D/(2*q)`. The Fourier normalization reduces its dependence to `D^(-1/2)` with the stated phase and square-root qualifications. This is not a direct torsion evaluation.

The Liouville convention is consistent with source charges equal to twice the chapter's `alpha`. The initial bootstrap pair-sum domain is correctly translated to the chapter's ordering of marks. The screening specialization has `s=-1` and lies outside that initial real-domain integral statement, so charge continuation is kept separate. The first-moment inequalities are strict; reference-metric factors cancel; local singularities are integrable for `mu_i<1`, and the integrand decays as `|w|^-4` at infinity. The curvature and WP factors agree with Chapter 8. Finite period estimates are not presented as bounds on the infinite fusion spectrum.

The double-sine leading functional equations and reflection normalization agree with the stated classical phase. The introductory formal limit is not promoted to an independent uniform theorem; the later proved uniform input remains in Chapter 15.

The Klein metric determinant gives density `(1-|x|^2)^-2`. The homothetic expansion, moment coefficients and explicit nonnegative scalar tail are correct. The Lorentzian face-normal expansion gives the displayed interior-dihedral coefficient and the first-curvature identity `sum L_e*b_e=-3*V`. This homothetic path is kept distinct from the fixed-conformal angle path, and differentiation of the remainder is qualified. Rank loss of the Euclidean normal Gram matrix explains why a fixed-shape hyperbolic asymptotic cannot by itself yield a uniform flat-limit statement.

For the compact model, a finite cover of a measurable compact set, the stated uniform exponential estimate and locally uniform WP coefficients provide a bounded integrable majorant. Dominated convergence therefore proves the displayed compact integral limit. No noncompact tail domination, full state-sum invariant or regeneration theorem is inferred.

## Primary-source audit

`independent-source-review.json` contains 23 source records with exact version URLs, inspected statements or pages, and access limits. Selected statements were retrieved in full text from 20 sources. Hodgson's thesis was checked only against author-hosted bibliographic metadata; Witten's 1989 Jones paper only against publisher metadata and abstract. Gukov's cited full text could not be retrieved independently in this review; overlapping background was checked in Dimofte and Witten's later accessible papers. No external full proof or external PDF byte hash is claimed.

Two critical normalization checks were performed directly against the source statements:

- [Chen–Murakami, arXiv:1706.04887v3](https://arxiv.org/pdf/1706.04887v3), pages 1–3: Theorem 1 is the general exponential limit with its admissibility and ideal/ultraideal vertex condition. Theorem 2 uses rational limiting data with odd numerators and denominators and its exact odd-level sequence. Its root is `exp(4*pi*i/r)` and the prefactor is `sqrt(2)*pi`, not `sqrt(2*pi)`. The revised text preserves this distinction.
- [Costantino, arXiv:math/0611399v4](https://arxiv.org/pdf/math/0611399v4), page 3 notation, page 4 Definition 2.4, pages 7–8 Definitions 3.1–3.2 and page 10 Theorem 3.9: evaluation means the leading Laurent coefficient after removing the pole; the geometric quantity is the doubled D-block volume. The revised text does not conflate it with ordinary substitution into a singular symbol or the volume of one tetrahedron.

The source table also records the exact bootstrap domains, first-moment range, quantum-sine convention, spherical recoupling regime, and source-specific torsion qualification. The independently checked scope is the cited statements and their applicability here, not full reproof of the external literature.

## Independent bounded probes

The fresh reviewer command was:

```
/tmp/polyhedra-baseline-20261031/bin/python execution/final-chapters-review-2026-11-01/quantum-review/independent_probes.py
```

It completed successfully with Python 3.12.11, mpmath 1.3.0 and SymPy 1.14.0. `independent-probe-results.json` records the source hashes, script hash, exact outputs and residuals. No packages were installed.

- Fifteen exact radial-moment fixtures compare multinomial monomial integration with independently expanded Duffy or translated-unit-cube integrations, through order four for the simplex, cube and translated box. The simplex begins `1/6, 1/20, 2/105`; the cube begins `8, 8, 152/15`.
- A symbolic determinant checks the Klein density. Nine exact scalar-tail identities, orders zero through eight, check the truncation formula. Vertex-derived face normals give curvature sums `-1/2`, `-24` and `-12` for the three polyhedra, respectively, each equal to minus three times its Euclidean volume.
- Four exact slope fixtures, including both signs of nonzero `q`, check the generating-function derivatives, stationary equation and Hessian normalization. Nine rational charge fixtures check the screening specialization and strict first-moment margins.
- Eighteen figure-eight cases use nine colors `2,3,6,7,12,31,40,60,120` at 70 and 110 decimal digits. The independently evaluated complex half-power expression agrees with the positive log-sum-exp expression, with maximum relative residuals approximately `6.70e-70` and `5.63e-110`. Endpoint-product, maximum-location and sum bounds also pass with scale-aware precision tolerances.
- Independent Lobachevsky quadrature and the dilogarithmic value agree at the working precision. The reported zero difference at 70 digits is a floating-point result, not an exact identity or interval certificate. Selected scalar q-product remainders also agree with their elementary bounds.

These are bounded review probes. They are not execution of the future maintained companion and do not certify external asymptotic theorems, numerical integration errors, global realization or an invariant construction.

## Planned companion contract and exposition

The proposed `computational-targets.md` is mathematically suitable for the implementation role. It distinguishes exact arithmetic from 70/110-digit comparisons; requires independent expressions, explicit branches, scales and residuals; uses positive sums through logarithms; and forbids accepting an unresolved tiny signal through an absolute tolerance. It correctly prefers exact subleading Klein coefficients over subtraction of nearly equal numerical volumes. Series truncation bounds and quadrature errors remain separate. The future runner still requires its own implementation and execution review; none is approved by this document.

The revisions improve the logical transitions between definitions, elementary proofs, cited results, conditional semiclassical arguments and proposed finite checks. They avoid treating precision agreement as an independent oracle, an arbitrary rounding sequence as a refined 6j theorem, pole evaluation as ordinary substitution, fixed-shape asymptotics as a uniform degeneration theorem, or compact convergence as noncompact domination. All retained labels and chapter connections remain coherent.

The separately proposed bibliography patch pins the existing Chen–Murakami link to version 3. It is a reasonable optional metadata change, not a silently applied edit or a condition of this source-text approval.

## QR01 repair and final acceptance

QR01 is preserved in `initial-findings.json`. The author added these actual hashes to `reviewed_dependency_sha256` in the ledger:

| Direct dependency | Reviewer-observed SHA256 |
| --- | --- |
| `book/chapters/03-ideal-tetrahedron.tex` | `81c51ade3378fbfd4baff1cebeb2dcdd8b0fd43a032ac45fb3b30c4908060797` |
| `book/claims/sections7-8.json` | `7438f1b5c8fde23fa81b0b1c3250d2965debf79678026d649bd7ff7cd368439d` |

The affected dependency declarations belong to `s10.bloch_wigner`, `s10.curvature_measure`, `s11.wp_scale` and `s11.compact_model`. The author refreshed its manifest and handoff in `quantum-author/revision-v2/` without erasing the initial evidence. The reviewer ran `verify_final_metadata.py`, which independently read the actual repaired canonical ledger, checked the announced manifest hash, removed the two inserted lines and recovered the initial bytes exactly, compared all 61 claims, confirmed unchanged chapter bytes and rehashed all 11 live dependencies. It completed successfully and wrote `final-acceptance.json` and the final byte snapshot. The unchanged mathematical probes were not rerun. This approval is bound to the three final canonical hashes listed above; the ledger's author-side pending-review field was intentionally not self-edited by either author or reviewer.

The reviewer changed no canonical file, staged or committed nothing, rebuilt no book or PDF, installed nothing and performed no upload.
