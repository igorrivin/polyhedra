# Frozen author handoff for independent review

The new length-8192 campaign is implemented and both author replays completed.
No canonical artifact, chapter, ledger, old experiment, or old artifact was
edited by this implementation task. No commit or upload was made. The source
is now frozen for independent code review, followed by a clean-source replay.

The implementation is `consolidated/experiments/torus_campaign/`, containing
`campaign.cpp`, `run.py`, `README.md`, and `tests/test_campaign.py`.
The exact seven-file source/input freeze, strict v1-v2 comparison, final
scientific summary, and raw-stream identities are in
`v1-v2-comparison-and-author-freeze.json`. The full compact author candidate is
`full8192-author-v2/result.json`; native reports and all raw streams are in that
same external execution directory. `compare_author_replays.py` is the source
of the strict comparison. Running it again requires a fresh comparison output
name because the current output is exclusive.

The driver receipts are retained in each `result.json`. Meaningful regression
receipts are retained in `verification-v2.json`: 9 new tests and all 16 frozen
Section 30 tests passed. `preflight512-v2/result.json` records successful
same-source moderate validation, exact 100/140-digit fixed64 oracle checks,
the independently written direct-trace FIFO traversal, 128 deterministic
membership probes per surface, and small direct metric/sensitivity checks.

The full v2 driver took 59.09 seconds. Native stage totals were 19.81 seconds
for modular and 32.08 seconds for asymmetric. Native-process peak RSS was
149,323,776 and 152,125,440 bytes respectively; these are per-process peaks,
not the aggregate simultaneous memory of the parent Python process and its
child. Both actual compiler mantissa measurements are 53 bits for double and
long double. Direct decimal references use genuine 100 and 140 digits.

Counts through8192 are exactly 18,191,508 and 18,486,116, matching the retained
historical counts. Every retained historical printed M/Q entry at
T=32,128,512,2048 agrees with the new measurements at four decimal places.
This agreement does not recover the missing historical implementation or raw
archive. V1 and v2 have exactly equal dyadic N/A/Delta2_A tables, every M/Q row,
every exact conditional sensitivity row, cutoff/frontier margins, sector and
traversal counts, and FNV identity hashes. All four raw streams have identical
SHA256 hashes between v1 and v2, verified by reading both versions.

The v2 precision selection adds twelve nearest-below-final-cutoff curves per
sector with deterministic slope tie-breaking. There are 36 distinct such
curves per surface. Their observed lengths range from 8191.995515439277 to
8191.999874994218 (modular), and 8191.988460428032 to8191.999803990989
(asymmetric). Total selected samples are151 and126; counts at length>=6144
are46 and41; counts at depth>=1024 are21 and17. Every selected slope, path,
selection reason, 100/140-digit direct length, and residual is retained.

Worst selected native-length residuals are5.52810645e-10 and1.19404116e-9.
Worst 100-vs140 residuals are8.93562514e-97 and4.51874254e-96. These are
sampled observations, not every-node error certificates. Minimum observed
dyadic-cutoff distances are1.25005782138e-4 and8.36935365385e-5.

At assumed length error epsilon=1e-6, maximum exact conditional M envelope
widths across all new rows T=4,...,2048 are1.23130430745e-6 and5.61207276795e-7,
both atT=4. Across the historically printed subset only, maxima are
1.20589304806e-7 and3.67591167679e-8, both atT=32. These are new conservative
bounds under the stated listed-length and completeness/no-entry hypotheses.
Different historical arithmetic, sample choices, block ranges, and bound
constructions are not reconstructed by these numbers.

The finite Section31 extension records signed all-point
`A(L)=2 sum floor(L/ell)` and `A(2L)-4A(L)` at the same dyadic cutoffs using
exact comparisons of stored binary64 rationals. Independent Fraction floor
checks through64 pass. Hyperbolic length units are retained; no shortest-vector
rescaling or asymptotic assertion is made.

For the reviewer, the central mathematical checks are the three-sector
coverage/pruning conventions; grouping and one-sided endpoint handling in
`metrics`; exact common-denominator conversion and four-stream envelope in
`sensitivity`; and independence/extent of the fixed64, moderate512, and
selected long-path checks. All actual scientific source/input identities are
captured by the v2 manifest. Further changes require a new freeze and replay.

After review and source checkpoint, a clean replay can use the existing
same-source512 preflight (the driver checks content hashes), or a fresh clean
512 preflight, followed by:

```sh
/tmp/polyhedra-baseline-20261031/bin/python experiments/torus_campaign/run.py --cutoff 8192 --phase clean_replay --preflight /absolute/path/to/preflight512-v2/result.json --output-dir /absolute/path/to/new-clean-full8192
```

The clean output belongs outside the source checkout until that run has passed.
Its compact result can then be curated as the separately reviewed new campaign
artifact, with an explicit raw-stream regeneration/retention policy.
