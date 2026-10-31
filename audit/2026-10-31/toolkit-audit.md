# Toolkit evidence audit for integration planning

Audit date: 2026-10-31. Working tree: `/Volumes/Lexar/lambda/devel/polyhedra/ideal_poly_volume_toolkit`, clean `main` at `cc6b689652ce735f2098bb0a3235089210d764df`. This is a bounded source and numerical audit, not full numerical validation or a theorem review. No source, data, Git configuration, or dependency environment was changed.

## Inventory and present structure

- 925 tracked files; 273 tracked Python files; 46 package Python modules totaling 24,108 lines; 32 tracked `tests/test_*.py` files.
- Tracked materialized working-tree bytes: 76,586,772. Git pack: 14.74 MiB, 1,577 packed objects. 412 Git LFS paths; zero unresolved LFS pointer files among tracked working-tree files.
- Largest tracked files: `results/ground_truth_n10.json` 14,963,652 bytes; `results/rl_validation/controller-v2-seed42-protocol2-20260815T211114Z.json` 10,421,620; original/corrected spanning-tree JSONs about 6.23 MB each; `paper/maximal_ideal_polyhedra.pdf` 1,466,386.
- `pyproject.toml:1-98` already provides a setuptools package, Python `>=3.10,<3.15`, minimal NumPy/SciPy/mpmath core, feature extras, and the installed `ideal-poly-optimize` command. Do not recreate these as if missing.
- `CLAUDE.md:1-48` requires clear ownership, documented structural moves, and a migration plan. `docs/architecture.md` and `docs/module-index.md` describe existing owners. `docs/plans/codebase-improvement-roadmap.md:8-80` is an active preexisting cleanup plan; extend/reconcile it rather than create competing cleanup queues.

## Confirmed defects or misleading contracts

### 1. Exact arithmeticity status can be created by floating underflow

Evidence: `ideal_poly_volume_toolkit/rivin_holonomy.py:763-770` accepts a `numbers.Real`, converts it to float, and returns the converted mapping. `:884-895` checks exact zero only after this conversion and then reports `certified_declared_exact_zero_shear`.

Reproduction: for coherent tetrahedral faces `[(0,2,1),(0,1,3),(1,2,3),(2,0,3)]`, supply `Fraction(1,10**400)` on all six shear edges. All original values are nonzero, but all normalized values become `0.0`, `has_exact_zero_shears=True`, and `is_arithmetic=True`. This is a confirmed exact-status bug for an accepted input type, not evidence that the standalone abstract integer certificate is wrong.

Correction: determine exact-zero declaration before lossy conversion, or reject unrepresentable inputs. Keep approximate diagnostics and exact declaration as distinct values. Add a regression for nonzero rational underflow and ordinary exact zero. Retain the separate coordinate-derived path's refusal to issue an exact certificate.

### 2. Legacy rigid realization depends on cyclic rotation of a face

Evidence: `ideal_poly_volume_toolkit/geometric_realization.py:198-260` chooses a side from the ordered pair left after removing the new vertex, without maintaining the original cyclic face orientation. `:301-306` returns success merely when every vertex has been placed. It also fixes the two numerically smallest vertex labels whether or not they share an edge (`:60-87`).

Confirmed reproduction, preserving the same target angles and same oriented triangulation: original coordinates `(0,0),(1,0),(-.3,1.2),(1,.8)` with faces `[(0,1,3),(0,3,2)]` produce signed double areas `[0.8,1.44]`. Cyclically rotating only the second face to `(3,2,0)` produces `[0.8,-1.44]` and a reflected vertex, but still `success=True`. Script: `/Volumes/Lexar/lambda/devel/polyhedra/audit/2026-10-31/toolkit-probes.py`.

Correction: make the maintained `rivin_delaunay.realize_angles_as_points` the canonical realization path, with the independent geometric audit. Either retire this legacy implementation behind a documented compatibility wrapper or repair it with orientation, label, closure, overlap, and residual tests. The legacy path remains actively recommended by `docs/GEOMETRIC_REALIZATION_README.md:47-73` and used by `examples/test_rigid_construction.py`.

### 3. Scalar Lobachevsky derivatives are incorrect near endpoints

Evidence: `rivin_delaunay.py:774-776` returns zero for the gradient near either endpoint; `:791-793` returns `-1e10` for the Hessian near both endpoints. But the declared formulas are `-log(2 sin theta)` and `-cot(theta)`, the latter positive near pi.

Confirmed scalar probe using source AST and Python `math` (without importing SciPy): at `theta=pi-1e-11`, code gradient is `0.0`, true value approximately `24.6352765`; code Hessian is `-1e10`, true value approximately `+9.9998767e10`. At `1e-11`, gradient is again incorrectly zero.

Scope: these public helpers have no current internal callers (repository-wide Python search found only their definitions). The active Newton implementation directly computes the derivative formulas at `:815-829`; this defect does not establish that its interior Newton steps are wrong. Correct helpers before reuse by monograph Hessian code.

### 4. “Exact” volume naming does not describe exact or fully arbitrary-precision computation

Evidence: `geometry.py:175-177` mutates global `mp.mp.dps` and casts theta to Python float; `:250-263` first computes triangle angles in NumPy and returns a float. `:326-372` starts from complex128 coordinates and accumulates a float. `bloch_wigner_mpmath` explicitly claims to be exact (`:218-226`), returns a float, and lacks removable-value handling at zero/one. `volume_threshold.py:355-363` calls a float result “exact.”

Correction: distinguish binary64, arbitrary-precision evaluation, and rigorous enclosure. Rename/document the existing mode as high-precision kernel evaluation on binary64 input, retain a deprecated alias, scope mpmath precision with a context, and add a genuinely arbitrary-precision input/output path if the monograph needs it. Test removable endpoints and degenerating inputs. Exact arithmetic topology/holonomy is a separate capability.

### 5. Reported angle-optimizer volume uses a fixed truncated Fourier sum

Evidence: `rivin_delaunay.py:1103-1105` reports volume with exactly 64 Fourier terms; geometry's public planar entry defaults to the same truncated “fast” mode (`geometry.py:326-330`), whereas the sphere entry and canonical optimization objective use Bloch–Wigner. These are intentionally different algorithms, but a monograph table must not silently mix their precision.

Correction: use the canonical accurate kernel for final accepted values, recording algorithm and tolerance; keep approximation only where explicitly selected and error-bounded. This audit did not quantify the 64-term error over an entire result corpus.

### 6. Old realization documentation states an incorrect mathematical implication

Evidence: `docs/GEOMETRIC_REALIZATION_README.md:5-13` claims any feasible LP triangle-angle assignment is sufficient for its geometric realization and says boundary vertex sums are 2pi. The actual flatness condition is on interior vertices; the code at the top of `rivin_delaunay.py` states it correctly. A feasible angle assignment need not have compatible edge lengths around cycles; closure/log-sine conditions are additional requirements. The monograph must distinguish LP feasibility from the particular compatible maximizer and verified coordinate realization.

Correction: replace this narrative and link to the maintained residual-bearing reconstruction contract. This is especially important when integrating the ipoly log-sine/Hessian discussion.

## Confirmed design debt and ownership gaps

- `volume_threshold.py:32-163` duplicates sphere projection, hull/Delaunay, and Lobachevsky-series/angle helpers from `geometry.py`; its self-contained claim at `:8-9` contradicts its import at `:22-25`. It also mixes “all supplied points” and “implicit infinity” contracts (`:272-320`). Define explicit infinity semantics, reject NaN as invalid rather than treating any nonfinite input as infinity, and delegate to one geometry owner.
- `pointset_to_fuchsian.py` combines holonomy, volume gradients, mesh export, and rendering. `invariant_trace_field_signature` (`:261-271`) computes near-integer squared traces of generators only; it does not compute an invariant trace field or establish arithmeticity. Its name and README description (`README.md:147`) need narrower wording.
- `bin/analyze_distribution.py:39-459` still owns sampling and fitting product logic; `bin/gui.py:172-294` has its own distribution workflow. Extract one service before installing a distribution command. This is already queued at `docs/plans/codebase-improvement-roadmap.md:27,30`.
- The top-level package exports H4 routines eagerly (`__init__.py:11-29`) while H3 is the primary use case. Define a public API/export/deprecation policy without wholesale file movement.
- `tests/test_geometry.py:3-5` imports Torch unconditionally, so the combined geometry test module cannot run with the minimal core environment. `tests/test_optional_dependencies.py:10-62` does verify no-Torch behavior via an import blocker, but `:65-74` requires Torch. Separate core and optional CI jobs/tests; keep existing full CI.
- The Rivin active-set solver adds constraints but never tests multiplier signs or releases constraints (`rivin_delaunay.py:988-1099`), and its success flag is based on convergence and maximum dihedral (`:1114-1119`) rather than every reported residual. `_newton_in_nullspace` clips iterates and uses a feasibility-only line search (`:807-854`). These are review targets, not newly proved optimizer failures. Require KKT, equality, inequality, and boundary diagnostics before interpreting success as a global optimum.

## Working foundations to retain

- H3's accurate vectorized Bloch–Wigner owner and pole-aware sphere projection: `geometry.py:68-128,185-215,378-407`.
- Canonical optimization service and result schema: `optimization.py:327-436`, `optimization_cli.py`, `docs/schemas/optimization-result-v1.schema.json`; GUI/CLI already share this path.
- Lazy Torch compatibility boundary: `geometry.py:18-35`; feature extras already exist.
- Exact abstract zero-shear certificate explicitly excludes coordinate realization: `rivin_holonomy.py:700-716`. It validates closed-sphere topology and evaluates integer holonomy matrices. Keep that scope visible in the book.
- Independent numerical realization audit and solver: `rivin_zero_shear.py:1329-1485,2319-2440`; established tests cover topology, support, orientation, embedding, shears, and labeled facets. Some predicates use exact rational fallback on represented floats, but root existence and exact real geometry remain unproved without interval validation.
- `rl/` is already a feature subpackage, with package-root shims. Work accounting, canonical-vs-surrogate separation, model provenance, and paired-study protocols already exist; avoid reimplementing them in a second package.
- Existing artifact schema/manifest: `docs/schemas/result-manifest-v1.schema.json`, `results/manifest.json:1-90`; two explicit canonical input records, historical/derived/superseded collection classifications. The canonical records explicitly admit unavailable historical seeds/commit metadata (`:14-26,37-49`), so “canonical input” does not imply fresh reproduction.

## Already documented limits and publishing hazards

- `docs/implementation-status.md:127-146` records non-generic H4 pole-dependent volumes, broken `scripts/optimize_facet_full.py`, coplanar-facet tolerance issues, higher-dimensional WIP, superseded arithmetic corpora, and lack of interval realization proofs. Treat these as known limits pending dedicated repair, not new discoveries from this audit.
- `docs/implementation-status.md:183-245` warns about incomplete H5 saved records and superseded RL speedup claims. Its study status is an August snapshot; a newer 10 MB controller-v2 result exists, so reconcile live artifacts before repeating status claims.
- `.gitattributes:4-16` scopes LFS rules to paths; moving either repository under a new prefix requires preserving/remapping those rules. Hashes and migration mappings should survive integration.
- `.github/workflows/sync-to-hf.yml:3-24` force-pushes main to `huggingface.co/spaces/igriv/idealpolyhedra` on every main push. Do not transplant this workflow into a monorepo unmodified; it would target the old application with new repository contents. Reconcile deployment ownership explicitly before enabling workflow execution.
- `.github/workflows/monthly-maintenance.yml:35-46` upgrades every outdated installed package, potentially overriding the tested upper bounds after installing `[dev]`. Its AI-fix automation at `:103-179` should be explicitly reconsidered in the monorepo, not accidentally inherited as a publishing workflow.
- `app.py`, `Dockerfile`, `bin/gui.py` are a Python/Gradio Hugging Face application. They are not an OpenAI Sites frontend; preserve them as a separate local/application adapter or archive after a deliberate decision.

## Verification performed

1. `git status --short --branch`: clean before and after inspection.
2. Python AST parsing of all 273 tracked Python files: zero syntax failures. No bytecode written.
3. LFS inventory: 412 tracked LFS paths, zero unresolved working-tree pointer files. This was not a full object-history/hash/schema audit.
4. Default Python is 3.15 and lacks numerical/test dependencies; Python 3.11 and bare uv 3.12/3.13 environments also lack them. Existing `/Volumes/Lexar/lambda/devel/billiards/.venv/bin/python` has NumPy/SciPy but no mpmath/pytest/Torch. No installation was attempted.
5. Bounded source-module probes using that existing NumPy/SciPy interpreter:

   `PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python /Volumes/Lexar/lambda/devel/polyhedra/audit/2026-10-31/toolkit-probes.py`

   The canonical seed-10 LP→angle optimization→realization case from `tests/test_penner_rivin_regression.py:104-125` passed: angle error `2.5803332996847785e-14` degrees, closure error `2.3557928023801794e-15`, preserved triangulation. Exact tetrahedron zero-shear certificate returned index 12 and three determinant-one integer generators. The cyclic-rotation and rational-underflow probes reproduced the two defects above.

6. Scalar derivative probe extracted the two actual helper functions by AST and bound NumPy's scalar math operations to Python `math`. This confirmed the endpoint clamp defect; it was not an execution of the full optimizer.

Full pytest, package installation/build, GUI, high-precision volume validation, data schema validation, CI, high-dimensional and long-running optimization results were not run. Direct source-module loading deliberately avoids the package's eager mpmath import and must not be represented as successful package installation or all-module import testing.

## Reuse patterns and confidence

Copy the established optimization serialization/data-contract pattern from `optimization.py:369-436`; copy ownership and compatibility-shim conventions from `docs/architecture.md` and `tests/test_script_layout.py:21-45`; extend the existing exact-vs-numerical status scheme in `rivin_holonomy.py:774-924`; reuse the independent zero-shear audit rather than duplicating predicates in book widgets.

High confidence: clean commit/inventory, code snippets, duplicate ownership, explicit documented limits, the two live reproduced bugs, scalar derivative signs, precision casts, CI/deployment wiring. Moderate confidence: proposed ownership cuts and active-set review priorities. Unresolved: full test baseline, live remote CI, entire corpus correctness, formal proof claims, all H4/H5/H6 behavior, and current RL-study conclusions.
