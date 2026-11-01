# Section 15 analytic author review

Date: 2026-11-01. Baseline: `3ddf610dbe4578c7828e55f4e9cd92aacaba6df6`. Author scope: `book/chapters/15-quantum-airy.tex` and `book/claims/section15.json` only. This is the analytic freeze; the separately assigned exact-integrand computation and its eventual manuscript supplement are not included.

The stated uniform regular-family Airy theorem and its first correction are retained with an expanded analytic proof. No additional conditional hypothesis was needed to close the identified local and global estimates. This author assessment uses the specified external special-function identities and the geometric Murakami–Yano volume theorem; it does not re-prove those source theorems. Independent approval belongs to the separate reviewer record for the exact file hashes below.

## Repairs and proof coverage

1. The Barnes normalization is now explicit. The convergent Gamma integral has subtraction `(Q-2x)/(2u)`. TV arXiv v3 (A.1) prints `(Q-2x)/u`; the small-u expansion proves that this printed coefficient cannot converge. The corrected difference gives the exact real log-S integral and the existing centered remainder `D_b` with its displayed sign and factor `1/2`.
2. The leading centered primitive is fixed exactly, including its linear constant. Its second derivative is `pi*cot(pi*z)`, its value at `1/2` is zero, and its first derivative there is `log(2)`. The last identity follows from `csch(s)=coth(s/2)-coth(s)` by dilation. Compact holomorphic bounds and the global real-part estimate follow directly from the remainder integral. The chapter distinguishes the centered z strip from the larger fundamental x strip.
3. The formerly implicit phase-constant argument is replaced by a real specialization of Murakami–Yano (1.14)–(1.18). Oddness and periodicity give `G=2*(U_Lambda+Delta_Lambda)` term by term. The two compact saddle values have absolute value `2W` and tend to the same Euclidean point with `W->0`; therefore `G_star=0` exactly, without an unspecified complex branch choice.
4. The initial contour is now relocated at fixed b before invoking the small-b centered-strip estimate. The exact eight-factor modulus has exponent `-2*pi*Q*abs(Im w)` because the coefficients sum to `-2Q`. Horizontal connectors vanish, the pole families remain separated, and locally uniform domination gives holomorphic continuation. The literal printed TV `dw` and the chapter's upward `dw/i` retain their explicit factor of i.
5. The fold-line phase maximum is strict by the displayed positive rational derivative of Psi. The large-y sine arguments give a uniform limiting decay slope `2*pi`. This yields an explicit negative phase gap outside any fixed small fold neighborhood, with linear decay farther out. The small-b exact modulus estimate transfers it to the entire quantum contour.
6. On the positive displacement `c*h^(1/3)`, the even Taylor expansion gives the claimed quadratic-plus-quartic Gaussian bound, uniformly for all fixed bounded real zeta. The chapter records a concrete phase remainder `C*(|x|^5+|t||x|^3+t^2|x|+|t|^3)`. After rescaling, exponentiation on the growing cutoff gives an integrable `C_Z*lambda^2*(1+|Y|^8)` error. The complementary local and global tails are controlled separately. This proves the additive uniform error, including negative zeta and Airy zeros.
7. The vertical Airy representation is derived from DLMF 9.5.4 using explicit vanishing horizontal connectors. This fixes the orientation and signed Jacobian. The existing finite coefficient algebra then gives the unchanged first correction `-3*sqrt(2)*h^(1/3)*Ai'(zeta)` and prefactor `3*h^(1/3)/(4b)`.
8. Noncancellation now uses the positive minimum of Ai on each fixed `[0,Z]`. The scalar sine zeros are genuine double poles in that physical window for sufficiently small b. The displayed resonance sequence is labeled as candidate scalar resonances, with genuineness established for all sufficiently large m. No noncancellation or relative-error assertion is made on negative-zeta intervals containing Airy zeros.

## Scope and status boundaries

The proof covers the explicitly normalized meromorphic Barnes integral on one regular slice, for every fixed bounded real transition interval as b tends to zero. It does not establish arbitrary-shape asymptotics, a uniform limit with unbounded zeta, fixed nonzero volume, a glued topological invariant, a colored-Jones volume conjecture, or identification with the cone-metric measure.

The 13-claim ledger now separates author-checked analytic derivations, external-statement consequences, prior finite exact algebra, the prior Airy approximation column, and the original historical quantum calculation. The original numerical subsection is byte-identical to baseline at this analytic freeze. New numerical values, when independently verified, must carry their own provenance and be supplemented in a separately reviewed change; they cannot recover the original missing evaluator or raw output.

## Primary-source pins

- [Teschner–Vartanov, arXiv:1202.4698v3](https://arxiv.org/pdf/1202.4698v3), version dated 2013-04-30: (2.27) and following contour prescription, printed p. 7; (A.1), p. 22; (A.11), (A.13), (A.15), (A.16) and the Gamma quotient, pp. 22–23. The HTML and PDF text both contain the factor-two error in the linear subtraction of (A.1). The correction is derived in the chapter from convergence, not inferred from a numerical fit.
- [Murakami–Yano, CAG 13(2), 379–400 (2005)](https://intlpress.com/site/pub/files/_fulltext/journals/cag/2005/0013/0002/CAG-2005-0013-0002-a005.pdf), DOI `10.4310/CAG.2005.v13.n2.a5`: Theorem 2 and (0.4)–(0.8), pp. 381–382; real Lobachevsky specialization (1.14)–(1.18) and the following absolute-value statement, pp. 385–386. The author-hosted preprint is independently linked in the reviewer record; this author uses the published pagination.
- [DLMF 9.5.4](https://dlmf.nist.gov/9.5.E4), version 1.2.8, release 2026-09-15: oriented Airy contour. [9.2.1 and 9.2.3](https://dlmf.nist.gov/9.2) and [9.9(i)](https://dlmf.nist.gov/9.9.i) additionally support the Airy ODE, positive initial value and absence of nonnegative real zeros. The vertical deformation is proved in the chapter rather than imported as an unstated convention.
- Corroboration of the corrected Gamma normalization, not a new manuscript dependency: [Verlinde–Zhang, JHEP05(2025)053, Appendix A.4, p. 23](https://doi.org/10.1007/JHEP05(2025)053). The primary published PDF gives the denominator `2t`. No bibliography entry was changed.

The sources were opened on 2026-11-01. These are document/version/equation pins, not downloaded-source-byte hashes.

## Verification performed

`git diff --check` passes. The ledger parses as JSON. A read-only recursive expansion of `book/main.tex`, compared with the baseline commit, confirms all 607 labels are unique and in exactly the same order. The 21 Section 15 labels are unchanged in order and are all covered by the ledger. The original numerical subsection is byte-identical to its outer baseline snapshot. No builds, installs, commits, network mutations, uploads, or changes to original repositories were performed.

The exact checks are in `audit-owned.py`, `label-coverage.json`, `baseline-sha256.json`, and `author-manifest.json` in this directory. Snapshot copies precede all author edits under `baseline/`.

Final analytic author hashes:

- `book/chapters/15-quantum-airy.tex`: `2688ef6862492f93cd49de4c50017eb33496ad0d1b77cd8f4220150910a2ef1e`
- `book/claims/section15.json`: `8d5ba46372dda6a108bf913e30b661f87e16b4985b444ed8107d9feefb4c6c3d`
