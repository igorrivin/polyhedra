# Sections 17–22 author freeze

The six assigned chapters and `book/claims/sections17-22.json` are ready for independent mathematical review. Author work is complete for this freeze; this report is not an independent approval. The baseline is `151673b1817e66aae493eb7da1be5ddf49adfe0f`.

## Source scope

Only these seven canonical files were written by this role:

- `book/chapters/17-unfolding-constant-series.tex`
- `book/chapters/18-figure-eight-curves.tex`
- `book/chapters/19-pants-twists.tex`
- `book/chapters/20-torus-twist-series.tex`
- `book/chapters/21-cuff-matching.tex`
- `book/chapters/22-cusps-orthospectrum.tex`
- `book/claims/sections17-22.json`

The main manuscript, bibliography, shared documents and previously reviewed chapters were not edited. No required shared-file or bibliography patch remains. The source audit notes optional addition of Basmajian's original citation, but the existing Parlier key supports the exact stated oriented convention. No stage, commit, maintained companion implementation, installation, PDF operation or upload was performed.

## Mathematical changes

- Unfolding now states nonnegative versus absolutely integrable hypotheses, stabilizer decoration and orbifold conventions. A volume supplies an average unless constancy is independently known. Differentiation and variance criteria have their needed convergence and regularity hypotheses.
- Hu–Tan's displayed dilogarithm kernel is restricted to the cusped torus. Luo–Tan retains the closed oriented genus and subsurface-indexing hypotheses. The Mirzakhani integration citation is corrected to Theorem 7.1/Lemma 7.3; the cusp limit is pinned to Lemma 3.1, equation (3.1).
- Figure-eight classification retains two distinct equal-length nonhyperelliptic labels and one hyperelliptic label per torus simple curve. The pants lift signs, local versus ambient covers and non-disjoint simple lifts are explicit. The positive single-length kernel has a proved alternating tail and an exact finite residual identity.
- The exact local endpoint Hessian is positive definite for fixed ultraparallel lifts at distance `d>0`. The strict twist-convexity proof fixes the itinerary, lifts and winding, interpolates minimizing endpoint configurations, and excludes an all-endpoints-fixed gauge through a gluing equation with twist coefficient `+1` or `-1`. Disjoint curves are the constant-length exception.
- The torus crossing formula explicitly requires a simple curve crossing once. Independent commutator matrices fix the signed boundary convention; derivatives, coarea density, beta integrals, finite integral tails and the exact H/K lattice tail are derived.
- Cuff gluing distinguishes positions from tangential momenta and uses a common coordinate after boundary-orientation reversal. Transverse opposite-side passage fixes the normal sign as well.
- Cusp-gap statements exclude geodesic boundary; exiting rays otherwise require extra terms. Truncation is signed for general decorations, with `lambda=exp(d/2)` and no square-root-of-two factor. Torus arc/curve correspondence and triangle conventions are pinned separately from the local cusp trace proof. Basmajian has coefficient 2 for oriented arcs and 4 after pairing orientations.

## Preserved and added anchors

All 48 baseline labels and all section/subsection headings of these six chapters survive in their original order. The six additions, in source order, are:

1. `eq:figurekerneltail`
2. `eq:figurefiniteidentity`
3. `eq:localdistancehessian`
4. `eq:torustwistderivatives`
5. `eq:torusintegraltail`
6. `eq:Hpartialsumtail`

The read-only graph check found 36 source inputs including wrapper and main manuscript, 613 unique labels, and all 607 baseline global labels surviving in order. This is a snapshot observation, not this author's approval or freeze of the other authors' files.

## Evidence and remaining limits

The ledger records 59 substantive claims with exact formulas, hypotheses, proof summaries, source pins, conventions and computation boundaries. The `source-audit.md` record distinguishes statement checks from full external-proof review. In particular:

- Lei–Zhang was available only through its publisher-supplied first-page abstract. No inaccessible full proof is claimed checked.
- Mirzakhani's volume paper was inspected through targeted primary-PDF indexed statements after direct retrieval timed out.
- Kerckhoff's accessible simple-curve statement is context; the chapter's nonsimple twist proof is local.
- Wolpert's background first variation is independently derived in the chapter. The final-page external formula was not recovered in this increment.
- The complete original McShane, Basmajian and Luo–Tan proofs were not re-refereed.

`author_scratch.py` passed 80 finite exact identities/predicates and 268 floating comparisons at each of 70 and 110 digits. `author-scratch-result.json` records versions, the script identity and observed residuals. This is representative author evidence, not the complete maintained companion and not interval arithmetic. A probe initially compared the exact lower bound `t^2 h(t)>=2` with a strict floating inequality and encountered last-digit rounding below 2 at 110 digits; the repaired probe uses its declared numerical tolerance. The analytic bound was unchanged.

The finite kernel telescoping coefficients were checked exactly. At large N, a floating zero on the left is classified as cancellation-limited, while the strictly positive tail bound is retained logarithmically. At length 1000, direct tanh/coth subtraction loses the positive signal; stable H, logistic-tail and `log1p` shadow calculations retain it and use relative or scaled checks. Analytic tails remain separate from roundoff and quadrature.

`companion-contract.md` preserves groups G1–G10 for the later implementation at `experiments/quantum_geodesics/`, with result `artifacts/quantum_geodesics/result.json`. It also includes stable torus `delta=A^2-1`, a small-cuff fixture and explicit guard-precision/reference-conditioning guidance. Maintained implementation and execution are marked pending in every ledger coverage record. No global curve or orthogeodesic sum is numerically approximated, and no general multicurve minimizer is requested.

`author-validation.json` records heading, label, citation, local brace/environment and EOF checks. All seven new canonical files were checked directly by `git diff --no-index --check /dev/null FILE`, with no whitespace diagnostics; the tracked `git diff --check` also passed. Each chapter and the ledger end in exactly one newline. No PDF compilation was needed for these static checks.

`author-freeze-manifest.json` binds the seven canonical source hashes and this outer evidence set. Independent mathematical review, maintained companion implementation/review, integration and a later PDF build remain separate pending gates.
