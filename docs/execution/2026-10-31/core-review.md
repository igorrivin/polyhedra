# Independent core correctness review

Date: 2026-10-31. Reviewed working tree: `consolidated/`, based on import commit
`c53387221dc6d000ac46c0b1ce44232c50f02a3c`. No implementation edits, Git staging,
commits, or original-repository modifications were performed by this reviewer.

## Verdict

No blocking correctness regression found in the three changes. The reviewed
implementation fixes the two reproduced defects and the public endpoint
derivative helpers, with appropriately limited numerical status. This is approval
of this bounded change, not a complete proof audit or a passing full optional
dependency environment.

One minor documentation follow-up: the `geometric_realization.py` entry in
`packages/volume-toolkit/docs/module-index.md` still says “Geometric realization
from Rivin LP angles.” Align it with the revised oriented numerical development
contract, since arbitrary feasible LP angles need not close. The dedicated README
and architecture discussion already make the distinction correctly.

## Review findings

- Exact-zero shear status is now derived from the validated mapping's original
  values. Nonzero `Fraction` values lost during binary64 conversion cannot receive
  an exact certificate, while exact rational zeros retain certification. Coordinate
  diagnostics remain excluded from exact arithmeticity status. The existing
  independent integer holonomy evaluator is unchanged.
- The rigid development formula uses cyclic face orientation consistently and
  chooses an actual edge independently of vertex numbering. Shared-edge winding,
  nondegenerate angle data and incidence validation precede development. The final
  success gate checks finite distinct positions, oriented faces, angle residuals,
  and developing-map closure. The retained return fields and optional boundary
  argument preserve the useful compatibility surface; malformed input and
  disconnected/incompatible data now fail explicitly.
- The realizer does not claim global non-overlap, Delaunayness, convexity, or an
  interval existence proof. The new evidence fields and documentation state these
  limits. The substantial simplification removes duplicated circle-intersection
  branches rather than adding a second geometric implementation.
- Lobachevsky derivatives use `-log(2 sin(theta))` and `-cot(theta)` on the open
  angle interval, with nonfinite/out-of-domain input rejected. The near-pi Hessian
  sign is correct. Repository call search confirms these public helpers are not
  the active Newton solver's internal derivatives, so no optimizer-performance
  claim follows from this change.
- Targeted anti-pattern review found no exact certificate inferred from a
  tolerance in the changed code, no silent positive success merely from placing
  vertices, and no endpoint sentinel in the corrected derivative helpers.

## Independent verification

All commands ran from `consolidated/packages/volume-toolkit` with the isolated
CPython 3.12 environment at `/tmp/polyhedra-baseline-20261031`. Printed module
paths confirm that the current consolidated source was imported, not the original
baseline wheel. Dependencies were previously copied from local installed
snapshots after PyPI access failed; this does not validate fresh dependency
resolution.

```sh
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031 GRADIO_ANALYTICS_ENABLED=False \
/tmp/polyhedra-baseline-20261031/bin/python -m pytest -q \
  -p no:cacheprovider --continue-on-collection-errors \
  --junitxml=/Volumes/Lexar/lambda/devel/polyhedra/execution/2026-10-31/pytest-consolidated.xml
```

Result: **275 passed, 18 skipped, 4 failed, 9 collection errors, 2 warnings in
24.05 seconds**. See [log](pytest-consolidated.log) and
[machine-readable results](pytest-consolidated.xml).

Compared by test identity with the original baseline of 242 passed, 18 skipped,
5 failed and 9 collection errors:

- All 32 new tests pass (25 core regression cases and 7 Section 9 cases).
- The previous hardcoded LFS-count failure is fixed.
- The four remaining failures and eight collection errors still lack Gymnasium.
  The ninth collection error still lacks Hypothesis. No new failure or collection
  error appeared.
- The 18 existing skips and two existing SciPy quadrature warnings remain. The
  warnings arise at `rivin_delaunay.py:760` in existing Penner–Rivin/realization
  controls.

An independent numerical development smoke used a 12-vertex grid under a
nonsimilarity affine transform, shuffled face order, independent cyclic face
rotations, and arbitrary nonconsecutive signed vertex labels. All twelve seeded
cases succeeded and recovered the original coordinates after similarity
normalization; the largest discrepancy was **1.7902605487475002e-15**. This tests
the coordinate and label conventions against known geometry, not just the
implementation's own residual fields. It remains sampled coverage.

The source CLI was run with `python -m ideal_poly_volume_toolkit.optimization_cli`
using 4 vertices, 1 trial, 30 iterations, population size 8, one worker and seed 42.
The emitted schema-v1 record validates and reports volume
**1.0149416063705312**, 4 vertices, 4 faces, 6 edges and Euler characteristic 2.
This is a source CLI check; a corrected installed-wheel check is a separate
release verification step.

See [independent smoke details](core-independent-smoke.log),
[CLI record](tetrahedron-consolidated-cli.json), and
[CLI log](tetrahedron-consolidated-cli.log).

Ruff passes on the three changed modules plus `test_core_defect_regressions.py`.
`git diff --check` passes on the authored tracked changes. Root working status
contains only the expected integration-increment edits and untracked companion
files; no reviewer implementation changes were introduced.
