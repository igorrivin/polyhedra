# Sections 26–29 author handoff

Author revision completed 1 November 2026 against baseline commit `9c8b61790aaa674902b9d60e80122c318a578bcc`. This is an author audit awaiting independent mathematical review. No approval, PDF build, published artifact, upload, or companion execution is claimed.

The owned canonical output consists of four chapter files and `book/claims/sections26-29.json`. All statements and proofs in those chapters were read and audited. External theorem statements, hypotheses, conventions and relevant source formulas were checked; their complete proofs remain cited inputs. All 125 existing labels are preserved in order, and the ledger assigns each exactly once among 59 claim records. The source record contains 24 entries, with explicit version/page pins and access limitations.

## Revisions

- Section 26 states the ambient group hypotheses for the Gorodnik–Nevo input, supplies an explicit two-sided Hölder rate after cylinder approximation, and states the geometric and finite-measure hypotheses for Babillot's qualitative converse. The finite trace converse, scalar-count counterexample, constant-roof obstruction, transition-cell hypothesis and cusp-loss formula remain separate claims. A scalar curve count is not promoted to a quantitative operator estimate.
- Section 27 restricts the finite filling-graph stabilizer argument to integral pairs, fixes the effective square-tiled source pin to Theorem 3.2, and makes the marked-space meaning of the exact polar pullback explicit. Inverting the approximate Jacobian requires a small relative error and endpoint factors bounded below. The modular Fourier identity now assumes absolute Fourier summability. All deaveraging and full-rate converses retain their quantitative endpoint and derivative assumptions.
- Section 28 clarifies that the admissible stratum model is a conull invariant subset of the affine homogeneous model. The polynomial classification now treats square polynomials and infinity explicitly, retaining the nonsquare genus-two Q(2,2) restriction. The base spectral input has a precise source pin, and the Harish-Chandra integral normalization is displayed. Finite-cover, level-two and spectral restrictions remain; no theorem for arbitrary finite covers or a higher-dimensional principal stratum is claimed.
- Section 29 specifies the isolated first-atom cutoff and the observable's representative on the invariant conull set, repairs a malformed odd-divisor summation, and adds an analytic tail estimate for the rank-two Gaussian covariance series. The tail controls series truncation; it does not certify numerical integration or floating-point roundoff. Primitive pole-to-pole arcs, affine displacements and Fourier rank deletion retain their distinct meanings.

The first-atom and unit-corner dependencies from Sections 23–25 were coordinated with that author. They remain statements about locally finite coefficient measures and isolated atoms. No bounded extraction functional, full-kernel comparison, or uniform nonlinear estimate was imported.

## Preserved open and conditional boundaries

The book still does not derive a uniform two-endpoint transition estimate from unweighted simple-curve growth. The full two-endpoint inverse-Jacobian kernel is exact, but its required effective remainder is an assumption; no circular use of known mixing is presented as an independent counting proof. Cusp truncation and derivative norms remain charged explicitly. The nonsquare genus-two finite model uses external representation and spectral results; finite Gaussian or lattice checks cannot prove its smooth-flow mixing theorem. Hyperbolic first-atom conditioning and the comparison to full bisectors remain open in this audit.

## Sources and bibliography coordination

`source-pins.json` records exact inspected versions and pins. Its contents are also embedded in the canonical ledger. The original Cowling–Haagerup–Howe full-text endpoints were unavailable; the operative theorem statement was checked in the primary research text Benoist–Kobayashi, Proposition 2.6, and that limitation is explicit.

`bibliography-proposal.tex` gives the proposed addition of the 2026 Benirschke–Servan erratum to the existing bibliography entry. Root owns that edit. The chapter uses only the classical genus-two hyperelliptic isometry, not the broader embedding-classification argument repaired by the erratum. The Q(2,2) classification is proved directly by the polynomial calculation.

## Verification and companion contract

`check-revision.py` passed: frozen baseline hashes, exact label order, balanced braces/environments, all citation keys resolving against the 129-entry bibliography, unique claim IDs, valid status/source keys, chapter hashes matching the ledger, and complete one-to-one label coverage. It produces `label-check.json` and the reviewable `author-revision.diff`. This is source-integrity verification, not a PDF build.

`author-scratch-checks.py` passed 288 exact matrix identities for m=2,3,5 and n=1,...,32, plus three symbolic identities for the Lie-algebra commutator, Gaussian rotation derivative and terminal differentiation. The recorded environment is Python 3.12.11 / SymPy 1.14.0. `author-scratch-result.json` explicitly identifies these as limited author probes, separate from the planned root-owned companion.

`companion-fixtures.md` specifies eight finite fixtures, formulas, source labels, parameter ranges and limits. The two-mark Gaussian contract includes the determinant-orbit integral, divisor-series formula, Euler product, and analytic tails for both truncations. Numerical integration, arithmetic precision and total-error certification must be recorded separately by the companion. No `experiments/counting_mixing/` execution or `artifacts/counting_mixing/result.json` is claimed here.

`author-manifest.json` freezes the five owned canonical outputs and outer review records. Independent review should use those hashes and record any subsequent correction separately.
