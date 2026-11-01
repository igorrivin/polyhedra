# Separate full torus campaign: method requirements

This is a proposed replacement experiment, not validation of the missing original campaign. The historical length-8192 numbers and the fixed `experiments/section30` and `artifacts/section30` trees remain frozen. No full campaign was run for this author note.

## Inputs and coverage

- Use the exact two triples in `experiments/section30/fixture.json`, primitive slopes modulo sign, and `N(L)=#{ell<=L}` with curve multiplicities.
- Use all three disjoint Farey sectors, and record the roots separately. Preserve signed sector endpoints until slope canonicalization. Check determinant, child-slope addition, outward trace growth, subtraction ratio and integer overflow.
- Enumerate to at least 8192 plus the declared sensitivity radius; retain the closest included and pruned frontier curves to each cutoff. Numerical pruning is not an unconditional interval proof of completeness.
- Compare the entire list through 64 to the frozen exact Q(sqrt(11)) primitive-box oracle. Compare a moderate cutoff against an independently written traversal and deterministic slope membership probes. At 8192 the analytic slope-box bound is 20480, but enumerating that whole exact box would require roughly 5e8 primitive candidates; it is not the appropriate full-campaign oracle.

## Arithmetic and resources

The read-only Python timing probe is `resource-probe.json`. At cutoff 512 the existing binary64 log traversal took about 0.086 seconds for each surface and produced 71106 and 72222 curves. The process peak was about 44 MB. These measurements do not verify the large campaign. Quadratic extrapolation suggests tens of seconds for enumeration alone in Python, but its dictionary of tuple keys scales to several GB and its event dictionaries add much more.

`/usr/bin/clang++` is Apple LLVM 21.0.0. Predefined macros give 53 mantissa bits and maximum exponent 1024 for **both** `double` and `long double`. Therefore a long-double rerun on this host provides no extended precision. Record this fact in the run manifest.

A compact 24-byte `(int64 p,int64 q,double length)` record uses about 444 MB for 18.5 million curves. A single sorted length copy adds about 148 MB. Process one surface at a time and avoid materializing all full/half or uncertainty events. A 1–2 GB peak budget per surface is plausible but must be measured. Raw compact records for the two surfaces total about 880 MB before compression; do not embed millions of records in JSON. Native enumeration, sorting, and streaming sweeps should be timed on a moderate cutoff before any full run. No package installation is needed for the existing exact/Decimal oracle or the supported mpmath environment.

The root accepted the smaller length-only variant: the proved three-sector tree gives uniqueness, while the traversal retains root/sector counts, maximum depth, selected slope/path records and a deterministic hash of all slope identities in traversal order. Sorted binary64 length data then need about 148 MB per surface. An optional `(int32 p,int32 q)` sidecar adds about 148 MB; the analytic coordinate bound below 20480 makes that representation sufficient after explicit checks. Raw streams may remain in outer execution evidence with hashes and a regeneration recipe. Canonical results must still contain complete block/count/precision/sensitivity summaries and exact source identities.

## Full block statistics

- Compute all dyadic blocks `T=4,8,...,2048`, not merely the four printed rows. A block needs the complete length list through `4T`.
- Merge two sorted streams, full events at `ell` with jump `-4` and half events at `ell/2` with jump `+1`. Group every exactly equal stored event before updating. Do not merge unequal events by a tolerance.
- Evaluate the initial value at T; exclude its external left limit. Include both sides of each interior event and both the interior left limit and actual value at 2T. Preserve the maximizing location, side and integer count.
- Integrate each constant-D segment by `D^2*(1/a-1/b)` and use compensated summation. Check a second direct-count implementation on every interval for small cutoffs and selected intervals/maximizers at large cutoffs. Metrics from rounded event locations remain numerical observations.
- Store full block tables, integer counts at every dyadic cutoff, minimum cutoff distances and representative maximizing events with slope identities.

## Precision comparisons

Use the existing exact trace oracle at 100/140 decimal digits through 64, not only agreement of two log traversals. For long paths, declare a deterministic selection before final reporting: repeated left/right twists in every sector, alternating paths, the longest paths, paths closest to the final and dyadic cutoffs, and maximizer-event paths. At least thirty long samples should be retained individually. Re-evaluate traces by a separately written exact Q(sqrt(11)) recurrence or direct multiprecision trace recurrence, then lengths at two decimal precisions. Avoid Python call-stack recursion on long twist chains. Rationalize opposite-sign quadratic coefficients before numerical evaluation. Record every path, slope, precision and residual. Sample agreement does not bound the error at unsampled nodes.

## Conditional sensitivity envelope

For a fixed supplied list and an explicitly assumed position error epsilon, use

```
Nlo(u)=#{stored ell+epsilon <= u}
Nhi(u)=#{stored ell-epsilon <= u}
Dlo(u)=Nlo(2u)-4*Nhi(u)
Dhi(u)=Nhi(2u)-4*Nlo(u).
```

The pointwise distance of `[Dlo,Dhi]` from zero bounds `abs(Dtrue)` below; the larger absolute endpoint bounds it above. Sweep the four sorted endpoint streams `(ell±epsilon)` and `(ell±epsilon)/2`, with the same endpoint convention. This does not depend on an unknown internal event ordering. To claim exact finite rational bounds, convert the stored binary64 values and rational epsilon to exact common-denominator integers and use checked 128-bit comparisons, or perform the final comparisons with Python integers. Do not silently call a float-only sweep an exact enclosure. Bounds apply to the true complete spectrum only with the additional completeness/no-entry assumption on omitted curves. A radius such as 1e-6 is a hypothesis, not a certified consequence of sampled residuals.

For lengths in `[1,8193]` and epsilon=1e-6, a common denominator `2^53*5^6` accommodates full/half binary64 positions and epsilon endpoints. Endpoint numerators are below 2^81. If the count is below 2^26 then all D magnitudes are below 2^29, and the products used to compare normalized values are below 2^110, within a signed 128-bit integer. The implementation must check these range assumptions and exact conversion; changing the cutoff/radius requires rechecking them. This is an arithmetic design bound, not a checked implementation.

## Required retained outputs and review gate

Keep source/input/compiler/platform hashes; raw record layout and endian convention; per-surface spectrum hashes/counts; all block statistics; direct-reference comparisons; precision samples; cutoff/frontier margins; conditional sensitivity rows and their hypotheses; timings and peak RSS. Verify source immutability and independent reviewer approval before incorporating new numerical text. Numerical agreement may be compared to each retained historical number but must not be called recovery of the historical source or raw archive.

## Exact finite companion fixtures

1. For the unit square, `A(u)=4*floor(u)*(floor(u)+1)` and `P(u)=8*sum(phi(n),n<=floor(u))`. Check `P(L)=sum(mu(d)*A(L/d),d<=floor(L))` at integer and noninteger rational L. Treat the area-density constant symbolically when testing normalized formulas; no rational calculation certifies zeta(2).
2. For every integer cutoff `1<=D<=L`, compare `sum(mu(d)*A(L/d),d>D)` with the direct lattice sum of `M(floor(L/r(m)))-M(D)` over `0<r(m)<=L/D`, including the zero summands on the cutoff boundary. Square and rational diamond gauges both give exact fixtures.
3. The finite dyadic identity is `E(L)=4^(-k)*E(2^k L)-sum(4^(-j-1)*Delta2N(2^j L),j=0..k-1)`. For `N(L)=c*L^2+b*L+d`, `Delta2N=-2*b*L-3*d` exactly. Finite identities do not establish the limiting remainder condition.
4. For lengths `[2,2,4,5,8]` and block `[2,4]`, aggregate simultaneous events; the exact results are `M=5/2` and `Q^2=49/20`. The left limit at 2 is outside the block.
5. For rational row endpoints a<=b and n>=1, verify the divisor identity `sum(mu(d)*(floor(b/d)-ceil(a/d)+1),d|n)` against direct gcd counting. Include negative endpoints, zero, integer endpoints, primes and composites.
6. The geometric/arithmetic power balance is `d=(2-alpha)/(3-alpha-theta)` and `kappa=(2-alpha*theta)/(3-alpha-theta)`. At alpha=2/3 and theta=1/2,7/8,11/12, exact rational simplification gives 10/11,34/35,50/51. These are conditional algebraic consequences, not verification of any Mertens or geometric hypothesis.
7. For a finite primitive length list with multiplicities, verify `A(L)=2*sum(floor(L/lambda))` by explicitly enumerating signed positive multiples. Retain the shortest-vector normalization separately from hyperbolic length units.
