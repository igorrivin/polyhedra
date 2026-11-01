# Independent Section 15 analytic review

Date: 2026-11-01. Reviewer task: `airy_proof_review`.
Baseline: `3ddf610dbe4578c7828e55f4e9cd92aacaba6df6`.
Canonical files were read but not edited by this reviewer.

The revised analytic argument is approved for the stated proposition: fixed
`Z`, real `|zeta| <= Z`, `b -> 0`, the specified equal-label regular family,
the explicitly pole-cleared Barnes integral, and upward measure `dw/i`.
This is an additive expansion through its first correction. The final
hash manifest, when present, identifies precisely which chapter and ledger
bytes carry this approval. A later change is not automatically covered.

The review does not assert a theorem for general angle data, unbounded
transition parameter, fixed positive volume, an integrated cone-metric
measure, or a global state integral. It does not certify floating-point
quadrature or reproduce the proofs of the cited special-function and
Murakami–Yano theorems.

## Independent source checks

The reviewer independently fetched the following primary sources, rather
than relying on the author's source notes:

- Teschner–Vartanov, [arXiv:1202.4698v3](https://arxiv.org/html/1202.4698v3)
  and its [PDF](https://arxiv.org/pdf/1202.4698v3),
  equation (2.27), its prefactor and contour prescription; Appendix A,
  equations (A.1), (A.11), (A.13), (A.15), (A.16), and the Gamma quotient.
  Printed page pins 7 and 22–23 were independently confirmed in the PDF.
- Murakami–Yano, [author-hosted paper](https://murakami.w.waseda.jp/papers/tetrahedronrev3.pdf),
  Theorem 2, equations (0.1), (0.4)–(0.8), and the real Lobachevsky
  formulation (1.14)–(1.18), PDF pages 3–4 and 7–8. The publisher PDF
  endpoints returned HTTP 403 to this reviewer's fetch; the author's
  primary-source copy was readable. The printed statement that the
  absolute values of the real formulas equal hyperbolic volume was checked.
- [DLMF 9.5.4](https://dlmf.nist.gov/9.5.E4), including the orientation
  from the lower Airy ray to the upper Airy ray. Its deformation to a
  positive vertical line was checked separately below.

These checks verify the quoted statements and their specialization. They
are not independent reproofs of those external results.

## Issues found and repaired

1. The printed TV v3 Gamma integral has a factor-of-two error in the
   linear subtraction. Both reviewer and author found it independently.
   The chapter now writes the convergent formula and explains the correction.
2. The original real-integral argument did not distinguish the centered
   scaled strip from the larger fundamental strip of `S_b`. The chapter
   now separates arbitrary fixed-b contour relocation from uniform
   small-b estimates on a fixed closed scaled substrip near the fold.
3. The old phase-constant argument relied on incompletely specified complex
   dilogarithm branches. The new argument specializes the real
   Murakami–Yano formula and proves the constant exactly by continuity.
4. The whole-contour deformation, perturbation of the far-tail gap, and
   integrated weighted remainder were too compressed. They now have
   the quantitative bounds needed for the stated uniform expansion.
5. The original resonance wording appeared to assert noncancellation at
   every displayed resonance. The proof only gives all sufficiently large
   indices and a fixed bounded physical window. The wording now makes this
   restriction explicit and makes no such assertion near negative Airy zeros.

## Normalization and fixed-b analytic continuation

In TV (2.27), equal labels give four identical square roots of
`S_b(3 alpha-Q)/S_b(alpha)^3`; their product is its square. No residual
square-root sign remains on this slice. The four positive-orientation
integrand arguments reduce with multiplicities 4, 3, and 1 to those in
the chapter. Replacing the printed `dw` by `dw/i` changes the value by
the explicit factor `1/i`, exactly as stated.

Applying the `1/b` shift to `x=3 alpha-Q` gives the factor
`2 sin(pi x/b)`. Here `pi x/b=-(3 eta-pi)/(2 b^2)-pi`, whose sine is
`sin((3 eta-pi)/(2 b^2))`. Squaring proves the pole-clearing identity,
including its constant and sign.

For fixed positive `b`, TV's sector asymptotics after its change
`s_b(i x-iQ/2)` yield

`|S_b(a+iT)| = exp(pi(a-Q/2)|T|)(1+o(1))`.

The eight factors have total real coefficient

`4(w_R-3 alpha-Q/2)+3(4 alpha-w_R-Q/2)+(2Q-w_R-Q/2)=-2Q`.

Thus the full integrand decays as `O(exp(-2 pi Q |T|))`, uniformly
between any two fixed separating lines. The horizontal connectors vanish.
This proves absolute convergence and line independence without applying
the centered-strip estimate outside its domain. Small complex changes of
`alpha` only change bounded multiplicative constants and preserve the
separating contour; dominated integration gives local holomorphy.
The path from `alpha=Q/2` to the near-fold real labels has no integration
pinch. Pole clearing removes the relevant external prefactor poles.

## The real integral and uniform double-sine remainder

The corrected Gamma subtraction is `-(Q-2x)/(2u)`. Subtracting the
two Gamma integrals gives the convergent fundamental-strip formula

`log S_b(x)=integral [sinh((Q/2-x)u)/(2 sinh(bu/2)sinh(u/(2b)))
                    -(Q-2x)/u] du/u`.

At `x=z/b+b/2`, `u=2bs` splits this exactly into `F(z)/b^2+D_b(z)`,
with the displayed `D_b` coefficient `+1/2`. There is no hidden
normalization constant. For the leading integral, `F''=pi cot(pi z)`;
`F(1/2)=0`; and `F'(1/2)=log 2`. To check the last identity, put
`K(s)=coth(s)-1/s`. Then

`s^(-2)-(s sinh s)^(-1) = [K(s)-K(s/2)]/s`.

Integrating between cutoffs and changing scale leaves the upper
interval with limit `log 2` and a lower interval with limit zero.
Hence `F=-Lambda(pi z)/pi`, with exactly the chapter's normalization.

For bounded complex `z` within the scaled strip, the kernel estimate
`|csch u-1/u|<=C u` makes `D_b=O(b^2)` absolutely; compact-set
Cauchy estimates give all specified fixed-order derivatives.
For unbounded imaginary `z`, the real part of the numerator equals
`sinh((1-2 Re z)s) cos(2 Im z s)`. This retains its zero at `s=0`
and gives the required integrable bound independent of `Im z`.
An absolute complex bound is not being inferred from this real-part
argument. Shifting `z` by `(kappa-1/2)b^2` produces the stated sine
amplitude; the Taylor error is uniform in modulus on a closed substrip
because the second derivative of the leading primitive is bounded there.

The necessary centered strip is `0<Re(bx-b^2/2)<1`. Near the fold all
five arguments have a fixed positive scaled margin, including the
argument close to the upper boundary. The full defining contour need
not share that margin; the preceding fixed-b relocation handles it.

## Exact phase constant and finite coefficients

For the regular slice, the real Murakami–Yano functions are

`U_Lambda = Lambda(v/2)+3 Lambda(v/2+2 eta-pi)
            -4 Lambda((v+3 eta-pi)/2)`,

`Delta_Lambda = 2 Lambda((3 eta-pi)/2)-6 Lambda((eta-pi)/2)`.

Oddness and period `pi` give exactly
`G=2(U_Lambda+Delta_Lambda)`. At either unit-circle root the external
theorem gives `|U_Lambda+Delta_Lambda|=W`. Both roots approach the
regular Euclidean fold, and the shrinking tetrahedron has `W -> 0`.
Continuity therefore proves `G_star=0` exactly. This argument uses no
high-precision agreement to infer an identity and needs no choice of
an unspecified complex dilogarithm branch.

The reviewer also independently derived the derivatives from the five
affine angles, and checked them with exact SymPy arithmetic in
`independent_algebra.py`, importing no author companion. The output is
`independent-algebra-result.json`. It verifies both first-derivative
logarithmic ratios equal 1, all displayed higher derivatives,
`A_star=9/4`, `(log A)_v=7 sqrt(2)`, the rational identity for `Psi'`,
the fixed-b tail coefficient, the Airy correction cancellation, and the
oriented scalar `3/4`. These are finite algebra checks, not the proof of
the contour or uniform estimates.

## Whole-contour gap and local majorant

On the fold vertical line, the stated arctangent expression for the
negative derivative of `Re G` follows from the logarithm of `sin`
on `0<Re theta<pi`. Its rational derivative is positive for positive
`r`, and its limit is `2 pi`. Thus the fold is the unique maximum.

For nearby real parameters the identity `4a1+3a2+a3=2pi` makes the
large-positive-y derivative `-2pi+O(exp(-y))`, uniformly. Complex
conjugation treats the other tail. Compact annuli retain their strict
gap by continuity. This proves a fixed negative gap beyond any
sufficiently small fixed fold neighborhood, followed by linear decay.
The amplitude decays as `O(exp(-|y|))`, and the real-part quantum
remainder bound transfers the estimate to the exact integrand.

On the displaced line `v=v_star+c lambda+iy`, with fixed `c>0`,
`G_vv=54 c lambda+O_Z(lambda^2)` is positive and `G_vvvv` remains
strictly negative. The real part of the analytic Taylor expansion is
`-G_vv y^2/2+G_vvvv y^4/24+O(y^6)`; a uniform sixth-derivative bound
and a sufficiently small fixed neighborhood yield
`-c1 lambda y^2-c2 y^4`. Since `G(v_star+c lambda,eta)/h=O_Z(1)`,
rescaling `y=lambda Im(Y)/3` gives an integrable Gaussian independent
of the small parameter. This is valid on both sides of the transition
for bounded real `zeta`; positivity of `zeta` is unnecessary here.

## Integrated remainder, orientation, and pole scope

Analyticity supplies
`R_G=O(|x|^5+|t||x|^3+t^2|x|+|t|^3)`. Under the stated weights,
`R_G/h=O_Z(lambda^2(1+|Y|^5))`. On `|Y|<=lambda^(-1/12)`, both
the quartic order-lambda phase correction and this remainder are
uniformly small. Exponentiation, multiplication by the amplitude,
and the `O(lambda^3)` exact quantum error produce
`O_Z(lambda^2(1+|Y|^8))` against the base Gaussian. Its integral is
`O_Z(lambda^2)`. The Gaussian controls the rest of the local contour
by more than every power of lambda; the fixed global gap controls
the remaining contour exponentially. Thus the passage from a local
pointwise expansion to an integrated additive error is justified.

For the Airy contour, at imaginary height `T` the horizontal connector
has `3c<=x<=T/sqrt(3)` and real exponent at most
`-(8/9)xT^2+Zx`. It vanishes, with any fixed moment factor included.
The upward orientation is the one in DLMF 9.5.4. Consequently the
moments give `(-1)^k Ai^(k)`. The fourth derivative identity cancels
the `zeta^2 Ai` terms, leaving `-3sqrt(2) Ai'`. Finally
`dw/i=lambda dY/(6pi i b)` and `A_star=9/4` give `3lambda/(4b)`.

The positive minimum of `Ai` on each fixed `[0,Z]` makes the cleared
quantity nonzero for sufficiently small b. Therefore zeros of the
squared sine are genuine double poles there, including all
sufficiently large members of the displayed sequence. No such uniform
noncancellation is asserted over negative Airy zeros. The chapter
explicitly excludes the unbounded-zeta and fixed-volume matching limits.

## Evaluator-bound consultation (not an implementation review)

The evaluator author separately requested an analytic check of its
finite csch expansion remainder. For `K>=1`, the coefficient and bound
sent to the reviewer imply

`|D_b-D_K| <= b^(4K+2) zeta(2K+2)/pi^(2K+2)
 * (2K)!/2^(2K+1)
 * [HurwitzZeta(2K+1,a)+HurwitzZeta(2K+1,1-a)]`, `a=Re z`.

This follows from `|sinh((1-2z)s)|<=cosh((1-2a)s)` and the geometric
expansion of `1/sinh s`. The full logarithmic multiplicity is 16.
The reviewer checked these constants and the stated rational
replacements using a centered-strip margin. Converting a logarithmic
error `B` into integral error still requires `exp(B)-1` times an
absolute-integrand bound. No evaluator code, numerical result, or
quadrature certificate is approved by this consultation.

## Frozen author snapshot

The author froze the analytic chapter and its ledger for this review.
The chapter SHA256 is
`2688ef6862492f93cd49de4c50017eb33496ad0d1b77cd8f4220150910a2ef1e`.
The ledger SHA256 is
`8d5ba46372dda6a108bf913e30b661f87e16b4985b444ed8107d9feefb4c6c3d`.
All 21 chapter labels and their order match the baseline. The ledger has
13 unique claims, all of whose labels exist. The ledger separates
author analytic derivation, external inputs, finite exact checks,
approximation-column checks, and the historical calculation's missing
provenance. Its independent-review pointer appropriately refers to a
separate record. The reviewer approves that distinction and the analytic
claims at these exact hashes. The final machine-readable record is
`approved-hashes.json`; subsequent numerical supplementation requires a
new delta review and a new manifest.
