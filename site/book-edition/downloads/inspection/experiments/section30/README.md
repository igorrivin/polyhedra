# Section 30 bounded torus diagnostic

This is a new, reproducible experiment through hyperbolic length **64** for
the two trace triples in `eq:diagnostictracetriples`. It does not recreate
the missing length-8192 archive or validate its printed counts, selected
rows, precision claims, or sensitivity tables. Those historical values
remain explicitly unreplayed in the [chapter](../../book/chapters/30-sharp-diagnostics.tex).

The driver needs only the Python standard library. From the repository root,
using the supported Python environment, run:

```sh
python experiments/section30/run.py --output /tmp/section30-result.json
python -m unittest discover -s experiments/section30/tests -v
```

The output path must not exist; earlier evidence is never overwritten.
The result records the exact fixture, source hashes, Git commit and dirty
state, Python/platform, run time, complete slope/trace/length data, metrics,
and measured residuals. The curated result is
[`artifacts/section30/result.json`](../../artifacts/section30/result.json).
It is generated separately from the reviewed source commit. The initial
author-run evidence is retained in the revision checkpoint; a dirty author
run is not a clean-source replay.

## Curve and trace conventions

A curve is a primitive integer pair `(p,q)` modulo simultaneous sign.
The representative has `q>0`, except for the single root `(1,0)`.
Roots `(1,0)`, `(0,1)`, `(1,1)` receive the ordered input traces `x,y,z`.
Every equal trace retains every distinct curve: the modular triple `(3,3,3)`
is three curves. Thus the unoriented curve count is half the signed
primitive-vector count for the associated norm ball.

The roots and three open Farey sectors cover the rational slopes once.
The raw signed endpoint pairs used in the traversal are
`((1,0),(0,-1))`, `((1,0),(1,1))`, and `((0,1),(1,1))`. Interior nodes are
mediants; endpoints remain roots and are never inserted again. The trace
across an edge is `a*b-opposite`. After an outward trace `c>=max(a,b)>2`,
the child traces `a*c-b` and `b*c-a` exceed `c`. This proves the pruning
rule. The numerical implementation additionally checks increasing log
traces and a subtraction ratio at most one half (with a recorded small
binary64 allowance).

The curve/region identification and edge trace identity are checked against
[Bowditch, Sections 1 and 2](https://warwick.ac.uk/fac/sci/maths/people/staff/brian_bowditch/bhb-markoff.pdf).
The finite-box bound and implementation checks below are derived here.
No global counting theorem or recent flatness preprint is audited by this
experiment.

## Independent coverage and arithmetic checks

The main traversal uses binary64 log traces, `log1p` for subtraction, and a
length formula that never exponentiates a large trace. A separate oracle
tests every primitive slope in `|p|<=160`, `0<=q<=160` (31,224 slopes).
For each slope it obtains the two Farey parents with the Euclidean modular
inverse and evaluates the trace polynomial in exact rational arithmetic
over `Q(sqrt(11))`. It does not use length-based tree pruning.

For completeness of that box, write `v=log(trace/2)`. Outward subtraction
by a ratio at most one half gives `v_child>=v_left+v_right`. Both fixtures
have minimum root trace at least `5/2`, and
`log(5/4)>1/5`, for example by integrating `1/t>4/5` on `(1,5/4)`.
Mediant induction gives `v>=F/5`. Here `F=|p|+q` in the negative sector,
`F=p` for `p>=q>=0`, and `F=q` for `q>=p>=0`. These formulas are the sums
of the nonnegative endpoint coefficients in the respective sector bases;
each is at least `max(|p|,q)`. Since `length=2 acosh(exp(v))>2v`, length
at most 64 implies `max(|p|,q)<160`. This is an analytic coverage bound;
the final comparison of transcendental lengths with 64 is still numerical.

Traces are exact pairs `a+b*sqrt(11)`. Opposite-signed coefficients are
evaluated as `(a*a-11*b*b)/(a-b*sqrt(11))`, with an exact rational norm,
to avoid catastrophic cancellation. A Pell-unit regression exercises
this path with `(10-3*sqrt(11))^80`. Lengths are evaluated with scoped
Decimal precision 100 and 140. Both precisions and the log traversal select
the same 1104 modular and 1127 asymmetric slopes. The observed maximum
Decimal precision difference is below `1.1e-98`; the maximum binary64-log
length difference is below `1.1e-13`. Exact algebraic traces do not make
transcendental lengths or cutoff decisions exact or interval-certified.

## Block metrics and conditional sensitivity

We use `N(L)=#{length<=L}`, `D(L)=N(2L)-4N(L)`, and blocks `[T,2T]`
for `T=4,8,16`. The stored lengths reach 64, the largest required threshold.
At `length/2` the jump in `D` is +1; at `length` it is -4. All numerically
equal events are aggregated before updating. Both one-sided limits at
interior events and the terminal endpoint are included in the supremum;
the external left limit at `T` is excluded. The exact integral on an open
event interval `(a,b)` with constant integer `D` is
`D^2*(1/a-1/b)`. A second implementation directly counts on every interval
and endpoint without using the event-update accumulator. The regression
fixtures include simultaneous full and half events with opposite jumps.

The displayed chapter metrics use the exact-trace oracle lengths rounded
to binary64. Log-recursion metrics are recorded separately. In the checked
run their maximum differences are below `2.7e-15` for `M` and `3.2e-15`
for `Q`. These comparisons do not certify the order of arbitrarily close
transcendental events, and no tolerance is used to merge different events.
`checks_passed_scope` in the result states the actual gates; metric
discrepancies are explicitly retained as diagnostics.

The replacement also computes a conditional sensitivity enclosure for `M`.
Assume every stored length `l_i` differs from the true one by at most
`epsilon=1e-10`. Define

```text
N_lower(u) = #{i : l_i+epsilon <= u}
N_upper(u) = #{i : l_i-epsilon <= u}
D_lower(u) = N_lower(2u) - 4*N_upper(u)
D_upper(u) = N_upper(2u) - 4*N_lower(u).
```

Then `D_lower<=D_true<=D_upper`. Its distance from zero is a lower bound
for `|D_true|`; the larger absolute endpoint is an upper bound. Take the
suprema after dividing by `u` on `[T,2T]` to bound `M`. These functions
are constant between interval endpoints at `l_i±epsilon` and
`(l_i±epsilon)/2`; endpoint values and one-sided limits suffice, as above.
The implementation uses exact `Fraction` values for the stored binary64
lengths, rational radius, event positions, and final bounds. Rounded
decimal displays accompany the exact rational endpoints. The largest
observed width is below `1.3e-10` over these six blocks.

This enclosure concerns the supplied finite list with fixed curve membership.
For application to the complete torus spectrum, additionally assume that
no omitted curve can enter a threshold up to `4T` under the perturbation;
the listed-length radius alone does not imply that condition. The enclosure
is **not** a proof of either hypothesis or a general interval-arithmetic
enumeration. It allows nearby events to
change order and is deliberately conservative about their correlations.
No length-8192 sensitivity statement is recovered.

## Remaining evidence

Recovery of the original source, complete output and precision records,
or a separately reviewed full replacement campaign, is still required to
validate the retained long-range report. Larger cutoffs, long twist paths,
event certification, rigorous transcendental bounds, and asymptotic
inferences are outside this fixed experiment. The proof statements in
Section 30 outside this diagnostic keep their separate review status in
the [claim ledger](../../book/claims/section30.json).
