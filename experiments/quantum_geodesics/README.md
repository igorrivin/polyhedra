# Finite quantum and geodesic checks

## Regge and Wigner 6j teaching example (Section 10.1)

The standalone [regular-tetrahedron example](regge_example.py) evaluates the equal-integer-spin Wigner 6j-symbol by exact rational Racah sums, then compares it with the Euclidean Ponzano–Regge leading term for spins 10, 20 and 40. It also computes the angle deficit for five regular tetrahedra around an edge. The phase uses **exterior** dihedral angle `acos(-1/3)` and length `N+1/2`; the deficit uses **interior** angle `acos(1/3)`.

```sh
python experiments/quantum_geodesics/regge_example.py --output /tmp/regge-example.json
```

The output must be a new file. The [author's result](../../artifacts/regge_example/result.json) records the exact fractions, 80- and 120-digit floating evaluations, cross-precision residuals, software versions and driver hash. The [revision record](../../docs/execution/regge-turaev-viro-2026-11-03/README.md) includes a separate SymPy comparison. This is a finite illustration, with no interval error bound or numerical proof of the asymptotic theorem. It does not implement general or root-of-unity 6j-symbols. The earlier four-group quantum and ten-group geodesic campaign below keeps its original code and recorded results.

## Preserved quantum and geodesic campaign

This offline companion has four finite quantum groups and ten finite geodesic groups. It is independent of the supported volume-toolkit package. The accepted formula contracts and review records are copied under `contracts/` with their original bytes; these record provenance, not approval of this implementation. The geodesic contract approval covers its finite mathematical specification, separately from manuscript prose and claim-ledger review.

Run in the existing supported Python environment (Python 3.12, mpmath 1.3, SymPy 1.14):

```sh
python experiments/quantum_geodesics/run.py --output /tmp/quantum-geodesics-result.json
python -m unittest discover -s experiments/quantum_geodesics/tests -v
ruff check experiments/quantum_geodesics
```

Output must be a new file in an existing directory outside the companion source. Initial author results remain preserved under the outer `../execution/final-chapters-review-2026-11-01/computation/`. The [reviewed clean-source result](../../artifacts/quantum_geodesics/result.json) is recorded in the [completed checkpoint](../../docs/execution/final-chapters-review-2026-11-01/README.md), which identifies its source commit and separate author, review and final-generation evidence. No result is computed or written on import; the driver works from another working directory. Explicit exceptions remain active under `python -O`. Serialization happens before exclusive file creation, so failed identities or nonfinite data cannot produce a successful result.

This post-run README correction leaves the result's recorded README hash and the historical acceptance records unchanged. Code, fixtures and mathematical modules are unchanged; this prose-only edit is not a new scientific replay.

The fixture parser rejects duplicate keys, NaN/infinity tokens and JSON floating numbers; exact noninteger inputs must be strings. Result status is stage-neutral: author, reviewer and final replay receipts assign the evidence stage separately.

The full driver pins the complete independently reviewed scientific and provenance profiles, so missing, duplicated or substituted cases and altered declarations fail before computation. It binds all six existing local contract/review/source copies and the accepted source map to those preserved records. These accepted pins are distinct from live manuscript observations: later authorized prose integration may change a live hash without changing the accepted contract identity. Focused lower-level functions still accept the bounded subsets used by regression tests.

The stable groups are:

- `Q1_figure_eight`: N=2 through 40, 60 and 120. Log recurrence and log-sum-exp for positive products versus the finite complex Habiro–Lê expression. Half powers are defined by their exponentials before evaluating q. Imaginary residuals, final product N², maximizing indices including the N divisible by six tie, and logarithmic bounds are reported. Integer-coefficient polynomial identities are separate exact records. Finite growth values are illustrations only.
- `Q2_klein_geometry`: exact radial moments through order eight for the standard simplex, centered cube and a translated rational box. Duffy beta integrals and shifted-coordinate separable integrals independently check moments. Euclidean normals and supports are derived from vertices; Lorentz-normal differentiation checks each first dihedral curvature coefficient and its volume sum. Scalar tail identities and their rational evaluations bound geometric-series truncation only. There is no volume quadrature or subtraction to recover small coefficients.
- `Q3_peripheral_filling`: multiplier logs, half-log Weyl shift and formal filling stationarity/Hessian. Both signs of nonzero q occur. The existing exact `quantum_surgery.filling_inverse` helper is freshly called only after all three dependency files pass SHA-256 guards. No old run or claimed outcome is imported. Gaussian dependence is checked after squaring; no branch-independent square-root identity or geometric filling is claimed.
- `Q4_charge_curvature`: exact rational weights and rational b² verify the charge dictionary, screening exponent, strict first-moment inequalities, real-coordinate curvature factor and top exterior-power factors for dimensions one through three. All marks are finite and d²w=dx dy. These are specialization checks, not GMC construction or moduli integrals.

The geodesic groups are:

- `G1_torus_unfolding`: the rational stack factor, finite Fermi integrals at R=12,30,60, and finite alternating Dirichlet sums with their distinct signed tails.
- `G2_pants_traces`: six signed rational SL(2) matrices, trace polarization, the inverse pants-trace map, and three retained curve labels for each simple trace 3,4,5,10. Equal traces do not merge labels.
- `G3_figure_eight_kernel`: stable h and F_N at all seven required inputs and N=4,12,40,180, with positive or logarithmic analytic tails. Independent formal-symbol coefficients establish the finite telescoping algebra. Floating residuals too small relative to the source quantities are explicitly cancellation-limited. Finite three-curve blocks are not a whole-surface sum.
- `G4_local_distance`: Lorentz distance, numerical gradients and Hessians, and exact polynomial reductions using the hyperbolic identities. The specified endpoint/distance grid includes d=.03. Interior positive eigenvalues are sampled evidence; the exact simplifications remain separate.
- `G5_seams_torus_holonomy`: all required seams and torus matrix/derivative fixtures, including a=10⁻¹² with extra guards. A separate a=1000 minimum uses stable asinh/log1p formulas and identifies the matrix-acosh loss of signal. Matrix cancellation budgets are estimates, not certified reference accuracy.
- `G6_twist_coarea`: finite direct and coarea quadratures for two cuff/boundary pairs, all five s values and U=12,30,60. Length-side coordinates remove the endpoint singularity and use geometric subdivisions. The beta total, exact s=2 finite integral/tail, and sublevel endpoints are checked. Heuristic quadrature estimates, two-precision convergence observations, analytic omitted-integral bounds and floating budgets remain separate; no total-error certificate is claimed.
- `G7_twist_partition`: stable H, tanh and length-side K formulas; exact finite telescoping; positive logistic tails through L_N>1000; signed twist reduction with integer relabeling; and exact uniform-window partitions including zero-mass endpoint contacts. u=1000 and tiny complements use positive relative checks, with failed direct subtraction routes classified explicitly.
- `G8_endpoint_matching`: exact cyclic endpoint spacing and winding lifts, plus a local stationary and a position-matched nonstationary example. There is no closed-curve reconstruction solver.
- `G9_cusp_decoration`: all 27 rational cusp matrix cases, signed truncation and lambda normalization, decoration invariance, and exact Markov/flip checks. H=20,t=3 gives a negative signed length; large decorations are not asserted to be embedded.
- `G10_boundary_shadows`: independent circle endpoints and two log1p formulas, retaining positive shadows for d=100,1000. The factor of two for an unoriented arc is explicit. No complete orthospectrum is summed.

Floating calculations use cloned mpmath contexts with **70 and 110 requested decimal digits**. Ordinary groups use 20 guard digits (90/130 actual); G3 uses 100 (170/210 actual) for rapidly growing iterates through N=180; G5 uses 80 (150/190 actual) for small-cuff matrix cancellation. Every numerical group records its actual setting. Acceptance uses `10^(-(requested_digits-15))`. A positive signal must stay strictly positive and pass a relative residual test; zero, a nonpositive value, or a fixed fraction of a tiny positive signal is rejected. Signed or zero residuals need explicit formula-specific positive scales. Analytic tails, uncertified floating budgets, and cross-precision observations are distinct records. Agreement between two precisions is not an independent oracle or an error enclosure.

The result records code, fixture, test, README, contract and guarded dependency hashes, Git HEAD and full dirty status before and after, live manuscript observations relative to accepted source pins, all live book TeX hashes, software versions, residual scales, exact inputs and runtime. The run requires complete equality of the before/after source observations and Git status. A dirty run is recorded as dirty; an external checkpoint supplies later clean-source and approval receipts. Outer author or reviewer directories are not runtime dependencies. Earlier quantum-only author evidence remains preserved separately.

No general Jones or root-of-unity 6j evaluator, global moduli/filling/GMC solver, interval certificate, numerical asymptotic theorem, arbitrary polyhedron realization, geometric completeness claim, installation or upload is performed here.
