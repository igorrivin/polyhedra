# Independent companion review, 2026-11-01

Verdict: **approved for the stated finite computational scope after one corrected failure-path defect**. No unresolved blocker was found in the corrected eight-file companion. This review binds the code and relevant mathematical input files listed in `approval-manifest.json`; it is separate from the whole-manuscript mathematical and PDF reviews.

The reviewer read canonical `AGENTS.md`, all eight companion files, and the relevant formulas in Chapters 12, 13, 14 and 16. The initial manifest SHA-256 is `add353794e52560250ef4bc3f876d5c0e4974e84f2233d6c48f61645dbee8598`; the corrected author manifest is `bf83071d4af17033c8a1a9c53f3a634d6f8b3b9bc3acb444f4a00659c7d56dba`. Only `periods.py` and its test file changed. Their final hashes are respectively `a18044e87b1c49c0232dec5b56e94cc417e6faebda7dc3f0748858d9b12acdc3` and `a929d97ab2790a394cfa0e3a1874248de5ea54da42611f52c07bb0f7b6b58727`.

## Corrected defect

The original matrix norm took a Python maximum without checking every entry. A later NaN could be ignored: `NumericChecks(c).close('probe', c.matrix([1,c.nan]), c.matrix([1,0]))` falsely recorded residual `0.0`. The reviewer reported this before approval; the original author corrected it. `norm` now rejects every nonfinite entry, and `close` separately validates actual, expected and difference norms before scaling.

The reviewer loaded the preserved original module with its verified original hash and ran 24 matrix cases covering NaN, positive and negative infinity, both operands, and all four positions in a 2x2 matrix. The original accepted six invalid cases. The corrected code rejects all 24 and still accepts a finite complex matrix. `nonfinite-before.json` and `nonfinite-after.json` preserve the inputs, outcomes and source identities. The focused test additionally covers 40 scalar/vector nonfinite subcases and overflow during native finite-scalar subtraction. This was a real fail-closed defect; no observed finite fixture value or mathematical coefficient changed.

## Replays and independent derivations

The corrected reviewer replay is `replay-result-final.json`, SHA-256 `140015b209307488766f069de489d0a86260651cdde46736125104a3287ae744`. It passes 192 exact identity checks, 300 numerical checks at 60/90 decimal digits and 72 cross-precision comparisons. Maximum scaled residuals are 1.99900150636e-60 and 2.33422819083e-90; the maximum observed cross-precision difference is 4.31446206296e-60. The final run took 4.628 seconds. All 15 focused tests pass (5.449 seconds); Ruff passes with caching disabled.

The scientific result sections, including all recorded residual strings, are identical across the initial author result, original reviewer replay, corrected author result and corrected reviewer replay. The historical `replay-result.json` remains unchanged. Both the driver and the independent final probes verify stable source hashes over their runs.

`independent_probes.py` and `independent-probes-result-final.json` record 96 exact/guard checks and 34 numerical checks, plus two additional cut-plane points (13 numerical identities each). These do more than replay the driver's expected formulas:

- SymPy starts from the sine-defined trace to expand the Fricke relation with symbolic X, Y, Z, then solves the implicit correction and differentiates the chart Jacobian.
- Inverse-trigonometric geometry independently yields regular area and dihedral Taylor coefficients. Schlaefli integration and area inversion recover the volume terms. Symbolic saddle division/discriminant and derivatives of the dilogarithmic potential verify the local double root and cubic coefficients.
- The figure-eight cosh relation recovers c3 and c5 on the selected tangent branch. An independent coefficient solve inverts the formal filling equation, and integrating that inverse by the envelope relation reproduces the action through theta6.
- Direct constrained stationarity for the six Lobachevsky Taylor jets, solved order by order with a Lagrange multiplier, recovers susceptibility, zero cubic term and the quartic coefficient for all seven slopes, without using the companion's projected-inverse formula.
- A 700-term hypergeometric sum with exact rational recurrence coefficients checks the twelve s-period values at 100 digits; maximum observed scaled difference is 1.40e-100. A five-point real Laplacian of log(area) checks six density values independently of the Wronskian formula; maximum observed scaled residual is 4.86e-35.
- Two-sided delta0 = +/-1e-10 probes check pole cancellation, logarithmic basis differences and area limits at both balanced fixture points; maximum scaled discrepancy is 1.61e-10, within the stated 1e-8 finite-limit tolerance. The path has delta1=0 identically, so fusion and the t basis must reject it. Additional points -1/3+i/10 and 5/4-i/5 pass the finite period checks on their principal cut-plane branches.

The environment is CPython 3.12.11, mpmath 1.3.0, SymPy 1.14.0, using the existing `/tmp/polyhedra-baseline-20261031/bin/python`. SymPy is an independent exact algebra implementation; the numerical formulas still share mpmath arithmetic. No library installation was performed. Exact commands and all stdout/stderr logs are listed in `commands.json`.

## Domain, execution and anti-pattern review

Scientific fixture values enter as rational strings; the exact scalar/matrix/series constructors reject binary floats and booleans on their supported inputs. Weight admissibility, positive Heron chart, primitive oriented peripheral basis, nonzero formal filling derivative and the action chart q != 0 are enforced. The q=0 fixture is confined to covariance and tensor algebra. Multiplier logarithms, rather than SL2 eigenvalue logarithms, match the figure-eight cosh identity and the displayed factors.

The s basis and Hermitian form require only delta0 != 0, while fusion requires both delta0 and delta1 nonzero. Fully balanced weights use their own logarithmic/elliptic formulas. Euler endpoint substitutions analytically combine singular weights with the Jacobian; the weight-9/10 regression passes without zero-times-infinity. Cloned precision contexts preserve global mpmath precision. The corrected residual checker rejects nonfinite values before recording success.

The driver resolves inputs from its own path, runs from outside the repository, does no scientific calculation or output on import, refuses existing and symlink output paths, and uses exclusive output creation to prevent an overwrite race. All scientific checks precede output creation. Source identities, dirty Git state, executable/version, conventions and precision are recorded; a changed hash or commit aborts before a successful result is written. Failure checks use explicit exceptions, not removable Python assertions. The only production subprocess use reads Git provenance; no network, install, random sampling or external manifold engine is invoked. Focused tests cover import/CWD isolation, preserved evidence, injected calculation failure and changed-source refusal.

## Limits

Approval covers this fixed fixture, explicit exact identities, and the named independently checked derivations. Numerical tolerance, two-precision agreement and differences of finite logarithmic series are not interval enclosures or rigorous tail bounds. The finite Gram checks do not certify geometric realization or rank. Monodromy matrices are checked algebraically, without loop continuation. Formal coefficients do not compute a filled manifold, a certified filling volume or torsion. The local regular fold does not prove Section 15's global quantum Airy claims. No full spectral/double-sine/DOZZ computation or general rank/intersection engine is covered. The unaffected volume-toolkit suite was not rerun.

The reviewer wrote only this outer evidence directory. No canonical files, source commits, uploads, deployments, builds or installations were made by the reviewer.
