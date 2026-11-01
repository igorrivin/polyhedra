# Independent Section 15 quantum evaluator review

Date: 2026-11-01. Reviewer: `airy_code_review`.
Repository baseline: `3ddf610dbe4578c7828e55f4e9cd92aacaba6df6`.

**Decision: approve the corrected evaluator source and the bounded numerical
evidence described here.** The final source passed independent targeted
acceptance, 26 focused tests, Ruff, and a fresh smoke run from `/private/tmp`.
All seven parameter points also passed a separately written whole-integral
reference comparison, with maximum observed difference `1.80e-12`.
`approved-hashes.json` binds this decision to the four exact source files.

The completed 21-setting matrix remains an author computation under its
original, pre-repair hashes. The corrected-source acceptance and smoke runs
are separate evidence. A later clean-source full replay and canonical result
must retain their own identity and pass the supplied strict comparison;
they are not being claimed as completed by this review. The reviewer edited
only this outer `computation-review/` directory.

## Scope and evidence boundaries

This review concerns the exact cleared regular-family Barnes/double-sine
integral, its controlled finite logarithmic approximation, and its numerical
evaluation. It does not turn finite computations into the analytic uniform
Airy theorem, an interval enclosure, or a verified number of achieved digits.
The separately approved analytic report is
`../math-review/analytic-review.md`; its analytic source hashes were
`2688ef6862492f93cd49de4c50017eb33496ad0d1b77cd8f4220150910a2ef1e`
for the chapter and
`8d5ba46372dda6a108bf913e30b661f87e16b4985b444ed8107d9feefb4c6c3d`
for the ledger. Later numerical text needs its own delta review.

The historical `experiments/section15/` companion and table, and
`artifacts/section15/checks.json`, are not new evaluations of the quantum
integral. They were treated as read-only evidence with their prior status.
Historical rounded values were comparison inputs, not acceptance targets.

The following claims remain distinct:

1. The finite D-series remainder formula is an exact rational upper bound,
   conditional on the exact centered-strip hypotheses and exact arithmetic.
2. Floating-point strip checks and transcendental evaluations are not certified
   by that rational calculation.
3. `expm1(B)` transfers a logarithmic truncation bound B to an integrand bound;
   multiplying it by a numerical absolute-integral estimate gives an estimate,
   not a rigorous integral enclosure.
4. Quadrature internal errors, tail formula evaluations, observed agreement
   across settings, and reference calculations are finite numerical evidence.
5. The global asymptotic theorem is a separate analytic argument.

## Mathematical and code findings

The implementation has the correct five centered arguments. Starting from
`x=(w-3alpha,4alpha-w,2Q-w,3alpha-b,alpha)` and applying `z=bx-b²/2`
gives exactly the implemented shifts `(-1/2,-1/2,3/2,-3/2,-1/2)b²`.
The weights are `(4,3,1,2,-6)`, with absolute sum 16. The upward Jacobian
and the normalization give `2/(9pi) integral_R F(t)dt`; conjugation gives
the implemented `4/(9pi) integral_0^infinity Re F(t)dt`. Airy functions
are used only for the post-quadrature comparison column.

Both principal dilogarithm arguments avoid `[1,infinity)` on `0<Re z<1`.
The pair is holomorphic there, vanishes at 1/2, and has derivative
`-pi log(2 sin(pi z))` with the real-strip branch. This fixes the constant
and branch, rather than inferring them from numerical agreement. Four
additional derivative/reflection probes, including imaginary parts +/-3,
had residuals at most `4.3e-50` at 50 dps. These probes are checks of the
implementation, not the justification of holomorphy.

The independently inspected [DLMF 4.36.5](https://dlmf.nist.gov/4.36.E5)
gives the csch partial fractions. Finite geometric expansion yields the
stated coefficients and remainder for every positive real u, without a
small-u convergence restriction. Bounding the complex sinh by the cosh of
its real part and integrating the positive exponential expansion of
`1/sinh(s)` gives the Hurwitz-zeta remainder with exactly the stated powers
of 2, pi, b, and `(2K)!`. Substitution of `pi>3`, `zeta(2K+2)<2`, and the
integral-test Hurwitz bound gives the implemented rational expression.
`independent_algebra.py` independently checks the csch coefficients and
cot derivative polynomials through K=8 and records exact bound substitutions
at K=1,2,15,22. A separate import-based audit confirms production agreement.

The full direct log-S check uses the convergent subtraction, not the printed
factor-of-two typo in TV Appendix A.1. After `u=2bs`, its removable limit is
`a(a²-1-b⁴)/(12b²)`, `a=1-2z`. The algebraic tail from s=16 is exactly
`-a/(32b²)`. Both constants were derived independently with SymPy. Splitting
off this tail is necessary: an unmodified improper quadrature of the
algebraic subtraction had previously been misleading. The D integral's
origin limit `-ab²/12` is also correct.

The tail test correctly uses centered, shifted real angles. Its three
numerator coefficients are exactly the coefficients of the common-denominator
expression for Psi prime. Positive coefficients imply monotonicity for
nonnegative r. The derivative of the leading logarithm is
`-lambda Psi/(3h)`, so integration of the exponential envelope gives the
implemented factor `3h/(lambda Psi)` and the two-sided normalization.
The centered shifts also give the correct far-tail slope. The real-D
majorant follows from `0<=1/u-csch(u)<=u/6` and the cotangent integral.
The inequality can be proved by coefficient comparison with
`sinh(u)<=u/(1-u²/6)` for `u<sqrt(6)`, with the remaining range immediate.
No sign or bound is certified by its floating-point evaluation in this code.

Additional checks at nine parameter/cutoff combinations differentiate the
leading logarithm numerically and compare the independent slope formula;
the largest residual is `4.2e-48` at 50 dps. Twenty-five real-D probes stay
below the stated real-part majorant, with maximum observed ratio
`0.999999978524599953...`. Their finite sample is explicitly not a proof
of the global bound.

## Defects identified and repaired

1. An accepted odd cutoff can put the advertised shorter cutoff inside an
   unsplit panel. For example T=5 gives panels `(0,2,4,5)` and split=3;
   the recorded shorter integral and extension omit `[2,4]`. The author
   reproduced a `-0.0026948522550` accounting residual at C=2, 30 dps.
   The repair inserts the split into the panel endpoints.
   The full matrix's T=12 and T=14 settings are unaffected.
2. `check.py` used an executable `assert` for the cot-polynomial check,
   which disappears under `python -O`. It now uses an explicit failure.
3. Absolute-script invocation works from arbitrary directories, but the
   initial sibling import failed in package-import mode. Both modes now
   work, and quiet import from another working directory is tested.
4. The initial source gate compares only the first five declared hashes.
   It now rejects drift in every declared scientific source and HEAD.
5. The README's statement about recording the "last two panels" is inaccurate;
   each canonical setting records the final two-unit extension panel. The
   README now states the actual shorter cutoffs and recorded contribution.

None of these discoveries permits relabeling the pre-repair computation as
a run of repaired code. Any quantum-row-affecting change requires new full
numerical evidence. New independent D-method diagnostics are also fresh
checks and must retain their actual execution and source identity.

Initial failure-path checks reject NaN/infinite parameter strings, zero b,
out-of-strip contour/transition parameters, and nonfinite serialized floats
and complex values. Exact rational bounds fail closed when their target
cannot be reached. Result serialization disallows NaN, and output creation
uses exclusive mode. Final acceptance injected drift independently into
HEAD and each of the seven declared source hashes, and all eight cases
were rejected. Existing-output and missing-parent rejection occurs before
computation; the existing bytes were preserved. An injected nonfinite
quadrature result was rejected. An optimized-Python subprocess with a
deliberately corrupted cot-polynomial provider still failed explicitly.

The real odd-cutoff replay at C=2,T=5,30 dps now uses `(0,2,3,4,5)`.
Its shorter integral plus extension differs from the full value by only
`2.39e-32`. Independently evaluating both the full and shorter integrals
with the combined Barnes reference gives observed discrepancies of
`3.50e-13`, so this test checks the actual shorter integral as well as
the bookkeeping identity.

The final direct-D crosscheck adds tanh-sinh quadrature on a different
panel layout and a separate exact rational tail majorant. The bound
`b²/(6 epsilon) * 2^(-floor(2 epsilon L))` follows from
`b² exp(-2 epsilon L)/(12 epsilon (1-exp(-2L)))` for L>=1, then `e>2`.
For epsilon=1/50 and L=8192 it is about `4.76e-102`. The final record
explicitly says its numerical integral is over `[0,infinity)` and the
bound concerns an included tail; it is not an omitted-tail error estimate.
This avoids attributing finite-cutoff semantics to an infinite quadrature.

The preserved development record `../computation/direct-D-refinement.json`
contains a 60-dps alternate Gauss-Legendre result whose difference from the
bounded series is about `2.3e-46`, while its internal estimate is about
`1e-66`. The alternate tanh-sinh result agrees near `1e-63`; the two alternate
methods at 80 dps agree near `1e-84`. The original layout at 80 dps still
has an observed discrepancy around `1.5e-69`, also larger than its estimate.
The failed diagnostic was preserved, not hidden by reporting only a pass.
It directly illustrates why internal quadrature errors cannot be promoted
to a total certificate.

## Independent whole-integral calculation

`independent_reference.py` imports no author evaluator. It starts with the
original Barnes variables and combines the convergent full log-S integrals.
The exact weighted identity `sum_j weight_j a_j=4b²` makes the combined
algebraic subtraction `-2/s²`. On `(0,1)` it evaluates an independently
formed 21-term Taylor cancellation series; on `(1,infinity)` it uses stable
exponentials and integrates the subtraction analytically as `-2`.
It uses no dilogarithm, cot-polynomial D expansion, or Airy value.

SciPy 1.18.1 QUADPACK computes both the inner integrals and the outer real
integral on unit panels, unlike the author's mpmath Gauss-Legendre outer
quadrature on two-unit panels. mpmath 1.3.0 supplies 45-dps parameters and
Taylor coefficients, so this is independent formula/algorithm evidence,
not wholly independent arithmetic infrastructure. Current SciPy API
documentation was fetched using Context7 from the official repository.

The preliminary four-point cost probe took 0.022 seconds, so the complete
reference was feasible. The first whole-Q comparison at b=1/80,zeta=0,T=8
gave `0.45908648873519403` at C=1 and `0.45908648873566593` at C=5/4;
these differ from the author's first-row value by less than `9e-13`.
Whole-log differences at t=0,1,3,8 are between `1.9e-12` and `2.2e-12`.
The independent calculation therefore supports the first historical
rounding discrepancy. No historical value was used to tune the reference.

The reference was then run for all six historical inputs and the negative
continuation input. Its values are recorded in
`independent-whole-q-matrix.json`. The comparison with the completed 90-dps
author results is `independent-matrix-comparison.json`; all seven pass the
explicit `1e-10` comparison threshold, with maximum observed discrepancy
`1.7975819422e-12`. The 21-setting author matrix completed in about 427
seconds, with identical start/finish source snapshots. Its seven 60/90-dps
differences are below `4e-57` and contour/order differences below `1.3e-91`.
Those are observed agreements, not achieved-digit guarantees.

The new first value is `0.459086488736078952...`, whose nearest-six-decimal
rounding is `0.459086`. Its difference from the historical `0.459087` is
`-5.11263921048e-7`, just outside the nearest-rounding tolerance. The other
five historical entries agree after rounding; their original rounding
procedure and evaluator remain unknown. The negative input gives
`Q_(1/160)(-1)=0.517966671856531011...`.

The inner QUADPACK estimates range from roughly `1.1e-8` to `1.8e-7` in
the full logarithm. Its outer-only error estimates are around `1e-14` or
smaller, but do not include inner error. No integration warnings occurred.
The Taylor cancellation series and finite cutoff are unvalidated numerical
operations. Thus neither the outer error estimate nor observed agreement
is a true error enclosure for Q. The source tail formula at T=8 gives
`2.18e-44` for the first reference point, also without outward rounding.

## Commands and records

The supported pre-existing interpreter is
`/tmp/polyhedra-baseline-20261031/bin/python` (Python 3.12.11), with
mpmath 1.3.0, SymPy 1.14.0, SciPy 1.18.1, and NumPy 2.5.4. No packages
were installed. The initial focused suite passed 12 tests. The final suite
passed all 26 tests in 1.27 seconds, and Ruff passed both the production
companion and this review's four Python scripts.

Executed from the review directory:

```sh
/tmp/polyhedra-baseline-20261031/bin/python independent_reference.py --output reference-cost-probe.json
/tmp/polyhedra-baseline-20261031/bin/python independent_reference.py --whole --output independent-whole-q.json
/tmp/polyhedra-baseline-20261031/bin/python independent_algebra.py
PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-baseline-20261031/bin/python review_acceptance.py --output final-source-acceptance.json
```

From `/private/tmp`, the reviewer also ran:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-baseline-20261031/bin/python -u /Volumes/Lexar/lambda/devel/polyhedra/consolidated/experiments/section15_quantum/check.py --profile smoke --output /Volumes/Lexar/lambda/devel/polyhedra/execution/section15-analytic-review-2026-11-01/computation-review/final-source-smoke.json
```

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-baseline-20261031/bin/python -m pytest experiments/section15_quantum/test_evaluate.py -q
/opt/anaconda3/bin/ruff check experiments/section15_quantum
```

The targeted runner passed 13 contract checks and all 28 direct special-function
checks at each of 40 and 60 dps. The separate smoke run passed 28 direct
checks at 30 dps and recomputed the first whole-Q value at 40 dps as
`0.459086488736078952059515...`. Both runs retained identical declared source
hashes and HEAD from start to finish. The numerical chapter hash was
`efee2c699923ab31e4d7d48eeac57c60bf2ea088ea4ff17e617b9ed97202d6dd`.

The seven-row reference calls `whole_q(b=...,zeta=...)` for b in
`(1/80,1/160,1/320)` and zeta in `(0,1)`, then `(1/160,-1)`, with C=1,T=8.
The exact script and SHA-256 are retained; this calculation is inexpensive.

Additional records:

- `independent-algebra-result.json`: exact finite identities and rational bounds.
- `initial-source-audit.json`: malformed/nonfinite inputs, branch probes,
  production comparisons with independently generated algebra, and log references.
- `tail-and-real-part-probes.json`: derivative/tail and real-part diagnostic probes.
- `independent-whole-q.json`: complete reference at two contours for the first row.
- `independent-whole-q-matrix.json`: complete reference at all seven inputs.
- `independent-matrix-comparison.json`: seven comparisons with the original
  author matrix, with both artifact/source identities retained.
- `final-source-acceptance.json`: final 13 contract and 28x2 special-function
  checks, plus the real odd-cutoff result and its independent references.
- `final-source-smoke.json`: fresh final-source script invocation from another CWD.
- `validation-commands.json`: actual final test/lint command outcomes.
- `approved-hashes.json`: precise bounded approval and evidence manifest.

## Later clean-source full replay

`compare_full_runs.py` is supplied for the later clean-source replay. It
requires all 21 scientific row objects to be exactly equal after removing
only `rows[*].elapsed_seconds`, and all seven comparison objects to be
exactly equal. It compares each of the 27 shared special-function records
by name with no record-field exclusions, then separately validates the
28th tanh-sinh/tail-metadata record at both precisions. The only component
container field omitted is `independent_double_sine_checks[*].elapsed_seconds`.
It also checks runtime, sources, limitations, existing conventions, clean
and stable candidate HEAD/source snapshots, and the approved source hashes.
The changed run time, creation time, source identity, and added quadrature
convention are explicitly recorded. No such later artifact was evaluated
when issuing this source/evidence approval.
