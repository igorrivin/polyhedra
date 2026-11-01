# Dense affine-angle barrier solver

`ideal_poly_volume_toolkit.angle_barrier` owns the numerical short-step method
described in Section 9 of the monograph. It calls the existing `variational`
volume and derivative operators. It does not alter the free-angle, inequality-
constrained program owned by `rivin_delaunay`.

```python
import numpy as np
from ideal_poly_volume_toolkit.angle_barrier import solve_angle_barrier

base = np.array([[np.pi / 6, np.pi / 3, np.pi / 2]])
incidence = np.array([[1., 0.], [0., 1.], [-1., -1.]])
result = solve_angle_barrier(base, incidence, [-.2, .1], epsilon=1e-4)
print(result.status, result.volume, result.gap_bound_estimate)
record = result.to_dict()
```

The triangle example optimizes over the full triangle tangent space, with its
known regular maximum. A disk caller can obtain `base` and `incidence` from
`variational.corner_angles` and `variational.leading_trailing_matrix`. Other
callers supply their own affine slice. Completeness of that slice in a larger
geometric problem requires a separate argument.

## Input and coordinate contract

The angles are `alpha = base.ravel() + incidence @ u`, in radians. `base` must
be a nonempty `(M,3)` array with positive angles below pi. The finite real
matrix has shape `(3*M,n)`, has numerically independent columns, and every
column sums to zero within each triangle. The initial point defaults to
`u=0`; a supplied point must be strictly feasible. The solver never clips
angles, normalizes inputs, deletes dependent columns, adds regularization or
uses a pseudoinverse.

Triangle sums are checked with absolute tolerance `64*eps_machine*pi`.
Tangency uses a relative test in each triangle and column: scale its three
coefficients by their largest absolute value and require the absolute sum to
be at most `32*eps_machine` times their sum of absolute values. Zero triples
are handled separately. A tiny wholly non-tangent column therefore cannot
pass just because it is tiny. Numerical rank uses NumPy's default SVD rule,
after a global rescaling to avoid overflow. At most `2*M` independent tangent
coordinates are allowed. These are floating-point consistency checks, not
proofs of exact rank or exact affine constraints.

The result reports base and final triangle-sum residuals, as well as the
maximum scaled tangency sum. The latter is measured relative to the largest
coefficient of each triangle/column triple. Every accepted trace row records
its triangle-sum residual. The Bloch–Wigner volume and Lobachevsky derivatives
agree on the mathematical triangle-angle domain; the small admitted input
residual is numerical, and its effect is not enclosed. Inputs close enough to
the boundary for that discrepancy to matter require a separate precision
analysis. No supplied data are silently repaired.

Zero variables are supported explicitly. The domain then consists of the
single supplied point; the result has status `fixed_domain`, no path work,
gap estimate zero with `finite_gap_available=True`, and `target_t=t0`. This
does not make the floating volume evaluation exact.

## Schedule and numerical safeguards

The objective is `Phi_t=F-t*V`, where `F=-sum(log(sin(alpha)))`. The public
`log_sine_barrier(base, incidence, u)` returns its barrier value, gradient and
Hessian. With `C=incidence`, these are
`-C.T @ cot(alpha)` and `C.T @ diag(csc(alpha)**2) @ C`. The Hessian is assembled
as a Gram matrix for the barrier part.

Initial centering uses damped Newton steps of size `1/(1+lambda)`, with a
feasibility check and Armijo safeguard. It stops at computed decrement
`lambda<=1/4`, which is a neighborhood of the center, not an exact-center
solve. This stage has its own budget and count; the chapter's short-step bound
does not pay for it or for finding a feasible point.

For `m=3*M`, each path step increases `t` by `1+1/(20*sqrt(m))`, except that
the final increase is truncated at the target. The new-parameter decrement
must be at most `5/16`; one full Newton step must produce a feasible point
whose freshly evaluated decrement is at most `1/4`. A violated invariant
stops the run rather than silently substituting another path algorithm.
Success requires a separate fresh endpoint evaluation, centered decrement,
and `t>=17*m/(12*epsilon)`. The numerical target is rounded upward when needed
so the returned conservative estimate does not exceed the requested epsilon
solely because of the final division's rounding.

The solver uses dense binary64 Cholesky factorization and linear solves,
without forming an inverse. It checks finite arithmetic, numerical symmetry,
the Hessian's two-norm condition estimate, the linear solve residual, actual
angle positivity and parameter progress. The default condition limit is
`1e12`; accepted user limits lie between one and `1/eps_machine`. The relative
linear residual is
`norm(H*d+g, H^-1)/lambda`, evaluated using the same numerical factorization.
At computed zero decrement it must be exactly zero. Its default limit is
`1e-8`, and a configured limit must be positive and at most `0.01`.

These residuals are diagnostics. They do not certify the chapter's exact
one-percent energy-error hypothesis, and they do not account rigorously for
derivative or factorization errors. This implementation supplies no sparse,
iterative, randomized or nearly-linear backend.

## Results and failure states

`BarrierResult` and its trace rows are immutable dataclasses with detached
tuples. `to_dict()` gives a detached JSON-compatible record and rejects
nonfinite fields; unavailable estimates are `None`, serialized as `null`.

- `finite_gap_available` means the freshly computed decrement is below one
  and the finite-iterate formula is representable. Its estimate is
  `[m+(sqrt(m)+lambda)*lambda/(1-lambda)]/t`. The fixed-domain case always
  reports its finite zero gap, independently of this generic formula.
- `centered` means the decrement is at most `1/4`. A centered point has the
  conservative estimate `17*m/(12*t)` when representable.
- `target_reached` refers to the actual returned `t` and the recorded target.
- `converged` is true only for `converged` or the trivial `fixed_domain`
  status. A failed run can still have a finite gap estimate or a centered
  last point; those flags do not imply its requested target was reached.
- `certified` is always false. The estimates are numerical evaluations of
  exact-arithmetic theorems, not interval enclosures or embedding certificates.

Invalid inputs or controls raise `ValueError`. Runtime outcomes include
`centering_limit`, `path_limit`, `centering_failed`, `stagnation`,
`ill_conditioned`, `linear_solve_failure`, `numerical_failure`, and
`path_invariant_failed`. A failure returns the last accepted point, or the
validated initial feasible point if its first evaluation failed. Unavailable
volume/decrement diagnostics are null. The failed phase and attempted `t`
are reported separately, so a failed new-parameter trial does not silently
replace the last point's parameter.

`centering_steps` and `path_steps` count accepted updates. `backtracks` counts
step halvings; `evaluations` counts attempted complete state evaluations,
including rejected trials and the final independent endpoint evaluation.
History contains only accepted points, their parameters, objective components,
decrements, positivity margins, constraint residuals and solve diagnostics.
Each path row records its pre-step decrement and actual parameter multiplier.
Budgets are nonnegative integers; the backtracking trial budget must be
positive. The default limits are 100 centering steps, 5000 path steps and 60
backtracking trials per centering step.

## Verification and scope

`tests/test_angle_barrier.py` compares the barrier derivatives against
independent 70-digit numerical differentiation, checks the regular triangle
maximum, follows an asymmetric disk with a nontrivial center/path, and approaches
an analytically identified closed boundary maximum while remaining positive.
It exercises invalid affine data, finite controls, budget exhaustion,
ill-conditioning, an inaccurate linear solve, fresh-endpoint failure, rounding
of the target, and immutable result ownership. These are finite tests, not
proofs of numerical reliability on every input.

This method maximizes volume only on the supplied affine slice. It performs no
feasibility LP, disk-topology validation, convexity/embedding check, complete
peripheral-holonomy construction, or global geometric certification. The
reproducible examples and their independent references belong to the monorepo's
`experiments/section9/` directory. The earlier grid/FEM/forest companion remains
a distinct experiment.
