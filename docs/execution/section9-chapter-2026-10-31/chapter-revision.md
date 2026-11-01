# Section 9 revision response matrix

Date: 31 October 2026. Author: delegated `section9_math_audit` agent.
Baseline: `26b3c134d9308d345cb76f1240db9de982b2e5a6`; mechanically extracted
chapter SHA-256 `b9606d093e39ca6baaae11599c64fa0a3be0e84bfe7a788d225b5587b3be9132`.
The independent initial findings are preserved in [math-audit.md](math-audit.md)
and [companion-audit.md](companion-audit.md). This is author response evidence,
not the independent verdict on the revised bytes.

## Changes made

| Audit issue | Actual revised passage or stable label | Response and remaining boundary |
| --- | --- | --- |
| Core: implicit triangulation/domain hypotheses | `subsec:ipolyCoordinates`, `eq:ipolyAngleCoordinates` | Defined a finite connected oriented simplicial disk, nonempty grounded boundary, and the nonempty positive open bounded convex domain. |
| Core: coordinate completeness needs a proof | `eq:ipolyAngleCoordinates` and following unnumbered derivation | Used dual-face incidence rank `N_T-1`, Euler dimension `|I|`, and grounded injectivity. Added the annulus period limitation. |
| Core: holonomy orientation fixes the gradient sign | `prop:ipolyHessian`, `eq:ipolyHessian` proof | Defined counterclockwise radial development, gave the sine-law next/previous ratio, and stated that reversing orientation inverts holonomy. |
| Core: strictness and zero weights | `prop:ipolyHessian` proof | Proved triangle-form determinant one and positive first coefficient, hence full constant kernel and grounded SPD even with zero Delaunay weights. Included the empty-matrix convention. |
| Core: abstract identity versus geometric FEM | `eq:ipolyHessian`, `eq:ipolyWeightLower` and surrounding text | Retained the identity throughout the angle domain; limited actual planar FEM and the zero-weight flat-face interpretation to geometric realization. |
| Core/companion: stationarity versus realization/existence | `subsec:ipolyCoordinates`, paragraph after `prop:ipolyHessian` | Separated dilation, rotational holonomy, convex boundary and global realization; uniqueness of an interior critical point does not assert its existence. Added a separately identified Rivin 1999 source. |
| Core: DtN kernel and signed boundary weights | `eq:ipolyDtN` | Derived energy minimization, PSD and the exact constant kernel; retained nonnegative full weights for the passive-network interpretation. |
| Core: response observables and locality | `eq:ipolyBoundaryResponse` | Replaced automatic boundary interpretation by selected linear observables, wrote the local maximizing branches, and retained full row rank for the inverse. |
| Core: real Gaussian convergence parameter | `eq:ipolyGaussian` | Added `hbar>0`; retained SPD and complex-contour qualifications. |
| Core: rooted-forest scope and zero terms | `eq:ipolyForestDeterminant` | Retained the incidence-minor proof, stated signed-weight algebra and nonnegative Delaunay terms, and explained zero edges and positive total. |
| Companion: intrinsic norms, parameter versus objective | `subsec:ipolyBarrierComplexity`, `prop:ipolyCompatibility` | Specified nonredundant intrinsic affine coordinates and distinguished the parameter `m` of `F` from standard self-concordance of `F-tV`. |
| Companion: exact-center versus finite-center gap | Unnumbered derivations preceding `eq:ipolyStepBound` | Proved center existence, the closed-domain exact gap `m/t`, distance bound `lambda/(1-lambda)`, and finite gap at most `17m/(12t)` for decrement at most `1/4`. Boundary volume maxima are allowed. |
| Companion: finite short-step schedule | `eq:ipolyStepBound` and preceding paragraphs | Gave parameter factor `1+1/(20 sqrt(m))`, pre-step bound `5/16`, post-step bound `25/121`, terminal parameter `17m/(12 epsilon)`, and the initially centered-point assumption. |
| Companion: inexact solves and arithmetic complexity | Paragraphs following `eq:ipolyStepBound` | Gave a one-percent relative energy-norm solve tolerance and proof of decrement bound `10420/47961`. Stated exact derivative assumptions, randomized expected arithmetic scope and separate precision/success/centering costs. No maintained barrier implementation claimed. |
| Independent revision review: undefined `n` | Arithmetic-work paragraph after `eq:ipolyStepBound`; ledger `s9.inexact_arithmetic_work` | Defined `n=|I|+|B|` as full mesh vertex count; planarity gives `m=O(n)` and `O(n)` matrix entries. |
| Independent revision review: direct step feasibility | Inexact-step proof after `eq:ipolyStepBound` | Added `|d alpha_c|<sin(alpha_c)<=min(alpha_c,pi-alpha_c)` from the Hessian norm, proving strict positivity of the new angles. |
| Companion: Rippa fixed-data scope | `subsec:ipolyFlips`, `fig:mono-flip`; ledger `s9.rippa_energy` | Preserved fixed sites/nodal values and no volume-monotonicity transfer. Ledger records abstract-only source access, not a full-proof review. |
| Companion: marked flip-graph conventions | `subsec:ipolyFlips`; ledger `s9.flip_graph` | Specified orientation-preserving mapping classes and individually fixed marks, with the boundary-mark hypotheses retained. |
| Companion: Brock closed-surface hypotheses | `subsec:ipolyFlips`; ledger `s9.brock_comparisons` | Stated closed oriented genus at least two, quasi-Fuchsian conformal ends, appropriate coarse constants, and pseudo-Anosov mapping-torus scope. |
| Companion: layered tetrahedron bound | `subsec:ipolyFlips`; ledger `s9.layered_volume_bound` | Retained actual layered triangulation and tetrahedron-count assumptions, signed straightening argument, and the warning against a punctured-surface WP transfer. |
| Both: complete-metric theorem too abbreviated | `subsec:ipolyThreeManifolds`; ledger `s9.casson_rivin` | Specified orientable compact manifold, nonempty torus boundary, ideal triangulation, positive angle equations and full-space criticality including peripheral directions. |
| Both: 3D local Hessian is not a full Laplacian solver | `eq:ipolyThreeDimensionalHessian`; ledger `s9.three_dimensional_hessian` | Retained dependency/peripheral and non-SDD warnings; exact rank-two local example is audit evidence, not a complete coordinate routine. |
| Companion: free-dihedral versus fixed-data programs | `book/companion-reconciliation.md`, first section | Distinguished tangent spaces, gauges and geometric normalization. Historical separator claims remain unsupported transfers. |
| Companion: historical positive-maximizer contradiction | Reconciliation, “Closed maxima need not be positive” | Replaced it by a proved existence/uniqueness statement for the closed angle vector under compactness and positive feasibility; positivity and geometry remain additional conclusions. Historical bytes unchanged. |
| Companion: no-needle lemma overextended to clusters | Same reconciliation section | Included the needle-versus-flat directional-derivative distinction and explicitly left universal degeneration classification unproved. |
| Companion: exterior-angle Schläfli sign | Reconciliation, “Exterior-angle Schläfli sign” | Recorded negative interior-angle and positive exterior-angle conventions; explained the multiplier sign change and retained the already-correct canonical `eq:Schlafli`. |
| Companion: slack barriers and numerical rank | Reconciliation, “Barrier iteration, precision and reported timings” | Required strict relative feasibility and removal of identically tight slacks; separated floating rank selection from exact certification. |
| Companion: reported timing ratio omits feasibility | Same reconciliation section | Recorded both `129/0.16` and `129/(0.16+0.99)` (about 806 and 112) with cost exclusions; no fresh benchmark or general performance claim. |
| Both: primary-source access boundaries | Ledger `source_evidence` fields and reconciliation final section | Distinguished Rivin 1994 metadata from the later 1999 theorem text; Rippa abstract from unread full proof; read Boyd slides from timed-out book; checked external statements from full-proof re-audits. |
| Requested text-code-evidence bridge | New ending `subsec:ipolyComputation`; `book/claims/section9.json` | Added readable exact grid/forest/Schur/harmonic identities, numerical volume/Hessian comparisons, code/result/archive links, and 26 individually classified claims with explicit unsupported routines. |
| Current docs still said imported source unchanged | `book/README.md`, `book/computational-status.md`, `book/numerical-errata.md` | Recorded the current mathematical revision; dated original-byte/software/suite/artifact assertions to their earlier checkpoint. Reference PDF, historical sources, prior execution reports and scientific corpus remain unchanged. |

## Validation and ownership

`chapter-revision-checks.json` records the focused source/ledger checks:
all 601 original labels remain, with six new subsection labels and no
duplicates; the ordered sequence of numbered equation, align and proposition
environments is unchanged; all 26 claims resolve to canonical chapter labels;
all cited keys resolve; referenced existing code and evidence paths exist.
The six audit files below were verified in the outer execution directory and
are awaiting the parent's canonical evidence copy. The historical companion
hash is unchanged. `git diff --check` passed.

No production code, driver, figure, generated artifact or historical source
was edited by this author. No staging or commit was performed. The builder
owns PDF/HTML, equation-number checks against the full auxiliary file,
rendered-page review, numerical artifact regeneration and bundle verification.
The independent proof reviewer owns the verdict on these revised bytes.

## Evidence paths required at handoff

The following files are linked by the claim ledger and must be copied from
this outer directory to `docs/execution/section9-chapter-2026-10-31/`:

- `math-audit.md`
- `math-audit-checks.py`
- `math-audit-checks.json`
- `companion-audit.md`
- `companion_reference_probes.py`
- `companion_reference_probes.json`

Also preserve `math-audit-manifest.json`, this response matrix,
`chapter-revision-checks.json` and `chapter-revision-manifest.json` as execution
provenance. The parent's final execution `README.md` is linked by the current
book documents. `site/README.md` is owned by the builder and documents the
actual render sequence. Browser/publication status must come from its own
verification, not from this author response.

No mathematical objection remains unresolved in this author's assigned
scope. Open research questions, unsupported software routines, limited
primary-source access and remaining build/review gates are explicitly
retained in the ledger and notes.
