# Local publishing builds

The complete local working edition is built by `build_book.py`; its workflow is
described at the end of this document. The earlier Section 9 files and preview
remain frozen checkpoints with their own source, numerical and review records.

## Section 9 publishing build

`build_section9.py` owns the complete chapter conversion. Canonical mathematical
text remains in `book/chapters/09-volume-hessians.tex`; the full monograph includes
that file. The builder does not edit either source. It derives the standalone
preamble and bibliography from the full monograph, compiles the complete book
for authoritative labels, and checks the excerpt against those numbers.

The published directory contains `chapter.html`, the authored grid companion
`index.html`, the separate `barrier.html`, and local assets/downloads. The chapter includes all prose,
proofs, mathematical displays, both figures, selected bibliography, and the claim
ledger. The two Section 16 equations are explicitly marked reference-only and
outside this chapter's proof review. The claim ledger is not an automatic proof
certificate. No public upload or browser verification is performed by this tool.

## Build prerequisites

The chapter builder uses Python 3.12 or newer and only the Python standard
library. Install a normal TeX Live distribution with `latexmk`, `pdflatex`,
TikZ, `preview`, and the packages already named in the canonical preamble;
Pandoc with its JSON reader/writer and offline MathML support; and Ghostscript.
The tested local tools were TeX Live 2025, latexmk 4.86a, Pandoc 3.12.1 and
Ghostscript 10.04.0. Tool versions are captured in every build record.

TikZ is compiled from its unchanged source into cropped intermediate PDFs.
Ghostscript renders 240-dpi PNGs for HTML, with explicit dimensions and descriptive
alternative text. The chapter PDF retains vector TikZ. This pipeline does not
require Poppler, dvisvgm, a CDN, a browser, or a local web server. The tested
dvisvgm installation lacked a working PDF backend; DVI conversion reported
ignored PostScript specials and was rejected. No incomplete SVG is distributed.

Numerical reproduction separately requires a supported Python environment with
the toolkit or `PYTHONPATH=packages/volume-toolkit`, NumPy, SciPy and mpmath. See
the [experiment guide](../experiments/section9/README.md).

## Clean source generation

Review and commit sources first. Keep all generation outside the checkout so
all generators observe the same clean source commit. From the repository root,
using the supported Python environment:

```sh
PYTHONPATH=packages/volume-toolkit python experiments/section9/run.py \
  --output /tmp/section9-release/result.json \
  --site-dir /tmp/section9-release/site/section9

PYTHONPATH=packages/volume-toolkit python experiments/section9/barrier_run.py \
  --output /tmp/section9-release/barrier-result.json \
  --site-dir /tmp/section9-release/site/section9

python site/build_section9.py \
  --output-dir /tmp/section9-release/site/section9 \
  --computation-result /tmp/section9-release/result.json \
  --barrier-result /tmp/section9-release/barrier-result.json \
  --work-dir /tmp/section9-release/chapter-build

PYTHONPATH=packages/volume-toolkit python experiments/section9/run.py \
  --render-result /tmp/section9-release/result.json \
  --site-dir /tmp/section9-release/site/section9 \
  --chapter-page /tmp/section9-release/site/section9/chapter.html \
  --book-source-archive /tmp/section9-release/site/section9/downloads/monograph-source.zip

PYTHONPATH=packages/volume-toolkit python experiments/section9/barrier_run.py \
  --render-result /tmp/section9-release/barrier-result.json \
  --site-dir /tmp/section9-release/site/section9 \
  --chapter-page /tmp/section9-release/site/section9/chapter.html
```

The two `--render-result` commands only render existing reports. They validate current source
and fixture identities before creating their reproduction bundles and preserve
each report's original computation timestamp, numerical values, dependency
versions and provenance. The chapter tool receives both actual fresh result
paths explicitly and records their paths and SHA-256 values. The barrier input
is required when the current chapter or ledger references that example; an old
canonical result is never silently attached instead.

The builder rejects unresolved labels/citations, unknown raw TeX, MathML
fallback warnings, lost figures, inconsistent equation/bibliography numbers,
missing/external/cyclic source includes, broken local downloads, missing claim
evidence, and sources changed during a build. It supports only the chapter's
explicitly handled TeX constructs; add a regression test before extending the
converter. Presentation-only translation of `\rm`, `\hbox`, alignment numbering
and label commands never changes canonical proof text.
The existing computational companion must also match the explicit result:
the embedded HTML report, downloaded result/fixture, ZIP origin and payload
hashes are checked before a chapter is built.
For the barrier companion these checks also require the six computational
source roles and chapter hash to match the current source snapshot. All ZIP
payloads must be manifested without duplicate or external paths. The barrier
page and download bytes are frozen as build inputs and rechecked at completion.

All ledger paths become labeled inspection downloads inside the exported
directory; primary source URLs remain external citations. Missing current audit
reports can be displayed as pending only with `--allow-pending-evidence`, which
marks a preliminary preview. Final builds must omit that option. The original
ledger retains repository-relative ownership paths.

Inspect every PNG under `chapter-build/rendered-pages/` after building. The
manifest records rendering completion, not a completed visual inspection.
Perform an independent code/artifact review and record that review separately.
Static HTML integrity checks are not browser layout checks. Only after all
generators and reviews pass should the approved `result.json`,
`barrier-result.json` and complete
`site/section9` output directory be copied into their canonical locations in a
separate artifact commit. A final artifact manifest must hash the files after
the last render-only step; the chapter build record describes its own outputs.
Its barrier asset hashes describe inputs at chapter-build time. A subsequent
render-only refresh can add the optional chapter backlink to `barrier.html`;
the final post-refresh manifest owns that page's final bytes. Neither refresh
changes either numerical result or its computation provenance.

## Source archive and ownership

`downloads/monograph-source.zip` contains the complete local TeX include graph,
the generated `book/section9.tex` wrapper, the canonical chapter/ledger, the
companion reconciliation document, and a source manifest. Extract it and run
`latexmk -norc -pdf main.tex` or `latexmk -norc -pdf section9.tex` from `book/`.
Repository-relative links in canonical source are preserved. The distributed
chapter PDF uses a temporary copy with only hyperlink targets rewritten to the
adjacent supplied downloads. The numerical subset ZIP remains independently
reproducible and does not require these monograph assets.

- `build_section9.py`: source graph, PDF/HTML conversion, references, ledger,
  source archive, provenance, strict gates, and all-page PDF rasterization.
- `section9.css`: local reading layout; no external font or script dependency.
- `tests/test_build_section9.py`: strict converter and integrity regressions.
- `../experiments/section9/run.py`: numerical execution and identity-checked
  render-only companion; it does not duplicate the source-graph builder.
- `../experiments/section9/barrier_run.py`: fixed-fixture dense barrier
  experiments, independent references, numerical traces, and a separate
  detached reproduction bundle.

Focused checks:

```sh
python -m unittest discover -s site/tests -v
PYTHONPATH=packages/volume-toolkit python -m unittest discover -s experiments/section9/tests -v
PYTHONPATH=packages/volume-toolkit python -m pytest packages/volume-toolkit/tests/test_variational.py
```

## Reading preview export

`build_preview.py` owns the buildless reading frontend for the reviewed Section 9
edition. It consumes the exact 44 site assets and two numerical reports in the
barrier checkpoint's `final-artifact-manifest.json`. Changed, missing or extra
canonical assets are rejected. It neither reruns the numerical experiments nor
converts or edits the PDF. A later scientific edition needs a separately reviewed
input checkpoint before this exporter can adopt it.

The exporter adds a landing page, the six canonical subsection links, local
passage search, and a shared navigation bar in the three derived HTML pages.
Removing the two explicitly marked navigation/style insertions recovers each
original HTML byte for byte. The PDF, numerical records, code, figures and ZIPs
are copied unchanged. The output manifest separates the current research/build
commit from the earlier numerical source commit, records every input/output hash,
and describes this as a presentation export, not a new computation or proof review.

The search index is generated from the chapter and both companions, omitting
scripts, navigation and duplicate TeX annotations. It is both downloadable and
embedded with HTML-safe JSON escaping. The deferred classic script searches that
embedded data without a fetch, external dependency, or numerical backend; a local
file opening therefore does not depend on module or fetch permissions. Browser
rendering and interaction still require their own verification.

Generate into a derived publishing checkout outside this canonical research repo:

```sh
python site/build_preview.py \
  --output-dir ../publishing/polyhedra-reading-preview-20261101/dist \
  --require-clean
node site/tests/test_preview_search.cjs \
  ../publishing/polyhedra-reading-preview-20261101/dist/search-index.json
```

Omit `--require-clean` only for an explicitly recorded author preview. The builder
refuses symlinks, foreign files and modified prior output when refreshing an
existing export. Only header-recognized AppleDouble or Finder metadata is omitted
from its asset inventory; unknown files with metadata-like names are rejected.
The final packaging step must exclude those recognized platform sidecars too.
It does not initialize Git, set Site identity, handle credentials,
push source, or deploy. The Sites owner manages `.openai/hosting.json` and the
official source/package/publication workflow in the derived checkout. Never run
that source helper at the canonical research root. Registration, local packaging,
source synchronization and deployment success are distinct states.
The maintained `preview/source.gitignore` is copied to the publishing checkout's
root. Its archive patterns apply only to that root, so the reproduction ZIPs
under `dist/` remain tracked; Site identity is not ignored.

`preview/` contains the maintained landing template, stylesheet and browser-local
search code. `tests/test_build_preview.py` checks byte preservation, safe output
ownership, source mismatch rejection, safe embedded JSON and local targets;
`tests/test_preview_search.cjs` checks search behavior and actual edition queries.
No browser/server is started by these checks. The scope remains a Section 9
working edition, while the complete LaTeX download is explicitly the broader draft.

## Complete local working edition

`build_book.py` converts the active canonical TeX graph into separate reading
pages: an introduction, 32 numbered chapters, Appendices A/B, and the complete
bibliography. A contents page preserves the authored part summaries and adds
browser-local passage search. Previous/next links, page contents, and a complete
label-to-page map connect the edition. The HTML uses native MathML and local
assets; no CDN, network API, framework installation or numerical backend is
required. The visible byline, affiliation and HTML metadata come from the
canonical TeX author declaration. The canonical introduction, including its
acknowledgment, is retained as body content.

The converter reuses the source graph, compiled-label reader and integrity
helpers from `build_section9.py`, and the safe inventory and search primitives
from `build_preview.py`. It does not modify their behavior or regenerate the
frozen Section 9 files. Its full-book extensions explicitly handle shared
theorem/remark/question numbering, multi-label alignment rows, appendices,
paragraph headings, all eight tables and all nine TikZ figures. Alignment row
numbers come from the compiled auxiliary labels and are attached to the
corresponding MathML rows. Unknown raw TeX and every Pandoc warning/fallback
remain fatal. A presentation-only `\hspace` normalization fixes the known
Section 15 MathML limitation without changing canonical source.
Every active source input and body region must be routed or explicitly rejected.
Unexpected inter-chapter prose, nested inputs, wrapper content and unexplained
bibliography content fail the build instead of disappearing. Numbered ordinary
equations require canonical labels; unsupported unlabeled numbering is rejected.

Use the existing supported Python 3.12 environment and installed Pandoc, TeX
Live/latexmk and Ghostscript. The builder creates a fresh full-book PDF and
renders each unchanged TikZ drawing into a local PNG. All source and generated
work must be outside the research checkout, in two separate directories:

```sh
/tmp/polyhedra-baseline-20261031/bin/python site/build_book.py \
  --output-dir ../execution/editorial-local-release-2026-11-02/licensed-edition-dist \
  --work-dir ../execution/editorial-local-release-2026-11-02/licensed-edition-build \
  --require-clean
/opt/homebrew/bin/node site/tests/test_book_search.cjs \
  ../execution/editorial-local-release-2026-11-02/licensed-edition-dist/search-index.json
```

Omit `--require-clean` only for an explicitly identified author preview. A final
generation follows independent source review and uses the resulting clean
checkout. Source bytes are frozen before conversion and rechecked at the end.
PDF visual inspection and browser rendering, navigation, keyboard use and
search checks are separate verification steps; a successful static build does
not claim those checks. The builder starts no server and makes no browser,
Site-registration, credential, source-synchronization, upload or deployment
calls. Existing Site identity and audience remain untouched.

Every invocation uses a new empty scratch directory and freshly compiles the
frozen source. There is no supplied-PDF, auxiliary-file or compilation-receipt
reuse option. The compilation receipt records this invocation's actual outputs;
it is evidence output rather than a trusted input shortcut. Output and scratch
paths are normalized before containment and overlap checks, with symlink aliases
rejected. Existing output must match its ownership manifest; foreign files and
modified exports are refused. The build is staged and replaces a prior export
only after all static checks pass.

The complete PDF and exact 36-file active TeX source graph are downloadable.
The source ZIP also carries the exact `LICENSES/README.md` scope map,
`MONOGRAPH-NOTICE.md`, full `CC-BY-4.0.txt`, `new-companions-MIT.txt` and retained
`volume-toolkit-MIT.txt` terms, and the `new-companion-files.txt` covered-file list.
The exact `packages/volume-toolkit/LICENSE` notice keeps the scope map's package
notice link complete inside the source ZIP.
Its source manifest hashes the TeX and licensing inputs separately. The same
seven licensing files are distributed in the inspection tree, preserving the
original notice for the selected toolkit source files.
`book/downloads.json` is an explicit inspection allowlist for existing
classified reports, their guides, selected source files and claim ledgers.
Selected source files are for inspection, not newly advertised standalone
reproduction packages. The computation index keeps finite scope, original
source identities and known limits visible; it never replays a campaign or
claims a missing historical evaluator was recovered. Private holdouts and
unclassified research outputs are excluded. The monograph text, original
figures and TeX source use CC BY 4.0. New maintained computational companion
files explicitly listed in `LICENSES/new-companion-files.txt` use MIT. The
scope map preserves third-party rights and inherited licenses; these grants
do not assign one license to historical archives or recorded result evidence.

The 44 original Section 9 site assets are copied byte-for-byte under
`historical-section9/`. Their older PDF, source archive and numerical records
remain explicitly historical. The complete edition's manifest separately
records current source and tool identities, every selected input and output
hash, historical input hashes, PDF/auxiliary/figure provenance, label and
bibliography maps, and static verification counts. No old result's timestamp,
source record, dirty-state field, numerical value or precision record is
rewritten.

Focused regressions and the existing site suite:

```sh
/tmp/polyhedra-baseline-20261031/bin/python -m unittest discover -s site/tests -v
/opt/homebrew/bin/node site/tests/test_book_search.cjs
```
# Public repository links

The public monograph is at https://polyhedra.dimensionreducers.ai and its computational repository is https://github.com/igorrivin/polyhedra. The [publication guide](../docs/publication.md) describes the exact-commit links, release archive, and PDF annotations.

After generating a complete local edition, `link_repository.py` produces a separate linked public edition. It preserves the original build manifest and scientific files, validates every repository target, and adds `downloads/repository-link-manifest.json`. The final run requires a clean source commit and an output directory outside this checkout. Configuration and the nine companion recipes are in `book/repository.json`.

```sh
python -m pip install pymupdf
python site/link_repository.py --source site/book-edition --output /tmp/polyhedra-linked --ref HEAD
```

The earlier builder and preview instructions below describe their original local stages. The linking step does not rerun their mathematical conversion or any scientific campaign.
