# Sections 30–31 author audit

The local analytic chain was checked against the extracted baseline at commit `9c8b61790aaa674902b9d60e80122c318a578bcc`. The two chapter files retain all 35 labels in their original order. Section 30 has 32 fine-grained claim records and Section 31 has 25. This is the author phase; independent review and integrated typesetting remain separate root-coordinated gates.

## Mathematical conclusions and changes

The normalized Möbius identity is correct for signed primitive vectors and a convex-body gauge whose lattice minimum is one. The rewritten opening records the boundary convention and the elementary uniform tail bound. The decreasing-envelope Dini comparison correctly treats the final interval below one separately. Its absolute-value consequence is O(L); the PNT splitting in Section 31 gives o(L) when the same geometric Dini integral is finite.

The strictly convex all-point o(L) proof is sound. Strict convexity makes both endpoint chords vanish, concavity gives absolute continuity and integrable derivative, and the fixed-ray Fourier limit follows from Riemann–Lebesgue. After smoothing at a fixed physical radius, the nonzero Poisson terms admit a summable majorant independent of the dilation. Taking the dilation limit before the smoothing-radius limit gives o(L), without an unproved uniform directional decay rate. The text now expands the endpoint absolute-continuity argument. No smoothness, positive curvature, or external irrational-flatness theorem enters this proof.

The dyadic inversion is exact after a finite telescoping remainder, and the quadratic asymptotic is essential for its infinite version. Event statistics correctly need lengths through 4T, include multiplicities and both relevant one-sided limits, aggregate simultaneous events, and exclude the external left limit at T. The exact rational example `[2,2,4,5,8]`, T=2 gives M=5/2 and Q²=49/20.

The row proof is valid when a two-sided local upper graph exists. This graph condition is now explicit rather than hidden in “write the boundary as.” The irrational contact removes the initial lattice point; widths are eventually smaller than the prime row index; integer rounding and exclusion of at most one prime multiple give the w−2 bound. Concavity yields the exact microscopic-width comparison. The three illustrative profiles are convex sufficiently near zero and give their stated inverse widths, but no one profile has been established for either experimental torus. The height requirement now follows from an exact perturbation identity, and floor/ceiling certification is distinguished from numerical precision agreement.

The large-divisor transfer identity, reciprocal-radius lattice bound, Möbius area tail, and the fixed-U PNT argument are correct. The logarithmic and power balance exponents are correct, with both geometric and arithmetic hypotheses required. The VK comparison is a consequence of the same splitting argument and is not asserted optimal.

The fixed zero-free-half-plane equivalence previously had only a compressed proof sketch. The revision gives explicit zero-free disks for the logarithm, a Borel–Carathéodory bound, a three-circles exponent below one, and half-integer Perron inversion at T=x². The converse uses local uniform convergence of the Mellin integral. The zeta pole is expressly excluded from the nonvanishing statement and becomes a harmless zero of the reciprocal. No recent preprint proof is needed for this conditional implication.

A substantive additional restriction concerns the proposed all-point O(L/log L) target. Under the same irrational contact/graph hypotheses, all integer points on the row give

`max(|Delta(L)|,|Delta(L+1/L)|) >= (L/2)*W(h/L^2)-O_B(1)`.

There is no primitive density factor, and no prime restriction is needed. Therefore this target requires W(h/L²)=O(1/log L) along the contact sequence. The double-exponential profile already displayed in Section 30 has width of order `(log log L)^(-1/beta)`, violating that condition. The text now states compatibility as an additional requirement and keeps the target for a specified torus ball open.

## Primary-source inspection

`source-pins.json` records all eight primary sources and statement locators. Bārāny–Martin–Naslund–Robins v2, Theorems 1.2/1.4, match the polygon comparison. McShane–Rivin v1 Section 2 supplies the norm and integral strict triangle inequality; a boundary segment would contain two distinct rational rays, contradicting that strict inequality. Its Theorem 4.1 is the cumulative benchmark and Conjecture 4.3 is the modular conjecture. Its blanket infinite-flatness and literal linear-lower-bound prose is not treated as an audited input.

Doan–Li–Nguyen v3, Theorem 4.7 and Lemma 4.8, match the stated refinement. The previous sentence claiming that “we have checked the local Fricke and convexity mechanism” had no retained audit evidence and was removed. Only source statements are checked here; this does not validate the preprint's full proof. Its exact-level multiplicity claim remains distinct from cumulative error bounds.

Zhai's publisher PDF gives the geometric hypotheses on page 1 and equations (1.4)/(1.5) on page 2. Baker's publisher PDF gives (H1)–(H4) on pages 267–268 and Theorem 1 on page 268. Both parameter conversions x=L² are correct. The chapter now names rational endpoint tangent slopes in Baker's class explicitly.

Both OpenAI theorem statements were inspected in actual TeX source files at initial-release revision `adc7f1241b42e322a6451854ab7e4b4c146bf78a`, with label `thm:main`. The raw PDFs were unavailable to the web extractor because of their content type; no PDF page number or local PDF hash is invented. The manuscript claims and the inferred Mertens hypotheses remain conditional. Neither proof, Lean artifact, proof-to-formalization correspondence, nor later review status was audited. `bibliography-suggestions.md` supplies root-owned reference edits.

The mathematical arXiv connector returned an unavailable-server error. Primary PDFs and exact-revision TeX sources were read through web retrieval instead. Direct Python network access failed DNS. These retrieval constraints do not block the statements actually read, but they mean the pins are source URL/version records rather than locally downloaded-byte attestations.

## Computation boundaries

The old length-64 driver, fixture, tests and result were not edited or rerun as a campaign. Their existing numbers and residuals remain identified as preserved prior evidence. All historical length-8192 counts, printed table values, precision comparisons and sensitivity claims remain verbatim and unreplayed. A future independent campaign must record fresh provenance and may only be compared with those old values.

`finite_checks.py` supplies small exact fixtures for square/diamond Möbius inversion, large-divisor reversal, square totients, coprime interval endpoints, finite dyadic identities, the block example and rational balance exponents. These finite identities are not proofs of the analytic limits or arithmetic hypotheses. `resource-probe.json` is a small read-only cutoff-256/512 timing probe of the old log recursion, with no high-precision validation and no extension of the accepted bounded evidence.

The full campaign contract was sent to and accepted by the root. It specifies length-only compact storage, a streamed slope identity hash, all dyadic block rows through T=2048, retained deterministic long-path samples, exact rational conditional sensitivity and source/resource records. The installed Apple compiler gives only 53 mantissa bits for long double, so it cannot supply the claimed extended precision by changing the native type. The root owns implementation and review of a new separate campaign.

## Scope of owned changes

Only `book/chapters/30-sharp-diagnostics.tex`, `book/chapters/31-arithmetic-remainder.tex`, `book/claims/section30.json`, and `book/claims/section31.json` were changed in the canonical tree. No main bibliography, shared status document, original repository, archive, previous PDF, experiment source or curated artifact was changed. No build, upload, commit or asymptotic inference was performed by this author phase.
