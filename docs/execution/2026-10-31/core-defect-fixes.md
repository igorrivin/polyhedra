# First core correctness checkpoint

Date: 2026-10-31. Scope: the consolidated toolkit only. No original repository was edited; no staging, commit, push or deployment was performed by this worker.

## Changes

- `ideal_poly_volume_toolkit/rivin_holonomy.py`: determine exact-zero shear status from the original validated real inputs, before conversion to float. Positive and negative nonzero `Fraction(1, 10**400)` values can still pass the floating zero-shear diagnostic, but cannot receive an exact certificate. Exact rational zeros still certify; the coordinate-derived path remains numerical.
- `ideal_poly_volume_toolkit/geometric_realization.py`: replace the duplicated circle-intersection branches with one oriented law-of-sines development over the face adjacency graph. Anchor an actual edge instead of assuming the smallest two labels are adjacent. Validate input shape, positive angles, triangle sums, edge incidence and coherent winding. Success now requires finite distinct coordinates, positive face orientations, small angle residuals and cycle-closure residuals. Disconnected or incompatible development fails explicitly. Preserve `points`, `vertex_list`, `success` and the optional boundary argument; add diagnostics and `evidence_status="numerical_development"`, `embedding_checked=False`.
- `ideal_poly_volume_toolkit/rivin_delaunay.py`: remove false endpoint clamps in public Lobachevsky gradient/Hessian helpers. Evaluate the correct formulas throughout the open interval (0, pi), and reject nonfinite or out-of-domain input. Their old near-pi Hessian had the wrong sign. These helpers are not used by the active interior Newton implementation.
- `tests/test_core_defect_regressions.py`: 25 new cases covering rational underflow/exact-zero control, cyclic rotation, arbitrary relabeling, incompatible cycle, disconnected/invalid input, and high-precision derivative comparisons.
- `docs/GEOMETRIC_REALIZATION_README.md`: replace the incorrect assertion that an arbitrary feasible LP angle assignment must realize, and correct interior-versus-boundary flatness. Document the maintained Rivin workflow, radians, and the generic development helper's precise scope.
- `docs/architecture.md` and `CHANGELOG.md`: reflect the corrected ownership/status and numerical contracts.

The canonical Rivin realizer is not a drop-in replacement for the generic rigid helper: it imposes Delaunay/convexity checks and may refine by optimization. The repaired helper preserves generic angle-development semantics instead of silently changing that problem.

## Verification

Working directory: `/Volumes/Lexar/lambda/devel/polyhedra/consolidated/packages/volume-toolkit`.

The isolated interpreter is `/tmp/polyhedra-baseline-20261031/bin/python`. This environment was prepared by the baseline worker from local package snapshots after network installation failed. It is not a fresh dependency resolver validation.

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
/tmp/polyhedra-baseline-20261031/bin/python -m pytest -q -p no:cacheprovider \
  tests/test_core_defect_regressions.py tests/test_rivin_holonomy_exact.py \
  tests/test_penner_rivin_regression.py tests/test_rivin_legalization.py
```

Result: **72 passed, 2 warnings in 1.17 s**. The warnings are the existing SciPy quadrature warning at `rivin_delaunay.py:760`, triggered in the Penner–Rivin/realization controls; no new warning category was introduced.

```sh
ruff check ideal_poly_volume_toolkit/geometric_realization.py \
  ideal_poly_volume_toolkit/rivin_holonomy.py \
  ideal_poly_volume_toolkit/rivin_delaunay.py tests/test_core_defect_regressions.py
```

Result: **All checks passed** (`/opt/anaconda3/bin/ruff`).

`git diff --check` on the seven owned files passed. Live imports of the two fixed modules were printed and confirmed to resolve inside the consolidated package, rather than the original wheel installed in the isolated environment.

An additional bounded development smoke generated SciPy Delaunay triangulations of 40 independent random points for seeds 0 through 19, computed their actual corner angles with atan2, and redeveloped each. All 20 passed; worst maximum angle residual was **9.827694213981886e-13 radians**. This is sampled numerical coverage, not a general proof.

## Limits

- Global triangle overlap, global embedding, Delaunayness, convexity and interval-certified existence are not checked by the generic development helper. Its result now states this explicitly.
- The fixed rational-underflow case concerns the exact declaration status, not the correctness of the independent integer abstract holonomy certificate.
- No full optional-dependency test suite or high-dimensional/RL campaign was run by this worker. The baseline's missing optional dependencies remain separate work.
- Scientific kernels and historical result tables outside these fixes remain unchanged.
