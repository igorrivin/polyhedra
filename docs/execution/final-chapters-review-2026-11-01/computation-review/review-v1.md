# Independent companion implementation review, v1

**Changes required in the driver validation gate. The frozen numerical result passes review.** Two bounded findings remain: required finite coverage can be removed without rejection, and declared acceptance/source provenance can be removed or changed without rejection. Neither finding is a wrong number or missing case in the actual frozen author fixture/result.

The reviewed source set is `1a19c98c7822ac5b22f46db044a70a45880a11470db10d94a5d084564ba7614d`: 20 companion files and three guarded `quantum_surgery` dependency files. The accepted subject for this review is the author's `full-v1/author-result-70-110.json`, SHA-256 `618d7125e80813db18b96c55513bd6a0432a1cf7fad63595c6c58d89112b67a4`, 4,694,249 bytes. The full initial subject is preserved under `subject-v1/`; it must not be replaced during repair.

## Required findings

### CR01 — complete finite coverage is not enforced

Location: `experiments/quantum_geodesics/run.py`, `validate_fixture` lines 73–79 and `validate_geodesic_fixture` lines 91–125 in the frozen version.

The gate checks a subset of lists exactly and other lists only for nonemptiness. Five in-memory corruptions pass both this gate and the affected group's calculation, normally and under `-O`:

1. Delete the last Q3 slope, `(5,-2,-2,1)`. Every remaining q is positive, contrary to Q3's required two signs.
2. Replace the Q2 polyhedra list by three copies of its first simplex. The centered cube and translated box disappear, and repeated IDs are accepted.
3. Replace G7 `large_partition` by `{"a":"7","tau":"0","N":0}`. No partition has the required `L_N >= 1000`; the separate `u=1000` individual term does not replace this tail fixture.
4. Keep only the first G8 stationarity case. The position-matched, shifted, nonstationary example disappears.
5. Keep only the first G8 endpoint list. The inconsistent cyclic-spacing configuration disappears.

The actual frozen fixture has all five required features. Its record counts and independent numerical evidence remain valid. This is a completeness-gate regression, not a formula failure.

Repair the driver so it rejects missing, duplicate, truncated, or substituted entries in the accepted scientific fixture profile across all 14 groups. The complete expected profile is the preserved fixture in `subject-v1/experiments/quantum_geodesics/fixture.json`; `required-fixture-profile-v1.json` supplies its canonical JSON digest and the complete data. Retain every current input, guard setting, extra large-cuff minimum, and semantic branch. Either an explicit accepted-profile pin or equivalent strict structural and semantic checks are suitable; comparing a fixture only with a fresh read of that same mutable fixture is not an independent gate. Keep lower-level mathematical functions available for focused subsets if desired; completeness belongs to the full driver.

Add regression cases for all five failures and representative omitted entries from the other grids, including duplicates. They must fail before `calculate`/success output in normal and optimized execution. Add an unchanged full-profile success case.

### CR02 — acceptance/source identity declarations fail open

Location: `experiments/quantum_geodesics/run.py`, `validate_fixture` lines 52–67 and `source_state` accepted-manuscript observation loop.

The current gate validates local target Markdown hashes only for whatever entries remain in `formula_contracts`. It neither requires both contract entries nor binds the other declared acceptance/source hashes to their existing local provenance copies. Eight independent corruptions pass normal and optimized validation:

1. Set `formula_contracts={}`.
2. Set `accepted_manuscript_sha256={}`; `source_state` then reports zero accepted-source observations.
3. Change quantum `review_acceptance_sha256` to 64 zeroes.
4. Change quantum `accepted_source_freeze_sha256` to 64 zeroes.
5. Change geodesic `review_acceptance_sha256` to 64 zeroes.
6. Change geodesic `final_source_review_sha256` to 64 zeroes.
7. Change geodesic `accepted_source_set_sha256` to 64 zeroes.
8. Change the accepted pin for `book/chapters/10-quantum-introduction.tex` to 64 zeroes.

All original local copies and declared pins are correct: the independent result audit checked all six local provenance files against the original fixture and the parent's accepted identities. The finding concerns accepting altered declarations without rejecting or withdrawing the associated contract provenance.

Require the complete approved contract records, their local acceptance/source-copy identities, and the complete 14-entry accepted-manuscript pin map. Reject missing/extra/altered provenance declarations and bind each declared local acceptance hash to the corresponding local file. Keep the three dependency guards intact. Do not introduce outer scratch directories as runtime dependencies.

Preserve the important distinction between an **accepted source pin** and the **currently observed manuscript**: later authorized prose-pointer integration may legitimately change the latter. Validate the accepted map against its accepted provenance, while continuing to record live current hashes and `matches_accepted_snapshot` separately. Do not turn a legitimate later live manuscript observation into a hard equality requirement with the earlier accepted source bytes.

Add all eight regressions under normal and optimized execution, plus a failed-run/no-output test for malformed provenance. Retain the successful original profile.

## Verified evidence

The actual full companion was rerun independently from `/private/tmp`, using the supported isolated Python and a new reviewer-owned output. It passed in approximately 16 seconds. The author's and reviewer's parsed JSON differ **only** at `/generated_at_utc` and `/runtime/elapsed_seconds`; all scientific strings, fixture values, source maps, status fields, and all other metadata agree exactly. This is a fresh reviewer replay of the dirty source, not a clean-source checkpoint replay.

Counts were derived from the actual record arrays, not copied from summary fields:

| Group | Exact | Floating comparisons | Cross-precision observations |
|---|---:|---:|---:|
| Q1_figure_eight | 82 | 508 | 82 |
| Q2_klein_geometry | 127 | 0 | 0 |
| Q3_peripheral_filling | 33 | 24 | 12 |
| Q4_charge_curvature | 205 | 0 | 0 |
| G1_torus_unfolding | 1 | 44 | 3 |
| G2_pants_traces | 27 | 0 | 0 |
| G3_figure_eight_kernel | 240 | 424 | 56 |
| G4_local_distance | 4 | 328 | 40 |
| G5_seams_torus_holonomy | 0 | 606 | 103 |
| G6_twist_coarea | 0 | 372 | 60 |
| G7_twist_partition | 452 | 1242 | 129 |
| G8_endpoint_matching | 2 | 6 | 2 |
| G9_cusp_decoration | 168 | 656 | 16 |
| G10_boundary_shadows | 1 | 56 | 6 |
| Total | 1342 | 4266 | 509 |

All 30 existing tests passed normally and under `-O`; Ruff passed. Reviewer-owned probes made 50 adverse-input/control checks in each mode: 37 behaved as required and 13 reproduced the two findings. The tests also confirm finite/exact input rejection, lost-positive-signal rejection, real-domain rejection, exclusive output creation, and a dangling output symlink being rejected without creating its target. AST inspection found zero production `assert` statements. No production use of Python `eval`, global precision mutation, hidden random oracle, broad exception swallowing, or import-triggered calculation was found. SymPy polynomial `.eval(1)` is exact polynomial evaluation.

The 23-file runtime map and complete author-stage manuscript/TeX maps are recorded in `result-audit-v1.json`. Before/after/current source observations agree, including Git HEAD, dirty status and all 46 observed book TeX files. These are **46 observed files, not 46 active inputs**; the integration inventory distinguishes 36 active inputs and 10 inactive preserved figure/preamble fragments.

## Independent mathematical and numerical checks

`independent_oracles.py` imports no companion implementation. Its 400 exact and 1,322 numerical checks passed, with alternate constructions across every group:

- Q1 uses cyclotomic quotient-ring polynomial products and root evaluation for all 41 N values.
- Q2 uses nested polynomial integrals, Cartesian box-edge support formulas, and exact rational scalar remainders; no optional full-volume quadrature is claimed.
- Q3 uses explicit Lagrange-reversion coefficients and mixed kernel derivatives for all four slopes; the implementation freshly calls only the guarded old inverse helper. Q4 independently checks all nine charge specializations and margins.
- G1 uses a dilogarithm primitive. G2 uses Fraction matrix products. G3 uses a higher-precision logarithmic recurrence for all 28 input/depth cases, compares the tiny positive B_N itself relatively, and separately bounds the **absolute** error in log B_N. Relative agreement in a huge logarithm alone would be inadequate.
- G4 uses an upper-half-plane asinh distance with numerical derivatives. G5 uses the Fricke identity and log-eigenvalue derivatives on all 49 ordinary/small-cuff torus cases. A separate 600-digit direct coth reference resolves the a=1000 positive minimum; no derivative or matrix oracle is claimed there.
- G6 uses incomplete beta finite integrals and positive omitted tails for all 30 cases. G7 uses translated logistic-density quadrature for individual terms and independent logistic tails for all 101 partitions. G8 checks both endpoint/winding cases and both derivatives. G9 uses Fraction cusp matrices, triangle identities and signed lengths. G10 uses an integral with the tiny exponential amplitude factored outside the quadrature.

These references use 250 digits ordinarily, 350 for the G3 iterate recurrence and 600 for the separate large-cuff minimum. They share mpmath as an arithmetic backend. They are alternate finite formulas, not independent roundoff certificates or global proofs.

Actual implementation precision is 90/130 digits ordinarily, 170/210 in G3 and 150/190 in G5. Requested precision is 70/110 and comparison thresholds are 1e-55/1e-95; neither field certifies all requested digits as correct. G3's exact finite symbolic telescope is separate from cancellation-limited numerical residuals. G6's analytic two-sided truncation inequality is separate from heuristic quadrature estimates and roundoff. G7/G10 retain positive tiny values where naive tanh/coth expressions return zero. Scientific strings with enormous exponents were parsed using arbitrary-exponent mpmath, not Decimal.

## Repair and acceptance boundary

Release the frozen canonical driver/tests to the author for CR01/CR02 repair only. No mathematical module or fixture value change is required. Preserve this initial subject and all evidence. A fresh full author run and normal/optimized tests are required after repair, together with a comparison showing that all scientific groups and numeric strings are unchanged. If the mathematical modules and fixture are byte-identical, the alternate-oracle evidence can be reused explicitly by identity; it must not be relabeled as a fresh oracle rerun. A targeted independent reviewer recheck must close both findings before full implementation approval.

No final code acceptance is granted by this report. No interval enclosure, whole-surface sum, arbitrary multicurve solver, global classification, general filling/GMC construction, asymptotic theorem, installation, clean-source checkpoint, PDF build, or upload is certified.
