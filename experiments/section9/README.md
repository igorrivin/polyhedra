# Section 9 worked example

This is the first text–code–result–HTML slice for the integrated monograph.
It is an authored computational companion, not a full LaTeX-to-HTML conversion.

The integer-coordinate 3 by 2 grid has twelve right-isosceles triangles and
two interior vertices. Its grounded stiffness matrix is `[[4,-1],[-1,4]]`;
the negative volume Hessian is twice that matrix. An independent rational FEM
assembly and exhaustive rooted-forest sum give determinant 60 exactly. The
volume is evaluated in binary64 against `12 * Catalan`; the off-origin
Hessian is compared with a 50-digit independent numerical derivative.

The diagonal weights vanish, so this is a non-strict Delaunay example.
The off-origin angle structure is not asserted to close geometrically.
Electrical boundary voltage and leading–trailing angle coordinates are
different variables. No strict polyhedron certificate, global optimum,
interval enclosure, or nearly-linear solver is claimed.

With the toolkit installed, run from any working directory:

```sh
python /absolute/path/to/consolidated/experiments/section9/run.py
```

Or from the consolidated repository without installing it:

```sh
PYTHONPATH=packages/volume-toolkit python experiments/section9/run.py
```

The defaults write `artifacts/section9/result.json` and
`site/section9/index.html`, including an actual runnable reproduction ZIP.
Open the HTML file locally. `--output` and `--site-dir` redirect generated files.
`--fixture` accepts an external path only to an unchanged copy of this fixed
rectangle fixture; it does not expose a general mesh experiment or renderer.

The ZIP contains the complete experiment, template, fixture, pinned NumPy/
SciPy/mpmath requirements, the toolkit MIT license, and unchanged copies of
the maintained `variational.py` and `geometry.py` modules in an explicitly
labeled package subset. It is not a full toolkit installation. No Torch,
Gradio or RL dependency is needed. Extract it outside the repository, install
its `requirements.txt` in an isolated environment, then run
`python experiments/section9/run.py`. An absolute runner path also works from
another working directory. The runner selects bundled code only when its
explicit bundle manifest exists. Normal repository execution continues to
support an installed wheel.

Individual downloadable Python files are inspection copies, not standalone
programs. Use the complete ZIP for detached reproduction. The book TeX and
reference PDF are optional and absent from that ZIP: the result explicitly
records missing optional assets, and its generated page omits unavailable
book links. This does not verify the complete monograph.

The main TeX download is now an inspection copy: the canonical monograph
includes a separate chapter file. The [chapter builder](../../site/README.md)
owns the complete LaTeX source ZIP and the full Section 9 HTML/PDF. Optional
`--chapter-page` and `--book-source-archive` arguments add links only to actual
supplied assets; the chapter must be built in the same `--site-dir` with its
local resources. These assets remain optional for detached numerical replay.

`--render-result existing-result.json` regenerates the companion from an
existing report without rerunning the computation. It checks source roles,
source availability, source hashes, fixture identity, and the result file before
packaging current code. A stale report cannot silently acquire a changed driver,
template, operator, or chapter. Rendering preserves the original computation
timestamp and provenance; reproduction requirements retain the recorded
dependency versions. Missing requested assets are errors. Both generators
support temporary output directories for generation from one clean source
commit; see the complete sequence in the publishing guide.

The runner captures Git status before it writes outputs. A preliminary run
from a modified checkout is marked dirty. A detached run records Git status
as unavailable (null), retains the bundle's originating provenance, and
checks payload hashes. Actual imported sources are recorded by stable roles,
with project-relative or external locations and hashes; required source
files cannot be silently omitted. For a release artifact, commit and
review code first, regenerate from that clean commit, and commit the resulting
artifact separately. The JSON records exact source/input hashes and the
precision, methods and numerical tolerances. A clean commit or an exact finite
fixture calculation is not a proof audit of the chapter.

Ownership:

- `fixture.json`: small public input, labels and conventions.
- `run.py`: independent exact fixture oracle, reproducibility record and driver.
- `page.html`: authored companion template and boundary-voltage illustration.
- `ideal_poly_volume_toolkit/variational.py`: reusable numerical operators.
- `tests/test_variational.py`: independent mathematical reference checks.

Canonical monograph labels: `eq:ipolyAngleCoordinates`, `eq:ipolyHessian`,
`eq:ipolyDtN`, `eq:ipolySchur`, `eq:ipolyForestDeterminant`.
