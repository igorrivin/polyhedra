# Section 9 chapter checkpoint

Date: 31 October 2026. Baseline source commit:
`26b3c134d9308d345cb76f1240db9de982b2e5a6`.

The revised [Section 9](../../../book/chapters/09-volume-hessians.tex),
its [26-claim ledger](../../../book/claims/section9.json), the
[companion reconciliation](../../../book/companion-reconciliation.md) and
current book-status documents have passed an independent mathematical review.
The [final proof review](proof-review.md) and
[frozen identity manifest](proof-review-final-manifest.json) delimit that
approval. The [independent implementation review](build-review.md) also
approves the publishing source and strict preliminary artifacts. Final
generation from a clean source commit, verification and a fresh detached
numerical replay have now passed; the local artifacts are committed. No Site
or public book edition has been published.

## Final local artifacts

The source commit is `1bafb83d2ec152f1f8eac75b2be0e3c4b796198e`; the separately
verified artifact commit is `a69e47346209fff04c94062552af5400d3d5da05`.
Later documentation commits do not change the recorded computation origin.
The [closeout](closeout.md), [final generation checks](final-generation-checks.json),
[artifact manifest](final-artifact-manifest.json), and
[commit record](artifact-commit.json) identify the exact results and limits.

- [Complete chapter HTML](../../../site/section9/chapter.html) and
  [ten-page PDF](../../../site/section9/downloads/section9.pdf).
- [Full monograph LaTeX source ZIP](../../../site/section9/downloads/monograph-source.zip).
- [Worked computational companion](../../../site/section9/index.html),
  [numerical result](../../../artifacts/section9/result.json), and
  [detached reproduction ZIP](../../../site/section9/downloads/section9-reproduction.zip).

All twelve numerical checks and exact fixture identities pass in the fresh
source run and detached replay. Every final PDF page image matches the pages
visually inspected in the preview. The final source archive has the same
seven payloads that the independent reviewer extracted and compiled; its
origin manifest now records the clean source commit.

## Mathematical changes and evidence

The [core audit](math-audit.md) and [companion audit](companion-audit.md)
identified the corrections; the [author response matrix](chapter-revision.md)
maps each finding to the actual revised text. The later
[proof review](proof-review.md) independently checks the revised arguments,
external-theorem hypotheses and evidence statuses. Its earlier pending
dispositions and frozen revision snapshots are retained, followed by the
explicit final approval. This is a bounded Section 9 review, not formal
certification, a complete review of every cited proof, or an audit of the
remaining monograph.

The chapter now proves completeness of the disk angle coordinates and
grounded strictness, including zero Delaunay conductances; fixes the holonomy
orientation and boundary-response scope; and separates abstract angle
identities from geometric realization. It supplies the finite-iterate volume
gap `17m/(12t)` at Newton decrement at most `1/4`, an explicit short-step
schedule and a controlled inexact-solve estimate. Initial feasibility and
centering, arithmetic precision and geometric error retain separate costs.
The historical companion's exterior-angle Schläfli sign, closed versus
positive maximizer, and timing-cost qualifications are recorded without
editing the preserved historical manuscript.

The [revision checks](chapter-revision-checks.json) retain all 601 original
labels and the original ordered numbered environments; six subsection labels
were added. The ledger distinguishes written derivations, checked external
statements, conditional algorithmic consequences, exact finite identities,
numerical comparisons and open questions. It explicitly identifies the
unimplemented barrier solver, nearly-linear solver and peripheral geometry
work. The earlier numerical result does not supply those implementations.

| Record | Evidence and scope |
| --- | --- |
| [Mechanical extraction](mechanical-extraction.json) | Expanding the initial chapter input reproduced the original full source byte-for-byte before mathematical revision. |
| [Core exact checks](math-audit-checks.json) | Rational finite examples for disk/annulus dimension, signed boundary weights, forests and a non-SDD local tetrahedron Hessian. |
| [Companion diagnostics](companion_reference_probes.json) | Seeded binary64 triangle diagnostics and exact rational step constants; samples are not proofs of the general inequality. |
| [Independent constant checks](proof-review-checks.json) | Separately derived exact short-step, finite-center and inexact-step constants. |
| [Final reviewed identities](proof-review-final-manifest.json) | Actual chapter, final ledger, current-document and reviewer-evidence hashes, including the status-only final ledger update. |

## Publishing-build evidence and remaining gates

The [read-only preflight](build-preflight.md) preserved a failed naive
conversion: four math fallbacks, missing equation anchors, unresolved
citations and absent TikZ images despite successful tool exit codes. Its
diagnostic HTML and AST are evidence files, not publication assets. The
mechanical-extraction record later records the PDF-operation marker being
executed once; the earlier preflight's “not executed” status is historical.

The [initial complete preview manifest](preview-build-manifest.json) records
a ten-page standalone chapter, 209 MathML expressions, two rendered figures,
authoritative label/citation mappings and no overfull boxes in the full-book
or chapter build. The [preview visual review](preview-visual-review.json)
records inspection of all ten PDF pages without clipping or collisions.
The two Section 16 formulas appear in an explicit reference-only panel;
their proofs remain outside the Section 9 review. Failed PDF/DVI-to-SVG
probes are preserved in the `dvisvgm-*` logs; the successful HTML preview
uses cropped 240-dpi PNGs, while the PDF retains vector TikZ.

That initial preview allowed the then-pending canonical evidence copies.
The numerical driver was subsequently corrected during review to preserve
stored dependency versions when rendering an existing report; the original
and corrected probes are retained separately. The later
[strict preview](strict-preview-build-manifest.json) requires all ledger
evidence, reports no pending files and identifies the corrected source bytes.
Its [checks](strict-preview-checks.json),
[complete artifact manifest](strict-preview-artifact-manifest.json) and
[all-page comparison](strict-preview-visual-comparison.json) record current
source/output identities, successful numerical and detached replays, unchanged
stored-result bytes after render-only refresh, and ten page images identical
to the visually reviewed preview. Both preview stages originated in a
modified checkout; neither is relabelled as a clean-source release run.

The [implementation report](build-implementation.md) and
[focused test results](focused-test-results.json) record eight builder
integrity tests, six rendering/provenance tests and eleven existing variational
tests passing. The independent reviewer repeated these focused checks,
reproduced and rechecked the environment-attribution correction, and verified
the exported PDF's internal and local-download links. The review preserves
one checker-only expectation correction separately from product findings.
Its [artifact checks](build-review-artifact-checks.json) and
[extracted-source builds](build-review-extracted-builds.json) verify the
seven-payload source archive outside the checkout: the full entry point builds
to 177 pages with 607 labels, and the chapter entry point builds to ten pages
with 28 labels. Neither build reads the original checkout, and both converge
without unresolved citations/references or overfull boxes. This full-book
build does not extend the proof review beyond Section 9.

The [chapter build guide](../../../site/README.md) owns the actual build
commands. Implementation review, focused regressions, source-archive
extraction/build, detached numerical replay and preview PDF/download
validation have now passed for the identified source and preview hashes.
The [final generation record](final-generation-run.json) now records the later
clean-source execution in temporary directories, and the
[final checks](final-generation-checks.json) and [copy manifest](final-copy-manifest.json)
verify the actual committed artifacts. Static HTML checks and PDF raster review do not establish browser
interaction or desktop/mobile layout behavior. The earlier browser/server
policy denials were not retried or worked around in this checkpoint.

## Dependencies and earlier numerical status

The [dependency record](dependency-download.json) preserves the single
ordinary download attempt and its [log](dependency-download.log). No wheel
was downloaded. The separate `pypi.org` lookup failed with DNS error 8;
the bounded local search found no Gymnasium, Hypothesis or pynauty.
No environment was mutated and the unchanged full suite was not rerun.
The prior numerical checkpoint's 393 passes, 18 skips, four failures and
nine collection errors remain the latest full-suite result, not a new result
of this chapter revision. See the
[numerical closeout](../numerical-correctness-2026-10-31/closeout.md).

The maintained [Section 9 experiment](../../../experiments/section9/README.md)
provides exact grid/forest/Schur identities and twelve numerical checks. The
strict-preview numerical run and separately extracted replay passed, with
all mathematical result fields equal outside provenance. The later
[clean-source result](../../../artifacts/section9/result.json) and
[fresh detached replay](final-detached-result.json) independently identify
their execution states and retain that same mathematical agreement. A render-only
refresh retains the existing result's original numerical provenance and is
not a fresh computation.

## Archival integrity and replay scope

[evidence-copy-manifest.json](evidence-copy-manifest.json) inventories the
byte-identical copies from the outer execution directory and verifies the
author/reviewer frozen hashes. Original raw evidence, failed probes and
pending revision stages were not rewritten to look like final success.
Some raw TeX snapshots and compiler logs retain original trailing whitespace
or blank final lines; those exact archival exceptions are listed in the
manifest. They are not newly authored implementation formatting.
The [source staging record](source-staging-verification.json) and
[artifact staging record](artifact-staging-verification.json) preserve the
exact accepted diagnostics, including the generated HTML's single-space blank
line already present in the reviewed preview. No unexpected whitespace finding
was accepted, and these records do not claim an unqualified whitespace pass.

The copied diagnostic scripts are inspection evidence of the recorded runs.
`math-audit-checks.py` and `proof-review-checks.py` use the standard library
and write JSON beside their own files. `companion_reference_probes.py`
additionally assumes its original outer `execution/<checkpoint>/` layout,
locates a sibling `consolidated` checkout and reads the pinned baseline with
Git. Its copy in this documentation directory is not a portable entry point;
no path adapter or independent replay is claimed by copying it.
`strict-preview-checks.py` and the `build-review-*` probes also retain their
recorded workspace/temporary-directory assumptions. Their successful
recorded executions are distinct from portability of these archived copies.
The final generation/check scripts similarly pin this local checkpoint and
are inspection records; use the maintained build guide for reusable commands.
The source snapshots are likewise archival inputs, not alternate maintained
chapters.

The supplied reference PDF, original archive, historical companion and prior
checkpoint evidence remain separate, unchanged records. Missing Airy/torus
evidence, broader mathematical review, publication licensing/credit and
deployment remain tracked in the [integration plan](../../../INTEGRATION_PLAN.md).
