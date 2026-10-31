# ipoly evidence audit for the integration plan

Audit date: 2026-10-31. This is fact gathering, not a complete mathematical referee report. No repository source was changed. All paths below are relative to `/Volumes/Lexar/lambda/devel/polyhedra/ipoly` unless qualified.

## Inventory and provenance

- Clean local checkout at `30ef40e23005509bd94d26f27dc48ea778832a50`; configured origin `git@github.com:igorrivin/ipoly.git`. Remote visibility and remote HEAD were not queried.
- `README.md:3-15`: one manuscript (LaTeX/PDF), 22 standalone Python research scripts, and two original archives. `README.md:17-31` names NumPy, SciPy, mpmath, SnapPy/Spherogram requirements and dependence on repository-root working directory. No package manifest, dependency lock, CI, test suite, license, or structured numerical results are present in this checkout.
- `verification_scripts.zip` contains precisely the 22 expanded scripts; every archived member is byte-identical to its expanded counterpart. `files (5).zip` contains the LaTeX, PDF, and script archive; all three are byte-identical to the expanded files. These are provenance copies, not divergent versions.
- The manuscript has 1,271 lines, uses `amsart` (`duffin_rivin_volume_laplacian_solvers.tex:1`), is dated 18 September 2026 (`:34`), and has no author declaration. The archive timestamps are later; do not confuse a printed manuscript date with a build/revision date.
- Existing provenance is unusually useful: `:1135-1161` distinguishes source consultation, second-hand references, computations, hand derivations, and memory. Preserve this evidence, then resolve the unchecked claims before publication.

## Computational coverage

| Material | Existing scripts and locations | Nature and reuse |
| --- | --- | --- |
| Volume gradient/Hessian and reciprocal dual network | `v1_volume_hessian.py:19-81` | Fixed-dihedral leading/trailing coordinates, finite differences, Newton, and Bobenko–Springborn identity. Small regression examples. |
| Excess, cut slack, degeneration, sharpness | `v2_excess.py:9-69`, `v3_chain.py:6-31`, `v5_cut.py:8-23`, `v6_smallangle.py:7-22` | Random checks and exhaustive small edge-subset enumeration, exponential in edge count. Extract fixtures and exact combinatorial tests rather than running all enumerations in routine CI. |
| Self-concordance and compatible barrier | `v4_sc.py:4-25`, `v13_compat.py:7-38`, `v14_identity.py:7-17` | Counterexample scan for bare volume, 250-digit degenerate-triangle scan, finite sample checks of identities and barrier. These computations support but do not prove uniform inequalities. |
| Circle-packing curvature Jacobian | `v7_packing_hessian.py:9-28` | Useful independent finite-difference oracle for a positive weighted Laplacian. |
| Once-punctured torus bundles | `v8_torus_bundles.py:8-40`, `v11_bundle_compare.py:5-49` | Angle-coordinate construction, starts, dense Newton, adaptive barrier; four named volume checks and empirical angle scaling. `v8:5` says parametrization was recalled from memory and checked against known volumes; verify published parametrization before promoting to API. |
| Fixed-dihedral sparse solvers | `v9_adaptive.py:8-72`, `v10_large.py:6-139`, `v12_trace.py:5-30` | Best reusable core: oriented corners, sparse incidence, max-margin LP, sparse LU, plain Newton and log/log-sine/power penalties, diagnostics. Not a nearly-linear Laplacian solver implementation. |
| Maximum volume in a combinatorial class | `v15_maxvol.py:9-48`, `v16_horospheres.py:8-55`, `v19_nosplit.py:7-42`, `v20_plain_on_boundary.py:8-40` | Three-family constraints, null-space barrier, developing geometry, tangent-horosphere residual, and stalled plain-Newton boundary examples. Strong candidate to supply missing bounded examples and regression fixtures for the toolkit. |
| Actual ideal triangulations and sparse KKT | `v17_threemanifolds.py:8-29`, `v18_nongeometric.py:9-29`, `v21_snappea_vs_ours.py:11-78` | Optional SnapPy/Spherogram layer. Keep separate from polyhedron APIs. No verified-hyperbolicity or interval implementation. |

The manuscript's computational provenance also claims exact hexagon checks, random Rippa flips/Loewner inequalities, low-stretch/grid checks, and unbiased clique sampling (`:1139-1140`). Their corresponding implementations are absent from the 22 `v*` scripts. Locate originals or add those experiments; do not imply this folder fully reproduces the paper.

## Confirmed corrections and concrete risks

1. **Positive-angle/maximizer claims are inconsistent.** `duffin...tex:898-900` calls the object a closure while retaining strict angle positivity and says the maximizer is unique with positive angles. The later proposition explicitly permits `(pi,0,0)` triangles (`:918-924`), and the reported experiments contain five such cases (`:948`). Split the open feasible domain, its closure, and degenerate strata, and audit uniqueness on boundary strata. The no-needle proposition is weaker than the heading “The polyhedron does not split” (`:915-931`); it does not by itself establish a global classification of degenerations.

2. **Schläfli sign convention mismatch.** `:335-336` defines theta as the exterior dihedral angle. `:934` writes `dV = -1/2 sum ell dtheta`, the sign for interior dihedral angles with the usual signed-distance convention. With exterior theta = pi - interior Delta, the sign should be plus. The criticality/tangency condition remains unaffected, but the sign and all conventions should be made consistent across sources.

3. **Stale conclusion about iteration bounds.** `:1116` says no polynomial bound on the number of Newton steps is proved, whereas `:483-509`, `:814-815`, and `:1128` distinguish the barrier bound from the unproved bound for plain Newton. Correct the summary to retain that distinction. Separately, the bit/word-length claims at `:498-509` need an explicit dependence on requested numerical accuracy and inexact solve errors, not only angle conditioning. Treat this latter issue as a proof-audit task, not a refuted theorem.

4. **The prose's “exact” row elimination is implemented using floating arithmetic.** `:970` and `v21:12-13` say redundant edge rows are removed exactly; `v21:18-22` builds a floating matrix and uses floating `scipy.linalg.qr(..., pivoting=True)`. The dropped rows are retained as `equations.check` (`:25`) but never used. Require exact integer/rational rank evidence or qualify the implementation, and verify all original equations in the returned solution. `v21:45` currently detects `max(abs(A@d)) > 1e-6` then does nothing (`pass`).

5. **Benchmark headline excludes mandatory setup.** The 6,000-tetrahedron row is SnapPea 129 s, LP 0.99 s, barrier 0.16 s (`:982`). The “800” speedup at `:991` is 129/0.16, while 129/(0.99+0.16) is about 112 including LP (before other setup). Present solver-only and complete-run timings separately. `v21:27-29` estimates SnapPea time by subtracting one independent copy timing; add repeated direct timing, warmups, exact versions, input triangulation signatures, full pipeline accounting, and convergence criteria. The text already acknowledges covers mainly test linear algebra (`:992`); preserve that qualification. No live SnapPy benchmark was replayed in this audit.

6. **LP failures and trivial domains are unchecked.** `v9:36-37`, `v10:44-45`, `v11:6`, `v15:32-33`, `v20:24-25`, and `v21:39-40` dereference `res.x` without checking success. A valid single triangle and a convex quadrilateral both make `v10.Run` raise `TypeError: 'NoneType' object is not subscriptable`: there are no variable interior corners, so its auxiliary max-margin objective is unbounded. A reusable solver must handle the zero-dimensional case and distinguish infeasible, unbounded auxiliary problem, numerical failure, and converged results.

7. **No robust solver-result contract.** `v8:40` returns iteration count and the gradient from before the last update; `v10:137-138` prints a result without distinguishing exhaustion of `t < 1e40` from success; `v21:51-52,71-73` returns on tiny steps or budgets without a full feasibility/stationarity/gap record. Dense null-space scripts likewise end at a fixed barrier weight. Make explicit status, equality/inequality residuals, minimum angle/slack, objective gap estimate, iterations, and precision part of the return value. Floating residuals are not mathematical certificates.

8. **Source-text execution and duplication hinder integration.** `v10_diag:2-3`, `v11:4`, `v12:3-4`, `v18:7`, `v19:4`, and especially `v20:47-48` splice and execute neighboring source text, sometimes changing `sys.argv` or function names. Most scripts run experiments at import time. Copy the useful routines into real modules with explicit data structures and main-guarded thin experiment drivers. The three-family constraints and barrier are duplicated across `v15`, `v16`, and `v20`; fixed-dihedral logic repeats across `v1`, `v9`, `v10`, `v12`; bundle Newton repeats across `v8`, `v11`.

9. **Input repair loses identity information.** `v10:25-31` discards Qhull-unused points and legalizes edges; `:51` does print the removal count. Return the retained/original vertex mapping, dropped IDs and reasons, and a repair record. A result on a reduced point set must not silently become a claimed result on the original combinatorics.

10. **Small-sample sharpness claim can be strengthened cheaply.** `duffin...tex:581` says the minimum excess equals d0 but only mentions enumeration for n <= 10. The existing excess identity `:525-530` gives a direct general proof: every proper edge-containing subcomplex contributes at least one outside corner, and all constructed chain angles are at least d0; an initial segment attains d0. Add that argument, and retain enumeration as a regression check.

11. **Minor diagnostic placeholder.** `v10_diag.py:7` prints a theta-max condition bound but contains `... if False else 1` inside the tangent. Replace it with the actual intended angle parameter before the output is used in a table.

12. **Substantial source verification remains.** `duffin...tex:1149-1161` explicitly records unconsulted Rivin sources, memory-derived variational theorems, barrier complexity, manifold claims, and an asserted separator property not proved in detail. Prioritize these claims and their hypotheses for source checking. Do not erase this provenance and thereby upgrade it into verification.

## Reusable patterns and toolkit overlap

- Sparse oriented corner-incidence construction: `v10_large.py:23-45`; update error handling and input mappings before use.
- Separate fixed-dihedral optimization from variable-dihedral maximum-volume optimization. Their constraints and solver structures genuinely differ (`duffin...tex:408-417,891-913`). Do not merge both under a boolean without preserving this distinction in API/results.
- Three-family polytope and log-sine barrier: `v16_horospheres.py:8-37`; add sparse representation, convergence contract and valid boundary handling.
- Geometry development and tangency residual: `v16_horospheres.py:38-55,65-72`; add progress/connectivity/orientation checks to avoid an endless loop for malformed disconnected input.
- Small boundary regression examples: `v15_maxvol.py:49-53`, `v20_plain_on_boundary.py:41-44` (octahedron and stacked tetrahedra).
- Optional sparse KKT construction: `v21_snappea_vs_ours.py:30-40`; fix rank/residual/status handling and isolate SnapPy internals from the numerical core.
- Toolkit already has `ideal_poly_volume_toolkit/rivin_delaunay.py` for three-family LP/maximization and related zero-shear/holonomy modules. A consolidation should compare constraints and answers on shared fixtures before deleting either implementation. Its public `lobachevsky_gradient` currently returns 0 close to both endpoints (`:774-776`) and its Hessian returns a negative sentinel near pi (`:791-793`), although the actual second derivative tends positive infinity there. This overlap was passed to the toolkit auditor.

## Live validation in this audit

No packages were installed. Default Python 3.15 and the bare installed uv Python 3.12/3.13 lack numerical dependencies. An existing interpreter at `/Volumes/Lexar/lambda/devel/billiards/.venv/bin/python` supplied Python 3.11.17, NumPy 2.4.6, and SciPy 1.17.1, but no mpmath, SnapPy, Spherogram or pytest. This is a borrowed environment, not a reproducible project environment.

Commands ran from the `ipoly` root with `PYTHONDONTWRITEBYTECODE=1`:

- `.../python v5_cut.py`: exit 0, maximum cut/excess identity error `6.75e-14`.
- `.../python v7_packing_hessian.py`: exit 0, Jacobian/Laplacian error `1.03e-09`, minimum conductance `0.209`, symmetry error `1.3e-09`.
- `.../python v14_identity.py`: exit 0, 200,000-sample identity max relative error `1.0e-12`; compatibility ratio max `1.6665` versus sqrt(3) `1.7321`; self-concordance ratio max `0.9998`.
- Imported `v10_large.py` using `importlib.util`, constructed `Run(default_rng(1).random((40,2)), 'audit random n=40')`, and ran `vanilla(maxit=100)` and `penalized('logsin', mult=10.0)`. Plain Newton: 7 reported iterations, max angle error `3e-15`; log-sine penalty: 10 counted steps, max angle error `1e-12`.
- The two boundary-only `v10.Run` inputs listed in finding 6 both reproduced the stated exception.
- `ast.parse` passed for all 22 scripts. All original archive members matched their expanded bytes. Final `git status --short` was clean.

Exact numerical commands (working directory `/Volumes/Lexar/lambda/devel/polyhedra/ipoly`):

```sh
PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python v5_cut.py
PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python v7_packing_hessian.py
PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python v14_identity.py
PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python - <<'PY'
import importlib.util, numpy as np
spec = importlib.util.spec_from_file_location('audited_v10', 'v10_large.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
R = m.Run(np.random.default_rng(1).random((40, 2)), 'audit random n=40')
if R.valid:
    R.vanilla(maxit=100)
    R.penalized('logsin', mult=10.0)
PY
PYTHONDONTWRITEBYTECODE=1 /Volumes/Lexar/lambda/devel/billiards/.venv/bin/python - <<'PY'
import sys, numpy as np, scipy, importlib.util
print(sys.version.split()[0], 'numpy', np.__version__, 'scipy', scipy.__version__)
spec = importlib.util.spec_from_file_location('audited_v10', 'v10_large.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for label, P in [
    ('single triangle', np.array([[0., 0.], [1., 0.], [0., 1.]])),
    ('convex quadrilateral', np.array([[0., 0.], [1., 0.], [1., 1.], [0., 1.]])),
]:
    try:
        R = m.Run(P, label)
    except Exception as exc:
        print(label, type(exc).__name__, str(exc))
PY
```

These are numerical spot-checks plus syntax/archive integrity, not a complete replay, tests of every supported platform, an interval certificate, proof of a global maximum, or a full verification of the monograph.

## Confidence and known gaps

High confidence: script structure, duplicate archives, exact local source locations, internal prose contradictions, numerical outputs above, and the reproduced trivial-domain crash. High confidence in the Schläfli sign mismatch under the text's stated exterior-angle and usual signed-distance convention; confirm a unified convention when editing all manuscripts. The barrier complexity, global uniqueness on the closed domain, separator claims, and broader topology literature need a mathematical/source audit rather than a stylistic edit. No current SnapPy API compatibility, numerical benchmarks, PDF layout or LaTeX rebuild was checked. No claimed global classification was inferred from sampled experiments.
