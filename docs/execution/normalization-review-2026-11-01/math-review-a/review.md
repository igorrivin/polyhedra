# Independent mathematical review: Sections 1–6 and Appendix A

Reviewer: `normalization_review_a`; date: 2026-11-01. Baseline:
`ad63b7ac9821040cb69e19c61bfbc46c68eff1a3`.

**Outcome: approved for this bounded normalization/hypothesis increment.**
No numerical-factor error or blocking mathematical defect was found in the
seven revised chapters. The exact approved bytes are pinned in
`verification.json`. One source improvement is recommended below and has been
sent to the parent for a separate author patch; the existing candid source
limitation is acceptable until that patch is reviewed. This approval does not
re-referee every cited external proof or designate the entire book reviewed.

## Derivations and domains checked

- Section 1 correctly separates a local scale change from an ineffective
  stabilizer. Kawazumi's equation (38), under its coefficientwise harmonic
  Beltrami identification, gives the raw pairing conversion used here. Its
  opposite FN wedge ordering and closed-surface scope are explicitly stated.
  Mondello's Theorem 1.4 uses the manuscript's FN ordering. The cone-surface
  extension is properly assigned to the separate Section 8 review.
- Section 2's unsigned-incidence rank proof is valid because a connected
  triangulation contains an odd cycle. Changing from edge coordinates to
  free fiber coordinates and perimeters gives the reciprocal absolute minor,
  not induced Euclidean hypersurface measure. Budd's rooted weighting and
  orientation-preserving equivalence give the stated unrooted weight and
  factor. His definition and Corollary 2 were inspected directly.
- Section 3's diameter/height-one horosphere gauge is consistent with signed
  distances. Mondello's reduced-length restatement of Penner gives the
  logarithmic-lambda coefficient after substituting reduced length equal to
  twice log lambda. The two ambient-coordinate Jacobians, angle-simplex area,
  two labeled orientation sheets, determinant -2, and integrability estimates
  agree. The intrinsic/conformal versus ambient cross-ratio distinction and
  collapsed flat-boundary modulus remain explicit.
- Section 4's Gram argument is valid. Every three-dimensional principal
  block has inertia (2,1), and interlacing plus the full determinant sign
  gives (3,1). The projected vectors have negative norm, negative pairwise
  product, and nonzero determinant, giving three noncollinear points on one
  hyperboloid sheet. Strict triangle inequalities follow. Perron–Frobenius
  applied to the positive off-diagonal matrix I-G gives the stated affine
  chart; its eigenvalue exceeds 1 since every row sum exceeds 3. Each edge
  meets the ball by the displayed midpoint norm. No global realization
  theorem is required for this local argument.
- Mondello's ordered wedge coefficient gives the stated half-kernel bracket.
  The restriction to a positive-boundary symplectic leaf precedes inversion.
  The coordinate-change calculation and Pfaffian density are correct;
  positivity of the denominator follows from the strict triangle inequality.
  The q=2 check gives coefficients 10 and 10/3. The cusp paragraph does not
  claim an unrenormalized finite-coordinate limit.
- Bao–Bonahon's required same-face path condition is accurately restored.
  Budd's polynomial identity is confined to genera 0 and 1. BMZ's independent
  coordinates and factor 2^(m-3) follow after replacing their n by m-1.
  Zonneveld's selected unequal pair and full-measure scope match Theorem 3;
  the text does not promote equal-length continuity to a new bijection.
- Section 5's Gauss–Bonnet sign, log-kappa convention, cone substitution,
  ordinary-DM pullback, stability restrictions, wall coefficient and
  projection-formula argument agree. AMN's definitions and pullback lemma
  were read directly. The genus-zero complementary-side observation is
  correct. The scalar four-point example is correct, and the text expressly
  retains divisor intersections in higher dimension. The pure-cone pairwise
  chamber and the sufficiently-large-boundary qualification in the mixed
  degeneration agree with Anagnostou–Norbury v4.
- Section 6's common orbifold and cover degrees match Hu–Tan Section 3.
  Multiplying the common integral pairing by degrees 2 and 4, then accounting
  for 4!/4 labeled sphere choices and the separate ineffective torus
  involution, gives the factors 12 and 24. The cone version also passes the
  orbifold-area and branched-cover count: quotient area pi-phi, torus twice
  that area, sphere four times. The zero-area endpoint is excluded.
- Appendix A's two Cayley–Hamilton trace identities give the displayed
  twist numerator, including its sign. The length derivative gives the
  density factor 2. The geometric component, smoothness, and Phi_z chart
  conditions now distinguish a failed coordinate pair from a singular
  character surface. No global fundamental domain is claimed.

## Source improvement for the author

The existing `Fillastre` bibliography item is the compact-metric survey and
was correctly removed from the funnel claim. The exact relevant reference
is instead:

> Key `FillastreMetrics`: F. Fillastre, *Polyhedral hyperbolic metrics on
> surfaces*, Geometriae Dedicata **134** (2008), 177–196.
> DOI: 10.1007/s10711-008-9252-2; arXiv:0801.0538v1.

The [version-1 paper](https://arxiv.org/pdf/0801.0538v1) explicitly states the
genus-zero realization as Theorem 1.1 on printed page 2, with congruence
qualification nearby. Section 1.3 on page 3 attributes the proof to
Schlenker. This supplies a precise external restatement of the needed
hypotheses, rather than merely Budd's informal attribution. The ledger can
record that statement check as completed while saying that Schlenker's
original proof was not inspected. It must not claim that this reviewer
proved the global realization theorem or independently inspected its
original paper.

Version pinning matters: the [version-2 document](https://arxiv.org/pdf/0801.0538v2)
is a two-page erratum concerning connectedness in the parabolic/Fuchsian
proof. The unversioned arXiv PDF currently resolves to that erratum, not to
the theorem statement. Preserve the existing survey citation for its other
uses and add a distinct bibliography key.

Suggested chapter change: retain attribution to Schlenker, and add
`\cite[Theorem 1.1 and Section 1.3]{FillastreMetrics}` as the precise
restatement. Update only the corresponding source and funnel claim records.

## Independent evidence and limits

Ran `/tmp/polyhedra-baseline-20261031/bin/python -B
../execution/normalization-review-2026-11-01/math-review-a/verify_review.py`
from the canonical repository; exit 0. The script independently preserves
all **607** source labels in their baseline order, validates the **28**
unique ledger claims and their label targets, and pins all eight reviewed
files. All fifteen tetrahedral perimeter minors were checked by rational
elimination. A **729**-assignment rational Gram grid contains 714 admissible
negative-determinant cases and 15 excluded positive-determinant cases;
**2,916** Schur-complement checks and exact LDL inertia checks passed.
These are finite algebra probes supporting, not replacing, the general
argument reviewed above. No floating tolerance or interval claim is made.

The independent code reviewer owns the companion implementation review and
replay. This review did not rebuild a PDF, run the toolkit's full suite,
change sources, inspect browser output, or perform publication actions.
Primary sources used for statement checks are pinned in `source-pins.json`.
The original Rivin angle-proof and Penner proof were not re-refereed; their
relevant formulations were checked through Bao–Bonahon, Budd and Mondello.
The historical and global-source limits in the ledger remain visible.
