# Independent mathematical audit of Section 9

Review date: 31 October 2026. Reviewed baseline: `26b3c134d9308d345cb76f1240db9de982b2e5a6`.
All `M:` line references below refer to that commit's
`book/polyhedral_volumes_and_geodesic_identities.tex`, SHA-256
`63102e64405a58b8f5d51bfdffe6be43fc5cfe9a232dc0f396f1709733d750dc`.
Section 9 is M:1547-2026. Later mechanical extraction does not change the
meaning of these pinned references.

## Disposition

The core coordinate, gradient, Hessian, Schur, and forest identities are
correct under the stated disk and positive-angle hypotheses. I derived
them independently below; this conclusion does not rely on the rectangle
experiment. In particular, the Hessian identity holds throughout the
abstract angle domain, whereas its interpretation as the stiffness matrix
of a single embedded planar mesh requires a geometric realization.

No theorem-level counterexample to those core identities was found. The
chapter should nevertheless make the following points explicit before its
claims are treated as a self-contained reviewed account:

1. **Grounding and strictness (M:1590-1594, 1635-1676).** Prove the kernel
   assertion, rather than relying on nonnegative weights alone. Zero
   Delaunay weights do not create an extra grounded zero mode under the
   positive triangle/disk hypotheses. The proof below supplies this fact.
2. **Holonomy convention and geometric conclusion (M:1600-1653).** Define
   the positive orientation of the radial development. Distinguish vanishing
   dilation from the independent rotational/convex-boundary hypotheses.
   State that the algebra proves criticality/uniqueness, not by itself
   existence of an interior critical point or a global planar embedding.
   An external existence result can be invoked with its exact hypotheses.
3. **Response variables and locality (M:1740-1759).** Call `Px` selected
   linear observables unless an actual geometric boundary interpretation has
   been supplied. They cannot simply be the fixed coordinates `u|_B=0`.
   Write the perturbation formulas for the maximizing branch near the
   nondegenerate maximum; a local Taylor expansion alone does not establish
   an unrestricted global maximum for an arbitrary function.
4. **Gaussian parameter (M:1771-1782).** State `hbar>0` for the exact real
   Gaussian formula. The existing positive-definiteness hypothesis is
   sufficient for the block inverse and square-root determinant.
5. **Three-manifold theorem scope (M:2005-2012).** The cited complete-metric
   conclusion needs the orientable, torus-boundary, full-angle-space
   hypotheses of Futer--Gueritaud Theorem 1.2. Vanishing derivatives only
   along a redundant collection of edge variables is not the stated
   theorem; peripheral directions must also be included, as the preceding
   paragraph already notes.

Items 1-4 are proof/convention completions and restrictions to the intended
meaning, not changes to the displayed algebra. Item 5 prevents an
unqualified extension of an external theorem. The independent audit of
barrier complexity and historical companion claims can add further findings;
I have not read any other newly produced review report for this increment.

## Assumptions and the affine coordinate space

Let `T` be a finite, connected, coherently oriented simplicial triangulation
of a topological closed disk, with nonempty boundary vertex set `B` and
interior vertices `I`. Every face has three distinct vertices. Let a base
assignment `alpha^0` have three angles in `(0,pi)` summing to `pi` per face,
and the prescribed opposite-angle sum at each edge. Define

`Omega = {u in R^I : alpha_c^0 + u_i-u_j > 0 for every corner c opposite i->j}`,

where all boundary values of `u` are zero. Positivity and the triangle sum
give the upper bound `alpha_c<pi` automatically. `Omega` is nonempty, open,
convex, and bounded; boundedness follows from injectivity of the linear
coordinate map and boundedness of all angle coordinates.

Here and below, angle constraints and boundary values are exact mathematical
conditions. A numerical residual is evidence for their approximate
satisfaction, not a topology or embedding certificate.

### Completeness of the coordinates, M:1616-1626

Triangle increments telescope, and the two opposite-corner increments across
an interior edge cancel. Boundary-edge increments are zero. Conversely,
describe an admissible infinitesimal assignment by one signed variable on
each interior edge, after using the shared-edge and boundary-edge equations.
The triangle equations are the incidence equations of the connected dual
graph of faces. Their rank is `F-1`, so the tangent dimension is

`E_int-F+1 = I`,

using Euler's formula and `E_boundary=B` for a disk. Equivalently, the
triangle-edge bipartite incidence matrix has rank `F+E-1` and nullity `I`.
If every corner increment from `u` vanishes, then the values of `u` agree
across every edge. Connectedness makes `u` constant, and the boundary value
sets that constant to zero. Thus the proposed map is injective between
spaces of the same dimension and parametrizes the entire affine space.

The disk hypothesis is essential to that last conclusion. A triangulated
annulus with no interior vertices has a one-dimensional angle-increment
space, while the proposed grounded vertex map has no columns. It has an
additional period. This is a counterexample to extending the coordinate
claim unchanged to arbitrary surfaces with boundary, not a counterexample
to the stated disk claim. The independent exact incidence calculation in
`math-audit-checks.py` records both a disk and an annulus.

### Cone and boundary angles, M:1600-1613

Around an interior vertex incident to `k` triangles, summing those triangle
equations and subtracting all opposite angles gives

`sum_t alpha_(t,i) = k*pi - sum_(e incident to i) Delta_e`.

At a boundary vertex with `k` incident triangles there are `k+1` incident
edges, giving the extra `-pi` in the stated boundary formula. Both formulas
are correct and are fixed by the prescribed edge data. A flat interior
requires the first quantity to be `2*pi`; a strictly convex boundary
requires each boundary angle to lie in `(0,pi)`. Neither condition should
be silently dropped when the algebra is given a planar/polyhedral meaning.

## Gradient, Hessian, and positivity

### Gradient convention, `eq:ipolyHessian`, M:1635-1653

For a positively oriented face `(i,j,k)`, the angle increments are

`d alpha_i=du_j-du_k`, `d alpha_j=du_k-du_i`, `d alpha_k=du_i-du_j`.

Therefore differentiation with respect to `u_i` gives

`-Lambda'(alpha_j)+Lambda'(alpha_k) = log(sin(alpha_j)/sin(alpha_k))`.

Develop the star counterclockwise, carrying the radial edge `ij` to `ik`.
The sine law gives the ratio of the next radial length to the previous one
as `sin(alpha_j)/sin(alpha_k)`. The product over the star is the positive
dilation `H_i`, so the displayed gradient is `log H_i`, with this convention.
Traversing the star in the opposite direction replaces `H_i` by its inverse;
the chapter should not leave the convention implicit.

This computation makes sense for abstract positive triangle shapes. It does
not require closure. If the total angle is not `2*pi`, setting `H_i=1`
still leaves rotational holonomy. With the flat-interior assumptions, a
critical point kills the dilation around the generators of the punctured
disk. Global embedding additionally needs the boundary/development argument
or an appropriate realization theorem.

### Factor two, `eq:ipolyFEM` and `prop:ipolyHessian`, M:1563-1659

The scalar derivatives give

`-D^2 V[u][h,h] = sum_c cot(alpha_c) (h_i-h_j)^2`.

An interior edge contributes both opposite cotangents; a boundary edge has
zero difference because its endpoints lie in `B`. Defining the usual edge
weight as one half of that cotangent sum gives exactly

`-D_u^2 V = 2 L_II(alpha)`.

The factor two and signs are correct. The finite-element normalization is
independently obtained from the barycentric gradients of a Euclidean
triangle: the off-diagonal local stiffness entry is `-cot(alpha_k)/2`.
The edge formula for `v^T L v` then counts each undirected edge once.

The algebraic matrix identity holds for every `u in Omega`. At a geometric
realization, the same weights are the actual planar finite-element weights.
Off the geometric locus they still define the algebraic cotangent matrix;
one must not claim that an arbitrary off-origin angle vector is a globally
embedded planar mesh. The maintained example already respects this limit.

### Strict concavity and the missing kernel argument

For any positive triangle with `alpha_1+alpha_2+alpha_3=pi`, put
`c_i=cot(alpha_i)`. On tangent vectors `a_1+a_2+a_3=0`, the cotangent form is

`Q(a)=(c_1+c_3)a_1^2+2 c_3 a_1 a_2+(c_2+c_3)a_2^2`.

Its first diagonal coefficient is
`sin(alpha_2)/(sin(alpha_1) sin(alpha_3))>0`, and its determinant is
`c_1 c_2+c_2 c_3+c_3 c_1=1`. Hence it is positive definite on this
two-dimensional tangent space. This is a pointwise trigonometric proof;
it is not an inference from the example.

Apply that form to the three edge differences induced by a vertex function.
Its zero space on one triangle consists exactly of constant vertex values.
Summing over connected triangles gives the constant vector as the only zero
mode of the full cotangent matrix. Grounding `B` removes it, so `L_II` is
positive definite whenever `I` is nonempty. In the zero-dimensional case,
use the empty matrix and determinant one conventions.

This proof works for all positive triangle angle triples and does not
require nonnegative individual edge weights. Delaunayness is the extra
condition that makes the relevant coefficients a positive-conductance
network. If some prescribed sums equal `pi`, their weights vanish, but
positive feasibility prevents a positive-weight interior component from
becoming disconnected from every boundary vertex: its indicator would
otherwise be an extra zero-energy grounded vector. Thus the inverse used
in Newton's equation and in the Schur formulas is justified, including the
non-strict Delaunay case.

Consequences: `V` is strictly concave on `Omega`; an interior critical point
is unique and is its global maximum on `Omega` (and by continuity on its
closure). These statements alone do not prove that the maximum is interior.

### Weights and Newton sign, M:1581-1589 and 1661-1676

The cotangent addition identity gives

`w_e=sin(Delta_e)/(2 sin(alpha_e) sin(beta_e))`.

For `0<Delta_e<pi`, the denominator is at most
`2 sin^2(Delta_e/2)`, proving the stated sharp lower bound
`w_e>=cot(Delta_e/2)>0`, with equality at equal opposite angles.
For `Delta_e=pi`, the weight is zero. The additional description at
M:1669 that this diagonal subdivides a flat face applies at a geometric
polyhedral realization; an abstract zero weight alone does not establish
an embedded flat face. Newton's maximizing equation is
`(-D^2 V) delta u=grad V`, so `2 L_II delta u=log H` has the correct sign.
Global convergence or feasibility of a full Newton step does not follow.

## Boundary response, Gaussian elimination, and forests

### `eq:ipolyDtN`, M:1727-1738

With a symmetric cotangent matrix whose only null vector is constant,
minimizing energy at fixed boundary voltage gives
`L_II v_I+L_IB v_B=0`. Substitution yields exactly the displayed Schur
matrix `N`. It is positive semidefinite, its kernel is the boundary
constant vector, and grounding one boundary node makes it positive definite.
This follows by the energy-minimization identity; it does not need every
boundary-to-boundary conductance to be nonnegative.

The passive resistor-network interpretation of the full boundary problem
does require nonnegative conductances. A single obtuse triangle with angles
`(2*pi/3,pi/6,pi/6)` has, after scaling by `2*sqrt(3)`, stiffness matrix

`[[6,-3,-3],[-3,2,1],[-3,1,2]]`.

It is positive semidefinite with constant kernel, but its positive
off-diagonal entry corresponds to a negative edge conductance. Thus the
chapter's existing boundary-weight qualification is necessary and should
remain adjacent to the electrical interpretation.

### `eq:ipolyBoundaryResponse`, M:1740-1759

Assume a sufficiently smooth function has a nondegenerate local maximum at
zero with Hessian `-K`, `K>0`. The implicit-function theorem solves
`grad V(x)+P^T j=0` locally as
`x(j)=K^{-1}P^T j+O(|j|^2)`. Substitution gives
`V_0+(1/2)j^T P K^{-1}P^T j+O(|j|^3)`.

If `P` has full row rank, `chi=P K^{-1}P^T` is positive definite. A Lagrange
multiplier for `Px=b` gives
`x=K^{-1}P^T chi^{-1}b+O(|b|^2)` and the displayed negative quadratic
correction. These are correct local maximizing-branch formulas. They can be
global in a suitable concave problem, but locality should be explicit when
only the displayed Taylor expansion is assumed. Use `P=0` or a rank-deficient
`P` only in the first formula; the inverse in the second needs full row rank.

The electrical `v_B` and the fixed leading--trailing boundary values are
different variables. The algebra works for any selected linear observables
`Px`; an additional model-specific identification is needed to call them
geometric boundary data. The paragraph's warning about the Dehn-filling
dictionary is correct and should remain.

### `eq:ipolySchur` and `eq:ipolyGaussian`, M:1761-1783

Completing the square gives

`x^T K x=(y+K_yy^{-1}K_yz z)^T K_yy (y+K_yy^{-1}K_yz z)+z^T K_eff z`.

It proves the Schur formula and determinant factorization directly.
With `K>0` and `hbar>0`, integrating the first quadratic form over real
`y` gives precisely the stated positive Gaussian factor. This is an exact
finite-dimensional identity; any contour, complex determinant phase,
higher-order remainder, or quantum-invariant identification needs separate
data. The manuscript already warns about those distinctions.

### `eq:ipolyForestDeterminant`, M:1785-1799

Choose an oriented incidence matrix `D` with one column per undirected
edge, and remove boundary rows to obtain `D_I`. The factorization
`L_II=D_I diag(w) D_I^T` is valid with arbitrary real weights. Cauchy--Binet
gives a sum over `|I|`-edge subsets, with coefficient
`det(D_I[:,S])^2`. An invertible minor has no cycle and no component
containing two roots. Counting edges then forces every component to have
exactly one boundary root; leaf elimination gives determinant `+/-1`.
Conversely every such forest has such a minor. The factor `2^|I|` follows
from `-D^2 V=2L_II`. Zero weights simply contribute zero terms.

This is an exact general algebraic identity, not only a fixture identity.
In the positive Delaunay problem its nonzero terms are nonnegative; the
positive grounded determinant ensures at least one positive rooted forest.
No claim that forest enumeration is computationally efficient follows.

## Additional checks within the chapter

I read the complete Section 9. The following observations record what was
checked in addition to the primary matrix scope and what still needs the
separate source/complexity review.

- `prop:ipolyCompatibility` / `eq:ipolyCompatibility` (M:1817-1860): the
  local representation `h_i=lambda sin(alpha_i) cos(psi_i-tau)` spans the
  two-dimensional tangent plane because the weighted side vectors close
  and two are independent. Its energy and third-derivative identities have
  the stated factors. The bound on the cosine of the sum follows from
  expanding `cos(a+b+c)`; trianglewise summation is legitimate since each
  local cotangent energy is nonnegative. Thus the stated compatibility
  constant and the resulting standard self-concordance inequality are
  algebraically consistent. This does not by itself instantiate a complete
  inexact path-following algorithm.
- The barrier derivative bound follows from
  `cot^2(alpha)/csc^2(alpha)=cos^2(alpha)<=1`, Cauchy--Schwarz, and affine
  restriction. Concavity of sine gives
  `-cot(alpha)(beta-alpha)<=1-sin(beta)/sin(alpha)<=1`; hence the central
  point gap `m/t` follows with the stated stationarity equation. The
  relative `1+O(1/sqrt(m))` change of `t` has a bounded decrement because
  the new Hessian dominates `F''`. The big-O step/work claims additionally
  depend on an explicit centering and inexact-Newton policy; retain the
  existing exclusions of feasibility, bit precision, and geometric error.
- Non-self-concordance of `-V` can be seen inside a genuine one-interior-
  vertex disk. Take a three-triangle fan with center angles `2*pi/3`,
  outer angles `a=pi/6`, and variable outer angles `a+u,a-u`. As
  `s=a-u` tends to zero, `(-V)''~3/s` and `|(-V)'''|~3/s^2`, so their
  self-concordance ratio grows as `1/sqrt(3s)`. This is an asymptotic
  derivation, not a finite-sample inference.
- `eq:ipolyThreeDimensionalHessian` (M:1983-2003) is the direct substitution
  of `d alpha=dp_gamma-dp_beta` and cyclic analogues into the scalar
  cotangent form. It is not a coordinate completeness result. Even at a
  regular tetrahedron, splitting each `p` into the sum of an opposite pair
  of `y` variables gives positive off-diagonal entries between the two
  variables of the same pair. The exact scaled matrix in the independent
  check is positive semidefinite but not diagonally dominant. The
  manuscript's warning against transferring the planar SDD conclusion is
  therefore substantive and correct.
- The Rippa, flip-graph, WP-distance, mapping-torus, and global topology
  references are external inputs, not consequences of the matrix proof.
  This report does not independently verify those complete theorems or
  their proofs; that task remains with the separate companion/source audit.

## Primary-source verification and limits

The arXiv MCP connector was tried first and returned an unavailable-server
error (SSE endpoint HTTP404). Primary web PDFs were used as fallback. No
unpublished manuscript text was uploaded to an external model or service.

- [Annals metadata for Rivin1994](https://annals.math.princeton.edu/1994/139-3/p02)
  confirms title, author, volume139(3), pages553-580, DOI10.2307/2118572.
  The DOI endpoint exposed no theorem text. Its full proof was **not read**
  or independently reverified here.
- [Rivin, Combinatorial optimization in geometry, v1](https://arxiv.org/pdf/math/9907032v1),
  a separate later primary paper: Definition1.1 and Lemma1.2 state the edge,
  cone, and boundary conventions; Theorems1.4/1.6 give uniqueness and
  existence for positive feasible prescribed Delaunay data, with a singular
  Euclidean metric unique up to scaling. Theorem4.11 treats flat convex
  disks through explicit vertex and cut conditions. These statements were
  read; their complete proofs and all cited antecedents were not audited.
  A new citation to this paper must not be represented as a full-text check
  of the 1994 paper.
- [Futer--Gueritaud, From angled triangulations to hyperbolic structures, v2](https://arxiv.org/pdf/1004.0440v2):
  Theorem1.2 concerns orientable 3-manifolds with torus boundary and
  criticality on the full positive angle space. Proposition2.5 separates
  edge gluing from completeness; peripheral equations supply the latter.
  Sections4-5 provide the leading--trailing argument. Theorem6.2 has
  different hypotheses for polyhedral boundary. This supports the
  scope correction above and does not give a blanket theorem for arbitrary
  triangulated 3-complexes or constrained edge-only stationary points.

The independent derivations in this report are mathematical arguments;
source retrieval verifies what the cited papers state, not their entire
proofs. The exact small checks below are executable illustrations of the
scope distinctions. None is a global realization classifier, interval
certificate, full monograph audit, or performance theorem.

## Claim-to-evidence map for chapter editing

| Stable label / passage | Status supported by this review | Editorial action |
| --- | --- | --- |
| `eq:ipolyFEM` | Exact trianglewise derivation at geometric realization | Keep; define edge counting and signed boundary weights. |
| `eq:ipolyDelaunayweight` | Exact trigonometric identity/equivalence | Keep positivity qualification. |
| `eq:ipolyAngleCoordinates` | Complete affine parametrization for a disk | Expand dual-incidence rank/injectivity proof; do not generalize topology silently. |
| `prop:ipolyHessian`, `eq:ipolyHessian` | Exact abstract-angle identity and oriented holonomy derivative | Define CCW development; distinguish global geometric realization. |
| `eq:ipolyWeightLower` | Exact lower bound, sharp at equal opposite angles | Keep zero-weight endpoint separate. |
| `eq:ipolyNewton` | Exact local Newton equation | Add strictness/kernel proof; no automatic convergence claim. |
| `eq:ipolyDtN` | Exact Schur minimization with one constant mode | Distinguish passive network signs from PSD energy. |
| `eq:ipolyBoundaryResponse` | Local smooth maximizing-branch expansion | State full row rank for inverse and local/observable meaning. |
| `eq:ipolySchur` | Exact block identity | Keep SPD block assumption. |
| `eq:ipolyGaussian` | Exact real integral for SPD block and positive hbar | Add `hbar>0`; preserve complex-contour caveat. |
| `eq:ipolyForestDeterminant` | Exact general incidence-minor identity | Keep proof and nonnegative-term conditions; finite enumeration is illustrative. |
| `eq:ipolyBarrier`, `prop:ipolyCompatibility`, `eq:ipolyCompatibility` | Trianglewise derivative proof checked | Separate algebra from implementation and inexact-solver theorem. |
| `eq:ipolyStepBound` | Centered path-following consequence subject to stated algorithmic controls | Preserve independent complexity review and separate costs. |
| `eq:ipolyThreeDimensionalHessian` | Exact local substitution; not a complete coordinate system | Define local angle map; keep rank/peripheral/SDD limitations. |
| Three-manifold critical-point paragraph | External theorem with specific topological and full-tangent hypotheses | State those hypotheses explicitly. |
| Rippa/flip/WP/mapping-torus passages | External inputs, not verified by this matrix audit | Require separate source audit; no inference from current code. |

## Minimal replacement statements

After the coordinate description, a short lemma can state:

> On a connected triangulated disk, with positive angles summing to pi in
> each face and fixed opposite-edge sums, the grounded leading--trailing
> map parametrizes the entire affine angle space. The negative volume
> Hessian is positive definite there. This strictness follows from the
> positive triangle cotangent form and does not require every individual
> edge weight to be positive.

After the holonomy formula:

> Here dilation is measured by counterclockwise development from each
> radial edge to the next. Vanishing logarithmic dilation is the
> stationary equation. Flat interior cone angles and the stated convex
> boundary data are separate geometric hypotheses; an existence or
> embedding conclusion uses the corresponding realization theorem.

Before boundary response:

> Let a smooth function have a nondegenerate maximum at the origin, and
> consider its local maximizing branch under small perturbations. Let
> `Px` be selected linear observables. They represent geometric boundary
> data only when a separate model-specific identification is specified.

In the three-manifold paragraph:

> For an orientable ideal-triangulated 3-manifold whose nonempty boundary
> consists of tori, an interior critical point of volume on the full
> positive angle space yields the complete hyperbolic metric, by the
> Casson--Rivin theorem in the cited formulation. Edge-only stationarity
> and the local Hessian formula do not replace the peripheral conditions.

These proposals preserve all existing theorem/equation labels and the
mathematical content of the core identities. They do not authorize changing
the archived companion or pretending that the current numerical solver
implements a certified barrier algorithm.

## Executed exact illustrations and provenance

`math-audit-checks.py` is a standalone standard-library script using integer
and rational arithmetic. It imports no maintained toolkit code. The recorded
run used `/tmp/polyhedra-baseline-20261031/bin/python`, completed successfully,
and produced `math-audit-checks.json`. It checks:

- A three-triangle disk has angle-tangent dimension and coordinate rank one;
  a six-triangle annulus with no interior vertices has tangent dimension one
  but coordinate rank zero.
- The obtuse boundary example has exact scaled eigenvalues `0,1,9`, including
  a positive off-diagonal matrix entry.
- The regular ideal tetrahedron's edge-variable Hessian is a rank-two Gram
  matrix, has positive off-diagonal entries, and is not diagonally dominant.
- Rooted-forest enumeration equals the grounded determinant, with sums `196`
  and `144` before and after an interior conductance is set to zero.

These finite checks illustrate the general derivations and scope
counterexamples above; their status is exact finite arithmetic, not a proof
by sampling or a new production test suite. The JSON records the script hash
and the reviewed baseline. A separate audit manifest records artifact hashes
and source-access limits. The only working-tree changes observed during this
audit were the builder's mechanical chapter extraction; this reviewer changed
only files under the outer execution directory.
