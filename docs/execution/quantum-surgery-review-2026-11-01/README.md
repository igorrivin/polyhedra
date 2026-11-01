# Quantum boundary and Dehn filling review

This checkpoint covers Sections 12–14 and 16: finite quantum boundary
formulas, screened periods and fusion, local classical folds, and local Dehn
filling response. The two new ledgers contain
[30 quantum claim groups](../../../book/claims/sections12-14.json) and
[26 surgery claim groups](../../../book/claims/section16.json). Independent
reviews approve the stated derivations and primary-source hypotheses within
their explicit scope. They do not reprove all external results or approve
the inherited global quantum analysis of Section 15.

Source commit: `514bc30b0d86a0a38b2ede1cb9dfb261a6b2995a`. The [closeout](closeout.md) records the
changes, evidence, preservation checks and remaining work. The
[companion result](../../../artifacts/quantum_surgery/result.json) was freshly
generated from that clean source commit, outside the checkout. Both recorded
source states are clean and all 13 recorded input hashes match committed
bytes. The [scientific comparison](clean-source/scientific-comparison.json)
matches every field of the final independent replay except the four explicit
timestamp, elapsed-time and source-state fields.

The [186-page working draft](../../../artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf)
is the exact reviewed precommit PDF. Its 18 active TeX input hashes match the
source commit. The integration reviewer actually inspected 56 selected pages,
including every changed-section page, adjoining pages, affected front matter
and bibliography. The other 130 pages were not visually reviewed in this
pass. No postcommit PDF rebuild or browser verification is claimed.

The computational review found and closed one real defect: a later matrix
NaN could be ignored by a maximum and falsely pass with residual zero.
The corrected guard rejects nonfinite actual, expected and difference entries
before scaling. The [before](computation-review/nonfinite-before.json) and
[after](computation-review/nonfinite-after.json) records preserve the independent
24-case regression: six invalid cases formerly passed; all now reject.
The fixed finite scientific outputs did not change.

The principal review and provenance records are:

- [Quantum mathematics](quantum-review/independent-review.md),
  [source pins](quantum-review/source-pins.json) and
  [exact approved hashes](quantum-review/approved-hashes.json).
- [Surgery mathematics](surgery-review/review.md),
  [source pins](surgery-review/source-pins.json) and
  [exact approved hashes](surgery-review/approved-file-hashes.json).
- [Companion implementation](computation-review/review.md),
  [final approval](computation-review/approval-manifest.json) and
  [final independent replay](computation-review/replay-result-final.json).
- [Integrated source/PDF review](integration-review/review.md),
  [final 20-path approval](integration-review/approved-source-manifest.json),
  [visual scope](integration-review/visual-review.json) and
  [source commit receipt](checkpoint/source-checkpoint.json).

The initial author freezes remain historical. The
[ledger path correction](path-pointer-correction.json),
[source citation correction](surgery-math/source-pin-correction.json) and
[finite-guard correction](computation/nonfinite-guard-correction/report.md)
record subsequent changes without rewriting those freezes. Final review
manifests bind the corrected source identities.

The [copy manifest](evidence-copy-manifest.json) identifies 48 exact
evidence copies and records omitted outer material. No large rendered-page
archive, build cache, full duplicate chapter archive or redundant initial
result is committed. Some archived reviewer scripts refer to those outer
working files. The maintained [companion guide](../../../experiments/quantum_surgery/README.md)
is the reproduction entry point.
Bare archived filenames in reports and freeze metadata resolve within their
originating outer execution directory when the named file was omitted from
the curated set; they do not imply that every historical file was copied here.

Run `python -B docs/execution/quantum-surgery-review-2026-11-01/verify_checkpoint.py`
after the local artifact commit to verify identities, ancestry, preservation
and links. Before that commit, use `--candidate`. The verifier does not rerun
scientific calculations, rebuild the PDF or repeat visual review. It writes
its receipts outside the checkout, avoiding a self-referential final commit.
Use `--receipt /absolute/outer/execution/path.json` for a reviewer-owned
receipt under this checkpoint's outer execution directory. Receipts are
created exclusively; a repeated default run uses a timestamped filename.

Next comes the broader Section 15 contour, tail and uniform-remainder review.
The original exact quantum integral and length-8192 torus campaign remain
unrecovered/unreplayed. Remaining chapter reviews, optional-dependency
coverage, HTML/browser verification and publication metadata/licensing are
separate tasks. Upload remains the final publication step.
