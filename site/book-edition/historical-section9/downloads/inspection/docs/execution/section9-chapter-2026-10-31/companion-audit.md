# Independent Section 9 companion reconciliation audit

Date: 2026-10-31. Reviewer: delegated `section9_companion_audit` agent.

Baseline: `consolidated` commit `26b3c134d9308d345cb76f1240db9de982b2e5a6`. Locations below refer to that commit's monolithic `book/polyhedral_volumes_and_geodesic_identities.tex`, where Section 9 occupies lines 1547–2028. The concurrently authorized extraction to `book/chapters/09-volume-hessians.tex` does not change these baseline locations. No canonical/product/historical source was edited by this reviewer, and no other new review report was consulted before completing these findings.

Read: repository `AGENTS.md`; complete baseline Section 9 and its relevant angle conventions; historical `research/ipoly/duffin_rivin_volume_laplacian_solvers.tex` portions covering the variational problems, compatibility, complexity, boundary maxima, and provenance; historical `v4_sc.py`, `v13_compat.py`, `v14_identity.py`; existing `audit/2026-10-31/ipoly-audit.md`. The maintained computational code and the rest of the monograph were not independently certified by this review.

## Decision

The trianglewise compatibility inequality, standard self-concordance of the barrier objective, and the barrier-parameter bound are valid. The short-step complexity can be retained with an explicit finite-centering convention, supplied below. Section 9 already separates most of the historical companion's unsupported transfers: geometric convexity from positive angles, fixed dihedral data from free dihedral optimization, planar Laplacian solvers from arbitrary three-manifold Hessians, and value approximation from geometrization.

Before calling the chapter reviewed, make three narrow changes: state a finite-centering stopping rule, give the Casson–Rivin theorem its full geometric hypotheses, and put the cited Brock comparisons explicitly in the closed-surface setting. Add a companion errata/reconciliation note, preserving historical bytes, for the exterior-angle Schläfli sign and the historical positive-maximizer claim. Neither error is presently asserted in the canonical Section 9.

| Baseline location / label | Verdict | Required action |
| --- | --- | --- |
| 1804, bare `-V` not uniformly self-concordant | Correct | Optional explicit degeneration below; no weakening needed. |
| 1810 `eq:ipolyBarrier`, 1816 `prop:ipolyCompatibility`, 1820 `eq:ipolyCompatibility` | Correct on positive triangle-angle domain, and on its affine restrictions | Retain. Clarify that derivatives and inverse norms use intrinsic affine coordinates after dependencies are removed. |
| 1862–1880, `eq:ipolyStepBound` | Correct asymptotic, finite-centering convention implicit | Retain exact-center `m/t`; add decrement `<=1/4`, finite-center `17m/(12t)`, and an initial centering assumption. |
| 1882–1898, Laplacian arithmetic scale | Conditional and essentially correctly qualified | Retain controlled inexact-solve requirement; say randomized/expected arithmetic work if invoking the cited Spielman–Teng result. Do not claim bit complexity or an implemented method. |
| 1596–1614, positive domain and convex boundary | Canonical text correctly supplies missing boundary condition | Retain, including the distinction from abstract Hessian identities. |
| 1628–1631, geometric closure via variational principle | Appropriately narrow | State positive criticality/geometric realization separately from compactness, uniqueness of an angle optimum, and coordinate gauges if adding an existence theorem. |
| 1907–1915, Rippa | Correct fixed-data comparison | Retain fixed planar points and nodal values, and separation from volume/topological flips. Full original proof was not re-read; primary abstract supports the stated theorem. |
| 1964–1971, marked flip graph | Correct with the cited conventions | Optionally specify orientation-preserving homeomorphisms and whether marks are individually labelled; do not replace with an unmarked or boundary-free surface statement. |
| 1971–1980, Brock | Mapping-torus clause already correct; first comparison can inherit too broad a scope from preceding sentence | Explicitly start the Brock comparisons with a closed oriented surface of genus at least two. Retain additive/multiplicative coarse constants as appropriate. |
| 1982–1990, layered bound | Correct conditional straightening argument | Retain assumption that the sequence really supplies a triangulation of the stated finite-volume hyperbolic mapping torus, and that `N` is its tetrahedron count. |
| 1992–2017, Casson–Rivin / 3D transfer | Matrix warning and affine barrier transfer correct; theorem hypotheses abbreviated | Specify an orientable compact 3-manifold with torus boundary, ideal triangulation, positive angle space, and criticality on its full tangent space including peripheral directions. |

## Independent mathematical derivations

### Compatibility and barrier parameter

Write `V_T = Lambda(alpha_1)+Lambda(alpha_2)+Lambda(alpha_3)` with positive `alpha_i` summing to `pi`, and `Lambda'(a)=-log(2 sin a)`. For a tangent `h`, `sum h_i=0`,

`A = -D²V_T[h,h] = sum cot(alpha_i) h_i²`,

`B = D²F_T[h,h] = sum h_i²/sin²(alpha_i)`,

`T = D³V_T[h,h,h] = sum h_i³/sin²(alpha_i)`.

The positivity of `A` is on the two-dimensional triangle tangent space, even though individual cotangents can be negative. Set `s_i=sin alpha_i` and `psi=(0,alpha_1+alpha_2,pi+alpha_2)`. The vectors `s_i exp(i psi_i)` close and span the plane. Thus their scalar products with a vector of polar coordinates `(lambda,tau)` parametrize every tangent `h_i=lambda s_i cos(phi_i)`, `phi_i=psi_i-tau`. Direct trigonometry gives

`A=lambda² s_1 s_2 s_3`,

`B=lambda² sum cos² phi_i`,

`T=lambda³ s_1 s_2 s_3 cos(phi_1+phi_2+phi_3)`.

For clarity, the cosine bound used in the manuscript follows by expanding

`cos(a+b+c)=cos(a)cos(b+c)-sin(a)sin(b)cos(c)-sin(a)cos(b)sin(c)`.

It gives `|cos(a+b+c)| <= |cos a|+|cos b|+|cos c|`, then Cauchy–Schwarz gives the factor `sqrt(3)`. Hence `|T| <= sqrt(3) A sqrt(B)`. Summing over triangles is legitimate because each `A_T>=0` and `sqrt(B_T)<=sqrt(sum B_T)`.

For `f(a)=-log sin a`, `f''=csc²a` and `f'''=-2 csc²a cot a`, so `|f'''|<=2(f'')^(3/2)`. Summing and restricting to affine coordinates preserve standard self-concordance. If `A=-t D²V[h,h]>=0` and `B=D²F[h,h]`,

`|D³(F-tV)[h,h,h]| <= 2 B^(3/2)+sqrt(3) A sqrt(B) <= 2(A+B)^(3/2)`.

The last scalar inequality follows, for `r=A/B>=0`, from `2(1+r)^(3/2)-2-sqrt(3)r>=0`: its derivative is at least `3-sqrt(3)>0`. Finally,

`|DF[h]| = |sum cos(alpha_i) h_i/sin(alpha_i)| <= sqrt(m) sqrt(D²F[h,h])`.

This is the parameter bound `nu<=m` for `F`, not a claim that every nonlinear objective `F-tV` has barrier parameter `m`. The latter is a standard self-concordant objective; the path argument below uses the parameter bound only for `F`. This distinction is already respected in the proposition.

The companion's description of `D²F` as “the third derivative” of `V` conflates tensor orders; the canonical text has already repaired it.

### Why the bare volume does not have the claimed uniform property

Take `alpha=(s,2s,pi-3s)` and `h=(1,-1,0)`. Then

`A=cot s+cot(2s) ~ 3/(2s)`,

`D³V[h,h,h]=csc²s-csc²(2s) ~ 3/(4s²)`.

Thus `|D³V|/A^(3/2) ~ (1/sqrt(6)) s^(-1/2)`. This is an explicit counterexample to a uniform standard self-concordance bound for the bare negative volume; it supports, rather than contradicts, canonical line 1804.

### Exact centers, finite centers, and an explicit short-step rule

Work on the intrinsic affine space of feasible angle vectors, with dependencies removed. Let `Phi_t=F-tV`, `H_t=D²Phi_t`, and assume a nonempty positive domain. Its closure is compact in angle coordinates. Volume extends continuously to that closure, while `F` diverges at its relative boundary. Consequently each `Phi_t` has an interior minimizer `x_t`, unique in nonredundant angle coordinates. The zero-dimensional case is vacuous.

For any positive `x` and closed feasible `beta`, concavity of sine yields

`0 <= sin beta_i <= sin x_i + cos x_i (beta_i-x_i)`,

and therefore `DF(x)[beta-x] <= m`. At the exact center, `DF(x_t)=t DV(x_t)` on the tangent space; concavity of `V` then gives `V* - V(x_t) <= m/t`. The optimizer `beta` may have zero angles: this argument does not assume an interior maximizer of `V`.

For a finite iterate, define its Newton decrement

`lambda = ||D Phi_t(x)||_(H_t(x)^(-1))`.

If `lambda<1`, standard self-concordance implies

`r := ||x_t-x||_(H_t(x)) <= lambda/(1-lambda)`.

A short derivation avoids metric ambiguity. Put `d=x_t-x`. Along the segment, the one-direction Hessian lower bound is `D²Phi_t(x+s d)[d,d] >= r²/(1+s r)²`. Integrating the derivative difference between `x` and the stationary point gives `-D Phi_t(x)[d] >= r²/(1+r)`. Cauchy–Schwarz bounds the left side by `lambda r`; hence the stated distance bound.

Also `H_t>=D²F`, so `||DF(x)||_(H_t^(-1))<=sqrt(m)` and

`t ||DV(x)||_(H_t^(-1)) <= sqrt(m)+lambda`.

Concavity at the finite point `x` gives `V(x_t)-V(x)<=DV(x)[d]`. Combining these facts proves the explicit finite-centering certificate

`V* - V(x) <= [m+(sqrt(m)+lambda)lambda/(1-lambda)]/t`.

For `lambda<=1/4` and `m>=1`, this is at most `17m/(12t)`. Thus a finite-center stopping rule is `t>=17m/(12 epsilon)` together with `lambda<=1/4`; the exact-center constant `m/t` should not be assigned without qualification to arbitrary approximate iterates.

A concrete exact-arithmetic schedule preserves this neighborhood. Start with `lambda_t(x)<=1/4` and increase `t` by the factor `1+1/(20 sqrt(m))`. If `delta=(t'-t)/t`, then

`D Phi_(t')(x)=(1+delta)D Phi_t(x)-delta DF(x)` and `H_(t')>=H_t`,

so `lambda_(t')(x)<=(1+delta)/4+delta sqrt(m)<=5/16`. One full Newton step is feasible and has new decrement at most

`(lambda/(1-lambda))² <=25/121<1/4`.

The number of parameter changes is therefore `O(sqrt(m) log max{e,m/(t0 epsilon)})`, assuming the initial point already satisfies the centering condition. This independently supplies the missing concrete interpretation of `eq:ipolyStepBound`. It does not pay for feasibility or initial centering.

The primary authors' [Boyd–Vandenberghe lecture slides](https://web.stanford.edu/~boyd/cvxbook/bv_cvxslides.pdf), PDF pages 378–382, corroborate the short-step analysis and its initial-centering hypothesis. The book PDF itself timed out and was not read in this audit.

### Optional explicit inexact-solve rule

The canonical text may retain a conditional controlled-tolerance clause instead of presenting these details. They show that the clause has a concrete possible meaning.

At a newly increased parameter let the exact Newton step be `d_N=-H^(-1)g`, with `lambda=||d_N||_H<=5/16`. Suppose a computed step `d` satisfies `||d-d_N||_H<=lambda/100`. Put `delta=||d-d_N||_H` and `r=||d||_H`, so `delta<=1/320` and `r<=101/320<1`. Self-concordant Hessian comparison and integration of the Taylor remainder imply

`lambda_new <= delta/(1-r)+r²/(1-r)² <=10420/47961<1/4`.

Indeed the old dual-norm residual of `g+Hd` is at most `delta`; the nonlinear gradient remainder is at most `r²/(1-r)`; converting to the new dual norm costs at most `1/(1-r)`. This bound is deliberately conservative. It treats exact evaluation of the gradient, Hessian, and objective; it is not a floating-point stability theorem.

[Spielman–Teng, arXiv cs/0607105v5](https://arxiv.org/pdf/cs/0607105), Theorem 5.5, supplies a relative energy-norm solve guarantee for positive-definite SDD matrices with randomized nearly-linear arithmetic complexity. Its Section 6 treats precision separately and retains condition-number/accuracy dependence. Therefore fixed relative solve accuracy can preserve the short-step neighborhood, but success probabilities across iterations, coefficient precision, transcendental evaluations, and the starting point still require separate treatment. This source supports a conditional expected arithmetic scale, not an unconditional bit-complexity theorem or a measurement of this repository's implementation.

## Existence, uniqueness, boundary geometry, and normalization

### Fixed-data angles are a different optimization family

Canonical `eq:ipolyAngleCoordinates` keeps every opposite-edge sum fixed and grounds `u|_B=0`; these are leading–trailing variations, not logarithmic metric scale factors. Grounding removes the additive coordinate gauge. A unique angle vector is still distinct from a planar realization, whose Euclidean similarity must be normalized separately (for example, one directed edge at `0,1` and a choice of orientation). Sending a chosen ideal vertex to infinity is a hyperbolic-isometry normalization, not a proof of planar closure or convexity.

Historical `P_3` instead lets the edge sums vary under Delaunay and boundary inequalities. It has more tangent directions and additional slacks. The planar grounded-Laplacian statement does not automatically describe its reduced Hessian. Historical lines 912–913 assert separators/operation bounds for that system without the structural justification needed to promote them into a current theorem. The canonical chapter correctly omits that transfer.

For `F_3=F-sum log s_j`, ordinary logarithmic affine slacks preserve self-concordance and add their number to the parameter bound. This requires an actual strictly feasible relative domain for those slacks. A constraint identically tight on the feasible affine hull must first be removed as a slack and included in that affine hull; writing `log 0` is not a barrier construction.

### Explicit positive-angle counterexample to automatic convex boundary

Take the disk with triangles `(0,1,2)` and `(0,2,3)`, with corner angles respectively

`(pi/2, pi/3, pi/6)` and `(2pi/3, pi/6, pi/6)`.

All angles are positive. The only shared-edge opposite sum is `pi/3+pi/6=pi/2<pi`. There are no interior vertices and hence no missing interior curvature equations. Yet the boundary angle at vertex 0 is `7pi/6>pi`. Coordinates realizing these triangles consistently are

`z0=0`, `z1=-i/sqrt(3)`, `z2=1`, `z3=-1/2+i sqrt(3)/2`.

This is a concave developed boundary; vertex 0 lies inside the convex hull of the other three vertices. Positive fixed-data feasibility and a locally Delaunay interior edge do not give the asserted convex ideal-polyhedral interpretation with that boundary. The canonical `0<kappa_b<pi` condition already excludes it. This example does not disprove the existence of a nonconvex planar realization; it proves precisely the missing convexity implication.

### What the no-needle lemma does and does not prove

Historical `prop:nosplit` (918–925) correctly excludes a triangle of type `(0,beta,pi-beta)`, with `0<beta<pi`, from a closed maximizer whenever a positive feasible angle vector exists. Along the segment toward a positive vector, such a triangle contributes a positive infinite directional derivative. A `(pi,0,0)` triangle has finite directional derivative because its logarithmic singularities cancel. Thus every maximizing triangle is positive or `(pi,0,0)`.

This does not establish the stronger geometric classification of every possible separating cluster after the proposition. In particular, the experimental observation that all encountered flat triangles have a particular boundary-incidence pattern is not a proof that all degenerations have that pattern.

The lemma does allow a useful rigorous repair of the historical uniqueness assertion. Let `K` be a compact convex angle domain with triangle sums `pi`, containing a point positive in every triangle, and with `V` the sum of triangle volumes. Its closed maximizer is unique in angle coordinates:

1. Existence follows from continuity and compactness.
2. The no-needle argument applies to every maximizer.
3. If two maximizers differ, their whole segment also maximizes by concavity.
4. A triangle positive at one endpoint is positive on the open segment. Strict concavity of triangle volume forces that triangle's angles to be identical at both endpoints.
5. Two distinct `(pi,0,0)` assignments in a triangle produce a needle on the open segment, contradicting step 2.
6. Therefore all triangle angles coincide at both endpoints.

This proves uniqueness of the closed angle maximizer under the stated hypotheses; it does not prove that all its angles are positive or that it realizes the prescribed combinatorial type geometrically. Historical lines 898–900 claim both positivity and geometry unconditionally, while lines 948–950 report flat maximizing triangles. Preserve that contradiction as a documented correction, not as an silently edited historical source.

Boundary maxima also make an expression involving `log(1/alpha_min*)` meaningless when `alpha_min*=0`. A volume-gap bound does not certify angle error, embedding, the sign of an asymptotically zero slack, or combinatorial type without additional quantitative estimates. The canonical final paragraph correctly leaves such angle bounds open.

### Schläfli convention erratum

Historical line 934 writes `dVol=-(1/2) sum ell_e dtheta_e` while `theta_e` denotes the exterior angle (explicit at lines 310–311 and 333–335). With the standard signed horospherical truncated edge length, the compatible conventions are

`dVol=-(1/2) sum ell_e dDelta_e` for interior angles,

`dVol=+(1/2) sum ell_e dtheta_e` for `theta_e=pi-Delta_e`.

[Rivin–Schlenker, arXiv math/0001176v2](https://arxiv.org/pdf/math/0001176), equation (1) and the sign-change explanation on printed page 2, explicitly distinguishes these conventions. Changing a horosphere alters incident truncated lengths by vertex terms; their contribution vanishes on angle variations preserving the ideal-vertex angle equations. The stationary multiplier condition is unaffected by the global sign, after renaming the multipliers. The sign should nevertheless be recorded explicitly because derivatives and numerical comparisons depend on it. Canonical `eq:Schlafli` elsewhere already uses the negative sign with interior angles correctly.

## External comparison hypotheses and primary-source pins

The following is a verification of the specific transferred statements, not a re-refereeing of all cited papers. Arxiv connector access failed with MCP SSE/ngrok HTTP 404; only minimal bibliographic queries and public primary sources were then used. No unpublished source was uploaded to an external reviewer.

| Source and pin | Checked scope and chapter consequence |
| --- | --- |
| [Rippa, Minimal roughness property of the Delaunay triangulation](https://doi.org/10.1016/0167-8396(90)90011-F), Computer Aided Geometric Design 7(6), 1990, 489–497 | The primary publisher abstract states minimization of integrated squared PL gradient for fixed planar data sites and function values. Thus the quadratic-form ordering is for a common nodal vector space. It is not a theorem about changing geometric sites, hyperbolic-volume monotonicity, or arbitrary topological flips. The original PDF mirror timed out and the publisher full page returned 403, so only the primary abstract was verified here; no claim to have checked its full proof. |
| [Disarlo–Parlier, arXiv 1411.4285v1](https://arxiv.org/pdf/1411.4285), Section 2.1 and Lemma 2.3, printed pages 6–9 | Connected orientable finite-type triangulable marked surfaces, with marked points on every boundary component, and their specified marked-point isotopy conventions. Cocompactness comes from finitely many combinatorial triangulation types; stabilizers are finite, giving the proper action used by the orbit quasi-isometry. The canonical qualification matches this. Preserve label and isotopy conventions rather than generalizing to unmarked boundary components. |
| [Brock, arXiv math/0109048v2](https://arxiv.org/pdf/math/0109048), introduction, Theorems 1.1–1.2 | The source develops the comparison for closed oriented surfaces of negative Euler characteristic: pants graph versus WP metric, and coarse convex-core volume versus WP distance, with topology-dependent constants and additive error where stated. Explicitly use that setting in this paragraph; a boundary/punctured extension was not independently verified here. |
| [Brock, arXiv math/0109050v1](https://arxiv.org/pdf/math/0109050), Theorem 1.1 | Closed oriented surface of genus at least two, pseudo-Anosov monodromy; mapping-torus volume is comparable to WP translation length with topology-dependent multiplicative constants. The current mapping-torus sentence already says closed. Do not silently apply it to the punctured fiber of an ideal layered triangulation. |
| Layered tetrahedron bound; compare [Disarlo–Parlier](https://arxiv.org/pdf/1411.4285), Proposition 2.19 | The chapter's sharper `N v3` follows directly by straightening a triangulation representing the hyperbolic fundamental class: each signed ideal tetrahedron volume has absolute value at most the regular ideal tetrahedron volume. Positive geometric shapes of the chosen combinatorial triangulation are not required. This bounds actual tetrahedron count, not automatically any chosen mapping-class word length. The source proposition uses a coarser constant; it is not being quoted for the sharp `v3`. |
| [Futer–Guéritaud, arXiv 1004.0440v2](https://arxiv.org/html/1004.0440), Theorem 1.2; Section 5, Proposition 5.4 and proof of Theorem 1.2 | An orientable compact 3-manifold with boundary a union of tori and an ideal triangulation: a positive angle structure is a full-space critical point of volume exactly when it supplies a complete hyperbolic metric. Leading–trailing edge equations alone test edge consistency; peripheral directions supply the real peripheral holonomy conditions needed for completeness. A boundary maximum may occur for a nongeometric triangulation even of a hyperbolic manifold. Specify full criticality and those hypotheses in the canonical sentence. |

For the `Nv3` argument, the ideal-tetrahedron bound also follows from the chapter's own triangle-volume formula: strict concavity plus symmetry puts the positive maximum at `(pi/3,pi/3,pi/3)`, while degenerate limits do not increase it. Summing signed volumes then gives the stated upper bound. No flip-monotonicity theorem is needed for that implication.

## Suggested canonical wording and reconciliation note

After the exact-center gap paragraph, add a compact statement such as:

> All local norms are taken on the intrinsic affine angle space. At a finite iterate `x`, let `lambda_t(x)` be the Newton decrement of `F-tV`. If `lambda_t(x)<=1/4`, then `V*-V(x)<=17m/(12t)`. One may maintain this neighborhood by increasing `t` by `1+1/(20 sqrt(m))` and taking one full Newton step: the decrement is at most `5/16` before that step and at most `25/121` afterward. Thus the iteration bound holds from an initially centered point, with `t>=17m/(12 epsilon)` as a sufficient terminal parameter. Controlled inexact solves require a corresponding energy-norm tolerance.

Retain a derivation of the finite-center gap in the text, a short proof, or an explicitly linked mathematical appendix; the constants alone should not become an unexplained assertion.

Replace the Casson–Rivin opening of the critical-point paragraph by:

> For an ideal triangulation of an orientable compact three-manifold whose boundary is a union of tori, a positive angle structure critical for volume on the full angle space gives the complete hyperbolic metric. Full criticality includes peripheral directions; edge variations alone do not impose completeness.

Begin the Brock comparison with “For a closed oriented surface of genus at least two, ...”, while leaving the preceding more general marked flip-graph statement separate. Preserve the following warning about transferring closed results to punctured fibers.

Suggested reconciliation-note content, outside the immutable historical import:

* The fixed-dihedral disk and free-dihedral `P_3` programs have different tangent spaces and Hessian structure. Positive angle feasibility is distinct from convex developed boundary and from geometric closure.
* Historical exterior-angle Schläfli formula at line 934 has the wrong sign; the stationary multiplier characterization survives the sign correction.
* Historical `P_3` positive-maximizer assertion at 898–900 must allow closed maxima with `(pi,0,0)` triangles. Uniqueness in angle coordinates follows under positive feasibility by the argument above; positivity and geometric realization need separate hypotheses.
* The no-needle proposition does not classify every possible cluster degeneration or prove a universal non-splitting theorem.
* A barrier short-step bound does not establish an unrestricted plain-Newton iteration bound. Word length must include requested accuracy and conditioning; zero limiting angles prevent uniform angle-error claims.
* Historical separator claims, floating rank selections labelled exact, and timing ratios remain historical evidence unless their hypotheses and end-to-end costs are re-established. The advertised `129/0.16` timing ratio omits the reported feasibility cost `0.99`; including only that already changes it to about `112`, before other unmeasured costs. No fresh historical benchmark was run here.
* Tangent-horosphere/zero-shear/modular-holonomy statements require an actual geometric realization and the stated combinatorial situation; abstract angle equations or stationary multipliers alone do not establish embedding or that classification.

## Reproducible independent diagnostics and evidence boundary

Artifacts alongside this report:

* `companion_reference_probes.py`: Python standard-library diagnostic, importing neither the toolkit nor the historical scripts.
* `companion_reference_probes.json`: fresh results plus SHA-256 identities of baseline canonical source, historical companion, and pre-existing audit.

Command: `python3 execution/section9-chapter-2026-10-31/companion_reference_probes.py`, run from the outer workspace.

The 10,000 seeded binary64 triangle probes gave maximum relative `A`-identity residual `8.22e-13`, scaled third-derivative residual `8.11e-13`, and tangent-sum residual `2.67e-15`. The largest sampled compatibility quotient was about `1.516`, below the proved bound `sqrt(3)`; sampling does not prove that bound or determine its sharp constant. The explicit boundary counterexample reproduced angles `(90,60,30)` and `(120,30,30)` degrees and boundary angle `210` degrees. Degeneration probes support the derived `1/sqrt(6)` asymptotic and the finite versus divergent boundary derivatives. Short-step constants were checked with exact rational arithmetic.

These diagnostics support transcription and arithmetic checks. The proof arguments are written above; no automatic theorem prover, interval certificate, global enumeration, new numerical solver, or complete historical replay is claimed. Changes made by the separately authorized chapter builder during this review were confined to its own task and were not treated as independently audited mathematical revisions.
