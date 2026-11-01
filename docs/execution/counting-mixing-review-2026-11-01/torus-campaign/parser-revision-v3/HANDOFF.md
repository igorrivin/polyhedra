# Parser repair ready for final review

The native parser now requires complete numeric tokens for lengths, block
starts, cutoffs and roots. `DIRECT` and `RECORD_LENGTHS` accept exactly `0`
or `1`. Malformed campaign arguments are rejected before stream creation.
The metrics input must be a regular file, and its read must reach EOF without
an I/O error. A readable empty ordinary file remains valid.

Thirteen focused tests and Ruff pass. All six reviewer failure probes reject
their inputs without producing a result. The repaired length512 campaign
passes every validation and has identical scientific report fields, native
scientific fields and all six raw-stream SHA256s compared with v2. Only
source/compiler provenance, execution paths, timings and RSS are excluded
from that comparison. The arithmetic/traversal and campaign sample-selection
source regions are byte-identical to v2; `run.py` is entirely unchanged.

Review these files:

- `parser-repair-final.patch`: exact patch from the preserved v2 source.
- `before/` and `after-final/`: source snapshots.
- `after-final-source-sha256.json`: current source freeze.
- `verification-final-summary.json`: passed scope and scientific equivalence.
- `verification-final-receipts.json`: actual tests, Ruff and replay commands.
- `malformed-probes-final.json`: reviewer probe rejection receipts.
- `preflight512-v3-final/result.json`: the repaired-source preflight for the
  final clean-source8192 replay.
- `verify_final_parser_repair.py`: verification and comparison source.

The first EOF-only guard did not reject a directory on this Apple C++ library;
that failed test and its source snapshots are preserved in
`io-guard-attempt1/`. The final repair adds the regular-file check and retains
the EOF/bad-state check. Earlier v3 interim evidence also remains untouched.

The original full v1/v2 reports, their freeze manifest, and the frozen64
artifact were checked unchanged. No full author campaign was rerun for this
parser-only repair. Final independent review, source checkpoint and the
clean-source8192 replay remain required. No commit, book build, upload or
canonical artifact was made by this repair.
