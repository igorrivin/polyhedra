# Sections 23–25 mathematical-author handoff

The author revision is frozen for independent review. It changes only the three owned chapter files and adds `book/claims/sections23-25.json`. No build, commit, upload, historical-artifact replay, or computational-package implementation was performed by this author. The root independently approved the structurally equivalent extraction before these edits.

## Changes and scope

- Section 23 states the periodic normal-variation hypothesis for the Hessian, pins the multicurve-basis and bracelet inputs, makes the spin/Chebyshev sign conversion explicit, and supplies the compact-complex-time Gaussian majorant and spectral cutoff justification. The twist-derivative argument now covers immersed curves by cutting into geodesic arcs and records the coincident-support zero case.
- Section 24 restricts the imported fixed-orbit asymptotic to nonzero rational multicurves, specifies actual integral train-track lattices, and justifies the finite convex chamber bodies and their interior balls. It repairs two malformed simple-curve subscripts, explains the later contributing orbital label, derives the odd-iterate tail constant and shell estimate, and distinguishes component counting from one-support selection after valid integral division.
- Section 25 pins the one-crossing pants input and coincident-cuff convention, states the essential distinct-cuff setting for the fixed-linear-selector obstruction, and specifies the positive-length convolution completion and fixed-coefficient Gaussian-transform majorant. Its added RivinFigures citation resolves an existing bibliography entry; the bibliography was not edited.

The first-atom and unit-corner conclusions used by Sections 26–29 are unchanged. Coefficient measures remain locally finite signed/complex measures. No bounded linear extraction functional, positive identity on the unfiltered spectral side, effective simple-curve exponent from algebra alone, or full kernel approximation is asserted. No fatal counterexample to the retained local conclusions was found; the aggregate counting and conditioning boundaries remain explicit.

## Ledger and primary sources

The ledger has 52 claims, 80 substantive labels, and 14 version-pinned primary-source records. All 91 chapter labels are preserved in order; the other 11 are structural or figure labels. Claims identify hypotheses, proof type, dependencies, source pins, finite computational coverage, and gaps. Author review is complete for a separate reviewer; independent review is explicitly pending.

External inputs were checked at the statement and normalization level using primary sources, not completely re-refereed. EMM supplies an existential exponent; AHT supplies component computation rather than an average selector estimate; punctured-torus primitive-vector counting requires the unoriented factor one half. Naud normalization is pinned to the 2022 arXiv version; no later journal version is needed.

The ledger records two retrieval limitations. Mirzakhani's journal Proposition 3.1 was obtained through primary-PDF search text with printed page labels and cross-checked against the differently numbered theorem in the earlier primary preprint; direct opening timed out. Wolpert's first-variation and deformation pages were retrieved, but the final-page cosine formula was not independently recovered by these tools; the chapter gives the endpoint derivation and no fabricated final-page pin. The background Rivin asymptotics note is not imported as a quantitative proof or coordinate-parity normalization.

## Implemented and pending computation

An author scratch run in the supplied Python environment with SymPy 1.14.0 checked 471 exact finite identities, all passing. `scratch-exact-results.json` preserves the result. Coverage includes bounded Chebyshev and figure-eight coefficients through order 12, root-sum weights and cancellation, and symbolic SL(2) trace identities. It supplies no global enumeration, geometric certificate, asymptotic estimate, or infinite-series numerical certificate. The scratch run was executed from an inline script; its output is preserved, and it is not a maintained companion test suite.

`companion-fixtures.md` provides formulas and expected values for the later computational author, including exact selectors and a finite length-valued Euler-product model. Those planned fixtures have not all been run by this author. `experiments/counting_mixing/` and `artifacts/counting_mixing/result.json` are planned downstream outputs, not evidence available at this freeze. The finite Euler lengths are formal data, not a certified hyperbolic surface.

## Freeze and handoff

`author-freeze-manifest.json` gives hashes and sizes for all four owned canonical files, baseline hashes, preserved labels, existing-bibliography resolution, valid nested environments, and ledger coverage. `author-changes.patch` holds the chapter diffs against the captured extraction baseline. `baseline-manifest.json` and `baseline/` preserve the pre-edit state. `write_ledger.py` generated the ledger and is outside the canonical increment.

No full LaTeX build was run, as requested. The next steps are independent mathematical review, separately authored companion implementation and execution, and coordinated repository/build review. Changes after this freeze require updated hashes and review records.
