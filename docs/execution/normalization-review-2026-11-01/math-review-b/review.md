# Independent review of Sections 7–8

Reviewer: `normalization_review_b`, 2026-11-01. Reviewed the two complete
chapter files and all thirteen ledger claims. This is a statement,
normalization and derivation review, not a new refereeing of every cited proof.

**Verdict: mathematical content passes; two bounded source-attribution
corrections are requested before final hash approval.** No numerical-factor
error or invalid chamber example was found. No canonical file was edited.

1. In the Section 8 compactification paragraph, Koziarz–Nguyen's curvature
   conversion is in **Section 7.4**, printed pp. 32–33. Section 7.3 gives the
   divisor class. Correct the prose, citation, ledger evidence and source pins
   accordingly.
2. Specify that balanced-weight formulas are obtained by continuity, citing
   **Remark 1.3**. That remark excludes balanced subsets from the paper's direct
   metric/current analysis while retaining its volume formula by continuity.
   Avoid implying a directly inspected balanced closed-current theorem. The
   manuscript's later continuity argument for the divisor identity is sound.

The reviewed source identities and label checks are in `review-manifest.json`.
After these changes, only a targeted wording/hash recheck is needed unless
additional mathematical content changes.

The WP factor was checked without using the total-volume limit as evidence.
Kawazumi's equation (38) calibrates the raw real tangent form to minus twice
the imaginary Hermitian pairing. Wang's period calculation identifies the
negative logarithmic-area Hessian with the positive area-average norm after
conversion of his area units and signs. Thus the manuscript's `iG` convention
gives half the curvature-minus-one CH form. Independently, the affine
pillowcase deformation has Beltrami coefficient `i/(2 Im(tau))`; unit-area
raw norm is `1/(4 Im(tau)^2)`. Its real FN area coefficient is twice that
norm, half the hyperbolic area coefficient. This local check does not appeal
to a compactification or lattice volume.

The conic analytic deduction is appropriately local: weights stay in `(0,1)`,
marks remain separated, area is normalized, and the flat limit is positive.
The Mazzeo–Weiss deformation framework supplies a local family with bounded
conic coefficients. Simple poles then admit the stated integrable dominator.
One obtains locally uniform convergence by controlling small cone discs
uniformly and using uniform convergence on their complement, followed by
matrix inversion. The text claims no uniformity at collisions or zero
weights and does not infer total-volume convergence from this argument.

For the universal-curve calculation I checked the vertical-component signs,
fiber degree of the perturbation, projection formula and continuity argument.
The stated pullback identity is supported by the source's Remark 8.1; its
intersection rules are in Section 8.4. Stable light subsets are counted once.
The independent AMN check confirms the squared collision correction and the
geometric top-intersection interpretation in the positive-area chamber.

Section 7 correctly distinguishes labels, permitted equal-weight
permutations, and ineffective group actions. The cited half-integral theorem
uses one specified equal-weight block. Period area, signature, disk curvature,
collision exponent and pillowcase degree agree with the sources. The cyclic
cover is connected because the denominator is minimal; at a branch with
`g=gcd(q,m)` the differential has order `(q-m)/g-1 >= 0`, while infinity is
regular since the numerator sum is `2q`. No lattice claim is inferred for
arbitrary real weights.

The final-chamber bounds are strict when a light subset exists; balanced
subsets are excluded for positive epsilon. The empty-light endpoint is handled
separately. The balanced-family coefficient jump does not contradict
continuity of the full piecewise volume, because the chamber width shrinks.
McMullen's partition convention is labeled and curvature minus one; its
finite-volume extension includes balanced cases.

`independent_checks.py` imports no companion implementation. With Python
3.12.11 it passed 85 four-point rational weight vectors, four named cases,
the symmetric five-point boundary/partition computation, 435 local cyclic
cover orders, and three local pillowcase coefficient checks. These are finite
arithmetic checks, not proofs of the general analytic or divisor statements.
All 27 pre-existing chapter labels are preserved in order. Build and visual
verification, software review and clean-source artifact generation are
separate tasks; none is claimed here.
