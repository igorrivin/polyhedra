# Crosscutting numerical correctness review

**Approved for the reviewed product, contract and portable-replay scope. No
remaining product-code or adapter blocker was found.** Two adapter defects
found during this review stage were corrected and exercised before approval.
Final integration-evidence synchronization was then verified. Clean-commit
artifact generation remains a separate closeout task.

This review compares the uncommitted increment with baseline `285a6cb`, reads
the owning-module contracts and affected tests, and checks static anti-patterns,
schema preservation and evidence provenance. It does not repeat the full
suite, the installed-wheel checks, the 74-case mathematical review, or the
separate three implementation reviews. All checks below ran against the local
checkout; no original repository, product source, Git index or commit was
changed by this reviewer.

## Source identities and numerical ownership

The three independently approved product identities still match:

| Module | SHA-256 |
| --- | --- |
| `geometry.py` | `eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73` |
| `optimization.py` | `1e9cedb1bd48e8a79356c51c336199b9134012eedf59487b6819fb491918098e` |
| `rivin_delaunay.py` | `65a388fc0682a32370c2ad886ef807852ae68df07f1a00d7f7b3a587f066f053` |

Additional changed-source/schema hashes and commands are in
`crosscutting-checks.json`.

- The maintained geometry owner contains the new binary64 and MP kernels.
  Angle-volume reporting and threshold defaults delegate to it; optimizer
  endpoint checks explicitly choose `mode="bloch_wigner"`. No new competing
  product evaluator was introduced. Existing explicit finite-series and
  optional Torch paths remain compatibility/research paths with separate scope.
- AST inspection finds no `dps` or `prec` attribute assignment in the changed
  geometry module. Supported input conversion and MP arithmetic occur inside
  `workdps`, and the contract correctly distinguishes working precision, input
  information, MP output, high-level float output and binary64 topology.
  Scoped precision is not represented as thread-local or as an error enclosure.
- The corrected angle optimizer does not clip angles or infer success from
  the iteration budget. Original equality and inequality matrices remain in
  the final primal, full-space stationarity, multiplier-sign and
  complementarity audit. Numerical rank reduction affects step construction,
  not which original constraints count at acceptance. Exact flat-angle cases
  and numerical witness failures retain explicit status.
- The optimizer service ranks verified endpoint values and checks boundary
  reconstruction before choosing the winner. Raw DE convergence remains
  separate from candidate validity, including after serial polishing.
  Deep copies isolate callbacks without claiming immutable post-return arrays.
  Invalid values are recorded explicitly rather than fabricated as valid
  coordinates; the shared serializer performs a strict-JSON check before the
  CLI or GUI writes its result.

## Compatibility, tests and documentation

The v1 schema is byte-identical to baseline `285a6cb`; the v1 fixture is
byte-identical to the earlier CLI artifact, SHA-256
`f8408759dd9a0b46f047bb4fb58ff9f4f1811a80c5ca22b4277ff66f3d8f8558`.
Both schemas and the fixture have ordinary Git filter attributes. Schema v2
expresses validation and verification work, and the closed v1 schema is not
silently reused for new producer output.

The changed older tests replace obsolete assumptions rather than remove
acceptance checks: polish fixtures now have physically consistent objectives;
callback tests require equal values in distinct objects; final-tie tests
require feasible/KKT-checked final angles; legalization tests preserve the
strict acceptance conditions and repeated deterministic path while bounding
the changed amount of work. New tests include independent quadrature/Clausen
references, actual constraint reconstruction, rational fixture checks,
instrumented objective-call counts and explicit failure-state probes. The
controlled malformed/cached-score probes are correctly labeled as contract
tests, not ordinary SciPy behavior.

The contract docs, ownership index, changelog, errata and computational ledger
separate exact finite identities, numerical residual checks, geometric
embedding and monograph claims. Section 9's fixed-dihedral coordinates are
explicitly distinguished from the free-angle inequality optimizer. Existing
research outputs and uncommitted review failures retain their stated source
and evidence status. The separate `refine_geometry_for_volume` cached-score
path, H4/H5, Torch, optional dependencies, full corpus/proof review and
publication are not implicitly covered.

A nonblocking editorial remnant remains: the first docstring line of
`volume_threshold.py` says "Self-contained module", although its body and
new contract correctly describe its canonical-kernel dependency. Removing
that old heading is a small future documentation cleanup, not a numerical
acceptance or scope defect in the corrected implementation.

## Portable replay checks and resolved findings

The adapted drivers import maintained product owners and retain the original
independent diagnostic calculations. Their diffs add repository/output
selection and provenance; they do not duplicate a product kernel. Archival
failed-source snapshots are clearly used only as identified diagnostic inputs.

Review caught `strargs.output` in the angle adapter's final print. F821 lint
confirmed the undefined name; it is now `str(args.output)`. A real precision
adapter run by the documentation owner additionally exposed collision between
the added CLI namespace `args` and an original local tuple named `args`;
only the added namespace was renamed to `replay_options`. Syntax and `--help`
checks alone would not have exercised either end-of-run path.

The documentation owner then ran all three complete bounded replays to new
temporary outputs. This reviewer independently inspected those JSON records
and verified their actual driver/source hashes. Final adapter hashes are:

| Adapter | SHA-256 |
| --- | --- |
| `angle-before-after.py` | `f0f60392144c665af4f18ffa8b8ea3e74acf51b3b696942d38b4786901fe2db7` |
| `angle-independent.py` | `fac5a49494dae1819482d88c9f78e90f6bc7a4988be2274c70e1573f44cf0b8a` |
| `precision-independent.py` | `68a34fa56063e9c5596f9045d35f39941554610e871cb2c7e1f8aa2dcfbc9cd8` |

The final outputs cover five before/after cases plus 90 LP inputs, seven
independent angle comparisons with the exact `1/7` fixture, and 74 precision
cases with no failures. Final undefined-name lint, all three help commands
from `/tmp`, AST parsing and `git diff --check` pass. Product-source hashes
did not change during these adapter corrections. Detailed hashes are in
`crosscutting-evidence-checks.json` and the authored
`replay/verification.json`.

At manifest SHA-256
`8f4c5303b6fcbfc1df44412049221572526634b57f8398fcfdbb5a9f8d31ddb4`,
all **103 destination hashes match**. Two still-running integration origins,
`integration-installed-probes.py` and `.log`, changed after the initial copy.
The documentation owner was notified and synchronized final integration
evidence, preserving the earlier installed-probe harness failure log. The
follow-up inventory at SHA-256
`18f75ff197eb235a18800cb9a4ecac3db0cebc4719a82c03e64109d3ee982155`
has **125 entries with zero origin or destination mismatches**. The new
`crosscutting-final-evidence-checks.json` records that successful recheck;
the intermediate record remains unchanged. AppleDouble sidecars are excluded
from source and evidence checks. This review still does not claim the later
clean-commit artifact or publication gates.
