# Independent Section 9 review — 2026-10-31

Reviewed the uncommitted Section 9 implementation in `consolidated/` based on import commit `c53387221dc6d000ac46c0b1ce44232c50f02a3c`. No implementation files, generated results, or Git state were modified by this review. Scratch copies were made in the system temporary directory and removed after the probes.

Verdict: the mathematics and finite-fixture checks pass. Reproducibility and integer-input validation need the corrections below before this increment is committed and its final artifacts regenerated.

## Findings requiring correction

1. **P1 — Normal installed-package execution fails while collecting provenance.** `experiments/section9/run.py:115-120` makes every source path relative to the repository root. An installed wheel places `variational.py` and `geometry.py` outside that root, so `Path.relative_to` raises `ValueError` before any computation. This contradicts the installed-toolkit command at `experiments/section9/README.md:19-23`. An external `--fixture` path fails for the same reason.

   Reproduced by copying the current package, unchanged, to a temporary package directory and importing it via `PYTHONPATH` from outside the checkout. The source driver raised `ValueError: '.../ideal_poly_volume_toolkit/variational.py' is not in the subpath of '.../consolidated'`. A temporary copy of the supplied fixture separately produced the equivalent `ValueError` for `fixture.json`.

   Use explicit source roles and path locations rather than requiring every imported source to be in the checkout. Preserve hashes of the actual imported module and kernel, the actual fixture, driver, template and book sources. State whether a path is repository-relative or external. Required sources must not disappear silently: the current `if p.exists()` also suppresses missing source records. Test installed-package imports and an external fixture location, then compare the recorded hashes with the actual files.

2. **P1 — The downloads are inspection files, not a runnable reproduction set.** All six linked downloads exist and byte-match their sources, but the downloaded `run.py` assumes its original directory depth. In its current download location it computes `ROOT=consolidated/site` and `HERE=consolidated/site/section9/downloads`. There is no `book/` at that root and no `page.html` next to the downloaded driver. After the provenance issue is fixed, these missing inputs still prevent rendering. The downloaded `variational.py` also imports `.geometry`, which is not included. The README calls these “self-contained download files.”

   Supply an actual reproducibility archive with runner, fixture, template, clear dependency/setup instructions and complete runtime sources. It may vendor the small package subset with `geometry.py`, or require a specified installable toolkit artifact; a lone `variational.py` is insufficient. Handle book-download paths explicitly or make those optional for standalone execution. Verify the extracted archive in a fresh directory outside the checkout without relying on source paths from the development tree. Individual source links can remain as inspectable files and should be labeled accordingly.

3. **P2 — Oversized unsigned labels silently change the mesh.** `packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py:22-24` validates nonnegativity before converting to signed `int64`. A `uint64` value of `2**64-1` wraps to `-1`, and `_mesh` subsequently accepts it as a Python negative index. For points `[[0,0],[1,0],[0,1]]`, triangles `np.array([[0,1,2**64-1]], dtype=np.uint64)` return the angles of the legitimate last-vertex triangle instead of rejecting the invalid label.

   Check integer representability before casting, including the analogous interior/elimination label conversions. Add a focused regression asserting rejection rather than accidental vertex substitution.

## Scope clarification worth including with the corrections

The driver and page are intentionally specialized to this rectangle: reference volume `12*Catalan`, two interior vertices, the 2-by-2 exact determinant, and voltage `x/3` are fixed. The CLI exposes `--fixture`, while the page also hardcodes the off-origin parameter pair `(0.05,-0.03)`. Either require this fixture contract explicitly, or render variable quantities from the supplied fixture/report. An arbitrary fixture path should not imply a general mesh-experiment renderer. This is not a mathematical problem with the supplied fixture.

## Mathematical review

- Compared code and prose with the canonical monograph around lines 1551–1799 and labels `eq:ipolyAngleCoordinates`, `eq:ipolyHessian`, `eq:ipolyDtN`, `eq:ipolySchur`, and `eq:ipolyForestDeterminant`.
- The corner increment `u_b-u_c` in a positively oriented face `(a,b,c)` agrees with the directed opposite-edge convention. Triangle and shared-edge sums are preserved.
- `Lambda'=-log(2 sin(alpha))` and `Lambda''=-cot(alpha)` yield `-D²V=2 L_II` in these coordinates. The factor two is correct. The separate barycentric-gradient FEM assembly supplies an independent matrix construction.
- The integer-coordinate fixture gives `L_II=[[4,-1],[-1,4]]`, `K=[[8,-2],[-2,8]]`, `det(L_II)=15`, and `det(K)=60`.
- Exact `Fraction` calculations originate from integer geometry, rather than rationalizing rounded floating-point matrix entries.
- The rooted-forest enumerator selects exactly `|I|` edges, rejects cycles, and requires one boundary root per component. Here nine forests independently connect the two interior vertices to boundary neighbors, and six use their mutual edge; all fifteen contributing weights are one.
- Eliminating the first coordinate of `K` gives `15/2`; the determinant factorization is `8*(15/2)=60`.
- For boundary voltage `x/3`, harmonic interior values are `1/3,2/3` and the energy is `2/3`, consistent with the constant gradient on the rectangle of area six.
- The off-origin derivative oracle independently differentiates the Clausen volume at 50 decimal digits. The runner restores the prior precision context. This is a numerical comparison, not an interval enclosure.
- Prose clearly distinguishes angle coordinates from electrical voltages, abstract deformed angles from a closed geometric realization, non-strict Delaunay flat diagonals from a strictly simplicial convex certificate, and a finite fixture check from a full chapter proof audit. No mathematical overclaim requiring correction was found for this example.

## Executed checks

Environment: `/tmp/polyhedra-baseline-20261031/bin/python`; imports explicitly resolved to the current `consolidated/packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py`.

- `tests/test_variational.py`: **7 passed in 5.94 seconds** with bytecode/cache writes disabled.
- Fresh in-memory `build_report()`: all **12 numerical checks** and the exact fixture checks passed. No generated output was overwritten.
- Largest declared numerical residual: `3.552713678800501e-14`; independent off-origin Hessian discrepancy: `1.7763568394002505e-15`.
- Six download payloads match their source bytes: fixture, result, driver, reusable operators, canonical TeX and supplied PDF.
- Current source hashes in the freshly constructed report match the files read by this review.
- Reproduced both external-path failures and unsigned-label overflow as described above.

## Remaining verification boundaries

Final artifacts currently describe a dirty preliminary working tree. Regenerate them only after the reviewed source has been committed cleanly, then commit outputs separately. The mathematical source itself has not undergone a whole-chapter proof audit.

Per the parent’s environment checks, browser interaction and visual layout are **not verified**: the sandbox rejects a localhost listener, the in-app browser is unavailable, and Chrome automation rejects local-file URLs. No alternate surface or server workaround was attempted. Static source/download checks do not replace browser interaction QA.
