# Independent integration and PDF review

The bounded Section 15/30 source increment is approved. No unresolved
structural, publication-order, preservation, source-label or inspected-page
layout finding remains. This approval is tied to the sixteen source hashes
in `final-integration-review.json`, not to a future modified checkout.

## Independent checks

- The pre-revision section extraction reconstructs baseline `df952174` byte
  for byte. All 607 labels remain unique and in their original order.
- All 1,056 baseline inventory entries were independently checked against
  Git blob data or their 412 LFS pointer hashes and sizes. In the final
  tree, 1,053 retain their bytes; the three intended changes are the main
  source, book README and computational-status ledger.
- The original repositories retain both recorded heads and all 953 tracked
  file hashes and lengths. The supplied source archive retains its hash.
  Existing Section 9 science, site exports and the reference PDF are unchanged.
- The existing source-graph reader resolves the five TeX files without
  modification. All 25 existing site/build tests passed. The script invocations
  and their outputs are retained beside this report.
- The four shared documents preserve the distinction between exact finite
  checks, multiprecision comparisons, inherited analytic assertions and
  unreplayed historical numbers. The Section 9 status block is unchanged.
- All six Airy table rows and all four historical torus rows retain their
  exact printed data. The replacement torus table is separately identified.
- The revised plan puts local generation and complete local release checks
  before final upload/deployment, while retaining a deployed access/smoke check
  within that final publication step.
- The 109 shared-document local link occurrences comprise 103 existing paths
  and six references to three expected final-generation targets: the new
  checkpoint README and the two canonical result JSON files. These targets
  are pending and must be checked after clean result generation; they are not
  claimed available by this source-stage review.
- `git diff --check` and explicit whitespace checks of the sixteen authored
  source files passed. The two experiment drivers use Git subprocesses only
  for read-only provenance; no remote execution, upload or silent
  certification path was found in this integration scope.

## PDF build and visual inspection

The required PDF-operation marker ran successfully once immediately before
the first PDF build. The build used a frozen copy of the five TeX sources
and the repository's established `latexmk` flags, with shell escape disabled.
It did not regenerate any existing scientific or site artifact.

The resulting working manuscript has 179 pages, 607 compiled labels and
126 bibliography entries. There are no unresolved or duplicate references
or citations and no overfull boxes. The build log retains the single
underfull-box warning; no corresponding clipping or overlap was observed.

PDF SHA-256:
`44e428ddbc625231f483748a9bfce914b4d4fc987a0c34b6201003e6dc87cacd`.

Ghostscript rendered pages 68–75 and 155–166 at 120 dpi because Poppler is
unavailable. All twenty images were actually viewed, covering both complete
revised sections and adjacent text. Tables, equations, the existing figure,
computational paths, section transitions and page numbering are legible and
contained within the page. No overlap, clipping, broken symbols or table
splitting was observed. `pdf-build-review.json` records every rendered hash;
`final-integration-review.json` records the completed visual review.

This is a precommit build of the recorded source hashes. The other 159 pages
were not visually reviewed in this pass. Compilation and this visual check
do not constitute a full-book mathematical review, browser QA, publication,
an exact quantum-integral replay or the original length-8192 torus campaign.
Clean numerical generation, final evidence packaging and postcommit checks
remain separate completion gates for the parent task.
