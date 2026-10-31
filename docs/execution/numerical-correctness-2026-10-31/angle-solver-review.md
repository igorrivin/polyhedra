# Independent review of Rivin numerical corrections

Review stage: **changes requested for two public reporting defects**. No
additional mathematical or numerical acceptance blocker was found in this
bounded review. This is a pre-fix review; the corrections below need focused
regressions and re-review before approval.

Reviewed source: `consolidated/packages/volume-toolkit`, baseline commit
`285a6cb71473ba1f238983e062662cf890cbba05`, with uncommitted numerical changes.
The Rivin source SHA-256 was
`05511c8a360898d161a5584a0a93074243588004399e72933f95f19fe2e431b1`.
The geometry dependency SHA-256 during independent probes was
`3a1ce69bddaa9afc980376cf382ed84ccd7b5746c2d30f5e89edc7f85307f4e9`.
No source, original repositories, commits, or remotes were changed by this
reviewer. Only these outer execution evidence files were written.

## Corrections required

1. **The public feasibility formatter overclaims its evidence**
   (`rivin_delaunay.py:737-772`, also the module docstring at lines 1-18).
   `realizable=False` now means that this run did not verify a positive witness;
   the formatter nevertheless prints `NOT REALIZABLE as Delaunay triangulation`.
   A positive subthreshold minimum such as `5e-7` is also labeled `(<= 0)`.
   Conversely, the formatter calls a positive assignment on two disconnected
   triangles `REALIZABLE as Delaunay triangulation`, although no disk or embedding
   validation occurs. In strict mode it labels the measured witness minimum
   `Maximum min angle`, which is not the common-margin objective. Update both
   outcomes, the objective wording, and the module-level scope. Regressions
   should include solver failure, positive subthreshold margin, strict success,
   and the absence of an embedding/infeasibility certificate claim. The function
   docstring and `docs/rivin-numerics.md` already state the appropriate scope.
   The public optimizer's initial-LP failure path has the related problem:
   injecting the documented, valid API state `solver_success=True`,
   `success=True`, `realizable=False`, positive minimum `5e-7` yields
   `termination_reason=feasibility_lp_failed` and the contradictory message
   `Feasibility LP failed: Optimization terminated successfully. ...`.
   Distinguish an unsuccessful solver/audit from absence of a verified
   positive start and retain the available LP status/margin diagnostics.
   This is a controlled API-state probe, not a claimed naturally occurring
   small triangulation fixture. The optimizer correctly remains unsuccessful;
   the defect is its reason and lost numerical context.

2. **`n_volume_evaluations` undercounts actual objective work**
   (`rivin_delaunay.py:944-965`, `1171`, `1271`). The line search evaluates its
   starting value before initializing its counter, and the final public volume
   evaluation is also omitted. An instrumented equilateral LP start reports
   **0** evaluations but performs **1**. A nonstationary one-triangle start
   `[0.2,1,pi-1.2]` reports **7** but performs **14**. Count all objective calls,
   or explicitly name and document separate candidate/total counters. Add a
   wrapper-based regression, including an already stationary zero-budget run
   and an early failure that makes no objective calls. No candidate-only
   interpretation is currently documented.

The first finding was sent promptly to the parent. The parent independently
noticed the counter defect and requested the instrumented confirmation above.

## Mathematical and implementation assessment

- **Strict LP:** a common margin is equivalent to searching for a strictly
  positive witness for this finite system: for any strict assignment, the
  minimum of its positive corner angles and strict inequality slacks is a
  positive feasible common margin; the converse follows immediately from a
  positive margin. This does not separately maximize either margin and is not
  lexicographic optimization. All original equalities, inequalities, and the
  nonnegative margin bounds are independently checked before accepting a
  solver candidate. Failed, absent, nonfinite, wrong-shaped, and infeasible
  candidates are covered by tests. Numerical tolerance and the positive-witness
  threshold are explicitly separated from an exact infeasibility claim.
- **Exact fixture:** the reviewer reconstructed incidences independently,
  formulated a single-margin LP (rather than the implementation's coupled
  `t,epsilon` variables), and verified rational primal and dual witnesses.
  Every primal row is satisfied exactly, the dual signs and stationarity are
  exact, and the dual minimization objective is `-1/7`. Together they prove
  that the normalized common-margin optimum for this fixture is exactly
  `1/7`. Rational vectors and a rerunnable verifier are in the probe artifacts.
  This certifies only the finite angle program.
- **Feasible optimization:** the projected Newton/gradient direction, actual
  volume Armijo comparison, open-domain step limit, and inequality blocker
  handling preserve the intended affine/inequality constraints up to the
  stated floating-point tolerance. There is no angle clipping. Under the
  maximization convention `grad(V)=A.T*lambda+B.T*mu`, the negative-multiplier
  release sign is correct. Working-set rank selection is numerical, while
  every original row is retained for final audit.
- **Final gate:** success requires positive nonflat angles, original primal
  residuals, nonnegative multiplier fitting, full stationarity, and
  complementarity. Redundant binding inequalities are handled by a
  nonnegative solve, rather than incorrectly demanding signs from one
  arbitrary unconstrained multiplier solution. Zero-dimensional cases still
  receive primal checks. A zero iteration budget cannot bless a nonstationary
  initial state. Forced line-search failure remained unsuccessful with
  stationarity residual `0.9964`; forced singular Newton solves recovered
  through projected gradient and passed only after residual `4.68e-13`.
- **Boundary classification:** `require_interior` checks a converged final
  dihedral tie, not a transient active constraint. The actual eight-face
  fixture released two initially active constraints and matched the
  independent optimum. Legalization and realization acceptance tolerances
  were not relaxed. The only existing-test changes replace premature tie
  speed expectations and a fixed one-flip path by final KKT consistency and a
  bounded, repeated deterministic path. The strict endpoint checks remain.
- **Value helper:** the cutoff quadrature has been removed. Eight independently
  evaluated endpoint/interior probes use 400-digit Clausen references at the
  exact represented binary64 arguments, including the minimum positive
  subnormal and `nextafter(pi,0)`. All absolute errors are below `3e-15`; the
  subnormal probe differs by one subnormal unit. Endpoints and out-of-domain
  inputs have explicit contracts. This is not an interval evaluation.
- **Failure metadata:** a nonstationary zero-budget result is unsuccessful,
  records `max_iterations` and a failing KKT residual, and serializes as strict
  JSON after the documented NumPy-to-native conversion customary for this API.
  Raw result dictionaries still contain NumPy arrays; no native-JSON API is
  claimed here.

For publication, it would be useful to add one explicit cross-reference in
`docs/rivin-numerics.md`: this free-corner-angle optimization with dihedral
inequalities is a different feasible family from Section 9's prescribed
dihedral, leading-trailing coordinates. The current numerical-contract doc
does not claim they are identical, and the Section 9 companion and
`variational.py` retain their separate scope. Do not reuse these KKT results as
validation of a Section 9 coordinate-space theorem or a global embedding.

## Independent numerical comparisons

The reviewer constructed all triangle, vertex, and opposite-edge constraints
without toolkit matrix/topology helpers. SLSQP used those constraints and a
35-digit Clausen-sum objective independent of the canonical binary64
Bloch-Wigner objective. Final values were also reevaluated at 60 digits.

Seven cases passed: one triangle, two-triangle square, four-triangle fan, the
eight-face release fixture, random 8-point triangulations with seeds 0 and 3,
and a random 15-point triangulation with seed 2. All toolkit and reference
solves succeeded. The largest objective difference was `4.23e-13`, the largest
angle difference `6.32e-7`, the largest original equality residual `1.78e-15`,
and no positive inequality violation was measured. The release fixture's
negative multipliers were approximately `-0.45646` and `-0.05233`. This bounded
sample is evidence for the implementation, not exhaustive mesh coverage or a
global classification.

## Verification and artifacts

- Focused source tests: **60 passed in 1.48 seconds** across
  `test_rivin_numerical_contracts.py`, `test_penner_rivin_regression.py`,
  `test_rivin_legalization.py`, and `test_rivin_solver_comparison.py`.
- Used `/tmp/polyhedra-baseline-20261031/bin/python` from the package source
  directory, with bytecode/cache/plugin autoload disabled as requested.
  Imported source path and NumPy/SciPy/mpmath versions are recorded in JSON.
- Ruff 0.12.0: **all checks passed** on the Rivin module and three changed test
  files. The baseline Python lacks the Ruff module, so the existing
  `/opt/anaconda3/bin/ruff` executable was used without installing anything.
- `git diff --check`: passed. No full-suite run was performed while the
  independent geometry/service corrections were still in progress.

Artifacts in this directory: `angle-review-tests.log`,
`angle-review-tests.xml`, `angle-review-ruff.log`, `angle-review-probes.py`,
`angle-review-probes.log`, and `angle-review-probes.json`.

Review scope excludes a new audit of the multiprecision geometry kernel,
optimization callback mutation, packaging/remote execution, global disk
recognition, and publication deployment. Those remain separate owner/reviewer
responsibilities.
