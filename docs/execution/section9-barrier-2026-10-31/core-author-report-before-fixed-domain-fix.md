# Section 9 dense barrier: core author report

Owned source is limited to the new `angle_barrier.py`, its tests, new solver contract, and four nearest toolkit ownership/readme documents listed in `core-final-manifest.json`. No commits, top-level export changes, canonical generated outputs, or edits to `variational.py` were made by this agent.

## Contract

`solve_angle_barrier(base_angles, incidence, initial_u=None, *, epsilon=1e-4, t0=1.0, max_centering_steps=100, max_path_steps=5000, max_backtracks=60, condition_limit=1e12, linear_residual_tolerance=1e-8)` returns an immutable `BarrierResult`; `to_dict()` requires finite JSON data. `log_sine_barrier` exposes F and its affine derivatives. The documented contract separates numerical rank and input consistency, finite gap availability, centered decrement, scheduled target reached, and overall convergence. Runtime failures retain the last accepted point. Zero variables are an explicit `fixed_domain` exception with zero gap and no path work. The target is rounded upward when needed to prevent its floating division from reporting a conservative estimate greater than epsilon.

The implementation reuses existing volume/derivative operators, has separate initial damped-centering and full short-step path budgets, records pre/post decrements and actual parameter multipliers, tests actual endpoint feasibility, and freshly reevaluates the final nontrivial endpoint. Cholesky, SVD condition estimates and numerical residual checks do not certify exact arithmetic or one-percent energy error. Affine slices are caller-supplied; there is no topology, embedding, feasibility LP, peripheral completeness or nearly-linear solver implementation.

## Validation and preserved failure

The initial focused invocation produced 1 failed and 39 passed. `core-tests-initial.log` and its command JSON preserve that failure. The only failure incorrectly required the initial centered point to be near the exact Phi_1 minimizer in its Euclidean coordinate. The algorithm correctly stopped inside lambda <= 1/4 at u approximately -0.002759. The test oracle was corrected to check the computed centered neighborhood, substantial movement from -0.1 and the nontrivial later path excursion; the solver was not changed to satisfy the incorrect center assumption.

The final focused invocation, recorded exactly in `core-tests-final-command.json`, passed **41 tests in 12.59 seconds**: 30 new barrier cases and 11 existing variational cases. Coverage includes independent 70-digit barrier differentiation, regular-triangle maximum, asymmetric disk path, closed boundary maximum, zero variables, target rounding, invalid controls/affine data, budget failures, conditioning/linear-solve failures, final reevaluation failure and input/result ownership. These remain finite numerical tests.

`core-static-checks.json` records successful Ruff, toolkit whitespace checks, a no-diff check on `variational.py`, and final newline/trailing whitespace checks on all new authored files. Source hashes are frozen in `core-final-manifest.json`. Broader package and independent review checks belong to the parent/reviewer.

## Library documentation

NumPy documentation was fetched using Context7 resolve-library-id followed by query-docs before implementation. Relevant official references were numpy.linalg.cholesky (factor orientation and solve sequence), numpy.linalg.cond (SVD two-norm estimate), and numpy.linalg.matrix_rank (numerical default rank threshold). The supported environment's NumPy 2.5.4 docstrings were also checked. No dependencies were installed.
