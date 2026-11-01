# Section 9 chapter: build and dependency preflight

The local machine has a usable TeX/Pandoc toolchain. The missing test
dependencies remain unavailable. This is a read-only source and environment
preflight, not a new PDF build, mathematical review, browser check, or final
chapter conversion. Repository HEAD was `26b3c134d9308d345cb76f1240db9de982b2e5a6`;
the checkout remained clean. No existing environment, original repository,
product source, canonical manuscript, Git index, or commit was changed.

## Available build tools

| Tool | Observed installation |
| --- | --- |
| latexmk | `/Library/TeX/texbin/latexmk`, 4.86a |
| pdfLaTeX, XeLaTeX, LuaLaTeX | `/Library/TeX/texbin/`; pdfTeX 1.40.27, TeX Live 2025 |
| Pandoc | `/opt/homebrew/bin/pandoc`, 3.12.1, Lua support |
| Ghostscript | `/usr/local/bin/gs`, 10.04.0 |
| Node | `/opt/homebrew/bin/node`; exact version in `build-preflight.json` |
| pypdf | Available in `/tmp/polyhedra-baseline-20261031/bin/python` and Anaconda Python 3.12 |
| ReportLab | Available in `/opt/anaconda3/bin/python` |

`tikz.sty`, `lmodern.sty`, and `xr-hyper.sty` resolve in TeX Live 2025. The
ordinary PATH and the checked Homebrew/Anaconda/`/usr/local` paths do not
provide Poppler's `pdftoppm`, `pdfinfo`, or `pdftotext`. Ghostscript is the
available PDF-to-PNG rendering alternative, but no page rasterization was
performed during this bounded preflight. The supplied PDF has 174 pages;
its outline places Section 9 at PDF page 27. The reference PDF's metadata
records an earlier TeX Live 2023/Debian build, not this machine's toolchain.

The mandatory PDF-operation marker exists at:

```text
/Users/igorrivin/.codex/plugins/cache/openai-primary-runtime/pdf/26.1026.10807/skills/pdf/container_tools/mark_artifact_operation_started.mjs
```

It has been read and hashed, **not executed**. Immediately before the first
actual PDF authoring command, the authoring worker must run this existing
script once with `--operation-kind create --expected-output-count 1
--output-format pdf` (adjust the count if the final task creates multiple
PDFs). No substitute marker is necessary. This preflight produced diagnostic
HTML/AST files only, not a PDF.

## Actual conversion probe

The current Section 9 is 482 source lines and 23,169 UTF-8 bytes. It contains
20 labels, 14 `equation` environments, one `align`, two propositions, two
proofs, and two inline TikZ figures. Its ten distinct citation keys are
`BoydVandenberghe`, `BrockMappingTori`, `BrockWPVolumes`, `DisarloParlier`,
`DuffinNetworks`, `FuterGueritaud`, `IpolyStudy`, `RippaEnergy`,
`RivinEuclidean`, and `SpielmanTengSolvers`. The only references outside the
chapter are `eq:cuspHessian` and `eq:cuspmatrixHessian`.

A temporary, unedited excerpt combined the existing preamble, Section 9 and
`setcounter{section}{8}`. Pandoc converted it to JSON and standalone HTML.
Both processes returned zero, but the naive HTML is **not acceptable**:

- The AST contains 113 math nodes; only 109 become MathML. Four formulas
  produce explicit fallback warnings and remain literal TeX:
  `eq:ipolyBoundaryResponse` (the `align`/`notag` syntax), `eq:ipolySchur`
  and `eq:ipolyGaussian` (`\rm eff`), and `eq:ipolyStepBound` (`\hbox`).
- All 15 equation label IDs are absent from HTML, although the label text
  remains available inside math strings. Section, proposition and figure
  identifiers survive. Equation anchors and displayed reference numbers
  therefore require explicit handling.
- The AST retains two figure records and their captions but contains no
  `Image` node: the inline TikZ drawings have disappeared in this naive
  conversion. A figure count alone would miss this loss.
- Ten `Cite` nodes contain raw LaTeX citation fallback; the excerpt has no
  resolved bibliography. Citation handling must preserve the chapter's keys,
  locators and references, not merely suppress warnings.
- Pandoc 3.12.1 warns that `--mathml` is deprecated; the documented spelling
  for the implementation is `--math-method=mathml`.

The complete AST, fallback log, source excerpt and diagnostic HTML are
preserved as `pandoc-preflight-ast.json`, `pandoc-html-preflight.log`,
`pandoc-preflight-excerpt.tex`, and `pandoc-preflight-diagnostic.html`.
`pandoc-preflight.json` records exact commands, source/excerpt hashes, all
node counts, reference-link nodes, figure payloads and missing IDs. These
files are diagnostic evidence, not publication assets.

## Recommended bounded build design

Extract only Section 9 to its canonical chapter input and replace the full
source block with `\input`; preserve the existing labels and mathematical
numbering conventions. A standalone wrapper should use section counter 8,
the shared preamble, and a consistent bibliography/reference mapping.
The full book build supplies authoritative equation/proposition/figure
numbers and the two external reference targets. Verify numbering against
its `.aux` data rather than assuming Pandoc reads LaTeX counters identically.

For HTML, use the structured Pandoc AST with explicit label/reference and
citation mappings. Use `latex+raw_tex` when retaining raw TikZ for a filter,
or replace the two designated figures by separately built images. The
official Pandoc Lua-filter example compiles TikZ with pdfLaTeX and converts
the PDF to SVG with `pdf2svg`; availability of that SVG converter was not
verified here. Ghostscript provides a PNG alternative if required. Preserve
the figures' labels and captions and verify actual image content, not only
the figure nodes.

A renderer-only syntax translation may handle equivalent math spellings;
it must not modify canonical mathematics merely to satisfy the converter.
Require zero math fallbacks, no unexplained dropped raw TeX, all chapter
labels and cited keys resolved, both images present, and explicit external
reference links. PDF pages must then be rendered and visually inspected.
The old local-server/browser-file-URL policy denials were not retried or
worked around; static conversion and document rasterization are distinct
from a browser-layout approval.

Modularization also affects `experiments/section9/run.py`: its existing
single-file TeX download and `book.tex` hash no longer describe all source
dependencies. The implementation must include the chapter and shared inputs
in provenance and provide a complete source archive, or clearly identify
individual files as inspection copies. Do not make the current download
look like a standalone compiling manuscript when it requires omitted inputs.

## Optional test dependencies

Targeted searches checked the local pip and uv caches, uv tool environments,
Homebrew packages, Anaconda Python, the existing baseline, and discovered
project virtual environments under `/Users/igorrivin/devel` and
`/Volumes/Lexar/lambda/devel`. No Gymnasium, Hypothesis or pynauty install or
wheel was found. The checked additional dependency names `cma`,
`stable_baselines3`, `sortedcontainers`, and `farama_notifications` were also
absent. This is a bounded search, not an assertion about every file on every
attached volume.

One normal `pip download` attempt, using the supported Python 3.12.11
baseline interpreter and a new empty temporary destination, requested
Gymnasium, Hypothesis and pynauty with zero retries and a 12-second network
timeout. It returned 1, reported no matching Gymnasium distribution and
downloaded no files. A separate DNS check for `pypi.org` failed with
`gaierror: [Errno 8] nodename nor servname provided, or not known`.
`dependency-download.json` and `.log` preserve the exact command and output.
No relevant PIP environment override was present in the checked variables.

No new test environment was created because the missing dependencies could
not be supplied, and no unchanged failing suite was redundantly rerun. The
prior 393 passes, 18 skips, four failures and nine collection errors remain
the latest full-suite result; this preflight does not upgrade that result.
When the dependencies are available, use a newly created Python 3.12
environment, preserve or explicitly resolve its dependency versions, confirm
that imports target the maintained checkout, rerun blocked tests first, then
the full suite. Resolve any newly exposed failures on their evidence; missing
Gymnasium can hide downstream import requirements.

## Documentation and evidence

Current documentation was fetched with Context7, using resolve-library-id
before query-docs: [pip offline installation](https://pip.pypa.io/en/stable/user_guide/),
[pip download](https://pip.pypa.io/en/stable/cli/pip_download/),
[Python venv](https://github.com/python/cpython/blob/main/Doc/library/venv.rst),
[Pandoc manual](https://github.com/jgm/pandoc/blob/main/MANUAL.txt),
[Pandoc Lua filters](https://github.com/jgm/pandoc/blob/main/doc/lua-filters.md),
[Pandoc label/reference tests](https://github.com/jgm/pandoc/blob/main/test/command/refs.md),
[Ghostscript rendering](https://github.com/artifexsoftware/ghostpdl/blob/master/doc/src/Use.rst),
and [latexmk output directories](https://github.com/debian-tex/latexmk/blob/master/_autodocs/api-reference/files-and-directories.md).

`build-preflight.json` records observed tool versions, marker hash, checked
paths, environment limits, documentation URLs and hashes/sizes of the
diagnostic evidence. No external provider received unpublished manuscript
text. Only documentation queries and the failed package/DNS lookup used
network capabilities.
