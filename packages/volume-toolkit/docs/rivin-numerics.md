# Numerical Rivin angle contracts

`ideal_poly_volume_toolkit.rivin_delaunay` owns the angle-feasibility LP,
constrained angle-volume optimizer, and their numerical residuals. The
constraints assume the intended triangulated-disk setting. These routines
do not certify disk topology, global embedding, exact rank, or an interval
enclosure of an optimum.

This solver varies free corner angles subject to dihedral inequalities. The
[Section 9 companion](../../../experiments/section9/README.md) instead uses
leading–trailing coordinates with prescribed dihedrals, implemented in
`variational.py`. These are different feasible families; the KKT checks here
do not validate a theorem about the Section 9 coordinate space.

## Feasibility LP

The LP uses angles normalized by pi. `angles` and `min_angle` use those
normalized units; `angles_radians` and `min_angle_radians` multiply by pi.
Every successful solver candidate is checked against every original
equality, inequality and bound, with normalized tolerance `1e-8`. The raw
solver status remains available in `solver_success` and `status`;
`success` additionally requires the residual audit.

In standard mode the objective maximizes the minimum angle. In strict mode
the angle lower bound and the dihedral/boundary slack share one variable:
`t=epsilon`. Maximizing this common margin supplies a positive witness if
one is numerically found. `slack` is that guaranteed common normalized
margin, and `min_angle` is the measured minimum angle of the returned
witness. The separately reported measured dihedral and boundary margins
can be larger. The legacy `max_dihedral` fields remain the upper bound
implied by the common slack, not a claim that an edge attains it.

The former objective `1000*epsilon+t` could favor zero angles and report
`realizable=False` even when a strictly positive assignment existed. The
regression fixture in `tests/test_rivin_numerical_contracts.py` supplies an
exact rational normalized-angle witness with common margin `1/7`.

`realizable=True` requires an audited positive witness (`min_angle>1e-6`,
and also `slack>1e-6` in strict mode). `realizable=False`, including a
solver failure or a margin below the threshold, means that no positive
witness was verified by this run. It is not an exact infeasibility proof.
The explicit `feasibility_status` distinguishes these outcomes.
The readable report uses the same witness language, prints measured values
without rounding small positive margins to zero, and labels the strict
common-margin objective separately from the measured minimum angle.

## Angle-volume optimization

`optimize_hyperbolic_volume` uses feasible projected Newton steps and an
Armijo line search on actual binary64 volume values. All angle coordinates
remain in the open interval `(0,pi)`; the implementation never clips them
to an epsilon floor. Singular or unrepresentable Newton curvature falls
back to a finite projected-gradient ascent direction. The final checks
still determine whether the returned point is acceptable.

Inequalities enter the working set when they block a step. A constraint
with a negative multiplier can leave it. Affine solves and null spaces
use numerical SVD/lstsq rank with relative cutoff `1e-12`, while all
original rows remain in the final residual audit. No row is silently
discarded from the acceptance conditions.

For maximizing volume with `A theta=b` and `B theta<=d`, the convention is

`grad(V)=A.T lambda+B.T mu`, `mu>=0`, `mu*(d-B theta)=0`.

The final audit independently fits nonnegative inequality multipliers,
allowing redundant binding constraints. At the default tolerance `1e-10`,
success requires positive nonflat angles and all of:

- Maximum absolute equality residual at most the tolerance.
- Maximum positive inequality violation at most the tolerance.
- Maximum absolute stationarity residual at most the tolerance.
- Maximum absolute complementarity residual at most the tolerance.
- No negative inequality multiplier beyond the tolerance, and a successful
  nonnegative-multiplier solve.

`kkt` records those quantities and all multiplier arrays.
`reduced_gradient_norm` is the Euclidean norm in the final working-set
null space. `n_active_constraints` and `active_constraint_labels` describe
the final near-binding inequalities (within ten times the tolerance);
`working_set_indices` and `active_set_history` separately describe the
algorithm's choices.

`require_interior=True` rejects a converged dihedral within `1e-9` of pi.
It does not infer the final answer from a temporary active constraint.
Boundary-vertex equalities alone do not trigger that flag. A rejected tie
can therefore have passing numerical KKT checks while `success=False` and
`rejected_tie=True`. Downstream arithmeticity and geometric realization
retain their separate checks.

`max_iter` bounds iterations (default 300); `max_active_rounds` bounds
working-set changes (default `max(20,4*number_of_inequalities)`). Budget
exhaustion cannot turn a nonstationary point into success. An already
stationary feasible point can pass the independent audit even with a zero
iteration budget. Shape/nonfinite input errors raise `ValueError`;
nonpositive, flat or infeasible initial angles return an explicit failure
without a silently altered candidate. Exact flat-angle maximizers remain
outside this differentiable solver's domain.

When an LP supplies the start, `feasibility_lp` retains its status, message,
normalized margins, threshold, residual audit, and `solver_iterations`.
Optimizer failures distinguish `feasibility_lp_failed` (solver failure),
`feasibility_lp_audit_failed` (an unverified solver candidate), and
`no_positive_initial_witness` (an audited candidate below the positive
witness threshold). `feasibility_lp` is `None` for caller-supplied starts.

`n_volume_evaluations` counts every objective call made by the optimizer:
the starting value of each line search, accepted and rejected trial values,
and the final reported volume. Early failure before any value evaluation
reports zero; an already stationary start evaluated only for reporting
counts one. `n_iterations` counts angle-optimizer iterations, with the LP's
`solver_iterations` kept separately. Neither counter is a runtime benchmark.

## Value evaluation and evidence status

Final angle volumes use the canonical `geometry.bloch_wigner` kernel,
with the method recorded as `bloch_wigner_binary64`. A cyclic choice of
the largest sine as shape denominator keeps its modulus at most one.
The old 64-term Fourier sum is no longer used for final reported values.
`lobachevsky_function` also uses the canonical identity
`Lambda(theta)=D(exp(2i theta))/2` on `[0,pi]`, with explicit zero endpoints
and rejection outside that domain. Its former cutoff quadrature has been
removed.

These are floating-point evaluations and numerical KKT checks. They are
not exact volumes, interval proofs, or automatic arithmeticity/global
optimality certificates. The exact rational regression witness certifies
only its stated finite angle constraints. Historical strict-feasibility
outputs and Fourier-based reported volumes retain their original
provenance and require explicit replay before being used as current
numerical evidence.
