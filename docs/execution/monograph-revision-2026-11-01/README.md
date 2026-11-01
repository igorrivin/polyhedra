# Airy and torus revision checkpoint

This local increment corrects the computational-evidence descriptions in
Sections 15 and 30, supplies checked finite computations, and places upload
after manuscript revision and complete local release verification. The
[closeout](closeout.md) identifies the source, artifacts and remaining work.

The approved source commit is `cf34fcbcd0ee867a2dee974d9c952238bc5c6ce6`,
directly after `df952174e55f08a52596d912d9713a9d1e116313`. Its sixteen source
files match the independent review hashes.

| Deliverable | Verification and scope |
| --- | --- |
| [Section 15 companion](../../../experiments/section15/README.md) and [clean result](../../../artifacts/section15/checks.json) | 31 exact algebra checks; six Airy approximation rows at 80 and 120 digits. The original quantum-integral values remain unreplayed. |
| [Section 30 companion](../../../experiments/section30/README.md) and [clean result](../../../artifacts/section30/result.json) | New length-64 calculation: 1,104 modular and 1,127 asymmetric curves, checked against exact traces and independent numerical oracles. The original length-8192 report remains unreplayed. |
| [Working monograph PDF](../../../artifacts/monograph-revision-2026-11-01/monograph-working-draft.pdf) | 179 pages, 607 resolved labels and 126 bibliography entries. Twenty changed/adjacent pages were visually checked. This is the reviewed precommit PDF; its five TeX input hashes match the source commit. It was not rebuilt after committing. |

The [Airy review](scientific-review/airy-review.md),
[torus review](scientific-review/torus-review.md), and
[integration/PDF review](integration-review/independent-integration-review.md)
approve this bounded increment. They do not designate either entire chapter
or the whole monograph mathematically reviewed. The original proof blocks,
historical table rows and all 607 labels are preserved.

Both final computations ran from the clean source commit, with outputs first
written outside the checkout. Their scientific values match the approved
independent replays exactly; only explicit provenance and timing fields were
excluded from that comparison. See the
[comparison record](clean-source-scientific-comparison.json) and
[artifact manifest](candidate-artifact-manifest.json).

The [evidence inventory](evidence-copy-manifest.json) lists every byte-preserved
copy and the files retained only in the outer execution directory. Original
reports and manifests describe that full outer evidence tree. Large prior
torus result files, rendered PNGs, duplicate PDF/source snapshots and most
build products are not duplicated here. The one canonical final torus result
contains the full checked slope/trace/length list. The supplied source ZIP,
reference PDF, original repositories and older Section 9 artifacts are unchanged.

Run [the final verifier](final-postcommit-verification.py) after the artifact
commit. It writes a receipt outside the checkout to avoid a self-referential
committed HEAD record. The final artifact commit and integrity result are
recorded there.

Next is the normalization and hypothesis review of Sections 1–8. The exact
double-sine integral, original large torus run, broader mathematical review,
full dependency-enabled tests, full web edition, authorship and licensing
remain separate tasks. Existing Section 9 HTML and preview files are frozen
earlier checkpoints. No HTML was regenerated and no upload, deployment or
remote push was attempted in this increment.
