# Section 9 chapter build implementation and strict preview

Implementation and strict preview completed on 31 October 2026. No source
commit, staging, canonical generated artifact replacement, public upload, or
browser verification was performed by this agent. The source checkout is dirty
relative to `26b3c134d9308d345cb76f1240db9de982b2e5a6`; these are review artifacts,
not final release artifacts.

## Delivered source changes

- Section 9 was mechanically extracted to
  `book/chapters/09-volume-hessians.tex`. Before mathematical revision, expansion
  of the new input line reproduced the original monograph byte-for-byte and
  preserved all 601 original labels in order. See `mechanical-extraction.json`
  and `section9-original.tex`. The mathematics author subsequently owned and
  revised the chapter and narrow bibliography entries.
- `site/build_section9.py` implements a strict standard-library build: snapshot
  the complete local TeX include graph; compile the full monograph for numbering;
  extract preamble/bibliography; generate a standalone PDF; convert the complete
  chapter through Pandoc JSON to offline MathML; render original TikZ drawings;
  render and link the claim ledger and inspection evidence; create a complete
  monograph source ZIP; and record exact input/output hashes.
- `site/section9.css`, `site/README.md`, and the builder regression tests own the
  rendering layout, entry points, supported constructs and failure gates.
- `experiments/section9/run.py` now records the chapter hash, labels its single
  main-TeX download an inspection copy, supports optional actual chapter/source
  archive links, and offers `--render-result`. Rendering validates existing
  code/input identities and retains the original report's numerical provenance,
  dependency versions and computation timestamp. Detached default reproduction
  remains independent of monograph assets. Narrow experiment docs/tests updated.

## PDF authoring and conversion scope

The required existing PDF artifact marker ran successfully exactly once before
mechanical authoring: `--operation-kind create --expected-output-count 1
--output-format pdf`. It was not rerun. Canonical LaTeX is the appropriate source
format for this monograph. Full-book and cropped-figure PDFs are intermediate
validation inputs; the authored deliverable is the standalone chapter PDF.

The locally installed dvisvgm cannot read PDFs without its missing PDF backend.
Its native DVI probe reported ignored PostScript specials, so that incomplete SVG
path was rejected. Preserved logs: `dvisvgm-pdf-failure.log`,
`dvisvgm-dvi-tex-probe.log`, and `dvisvgm-dvi-incomplete.log`. The actual supported
path compiles unchanged TikZ into cropped PDF, then Ghostscript renders 240-dpi
PNG assets with dimensions and descriptive alt text. The chapter PDF retains
vector TikZ. Both generated PNGs were visually inspected and are complete.

The standalone PDF preserves Section 9, equations 9.1--9.15, propositions
9.1--9.2, and figures 3--4. External equations 16.7--16.8 are placed in an explicit
reference-only panel outside this chapter's proof review. Bibliography numbering
comes from the full monograph. The complete source ZIP contains the canonical
include graph, generated standalone wrapper, ledger, companion reconciliation,
and a payload/source manifest. Its source hashes and payload hashes were checked;
independent extracted builds are delegated to the code/artifact reviewer.

## Strict preview and focused verification

Strict preview directory: `/tmp/polyhedra-section9-build-v3`.

- Numerical report: `result.json`; all 12 tolerance checks and the exact finite
  fixture checks passed.
- Publishing tree: `site/section9/`; final render-only refresh added crosslinks
  after chapter generation. Stored result bytes were unchanged.
- Retained snapshot, logs, AST and all-page renders: `chapter-build/`.
- All required ledger evidence exists; this build omitted
  `--allow-pending-evidence` and reports no pending evidence.
- Full monograph compiled with 607 labels: the 601 baseline labels plus six
  subsection labels. All 26 chapter labels are present in the PDF and HTML.
- HTML contains 209 MathML expressions, two rendered figures, and 12 selected
  bibliography entries. Pandoc emitted no reader/writer warning or math fallback.
- Standalone PDF has 10 pages and zero overfull boxes. All pages were rendered.
  Parent visually inspected all ten v2 pages; every v3 page PNG is byte-identical
  to the corresponding approved v2 page. This comparison is render verification,
  not byte identity of the PDFs themselves (their build metadata differs).
- Eight builder integrity tests, six rendering provenance tests and the existing
  eleven variational tests pass. Logs are `chapter-build-tests.log`,
  `rendering-tests.log`, `variational-tests.log`.
- Detached replay extracted the numerical ZIP outside the repository and ran
  from `/tmp` with `/tmp/polyhedra-numerical-core-20261031/bin/python`. It passed;
  every mathematical report field outside provenance equals the source run.
  Detached Git status is unavailable, origin provenance is retained, all payload
  hashes match, and optional book assets are truthfully absent.
- `strict-preview-checks.py/.json` verifies identities after the final render-only
  refresh: current source inputs, all builder-owned outputs, explicit result,
  embedded companion report, downloaded fixture/result, numerical ZIP origin and
  payloads, complete source ZIP hashes, and local links in both HTML pages.
- `strict-preview-artifact-manifest.json` hashes the entire resulting publishing
  directory after the final refresh. It is separate from the builder's own
  `strict-preview-build-manifest.json`.

PDF preview hash and all-page comparison are in
`strict-preview-visual-comparison.json`. Contact sheet:
`/tmp/polyhedra-section9-build-v3/chapter-build/contact-sheet.png`.
Individual pages: `chapter-build/rendered-pages/page-001.png` through
`page-010.png`. Final clean-source generation must rerender and compare or inspect
its actual pages; the build manifest intentionally does not claim an automatic
visual review.

## Review fixes and remaining boundary

The rendering environment initially supplied requirements/README version strings
when packaging a stored report. Both implementer and independent reviewer found
this provenance defect. It is fixed by taking captured versions from the stored
report; a sentinel-version regression proves that a different rendering runtime
cannot rewrite the numerical environment claim. Additional review feedback added
current-export ZIP mapping for ledger site paths and strict existing-companion
identity checks, rather than trusting mere file existence.

Current final implementation hashes are recorded in `strict-preview-checks.json`:

- builder: `b02995dab6d0c1b7b9c5f700a12be0878481a8d372057339daeea40b41afff94`
- numerical driver: `91525e17669887d7863834a3322207088c7ff4dbf4b4f8348a67b529a6142a19`

Code/artifact review, a clean source commit, generation to temporary directories
from that clean commit, final artifact verification/copy, and an artifact commit
remain parent-owned release steps. Do not characterize this dirty-source preview
as final clean generation. No package implementation changed, so the broader test
suite was not rerun. Missing optional Gymnasium/Hypothesis/pynauty dependencies
remain the previously documented DNS blocker; no existing environment, system
installation, or user configuration was changed. Static HTML checks and PDF
visual inspection do not establish browser layout or public deployment.

Current documentation was fetched with Context7 for Pandoc, latexmk,
Ghostscript, dvisvgm, TikZ drivers, Python/pip setup during preflight, and Pillow
12.1.0 contact-sheet generation. Relevant primary documentation:
<https://pandoc.org/MANUAL.html>, <https://pandoc.org/lua-filters.html>,
<https://dvisvgm.de/Manpage>, <https://tikz.dev/drivers>, and the versioned Pillow
12.1.0 documentation. The CLI/API calls were then verified against installed
tools and actual outputs.
