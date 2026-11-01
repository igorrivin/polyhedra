# Computational status of the monograph

This ledger records the maintained numerical foundations and three computational passages in the [canonical source](polyhedral_volumes_and_geodesic_identities.tex). Section 9 has now been extracted and revised following the bounded mathematical review required by the [integration plan](../INTEGRATION_PLAN.md); the original source snapshot and supplied reference PDF retain their original bytes. A reproduced finite example does not audit a general proof, and missing computational evidence does not by itself disprove a mathematical statement. Historical line references below refer to the monolithic source at `26b3c134d9308d345cb76f1240db9de982b2e5a6`; stable labels identify the current text.

## H³ numerical foundations

The [numerical errata](numerical-errata.md) records the bounded software corrections and changed values. The [execution checkpoint](../docs/execution/numerical-correctness-2026-10-31/README.md) preserves author results, independent review findings and their separate resolution stages. Existing scientific tables and research outputs have not been comprehensively replayed or rewritten.

| Evidence type | Maintained contract | Limit |
| --- | --- | --- |
| Binary64 volume | [Canonical Bloch–Wigner kernel](../packages/volume-toolkit/docs/numerical-precision.md), explicit method in final angle/optimizer reports; finite large arguments handled without magnitude overflow. | Floating-point values, not certified enclosures. Legacy `fast` defaults remain finite Fourier approximations. |
| Multiprecision evaluation | mpf-returning kernels preserve supported inputs and scope working precision; legacy `exact`/`eval_only` names alias numerical mpmath evaluation. | High-level output and Qhull/projection geometry remain binary64; extra working digits cannot recover lost input information or validate topology. |
| Angle feasibility and stationarity | [Common-margin LP and full numerical KKT audit](../packages/volume-toolkit/docs/rivin-numerics.md), with feasible steps and active-constraint release. | A verified finite angle-program witness or numerical stationary point is not a global embedding, exact infeasibility or interval-optimality certificate. Exact flat-angle optima are outside the differentiable solver. |
| Optimizer endpoint | [Fresh canonical endpoint checks](../packages/volume-toolkit/docs/optimizer-result-contract.md), separate raw convergence and candidate-validity fields, strict schema-v2 JSON. | A valid unconverged candidate can be retained; no global maximum follows. Historical v1 files retain their original status. |
| Exact finite identities | Section 9 integer/rational matrices and forest enumeration; the strict LP fixture's rational primal and dual witnesses establish common margin `1/7`. | Exact statements about the named fixtures only. They do not certify general numerical routines. |

The free-corner-angle optimizer with dihedral inequalities and Section 9's prescribed-dihedral leading–trailing coordinates describe different feasible families. A KKT result for the former is not a proof of a coordinate-space assertion in the latter. The imported [historical companion](../research/ipoly/duffin_rivin_volume_laplacian_solvers.tex) remains unchanged; the [reconciliation note](companion-reconciliation.md) records the reviewed positivity, exterior-angle Schläfli sign, complexity and benchmark corrections.

## Section 9: reviewed mathematics and reproducible finite examples

The [modular chapter](chapters/09-volume-hessians.tex) and [claim ledger](claims/section9.json) now separate general derivations, checked external theorem statements, conditional algorithmic consequences, exact finite checks, numerical comparisons and open questions. The [core audit](../docs/execution/section9-chapter-2026-10-31/math-audit.md) supplies coordinate completeness and grounded strictness, including zero Delaunay weights. The [companion audit](../docs/execution/section9-chapter-2026-10-31/companion-audit.md) supplies the finite-centering proof and source-scope checks. Neither report claims a complete re-refereeing of the cited literature or the rest of the monograph.

| Source claim or convention | Current implementation and evidence | Scope and next review |
| --- | --- | --- |
| Leading–trailing angle coordinates, `eq:ipolyAngleCoordinates` | [Maintained operators](../packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py) and [fixture](../experiments/section9/fixture.json) use the directed opposite-edge convention. | Completeness is proved for a disk; an exact annulus counterexample records the topology restriction. Fixed boundary angle coordinates and electrical boundary voltages are separate variables. |
| Negative volume Hessian equals twice the grounded FEM matrix, `eq:ipolyHessian` | Integer grid gives `L_II=[[4,-1],[-1,4]]` and `K=[[8,-2],[-2,8]]`. Independent rational FEM assembly and high-precision numerical differentiation check this fixture. | The general identity, CCW gradient convention and grounded kernel are derived in the chapter and independently audited. A planar FEM realization is additional geometry; arbitrary deformed angles remain abstract. |
| Dirichlet-to-Neumann and Schur operations, `eq:ipolyDtN`; `eq:ipolySchur` | Eliminating the first variable of `K` gives `15/2`, with determinant `8*(15/2)=60`. Boundary voltage `x/3` gives interior values `1/3,2/3` and energy `2/3`. | General energy-minimization and block identities are proved; computations use dense small matrices. No nearly-linear solver or complexity benchmark is supplied. |
| Forest determinant formula, `eq:ipolyForestDeterminant` | Exhaustive boundary-rooted forest enumeration gives fifteen unit-weight terms; multiplying by `2^2` gives `det(K)=60`. | The general incidence-minor proof is separate from exact finite enumeration. Enumeration is an oracle for this fixture, not an efficient general algorithm. |
| Barrier and short-step bounds, `prop:ipolyCompatibility`; `eq:ipolyStepBound` | The [dense affine-angle solver](../packages/volume-toolkit/ideal_poly_volume_toolkit/angle_barrier.py) implements the log-sine barrier, separately budgeted centering and the specified path schedule. Its [fixed-fixture driver](../experiments/section9/barrier_run.py) compares against independent multiprecision references and records all accepted iterates. | The mathematical finite-center bound is `17m/(12t)` at decrement at most `1/4`; its binary64 evaluation is a numerical estimate. No certified energy-error guarantee or nearly-linear backend is supplied. Feasibility construction, initial centering, precision and geometric error have separate costs. |
| Full three-manifold criticality, `subsec:ipolyThreeManifolds` | Checked scope of the Casson–Rivin theorem and an exact local non-SDD Hessian example. | Requires an orientable ideal-triangulated compact manifold with torus boundary and full angle-space criticality, including peripheral directions. No complete peripheral basis, solver or metric certificate is supplied. |

The [worked companion](../site/section9/index.html), [reproduction guide](../experiments/section9/README.md), [runnable archive](../site/section9/downloads/section9-reproduction.zip), and [result](../artifacts/section9/result.json) connect the text, implementation and evidence. The [initial mathematical review](../docs/execution/2026-10-31/section9-review.md) is preserved, with its three implementation findings addressed in the [independent re-review](../docs/execution/2026-10-31/section9-rereview.md). A separate [installed-package verification](../docs/execution/2026-10-31/package-verification.md) ran both the corrected wheel and extracted archive outside the source tree in a minimal NumPy/SciPy/mpmath environment. The result records the actual source and input hashes, methods, versions and numerical tolerances. Its source commit and dirty-state fields identify the run precisely.

Zero-weight square diagonals make this example non-strict Delaunay. Deformed off-origin angles are abstract angle structures; geometric closure is not asserted. The example supplies neither a strict convex-polyhedron certificate nor an interval enclosure. Its authored HTML companion remains distinct from the complete chapter conversion produced by the [chapter build](../site/README.md). Build, PDF rendering and browser verification have separate status in the [chapter execution evidence](../docs/execution/section9-chapter-2026-10-31/README.md).

The separate [barrier examples](../site/section9/barrier.html),
[result](../artifacts/section9/barrier-result.json), and
[reproduction archive](../site/section9/downloads/barrier-reproduction.zip)
cover the new dense solver. Its contract requires a supplied positive affine
slice; it does not infer that a chosen basis spans every geometric deformation.
The result distinguishes a finite gap estimate, a centered point, a reached
target parameter, and numerical convergence. It returns unsuccessful states
for exhausted budgets or failed numerical safeguards, and never marks a result
as formally certified. The [barrier checkpoint](../docs/execution/section9-barrier-2026-10-31/README.md)
owns the new numerical and export review. The earlier mathematical review is
still tied to its frozen source hashes, with proof mathematics retained and
computational prose updated separately. Original chapter-generation reports
remain historical records rather than checks of these changed bytes.

At the numerical-correctness checkpoint, the result and reproduction archive were regenerated from clean source `9188e0624cdf6d9949af1f620336eff67c8b59d7` and committed as `29440cfbfcdaa23711cfdac4e09bf5f939404273`. That run passed all twelve numerical checks and exact fixture identities, with all seven recorded source/book hashes matching. Its archive was extracted outside the checkout and replayed in the minimal environment, verifying all nine payload hashes and its clean originating commit. These are results for that source state, not hash verification of the subsequently revised chapter; see the [numerical closeout](../docs/execution/numerical-correctness-2026-10-31/closeout.md). A later generated result must identify its own source and artifact provenance. Earlier source `c02b358de5a6f724faf3368a641ba64f5841d859` and artifacts `74e2abc67e434e0d7eadf70d7becaa6de2f77785` remain preserved in Git history and the first checkpoint. The [preliminary installed-wheel and detached-archive replays](../docs/execution/numerical-correctness-2026-10-31/integration-section9-replays.json) remain separate records of the modified checkout examined before the clean-source run.

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

The remaining claims, normalization fixtures and proof dependencies are tracked in the [full audit](../audit/2026-10-31/monograph-audit.md) and [plan](../INTEGRATION_PLAN.md). Section 9 now has a modular source, a claim ledger and a chapter conversion workflow; the rest of the monograph still needs its corresponding review, modularization and evidence coverage. The supplied PDF's earlier four-page visual sample does not verify a new build. Authorship, text/companion licensing, distribution policy and public deployment are outstanding. No Site has been published by this revision.
