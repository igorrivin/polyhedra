# Whole-monograph exposition pass, 3 November 2026

This pass responds to the undefined spin labels in the physics box and applies the same reader-oriented treatment throughout the monograph. It starts from release r4, commit `72b441ebb504cb7efb5232680600196023383691`. The working reader knows undergraduate linear algebra, calculus and basic surface topology. Later specialist proofs retain their prerequisites, with working definitions and explanations of why the machinery is used.

The introduction, all 32 sections, both appendices, boxes and captions, and the two current reading/computation guides were read. Revisions occur inside arguments as well as at section openings. The table records the actual issues addressed; [coverage.json](coverage.json) binds chapter source hashes and patch-report hashes to that inventory. This is an inline author exposition pass, not a new independent mathematical approval or a claim that a first-time reader has validated every explanation.

The physics box now distinguishes the dimensionless labels j and m from the operators J and their dimensional eigenvalues. New drawings explain the angle-domain integral, the change of domain in unfolding, and cuff-position matching. They are unnumbered to retain the existing numbered figure and equation references.

The [small exact companion](../../experiments/exposition/README.md) makes the new teaching calculations reproducible. Its saved result records its actual source state; it does not rerun or replace any historical scientific campaign. The [exposition skill](../../.agents/skills/exposition/SKILL.md) and its [calibration examples](../../.agents/skills/exposition/references/revision-examples.md) are versioned in this repository. They are not installed in a user's global skills directory.

| Section | Definitions and mechanism addressed | Worked example or teaching device |
| --- | --- | --- |
| 1 | Moduli, symplectic volume, marking and stabilizers | Pants counts and torus orbifold weight |
| 2 | Angle-cell variables, dual graphs, delta measure and ribbon graphs | Regular tetrahedron and constraint versus arclength |
| 3 | Shape-space volume versus polyhedron volume; decorated lengths | Equilateral cross-ratio and angle-domain diagram |
| 4 | Minkowski types, Poisson tensors, Casimirs and leaf densities | Inverse two-dimensional Poisson block |
| 5 | Cone openings, chambers, compactification and intersection classes | Cone weight one third and collision meaning |
| 6 | The common-cover comparison and boundary winding | Areas in the two covers and their common quotient |
| 7 | Developing maps, periods, monodromy, Hermitian signature and Kähler potential | Cone radial coordinate, collision rotation and square torus |
| 8 | Metric versus moduli rescaling; final chamber and order of limits | Inverse cometric rescaling and polynomial degrees |
| 9 | Finite-element functions, grounded Laplacians, barriers and mapping tori | Three-vertex resistor network, minimum and Gaussian |
| 10 | Spin labels versus operators, amplitudes, holonomy and semiclassical terms | Spin-half probabilities, Jones N=3 and Gaussian integral |
| 11 | Scale, Hausdorff convergence and the transition parameter | Cube moment and competing area/quantum scales |
| 12 | Integrability, relative characters, disintegration and WKB indices | First density correction and Fourier phase |
| 13 | Finite versus infinite fusion routes, special functions and logarithmic bases | Euler substitution, collision angles and logarithmic limit |
| 14 | Basis normalization, Gram rank and the need for cubic asymptotics | Nonbalanced fusion matrix and screened Gram spectrum |
| 15 | Airy contour, additive error at zeros and proof estimate structure | Cubic scale and quartic correction order |
| 16 | Dehn filling, logarithm variables, sources, coisotropic reduction and half-densities | Linear filling model and quartic correction after elimination |
| 17 | Quotient integration and why products need new counting arguments | Unfolding interval diagram and exponential test function |
| 18 | Free homotopy, iteration, curve versus knot and sheet switching | Positive pants traces and the functional equation |
| 19 | Twist itinerary, ultraparallel lines and stabilizer quotient | Fermi distance/Hessian and circle unfolding |
| 20 | Coarea branches, endpoint singularity and telescoping | A=2 twist model and its second derivative |
| 21 | Cuff coordinate, winding, endpoint versus tangent matching | Two-endpoint translation diagram and a corner |
| 22 | Cusp metric, horocycles, truncated lengths and orthospectrum | Intersecting translated semicircles and horocycle rescaling |
| 23 | Coefficient extraction, signed measures, transforms and representation operations | Double/triple trace powers and virtual characters |
| 24 | Measured laminations, train tracks, covolume, primitive versus connected | Square lattice, root-of-unity selector and smoothing balance |
| 25 | Linear filter weights and length convolution | Two cancellation checks and a surviving simple iterate |
| 26 | Correlation, Sobolev/localization costs and external spectral inputs | Complete two-state count and correlation computation |
| 27 | Independent character variables, strata, polar Jacobian and derivative hypotheses | Stretched rectangle, oscillatory error and inverse residues |
| 28 | Branched covers, quadratic differential orders and representation norms | Pullback order, square-torus marks and Fourier modes |
| 29 | Observables, norm-ball geometry, independent length cutoffs and Fourier projection | Prime row, exponential weight and Gaussian covariance |
| 30 | Error notation, gauge units, Dini modulus, primitive rows and trace recursion | Logarithmic integrals, dyadic cancellation, n=6 row and trace 6 |
| 31 | Arithmetic versus geometric cancellation and complex-analysis proof route | Mertens sum, balanced 10/11 exponent and signed multiples |
| 32 | How to read a research question and identify a useful computation | Known four-boundary target versus proposed cell integral |
| A | Holonomy and traces, matrix commutator and the coordinate Jacobian | Density at a geometric point with absolute Phi_z=4 |
| B | Using the convention table and distinguishing reused symbols | Cone opening/deficit, dihedral angles and independent spin row |

The introduction now states the reading prerequisites. The book README and computational-status guide give a first route into the code, distinguish saved outputs from fresh execution, and remove obsolete claims that the book had not been published.

## Verification boundaries

All 34 chapter/appendix revisions were applied as hash-guarded, bounded patches against the r4 working copies. Existing label sequences were checked before each source write. The three figure-caption changes are explicitly handled by the HTML converter; an ordinary unlabeled numbered figure still fails closed. Focused publishing tests cover caption preservation, accessible text and rejection of ambiguous source labels. Final compiled-number, source-hash, PDF and publication checks have their own release receipts.

The skill was validated by the skill-creator validator. Its behavior was calibrated against the actual spin-box, unfolding, cuff and arithmetic revisions: each has a defined input, a reason for the construction, an explicit output and a stated scope. This is an author calibration, not a separate agent evaluation. The original mathematical claim ledgers and independent acceptance reports retain their prior source identities. Further reader feedback may expose additional pedagogical gaps; this pass does not turn the monograph into a prerequisite-free textbook.
