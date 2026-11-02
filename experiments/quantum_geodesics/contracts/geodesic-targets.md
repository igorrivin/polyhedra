# Sections 17–22 finite companion contract

Author specification, 2026-11-01. This is a mathematical contract for a later implementation role, not maintained code or an execution result. Baseline: `151673b1817e66aae493eb7da1be5ddf49adfe0f`.

Use the existing isolated Python environment. Do not install dependencies. Exact rational and polynomial identities are exact evidence; high-precision values, numerical derivatives, quadrature, and precision comparisons are floating evidence. No numerical value below is an interval enclosure. Report the evaluation precision separately from analytic truncation inequalities.

## Conventions and admissible inputs

- Curvature is -1. Closed lengths are positive; a cusp cuff has length zero. Positive geometric trace is `2*cosh(length/2)`, and is distinct from a globally signed SL(2) trace.
- Simple and figure-eight classes are unoriented and retain their topological labels even if lengths agree. Figure-eight curves are primitive and have exactly one transverse double point. A torus simple class produces two distinct N-type labels and one H-type label.
- Real inverse hyperbolic cosine is the nonnegative branch on `[1,infinity)`. All square roots are nonnegative. Reject invalid domains instead of clamping them.
- A local endpoint-distance fixture requires `d>0`; ordinary seam inputs require `a,b>0`, `c>=0`. An internal twisting cuff has `a>0`; torus boundary `b>=0` includes the cusp.
- Twist is signed hyperbolic displacement, with Dehn twist period `a`. H-kernel truncation first reduces the representative to `|tau|<=a/2` and records the integer relabeling. A fixed crossing curve's length is not periodic.
- Truncated cusp length is signed when decorations overlap. `lambda=exp(d/2)` with no additional square-root-of-two factor. Horocycle length is `H>0`.
- Every artifact identifies the exact formulas/labels, inputs, decimal precision, residuals, software versions, source hashes, and evidence status. A source-theorem statement check is not a full proof audit.

## Required finite groups

### G1. Torus unfolding normalization

Check the rational factors `1/2 * (pi^2/12) / (pi^2/12) = 1/2`, independently evaluating the Fermi integral `I=integral_0^infinity x/(1+exp(x)) dx` against `pi^2/12` and a finite alternating Dirichlet sum. Integrating only to `R` has analytic tail at most `(R+1)*exp(-R)`. The alternating sum through `m=M` has error at most `1/(M+1)^2`, with the alternating sign. Use `R=12,30,60` as distinct finite checks, not an infinite quadrature that hides its tail. This checks the calculation given the stack WP convention; it does not numerically prove McShane or an orbifold quotient factor.

### G2. Pants traces and torus multiplicities

For rational SL(2) matrices constructed independently of the trace polynomial, verify `tr(A B^{-1})=tr(A)tr(B)-tr(AB)`. Include at least six matrices with nonzero off-diagonals and positive/negative signed traces. Keep the positive-pants specialization separate: compatible pants lifts have `tr(A)=t_a`, `tr(B)=t_b`, `tr(AB)=-t_c`, yielding `t_gamma=t_a*t_b+t_c`.

Check the exact inverse linear map from `(t_a,t_b)` to `(2t_a+t_b,t_a+2t_b)` and back. At `t=3,4,5,10`, verify the two N traces `3t` and the H trace `t^2+2`, retaining all three labels. At `t=3` the N traces are both 9 and the H trace is 11. These fixtures do not establish topological classification or global simplicity of a word.

### G3. Universal figure-eight kernel and analytic remainder

Let `x_0=x>6`, `x_{n+1}=x_n^2/9+2`, and
`F_N(x)=sum_{n=0}^{N-1} (-1)^n 2^{-n-1} h(x_n/3)`.
Use the stable formula `h(t)=(4/t^2)/(1+sqrt(1-4/t^2))` rather than cancellation in `1-sqrt(...)`. Compare with the direct formula where both are well conditioned. Required inputs: `x=6+10^-20, 6.01, 7, 9, 11, 30, 1000` entered as decimal strings or exact rationals. Evaluate at 70 and 110 decimal digits and for several finite `N` (for example `4,12,40,180`). If an implementation stops adaptively, it must record the actual `N` and its bound.

The analytic remainder is
`|F-F_N| <= B_N(x)=2^{-N-1} h(x_N/3) <= 2^{-N-1}`,
and its sign is `(-1)^N`. Independently test the *finite exact identity*
`2F_N(x)+F_N(beta(x))-h(x/3)=(-1)^{N-1}2^{-N}h(x_N/3)`.
This finite residual identity is stronger evidence than comparing two approximations to the same infinite formula.

Verify the finite telescoping coefficients algebraically as well. At large N the exact right-hand residual can be vastly smaller than working roundoff relative to the O(h(x/3)) quantities on the left. A rounded zero on the left is not relative verification of that positive or negative tiny residual. Use an absolute scale appropriate to the separately recorded roundoff, and report such a comparison as cancellation-limited. Retain the nonzero right-hand residual and B_N in stable or logarithmically scaled form; never replace a tiny positive bound by zero. Useful scaled checks include t^2*h(t), and log(B_N)=-(N+1)*log(2)+log(h(x_N/3)). Keep analytical truncation, numerical rounding, and finite coefficient telescoping as three distinct claims.

Check positivity and `h(x/3)/4 <= F <= h(x/3)/2` using analytic remainder allowances. For each of the finite simple-trace fixtures from G2, check `2F(3t)+F(t^2+2)=h(t)` with the bound `2B_N(3t)+B_N(t^2+2)` and separate floating residual. `x^2 F(x)` at increasing `x` is only an asymptotic illustration of the analytically proved limit 9.

Do not claim numerical evaluation of the all-geodesic sum. A finite list of simple traces supplies finitely many complete three-curve blocks, not an enumeration or an independent proof of McShane. No global curve-sum tail estimate is required because no global curve-sum approximation is proposed here.

### G4. Local distance, gradients, and positive Hessian

For `C=cosh(d)`, `z=C cosh(u)cosh(v)-sinh(u)sinh(v)`, `S=sqrt(z^2-1)`, compare `D=acosh(z)` with the hyperboloid Lorentz product of
`p=(cosh(u),sinh(u),0)` and `q=(C cosh(v),sinh(v),sinh(d)cosh(v))`.
The gradient is `(z_u,z_v)/S`. Independently compare numerical differentiation of the Lorentz-distance implementation with

`H=(sinh(d)^2/S^3) [[z cosh(v)^2,-cosh(u)cosh(v)],[-cosh(u)cosh(v),z cosh(u)^2]]`.

Its determinant is `sinh(d)^4*cosh(u)^2*cosh(v)^2/S^4 > 0`. Derive/check the simplifications algebraically using `cosh^2-sinh^2=1`; finite positive eigenvalues alone do not prove convexity. Include `d=.03,.5,2,7` and endpoint pairs `(0,0),(1,-2),(-3,2),(.1,.2),(4,4)`. Record both gradient and Hessian residuals and use 70/110 digits. Check `D(0,0)=d` and the orientation conversion `v -> -v`.

### G5. Ordinary seams and torus holonomy

For `a,b>0,c>=0`, evaluate the seam formula and verify the rearranged right-angled-hexagon identity. Use `(.2,.7,0),(1,1,0),(1,2,3),(8,.5,4)`. Do not call the rearrangement an independent geometric reconstruction.

An independent matrix check is available: set `X=diag(exp(a/2),exp(-a/2))`, `J_d=[[cosh(d/2),sinh(d/2)],[sinh(d/2),cosh(d/2)]]`, and `Y=J_d*diag(exp(-b/2),exp(b/2))*J_d^{-1}`. Direct multiplication gives `tr(XY)=2cosh(a/2)cosh(b/2)-2cosh(d)sinh(a/2)sinh(b/2)=-2cosh(c/2)`. Its two axes are ultraparallel at distance d. This verifies the seam convention via an independent matrix product.

The independent torus check is a matrix model. Put `X=diag(exp(a/2),exp(-a/2))`, `A^2=(cosh(a)+cosh(b/2))/(cosh(a)-1)`, `B_0=[[A,sqrt(A^2-1)],[sqrt(A^2-1),A]]`, and `B_tau=diag(exp(tau/2),exp(-tau/2))*B_0`. Matrix multiplication must independently give `det(B_tau)=1`, `tr([X,B_tau])=-2cosh(b/2)`, and `tr(B_tau)=2Acosh(tau/2)`. Test `a=.2,1,3`, `b=0,.7,4`, `tau=-4,-.5,0,.5,4`.

Compare numerical derivatives of `2acosh(abs(tr(B_tau))/2)` with
`ell'=A sinh(tau/2)/sqrt(A^2cosh(tau/2)^2-1)` and
`ell''=A(A^2-1)cosh(tau/2)/(2(A^2cosh(tau/2)^2-1)^(3/2))`.
Require `|ell'|<1` and `ell''>0` on these finite nondegenerate fixtures, with the general inequalities supplied analytically in the chapter.

Conditioning guidance for implementation: compute `delta=A^2-1` directly as `(1+cosh(b/2))/(2*sinh(a/2)^2)`. This avoids `cosh(a)-1` at a small cuff and subtraction of 1 from a nearly unit `A^2` at a large cuff. A stable length is `2*asinh(sqrt(delta+(1+delta)*sinh(tau/2)^2))`; it retains the tiny positive minimum even when a rounded A equals 1. Add at least `a=1e-12`, with `b=0,.7` and `tau=0,.5`, as small-cuff fixtures. Matrix commutator cancellation can lose digits in this regime: record requested precision, actual guard precision, and any reference accuracy limit instead of treating the matrix formula as an unlimited-accuracy oracle. No general degeneration solver is requested.

### G6. Coarea and exact twist integrals

For selected G5 pairs, evaluate on a finite `[-U,U]` both the direct integrand `cosh(ell(u)/2)^(-s)` and an independent length-side coarea integral. Remove the square-root singularity by `y=sqrt(cosh(r/2)^2-A^2)`; the transformed length-side integrand is `4(A^2+y^2)^(-s/2)/sqrt(A^2+y^2)` for `y>=0`. Its finite upper limit is `A*sinh(U/2)`.

Compare with `2 sqrt(pi) Gamma(s/2)/(A^s Gamma((s+1)/2))` for `s=.5,1,2,3,6` and `U=12,30,60`. The excluded two-sided twist tail is at most `2^(s+2)/(s*A^s)*exp(-s U/2)`. For `s=2`, also compare the exact finite integral `4*tanh(U/2)/A^2` and exact tail `4*(1-tanh(U/2))/A^2`.

Check the sublevel formula at `R<r0`, `R=r0`, and `R=r0+.1,r0+2,r0+6`, with `r0=2acosh(A)`. Substitute the endpoint twists back into the independently calculated matrix length. Quadrature error and roundoff remain uncertified and must not be merged into the analytic tail.

### G7. Twist-orbit partition and finite tails

For `a=.1,.7,2,7` and `tau/a=-.5,-.2,0,.37,.5`, compare the rational-hyperbolic `H_a` formula to its tanh difference and to `K_{a,b}(ell(u))` for `b=0,1,3`. For integers `N=0,1,4,12,50`, the symmetric partial sum equals exactly

`P_N(tau)=.5[tanh((tau+(N+.5)*a)/2)-tanh((tau-(N+.5)*a)/2)]`.

For `|tau|<=a/2`, its missing tail is nonnegative and at most
`2*cosh(tau)*exp(-(N+.5)*a)`. This follows from the exact identity
`1-P_N=1/(1+exp(tau+(N+.5)*a))+1/(1+exp((N+.5)*a-tau))`.
Check the exact finite formula first. Compute the tail using logistic expressions to avoid cancellation. Treat a numerical bound as an evaluated analytic expression, not an outward-rounded enclosure.

Include `u=100,1000` and L_N of at least 1000. Compute individual H terms using `2*sinh(a/2)*exp(-abs(u))/(1+2*cosh(a/2)*exp(-abs(u))+exp(-2*abs(u)))`; compute tail terms as `exp(-z)/(1+exp(-z))` for positive z. Tanh differences or `1-P_N` will round to zero in some of these cases; explicitly classify that loss of signal rather than accepting it as a relative check. Compare stable forms with relative/scaled acceptance and retain the positive tail itself even when the rounded partial sum is 1.

As an independent density example use the even uniform density on `[-1,1]`: its window mass is the length of `[u-a/2,u+a/2] intersect [-1,1]` divided by 2, and its lattice partition is a finite exact rational sum when `a,tau` are rational. Include endpoint contacts, where intervals overlap only on measure-zero endpoints. Do not assert pointwise positive terms for every arbitrary probability density; nonnegativity is the general property.

### G8. Matching positions is not matching directions

Use exact rational cuff circumference and endpoint lists to test one matching configuration and one inconsistent cyclic-spacing configuration. Keep the integer winding lift with each endpoint list. Separately use `S(x)=D_d(u,x)+D_e(x+tau,v)` and compare its numerical derivative to the sum of the two analytic endpoint derivatives. At `u=v=tau=0`, the stationary point `x=0` has orthogonal incoming/outgoing arcs. With a shifted endpoint, a position-matched `x=0` need not be stationary. This demonstrates the missing direction condition without claiming a general closed-curve reconstruction solver.

### G9. Cusp truncation, decoration, and ideal triangles

Construct `P=[[1,q],[0,1]]`, `c_A=(t_a+t_b)/q`, `A=[[t_a/2,((t_a/2)^2-1)/c_A],[c_A,t_a/2]]`, `B=A^{-1}P`. Exact rational choices `q=1,2,3`, `t_a,t_b=2,3,5` check `det A=det B=1`, `AB=P`, `tr A=t_a`, `tr B=-t_b`, `q*c_A=t_a+t_b`. Set `Y=q/H`; independently calculate the top of the image horocycle as `1/(c_A^2*Y)`, so its signed vertical separation is `log(c_A^2*Y^2)`. Compare with `2log((t_a+t_b)/H)`.

For torus traces `t=3,4,5,10` and `H=.1,1,6,20`, check `lambda=2t/H` and `1-sqrt(1-16 exp(-d)/H^2)=h(t)`. The `H=20,t=3` case supplies a strictly negative signed truncated length. Do not present nonembedded large decorations as embedded horocycles. Rescaling `H` by positive `k` changes `d` to `d-2log(k)` and leaves the weight invariant.

For ideal triangle lambda lengths `(u,v,w)=(1,1,1),(1,2,3),(2,3,5)`, exact rational arithmetic gives `H=2(u^2+v^2+w^2)/(uvw)` and associated traces `(Hu/2,Hv/2,Hw/2)`. Independently verify the Markov relation `x^2+y^2+z^2=xyz` and invariance of `H` under the flip `u'=(v^2+w^2)/u`. This checks decoration and trace algebra; it does not independently certify a complete torus representation.

### G10. Basmajian orientation factor

For `d>0`, take the boundary line `x=0` and the disjoint semicircle with center `coth(d)` and radius `csch(d)`. Its ideal endpoints are `tanh(d/2)` and `coth(d/2)`. Projecting perpendicularly to the first line gives a logarithmic shadow length `log(endpoint_high/endpoint_low)=2log(coth(d/2))`. Test this using independent circle endpoints for `d=.1,.7,2,8`. A segment counted in both directions supplies two such endpoint shadows, hence `4log(coth(d/2))` per unoriented arc. No finite collection is claimed to approximate a complete orthospectrum.

Also require `d=100,1000` to test tiny positive shadows. Use `q=exp(-d)`, `shadow=2*log1p(2*q/(1-q))`, and independently `z=2*q/(1+q*q)`, `shadow=log1p(z)-log1p(-z)` (twice atanh of the circle radius/center). Compare relative or scaled by `4*exp(-d)`. Direct coth/endpoint formulas can round to exactly 1 and hence shadow 0; this is a rejected route for the large-d fixtures, not an approximation that passes an absolute zero tolerance. Preserve analytic positivity and distinguish numerical evaluation from an interval enclosure.

## Explicit exclusions

No sampled value proves a surface identity, orbit enumeration, topological classification, cover extension, discrete holonomy, moduli fundamental domain, source theorem, general convexity theorem, or global reconstruction. No global figure-eight, dilogarithm, cusp-arc, or Basmajian spectrum is numerically summed. No maintained solver for arbitrary multicurve endpoint minimization is requested. The only infinite objects approximated numerically are the single kernel iteration and the single twist lattice, both with explicit analytic tails above; finite integrals carry their own analytic tails.
