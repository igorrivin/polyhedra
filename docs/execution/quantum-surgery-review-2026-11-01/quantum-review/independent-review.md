# Independent mathematical review of Sections 12–14

Date: 2026-11-01. Baseline: `bf260eaab047d9047602ece652e5a7e43625d3f6`.
Reviewer: independent `quantum_review` agent; no canonical authorship and no
imports from the computational companion. Exact approved source identities
are in `approved-hashes.json`.

**Verdict: approve the bounded mathematical increment.** I read the three
complete chapters and all 30 claim groups. I found no remaining false or
unproved unconditional claim requiring correction within this scope. All
88 labels are retained in their original chapter order: 85 labels assigned
to claim groups and three top-level chapter labels. The approved ledger
includes the separately authorized `check.py` to `run.py` pointer correction;
reversing that one replacement reproduces the initially frozen ledger hash.
No chapter bytes changed during review.

This approves the stated finite derivations and the use of the identified
primary-source statements with their hypotheses. It does not re-referee
all external proofs, establish an infinite spectral continuation, or approve
the inherited global analytic claims of Section 15. A separate reviewer is
responsible for the companion implementation and its eventual replay.

## Findings by mathematical responsibility

| Claims | Independent conclusion |
| --- | --- |
| `s12.first_moment`, `curvature`, `charge_continuation`, `screening_periods` | KRV (2.11) has coefficient `2/gamma=1/b`; the reference metric cancels because `gamma sum beta=4`. Strict moment bounds hold for the stated open weight domain and fixed `0<b<1`. KRV Theorem 6.1 applies to this real charge domain. The Gamma residue is negative, and changing from `s+1` to `epsilon=b(s+1)` multiplies its coefficient by `b`. Removing the pairwise powers by logarithmic curvature is valid off collisions. |
| `s12.four_point_area`, `relative_torsion`, `torsion_flat_limit` | Sending the fourth insertion to infinity has the claimed cancellation. The elliptic quotient contributes half the torus area. The revised torsion paragraph correctly rescales the Goldman, peripheral, and torsion forms together; `sqrt(2) dtr` is restricted to `B=-tr`. Mondello gives the local comparison, with global marked injectivity only in the stated smaller opening range. The CH limit remains conditional on the explicitly cited Section 8 controlled-family result, read here as an inherited dependency. |
| `s12.fricke_blowup`, `wkb_measure`, `quantum_dictionary` | The Fricke expansion, Heron chart, implicit first correction, and factor `1/2` agree. The correction is local and its cusp nonintegrability is acknowledged. The WKB measure is correctly branchwise and conditional. The order-`b` charge shift, negative area of shifted flat openings, and `s=A/(4pi b^2)-1` distinguish the fixed-`b` residue from the joint scale. |
| `s13.parameters`, `spectral_continuation`, `two_pinches` | The initial bootstrap domain is correctly translated from doubled source charges, and its overall correlation factor is distinguished. The pinch-index equation has only the two claimed solutions when `0<b^2<1`. DOZZ reflection and the shift identity give the displayed sum-coordinate residues and signs. The full-contour route is explicitly conditional on local normal convergence and retention of crossed residues. The independent moment/period route establishes the finite residue formula without that interchange. |
| `s13.screened_blocks`, `fusion` | Weight-one twisted-cycle screening gives the Ward intertwiner. Normalization and leading exponents identify the two nondegenerate internal blocks; their positive weights at `c>25` avoid Verma degeneracy. Gauss connection, determinant, and both beta-rescaled sine formulas agree with their specified branches. Exact independent level-one and level-two Virasoro Gram calculations also agree, as bounded checks of this identification. |
| `s13.area_pairing`, `density`, `total_volume` | The added second-coefficient argument closes the previous proof omission: one collision beta integral fixes one coefficient; distinct monodromy at the other puncture forces the off-diagonal entry to vanish and determines the other. All four connection entries are nonzero on the stated nonresonant real domain. Local domination justifies the `delta1=0` extension while keeping the `s` basis nonsingular. The Hermitian determinant identity has the stated sign and gives the positive density. Collision exponents, cusp treatment, Gauss–Bonnet, and the minimum formula are consistent. |
| `s13.balanced_logarithmic` | The logarithmic expansion uses the elliptic parameter convention correctly. The finite involution, off-diagonal pairing, period monodromies, cusp coefficient, and derivative-block interpretation agree. The second solution is explicitly distinguished from an ordinary block of the same Virasoro weight. |
| `s14.tv_normalization`, `finite_double_gamma`, `residue_square_roots`, `plancherel` | TV's trivalent ratios, reflected infinity label, and both Plancherel square roots are preserved. The double-Gamma shift gives the stated common scalar and Gamma factors. Rescaling the period connection gives the finite sine operator, and analytic versus absolute roots give complex orthogonality versus the real indefinite pairing. The revised prose sufficiently limits any identification with the residue of the infinite operator. The continued sine product and its balanced zeros do not define a pointwise bare-symbol limit. |
| `s14.screened_gram`, `screened_saddle` | The planar representation proves rank two for every admissible weight. Each finite matrix is a planar Gram matrix with one entry perturbed, giving both zero principal cofactors, the determinant, and the negative off-diagonal cofactor. The source geometric criterion requires that cofactor condition in addition to signature. Cancellation in the classical potential leaves the stated reduced equation; the canceled double branch root is not a regular fold. |
| `s14.compact_regular_geometry`, `classical_fold`, `volume_exponent`, `integration_coordinate` | Hyperbolic trigonometry, Schläfli integration, polynomial factorization, and local fold derivatives agree, including `54i`, `18sqrt(2)i`, the Airy scale, and `hbar_vol=pi b^2`. The source's volume factor is read with its geometric root and branch choices. The original exact TV integrand fixes `u=exp(2pi i b w)`; the corrected lift has all three argument types in the fundamental strip for sufficiently small `b`. |
| `s14.uniform_quantum_dependency` | Correctly excluded from this approval. The local classical fold and strip separation supply neither the global contour nor uniform tail estimates for the exact quantum integral. The revised references to Section 15 do not silently upgrade this local calculation into such a result. |

The simultaneous torsion rescaling, second Hermitian coefficient proof,
conditional TV interpretation, and local/global Airy distinction therefore
suffice for the four author revisions under review. No numerical factor
change is requested.

## Independent evidence and limits

`independent_probes.py` ran under Python 3.12.11, SymPy 1.14.0 and mpmath
1.3.0, at 80 decimal digits for the numerical part. It passed 36 exact
symbolic checks and 40 numerical comparisons. The largest numerical
residual was approximately `2.48e-51`, from the balanced symmetric
parameter derivative, tested at `1e-47`; the other checks use `1e-65`.
Three small-`b` sine-quotient observations are separately recorded as
convergence observations. They are not interval enclosures or tail bounds.
The exact Gram fixtures cover all four `(j,k)` cases at one radical
weight choice; the general Gram argument is checked directly below.

For the latter, the four planar reference angle columns may be taken as
`(0,theta2+theta3,theta2,theta1+theta2+theta3)`, with respectively the
shifts `(0,0,0,0)`, `(0,h,h,h)`, `(0,0,0,h)`, `(0,h,0,h)` for
`(j,k)=(0,0),(0,1),(1,0),(1,1)`. The changed entries are exactly the
four entries in the chapter table. A rank-two matrix has vanishing
cofactors, and its determinant under a single symmetric off-diagonal
increment is `-det(G_complement)*epsilon^2`; differentiation gives
`C_ab=-det(G_complement)*epsilon`. The complementary minors are the
listed `q`. A positive two-by-two principal minor together with a
negative determinant gives signature `(3,1)`, while the negative
cofactor excludes the asserted ordinary convex realization.

Primary statements and formula pins were fetched independently during
this review; see `source-pins.json`. PDF screenshots failed with cache
misses, so the mathematical source checking used the extracted PDF text
and the DLMF/Wiley HTML formulas. Sections 7–8 and Appendix A were read
only where the present arguments explicitly depend on them. Section 15's
analytic proof and historical exact-integral table are not newly approved
or disproved. No build, installation, commit, upload, or browser action
was performed.
