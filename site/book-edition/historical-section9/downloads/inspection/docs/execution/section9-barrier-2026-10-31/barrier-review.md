# Independent dense barrier solver review

**Final verdict: approved for integration as a dense binary64 implementation of the documented affine-angle contract.** One reproduced reporting defect was corrected and independently rechecked. No unresolved core correctness defect was found. This verdict covers the exact bytes below; it is not a floating-point certificate, a complete optional-dependency test pass, or a release/publication approval.

Reviewer: independent `barrier_solver_review` agent. The reviewer read the repository AGENTS/CLAUDE instructions, the complete new module, its tests and contract, the existing variational operators, nearest ownership documentation, and the chapter's compatibility, finite-iterate, short-step and inexact-step arguments. The reviewer did not edit maintained source, commit, deploy, or reinstall dependencies.

## Verification verdict

**Pass, with the numerical and environment limits recorded below.**

The mathematical mapping is consistent. In the supplied coordinates `alpha = base + C u`, the module uses `F = -sum(log(sin(alpha)))`, gradient `-C.T cot(alpha)`, and barrier Hessian `(C/sin(alpha)).T (C/sin(alpha))`. The objective derivatives are `g_F - t g_V` and `H_F - t H_V`. On the chapter's exact triangle-angle tangent space, the volume is strictly concave and the barrier Hessian is positive definite after removing dependencies. The implementation validates a nonempty strictly positive initial point, per-triangle tangency, numerical full column rank and dimension. Its tolerances are numerical consistency checks, not exact constraint proofs.

The chapter assigns parameter `m` to `F`; it does not assign that parameter to `Phi_t = F - t V`. The finite-iterate estimate is `[m+(sqrt(m)+lambda)*lambda/(1-lambda)]/t` for `lambda<1`, with `17*m/(12*t)` in the centered neighborhood. The implementation uses those formulas with their appropriate decrement gates. Cholesky computes `H = L L.T`, solves `L y = g`, uses decrement `||y||`, and then solves `L.T d = -y`. There is no inverse or pseudoinverse. The condition estimate and dual residual are useful diagnostics; use of the same floating factorization does not prove the exact one-percent energy-error hypothesis in the chapter.

Initial centering has its own count and budget. It uses the damped Newton size `1/(1+lambda)`, direct feasibility evaluation and an Armijo safeguard. It stops in the `lambda<=1/4` neighborhood, not at an exact minimizer. The path uses multiplier `1+1/(20*sqrt(m))`, a truncated final parameter increase, the pre-step `5/16` gate, one full Newton step and the post-step `1/4` gate. The numerical target is rounded upward if needed to prevent its reverse division from exceeding epsilon. A nontrivial successful endpoint is separately reevaluated. Failed trials retain the last accepted point and report the attempted phase and parameter. The zero-dimensional single-point case is explicit.

Independent probes in [review_numerical_probes.py](review_numerical_probes.py), with results in [review-independent-probes.json](review-independent-probes.json), all passed on the final source:

- An additional two-triangle, two-variable affine example uses direct 80-digit differentiation of a log-sine/Clausen objective, independently of the toolkit derivative and Newton helpers. Barrier value, gradient and Hessian errors were approximately `4.25e-16`, `4.04e-16`, and `8.01e-15`. Four independently differentiated path samples agreed in decrement to absolute error at most `5.16e-14`.
- Its independent stationary reference has volume `1.95167530636461926916079914683504035337...`. The returned point's mathematical gap was approximately `6.20e-15`, below the reported estimate `7.06e-6` for requested epsilon `1e-5`. The run used four centering and 676 path steps. These are high-precision numerical comparisons, not interval enclosures of a root or gap.
- An invertible coordinate mixing and uniform scales `1e-60` and `1e60` preserved final angles within `2.23e-16` and retained step counts. Derivative scales `1e-200` and `1e200` returned explicit ill-conditioned/arithmetic failures rather than convergence.
- Separate cases distinguish a finite estimate from centering, centering from reaching the target, and reaching the target from convergence. Read-only inputs remained byte-identical; the result and detached payload did not alias inputs or one another. Empty, non-tangent, zero/dependent, overdimensioned, complex and inconsistent-angle inputs were rejected.
- A near-flat accepted float triple exposed the documented source-precision limitation: its exact binary64 lift differs from real pi in sum by about `-3.00e-16`; the lifted Clausen sum and shape-based Bloch–Wigner value differ by `8.09e-15` at a volume scale of `1.39e-12`. The binary64 evaluator agrees with a direct high-precision Bloch–Wigner definition. The discrepancy demonstrates why accepted residual tolerances and numerical gap formulas are not rigorous geometric error bounds; no input was silently normalized.

### Reproduced defect and correction

On the initial reviewed module `ea73137f...`, the call

```python
solve_angle_barrier(np.full((1, 3), np.pi/3), np.empty((3, 0)),
                    t0=1e-310, epsilon=1e-310)
```

returned successful `fixed_domain`, both gap estimates zero, but `finite_gap_available=False`. The general `m/t` calculation overflowed before the fixed-domain override replaced its estimates. The same inconsistency appeared at the smallest positive binary64 `t0`. The original output is retained in [review-zero-dimension-small-t-initial.json](review-zero-dimension-small-t-initial.json).

The author added `finite_gap = True` in the successful fixed-domain override, two regressions, and an explicit contract sentence. Independent probes and the installed-wheel test confirm the correction. Hash reconstruction proves that this single assignment is the only solver-code change since the full-suite run. This is a reporting correction; it does not change any positive-dimensional iteration. The author's earlier failed approximate-centering test also remains preserved in `core-tests-initial.log`; demanding closeness to the exact center was an incorrect test oracle, not a defect in the decrement stopping rule.

### Tests and exact command evidence

All source test runs used `/tmp/polyhedra-baseline-20261031/bin/python` with `PYTHONDONTWRITEBYTECODE=1`, `PYTHONPATH=packages/volume-toolkit`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `MPLCONFIGDIR=/tmp/polyhedra-mpl-20261031`, `GRADIO_ANALYTICS_ENABLED=False`, and `-p no:cacheprovider`, from the consolidated repo. Full argv, environment, return code, timing and source hashes are recorded alongside the retained raw log and JUnit XML.

| Run | Actual result | Source identity | Exact command record |
|---|---|---|---|
| Initial focused barrier, variational, geometry, precision, correctness regressions | 98 passed | `ea73137f...` | [review-focused-command.json](review-focused-command.json) |
| Available complete package suite, exactly one run, `--continue-on-collection-errors` | **423 passed, 18 skipped, 4 failed, 9 collection errors**, exit 1 | `ea73137f...`, before the one-line reporting correction | [review-full-command.json](review-full-command.json) |
| Final barrier and existing variational tests | **43 passed**: 32 barrier cases and 11 variational cases | `d782aff2...` | [review-focused-fixed-command.json](review-focused-fixed-command.json) |

[review-full-suite-comparison.json](review-full-suite-comparison.json) compares the new XML with the preceding numerical checkpoint's actual XML: all failure, collection-error and skip identities **and messages** are unchanged; passed count increased from 393 to 423. The full suite was not rerun after the narrowly scoped fix, and no final-source full-suite pass is claimed.

The four failures are all missing Gymnasium:

- `tests.test_h4_symmetric_maxima_campaign::test_real_n8_sixteen_cell_calibration_smoke`
- `tests.test_rl_training_launcher::test_launcher_writes_truthful_atomic_model_and_config`
- `tests.test_rl_training_launcher::test_training_failure_leaves_no_partial_artifact_or_lock`
- `tests.test_rl_training_launcher::test_dry_run_writes_nothing_and_never_calls_trainer`

The collection-error modules are `tests.test_cage_optimizer_accounting`, `tests.test_h4_combinatorics_benchmark`, `tests.test_h4_combinatorics_response`, `tests.test_h4_symmetric_benchmark`, `tests.test_h4_symmetric_response`, `tests.test_rl_budget_contract`, `tests.test_rl_harness`, `tests.test_rl_validator` (Gymnasium), and `tests.test_numerical_properties` (Hypothesis). The 18 skips require pynauty. The raw log and complete identities are retained; no dependency installation or network retry was attempted.

### Offline distribution and installed import

[review-package-validation.json](review-package-validation.json) retains exact build/install/import argv and environment, archive manifests, package metadata, hashes and before/after installed-source snapshots. [review_build_install.py](review_build_install.py) is the reproducible check. The build used `python -m build --no-isolation --outdir ... packages/volume-toolkit`; the default build produced an sdist and a wheel from that sdist using the existing backend. Both include the exact final solver, unchanged variational/geometry modules and unchanged package initializer. The wheel has 54 files and the sdist 60; neither contains AppleDouble `._`/`__MACOSX` entries or bytecode. Metadata retains version `0.3.0`, MIT licensing, Python `>=3.10,<3.15`, and the existing dependency/extra declarations.

The wheel was installed with the existing minimal interpreter using `pip install --no-index --no-deps --no-compile --target <new-temporary-directory> <wheel>`. The probe ran outside the checkout, with that target before pre-existing site-packages, and asserted the actual imported path and module hash. It exercised the asymmetric disk through three centering and 841 path steps, returning volume `3.006286641742618`, and checked the corrected tiny-`t0` fixed domain. The environment has NumPy 2.5.4, SciPy 1.18.1 and mpmath 1.3.0 and no Torch. The old installed toolkit's source and dist-info hashes are unchanged. See [review-installed-wheel-probe.json](review-installed-wheel-probe.json).

This is preliminary installed-wheel validation of these working-tree bytes using existing dependencies. It is not dependency resolution, a fresh environment installation, a full supported-Python matrix or a clean-source release build. Canonical release artifacts may be rebuilt later from the identical committed source.

## Anti-pattern verdict

**Pass.** No clipping, input normalization, silent gauge deletion, pseudoinverse, artificial regularization, cached-success shortcut or fake certificate was found. `certified=False` and explicit scope travel with the result. The finite-gap, centered, target and converged flags have distinct meanings, including failed runs with useful retained estimates; the identified zero-dimensional exception is now consistent. Overflow, bad factorization, condition/residual failures, budget exhaustion, stagnation and violated path gates produce explicit nonconvergence. The strict positivity and linear-solve checks do not masquerade as topology, embedding, peripheral-holonomy or nearly-linear-complexity evidence. Source-rounding assumptions remain visible.

## Code-quality verdict

**Pass.** The implementation has one owning module and does not alter existing public imports or computational kernels. Shared preparation/evaluation/finish helpers centralize validation, diagnostics and failure handling. Immutable trace/result snapshots, detached payloads, finite-JSON validation and explicit nullable diagnostics make the result auditable. The dense condition estimate and factorization cost, retained trace size, and accepted-state-only history fit the documented small-example scope; no scalability claim is inferred. Existing operators and exports remain byte-identical to baseline. New module indexing, architecture, README, implementation-status and contract documentation are present.

Independent Ruff checks on the module/tests, tracked toolkit whitespace checks, explicit new-file newline/trailing-space checks, and unchanged-file checks passed. Commands and hashes are in [review-static-and-source-hashes.json](review-static-and-source-hashes.json).

## Exact final bytes and boundary of approval

| File | SHA-256 |
|---|---|
| `angle_barrier.py` | `d782aff2a23c9073c6f7cf02666cc0ec3f4446f28185c7474116fcf42edbbd07` |
| `tests/test_angle_barrier.py` | `31d9bd367799b9d6016dddefc255c27635e78046f33fd7c9bfa424f86b0d7a45` |
| `docs/angle-barrier.md` | `9e30060b75b49c5ba29067d6590aa7e9bc17b37d06a730b1808dc35e91b5faa8` |
| unchanged `variational.py` | `f964764a992089b3725205d0730d27e1254f2b3b9ea17e73eaccae9465e9a07b` |
| unchanged `geometry.py` | `eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73` |

The full seven-file authored source manifest matches the independently computed hashes; the static record also identifies the unchanged initializer/build metadata and the reviewed chapter. [review-final-manifest.json](review-final-manifest.json) binds this report to its source/evidence inventory. Any subsequent solver change requires an affected-check rereview. The experiment artifacts, publisher validation and final publication checkpoint have separate review owners.
