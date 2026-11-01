# Counting and mixing structural extraction

This is the frozen structural gate for Sections 23–31 at canonical baseline
`9c8b61790aaa674902b9d60e80122c318a578bcc`. Eight sections were extracted into
`book/chapters/23-trace-coefficients.tex`, `24-quantitative-counting.tex`,
`25-global-coefficient-filters.tex`, `26-counting-to-mixing.tex`,
`27-weighted-mixing-converse.tex`, `28-genus-two-model.tex`,
`29-controlled-observables.tex`, and `31-arithmetic-remainder.tex`.
The main manuscript now inputs those exact byte slices. The part headings stay
in the main manuscript; the existing Section 30 chapter remains byte-identical.

The recursive expanded manuscript before and after extraction has SHA-256
`64b039ffba8802c7f2a52784f216298a4e65a43e4594cd24b8f3b76fb1aee1ed`.
Expansion from `book/main.tex`, which additionally retains its entry-point
comment, has SHA-256
`c1772c08cc60cd2b3045ff2600322ab91089b30c8cc7a968475eff56a85073d7`.
Both comparisons are exact byte equality, with all 607 unique labels and 129
unique bibliography items retained in their original order. All 32 numbered
sections, including the nine sections numbered 23–31, retain their titles and
section-label mapping.

`structure-manifest.json` binds the 18-file baseline active TeX graph and the
26-file extracted graph, every section's labels, and the exact nine changed or
new source hashes. `baseline-source-graph/` and `extracted-source-graph/` contain
full frozen snapshots. `baseline-tracked-inventory.json` binds all 1,914 prior
tracked files to Git blobs, with all 412 materialized LFS objects verified against
their recorded identities. The post-extraction check found precisely the main
source changed among those files; the other 1,913 prior files were byte-identical.
The only new canonical files were the eight chapters above. The index and HEAD
were unchanged, and `git diff --check` passed.

Replay the frozen evidence without writing to the canonical repository:

```sh
python3 /Volumes/Lexar/lambda/devel/polyhedra/execution/counting-mixing-review-2026-11-01/structure/extract_chapters.py --verify-only
```

`verification.json` records the successful immediate replay, including agreement
with the live graph before mathematical revision. `commands.json` records that
command, its exit code, the exact Git status, and the whitespace check. The
verifier continues to check the frozen extraction after authors revise chapters;
its live-source comparison is then informational rather than a new claim of
source equivalence.

This gate concerns source preservation only. No mathematics, numerical evidence,
PDF, marker, canonical artifact, commit, or publication operation was produced.
The algebra and dynamics authors were told to wait for the root agent's
independent structural approval before editing their chapters.
