# H³ numerical-correctness checkpoint

Date: 31 October 2026. Baseline:
`285a6cb71473ba1f238983e062662cf890cbba05`. This increment continues Phase 2
of the [accepted integration plan](../../../INTEGRATION_PLAN.md), after the
[first checkpoint](../2026-10-31/README.md). It corrects maintained H³
precision, angle optimization and optimizer-result contracts. The original
repositories, canonical monograph source/PDF, historical `research/ipoly`
sources and existing scientific data corpus remain unchanged.

Fresh endpoint validation is owned by
`optimization.optimize_ideal_polyhedron`. The separate historical
`refine_geometry_for_volume` still uses its solver's cached objective and is
outside that service audit; H⁴/H⁵ and Torch algorithms are also outside this
increment.

This local checkpoint records independently approved precision, service and
angle corrections, the integrated available-suite attempt, and passing
minimal-wheel checks. The [closeout](closeout.md) records the committed source,
Section 9 regeneration from clean source, and final detached-archive replay.
The complete Phase 2 release gate and publication remain outstanding.

## What changed

- [Precision](../../../packages/volume-toolkit/docs/numerical-precision.md):
  mpf-returning kernels preserve supported inputs and scope their working
  precision. Stable Bloch–Wigner reductions handle extreme finite arguments
  and tiny imaginary parts. Legacy `fast` defaults remain finite Fourier
  approximations; `exact`/`eval_only` are numerical mpmath aliases. High-level
  results and Qhull/projection remain binary64.
- [Angle calculations](../../../packages/volume-toolkit/docs/rivin-numerics.md):
  strict feasibility maximizes a common margin in pi-normalized units;
  feasible projected steps, constraint release and a full original-row KKT
  audit replace clipping and premature activation decisions. Final volumes
  use the canonical binary64 kernel. Flat angles are explicit failures of the
  differentiable solver. Reporting distinguishes numerical witnesses from
  embedding/infeasibility conclusions and counts actual volume calls.
- [Optimizer results](../../../packages/volume-toolkit/docs/optimizer-result-contract.md):
  endpoints are freshly evaluated and checked before ranking; raw convergence
  remains separate from candidate validity. Callback snapshots are detached
  from internal records. New schema-v2 outputs are strict JSON with explicit
  verification work; the v1 schema and historical fixture remain unchanged.
  Threshold APIs reject undefined inputs and state their numerical scope.

The [numerical errata](../../../book/numerical-errata.md) records the changed
bounded values and the distinction between baseline defects and uncommitted
review findings. In particular, the old regular-tetrahedron Fourier report
`1.0151497106006686` exceeds the independent value
`1.0149416064096536` by approximately `2.08104191e-4`. No corpus-wide replay or
automatic correction of historical tables was performed.

## Review stages and evidence

Each report describes the source hashes it actually examined. Preserved
failing outputs are historical evidence, not the final verdict on later
source. Copied files are not new executions.

| Area | Initial findings | Correction and current evidence |
| --- | --- | --- |
| Precision | [Original review](precision-review.md): 49 focused tests passed, but independent MP comparisons found a negative-axis wrong-sign/magnitude blocker. A separate near-one stringent target miss was nonblocking. The exact reviewed source bytes remain in `precision-reviewed-geometry.py`. | [Author correction](precision.md) and [independent follow-up](precision-rereview.md): **60 focused tests pass**, all 74 original independent cases and 20 additional signed negative-axis cases pass. **Approved** for the reviewed H³ scope. [Manifest](precision-rereview-manifest.json). |
| Optimizer/threshold/schema | [Baseline audit](optimization-audit.md) reproduced unchecked cached scores, candidate loss and nonfinite output. [Initial service review](service-review.md) then found mutable callback aliases in the new implementation. | [Author correction](optimization-service.md) and [independent callback follow-up](service-review-callback-followup.md): **64 focused tests pass**, original mutation probe and additional nested/retained-reference probes pass. **Approved** for this scope. |
| Rivin angle solver | [Independent review](angle-solver-review.md): 60 focused tests and seven independent MP/SLSQP comparisons pass; exact primal/dual witnesses prove common margin `1/7` for the named fixture. Requested corrections to feasibility wording and omitted volume-call counts. | [Author follow-up](angle-solver.md) and [independent approval](angle-solver-followup-review.md): **73 focused tests pass**, thirteen new reporting/count regressions, truthful 1/1 and 14/14 instrumented work counts, unchanged bounded numerical outcomes. [Independent machine evidence](angle-independent-followup/review-result.json). **Approved** for this scope. |

The [integrated verification](integration-verification.md) checks the reviewed
sources together. The [machine summary](integration-summary.json),
[commands](integration-commands.json) and
[final source hashes](integration-source-hashes-final.json) distinguish the
following results:

| Integrated check | Recorded result and limit |
| --- | --- |
| Available full-suite attempt | **393 passed, 18 skipped, 4 failed, 9 collection errors, zero warnings**. Failure/error/skip node IDs match the previous checkpoint exactly; Gymnasium/Hypothesis are missing, and pynauty cases skip. There are 114 additional passes. This is not a clean optional-dependency suite. |
| Source, wheel, sdist and installation | All **47 package Python files** match across live source, temporary build copy, both distributions and installed wheel; hashes remained stable. Both distributions were built and inspected; only the wheel was installed. Version remains 0.3.0, with no release or tag. |
| Minimal installed core | New isolated environment, only local NumPy/SciPy/mpmath snapshots plus pip and the new wheel. `pip check`, installed numerical probes, v2 CLI/schema checks and preserved v1 fixture/schema checks pass. This is not a fresh online dependency resolution. |
| Data integrity | 412 materialized LFS paths, 354 JSON payloads, two canonical input hashes and two manifest artifacts pass. This checks retained data integrity, not a fresh numerical replay of that corpus. |
| Preliminary Section 9 reproduction | Both installed-wheel and newly extracted archive modes pass all **12 numerical checks** and exact rational fixture identities. All nine archive payload hashes match. Their origin records the modified checkout honestly; these preliminary records are preserved unchanged. |
| Final canonical Section 9 reproduction | Regenerated from clean source `9188e0624cdf6d9949af1f620336eff67c8b59d7`, committed as `29440cfbfcdaa23711cfdac4e09bf5f939404273`, and replayed from the final ZIP outside the checkout. All 12 numerical checks, exact fixture identities and nine payload hashes pass. [Final evidence](closeout.json). |

The installed verification harness initially read a nonexistent LP field
`residuals`; its correction uses the existing `primal_residuals` field.
The [initial harness log](integration-installed-probes-harness-before.log)
and [successful installed results](integration-installed-probes.json) preserve
that distinction. No product fix was needed for this harness error.

Precision source SHA-256 after approval:
`eb01142ad2cc8a9d3018737be59f90c19b6035b2e5d416c75865bf3fad8baf73`.
Service source SHA-256 after approval:
`1e9cedb1bd48e8a79356c51c336199b9134012eedf59487b6819fb491918098e`.
Angle source SHA-256 after approval:
`65a388fc0682a32370c2ad886ef807852ae68df07f1a00d7f7b3a587f066f053`.

The independent seven-case angle comparison had maximum volume difference
`4.23e-13`; it is bounded numerical evidence, not exhaustive mesh coverage.
The strict LP fixture's rational certificate proves only its finite angle
program. The `n=15`, seed-2 legalization regression changes from one flip to
two; strict acceptance checks and repeated deterministic paths remain. This
is changed work, not a speed improvement. These free-angle inequality
programs differ from Section 9's fixed-dihedral leading–trailing coordinates.

The service's deliberately inconsistent cached-score fixture (`100` versus
approximately `1.01494`) checks its boundary contract; it does not establish
ordinary SciPy misbehavior. Its fresh CLI smoke reports volume
`1.0149416063712777`, 185 SciPy evaluations and one separate verification
evaluation, with both convergence and validation successful. The previous
checkpoint's `1.0149416063705312` is a saved prior result; the new replay also
includes the kernel correction. See [JSON](optimization-service-cli.json),
[log](optimization-service-cli.log) and [summary](optimization-service-summary.json).

## Reproduction

Use a supported Python 3.10–3.14 environment with the package's declared
dependencies; [root installation instructions](../../../README.md) describe
the normal setup. Recorded reviews used Python 3.12.11 and copied local
NumPy/SciPy/mpmath snapshots after the earlier DNS failure. They are not a
fresh online dependency-resolution result. Exact versions are recorded in
the machine evidence and [previous environment snapshot](../2026-10-31/requirements-snapshot.txt).

From the consolidated repository root, after creating `.venv`:

```sh
POLY_REPO="$PWD"
POLY_PY="$POLY_REPO/.venv/bin/python"
cd packages/volume-toolkit
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  "$POLY_PY" -m pytest -q -p no:cacheprovider \
  tests/test_geometry_precision.py tests/test_geometry.py tests/test_variational.py \
  tests/test_rivin_numerical_contracts.py tests/test_penner_rivin_regression.py \
  tests/test_rivin_legalization.py tests/test_rivin_solver_comparison.py \
  tests/test_optimization.py tests/test_optimizer_result_contract.py \
  tests/test_correctness_regressions.py tests/test_data_integrity.py
```

These are the executable focused references; their overlapping author/review
counts must not be summed into a full-suite total. The integrated available-
suite attempt reports **393 passed, 18 skipped, 4 failed and 9 collection
errors**, with no warnings; see [log](integration-full-tests.log) and
[JUnit XML](integration-full-tests.xml). The remaining failures/errors require
unavailable Gymnasium or Hypothesis. This is not a clean optional-dependency
suite. The [integrity check](integration-data-integrity.log) confirms 412
materialized LFS paths, 354 JSON payloads, two canonical input hashes and two
manifest artifacts. The [wheel/sdist checks](integration-distributions.json),
[installed-package probes](integration-installed-probes.json) and
[Section 9 preliminary replays](integration-section9-replays.json) are recorded
separately. The prior 279-pass result belongs to the first checkpoint, not to
this corrected source.

The [crosscutting review](crosscutting-review.md) approves ownership,
compatibility, evidence boundaries and the portable replay adapters after
real execution. Its intermediate and final evidence checks are preserved;
the earlier integration-copy mismatch was resolved by copying the completed
reports. [Portable execution evidence](replay/verification.json) records all
three successful adapter runs and the two adapter-only bugs corrected before
approval. Neither bug changed a product kernel.

For portable before/after and independent-reference drivers, use
[replay instructions](replay/README.md). Those adapters take `--repo` and an
explicit new `--output`, preserve the original diagnostic computations, and
never replace stored review outputs. The retained top-level reviewer scripts
document the original invocation environments and may contain machine paths
or write to sibling evidence files; they are archival source, not portable
launchers. No operational workflow depends on a duplicated product kernel.
The preserved failed `precision-reviewed-geometry.py` is used only to verify
and reproduce that identified intermediate review defect.

## Evidence inventory and continuation

[evidence-files.json](evidence-files.json) records origin and destination
paths, both SHA-256 hashes, copied byte counts and every replay adaptation.
Origin paths are relative to the outer workspace; destination paths are
relative to this repository. Original scripts and review-stage evidence are
preserved; the adapted drivers live only in `replay/`. The inventory records
one location-only report adaptation identifying omitted distribution binaries
at their original outer-workspace path; no numerical observations changed.
The manifest's `force_add_paths` enumerates exact copied `*.log` paths ignored
by root Git rules. Add only those paths when staging evidence; exclude
AppleDouble `._*` files. Temporary environments, wheels and sdists are omitted.
The [integration-specific manifest](integration-evidence-manifest.json)
records the verifier's original output hashes. The later
[closeout inventory](closeout-evidence.json) separately records clean-source
generation, final replay and preservation checks. The pre-commit staging
manifest remains a historical record of the initial staging scope.

The reviewed numerical source was committed as `bed2d7dbaf80df7bcc4fd75ecce0459627c58963`.
A following [test-whitespace correction](source-hygiene.json) produced clean
source `9188e0624cdf6d9949af1f620336eff67c8b59d7`; only two trailing blank lines
were removed, with both test ASTs unchanged and all 47 product Python hashes
unchanged. The initial staged whitespace check found those two issues; it was
not a passing gate. The corrected authored whitespace check passes.

The new Section 9 outputs and final replay are recorded in the
[closeout](closeout.md). Earlier source `c02b358de5a6f724faf3368a641ba64f5841d859`
and artifact commit `74e2abc67e434e0d7eadf70d7becaa6de2f77785` remain preserved
in Git history and the first checkpoint. This checkout has no configured
remote; this is a local checkpoint, with no push, package release or Sites
publication.

The full optional development environment, Gymnasium/Hypothesis coverage,
GUI construction and supported-Python/platform matrix remain release gates.
The local-listener/browser-file-URL restrictions still prevent browser layout
and interaction verification. Airy and torus evidence recovery, the complete
claim/proof ledger, monograph modularization/HTML conversion, release-PDF
review, licensing and publication remain future work. Numerical residuals,
exact finite fixtures and publication readiness retain separate statuses.
