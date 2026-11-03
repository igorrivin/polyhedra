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

## Log-sine barrier examples

`barrier_run.py` adds three fixed examples for the chapter's finite-iterate
barrier argument. The maintained solver and its input/failure contract are in
[`angle-barrier.md`](../../packages/volume-toolkit/docs/angle-barrier.md).
This is a dense binary64 implementation with an explicitly supplied affine
angle domain and strictly feasible start. It does not implement a nearly-linear
method or certify the floating-point gap estimate.

From the consolidated checkout, use an installed toolkit or an explicit source
path:

```sh
PYTHONPATH=packages/volume-toolkit python experiments/section9/barrier_run.py \
  --output /tmp/section9-preview/barrier-result.json \
  --site-dir /tmp/section9-preview/site/section9
```

Defaults are `artifacts/section9/barrier-result.json` and
`site/section9/barrier.html`; all download names are separate from the original
grid example. The output includes complete centering/path traces, accepted
parameters, positivity and constraint diagnostics, linear-solve checks, final
decrement, schedule, work counts, and independent reference comparisons. The
initial damped centering work is separate from the subsequent short path steps.
Centering stops at decrement at most 1/4; its accepted point need not be the
exact minimizer of the initial barrier objective.

The fixtures are deliberately small mathematical examples:

| Fixture | Independent reference |
| --- | --- |
| `regular-triangle` | The full two-dimensional triangle tangent space has its exact-space maximum at three angles π/3, with volume 1.014941606409653625… |
| `asymmetric-disk` | Four triangles join the rectangle corners (0,0), (4,0), (4,3), (0,3) to (1,0.5). The grounded leading–trailing coordinate preserves interior-edge opposite sums and has its geometric volume maximum at u=0, of volume 3.006286641747050653… Its pure barrier center is u≈0.03634147; the exact Φ₁ center is u≈0.02844640. |
| `boundary-maximum` | The affine slice consists of (π−2s,s,s) and (0.1−s,1+s,π−1.1), 0<s<0.1. Strict concavity and V′(0+)=2 log 2+log(sin(0.1)/sin(1))≈−0.74535421 give the unique closed maximum at s=0, of volume 0.316035844601294286… No geometric realization is asserted. |

The oracle uses 80-digit mpmath Clausen/log-sine formulas and bracketed scalar
stationarity calculations; it does not call the production Hessian. It records
the exact mathematical decimal/geometric references separately from the
Clausen model obtained by lifting the actual binary64 base angles and incidence
coefficients. It also compares the endpoint with a separate high-precision
Bloch–Wigner evaluation. The boundary example needs this distinction: tiny
rounded triangle-sum defects alter the limiting derivative and move the lifted
stationary point just inside the boundary. These are multiprecision comparisons,
not interval bounds. Endpoint volume comparisons and observed-gap tests use the
explicit 1e-11 allowance in the fixture; decrement checks have their own recorded
tolerances. Full traces and sampled high-precision reference gaps are retained.

`--fixture` only accepts an unchanged copy of `barrier-fixtures.json`; it is not
a general mathematical experiment or renderer. The code, template and fixture
are source-hashed, together with the actual imported `angle_barrier.py`,
`variational.py` and `geometry.py`. The chapter source is optional for detached
execution and hashed when available. `--render-result` validates all these
roles before packaging and preserves the original computation environment and
timestamp. It does not recompute the results. Supply `--chapter-page` only after
the chapter builder has produced the actual `chapter.html` in the same site
directory; detached standalone pages omit that link.

The `downloads/barrier-reproduction.zip` archive contains the runner, fixture,
template, three unchanged maintained numerical modules, a labeled minimal
package initializer, MIT license, captured requirements, and `barrier-bundle.json`
with a complete payload manifest and origin provenance. Extract it outside the
checkout, install its captured requirements in an isolated environment, then
run `python experiments/section9/barrier_run.py`; an absolute script path from
another working directory also works. This only needs NumPy, SciPy and mpmath.
The generated report records the current execution separately from the archive
origin and refuses altered payloads. Individual Python downloads are inspection
copies; the complete archive is the runnable reproduction.

`tests/test_barrier_examples.py` checks independent reference values, nontrivial
centering and disk motion, preservation of opposite sums, boundary rounding,
source identity, download completeness, captured versions, and payload tamper
rejection. The toolkit tests own the reusable solver's correctness. These fixed
fixtures do not establish scaling performance or prove all chapter claims.
