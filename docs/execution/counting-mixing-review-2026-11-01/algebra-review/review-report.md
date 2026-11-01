# Independent mathematical review of Sections 23–25

**Decision: approve the four frozen files at the hashes in `approved-hash-manifest.json`, within the scope below.** I found no blocking mathematical defect and request no mathematical repair. This is an independent review of the local derivations and of the statements and normalizations of the cited inputs. It is not approval of the maintained computational companion, a re-refereeing of every external proof, or final PDF/typesetting approval.

The review read all 881 lines of Section 23, 659 lines of Section 24, 348 lines of Section 25, all 52 ledger records, all 14 source records, and the author handoff, freeze manifest, patch, and companion specification. The baseline repository HEAD was `9c8b61790aaa674902b9d60e80122c318a578bcc`. All four supplied SHA-256 values matched before review and again in the independent probe run. Independently extracted labels comprise 91 unique labels: 80 substantive labels covered exactly once by the ledger, and 11 structural or figure labels.

**Independent derivations and delicate points.**

For the normal Hessian, the index form for a periodic normal field is `integral((f')^2 - K f^2)`, so curvature minus one gives the stated strictly positive form. Self-intersections do not change this local calculation. The equal-time broken-geodesic energy has value `ell^2` at constant speed. The hyperbolic law of cosines gives the chord length `2 asinh(sinh(r) sin(theta/2))`; each reconnection has two such chords. Its strict saving is a surgery effect. It is not a direction in the original Hessian domain.

For length triangularity, complete resolution replaces genuine crossings by shorter local chords. At a multiple crossing a noncrossing endpoint matching cannot retain all the original intersecting diameters. This supplies strict saving in every state. Products give the weak length inequality. For a nonsimple primitive, its finite resolved expansion has maximum output length strictly below its own length; substituting this expansion into the degree-k Chebyshev polynomial retains strict inequality below `k ell`. For a simple primitive only the leading monomial has equality. Thus the first mass for `m alpha` has the primitive numerator `ell(alpha)`, and no other orbital label can cancel it. The compact marked-family gap uses finitely many possible nearby labels and positive continuous length differences; it does not claim uniformity over growing targets.

The orientation factor in the Selberg formula is correct. Inverse primitive conjugacy classes are distinct on a torsion-free oriented hyperbolic surface, and SU(2) traces of inverses agree. Grouping them doubles Naud's denominator `2 sinh` to the chapter's denominator `sinh`. The rank-two identity term is also correct because area divided by `4 pi` equals `g-1`. Expanding the determinant product logarithm gives a positive derivative with numerator the primitive length; the additional factor two at `v=s+1/2` produces exactly the same orbital mass.

The bracelet argument preserves the needed magnitudes. A spin identification and the change from negative to unnegated traces change diagram/basis signs, and `P_n(-x)=(-1)^n P_n(x)` preserves the absolute coefficients. The positive twisted Fuchsian evaluation is used only for an algebraic bound. The ratio of a fixed positive-degree Chebyshev coefficient to `2 cosh(n ell/2)` is finite because the former is polynomial in n. Extra supports can contribute only constant Chebyshev terms, whose relative magnitudes are at most one. This proves the fixed-target bound; it does not produce a uniform bound for arbitrary targets.

The all-channel weighted coefficient estimate and the fixed-coefficient measure bound are different estimates, used correctly. Orbit packing gives at most exponential orbital growth. Gaussian decay dominates either exponential estimate on compact subsets of `Re(t)>0`, since `Re(1/t)` has a positive minimum there. Fixed-coefficient Laplace transforms converge for `Re(s)>1`. The smooth length cutoffs of a Gaussian have Fourier transforms converging in the Schwartz topology; at each fixed unitary twist, the finite exceptional spectrum and Weyl growth justify the spectral limit. The unboundedness example for the coefficient of a simple trace prevents replacing this construction with uniform-norm continuity. Differentiating atom positions has the stated minus sign in front of `delta'_L`, and local metric length derivatives add only polynomial factors to the Gaussian tail.

The primitive extraction identity is a locally finite divisor convolution: substituting `Q_V=sum_j D_j P_(psi^j V)` into the inverse sum leaves coefficient `sum_(k|n) mu(k)`. There is no missing dilation amplitude and no factor `1/k` in this measure inversion. It needs higher symmetric-power spectra. Conversely, the Euler logarithm has ordinary tensor powers and a factor `1/m`; replacing those powers by Chebyshev traces changes the product. Coincident lengths explain why one rank-two aggregate cannot simply be raised pointwise to recover individual power sums.

For total multicurve counting, the lattice-cell inclusions are valid for a fundamental cell contained in the radius-rho ball. Translating by the inball center before homothety is necessary and correctly done. The upper volume increment bounds both errors for `R>=rho/r`. EMM supplies length convexity and the finite polyhedral overlap handling. Finite convex refinement yields compact unit-length bodies with nonempty interior in full-dimensional chambers; boundary faces have lower-dimensional lattice growth. Their actual lattice covolumes account for parity. This establishes the total weighted multicurve error without asserting an effective connected-orbit estimate. Möbius inversion then gives primitive integral laminations, which can be disconnected. The punctured-torus factor one half is required for unoriented curves.

The near-collision construction works also in genus two: cutting along a nonseparating pair with connected complement leaves a four-holed sphere, where an interior twist moves the third cuff through infinitely many isotopy classes. Expanding `2 acosh(cosh(R/2)+2A)` gives the stated leading gap and action gap. Its normalized contribution is a statement about an individual orbital label before cancellation. The time bound therefore does not prove a lower bound for a net signed remainder.

For the uniform trace gap, a bracelet contributing to a simple coefficient has odd target winding; every additional support has even winding. Positivity and integer coefficients force one of the stated positive excesses. The exceptional sole target bracelet would contradict strict triangularity. The derivative of the action gap is negative because `y/sinh(y/2)` decreases. The orbit-packing constant follows from the ratio of hyperbolic disk areas, bounded by `exp(U+2D)/(1-exp(-epsilon/2))^2`. Summing odd windings gives `(1+exp(-epsilon))/(1-exp(-epsilon))^2`. In the shell sum, `t<=epsilon/4` gives Gaussian loss at least `exp(-2j)` against count growth `exp(j)`. The displayed recovery constant is conservative and valid. Existence of the later orbital label `(alpha,3)` does not depend on its net mass surviving cancellation.

For the support partition, the degree bound is on distinct supports, while the trace weight uses parallel multiplicities. Root-of-unity extraction has operator norm at most one on the finite sample vector. Möbius inversion is absolutely convergent by `km>=k+m-1`. Under the stated hypothetical sample remainder, the split at `k=1/s` gives the asserted Laplace error because `d-eta>1`. The sharp desmoothing error is the sum of a positive shell bound, normalization loss, and the assumed smooth error; optimizing h gives `min(1,eta/(m+1))`. No positive-axis Tauberian remainder is silently promoted to a sharp count. The component algorithm needs valid primitive integral division before it detects one distinct support.

For the global filter, both roots of `u^2-u=2 cos(theta)` have modulus at most two; their symmetric power sums are single-valued polynomials, including at a repeated root. Averaging their recurrence yields nonnegative integer weights and the stated generating function. Replacing each cuff trace by u in a pants monomial records total multiplicity degree. Identifying two cuff images preserves that degree. The remaining integral is the nonzero cosine Fourier mode, so all one-crossing iterates vanish. The empty weight is two, and the identity contribution is treated accordingly.

The obstruction words are cyclically reduced and nonperipheral in the pants free group. Their homology vectors `(1,0)`, `(3,2)`, `(3,2)` are indivisible, excluding proper powers there; for the first word, cyclic reduction distinguishes it from the peripheral a class despite the matching homology vector. Convexity keeps the geodesics in the pants, whose only simple closed curves are peripheral. Any ambient proper root follows the same image, hence lies in the pants group and is excluded as well. The three exact trace polynomials sum with the displayed signs to the simple trace. The triangle inequality gives the one-third obstruction. It applies to one fixed linear functional on all four labels; it does not rule out length-dependent or nonlinear methods.

For the Euler diagonal, each fixed length cutoff has finitely many primitive supports and multiplicities, so the formal product and logarithm are well-defined before any analytic claim. Genuine self-crossings or crossings of distinct components force strict shortening; repeated components can be separated while preserving a fixed positive saving at a genuine crossing. Equality requires a mutually disjoint multiset of simple primitives, which is uniquely determined by the target and has coefficient one, without a factorial. Local finiteness isolates this first atom, including the empty target at zero. Multidiagram sign coherence bounds each fixed coefficient by the positive product of hyperbolic traces. The logarithm of `2 cosh(u/2)` divided by u decreases, so the systole bound controls every geometric ratio; orbit growth gives convergence for `s>3/2` in addition to that ratio condition. A fixed convergent Laplace majorant controls every coefficient Gaussian transform. This does not assert convergence in a norm of the full character-valued product.

**Claim-by-claim coverage.** “Approve” means the statement holds with its written hypotheses and evidence boundary. For external or conditional claims it does not replace those hypotheses by a new proof.

| Claim | Decision and independently checked point |
| --- | --- |
| 23.01 | Approve: equal-time energy and periodic normal index form; Hessian positivity does not select simplicity. |
| 23.02 | Approve: hyperbolic chord formula and strict surgery saving. |
| 23.03 | Approve using the Charles–Marché basis theorem; integral skein coefficients and basis sign conversion agree. |
| 23.04 | Approve using the twisted trace formula; rank, inverse grouping, primitive numerator, and finite cutoff are consistent. |
| 23.05 | Approve: strict resolution inequality, product inequality, and power equality cases cover nonsimple primitives and iterates. |
| 23.06 | Approve: unique first label, positive mass, compact marked-family gap, and possible vanishing of nonparallel targets. |
| 23.07 | Approve: local cutoff moments recover the length exactly without a limiting interchange. |
| 23.08 | Approve using sign coherence; spin and Chebyshev parity preserve absolute coefficients. |
| 23.09 | Approve: polynomial winding growth divided by exponential trace growth; fixed-target qualification retained. |
| 23.10 | Approve: each orbital mass is O(L), and packing gives the total-variation growth bound. |
| 23.11 | Approve: Gaussian and Laplace domains and local uniform derivative majorants. |
| 23.12 | Approve: weighted coefficient convergence and spectral cutoff limit; no arbitrary infinite-expansion uniqueness. |
| 23.13 | Approve: fixed-parameter tail majorization retains the exact endpoint exponent; eventual real logarithms are justified. |
| 23.14 | Approve: recurrence, factorial coefficients, parity, and primitive-length masses. |
| 23.15 | Approve: generating function, csch expansion, sech/tanh conversion, and one-family half-plane. |
| 23.16 | Approve: figure-eight polynomial and all-iterate cancellation; distinct cuff indexing and identification warning are correct. |
| 23.17 | Approve: atom-location derivative sign and smooth local finite sums. |
| 23.18 | Approve: endpoint first variation extends to immersed curves; original cosine formula was independently recovered. |
| 23.19 | Approve: differentiating the mass and action gives the stated leading response; local uniform tail control suffices. |
| 23.20 | Approve: determinant logarithmic derivative, orientation factor two, and separate coefficient convergence domain. |
| 23.21 | Approve: exact Fricke/Adams defect; arbitrary Chebyshev substitution is not multiplicative. |
| 23.22 | Approve with additional higher twisting spectra: locally finite Adams/divisor inversion. |
| 23.23 | Approve as an external example theorem: scalar unmarked data differ from the labelled twist family. |
| 23.24 | Approve: positive multicurve lattice asymptotic and partial summation give Gamma(d+1). |
| 24.01 | Approve as the EMM external theorem for a fixed nonzero rational multicurve; no numerical exponent inferred. |
| 24.02 | Approve: translated inball homotheties, lattice-cell sandwich, and explicit volume error. |
| 24.03 | Approve using train-track convexity and finite overlap partition; actual lattices and faces give O(R^(d-1)). |
| 24.04 | Approve: primitive integral divisor inversion and distinction from connectedness. |
| 24.05 | Approve: primitive torus lattice count divided by two for unoriented curves. |
| 24.06 | Approve: fixed-surface twist construction and pants inverse-cosh expansion. |
| 24.07 | Approve: necessary scale for one absolute orbital contribution; equal-length signed cancellation remains possible. |
| 24.08 | Approve using bracelet positivity: integer trace excess and decreasing action gap. |
| 24.09 | Approve: disk packing and the exact odd-winding series produce the constants. |
| 24.10 | Approve: later orbital label exists, shell estimate and sufficient time follow; target enumeration is not supplied. |
| 24.11 | Approve: positive support polynomial, degree bound, and one-support interpretation. |
| 24.12 | Approve: absolutely convergent divisor inversion with no factor 1/k. |
| 24.13 | Approve: degree below q eliminates aliasing and Fourier extraction preserves the common error bound. |
| 24.14 | Approve as conditional: assumed sample expansion and d-eta>1 give the transferred Laplace remainder. |
| 24.15 | Approve at the stated algorithmic scope: components after valid integral division select one support; average remains unproved. |
| 24.16 | Approve: positive total counts bound the shell, including endpoint atoms. |
| 24.17 | Approve as conditional: shell loss plus smoothing error gives the displayed exponent. |
| 24.18 | Approve the scope boundary: minimum recovery and growing-length counting are different regimes. |
| 25.01 | Approve: root bounds and weighted coefficient functional norm; empty weight is two. |
| 25.02 | Approve: recurrence, exact arcsine moments, branch normalization, and generating series. |
| 25.03 | Approve using the one-crossing pants input: total degree survives cuff identification and cosine averaging kills all iterates. |
| 25.04 | Approve: the functional acts on the convergent weighted sum; the surviving residual is signed and unestimated. |
| 25.05 | Approve: exact trace identity plus nonperipheral, indivisible-homology word topology; fixed-functional obstruction only. |
| 25.06 | Approve: positive length and finite orbital cutoffs define the formal convolution product. |
| 25.07 | Approve: strict shortening leaves one disjoint-simple multiset at the target length, with unit mass. |
| 25.08 | Approve: coefficient majorization, ratio condition, half-plane, and complex Gaussian majorant. |
| 25.09 | Approve with higher twisting data: ordinary tensor powers reconstruct the scalar-trace Euler logarithm. |
| 25.10 | Approve: unit first atoms give the nonlinear reconstruction; no conditioning or remainder bound follows. |

**Independent probes and review quality.** The reviewer wrote and ran `independent_probes.py` using only integer and rational arithmetic, importing no maintained companion code. Its result file records **487 exact checks**, including Chebyshev and figure-eight polynomials through order 24, root moments through order 48, eight dense-chart Laurent identities, cyclic-word/homology checks, and a separate formal-length Euler fixture with lengths 3, 4, 5, 9 through cutoff 18. The finite Euler product was compared with a separate multiset/binomial enumeration and its convolution logarithm. Forty target first atoms were checked. The intentionally wrong ordinary-power-to-Adams replacement was detected at length six. Four coverage checks and four frozen-byte checks are included in the count; it is not a count of 487 mathematical theorems.

The symbolic matrix chart is `A=diag(a,a^-1)`, `B=[[b,c],[d,(1+cd)/b]]`. All Laurent coefficients of the identity defects vanish. Since pairs with diagonalizable A of distinct eigenvalues and nonzero transformed b form a dense open conjugacy chart, and word traces are regular functions on SL(2) pairs, this is an exact algebraic check of the displayed word identities. This reasoning has no bearing on geodesic primitivity or simplicity; those were checked separately by the pants argument. The bounded recurrence and Euler fixtures do not prove arbitrary geometric triangularity, infinite-series convergence, enumeration, or asymptotics.

The anti-pattern review found no promotion of signed data to positive counts, no missing orientation half/factor two, no confusion between component multiplicity and distinct support, no general primitivity test based on an unchecked coordinate gcd, no ordinary-power/Adams substitution in the Euler product, and no inference of a simple-curve error exponent from fixed-target convergence. Claims remain visibly external, conditional, exact, or open as appropriate. The pending companion execution fields are author-freeze provenance, not an analytic defect; downstream integration should link the independently reviewed execution record rather than silently overwriting the evidence history.

One optional editorial clarification would rename ledger claim 23.12 from “entire heat expansion” to “full heat expansion,” since holomorphy is only asserted on `Re(t)>0`. Its hypotheses and chapter text already specify that domain correctly; this wording is not a mathematical blocker and no change is required by this approval.

The [source audit](source-audit.md) records all 14 primary-source checks and access limits. In particular, Wolpert's cosine formula was recovered in this review, while direct access to Mirzakhani's journal PDF still timed out; the earlier primary preprint verifies the substantive leading-term statement. The independent proof approval rests on the stated imported theorems and the local derivations reviewed above, not on an assertion that the entire cited literature has been refereed anew.

No canonical files, computational companion files, historical artifacts, git metadata, commits, or uploads were changed by this reviewer. The approval does not wait for numerical-companion or PDF integration, and does not award those stages approval. Any subsequent mathematical change to the approved files requires a new hash record and review of that change.
