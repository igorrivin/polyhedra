# Polyhedra integration and correction plan

Analysis date: 31 October 2026. Scope: combine the two repositories and supplied monograph into one maintained research repository, correct the numerical software, and prepare a reproducible web and PDF monograph for OpenAI Sites. The original analysis and phase gates below are retained as the implementation plan. The progress record here distinguishes completed local increments from the remaining publication work; the planning-baseline observations are not assertions about the current checkout.

## Current execution progress

The [first integration checkpoint](docs/execution/2026-10-31/README.md) records the history-preserving import, reproduced defect corrections, package checks and initial Section 9 computation. The [numerical-correctness checkpoint](docs/execution/numerical-correctness-2026-10-31/README.md) records the precision, angle-solver and result-contract corrections. The original repositories, received archive, historical companion and supplied reference PDF remain preserved. Optional test dependencies are still unavailable; the latest full-suite failures and collection errors have not been relabelled as a pass.

The [Section 9 chapter checkpoint](docs/execution/section9-chapter-2026-10-31/README.md) now records independent approval of the modular chapter, its 26-claim ledger and the historical-companion reconciliation. All 601 original labels remain, with six subsection labels added. The finite-centering and controlled inexact-step arguments are proved with explicit hypotheses; the maintained computation does not yet implement that barrier algorithm. The complete PDF/HTML chapter, numerical companion and source/reproduction archives have been generated from a clean source commit and verified locally, including a fresh detached numerical replay and all-page PDF render comparison. The [closeout](docs/execution/section9-chapter-2026-10-31/closeout.md) records the distinct source and artifact commits. This is a completed local chapter checkpoint, not a public edition.

This completes the bounded mathematical-review portion of Phase 4 for Section 9, not the whole phase for the book. The current converter pilot uses the strict Pandoc/LaTeX workflow described in the [build guide](site/README.md); the converter alternatives below remain planning context. Airy and torus evidence recovery, broader chapter review and computational coverage, browser verification, publication metadata/licensing and Sites deployment remain outstanding. No Site has been published.

## Recommendation

Create one canonical `polyhedra` monorepo with preserved histories, retain `ideal_poly_volume_toolkit` as its existing installable Python package, and use the supplied monograph as the canonical text. Its Section 9 already integrates the central `ipoly` mathematics. Preserve the original `ipoly` manuscript and scripts as attributed historical material, then extract their useful algorithms into tested modules and named experiment drivers.

Keep LaTeX as the mathematical source of truth. Generate both the downloadable PDF and a chapter-based HTML edition, with stable theorem/equation anchors and explicit links to computations. The first Sites edition should serve generated text, figures, small interactive demonstrations, and reproducible computation packages. Heavy Python/SciPy/SnapPy calculations should run in the research environment and publish checked outputs; a hosted numerical job service is a separate later project.

Correctness and reproducibility come before broad file rearrangement. In particular, repair the two reproduced incorrect-success/certification cases, recover the missing numerical artifacts, and reconcile the older companion's mathematical claims before making them authoritative website content.

## Planning baseline evidence

Detailed source locations, commands, outputs, and limitations are in the [toolkit audit](audit/2026-10-31/toolkit-audit.md), [ipoly audit](audit/2026-10-31/ipoly-audit.md), and [monograph audit](audit/2026-10-31/monograph-audit.md). The [source inventory](audit/2026-10-31/source-inventory.json) records every tracked source file and archive member with SHA-256 hashes. `M:line` below denotes the main TeX member inside the monograph ZIP, as defined in the monograph audit.

| Source | Verified local state | Integration consequence |
| --- | --- | --- |
| `ideal_poly_volume_toolkit/` | Clean `main`, commit `cc6b689652ce735f2098bb0a3235089210d764df`; 925 tracked files, 273 Python files, 46 package modules; 76,586,772 logical tracked bytes; 412 LFS paths materialized | Keep its working packaging, APIs, tests, schemas, and ownership documentation. Reconcile its existing improvement roadmap with this plan. |
| `ipoly/` | Clean `main`, commit `30ef40e23005509bd94d26f27dc48ea778832a50`; manuscript, 22 scripts, two duplicate historical ZIPs; 28 tracked files | Import history and provenance; turn current source-text execution and repeated solvers into proper modules. |
| Monograph ZIP | SHA-256 `8f28b07686ea579a7dfb7b88ccef5c12bdd50b6e328737d5a8a79f6e06ba92dc`; all included checksums verified | Preserve this original archive as the received snapshot. |
| `companion_ipoly/` inside ZIP | All 25 files are byte-identical to the matching local `ipoly` files | There is no third divergent codebase to merge. Record the duplicate mapping instead of maintaining another copy. |
| Main monograph | 174-page successful rebuild; seven parts, 32 sections, two appendices, nine figures, 124 bibliography items, 601 unique labels | This is already a substantial monograph draft. Work is correction, modularization, computational support, and publication design. |

The workspace root is not presently a Git repository. Configured origins were read; live remote heads, visibility, and CI were not checked. No relevant ignored source files were found in either checkout.

Verification performed: all 295 tracked Python files parsed; the monograph rebuilt with no unresolved references/citations or overfull boxes; small existing numerical examples and targeted defect probes ran using an existing NumPy/SciPy environment. The canonical reconstruction probe had approximately 2.6e-14 degrees angle error and 2.4e-15 closure error. The abstract tetrahedral zero-shear certificate returned index 12. Three original `ipoly` checks and a small sparse-solver example also ran successfully. Full pytest, package installation, the numerical tables, SnapPy comparisons, and PDF visual inspection remain outstanding. A build is not a proof audit or a numerical replay.

## Corrections to prioritize

P0 means required before presenting the affected result as supported. P1 means the next integration or quality increment. P2 means substantial extension or research; it must have a stated scope rather than become an implicit requirement to solve an open problem.

| Priority | Finding and evidence | Correction and acceptance condition |
| --- | --- | --- |
| P0 | `rivin_holonomy.py:763–770,884–895` converts accepted real shears to float before deciding exact zero. Nonzero `Fraction(1,10**400)` values receive `certified_declared_exact_zero_shear`. | Test the exact declaration before conversion, or reject values that cannot be represented under the input contract. Nonzero rational underflow must never produce an exact-zero certificate. Preserve the independently valid abstract integer certificate. |
| P0 | `geometric_realization.py:198–260,301–306`: cyclically rotating one face reverses its realized orientation while `success=True`. | Consolidate on the maintained residual-bearing reconstruction path, or repair the legacy path. Require invariance under cyclic face rotation and relabeling, plus closure/orientation/embedding checks. Placement of all vertices alone is not success. |
| P0 | `rivin_delaunay.py:774–793`: public gradient clamps to zero near endpoints; Hessian has the wrong sign near pi. | Use mathematically correct stable formulas on a declared interior domain, and define endpoint behavior explicitly. Verify signs and asymptotics against an independent reference. These helpers have no current internal callers; the observation does not invalidate the active interior Newton formula. |
| P0 | `geometry.py:175–177,218–226,250–263,326–372` uses float inputs/outputs in paths called “exact”; precision is changed globally. Final angle-optimizer values use 64 Fourier terms (`rivin_delaunay.py:1103–1105`). | Separate binary64, arbitrary-precision evaluation, exact algebraic statements, and rigorous enclosures. Scope precision locally. Re-evaluate accepted results with the accurate canonical kernel; preserve historical approximations with their method metadata. Test degenerations and removable special-function values. |
| P0 | Old realization documentation says every feasible LP angle assignment is realizable and imposes boundary sums of 2pi (`docs/GEOMETRIC_REALIZATION_README.md:5–13`). | Distinguish angle feasibility, length/holonomy compatibility, compatible maximization, and validated coordinate realization. Correct interior-versus-boundary constraints before reusing this prose. |
| P0 | `ipoly` asserts a unique positive-angle maximizer at TeX:898–900 while later allowing flat triangles at :918–928; :1116 also contradicts its barrier iteration result. | Separate the open domain from its closure, audit boundary uniqueness, and distinguish plain Newton from the centered barrier method. Keep the no-needle proposition at its actual scope; do not promote it into a complete degeneration classification. |
| P0 | `ipoly` uses exterior angles but writes the interior-angle Schläfli sign at TeX:934. | Reconcile the angle and signed-length conventions throughout both texts and code. With the usual signed length and exterior angle, the sign is plus. The criticality condition itself is unchanged. |
| P0 | `v21_snappea_vs_ours.py:18–22` uses floating QR while the text calls row removal exact; :45 ignores a detected constraint violation. Several scripts dereference unsuccessful LP results. Boundary-only triangle/square examples crash in `v10.Run`. | Check all solver statuses, retain all original constraints for residual checks, handle zero-dimensional domains, and either supply exact rank evidence or label numerical rank selection honestly. Add explicit failure and convergence results. |
| P0 | `ipoly`'s 6,000-tetrahedron “800x” comparison excludes LP time: 129/0.16 versus 129/(0.99+0.16), about 112 before other setup (TeX:982–991). | Report solver-only and end-to-end costs separately; replay on fixed triangulations with versions, timings, accuracy, and full work accounting. Neither number is a fresh benchmark from this audit. |
| P0 | Main text M:12122–12127 says a torus diagnostic archive accompanies the book, but it is absent. The Airy table M:5220–5251 also lacks code and raw output. | Recover original artifacts if available; otherwise implement and independently reproduce the stated computations. Until then correct the availability claim and mark the tables as awaiting reproducibility verification. Do not backfill invented provenance. |
| P1 | Duplicated volume/threshold helpers, distribution logic in CLI and GUI, broad `pointset_to_fuchsian.py`, and `ipoly` source splicing | Extract by mathematical responsibility and delegate adapters to one owner. Preserve compatible entry points during migration. Narrow the misleading `invariant_trace_field_signature` name: its current near-integer generator-trace diagnostic is not a trace-field computation. |
| P1 | Figures exist both inline and as separately editable files; author metadata is empty; book/ipoly licensing is unstated | Use one figure source, populate authorship/credits and citation metadata, and make an explicit text/code licensing decision. Retain toolkit MIT notices without assuming they license the monograph. |

The [reproduction script](audit/2026-10-31/toolkit-probes.py) and [observed results](audit/2026-10-31/observed-probe-results.json) document the first two defects and the passing control cases. They are audit probes, not a replacement for the package test suite.

Additional review targets, not newly demonstrated failures: active-set multiplier/release logic, residual-based optimizer success, bit-complexity and inexact-solve assumptions, separator claims, and boundary/global uniqueness. Known non-generic H4 pole dependence and broken facet optimization remain explicitly experimental until repaired. Reconcile the newer RL result artifacts with dated status documents before repeating any RL performance conclusion.

## Proposed repository and ownership

The proposed structure is a destination, not a request for one large move. Keep the existing toolkit layout intact during the initial import; create new packages or subdirectories only when the first implementation needs them.

```text
polyhedra/
  README.md
  CITATION.cff
  LICENSES/
  provenance/                       # source commits, archives, import and path maps
  packages/
    volume-toolkit/                  # existing distribution, namespace and tests
      pyproject.toml
      ideal_poly_volume_toolkit/
      tests/
      bin/                          # compatibility adapters during migration
      docs/                         # existing package ownership and API docs
      results/                      # existing corpus retained until classified
    companion/                      # new, only as non-toolkit computations appear
      pyproject.toml
      src/polyhedra_companion/       # moduli, quantum, curve/counting computations
      tests/
  book/
    main.tex
    preamble.tex
    chapters/                       # initially preserve current sections and labels
    figures/                        # canonical TikZ sources
    bibliography/                   # one bibliography source
    generated/                      # generated tables and figure includes
  research/ipoly/                   # unchanged historical manuscript and v* scripts
  experiments/                      # named current drivers, inputs and run manifests
  artifacts/                        # curated new results and artifact index
  site/                             # book presentation, small demos, export tooling
  docs/                             # integrated architecture, corrections, claim map
  audit/                            # this audit and subsequent review evidence
  .github/workflows/                # explicitly reconciled monorepo workflows
```

The computational library retains the import name `ideal_poly_volume_toolkit` and existing optimizer command. General WP, quantum, and curve-counting calculations belong in the computational companion, which depends on the toolkit where appropriate. Reusable volume, angle-structure, and geometry kernels have one toolkit owner; the companion must not introduce another Lobachevsky implementation or another acceptance predicate for the same geometry.

Recommended ownership boundaries:

- `geometry.py` and the optional Torch layer: volume kernels, projection, numerical conventions. Refactor internal helpers only after parity tests.
- `rivin_delaunay.py` and `rivin_zero_shear.py`: distinct planar feasibility/optimization and strict coordinate-audit responsibilities. Reuse them from experiment drivers.
- A small variational module, created when extracting `ipoly`: sparse corner/incidence operators, constrained derivatives, Schur complements, and barrier support. Keep fixed-dihedral, variable-dihedral, and three-manifold problems distinct in their constraint models.
- `rivin_holonomy.py`: holonomy and abstract exact zero-shear certificates; numerical geometry remains separately assessed.
- Existing `optimization.py` and a package-owned distribution service: shared reusable workflows. GUI and CLI are adapters.
- `polyhedra_companion`: explicit book computations outside ideal-polyhedron geometry; optional SnapPy adapters isolate manifold dependencies.
- Existing higher-dimensional and RL features: retained research modules with their current scope and evidence labels. They do not need to dominate the monograph or delay an H3-focused publication increment.

### History and artifact migration

1. Capture both original branch/tag sets, source manifests, Git backups, and LFS objects. A Git bundle alone does not back up LFS payloads. Verify restoration before relying on backups.
2. Build the integrated repository in a fresh staging checkout. Import each original history under a prefix without squashing or rewriting the original commits. Record old commit IDs, import commits, and old-to-new paths.
3. Import the monograph as a named source snapshot. Keep the original ZIP and its checksum; replace its active duplicate companion references with links to the single `ipoly` import.
4. Preserve current result files and their classifications during this first step. Use manifest-driven moves later. Scope LFS attributes correctly after prefixing; preserve canonical versus historical versus superseded status.
5. Audit every workflow before enabling it. The existing HF workflow force-pushes `main` to the old Space on every push; do not carry that behavior into the monorepo. Retain HF only as an explicitly scoped application deployment if still wanted. Review the maintenance job's unconstrained dependency upgrades and automatic edits.
6. Verify history reachability, source checksums, LFS materialization, installation, imports, scripts, tests, document links, and Docker build context before making the new repository canonical. Retain recoverable originals through the transition; no history deletion or force-push is required.

The single maintained repository may have a GitHub remote and a derived Sites publishing checkout. The latter is a generated deployment mirror, not a second independently edited research repository.

## Monograph correction and editorial work

Retain the seven-part narrative and its three reading routes. Split the source at the existing 32 section boundaries first, preserving every label and numbering convention. Keep the article class initially so structural maintenance does not introduce an unnecessary renumbering problem; decide on a book class only after the HTML/PDF pilot.

Replace duplicated inline figures with canonical inputs and generated web renditions. Preserve short list-of-figures captions. Centralize notation, angle/length conventions, orbifold factors, and quantum normalizations. Add an index/glossary, chapter introductions, a prerequisites guide, and short computational examples where they explain a formula. Give the original `ipoly` manuscript a clear historical-companion status and move unique useful derivations into the canonical text or an appendix with provenance.

Create a claim ledger for the 35 numbered formal statements and other consequential assertions. Each record should contain the stable source label, hypotheses, status as stated in the text, source/derivation, review state, dependencies, associated code, and evidence. A numerical experiment does not certify a theorem; a formal algebraic certificate about abstract holonomy does not prove existence of a corresponding convex embedding.

Independent mathematical review should first examine:

1. The coordinate-specific identity `-D²V = 2L`, boundary conditions, Schur/forest formulas, and compatible-barrier argument (Section 9). The relevant coordinates are leading–trailing angle coordinates on a prescribed planar problem, not arbitrary vertex coordinates.
2. The factor `2^(-d)`, stack/effective measures, final-chamber conditions and nonuniform balanced-weight limit (Sections 1–8).
3. The distinction between the independent period/first-moment derivation and the additional spectral-continuation hypothesis (Section 13), then the regular-family contour/tail and Airy correction arguments (Section 15).
4. Peripheral conventions, local analytic-germ identity, sixth-order coefficients, and the conditional transfer to global quantum invariants (Section 16).
5. Endpoint weights in the counting-to-mixing converse, the nonsquare genus-two `(2,2)` restriction, and the distinct geometric/arithmetic hypotheses in sharp counting (Sections 27–31).

Preserve the recent-source qualifications already in the book. The cited OpenAI quasi-RH preprints exist; their correctness and formalization coverage were not verified here. Pin cited versions and keep uses conditional. The official [OpenAI math repository](https://github.com/openai/math) itself distinguishes verification stages. Audit the recent Doan–Li–Nguyen version and the remaining foundational references by exact statement and hypothesis before upgrading any source status.

## Computational support to add

The [complete section map](audit/2026-10-31/monograph-audit.md) covers all 32 sections and both appendices. The following groups turn it into an executable backlog. “New” means no dedicated implementation was found in the supplied sources; it is not a claim that no relevant software exists elsewhere.

| Priority and text | Existing foundation | Proposed deliverable and verification |
| --- | --- | --- |
| P0, Section 9 | `ipoly` v1/v5/v7/v9/v10/v13/v14, toolkit Rivin modules | One reproducible fixed-dihedral example with volume, gradient, constrained Hessian, FEM identity, boundary Schur response and rooted-forest determinant. Compare independent matrix assembly, finite differences, and exact small-graph determinants. |
| P0, Section 15 | Formula and six-row table only | Recover or implement log-double-sine evaluation and exact contour quadrature; regenerate all six rows with precision, contour, tail and convergence studies. Compare with the Airy first correction without substituting the asymptotic model for the purported exact integrand. |
| P0, Section 30 | Reported 18-million-curve enumerations but missing archive | Markoff/Farey enumerator preserving slope multiplicity, stable logarithmic recurrence, dyadic event statistics and sensitivity calculation. Start with small exact/high-precision cross-checks; then replay length 8192 with checkpointed inputs, raw counts, precision evidence and full block tables. |
| P0, retained companion claims | v8/v11/v17/v18/v21, original benchmarks | Named optional SnapPy experiments and full-residual solver comparisons; recover missing hexagon/Rippa/stretch/clique experiments or qualify their claimed reproducibility. Every retained numerical table needs an executable recipe and provenance. |
| P1, Sections 1–3, 5–8, Appendix A | Geometry primitives plus explicit formulas | Exact normalization fixtures, tetrahedral WP integral, chamber-aware cone/WP polynomial examples, flat-limit partition sum, torus–sphere factor, Fricke/Poisson check. Use independent formulas, rational arithmetic where possible, and convergence-controlled quadrature. |
| P1, Sections 7, 12–14 | Hypergeometric and finite-matrix formulas | Four-point periods, fusion matrix, Hermitian pairing, density, logarithmic equal-weight limit and rank tests. Track branches and compare connection formulas/monodromy; retain the separate unproved spectral-tail assumption. |
| P1, Section 16 | Manifold gluing/sparse linear algebra is adjacent | Optional cusp-shape/inverse-Hessian example, critical value and quartic/sixth-order Dehn-filling coefficients, figure-eight manifold comparison. Pin peripheral conventions and compare independent numerical filling data over increasing slopes. |
| P1, Sections 18–22 | Explicit trace, length and integral formulas | Pants trace and twist-length calculator, torus twist integral, cusp-arc and gap examples. Check derivatives independently and give truncation errors for infinite sums. Distinguish figure-eight surface curves from the knot complement. |
| P1, Sections 23–25 | Finite algebraic identities | Trace/skein polynomial examples, bracelet coefficients, selector obstruction, first atoms and finite Euler-product examples. Exact arithmetic for small cases; finite truncations retain explicit limitations. |
| P1, Sections 26–29 | Explicit finite models/formulas | Finite Markov count-versus-mixing example, marked-torus endpoint-weight lattice sums, Gaussian two-mark correlation. Check explicit formulas and norms without claiming a numerical proof of general mixing. |
| P1, Sections 30–31 | Torus enumerator after recovery | Möbius inversion and main-term-free discrepancy diagnostics that show geometric and arithmetic contributions separately. No inference of an asymptotic bound from a finite plot. |
| P2, Section 4 | Hyperideal formulas; ideal code is insufficient | Admissibility, truncation lengths, fixed-boundary leaf solve and local Pfaffian density quadrature. Start with a documented small cell; a complete global integration algorithm remains research. |
| P2, Sections 10–11, 14 and 32 | Local formulas and open program | Compact-family experiments, bounded quantum sums, broader gluing and degeneration prototypes. Define each finite target; do not promise general quantum asymptotics or resolve open questions through simulation. |
| P2, geometry extensions | Existing floating audits and experimental H4 | Validated root enclosures with strict support/embedding inequalities; robust non-simplicial H4 cell computation. These are substantial numerical-method projects, not merely cleanup. |

For every computational result, publish a machine-readable record containing: stable statement/equation IDs; input identity and checksum; entry point and parameters; seed if relevant; geometry/angle/measure conventions; precision and tolerances; residuals or enclosures; dependency versions; source commit and dirty state; runtime/work accounting; output hashes; evidence status. Reuse existing schema patterns and the artifact manifest rather than inventing incompatible metadata for each chapter.

The website should link both ways: from a theorem/example to its computation and from a result to the precise statement and assumptions. A computation card should expose the example, method, run recipe, checked result, accuracy, and downloadable data. New algorithmic coverage can grow by chapter; missing or open computations should be explicitly identified, not represented by inactive “Run” buttons.

## OpenAI Sites publication design

A reading-focused site should provide the seven-part table of contents, full-text search, stable section/theorem/equation links, references, PDF download, and a computational index. Use readable mathematical typography and responsive tables. Three initial interactive demonstrations are sufficient: tetrahedron shape/volume, a small Hessian/network boundary response, and a modest torus trace-counting example. All must share fixtures with the Python implementation; expensive research campaigns remain downloadable/replayable computations.

Keep one authored mathematical source. Prototype conversion on the existing tetrahedron section, Section 9, and the Airy section: these exercise equations, theorem environments, cross-references, tables, macros, and TikZ. LaTeXML is a candidate because its documented postprocessor supports cross-reference scanning and section-based HTML splitting; its compatibility with this manuscript must be demonstrated before committing to it. `make4ht` is installed locally and is a fallback to evaluate if needed. Plain text conversion or MathJax alone does not implement theorem numbering, bibliography links, or multi-page cross-references. See the [LaTeXML manual source](https://github.com/brucemiller/latexml/blob/master/doc/manual/manual.tex).

Build equation numbers and anchors from the canonical document. Use MathJax for supported mathematical rendering and accessibility where needed, with pinned assets and tested macros. Its [accessibility documentation](https://github.com/mathjax/mathjax-docs/blob/master/basic/accessibility.rst) describes available speech and expression-exploration support. Render TikZ diagrams to reviewed web assets from the same figure sources.

The current Sites plugin supports static output through `.openai/hosting.json` with `static.directory`. That fits a generated monograph. Its server environment is Cloudflare Workers; do not assume the existing Python/Gradio/SciPy/SnapPy application can be deployed unchanged. The existing Gradio interface can remain a local tool or a separately managed application. Sites is the publication frontend. The public [Sites guide](https://learn.chatgpt.com/docs/sites) describes hosting and sharing; the installed plugin's [workflow contract](/Users/igorrivin/.codex/plugins/cache/openai-curated-remote/sites/1.1.2/skills/sites/SKILL.md) supplies the build and source-publication details inspected for this plan.

For eventual publication, export only the curated site subtree into the Sites-owned source checkout, with the canonical research commit recorded in a build manifest. Use the supported source helper to commit/push/package that checkout, then save and deploy the matching archive and source commit. Test a private preview before the intended public edition, and record the saved version and deployed URL. The source helper operates on a repository root and stages its content; do not point it casually at the whole research repository or an arbitrary nested directory.

If the canonical research repository remains private, public code links must target a deliberately published source snapshot or accessible downloads, not private GitHub URLs that readers cannot open. Publication assets must exclude private benchmark answers and superseded results. This is a concrete concern because the toolkit already separates holdouts from public prompts.

## Implementation phases and gates

### Phase 0 — Evidence and documentation discovery

**Completed for planning:** source/duplicate inventory, bounded code inspection, targeted reproductions, source build, section-to-computation map, and Sites/converter documentation discovery. Context7 was consulted for Sites, LaTeXML and MathJax; its Sites result was sparse, so the installed Sites contract and official guide supply the actual platform details.

**Remaining baseline gate:** create a pinned supported Python environment and run the existing full suite, core-only import tests, wheel/CLI checks, data-integrity checks, and a visual PDF sample. The default local Python 3.15 is outside the toolkit's declared 3.10–3.14 range. Record failures before fixing them.

**Use:** existing `pyproject.toml`, `docs/release-0.4.0.md`, `tests/`, source inventory and audit reports. Keep historical reported validation separate from this new baseline.

### Phase 1 — Preserve and integrate

**Implement:** verified backups including LFS, unsquashed history imports, monograph snapshot, duplicate map, root ownership documentation and deliberately enabled CI. Preserve package layout and scientific output bytes during the import.

**Use:** current Git metadata and `.gitattributes`, `results/manifest.json`, `CLAUDE.md`, `docs/architecture.md`, and the existing improvement roadmap.

**Gate:** both original heads remain reachable; archived and imported source hashes agree; no nested active repositories/submodules accidentally replace the intended source trees; core install/CLI/tests still run from the new paths; no automatic HF force-push workflow is enabled. Migrate path-based links and workflow working directories explicitly.

### Phase 2 — Correct numerical and status contracts

**Implement:** the reproduced certification/reconstruction fixes, endpoint derivatives, precision naming/behavior, solver failure handling, and accurate final-value evaluation. Add focused regression tests for actual failure cases. Audit the active-set acceptance logic against KKT and feasibility residuals.

**Use:** existing optimization schema, zero-shear audit, `tests/test_penner_rivin_regression.py`, exact-holonomy tests, and the preserved defect probes.

**Gate:** failing examples become passing regressions; passing controls stay stable; no exact status is inferred from a tolerance or lossy conversion; declared failures remain visible. Package/full and minimal-core checks pass. Any retained historical numerical change is explained in an errata/result record.

### Phase 3 — Integrate the companion algorithms

**Implement:** extract shared sparse angle/barrier/Schur routines from the identified `ipoly` sections, add named experiment drivers, isolate SnapPy, and replace source splicing in current workflows. Retain originals as historical source. Consolidate threshold and distribution logic through current owners.

**Use:** `v10_large.py:23–139`, `v16_horospheres.py:8–55`, `v21_snappea_vs_ours.py:30–40`, and the toolkit's established service/serialization patterns. Correct the source problems before promoting routines to a supported API.

**Gate:** the Section 9 worked example reproduces its geometry, derivatives and matrix identities; original versus consolidated small cases agree within declared tolerances; row rank, original constraints, boundary-only cases and failure statuses are tested; scripts are import-safe and run independently of the caller's working directory. Performance assertions use end-to-end cost and accuracy.

### Phase 4 — Correct and modularize the text

**Implement:** reconcile companion contradictions, introduce the convention/claim ledger, split sections and figures, consolidate bibliography, add computational cross-links and publication metadata. Perform the targeted mathematical/source reviews above.

**Use:** the existing monograph's result map, reading routes, source labels, conventions appendix and explicit conditional statements; preserve the companion's honest provenance notes until resolved.

**Gate:** each substantive claim has a recorded status and dependency; critical proof gaps are repaired or explicitly narrowed/reclassified; all 601 existing labels resolve or have an intentional compatibility mapping; PDF rebuild and sampled page review pass. No mathematical content is silently altered by structural conversion.

### Phase 5 — Recover and extend computational evidence

**Implement:** first the missing Airy and torus archives and all retained numerical tables; next the P1 formula/identity packs. Generate tables and diagrams from structured results. Supply fast illustrative cases and separately budgeted full replays.

**Use:** source formulas and table locations listed above, exact small examples, optional independent SnapPy comparison, and the current artifact schemas.

**Gate:** every retained numerical claim/table has available inputs, code, output, precision/convergence evidence and provenance. The first Sites release includes a working Section 9 example, recovered Airy/torus evidence or candidly revised text, and normalization fixtures. Broader P1 coverage is tracked explicitly; P2 research targets are not disguised as completed functionality.

### Phase 6 — Generate and publish the web edition

**Implement:** successful conversion pilot, generated full HTML, search and navigation, cross-links, curated downloads, initial demonstrations, static Sites export and preview.

**Use:** the documented converter splitting/cross-reference workflow, MathJax accessibility support, and the installed Sites static/source workflow. Use returned Site identifiers and version/commit metadata; do not invent hosting APIs or recreate an existing Site on retries.

**Gate:** HTML and PDF agree on representative theorem/equation numbers and assumptions; all links and computational downloads work; diagrams and equations render on desktop/mobile; demos match Python fixtures and reject invalid inputs. Check intended visitor access, including public code links, and keep research-only artifacts out of the export. Deployment success must refer to the exact tested source/artifact version.

### Phase 7 — Verify the complete release

From a fresh checkout and declared environment, install the packages, run the relevant tests and data checks, rebuild PDF/HTML, replay the release's computation set, and verify artifact hashes and source links. Check that no unclassified historical result or conditional theorem has become an unconditional website claim. Run the inherited supported-version CI matrix, with core and optional dependencies separated. Record the research commit, book edition, computation manifest, Sites source commit and deployed version together.

**Completion means:** one maintained research repository; preserved originals and histories; corrected supported APIs; an auditable monograph with explicit mathematical scope; working computation links; reproducible retained results; and a tested Sites edition. Solving every open question in the book is outside that definition.

## First execution increment

Start with the baseline, preservation/import, and two reproduced correctness fixes, then deliver one complete Section 9 example from text to code to generated result to a local HTML chapter. This tests the proposed integration at small scope. In parallel after the import, recover the missing Airy/torus evidence and begin the focused mathematical review. Expand the web edition only after the conversion and computation-link contracts work.

Before the eventual public release, settle the author/credit line, text and companion-code licenses, canonical remote name/visibility, public source-download policy, and whether the old HF application remains supported. These choices do not prevent the analysis or local integration work. The unresolved numerical-method and proof questions are recorded as work items with evidence, not silently resolved by publication formatting.
