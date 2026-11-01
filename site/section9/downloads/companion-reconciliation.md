# Section 9 and the historical computational companion

Date: 31 October 2026. The canonical [Section 9](chapters/09-volume-hessians.tex)
has been revised following the independent [core mathematical audit](../docs/execution/section9-chapter-2026-10-31/math-audit.md)
and [companion audit](../docs/execution/section9-chapter-2026-10-31/companion-audit.md).
This note records the corrections without changing the historical
[companion manuscript](../research/ipoly/duffin_rivin_volume_laplacian_solvers.tex)
or its scripts. The manuscript's SHA-256 remains
`339a2440e65864339ae7ffb9fb3bdd69f8070232216a6045b65cb3550587de69`.
Historical line references below refer to those preserved bytes.

The [claim ledger](claims/section9.json) records the current mathematical and
computational status. General derivations, checked external theorem
statements, exact finite calculations and numerical diagnostics remain
separate kinds of evidence.

## Fixed angles, free angles and geometric realization

Section 9 fixes every opposite-edge sum and uses the grounded
leading–trailing coordinates `alpha_c=alpha_c^0+u_i-u_j`, with `u=0` on the
boundary. These coordinates fill the affine angle space of a disk. The
historical `P_3` program instead lets edge sums vary under Delaunay and
boundary inequalities. Its tangent directions and inequality slacks are
different; the planar grounded-Laplacian proof does not automatically give
the reduced Hessian or separator complexity of that program. In particular,
the assertion at historical lines 912–913 needs its own structural analysis.

Positive angle feasibility and locally Delaunay interior edges do not force
a convex developed boundary. The two triangles `(0,1,2)` and `(0,2,3)` with
corner angles `(pi/2,pi/3,pi/6)` and `(2pi/3,pi/6,pi/6)` have positive angles
and shared opposite sum `pi/2`, but boundary angle `7pi/6` at vertex 0.
They develop at `z0=0`, `z1=-i/sqrt(3)`, `z2=1`,
`z3=-1/2+i*sqrt(3)/2`, with a concave boundary. The canonical requirement
`0<kappa_b<pi` excludes this example from its convex interpretation.

The chapter now makes the other distinctions explicit: the Hessian identity
holds throughout the abstract angle domain; a single embedded planar FEM
mesh requires realization. Grounding removes the additive coordinate gauge.
A geometric Euclidean similarity still needs a separate normalization, such
as fixing one directed edge at `0,1` and choosing orientation. Sending an
ideal vertex to infinity is a hyperbolic normalization, not a proof of
closure. Tangent-horosphere, zero-shear and modular-holonomy classifications
require their geometric and combinatorial hypotheses; stationary
multipliers alone do not establish them.

## Closed maxima need not be positive

Historical lines 898–900 assert a positive geometric maximizer without the
needed qualifications, while lines 948–950 report flat maximizing triangles.
The valid replacement separates three conclusions: a closed angle maximum
exists, it is unique under the hypotheses below, and positivity or geometric
realization requires further information.

Let `K` be a compact convex feasible set of nonnegative triangle-angle
vectors, each triangle summing to `pi`, and assume it contains a vector
positive in every corner. The sum `V` of triangle volumes is continuous on
`K`, so a closed maximum exists. The historical no-needle argument
(`prop:nosplit`, lines 918–925) rules out a maximizing triangle of type
`(0,beta,pi-beta)` with `0<beta<pi`: moving toward the positive feasible
vector produces a positive infinite directional derivative. A triangle
`(pi,0,0)` instead has a finite directional derivative because its logarithmic
singularities cancel. Thus a maximizing triangle is positive or a permutation
of `(pi,0,0)`.

This yields uniqueness in angle coordinates. If two distinct maxima existed,
their segment would also maximize by concavity. For any triangle positive at
one endpoint, strict concavity on its positive tangent space forces identical
angles at both endpoints. Two distinct flat assignments in one triangle
would produce a needle on the open segment, contradicting the preceding
argument. Therefore the endpoints agree in every triangle. This proves
uniqueness of the closed angle vector; it does not prove that the vector is
positive or geometrically realizes the proposed combinatorial type.

The no-needle lemma does not classify every possible cluster of flat
triangles. Observed boundary-incidence patterns in experiments do not supply
a universal non-splitting or degeneration theorem. If the limiting smallest
angle is zero, a bound using `log(1/alpha_min*)` is not finite. A volume-gap
certificate alone supplies no angle-error, embedding or combinatorial-type
certificate.

## Exterior-angle Schläfli sign

Historical line 934 writes the negative Schläfli sign for `theta_e`, although
lines 310–311 and 333–335 define `theta_e` as an exterior angle. With signed
horospherical truncated lengths, the compatible conventions are

`dVol = -(1/2) sum_e ell_e dDelta_e` for interior angles, and

`dVol = +(1/2) sum_e ell_e dtheta_e` for `theta_e=pi-Delta_e`.

The sign change is stated in the primary [Rivin–Schlenker paper](https://arxiv.org/pdf/math/0001176v2),
equation (1) and the discussion on printed page 2. Changing horospheres adds
vertex terms to truncated lengths; those terms vanish for variations
preserving the ideal-vertex angle equations. The stationary multiplier
condition survives a global sign change after the multipliers are renamed,
but derivative and numerical conventions still require the correction.
The monograph's existing `eq:Schlafli` correctly uses the negative sign for
interior angles and is unchanged.

## Barrier iteration, precision and reported timings

The trianglewise compatibility proof is valid. It distinguishes the Hessian
of `F=-sum log sin(alpha_c)` from the third derivative of volume: their scalar
coefficients include `csc^2(alpha_c)`, but the tensors have different orders.
The barrier `F` has parameter at most the corner count `m`; `F-tV` is standard
self-concordant. The parameter bound is not asserted for the nonlinear
objective itself.

The revised `eq:ipolyStepBound` now specifies a finite algorithmic statement.
Starting at `t0>0` with Newton decrement at most `1/4`, increase `t` by
`1+1/(20*sqrt(m))` and take one full Newton step. The decrement is at most
`5/16` before that step and `25/121<1/4` afterward. A finite centered point
has volume gap at most `17m/(12t)`, so `t>=17m/(12*epsilon)` is sufficient.
The chapter proves the finite-gap estimate rather than assigning the
exact-center bound `m/t` to an arbitrary approximate iterate.

An explicit inexact alternative permits energy-norm step error at most one
percent of the exact Newton-step norm. The new decrement is then at most
`10420/47961<1/4`, assuming exact derivatives apart from that solve error.
Nearly-linear SDD solves give a conditional randomized expected arithmetic
scale after centering; success probabilities, coefficient precision,
transcendental evaluation and final geometric error need separate controls.
Neither this result nor a fast linear solve proves an unrestricted plain-
Newton iteration bound, a bit-complexity bound, or a geometrization algorithm.
The maintained Section 9 example does not implement this barrier schedule.

For the free-angle program, adding barriers for affine inequality slacks
requires a strictly feasible relative domain. Identically tight constraints
must first be included in the affine hull and removed from the slack list;
`log(0)` does not define a barrier. Removing numerical linear dependencies is
also distinct from an exact rank certificate. Historical floating-point rank
selections and script modes labelled “exact” retain their original numerical
status unless a separate exact argument is supplied.

Historical timing ratios are selected-input measurements, with their original
method and cost boundaries. The advertised comparison `129/0.16` is about
806; including just the separately reported feasibility cost `0.99` changes
it to `129/(0.16+0.99)`, about 112. Other unmeasured costs are still absent.
No fresh historical benchmark was run for this reconciliation, and neither
ratio is a general end-to-end complexity result.

## Three-manifold and surface-comparison hypotheses

The local three-manifold cotangent Hessian is correct, but opposite-edge
variable sums create positive off-diagonal entries. The exact regular-
tetrahedron example is a rank-two Gram matrix and is not diagonally dominant.
A full tangent basis also needs peripheral directions and removal of linear
dependencies. The planar positive-Laplacian solver conclusion does not
transfer automatically.

The complete-metric statement in the chapter now follows the precise
Casson–Rivin formulation: an ideal triangulation of an orientable compact
three-manifold with nonempty torus boundary, a positive angle structure with
triangle sums `pi` and global edge sums `2pi`, and criticality on the full
angle space. Edge equations alone do not impose peripheral completeness.
Boundary maxima need not give positive shapes for the chosen triangulation.

Rippa's comparison fixes planar sites and nodal values. The marked flip-graph
comparison retains its marking and boundary conventions. The Brock
comparisons are explicitly for closed oriented surfaces of genus at least
two, with additive/multiplicative constants where required. A layered
triangulation gives `Vol(M)<=N*v3` by straightening only when it really
represents the specified hyperbolic mapping torus, with `N` its tetrahedron
count. This does not transfer a closed-surface WP theorem to a punctured
fiber or prove hyperbolic-volume monotonicity under arbitrary flips.

## Evidence and access limits

The two audits contain the derivations and primary-source pins. Their
[exact finite checks](../docs/execution/section9-chapter-2026-10-31/math-audit-checks.json)
and [independent diagnostics](../docs/execution/section9-chapter-2026-10-31/companion_reference_probes.json)
check transcription and finite examples separately from the proofs. In
particular, the 10,000 binary64 compatibility probes do not prove the general
inequality or its sharp constant. No interval or automatic theorem-proving
certificate is claimed.

Rippa's primary abstract was available, but its full original proof was not
read. Boyd–Vandenberghe's primary lecture slides were checked; the book PDF
timed out. Rivin's 1994 article was verified through metadata only; the later
1999 preprint supplied separately identified theorem statements. The checked
external statements in the claim ledger do not claim that every cited paper
was re-refereed. These access limits do not weaken the independent algebraic
proofs written in Section 9 and its audits.
