# Section 30 author revision and bounded replacement

Baseline: `df952174e55f08a52596d912d9713a9d1e116313`. This is the author
implementation record; independent verification is a later, separate gate.
Only the six files listed in `torus-author-manifest.json` are owned by this
track. The main source extraction belongs to the structural track. No
canonical artifact, prior checkpoint, original repository, Site, or source
commit was modified by this author.

## Corrections

The chapter now distinguishes the supplied draft's length-8192 report
from the new length-64 experiment. It preserves all 22 original labels in
order and preserves the old four-row table byte for byte. The old counts,
precision comparisons, cutoff-separation statement, and sensitivity bounds
are explicitly reported/unreplayed. The false assertion that their source
archive accompanies the monograph is removed. This follows the missing
archive finding already recorded in the integration audit and computational
status ledger; the replacement does not invent provenance for those values.

The curve convention now explicitly identifies primitive slopes modulo
sign, retaining trace multiplicities. Root slopes and each open Farey
sector are specified. The event convention states `N(L)=#{ell<=L}`,
aggregates simultaneous opposite jumps, includes both one-sided limits
inside the block, and excludes the external left limit at its start.
The general inversion and constant-event integral were checked by direct
derivation. This is not a full audit of the strict-convexity, row-flatness,
rational-polygon, or recent-preprint arguments; their ledger status says so.

The local curve/region and trace-edge facts were checked against
[Bowditch's primary text, Sections 1 and 2](https://warwick.ac.uk/fac/sci/maths/people/staff/brian_bowditch/bhb-markoff.pdf)
on 2026-11-01. The source gives the rational-region correspondence,
simple-curve interpretation, trace-edge identity, and decomposition about
a root vertex. The finite-box derivation and fixed-fixture arithmetic are
separate checks supplied here. No manuscript was uploaded for this lookup.

## Independent calculations within the author implementation

The driver compares a binary64 logarithmic tree traversal against an
enumeration of all 31,224 primitive unoriented slopes in a coordinate box.
The latter obtains Farey parents by a Euclidean modular inverse and computes
traces exactly over `Q(sqrt(11))`, without length-based tree pruning.
For these fixtures, minimum root trace is at least 5/2. Outward traces obey
`v_child>=v_left+v_right` for `v=log(trace/2)`, and root `v>1/5`.
The three sector weights are `|p|+q`, `p`, and `q`, respectively, so
`length>2*max(|p|,q)/5`. This proves that length at most 64 lies inside
the tested 160 box. It does not certify the transcendental membership test.

Exact algebraic coefficients with opposite signs are evaluated through
their exact norm and conjugate denominator; this avoids potentially severe
decimal cancellation. The regression `(10-3*sqrt(11))^80` tests that path.
Independent Decimal evaluations at 100 and 140 digits select the same slopes
as the tree: 1104 modular and 1127 asymmetric curves. Their maximum observed
length difference is about 1.09e-98; binary64 log lengths differ from the
140-digit values by at most 1.03e-13. These are numerical comparisons.

For blocks T=4,8,16, the event sweep agrees with direct counts on every
event interval. Log-derived versus oracle-rounded metrics differ by at
most 2.67e-15 for M and 3.11e-15 for Q. These diagnostic discrepancies are
reported explicitly; `checks_passed` is not an event-order certificate.
The new table is separate from the old table and the exact full records
will be regenerated into `artifacts/section30/result.json` after source
review and commit.

A conditional sensitivity calculation bounds M for the supplied finite
curve list under assumed per-length error 1e-10 and fixed membership.
It uses exact rational interval endpoints and count bounds; the derivation
is in the experiment README. For the full torus spectrum there is another
explicit assumption: no omitted curve can enter a block threshold under
perturbation. Neither assumption is proved. The maximum observed interval
width is 1.24e-10 over the six bounded blocks. This addition supplies a new
bounded diagnostic; it does not recover the historical long-run assertion.

## Verification and evidence

The recorded checker `torus-author-checks.py` runs 16 focused tests, Ruff,
and the full fixed experiment from `/private/tmp`, checking import/CWD
independence. It records commands, outputs, source hashes and elapsed time;
checks label/table preservation, ledger targets and authored whitespace;
and verifies that no owned source changed while the checks ran.
The final run and manifest are `torus-author-result.json` and
`torus-author-manifest.json`. Earlier `torus-first-result.json` and
`torus-second-result.json` remain separate intermediate evidence.

The tests include exact root equations and signs, three equal root traces
as distinct curves, hand-derived short modular traces, a small independent
box, overflow-free log length, full/half simultaneous events, block-start
and prejump limits, interval integrals, precision-context restoration,
and conditional bounds with exact-zero and perturbed-error cases.

The full length-8192 campaign, arbitrary-cutoff API, rigorous transcendental
enclosures, long-twist precision study, and asymptotic conclusions remain
outside this revision. The other Section 30 proof statements retain their
separate review status. No upload or deployment was attempted.
