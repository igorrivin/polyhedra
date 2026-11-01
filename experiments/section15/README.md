# Section 15 finite checks

This companion checks finite algebra in the [Airy chapter](../../book/chapters/15-quantum-airy.tex) and recomputes its **Airy approximation column**. It does not evaluate the exact quantum integral. The six reported quantum-integral values are preserved as historical inputs in [historical-table.json](historical-table.json); they have no supplied raw-output, precision, contour or tail record.

From the repository root, with Python 3.10 or newer and mpmath installed:

```sh
python experiments/section15/check.py --output /tmp/section15-checks.json
```

The script resolves its source inputs relative to itself and can be invoked by absolute path from another directory. It makes no network calls. A failed comparison returns a nonzero exit status. The JSON records current Git source state, script/fixture/chapter hashes, Python and mpmath versions, working precisions, residuals, tolerances, elapsed time and explicit evidence limits.

The exact calculation works with rational pairs representing `a+b*sqrt(2)`. It differentiates the five affine-angle terms in `G`, checks the fold Hessian and third/fourth derivatives, derives the amplitude coefficient, clears denominators in the rational expression for `Psi'`, substitutes the weighted Airy variables, and reduces the correction using `Ai''(zeta)=zeta*Ai(zeta)`. Positivity of the sines at the fold fixes the signs in the squared amplitude and logarithmic identities. The phase constant `G_star=0` is not checked by this algebra.

The numerical calculation uses decimal strings for the printed inputs, scoped 80- and 120-digit mpmath arithmetic, and a separately coded ODE power series with 160 and 240 terms. That series uses mpmath's gamma and elementary functions for its initial values, so this is an independent formula check within one numerical library. Precision agreement and agreement to six printed decimals are numerical comparisons, not interval enclosures. Scaled differences use the retained rounded quantum values; their conditional rounding half-widths are arithmetic diagnostics, not reconstructed quadrature error bars.

The [claim ledger](../../book/claims/section15.json) separates these frozen finite checks from the later [Section 15 analytic review](../../docs/execution/section15-analytic-review-2026-11-01/README.md) and [exact-integrand companion](../section15_quantum/README.md). The later increment supplies a reviewed regular-family proof and new numerical quadrature with precision, contour and cutoff comparisons; those results are not produced by this script. Its new result path is `artifacts/section15_quantum/result.json` at the repository root. The original historical JSON and `artifacts/section15/checks.json` remain unchanged. The new first quantum value rounds to `0.459086`, whereas this preserved historical input is `0.459087`; the original rounding procedure remains unknown. Neither companion provides a total interval quadrature certificate.

Mathematical sources checked for this increment are [DLMF 9.2](https://dlmf.nist.gov/9.2), [DLMF 9.4](https://dlmf.nist.gov/9.4) and [DLMF 9.5](https://dlmf.nist.gov/9.5). The equal-label integral and its printed measure were inspected in [Teschner--Vartanov, arXiv:1202.4698v3, equation 2.27](https://arxiv.org/html/1202.4698v3); no complete re-audit of that paper is claimed.
