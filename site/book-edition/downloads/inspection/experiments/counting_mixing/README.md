# Finite counting and mixing formula companion

This companion checks bounded algebra and explicit numerical formulas associated
with Sections 23–31. It is separate from the torus spectrum campaign and from the
preserved `experiments/section30` evidence. It does not establish a global counting
theorem, an asymptotic rate, geometric model hypotheses, or an interval enclosure.

Run from the repository root with Python 3.12 and the existing mpmath 1.3 environment:

```sh
python experiments/counting_mixing/run.py --output /tmp/counting-mixing-result.json
python -m unittest discover -s experiments/counting_mixing/tests -v
ruff check experiments/counting_mixing
```

No installation or network access occurs. The output parent directory must exist,
and the output must be a new path outside this source directory. External evidence
paths and `artifacts/counting_mixing/result.json` are both supported; the latter is
reserved for the integration checkpoint's clean-source replay. Existing files and
symlinks are refused. Imports have no computation or write side effects. The driver
also works when invoked by absolute path from a different working directory.

`fixture.json` pins the mathematical formula/label contract, the author specification
hashes, all ranges, rational inputs, precision settings, and conventions. The pinned
author files are not runtime dependencies. Each run records the actual Git HEAD,
whole-checkout dirty status before and after, Python executable/version, mpmath
version, source file hashes, and an aggregate source-set hash. The source set covers
the companion's code, tests, README, and input data. It deliberately makes no claim
that concurrently revised manuscript files are frozen. Any companion source/input
hash or HEAD change between the snapshots aborts successful output. Changes in
other working-tree files are recorded rather than mislabeled as companion drift.

The output reports check counts per group, exact values, numerical residuals,
cross-precision differences, and limitations. Author execution is not independent
review or approval. Tests target signs, normalizations, multiplicities, endpoint
conventions, malformed inputs, nonfinite values, overwrites, and source drift.

The exact groups use Python integers and `Fraction`:

- Trace recurrences through power 12 are compared with factorial coefficients and
  rational generating-series coefficients. Figure-eight traces use `xy-z` with
  unnegated SL(2) traces. Identification `y=x` happens before coefficient extraction.
  Four rational SL(2) fixtures compare direct word products and trace formulas,
  including a nonzero Adams-operation obstruction and a commuting control.
- Global weights use both the moment recurrence and an independent binomial
  expansion of `(2-q)/sqrt((1-q)^2-4q^4)`, on the branch equal to one at zero.
  The empty monomial has weight two. Weight indices count total multiplicity,
  including identified cuffs, and are not a representation evaluation.
- The finite support selector uses exact exponent congruences for genus two and
  three. Möbius divisors through 60 use `sum mu(d)`, without a `1/d` factor. A formal
  disjoint-support model keeps support count distinct from parallel-copy count.
- The finite Euler product uses formal lengths `(2,3,4,7)` for `(x,y,z,xy-z)`
  through length 14. Polynomial convolution is compared with explicit multiset
  and binomial enumeration. Equal lengths are accumulated before support is read.
  A convolution logarithm is checked against ordinary tensor powers `T^m/m`;
  replacing them with Chebyshev/Adams powers is a deliberately failing alternative.
  These lengths are not asserted to arise from a common hyperbolic metric.
- Scalar path counts, closed traces, and stationary correlations are compared for
  the periodic two-state examples at `m=2,3,5`, `n=1,...,32`. An aperiodic matrix
  separately checks its trace gap and exact rank-one projection formula.
  The terminal-differentiation identity is checked in the exact algebra of formal
  exponentials, including the removable zero-rate case, before quadrature.
- For `2<=c<=31`, rational Bruhat multiplication and exhaustive inverse-residue
  enumeration preserve multiplicities. Endpoint characters are encoded as
  polynomials modulo `z^c-1`. The adaptive frequencies `m=n=c` give statistic one
  with zero continuous means; their growing smooth norms remain part of the scope.
- Primitive vectors in three specified rational unimodular lattices are searched
  at four radii. The search is complete for these finite ellipses because
  `|m_i| <= R*sum_j |(g^-1)_ij|`; the integer coordinate bounds are retained.
  Every boundary comparison is rational. All three nonzero parity classes, sign
  pairs, determinant integrality, and two Gamma(2) basis changes are checked.
  The stronger rational bound `count<=2+6R^2`, verified for these fixtures, implies
  the displayed `2+2*pi*R^2` bound using `pi>3`. This does not construct an arc lift.
- Gaussian rotation-norm coefficients and finite relative-mark Fourier
  orthogonality are exact checks. Increasing rational collinear sums in four boxes
  illustrate the rank-one issue; finite increase does not prove divergence or
  justify treating a truncated raw product as an L2 observable.
- Square and rational-diamond gauges check finite Möbius inversion and the
  Mertens-tail identity, including zero summands at the cutoff boundary. Finite
  dyadic telescopes are checked for polynomial and supplied-list counts. Rational
  event sweeps retain multiplicities, aggregate every simultaneous jump, exclude
  the external left limit at `T`, and include both the left limit and actual value
  at `2T`. They are compared with direct endpoint and interval-midpoint counts.
  For `[2,2,4,5,8]` on `[2,4]`, the exact outputs are `M=5/2`, `Q^2=49/20`.
  Signed primitive multiples, gcd row selectors with negative/zero endpoints,
  and the three conditional balance exponents are checked separately.

Numerical groups run at 60 and 90 decimal digits, each in its own cloned mpmath
context. Rank-two signals are strictly positive and use the relative residual
`|actual-expected|/expected` with tolerance `10^(-(dps-15))`. Positivity is checked
before comparison. Any analytic-tail allowance must also fit that relative
tolerance budget; it is recorded separately and never used to conceal a loose
quadrature. The other families retain
`10^(-(dps-15))*max(1,|actual|,|expected|)`, including genuine zero values.
Rank-two cross-precision checks use `|low-high|/high` with both values positive;
they cover all three covariance series forms and both scaled and unscaled radial
integrals. Formula comparisons use the same arithmetic backend; they are not
independent software or interval proofs.

For `f_ab=exp(-pi*(a*x^2+b*y^2))`, one-dimensional product quadrature checks the
mass norm, rotation-derivative norm, and flow covariance at three rational pairs
and four times. The flow is `a_t=diag(exp(t),exp(-t))`, so the covariance is
`1/(2*sqrt(ab)*cosh(t))`. Integrals are truncated at the scaled coordinate
`U=floor(dps/3)`. For an integrand `x^p exp(-pi*A*x^2)` on the line, the omitted
tails at `B=U/sqrt(pi*A)` are bounded analytically by
`exp(-U^2)/(U*sqrt(pi*A))` for `p=0`, and
`exp(-U^2)*(U+1/(2U))/(pi*A)^(3/2)` for `p=2`. Product-tail bounds are reported
separately from quadrature residuals. No bound on the quadrature error is claimed.

The rank-two covariance uses 24 terms and compares the divisor series, logarithm
series, and both signs of the determinant-orbit sum. Logarithms are evaluated as
`log1p(-q^n)` to retain small positive signals without subtraction from one.
For determinants 1, 2, 3,
radial quadrature independently checks the orbit formula after analytic integration
of the real shear coordinate. The Haar factor is
`2*pi*sqrt(pi/alpha)/(k*zeta(2))`, and the radial integrand is
`exp(-alpha*(r^2+k^2/r^2))`. Before quadrature its tiny amplitude
`exp(-2*alpha*k)` is factored out, leaving the peak-normalized integrand
`exp(-alpha*(r-k/r)^2)`. Both scaled and unscaled values and analytic tails are
retained and checked relatively. The radial cutoff is
`B=U/sqrt(alpha)`, `U=max(18,floor(dps/3))`. Its scaled omitted upper tail is at most
`exp(2*alpha*k-alpha*B^2)/(2*alpha*B)` before the Haar factor; restoring the
amplitude gives the unscaled tail bound. With
`q=exp(-4*pi*cosh(t))`, the two analytic series tails after `N` are at most
`q^(N+1)*((N+1)-N*q)/(1-q)^2` and
`q^(N+1)/((1-q)*(1-q^(N+1)))`, respectively, before the covariance prefactor.
These are analytic truncation statements whose floating evaluations do not
enclose roundoff or quadrature error. The time-zero value is the squared norm.
Regressions specifically reject zero, sign, half, and double mutants of the tiny
`t=2,k=3` integral and of every positive rank-two cross-precision observation.

Finite endpoint exponential products are compared with the residue-character
form, and three exponential families test terminal differentiation, including
the removable case `r=h`. Optional rectangle clipping, gap-function illustrations,
and plots are omitted. No arbitrary affine-quotient mixing, nonsquare-stratum
classification, geometric counting rate, full torus enumeration, recovery of
historical raw data, or spectral sensitivity enclosure is attempted.
