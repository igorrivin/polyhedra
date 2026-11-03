# Exact Section 15 quantum-integral companion

This independent companion evaluates the **cleared Barnes/double-sine
integral** of Section 15. It does not replace the integrand by an Airy
approximation. The historical values in `../section15/historical-table.json`
are read-only comparison inputs; their rounding convention is unknown.

The supported environment used for development is Python 3.12.11 with
mpmath 1.3.0. No installation, optional acceleration, or python-flint is
required. Run from any directory, with a new output path whose parent exists:

```sh
/tmp/polyhedra-baseline-20261031/bin/python /Volumes/Lexar/lambda/devel/polyhedra/consolidated/experiments/section15_quantum/check.py --profile full --output /absolute/new/result.json
```

`smoke` runs the independent checks at 30 decimal digits and the first
historical row at 40 digits. `full` checks the double sine at 40 and 60 digits,
then evaluates all six historical rows and one negative-zeta continuation
point (`b=1/160, zeta=-1`) under three settings: 60 digits, `C=1,T=12`;
90 digits, `C=1,T=14`; and 90 digits, `C=5/4,T=14` with two extra D terms.
The contribution beyond the shorter cutoff (10 for `T=12`, 12 for `T=14`)
is separately recorded, so the cutoff comparison does
not subtract rounded totals. The command refuses to overwrite an output and
does not write a successful result until all declared checks pass. Any change
to HEAD or a declared scientific source, including either chapter, between
the initial and final snapshots fails the run. Final manuscript edits must
occur outside a frozen computation run. The module can also be imported
without launching computation, including by its package name.

## Integrand, contour, and normalization

Let `h=2*pi*b^2`, `lambda=h^(1/3)`, `eta_E=acos(1/3)`, and
`eta=eta_E-lambda^2*zeta/(6*sqrt(2))`. Set `alpha=(pi-eta)/(2*pi*b)`
and `Q_Barnes=b+1/b`. The exact cleared integrand is

```text
F(w) = S_b(w-3*alpha)^4 S_b(4*alpha-w)^3 S_b(2*Q_Barnes-w)
       S_b(3*alpha-b)^2 / S_b(alpha)^6.
```

The upward contour is `v=2*pi*b*w=4*pi-5*eta_E+lambda*(C+i*t)/3`,
`C>0`. With the explicitly specified measure `dw/i`, the normalized value is
`Q_b=2/(9*pi) integral_R F(t) dt = 4/(9*pi) integral_0^infinity Re F(t) dt`.
The five centered arguments `x=z/b+b/2` are

```text
z1=(v-3*pi+3*eta)/(2*pi)-b^2/2       weight  4
z2=(4*pi-4*eta-v)/(2*pi)-b^2/2       weight  3
z3=(4*pi-v)/(2*pi)+3*b^2/2          weight  1
z4=3*(pi-eta)/(2*pi)-3*b^2/2        weight  2
z5=(pi-eta)/(2*pi)-b^2/2            weight -6.
```

Every real part is checked against `[epsilon,1-epsilon]`, `epsilon=1/100`.
This centered strip is narrower than the fundamental strip of the original
double-sine argument. All log factors are combined before exponentiation.

On `0<Re z<1`, use

```text
Lambda(pi*z) = (Li_2(exp(2*pi*i*z))-Li_2(exp(-2*pi*i*z)))/(4*i),
log S_b(z/b+b/2) = -Lambda(pi*z)/(pi*b^2)+D_b(z),
D_b(z) = (1/2) integral_0^infinity sinh((1-2*z)*s)/(s*sinh(s))
                       * (csch(b^2*s)-1/(b^2*s)) ds.
```

Both dilogarithms use their principal branches. Their arguments avoid the
cut in the open strip, the difference vanishes at `z=1/2`, and its derivative
is `-pi*log(2*sin(pi*z))` with the logarithm real on the real strip.

The starting Barnes formula is [Teschner--Vartanov v3, equation 2.27 and
Appendix A](https://arxiv.org/abs/1202.4698v3). Appendix A.1 prints a linear
subtraction twice the convergent coefficient. Subtracting the two convergent
double-Gamma integrals instead gives

```text
log S_b(x) = integral_0^infinity [
  sinh((Q_Barnes-2*x)*t/2)/(2*sinh(b*t/2)*sinh(t/(2*b)))
  -(Q_Barnes-2*x)/t ] dt/t.
```

The `direct_log_sine` check evaluates this entire convergent real integral,
after `t=2*b*s`, independently of the dilogarithm and cot-polynomial formulas.
It integrates the explicit algebraic subtraction tail analytically; only
the exponentially decaying remaining tail is sent to infinite quadrature.

## Controlled correction series

[DLMF 4.36.5](https://dlmf.nist.gov/4.36.E5) gives the csch partial fractions.
Finite geometric expansion yields

```text
csch(u)-1/u = sum_(k=1)^K a_k u^(2*k-1) + R_K(u),
a_k = 2*(-1)^k*(1-2^(1-2*k))*zeta(2*k)/pi^(2*k),
|R_K(u)| <= 2*zeta(2*K+2)*u^(2*K+1)/pi^(2*K+2),  u>0.
```

Let `P_0(c)=c`, `P_(n+1)(c)=-(1+c^2)*P_n'(c)`. The finite correction is

```text
D_K(z) = sum_(k=1)^K a_k*b^(4*k-2)*pi^(2*k-1)
                         *P_(2*k-2)(cot(pi*z))/2^(2*k).
```

In particular its first term is `-pi*b^2*cot(pi*z)/24`.
For `a=Re z` in the strip, the absolute remainder is at most

```text
b^(4*K+2)*zeta(2*K+2)/pi^(2*K+2) * (2*K)!/2^(2*K+1)
  * [HurwitzZeta(2*K+1,a)+HurwitzZeta(2*K+1,1-a)].
```

This follows by bounding the complex sinh by `cosh((1-2*a)*s)` and
integrating the positive geometric expansion of `1/sinh(s)`. The code uses
the coarser **exact rational** bound obtained from `pi>3`, `zeta(2*K+2)<2`,
and `HurwitzZeta(p,a)<=epsilon^(-p)+epsilon^(1-p)/(p-1)`. It multiplies by
the sum of absolute weights, 16, for the full logarithm and chooses K until
the bound is below `10^(-working_dps-5)`. The bound is global in `Im z`.
It controls series truncation only; strip membership and floating-point
evaluation are not certified by this rational calculation.

Independent checks compare `D_K` with direct real-integral quadrature at
all five arguments, compare full `log S_b` with its direct integral at two
complex arguments, and check reflection, the `b` shift equation, the
Lobachevsky derivative, the original-to-centered coordinate mapping,
conjugation, and addition of two D terms.
The nearest-strip complex argument is also checked with tanh-sinh quadrature
on a different panel layout. For `L>=1`, the direct D integral's tail has the
separate exact rational majorant
`b^2/(6*epsilon) * 2^(-floor(2*epsilon*L))`. This follows by first bounding
it by `b^2*exp(-2*epsilon*L)/(12*epsilon*(1-exp(-2*L)))`, then using `e>2`.
The recorded cross-method check uses `epsilon=1/50,L=8192`; this bound covers
only the tail, conditional on the numerically checked strip hypothesis.
The direct quadrature still integrates over `[0,infinity)`, including this
tail. The bound is a separate component diagnostic, not an omitted-tail error.

## Outer tails and evidence boundaries

For the three centered real angles `Theta_j=pi*Re(z_j)`, put
`c_j=cot(Theta_j)` and `r=tanh(y/2)`. The negative derivative of the real
leading phase along the vertical line is
`Psi(r)=4*atan(c_1*r)+3*atan(c_2*r)+atan(c_3*r)`.
Its derivative has denominator `product_j(1+c_j^2*r^2)`; the code records
and checks positivity of each coefficient of the numerator in `r^2`.
For positive coefficients, `Psi` increases. Also
`|Re D_b(z)|<=pi*b^2*|cot(pi*Re(z))|/24` follows from
`|csch(u)-1/u|<=u/6`. At `y=lambda*T/3`, these facts give the normalized
two-sided tail majorant formula

```text
4/(9*pi) * 3*h/(lambda*Psi(tanh(lambda*T/6)))
  * exp(Re(leading_log(T))
        +pi*b^2/24*sum_j |weight_j|*|cot(pi*Re(z_j))|).
```

Its numerical evaluation and numerator-sign checks use ordinary mpmath
arithmetic **without outward rounding**. They are diagnostic estimates.
The propagated D error uses a numerical absolute-integral estimate, and
mpmath's quadrature errors are internal heuristic estimates. No combined
interval enclosure or rigorous achieved-digit claim is made.

The output records parameters as strings, precision, contour and panels,
all residuals, exact rational D bounds, separate numerical error components,
cutoff/precision/contour comparisons, source hashes at start and finish,
commit and dirty status, runtime versions, timing, and historical residuals.
The Airy expression is calculated only after quadrature for comparison.
Agreement here is finite numerical evidence, separate from the global
asymptotic theorem and its mathematical review.

During development, a changed Gauss-Legendre panel layout at 60 digits
underestimated its actual direct-D quadrature error: a residual around
`2.3e-46` accompanied an internal estimate around `1e-66`. The original
refined layout and the alternate tanh-sinh method agreed with the bounded
series to approximately `1e-63`; both methods at 80 digits agreed to
approximately `1e-84`. The outer execution records preserve this failed
diagnostic. These observations motivate the cross-method check and the
explicitly uncertified error status.

Focused checks (no full toolkit suite):

```sh
/tmp/polyhedra-baseline-20261031/bin/python -m pytest /Volumes/Lexar/lambda/devel/polyhedra/consolidated/experiments/section15_quantum/test_evaluate.py -q
/opt/anaconda3/bin/ruff check /Volumes/Lexar/lambda/devel/polyhedra/consolidated/experiments/section15_quantum
```
