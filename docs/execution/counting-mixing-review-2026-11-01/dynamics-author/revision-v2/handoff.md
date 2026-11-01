# Metadata and bibliography delta handoff

Completed the requested bounded batch. The corrected ledger is awaiting independent targeted acceptance; the four analytic chapter hashes remain exactly those approved in `dynamics-review/approved-manifest.json`.

The ledger has exactly three changed leaf strings:

- R1: `s27.tensor_first_corner` now locates `eq:globaldiagonal` in Section 25.
- R2: Gorodnik–Nevo Theorem 5.2 is pinned to printed page 147, with its proof beginning on page 148.
- R3: Arana-Herrera's stabilizer denominator is pinned to the unnumbered display in the sketch of Theorem 1.1, printed/PDF page 5, immediately after Theorem 1.8. Equation (1.4), the removed locator, instead defines a scaled counting measure.

`source-pins-corrected.json` carries the two corrected source pins. Original author source pins, reports, manifests, scripts, baseline snapshots and all other top-level author evidence remain byte-identical; the before/after evidence for this batch lives only in this `revision-v2` directory. Do not regenerate the historical author ledger or report using the old scripts.

The shared main source changed only six existing bibliography entries: McShane–Rivin v1, Bárány et al. v2, Benirschke–Servan's 2026 erratum, Doan–Li–Nguyen's theorem/lemma locators and proof-audit qualification, and the two OpenAI initial-release PDF/source revision pins. Their conditional/unaudited status remains explicit. No new source verification or PDF hash/page verification is claimed by this metadata integration.

Checks passed: all main bytes outside the bibliography unchanged; all 129 bibliography keys/order unchanged; the complete expanded sequence of 607 unique labels unchanged; 125 chapter labels assigned exactly once among 59 ledger claims; all four approved chapter hashes unchanged; all original top-level author evidence unchanged. The precise patches are `bibliography-only.diff` and `ledger-only.diff`; `delta-manifest.json` records the three leaf repairs and both canonical before/after hashes.

Canonical SHA256 after this batch:

- `book/claims/sections26-29.json`: `8e462191ee8571f262d2c7ee9a90365a41eb526e9b1aaf4369fdb601897d506f`
- `book/polyhedral_volumes_and_geodesic_identities.tex`: `087fd8690a43fc023b0feb370dc07a1421e06f770d98abaf4234bc88116d6a07`

No chapter proof, code, shared README, PDF marker, PDF build, commit, upload or deployment was changed or run. Main bibliography ownership is released to root; targeted ledger acceptance remains the next review step.
