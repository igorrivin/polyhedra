# New full torus diagnostic campaign

This directory implements a **new** numerical experiment through hyperbolic
length8192. It does not recover the missing historical source or raw archive.
The fixed `experiments/section30` and `artifacts/section30` trees remain frozen;
the fixed result SHA256 is checked before every run. The exact ordered triples
are `(3,3,3)` and `(5/2,5-sqrt(11)/2,4)`, with roots `(1,0),(0,1),(1,1)`.
Each primitive slope modulo simultaneous sign is one curve. Equal traces retain
their multiplicities.

Use the supported Python interpreter and the available Apple compiler. No new
packages are needed. From the repository root, first run:

```sh
/tmp/polyhedra-baseline-20261031/bin/python -m unittest discover -s experiments/torus_campaign/tests -v
/tmp/polyhedra-baseline-20261031/bin/python experiments/torus_campaign/run.py --cutoff 64 --output-dir /tmp/torus-check64
/tmp/polyhedra-baseline-20261031/bin/python experiments/torus_campaign/run.py --cutoff 512 --output-dir /tmp/torus-preflight512
```

After checking those receipts and resource measurements, run:

```sh
/tmp/polyhedra-baseline-20261031/bin/python experiments/torus_campaign/run.py --cutoff 8192 --preflight /tmp/torus-preflight512/result.json --output-dir /tmp/torus-full8192
```

Outputs and their directory must be new. The full run requires a successful
512 preflight with identical campaign source and fixed input hashes. A final
`--phase clean_replay` additionally requires a clean source checkout. Source
and input hashes and the Git commit are checked again after computation.
Author runs in a dirty checkout are explicitly marked. Independent code review
and a clean-source replay are required before incorporating the new scientific
results into the chapter. Raw streams stay in external execution evidence;
`result.json` is the compact candidate artifact, pending that review.

The native code uses binary64 log traces, stable `log1p` subtraction, and three
disjoint open Farey sectors with raw endpoints `(1,0),(0,-1)`, `(1,0),(1,1)`,
and `(0,1),(1,1)`. Roots are inserted separately. Each visited mediant checks
its determinant, slope-addition range, subtraction ratio and outward log
growth. The exact reduced-root equations and inequalities are checked by the
Python exact quadratic oracle. Pruning uses increasing outward traces. The
enumeration guard is rounded upward beyond `cutoff+1e-6`. This is numerical
pruning, not an interval certificate of list completeness.

Only one surface is processed at a time. A compact sorted binary64 length
vector retains every curve. A separate external little-endian `(int32 p,
int32 q)` identity stream follows roots, sectors0/1/2 and left-child-first
depth-first order. Its SHA256 and a deterministic FNV-1a64 hash are recorded.
The sorted length stream has its own SHA256. The identities and sorted lengths
are **not index-aligned**; aligned `(p,q,length)` records are emitted only for
the moderate validation runs. Full replay regenerates both streams exactly
for the recorded compiler, input, and source. Paths and slopes of selected
curves, root/sector counts, maximum depth, cutoff and frontier margins are
retained in the compact report and raw native report.

All dyadic integer counts and blocks `T=4,8,...,2048` are computed. The event
sweep merges full events with jump-4 and half events with jump+1, grouping
exactly equal stored positions. It includes both sides of interior events,
both relevant terminal values and the initial actual value, excluding the
external left limit atT. Maximum comparisons use exact stored-event rationals.
The integral uses compensated summation of
`D^2*(b-a)/(a*b)`, algebraically `D^2*(1/a-1/b)`. Every interval is checked
by direct counts at small cutoffs; selected intervals and each maximizer are
checked at large cutoffs. The Python oracle independently checks small full
M/Q tables and every large-row maximizing count.

The report also records finite signed all-point counts
`A(L)=2 sum floor(L/ell)` and `A(2L)-4A(L)` at dyadic cutoffs, using exact
comparisons of stored binary64 rationals. The divisor-sum evaluation is
independently checked by direct floors through64. These are hyperbolic length
units; there is no shortest-vector rescaling and no asymptotic inference.

The conditional sensitivity sweep uses all four streams `ell±epsilon` and
`(ell±epsilon)/2`, with rational `epsilon=1e-6`. It forms
`Dlo=Nlo(2u)-4Nhi(u)` and `Dhi=Nhi(2u)-4Nlo(u)` and takes the suprema of the
distance of that interval from zero and its largest absolute endpoint,
divided byu. IEEE754 mantissas and exponents are converted exactly to the
common denominator `2^53*5^6`. Lengths in[1,8193], endpoint numerators below
2^81, count below2^26 and D magnitudes below2^29 are checked. The ratio
comparison products are below2^110 and multiplication is explicitly checked
in signed128 arithmetic. Python's unbounded integers check final ordering
and exact widths, and an independent Fraction sweep checks every small row.
This enclosure assumes every listed length has the stated error. Applying it
to the complete true spectrum additionally assumes completeness and no entry
by omitted curves. Neither hypothesis is certified by the sampled checks.

The full list through64 is compared with a fresh exact `Q(sqrt(11))`
primitive-box oracle at100 and140 decimal digits, and with every frozen
exact trace and slope. A separately written direct-trace FIFO traversal and
128 deterministic decimal membership probes check the moderate512 list.
Declared long samples cover left/right twists at depths16,64,256,1024,2048,
4096 when present; both alternating paths at depths6,10,14,16 when present;
each sector's deepest curve; nearest cutoff/frontier curves; block
maximizer events; and the twelve closest curves below the final cutoff in
each sector (equal lengths resolved by ascending slope). The latter declares
36 distinct near-final-scale paths before the replay. The full run requires
all 36 to have length at least 6144 and records their actual length range,
the counts of samples above 4096 and 6144, and depths at least 1024.
Every retained path is reconstructed from its slope and
reevaluated by direct Decimal trace recurrence at100 and140 genuine digits.
At least30 samples longer than64 are required in each full surface run.
All individual residuals and paths are retained. This does not certify errors
at unsampled nodes or the ordering of transcendental events.

The manifest records actual compiler flags, executable/source/input hashes,
platform, mantissa bits, stage times, and peak RSS. On the probed Apple LLVM21
host, both `double` and `long double` have53 mantissa bits: long double is
not used as an independent precision reference. No fast-math is enabled.
The only claim of exactness in the sensitivity rows concerns the finite
rational envelope computation under its explicit hypotheses.
