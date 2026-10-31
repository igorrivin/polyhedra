# Section 9 implementation evidence

Date: 31 October 2026. Scope: the approved first worked-example companion; not full chapter conversion, publication, or a proof audit.

## Files owned and changed

Paths below are relative to `consolidated/`:

- `packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py`: reusable small dense leading–trailing operators, binary64 angle-volume evaluation through the existing Bloch–Wigner kernel, derivatives, independent barycentric FEM assembly, and Schur complements. Inputs and singular failures are explicit. No general embedding/topology certificate is claimed.
- `packages/volume-toolkit/tests/test_variational.py`: eleven mathematical and reproduction tests, including independent high-precision derivatives, rational fixture identities, harmonic boundary data, face-order/relabeling invariance, zero-dimensional domains, and failure cases.
- `packages/volume-toolkit/docs/module-index.md`: one new ownership entry.
- `experiments/section9/fixture.json`: twelve oriented triangles on an integer-coordinate 3 by 2 rectangle, two interiors, coordinate conventions and scope.
- `experiments/section9/run.py`: independent rational FEM/forest oracle, numerical checks, provenance capture and HTML generation.
- `experiments/section9/page.html`: offline authored companion template; native HTML/SVG and a boundary-voltage scaling control.
- `experiments/section9/README.md`: usage, ownership, provenance sequencing and limits.
- `artifacts/section9/result.json`: preliminary result.
- `site/section9/index.html` and `site/section9/downloads/`: generated page, result, fixture, inspectable source, full imported monograph source/reference PDF, and a runnable `section9-reproduction.zip` archive.

No original repository was changed. No Git staging, commits, source promotion or external publication was performed by this agent.

## Mathematical fixture

The grounded FEM matrix is exactly `[[4,-1],[-1,4]]`, so the negative volume Hessian is `[[8,-2],[-2,8]]` with determinant 60. Exact rational FEM assembly originates from integer geometry, not rounded floating weights. Exhaustive boundary-rooted spanning forests give 15 nonzero terms, each weight one. Eliminating the first angle variable gives effective Hessian 15/2 and determinant factor 8*(15/2)=60.

The separate voltage problem with boundary data x/3 has interior values 1/3 and 2/3, energy 2/3. These are different variables from angle deformations. Zero-weight square diagonals make this non-strict Delaunay. Off-origin u=(0.05,-0.03) is an abstract angle-structure test, not a claim of geometric closure.

## Verification commands and results

From `consolidated/packages/volume-toolkit`:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-baseline-20261031/bin/python -m pytest tests/test_variational.py -q
```

Current result after independent-review corrections: **11 passed in 11.94 s**. The earlier seven-test run is superseded by this expanded verification.

From `consolidated`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/volume-toolkit /tmp/polyhedra-baseline-20261031/bin/python experiments/section9/run.py
```

Result: all exact and 12 numerical checks pass. Independent 50-digit volume derivative versus off-origin Hessian error is approximately 1.78e-15. Independent cotangent/FEM assembly differs by approximately 8.88e-16. Rational FEM versus floating FEM differs by zero for this integer fixture. Final generation was repeated only after correcting the imported PDF path and a matrix-table width style.

All current downloadable links were checked to resolve to local files, including the runnable ZIP. ZIP CRC validation passed. The generated inline script passed `node --check /tmp/polyhedra-section9-inline.js`. Browser interaction/layout QA is assigned to the parent. The old PDF is clearly labeled as the supplied reference edition, not a newly verified release.

Repository rendering uses `book/reference/polyhedral_volumes_and_geodesic_identities.pdf`. Book assets are optional for detached reproduction: missing optional records are explicit and the rendered page omits unavailable book links. Required numerical source records fail explicitly if missing.

## Provenance and release boundary

The result captures the source commit and full porcelain status before writing any output, input and source SHA-256 hashes (including the canonical volume kernel, template, TeX and PDF), dependency versions, methods, precision and tolerances. The current artifact is intentionally marked dirty because it precedes source review/commit. Regenerate from a clean reviewed code commit and commit the resulting artifact separately for a canonical run.

No full package test-suite result, global optimum, strict-realization certificate, rigorous interval enclosure, nearly-linear solver, full chapter conversion or full proof verification is claimed.

## Documentation used

- Canonical monograph Section 9, labels `eq:ipolyAngleCoordinates`, `eq:ipolyHessian`, `eq:ipolyDtN`, `eq:ipolySchur`, `eq:ipolyForestDeterminant`.
- Historical `research/ipoly/v1_volume_hessian.py` for the coordinate convention and independent-check pattern.
- NumPy documentation via Context7: https://numpy.org/doc/stable/reference/generated/numpy.linalg.solve.html (multi-RHS block solve rather than forming an inverse).
- mpmath documentation via Context7: https://mpmath.org/doc/current/calculus/differentiation.html and https://mpmath.org/doc/current/general.html (mixed derivatives and scoped `workdps`).
- Installed Sites skill: local-only, buildless static HTML is supported; no registration or publishing calls were made.

Latest preliminary source commit: `c53387221dc6d000ac46c0b1ce44232c50f02a3c`. Dirty at start: `True`. Environment: Python 3.12.11, NumPy 2.5.4, SciPy 1.18.1, mpmath 1.3.0.


## Independent-review corrections completed

The independent review in `section9-review.md` found three real issues. All are now corrected before commit:

1. **Installed-module and external-fixture provenance.** Source records have stable role identifiers, actual SHA-256 hashes, and either project-relative or external locations. They no longer require `Path.relative_to(ROOT)` to succeed. A regression places module files in a temporary site-packages layout and the fixture outside the checkout, checks all recorded hashes/locations, then removes the required kernel and checks the explicit failure. Actual wheel-layout execution is assigned to the separate package verifier.
2. **Runnable download archive.** `section9-reproduction.zip` has ten payload/manifest members: complete runner/template/fixture, unchanged maintained `variational.py` and `geometry.py`, a deliberately minimal attributed package initializer, toolkit MIT LICENSE, pinned requirements for only NumPy/SciPy/mpmath, README and payload/origin-provenance manifest. The README says this is a generated numerical subset, not a full toolkit distribution. Individual Python downloads are labeled inspection copies. The detached archive regression extracts outside the checkout, runs from a different directory with PYTHONPATH removed, verifies all computations and imported subset paths, and confirms that missing book assets and unavailable Git status are explicit. All payload hashes agree. No Torch, GUI or RL dependencies are required by this path.
3. **Unsigned-index overflow.** Face, interior and elimination labels are checked for signed-int64 representability before conversion. The `uint64(2**64-1)` example now raises rather than aliasing the last vertex. The regression covers all three conversions.

The CLI is explicitly specialized to this rectangle. An external `--fixture` must match the supplied fixture; a changed experiment fails clearly before computation. Detached execution records `repository_dirty_at_start: null`, not a false clean state, and retains the archive creator's source provenance separately. Current repository-generated results still correctly say dirty.

Current verification:

- `tests/test_variational.py`: 11 passed in 11.94 seconds.
- Fresh repository generation: all exact and twelve numerical checks pass.
- Extracted-bundle regression: complete execution and HTML generation pass outside the checkout; optional monograph assets are reported missing; no missing book links are emitted.
- All repository HTML download links resolve; ZIP CRC check passes; generated inline JavaScript passes `node --check`.
- True minimal-environment and current-wheel verification are delegated to the package verifier; they are not claimed here merely from the source-layout regressions.
- Browser QA remains unverified because the parent's environment denied local serving/local-file browser access. No workaround was attempted.

No files outside the assigned implementation, generated outputs, and this evidence report were edited. No Git staging, commit, or publication was performed by this agent. The source is stable for independent re-review and eventual clean-commit artifact regeneration.


## Final import-order cleanup

Moved ordinary NumPy/SciPy/mpmath imports before the bundle bootstrap. The sole delayed toolkit import retains a narrow, explained `# noqa: E402` because it must follow the explicit bundle path selection. No mathematics or package module changed in this cleanup.

- Ruff on the driver, variational module and focused tests: all checks passed.
- Focused tests after cleanup: 11 passed in 11.94 seconds.
- Preliminary result, offline HTML and reproduction ZIP regenerated; all exact and numerical checks pass.
- Final driver SHA-256: `efd0f829cb8e8663b23ab23eb0dd19e3988afd1db3710d2fccaf65c3a38f28f5`.
- Preliminary ZIP SHA-256: `f13c1437f6ac093e85de80b7fc1a5a020c8fc1624fc9fd0c7038eae132f81f66`.
- Fresh two-mode wheel/detached execution is delegated to the package verifier; the wheel contents are unchanged by this driver-only cleanup. No full-suite repeat was needed.
- No commit or publication performed; preliminary artifacts retain the dirty source state.
