# Normalization and hypothesis revision

This checkpoint covers Sections 1–8 and Appendix A. It makes their measure,
orientation, stabilizer, cone-wall and convergence conventions explicit and
adds a fixed exact-arithmetic companion. The two claim ledgers contain
[28 claims](../../../book/claims/sections1-6.json) and
[13 claims](../../../book/claims/sections7-8.json). This is a bounded review
of statements, normalizations and derivations, not a new refereeing of every
cited proof or of the entire monograph.

The source commit is `2a91e9f33b2b2e4ed3ae8ec9863870f91c22a83f`.
The [closeout](closeout.md) records the results, preservation checks and
remaining work. The [exact result](../../../artifacts/normalizations/result.json)
was generated from that clean commit. The
[working-draft PDF](../../../artifacts/normalization-review-2026-11-01/monograph-working-draft.pdf)
is the exact reviewed precommit build whose fourteen TeX input hashes match
the source commit. No postcommit PDF rebuild is claimed.

Use the [companion guide](../../../experiments/normalizations/README.md) to
reproduce the six fixed rational-weight fixtures and the measure, Gram,
Pfaffian and trace checks. The expanded independent probes are evidence for
finite cases; they do not replace the general proofs or their hypotheses.

The review records are chronological. The following supplements close the
findings in the earlier reports:

- Sections 1–6 and Appendix A: [mathematical review](math-review-a/review.md),
  [precise Fillastre statement and attribution](math-review-a/fillastre-patch-review.md),
  and [final eight-file approval](math-review-a/path-wrap-approval.json).
- Sections 7–8: [mathematical review](math-review-b/review.md),
  [two attribution corrections](math-b/author-corrections-v2.md), and
  [final approval](math-review-b/final-approval.json).
- Computation: [independent review](computation-review/review.md) and
  [resolved Section 8 pointer](computation-review/review-final-supplement.json).
- Source structure and PDF: [integration review](integration-review/review.md),
  [approved source and PDF manifest](integration-review/review-manifest.json),
  and [build and visual scope](integration-review/pdf-build-review.json).
- Reproduction provenance: [source receipt](checkpoint/source-checkpoint.json)
  and [clean-source comparison](clean-source/scientific-comparison.json).

The [copy manifest](evidence-copy-manifest.json) records the curated files
and omitted outer evidence. Frozen chapter copies, build caches, rendered
pages and earlier failed-build evidence remain in the workspace execution
directory; they have not been duplicated in Git. Archived reviewer scripts
may refer to that outer evidence. The maintained companion is the standalone
computational entry point.

Run `python -B docs/execution/normalization-review-2026-11-01/verify_checkpoint.py`
from a supported Python environment to verify the completed local checkpoint.
The verifier checks identities and provenance; it does not rerun the numerical
experiment, rebuild the PDF, or repeat its visual inspection. Its receipt is
written outside the checkout so that the final commit does not refer to itself.

The next substantive review covers Sections 12–14 and 16. The broader Section
15 analysis, missing original Airy/length-8192 evidence, remaining chapters,
optional-dependency coverage, full HTML/browser checks and publication
metadata/licensing retain their recorded limitations. Upload is the final
publication step; this checkpoint performs no remote operation.
