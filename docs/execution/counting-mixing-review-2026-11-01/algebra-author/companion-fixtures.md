# Sections 23–25: finite companion specification

Author specification, 1 November 2026. Canonical extraction baseline: commit
`9c8b61790aaa674902b9d60e80122c318a578bcc`. This file requests exact finite
fixtures; it does not report execution of `experiments/counting_mixing` or
creation of `artifacts/counting_mixing/result.json`.

Use integer/rational polynomial arithmetic. The conventions are unnegated
SL(2) traces, unoriented primitive classes, `P_0=2`, `P_1=x`, and a multicurve
monomial whose total degree counts parallel copies. Distinct support count
is a different statistic.

## 1. Chebyshev and figure-eight coefficients

Labels: `eq:coeffChebyshev`, `eq:coeffsimplepowers`, `eq:coeffoddpowers`,
`eq:coeffpowergenerating`, `eq:coefffigurepowers`,
`eq:coefffigurecancellation`.

Generate `P_(k+1)=x P_k-P_(k-1)` independently of the factorial formula.
For each `1 <= k <= 12`, compare every coefficient against

```
[x^(k-2j)] P_k = (-1)^j k (k-j-1)! / (j! (k-2j)!)
```

The constant term is included in the polynomial check. For positive `m`,
compare the `q^k` coefficient of
`q^m(1-q^2)/(1+q^2)^(m+1)` with `[x^m]P_k`.
Known rows: `[x]P_(1,3,5,7) = (1,-3,5,-7)` and
`[x^2]P_(2,4,6,8) = (1,-4,9,-16)`.

Substitute `x y-z` into the recurrence-generated `P_k`. For `r+m >= 1`,
all monomials have equal powers of `x,y`, and

```
[x^r y^r z^m] P_k(xy-z)
 = (-1)^(j+m) k (k-j-1)! / (j! r! m!) if k=r+m+2j,
 = 0 otherwise.
```

The sum of the `xy` and `z` coefficients is zero for every positive `k`.
Also test cuff identification `y=x`: only after expanding and collecting
monomials may a coefficient be extracted. For instance
`P_2(x^2-z)=x^4-2x^2 z+z^2-2`.

These are trace identities. Assigning hyperbolic lengths to an arbitrary
matrix input is not part of the exact check. In particular, the minus sign
in `xy-z` is not the sign convention of the positive pants length formula.

## 2. Matrix identities and the fixed-linear-selector obstruction

Labels: `eq:coeffAdamsobstruction`, `eq:globalobstruction`,
`eq:globalobstructionbound`.

For exact SL(2) matrices `A,B`, put `x=tr A`, `y=tr B`, `z=tr(AB)` and
`k=x^2+y^2+z^2-xyz-2`. Direct word traces should equal

```
tr(A^2 B A^-1 B^-1) = x(k-1)
tr(A^3 B^2) = (x^2-1) y z - x y^2 - x^3 + 3x
tr(A^2 B A B) = x z^2-y z-x
```

Their first plus second minus third is `x`. A useful symbolic matrix
parametrization for an independent dense-chart identity check is
`A=diag(a,1/a)`, `B=[[b,c],[d,(1+cd)/b]]` with `a,b != 0`.
Finite integer matrix fixtures can instead use products of upper and lower
unipotent shears, with direct word multiplication and inversion.

With `u=tr(AB)` and `v=tr(AB^-1)`, check
`P_2(u)+P_2(v)-P_2(x)P_2(y)=2(tr[A,B]-2)`.
Include a noncommuting pair for which the right side is nonzero.
The finite polynomial checks do not establish that the words are primitive
nonsimple geodesics; that topological argument is in Section 25.

## 3. Global one-crossing weights

Labels: `eq:globalmoments`, `eq:globalweightseries`,
`eq:globalonecrossing`, `eq:globalfilteredheat`.

Build `S_0(v)=2`, `S_1(v)=1`, `S_n=S_(n-1)+v S_(n-2)`. Replace odd powers
of `v` by zero and `v^(2j)` by `binom(2j,j)` to obtain `w_n` exactly.
The expected values `w_0,...,w_12` are

```
2, 1, 1, 1, 5, 11, 19, 29, 53, 109, 221, 419, 779.
```

Compare them to the Taylor series of
`(2-q)/sqrt((1-q)^2-4q^4)` at zero. The branch is the one with square root
equal to one at zero. Define `Lambda(x^a y^b z^c)=w_(a+b+c)` on pants
multicurve monomials. Test `Lambda(P_k(xy-z))=0` for `1 <= k <= 12`, and
the same after identifying `y=x` and collecting terms. For a simple trace,
`Lambda(P_k(x))`, `k=1,...,12`, is

```
1, -3, -2, 5, 11, -6, -41, -11, 124, 127, -307, -646.
```

For the obstruction words from item 2, the values are `(-5,5,-1)`.
The first-atom normalization is `w_1=1`; the empty monomial has weight
`w_0=2`, not one. This is a linear functional on the multicurve basis,
not an algebra homomorphism or a common-trace representation evaluation.

## 4. Finite support selector and divisor inversion

Labels: `eq:countonesupport`, `eq:countsupportmobius`,
`eq:countsupportfourier`.

For any polynomial of degree at most `q-1`, the exact residue-class rule
`q^-1 sum_j omega^(-j) omega^(jn) = 1_(n=1)` recovers its linear
coefficient. Avoid floating roots of unity: use reduction modulo
`omega^q-1`, or exact integer exponent congruences. Include genus two
(`q=4`, maximum degree three) and a higher genus.

The finite divisor identity is `sum_(k|n) mu(k)=1_(n=1)`; there is no
`1/k`. Check it for each `1 <= n <= 60`. A synthetic disjoint-support
model may assign formal positive integer lengths to three named supports,
list all weighted multicurves below a cutoff, and compare distinct support
count with total multiplicity. Such a model is not an enumeration of all
simple curves on a hyperbolic surface and proves no counting asymptotic.

## 5. Length-valued finite Euler products

Labels: `eq:globalEuler`, `eq:globaldiagonal`, `eq:globalEulerinput`.

Use a finite polynomial convolution model with simple disjoint generators
`x,y,z` of integer formal lengths `A=2,B=3,C=4`, and one nonsimple
generator `xy-z` of length `G=7`. The formal lengths obey the inequalities
needed by this fixture (`G>A+B` and `G>C`); they are not claimed to be the
lengths of a common hyperbolic metric. Expand the four scalar geometric
series only through length 14. Enumerate the finite multisets separately
and compare coefficients by exact length.

For each target `x^r y^s z^m` whose diagonal length `2r+3s+4m <= 14`, its
first coefficient atom must be at that length with mass one. In particular,
the `xy` coefficient begins with `delta_5+delta_7`, and the `z` coefficient
with `delta_4-delta_7`. The empty coefficient is exactly `delta_0` in this
four-generator fixture. Later masses can cancel when formal lengths
coincide; accumulate by length before taking support.

Independently expand the finite convolution logarithm through the same
cutoff and compare it to `sum_delta sum_m T_delta^m delta_(m L_delta)/m`.
The summand is an ordinary tensor character power. At `m=2`, replacing it
by `P_2(T_delta)=T_delta^2-2` is a deliberately wrong alternative and must
fail. Include the coincident-length information-loss example: traces
`(x,y)` and their common sum do not determine `x^2+y^2` through an ordinary
linear operation on that sum.

No finite truncation verifies the infinite Euler-product half-plane,
unit-diagonal theorem for all geometric multicurves, spectral recovery,
or sharp counting error.

## 6. Optional numerical illustrations

Labels: `eq:countpantsgap`, `eq:countactiongap`,
`eq:countuniformconstants`, `eq:countcertifiedtime`.

If included, evaluate the displayed elementary functions at declared
precision and chosen positive parameters, keeping these records separate
from exact algebra. Compare `L=2 acosh(cosh(R/2)+2A)` to
`R+8A exp(-R/2)` for increasing `R`, and check positivity/decrease of the
explicit action gap. These are function-value checks, not certification
of systoles, diameters, complete orbit lists, or global estimates.
