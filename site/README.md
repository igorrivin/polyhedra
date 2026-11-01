# Section 9 publishing build

`build_section9.py` owns the complete chapter conversion. Canonical mathematical
text remains in `book/chapters/09-volume-hessians.tex`; the full monograph includes
that file. The builder does not edit either source. It derives the standalone
preamble and bibliography from the full monograph, compiles the complete book
for authoritative labels, and checks the excerpt against those numbers.

The published directory contains `chapter.html`, the authored computational
`index.html`, and local assets/downloads. The HTML includes all chapter prose,
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
both generators observe the same clean source commit. From the repository root,
using the supported Python environment:

```sh
PYTHONPATH=packages/volume-toolkit python experiments/section9/run.py \
  --output /tmp/section9-release/result.json \
  --site-dir /tmp/section9-release/site/section9

python site/build_section9.py \
  --output-dir /tmp/section9-release/site/section9 \
  --computation-result /tmp/section9-release/result.json \
  --work-dir /tmp/section9-release/chapter-build

PYTHONPATH=packages/volume-toolkit python experiments/section9/run.py \
  --render-result /tmp/section9-release/result.json \
  --site-dir /tmp/section9-release/site/section9 \
  --chapter-page /tmp/section9-release/site/section9/chapter.html \
  --book-source-archive /tmp/section9-release/site/section9/downloads/monograph-source.zip
```

The last command only renders the existing report. It validates current source
and fixture identities before creating its reproduction bundle and preserves
the report's original computation timestamp, numerical values, dependency
versions and provenance. The chapter tool receives the actual fresh result
path explicitly and records its path and SHA-256.

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

All ledger paths become labeled inspection downloads inside the exported
directory; primary source URLs remain external citations. Missing current audit
reports can be displayed as pending only with `--allow-pending-evidence`, which
marks a preliminary preview. Final builds must omit that option. The original
ledger retains repository-relative ownership paths.

Inspect every PNG under `chapter-build/rendered-pages/` after building. The
manifest records rendering completion, not a completed visual inspection.
Perform an independent code/artifact review and record that review separately.
Static HTML integrity checks are not browser layout checks. Only after both
generators and reviews pass should the approved `result.json` and complete
`site/section9` output directory be copied into their canonical locations in a
separate artifact commit. A final artifact manifest must hash the files after
the last render-only step; the chapter build record describes its own outputs.

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

Focused checks:

```sh
python -m unittest discover -s site/tests -v
PYTHONPATH=packages/volume-toolkit python -m unittest discover -s experiments/section9/tests -v
PYTHONPATH=packages/volume-toolkit python -m pytest packages/volume-toolkit/tests/test_variational.py
```
