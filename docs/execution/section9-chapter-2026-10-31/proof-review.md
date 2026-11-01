# Independent proof review of the revised Section 9

Reviewer: `/root/section9_proof_review`. Date: 2026-10-31.
Baseline commit: `26b3c134d9308d345cb76f1240db9de982b2e5a6`.

Final disposition: **approved within the stated review scope**. The final
document and ledger-metadata addendum below completes the initially pending
checks; the earlier review stages and frozen hashes are retained.

## Disposition and exact review scope

The revised chapter and its 26-claim ledger pass this independent
mathematical review under their stated hypotheses. No theorem-level blocker
was found. Final reconciliation-document review is still pending; this
initial disposition does not approve unseen companion/status text.

The first complete stable revision actually reviewed is frozen in
`proof-review-revision-1-chapter.tex` and
`proof-review-revision-1-ledger.json`. Its hashes are:

| Source | SHA-256 |
| --- | --- |
| `book/chapters/09-volume-hessians.tex` | `abe89dd665b10fe808a0c4273f5f8ecdbe9fc9a5c0cd7b92bc3618a1759c2a5e` |
| `book/claims/section9.json` | `dc587dd1e862b52b81e555ccd221d30c0de55fe523b2f137bbc0cb7b0e9289af` |

The author first announced hashes `c49bfdd2...` and `6de972b3...`, then
incorporated this reviewer's requested definition of the input size before
the complete frozen review. Those earlier announced hashes are not passed
off as the bytes reviewed. `proof-review-revision-1-manifest.json` records
the actual hashes, all 20 retained baseline labels, six added subsection
labels, and the 26 claim statuses. The ledger correctly still says that its
independent re-review was pending at the time those bytes were frozen.

I independently derived the delicate estimates below, then read the actual
revised chapter and every ledger entry. I did not edit either file, rerun
the full numerical suite, certify floating-point errors, verify an embedding,
audit the whole monograph, or re-prove the complete cited external papers.
The other two audit reports were inputs to challenge, not substitutes for
checking the arguments.

## Independent checks of the finite and inexact barrier arguments

All vectors below are in the intrinsic affine angle tangent space, after
dependencies have been removed. This proviso is essential: an inverse
Hessian on redundant ambient parameters would not define the stated norm.
Let `Phi_t=F-tV`, `H=Phi_t''(x)`, and
`lambda=||Phi_t'(x)||_(H^-1)`. A nonempty positive affine angle domain has
bounded closure in angle coordinates. The logarithmic-sine barrier diverges
at its relative boundary, volume is continuous on the closure, and `F''`
is positive definite on any nonzero intrinsic tangent. Thus the claimed
unique interior center `x_t` exists. The zero-dimensional case is harmless.

1. **Exact-center gap.** For a closed feasible angle `beta_c`, concavity of
   sine gives `cot(x_c)(beta_c-x_c)>=-1`. Hence
   `DF(x)[beta-x]<=m`. At the center `DF=t DV`, and concavity of volume
   gives `V*-V(x_t)<=m/t`. Boundary maximizers are allowed; no lower bound
   on their smallest angle was used.

2. **Distance to the center in the correct basepoint norm.** Put
   `d=x_t-x` and `r=||d||_H`. The one-direction self-concordance differential
   inequality gives `Phi_t''(x+s d)[d,d]>=r^2/(1+s r)^2` throughout the
   segment. Its integral is `r^2/(1+r)`. Stationarity at the other endpoint
   and dual Cauchy--Schwarz therefore imply
   `r^2/(1+r)<=-Phi_t'(x)[d]<=lambda*r`. Thus
   `r<=lambda/(1-lambda)` when `lambda<1`. In particular, the norm is based
   at the finite iterate `x`, not at the unknown center.

3. **Finite-center gap.** Since `H>=F''`, the barrier gradient bound gives
   `||DF(x)||_(H^-1)<=sqrt(m)` and therefore
   `t||DV(x)||_(H^-1)<=sqrt(m)+lambda`. Apply concavity at `x` to
   `V(x_t)-V(x)`, then add the exact-center gap. This proves
   `[m+(sqrt(m)+lambda)lambda/(1-lambda)]/t`. For `lambda<=1/4`, write
   `u=sqrt(m)>=1`. The difference between `17u^2/12` and
   `u^2+u/3+1/12` is `(u-1)(5u+1)/12>=0`. This proves the stated
   `17m/(12t)` bound for every allowed `m`, rather than only testing a
   finite list of sizes.

4. **Parameter change and exact recentering.** For
   `delta=1/(20 sqrt(m))`, the new gradient is
   `(1+delta)Phi_t'-delta F'`, while `H_(t')>=H_t`. At the same point its
   decrement is at most `1/4+1/20+1/(80 sqrt(m))<=5/16`.
   The full-step estimate is `(lambda/(1-lambda))^2`, giving exactly
   `25/121<1/4`. Geometric growth of `t` gives the displayed
   `O(sqrt(m) log max{e,m/(t0 epsilon)})` number of changes. The starting
   condition and `t0>0` are explicitly assumed; no feasibility or initial
   centering cost is hidden in the count.

5. **Inexact recentering.** Set `d_N=-H^-1 g`,
   `eta=||d-d_N||_H<=lambda/100`, and `r=||d||_H`. At the new parameter,
   `eta<=1/320` and `r<=101/320`. The old dual norm of `g+Hd` is `eta`.
   Hessian comparison along the segment bounds the gradient remainder by
   `r^2/(1-r)` in that same old dual norm. Converting to the endpoint dual
   norm costs at most `1/(1-r)`. Consequently
   `lambda_new<=eta/(1-r)+r^2/(1-r)^2<=10420/47961<1/4`.
   Both occurrences of the denominator are needed. The exact arithmetic
   check gives positive margin `6281/191844` below `1/4`.

6. **Direct feasibility.** For a tangent step with `||d||_H<1`, domination
   `H>=F''` gives `|d alpha_c|<sin(alpha_c)` for every corner. Since
   `sin(alpha_c)<=min(alpha_c,pi-alpha_c)`, every new angle is still
   strictly between zero and pi. This directly verifies feasibility of
   the exact and inexact steps without assuming an unstated line search.

The source chapter now contains these qualifications. The inexact result
controls linear-solve error only; gradients, Hessians and norms are treated
as exact. It is not a floating-point implementation guarantee. The new
definition `n=|I|+|B|` resolves the only clarification requested in this
review: using only the number of interior unknowns would not account for
arbitrarily many boundary/input vertices. Disk planarity gives `m=O(n)`
and `O(n)` matrix entries. The arithmetic scale remains conditional on
solver success/tolerances at every step, with accuracy factors suppressed;
the chapter explicitly excludes bit complexity, starting-point costs and
geometric error certification.

`proof-review-checks.py` was executed with the isolated baseline Python.
It uses only `fractions.Fraction` and the standard library, and its JSON
records the exact rational constants and its script hash. It is a finite
arithmetic cross-check, not the proof of the general estimates above.

## Triangle identities, zero weights, and topology

For a positive triangle, the tangent cotangent form in coordinates
`a3=-a1-a2` has matrix
`[[c1+c3,c3],[c3,c2+c3]]`. Its leading diagonal is
`sin(alpha2)/(sin(alpha1)sin(alpha3))>0` and its determinant is one.
Therefore it is strictly positive on the two-dimensional triangle tangent
space, including obtuse triangles. For nodal differences, its kernel is
exactly the constant functions on that triangle. Summing over a connected
triangulation gives only the global constant kernel, and grounding the
nonempty boundary removes it. This proves strictness independently of
whether the assembled conductances are individually positive.

In particular, an interior component disconnected from the boundary by
zero Delaunay conductances would give a nonzero grounded indicator of zero
energy, contradicting the triangle argument. Zero Delaunay diagonals do
not invalidate the inverse Hessians. Boundary-to-boundary signed weights
do not enter the grounded problem. They do matter for the separate passive
network interpretation, which the revised text explicitly qualifies.

The complete angle parametrization uses the connected dual incidence rank
`N_T-1` and disk Euler identity `E_int-N_T+1=|I|`; the grounded vertex map
is injective by edgewise equality and connectedness. Thus it has the entire
required tangent dimension. The chapter correctly excludes the unnoticed
period directions of annuli and more general surfaces. Positivity bounds
all angles by pi and injectivity transfers boundedness to the chosen
coordinates.

I also checked the nontrivial trigonometric representation in the barrier
proof. For `psi=(0,alpha1+alpha2,pi+alpha2)` the weighted side vectors close
and two are linearly independent. Writing
`h_i=lambda sin(alpha_i) cos(psi_i-tau)` spans every tangent. With
`S=sin(alpha1)sin(alpha2)sin(alpha3)`, the elementary identities
`sum sin(alpha_i)cos(alpha_i)=2S` and
`sum sin(alpha_i)cos(alpha_i)exp(2i psi_i)=0` give the quadratic form
`lambda^2 S`. The cubic identity can be checked using
`z_i=exp(i phi_i)` and
`sin(alpha_i)=(z_k^2-z_j^2)/(2i z_j z_k)` cyclically: the resulting
Vandermonde identity is
`sum sin(alpha_i)z_i^3=4S z1 z2 z3`.
Together with `cos^3=(3cos+cos3)/4` and side closure, this gives the
chapter's cubic formula exactly. The cosine-sum bound and summation with
nonnegative triangle energies then prove compatibility. This is an
algebraic derivation, not evidence from random probes.

## Closed maximizers and the no-needle argument

The proposed companion correction is valid under the stated condition:
`K` is a compact convex set of angle vectors satisfying each triangle sum,
and it contains an angle vector positive in every triangle. The claim is
uniqueness in angle coordinates, not in a redundant parameter space.

Use `Lambda(s)=s(1-log(2s))+O(s^3)` and
`Lambda(pi-s)=-Lambda(s)`. Moving from a needle `(0,b,pi-b)` toward a
positive feasible point gives a contribution `-a s log s+O(s)`, `a>0`.
Its right directional derivative is positive infinite. At a flat vertex
`(pi,0,0)`, the contribution instead is
`s[(b+c)log(b+c)-b log b-c log c]+O(s^3)` with `b,c>0`, so the derivative
is finite. Positive triangles also have finite derivatives. Thus no other
triangle can cancel a needle's positive infinite contribution, and no
maximizer contains a needle.

If there were two distinct maximizers, concavity would make their segment
maximizing. A triangle positive at either endpoint is positive along the
open segment; its strictly negative second derivative forces its angles
to be unchanged. If both endpoint triangles are flat but at different
vertices of the closed angle simplex, their midpoint is a forbidden needle.
Thus every triangle agrees at the two endpoints, proving uniqueness.
This argument does not force all maximizing angles to be positive, prove
a particular degeneration classification, or certify a geometric
realization. Those stronger historical assertions must stay corrected in
the reconciliation note.

## Other chapter checks and resolution of the earlier audit findings

| Finding | Revised chapter disposition |
| --- | --- |
| Holonomy orientation and closure | Counterclockwise radial development fixes the sign of `log H`; rotational, convex-boundary and global realization hypotheses are separated. |
| Hessian normalization and Newton sign | Each interior edge is counted once, `-V''=2L_II`, and the maximizing equation is `2L_II delta u=log H`. |
| Zero-weight strictness | Triangle determinant-one proof and grounding supply the missing argument. |
| Flat-face interpretation | Asserted only at a geometric polyhedral realization, not from an abstract zero weight. |
| Response variables/locality | `Px` are selected observables; both maximizing branches are local and the inverse response requires full row rank. |
| Gaussian domain | `K>0`, real eliminated variables and `hbar>0` are explicit; no contour or quantum-invariant consequence is claimed. |
| Rooted forest determinant | Incidence minors justify the general identity; the fifteen-forest rectangle is explicitly a finite illustration. |
| Finite centering | Exact-center `m/t` is separated from finite `17m/(12t)`; basepoint norms and stopping condition are explicit. |
| Inexact/complexity scope | The solve tolerance is explicit; derivative arithmetic, success probabilities, initialization and geometric-error costs remain separate. |
| Rippa and surface comparisons | Common geometric/nodal data are fixed; closed-surface Brock hypotheses are explicit and distinct from punctured layered fibers. |
| Three-manifold criticality | Orientability, compact torus boundary, positivity and full tangent/peripheral criticality are included. |
| Computational evidence | Exact finite rational identities, binary64/50-digit numerical comparisons and unimplemented methods are distinguished. |

The Schur and determinant identities follow by completing the square and
block elimination under positive definiteness. The Dirichlet-to-Neumann
kernel follows from minimizing energy and the unique constant kernel of
the full cotangent matrix. The general rooted-forest formula permits real
signed weights algebraically; a minor with a cycle, no root, or two roots
in a component vanishes, and the surviving rooted-forest minors have
absolute determinant one. The three-dimensional edge-variable formula is
a local substitution, not a complete coordinate basis or an SDD theorem.

The layered `N v3` argument uses the usual straightening/fundamental-class
volume identity and the ideal-tetrahedron volume maximum. The elementary
summation is valid for signed straightened tetrahedra. It does not prove
that an arbitrary flip sequence produces the required triangulation.
The ledger includes this hypothesis rather than claiming a general
mapping-class algorithm.

## All 26 claim statuses

Each status below is appropriate for the frozen revision. The individual
entries' hypotheses and coverage gaps are part of the assessment, not
optional prose.

| Claim ID | Status | Review conclusion |
| --- | --- | --- |
| `s9.fem` | proved in chapter | Triangle stiffness normalization; geometric mesh hypothesis retained. |
| `s9.delaunay_weights` | proved in chapter | Exact trigonometric sign and lower bound; boundary signs qualified. |
| `s9.coordinates` | proved in chapter | Complete only for the stated disk constraints. |
| `s9.gradient_hessian` | proved in chapter | Oriented derivative and factor two; embedding not inferred. |
| `s9.strictness` | proved in chapter | General triangle/grounding proof, not sampled eigenvalues. |
| `s9.newton_equation` | proved in chapter | Local Newton equation; no iteration driver or convergence claim. |
| `s9.geometric_realization` | external statement checked | Source hypotheses and access limits retained; no constructive certificate. |
| `s9.dtn` | proved in chapter | Energy minimization and constant kernel. |
| `s9.observable_response` | proved in chapter | Local implicit-function expansion with the needed rank. |
| `s9.schur` | proved in chapter | Exact SPD block algebra. |
| `s9.gaussian` | proved in chapter | Exact real integral; no numerical quadrature or contour validation. |
| `s9.rooted_forests` | proved in chapter | General incidence identity; finite enumeration supplementary. |
| `s9.barrier_compatibility` | proved in chapter | General triangle identities; audit probes only diagnostic. |
| `s9.finite_centering` | proved in chapter | Correct finite-iterate value certificate with explicit decrement. |
| `s9.short_step_iterations` | conditional algorithmic consequence | Centered start, parameter rule and arithmetic/solve assumptions explicit. |
| `s9.inexact_arithmetic_work` | conditional algorithmic consequence | Size, solve, success and arithmetic conditions explicit; unimplemented. |
| `s9.rippa_energy` | external statement checked | Primary-abstract access limit honest; no full-proof audit claimed. |
| `s9.flip_graph` | external statement checked | Marked triangulable finite-type surfaces with boundary marking. |
| `s9.brock_comparisons` | external statement checked | Closed genus at least two; correct additive/multiplicative scopes. |
| `s9.layered_volume_bound` | proved in chapter | Short deduction using stated straightening/fundamental-class hypotheses. |
| `s9.three_dimensional_hessian` | proved in chapter | Local formula; finite non-SDD example is not a coordinate-completeness proof. |
| `s9.casson_rivin` | external statement checked | Full positive angle space and torus-boundary theorem scope retained. |
| `s9.fixture_exact` | exact finite check | Named grid, rational matrix/forest/Schur/voltage identities only. |
| `s9.fixture_numerical` | numerical check | Recorded finite numerical comparisons; neither exact nor interval. |
| `s9.wp_continuum_limit` | open | No continuum-limit theorem or experiment claimed. |
| `s9.quantitative_angle_bound` | open | Volume gap does not certify angles, embedding or combinatorial type. |

The status totals are 15 proved-in-chapter, five checked external
statements, two conditional algorithmic consequences, one exact finite
check, one numerical check and two open questions. Paths to the newly
produced review artifacts require the planned controlled copy into the
canonical repository before publication; this source review does not
replace that packaging check or a fresh numerical replay.

## Primary-source checks performed by this reviewer

I retrieved the public primary sources below directly, without uploading
unpublished manuscript text. These are checks of transferred statements
and hypotheses, not complete proof audits.

- [Rivin, 1999 preprint](https://arxiv.org/pdf/math/9907032v1), Theorems
  1.6 and 4.11: prescribed-angle feasibility gives the singular-metric
  statement; the convex flat-disk formulation has separate vertex and cut
  conditions. This is a distinct source from the 1994 Annals paper.
- [Futer--Gueritaud](https://arxiv.org/pdf/1004.0440v2), Theorem 1.2 and
  the opening of Section 6: full positive angle-space criticality,
  orientable three-manifold and nonempty torus boundary are the relevant
  scope. The revised sentence does not claim an edge-only criterion.
- [Spielman--Teng](https://arxiv.org/pdf/cs/0607105v5), Theorem 5.5 and
  Section 6: relative energy error and probabilistic arithmetic bounds are
  distinct from finite-precision controls. The canonical conditional
  statement preserves that distinction.
- [Disarlo--Parlier](https://arxiv.org/pdf/1411.4285v1), Section 2.1 and
  Lemma 2.3: the surface and marking conventions support the stated proper
  cocompact action and orbit comparison.
- [Brock on convex cores](https://arxiv.org/pdf/math/0109048v2), opening
  assumptions and Theorems 1.1--1.2, and
  [Brock on mapping tori](https://arxiv.org/pdf/math/0109050v1), Theorem
  1.1: the chapter correctly keeps these in the closed-surface setting
  and distinguishes additive errors from the multiplicative mapping-torus
  comparison.
- [Rivin--Schlenker](https://arxiv.org/pdf/math/0001176v2), equation (1)
  and the exterior-angle discussion on printed page 2: changing from
  interior to exterior angle reverses the Schlaefli differential sign.
  Applying it to ideal vertices additionally uses the standard signed
  horospherical lengths and fixed ideal-vertex angle equations.
- [Boyd--Vandenberghe slides](https://web.stanford.edu/~boyd/cvxbook/bv_cvxslides.pdf),
  self-concordance discussion and PDF pages 378--382: the general
  complexity analysis assumes self-concordant objectives and accounts
  separately for initial centering. The chapter-specific constants above
  were independently derived, not attributed verbatim to those slides.

This reviewer could not independently retrieve the
[Rippa publisher destination](https://doi.org/10.1016/0167-8396(90)90011-F):
the DOI redirect was inaccessible. The ledger accurately attributes its
primary-abstract check to the companion audit and expressly disclaims a
full-proof reading. That access limit has not been upgraded here.

## Pending reconciliation-document review

The author is still completing the companion reconciliation, current
status documentation and revision-response matrix. Their actual final
bytes and disposition will be recorded in an appended review rather than
silently folded into the frozen chapter/ledger review above.

## Final document review and ledger-metadata addendum

I subsequently read the complete companion reconciliation, current book
README, computational-status ledger, numerical errata and author response
matrix. All requested corrections are present with the stated scope. No
mathematical or status objection remains for these reviewed documents.

In particular, the reconciliation gives the valid closed-maximizer
existence/uniqueness argument under compactness, convexity and positive
feasibility, while preserving the possibility of `(pi,0,0)` triangles.
Its explicit concave-boundary example has the advertised positive angles,
shared opposite sum `pi/2` and boundary angle `7pi/6`. Its exterior-angle
Schlaefli sign is correct; the multiplier observation concerns the
stationarity equations and does not re-prove the later geometric
classification. Free-angle and prescribed-angle programs remain distinct.
The timing denominators are correctly separated, with no fresh historical
benchmark claimed. The original companion's hash remains
`339a2440e65864339ae7ffb9fb3bdd69f8070232216a6045b65cb3550587de69`.

The current docs correctly date the earlier numerical replay and test-suite
results to their original source states. Their values were read as preserved
historical evidence, not rerun or independently re-certified in this proof
review. They keep the supplied PDF, remaining monograph, unavailable Airy
and torus evidence, optional-dependency gates and public deployment outside
the Section 9 claim. The author's response matrix accurately maps each
audit finding to its revised passage. Its final check/manifest update
reflects the metadata-only ledger change described next.

The final ledger SHA-256 is
`f801da33c5224e04595211c23e7f54b1edc2087bff5ebd6d0bf739ade7f33ab8`.
It is independently approved as a **metadata-only** update of the frozen
ledger `dc587dd1...`. A direct JSON comparison confirms all 26 claim
entries and every original field except `revision_review` are unchanged.
The two new global fields point to this report and preserve the reviewed
chapter and pre-status-update ledger hashes. The final bytes are frozen in
`proof-review-final-ledger.json`, with the comparison recorded in
`proof-review-final-ledger-manifest.json`. That manifest also records the
first ad hoc checker stopping on an assumed field-name layout; its corrected
comparison uses the observed nested metadata layout. This was a checker
schema assumption, not a mathematical or ledger-content failure.

Final reviewed identities:

| File | SHA-256 |
| --- | --- |
| `book/chapters/09-volume-hessians.tex` | `abe89dd665b10fe808a0c4273f5f8ecdbe9fc9a5c0cd7b92bc3618a1759c2a5e` |
| `book/claims/section9.json` | `f801da33c5224e04595211c23e7f54b1edc2087bff5ebd6d0bf739ade7f33ab8` |
| `book/companion-reconciliation.md` | `e5d67047f552430aba9cfd59a2f99dbd69c8664b77c0384be2df35bd520d51a1` |
| `book/README.md` | `bb920296f4800e8cfd1ab3184ded3c049bd94887d493d6cad68f3eb36c4abc1a` |
| `book/computational-status.md` | `34d483e260fdba2fb7c5b7a4c6e4b86553933d460b523f3fc5ef4d9740b2c2ae` |
| `book/numerical-errata.md` | `63628db354fafc78e495f0e295bdaa5034cde4472680e171321b9d10fd55e072` |
| Author `chapter-revision.md` | `3d0399808652ce59c29325db387cc65284efc454a03c25b8f8c655db5f696b7f` |

The main TeX hash is
`3b3b93d26764392353030a30ef4569360d051e0d78d6e5eb7fd6bef1f96de546`;
this pins the chapter include and inspected bibliography additions, and is
not an approval of the remaining monograph's mathematics.

**Final verdict:** approve the revised Section 9 mathematics, its 26-claim
ledger, the reconciliation and accompanying status corrections under the
hypotheses and access limits recorded above. Every actionable finding of
the two initial audits is resolved in the assigned scope, including the
input-size clarification raised by this reviewer. The genuinely open
research questions and unimplemented computational methods remain open.
This is an independent mathematical review, not formal certification,
interval validation, a full-literature/full-monograph audit, a fresh
numerical-suite result, rendered-output approval, or publication approval.
The parent still owns controlled evidence copying and the separate build,
render, artifact, dependency and deployment checks.
