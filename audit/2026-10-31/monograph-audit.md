# Monograph source inventory and computational coverage audit

Audit date: 2026-10-31. Scope: source inventory, build check, computational opportunities, selected mathematical-status checks. This is not a proof audit of the complete monograph.

## Sources and reproducible checks

Original archive: `/Volumes/Lexar/lambda/devel/polyhedra/polyhedra_moduli_quantum_monograph_sources.zip`.
Safely extracted copy: `/tmp/polyhedra-monograph-audit/polyhedra_moduli_quantum_monograph/`.
Below, `M:L` means line L of archive member `polyhedra_moduli_quantum_monograph/polyhedral_volumes_and_geodesic_identities.tex`; `R:L` means the archive's root README.

Read: README and entire file/section/citation/label inventories; main front matter (M:1–379), full Sections 1–4 (379–847), 8–9 (1271–2028), selected spectral-continuation, Airy, Dehn-filling, counting, and open-question passages; searched the entire TeX for numerical/claim/proof-status indicators; compared all companion files with local ipoly; searched Python files in both repositories for missing topic implementations. Main mathematical text is 13,629 lines / 569,093 bytes. Source package has 39 files, consisting of README + SHA256SUMS, 25 companion files, 10 figure-source files, main TeX and PDF.

Checks performed:

- ZIP absolute paths, parent traversal, symlinks rejected before extraction.
- Every SHA256SUMS entry matches extracted file bytes.
- All 25 `companion_ipoly/` files byte-match the corresponding present local `ipoly/` file, including the manuscript/PDF, README and 22 Python scripts. This is duplicate provenance, not an independently evolved codebase.
- Regex source audit: 601 labels, all unique; 218 citation-key uses referring to 124 bibliography items; no missing ref/eqref keys or citation keys, no unused bibitems. This is a syntactic check, not verification of cited propositions.
- Nine inline TikZ diagrams. Their separate `figures/*.tex` copies differ only because the inline versions add short optional captions for the list of figures. They are semantically consistent now, but are two editable sources of truth.
- Ran `latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=/tmp/polyhedra-monograph-audit/build polyhedral_volumes_and_geodesic_identities.tex` from the extracted source root. TeX Live 2025, latexmk 4.86a. Exit 0; final PDF 174 pages. Final log: no LaTeX/package warnings, no undefined references/citations, no duplicate labels, no overfull boxes, one underfull paragraph at M:1649–1659. No visual PDF inspection.
- Main organization is 7 parts, 32 numbered sections, 2 appendices; 35 theorem/proposition/lemma/corollary environments. No external image or bibliography build dependencies.

## Confirmed publication and reproducibility issues

1. **A claimed accompanying diagnostic archive is missing.** M:12052–12137 describes the torus Markoff experiment: enumeration through length 8192, 18,191,508 modular-torus curves and 18,486,116 asymmetric-torus curves; dyadic maxima, 100-digit comparison, long-path checks, sensitivity bounds. M:12122–12127 explicitly says source, full block table, precision report, and sensitivity tables accompany the monograph as a reproducible diagnostic archive. None appears in this ZIP. No Python implementation was found in either supplied repository by relevant name/keyword searches. Recover the original artifacts before treating these tables as reproducible; otherwise qualify the availability statement. The finite-range conclusions are already appropriately limited (M:12129–12137).

2. **Airy table lacks executable provenance.** M:5220–5251 contains six numerical rows, a description of exact double-sine quadrature, and the scaled residual values 1.208/1.211/1.209. No implementation, raw outputs, precision settings, contour parameters, or runtime environment accompanies it. The text already says this is a numerical check, not a certified error bound. Recover/reimplement the exact integrand, independently reproduce the table and error diagnostics, and attach generated-data provenance.

3. **The archive is already a substantial monograph draft.** It does not need to be assembled from nothing: title, abstract, principal-result map, seven parts, reading routes, diagrams, conventions and 124-item bibliography are present. It does need publication metadata: `\author{}` and `pdfauthor={}` are empty (M:13–14,84–87), no license is included for the monograph, and the main source remains a 569 KB monolithic `article`. Decide authorship/credits and rights intentionally; do not infer these from the code license.

4. **Figure maintenance duplicates sources.** R:13–19 explicitly says editing `figures/` alone will not update the monograph. Use one canonical set of figure sources, preserve the inline short captions when deduplicating, and generate web SVG/PDF renditions from those inputs.

5. **Editorial scaffolding remains.** M:1545–1546 refers to a nonexistent `tmp/ipoly_monograph_bridge_bibliography.tex`; M:13570–13572 contains stale insertion instructions. These are comments, not build failures. Remove during modularization. The archive README says numerical scripts were not rerun during the editorial revision (R:47–49).

6. **Companion manuscript duplication needs a clear reading policy.** Section 9 already integrates the central ipoly arguments and cites the companion (M:1547–1559). Preserve ipoly's original manuscript as a historical companion, but avoid two separately maintained versions of identical theory. Retain unique computational details in appendices/examples and link them to the canonical text.

## Mathematical status and review priorities

No new theorem-level mathematical defect was established in this bounded inventory. The following are explicit limitations that must remain visible on the website and in the theorem-to-code registry, plus high-value review targets:

- **Coordinate-specific Hessian identity:** `-D_u^2 V = 2 L_II` is for positive corner-angle structures on a planar disk with prescribed edge sums and leading–trailing coordinates `alpha_c=alpha_c^0+u_i-u_j`, fixed boundary u (M:1561–1681). It is not automatically the same Hessian as a generic sphere-vertex coordinate optimizer or a 3-manifold gluing problem. Section 9 says so and retains positive feasibility, interior compatibility and convex-boundary admissibility. Tests and demonstrations must name the coordinate map and constraints.
- **Nonlinear complexity:** the barrier `F=-sum log sin(alpha)` and `F-tV` compatibility estimate are stated/proved M:1801–1860. Bound M:1871–1874 assumes initial centering. M:1885–1894 explicitly separates the nearly-linear linear solver from the entire nonlinear realization, with an approximately n^(3/2) arithmetic-work scale after centering and separate feasibility/precision/certification costs. Do not label all toolkit Newton methods nearly-linear certified realization.
- **WP/DM normalization and chambers:** M:1409–1460 gives `V_WP(A)=2^{-d} A^d V_CH + O(A^{d+1})`; M:1462–1516 spells out final-chamber bounds and nonuniformity at balanced weights. This factor was fixed in front matter per R:55–59. Copy all dimensions, label/orbifold conventions and chamber conditions into generated examples.
- **Conditional spectral continuation:** M:3650–3691 explicitly requires locally uniform L1 control and charge continuation, says the estimate is not proved here, and distinguishes the independent first-moment/period derivation from the infinite spectral derivation. An interactive calculation can check finite fusion identities; it cannot discharge the missing uniform analytic bound.
- **Airy theorem scope:** M:4807 onward is for a specified pole-cleared integral and the regular one-parameter family. The proposed extension to arbitrary nondegenerate shapes and global quantum gluing remains a question (M:12556–12583). Highest-value independent review: normalization of exact integral, full contour/tail argument (M:5058–5116), and uniform first correction (M:5117–5218).
- **Dehn filling:** M:5444–5610 is a local holomorphic critical-value/analytic-germ claim. M:5653–5795 makes the transfer to global quantum invariants conditional. Preserve peripheral u,v conventions and distinguish local Taylor checks, numerically filled manifolds, torsion factors, and global quantum asymptotics.
- **Dynamics:** the two-endpoint counting-to-mixing implication retains endpoint and derivative norms (M:9491–9844). The explicit genus-two result is only the nonsquare `(2,2)` stratum (M:10064–10820). These are not a proof for all strata or a consequence of a scalar count alone.
- **Sharp counting:** the reported experiment proves no asymptotic linear or sublinear bound; the exact row statistic also requires a verified supporting normal/flat point and sufficient height precision (M:12007–12049). Arithmetic and geometric assumptions are separate (M:12163–12511).

### Recent-source verification

The cited OpenAI preprints are real primary-source entries, not missing or invented citations:

- https://raw.githubusercontent.com/openai/math/main/preprints/The-Quasi-Riemann-Hypothesis-September-30-2026/README.md confirms OpenAI author, 30 September 2026 date, and title with Re(s)>7/8.
- https://raw.githubusercontent.com/openai/math/main/preprints/The-Quasi-Riemann-Hypothesis-October-5-2026/README.md confirms 5 October 2026, title, and human assistance.
- https://github.com/openai/math says the collection includes results at different verification stages, warns about possible issues in unformalized results, calls the manuscripts raw research data, and mentions human editing of the 11/12 writeup.

Both PDF GitHub pages are live. The web extractor could not parse raw PDFs due application/octet-stream; their full proofs, precise formalization coverage, and mathematical correctness were not checked. Existing conditional wording at M:12272–12310 and M:13555–13568 is appropriate. Pin exact source revisions and verify theorem status before publication. Do not convert these into unconditional inputs because the publisher is OpenAI. The same version-pinning/status workflow should cover Doan–Li–Nguyen v3 (M:12138–12160; not independently audited here).

## Complete section-to-computation map

`Existing` below refers only to the supplied material examined. Outside the volume/Hessian/3-manifold companion area, the archive contains formulas and tables, not corresponding executable modules. A keyword scan of all Python files in both repositories found no matches for Markoff, Airy, double-sine, Liouville, Weil–Petersson, Mertens, McShane, Neumann–Zagier, Dehn filling, Deligne–Mostow, or hypergeometric.

| Section and source start | Computable topic / useful artifact | Existing support and limit |
|---|---|---|
| 1, M:379 | Convention registry; known V_0,3, V_0,4, V_1,1 normalization fixtures; dimension, labels and orbifold factors | Formulas only; add exact fixture tests shared by later modules |
| 2, M:431 | Generate ideal angle cells, face-perimeter constraints, nonfacial-cut feasibility; automorphism-weighted small-n integration | Toolkit graph/Rivin machinery is adjacent; WP disintegration and cell measure need new code |
| 3, M:525 | Ambient cross-ratio -> lambda lengths/angles; Jacobian; analytic/numerical integral V_0,4=2pi^2; degeneration explorer | Geometry primitives reusable; dedicated WP density/integration new |
| 4, M:650 | Hyperideal Gram admissibility, truncation side/boundary lengths, fixed-L solve, Poisson/Pfaffian density, local quadrature | New module; full cellwise integral explicitly an open calculation, not a promised implemented theorem |
| 5, M:848 | Piecewise WP/cone polynomial evaluator with explicit wall detection | New; preserve signature/chamber predicates |
| 6, M:976 | Torus–sphere covering/normalization calculations | New exact checks; keep stack/effective factor |
| 7, M:1045 | Euclidean cone weights, periods/hypergeometric functions, Hermitian area, collision cone angles, elliptic equal-weight example | New; branch tracking and collision limits matter |
| 8, M:1271 | Light-subset/wall enumeration, final-chamber polynomial, McMullen partition sum for V_CH, exact n=4 cases and small-A limits | New; high-value inexpensive symbolic/rational tests, independent formulas for cross-checking |
| 9, M:1547 | Angle-coordinate volume/gradient/Hessian, FEM identity, Schur response, rooted-forest determinant, barrier path, flips | ipoly v1/v5/v9/v13/v14/v19 etc. and toolkit algorithms support parts; consolidate verified shared primitives, do not equate distinct coordinates |
| 10, M:2029 | Introductory tetrahedral weights, figure-eight quantum sum/volume trend, dilogarithms, stationary/Gaussian/Airy illustrations | New pedagogical computations; separately budget any exact state sums |
| 11, M:2925 | Small compact-polyhedron scale and volume expansion; prescribed family vs fixed area/shape comparison | New compact-geometry work; ideal-only engine cannot supply this by a flag |
| 12, M:3141 | First-moment/area integration, logarithmic curvature, Fricke character surface, torsion density, normalization comparisons | New; exact/symbolic low-dimensional checks are useful before high-dimensional numerics |
| 13, M:3590 | Four-point hypergeometric periods, finite fusion matrix, Hermitian pairing, explicit density/total volume, logarithmic equal-weight limit | New; finite formulas computable independently of unproved spectral tail hypothesis |
| 14, M:4217 | Double-gamma/sine factors, finite sine matrix, screened Gram rank, regular tetrahedron compact family/fold | New; special-function conventions and rank/branch checks essential |
| 15, M:4807 | Stable log-double-sine evaluator, exact contour quadrature, Airy first correction and uniform-window residual plots | Numerical table exists but executable evidence missing; recover/reproduce first |
| 16, M:5295 | Peripheral Hessian response, cusp shape, Legendre critical value, quartic/sixth-order Dehn coefficients, torsion, figure-eight benchmark | ipoly SnapPy/gluing code adjacent, but no supplied Dehn-filling implementation located; add optional SnapPy reference comparisons |
| 17, M:6227 | Unfolding multiplicities and known constant-series checks on examples | New; finite truncation requires explicit tail remainder |
| 18, M:6360 | Pants trace relation, figure-eight length, local double-cover examples, positive single-length kernel | New surface-geometry module; do not confuse with knot figure-eight from §10 |
| 19, M:6551 | Pants arc length under twist, holonomy products and derivative | New; reusable base for §§20–22 |
| 20, M:6692 | Exact torus twist function and integral; partition-of-unity/orbit-series convergence | New accessible interactive illustration with controlled truncation |
| 21, M:6791 | Endpoint/direction matching and stationary gluing equations across cuffs | New prototype; global itinerary control is open |
| 22, M:6837 | Truncated cusp arcs, McShane gaps and orthospectrum kernels | New; retain geometric index sets and truncation conventions |
| 23, M:6989 | SL2 trace polynomial recursion, skein/bracelet coefficients, finite atom distributions, iterates, figure-eight cancellation | New exact symbolic engine; finite examples can verify signs/normalizations but not infinite analytic convergence |
| 24, M:7848 | Dehn–Thurston lattice counting, primitive/connectivity filters, support selectors and finite isolation | New; separate geometric constants from observed finite counts |
| 25, M:8484 | Global one-crossing filter, fixed-linear-selector obstruction, truncated length-valued Euler product and first atoms | New; exact polynomial identities/finite truncations first |
| 26, M:8820 | Finite Markov transfer matrix: compare counting and mixing rates; illustrate spectral obstructions | New small standalone experiment; not a numerical proof for Teichmüller flow |
| 27, M:9221 | Weighted two-endpoint kernels, derivative weights, arithmetic endpoint examples | New; finite diagnostics require declared norms and tail cutoffs |
| 28, M:10064 | Genus-two quadratic differential/double covers, marked-torus parameters, finite lattice sums with endpoint weights | New; high-value exact finite-lattice examples, keep nonsquare (2,2) scope |
| 29, M:10822 | Primitive pole-to-pole arc observables, affine displacement sums, Gaussian two-mark correlation, rotation norms | New; numerical integration can compare explicitly stated norms/correlations |
| 30, M:11576 | Markoff/Farey enumeration with multiplicities, dyadic main-term-free statistics, row/divisor diagnostic, high-precision sensitivity | Extensive reported computation but missing claimed archive; first recovery priority |
| 31, M:12163 | Möbius inversion of all-point/primitive counts, empirical geometric discrepancy and arithmetic contribution separately | New; do not infer RH/zero-free-region or asymptotic error bound from finite data |
| 32, M:12515 | Research targets with dependency/status links | Registry, not automatic implementation scope; hyperideal full integration, general Airy/gluing, certified realization, sharp error remain research |
| Appendix A, M:12710 | Symbolic Fricke trace/Poisson normalization test of WP factor | New small exact regression fixture |
| Appendix B, M:12757 | Convention dictionary: normalization, boundary variables, quantum level, measures | Canonical metadata/schema for every computation and UI |

## Copy-ready source patterns and evidence boundaries

- Preserve source label names as stable website anchors: `sec:ipolybridge`, `prop:ipolyHessian`, `eq:ipolyHessian`, `eq:ipolySchur`, `eq:ipolyForestDeterminant`, `sec:quantumAiry`, `sec:sharpdiagnostics` etc.; there are no duplicate labels now.
- Reuse existing reading-route and result-status prose from M:235–370 as editorial scaffolding, not as evidence that the mathematical claims have been newly checked.
- Low-cost independent normalization fixtures: M:400–407 (WP base volumes), M:568–615 (tetrahedral WP density/integral/disintegration), M:1477–1515 (flat-limit polynomial examples), Appendix A M:12710–12755.
- Preserve existing condition statements rather than moving them only to footnotes: M:3650–3691 (spectral tail), M:1885–1894 (solver complexity scope), M:12114–12137 (floating-point sensitivity and asymptotic limits).
- Reuse the actual companion files by canonical path after merge; hashes establish they need no three-way conflict reconciliation against archive copies.
- New computed table/figure contract should record source equation/statement IDs, code entry point, input data, seed (if applicable), precision/tolerances, dependency versions, commit, output checksum, and result status (symbolic identity, numerical check, interval certificate, conditional illustration). This is a proposed contract, not an existing one.

## Confidence and gaps

High confidence: archive inventory, byte identity, hash integrity, source-reference completeness, successful TeX build, missing advertised diagnostic archive, missing executable Airy provenance, exact scope qualifications quoted above.
Moderate confidence: topic-wide missing-code map, because all Python sources were searched by relevant terms and repository inventory but not every function was proved incapable of covering those topics indirectly. Companion/core coverage should be merged with the dedicated code-audit reports.
Not performed: entire-paper proof verification, all 124 external references, PDF visual review, full replay of reported numerical tables/campaigns, Sites conversion/rendering, or broad literature completeness/novelty assessment. Publication should require focused independent review of the most consequential new arguments, not merely a green TeX build or passing code tests.
