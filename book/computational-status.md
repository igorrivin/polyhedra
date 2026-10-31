# Computational status of the monograph

This ledger begins the review required by the [integration plan](../INTEGRATION_PLAN.md). It records the status of three computational passages in the unchanged [canonical source](polyhedral_volumes_and_geodesic_identities.tex). The source snapshot and supplied reference PDF retain their original bytes. A reproduced finite example does not audit a general proof, and missing computational evidence does not by itself disprove a mathematical statement.

## Section 9: a reproducible finite example

| Source claim or convention | Current implementation and evidence | Scope and next review |
| --- | --- | --- |
| Leading–trailing angle coordinates, `eq:ipolyAngleCoordinates`, TeX line 1619 | [Maintained operators](../packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py) and [fixture](../experiments/section9/fixture.json) use the directed opposite-edge convention. | Fixed boundary angle coordinates; electrical boundary voltages are separate variables. |
| Negative volume Hessian equals twice the grounded FEM matrix, `eq:ipolyHessian`, line 1641 | Integer grid gives `L_II=[[4,-1],[-1,4]]` and `K=[[8,-2],[-2,8]]`. Independent rational FEM assembly and high-precision numerical differentiation check this fixture. | A finite exact matrix identity and numerical derivative comparison; the general proposition and all hypotheses still need a full proof review. |
| Dirichlet-to-Neumann and Schur operations, `eq:ipolyDtN`, line 1733; `eq:ipolySchur`, line 1768 | Eliminating the first variable of `K` gives `15/2`, with determinant `8*(15/2)=60`. Boundary voltage `x/3` gives interior values `1/3,2/3` and energy `2/3`. | Dense small-matrix computations. No nearly-linear solver or complexity benchmark is supplied. |
| Forest determinant formula, `eq:ipolyForestDeterminant`, line 1791 | Exhaustive boundary-rooted forest enumeration gives fifteen unit-weight terms; multiplying by `2^2` gives `det(K)=60`. | Exact arithmetic on this finite fixture; no enumeration claim for other meshes. |

The [worked companion](../site/section9/index.html), [reproduction guide](../experiments/section9/README.md), [runnable archive](../site/section9/downloads/section9-reproduction.zip), and [result](../artifacts/section9/result.json) connect the text, implementation and evidence. The [initial mathematical review](../docs/execution/2026-10-31/section9-review.md) is preserved, with its three implementation findings addressed in the [independent re-review](../docs/execution/2026-10-31/section9-rereview.md). A separate [installed-package verification](../docs/execution/2026-10-31/package-verification.md) ran both the corrected wheel and extracted archive outside the source tree in a minimal NumPy/SciPy/mpmath environment. The result records the actual source and input hashes, methods, versions and numerical tolerances. Its source commit and dirty-state fields identify the run precisely.

Zero-weight square diagonals make this example non-strict Delaunay. Deformed off-origin angles are abstract angle structures; geometric closure is not asserted. The example supplies neither a strict convex-polyhedron certificate nor an interval enclosure. The local HTML is an authored companion, not the complete converted chapter. Browser layout and interaction remain unverified under the current local-server and browser URL restrictions.

## Section 15: Airy table awaiting executable provenance

Source location: `sec:quantumAiry`, line 4808; the six-row numerical table and scaled residual discussion occupy lines 5220–5251. The text describes evaluation of the exact cleared integrand through a real-integral representation of `log S_b`, displaced-contour quadrature, and comparison with the first Airy correction. It explicitly classifies the computation as a numerical normalization check rather than a certified error bound.

**Current status:** the six values and three scaled residuals are reported source results. The supplied material and reachable local histories do not provide their executable implementation, raw output, precision settings, contour parameters or tail/convergence study. They have not been independently replayed in this integration. The [recovery inventory](../docs/execution/2026-10-31/evidence-recovery.md) records the search and its limits.

The next computational task is to recover the original evaluator and raw runs, or implement a separately reviewed evaluator of the stated exact integrand. It must reproduce all six rows while recording normalization, branch and contour choices, arithmetic precision, truncation/tail diagnostics and convergence across settings. Evaluating the Airy approximation alone would not reproduce the asserted exact-integral calculation. A separate mathematical review must check the regular-family hypotheses and the contour, tail and uniform-correction arguments.

Before publication, either attach that reproducible evidence or revise the edition's wording to identify the values as retained, unreplayed results. This ledger makes no change to the theorem or its proof status.

## Section 30: torus diagnostic archive unavailable

Source locations: `sec:sharpdiagnostics`, line 11577; `subsec:torustraceexperiment`, line 12053; `eq:diagnostictracetriples`, line 12067. Lines 12092–12127 report enumeration to length 8192, two curve counts, four selected table rows, direct-trace and long-path precision checks, and event-order sensitivity bounds. Lines 12125–12127 say that source, the full block table, precision report and sensitivity tables accompany the monograph.

**Current status:** that advertised archive was not found in the supplied ZIP, either repository, their locally reachable code history, or the other supplied ZIPs. The counts, maxima, precision comparisons and sensitivity bounds remain unreplayed reported results. The [historical torus-bundle script](../research/ipoly/v8_torus_bundles.py) concerns angle structures and three-dimensional bundle volumes; it does not implement this Markoff/Farey length-counting experiment.

Recovery should first seek the original source and full output archive. A replacement implementation needs explicit unoriented-curve multiplicities, root/sector coverage, logarithmic trace recursion, exact event and half-event definitions, dyadic statistics, precision comparisons and conditional sensitivity calculations. Start with small cutoffs and independent direct-trace checks before a full length-8192 replay. Preserve the monograph's finite-range scope: decreasing excursions in the displayed rows do not prove an asymptotic bound.

If the original archive remains unavailable, correct its availability sentence before publication and clearly label any newly generated experiment as a replacement run. Do not reconstruct missing raw evidence from rounded printed rows.

## Further editorial and release work

The remaining claims, normalization fixtures, companion contradictions and proof dependencies are tracked in the [full audit](../audit/2026-10-31/monograph-audit.md) and [plan](../INTEGRATION_PLAN.md). Next steps include section modularization with all existing labels preserved, a complete computation/claim ledger, and a full HTML conversion pilot. The supplied PDF has passed a four-page visual sample; a reported font/CMap warning still needs release-build investigation. Authorship, text/companion licensing, distribution policy and public deployment are outstanding. No Site has been published by this checkpoint.
