# Finite quantum and surgery checks

This offline companion checks explicitly bounded formulas from [Section 12](../../book/chapters/12-quantum-boundary-measure.tex), [Section 13](../../book/chapters/13-four-point-fusion.tex), [Section 14](../../book/chapters/14-normalized-quantum-comparison.tex), and [Section 16](../../book/chapters/16-dehn-filling-response.tex). It is separate from the volume toolkit. The geometric hypotheses and source theorems remain mathematical inputs.

Run with Python 3.10 or newer and mpmath 1.3.0. The supported review environment is `python`; no installation or network access occurs during these commands:

```sh
python experiments/quantum_surgery/run.py --output /tmp/quantum-surgery-result.json
python -m unittest discover -s experiments/quantum_surgery/tests -v
ruff check experiments/quantum_surgery
```

The output must be a new path in an existing directory. The driver resolves inputs relative to itself, works from another directory, and does no computation on import. A failed identity, numerical check, or source-change check stops before a successful result is written. Exclusive file creation also prevents overwriting evidence if the target appears during the run. Initial author output belongs outside the canonical repository, under `../execution/quantum-surgery-review-2026-11-01/computation/`. A later reviewed artifact may use `artifacts/quantum_surgery/result.json`.

`fixture.json` fixes two rational weight tuples with opposite signs of δ₀, three cut-plane points including a conjugate pair, two balanced points, three positive Heron-chart points, and seven primitive peripheral bases. Fractions and decimal inputs remain strings until converted exactly; binary floats are rejected as scientific inputs. Runtime measurements use ordinary wall-clock seconds.

The exact checks use `Fraction` and a small explicit representation of a+b√d for d∈{−3,−2,2,3}. Truncated series have degree at most six, and exact matrix determinants/inversion cover sizes at most four. The scope is:

- Section 12: the equal-trace Fricke expansion through A⁴ before dividing by A²; the Heron chart, orientation, implicit first correction and Goldman density coefficients at three rational points; the distinct heavy-charge and exact dictionary scalings. A fixed auxiliary Gram determinant checks that its two blocks have full rank.
- Section 14: regular tetrahedron area and dihedral Taylor coefficients through ℓ⁴, the Schläfli volume coefficients through ℓ⁵, and their area conversion; rank-three regular Euclidean Gram data; the saddle polynomial factorization and discriminant at two exact quadratic-field values, including its non-branch double root. The screened saddle cancellation is checked separately. These formulas are taken directly from Section 14; the earlier Section 15 companion and its outputs are not imported or copied.
- Section 16: recursive inversion of a=pu+qv through a⁵, followed by a=iθ, the stationary action through θ⁶, the envelope derivative, peripheral basis covariance, the canonical generating differential, and the square of the Gaussian Jacobian. The q=0 basis is checked only where that chart is defined. The figure-eight coefficients are checked against cosh(v/2)=1+cosh(u)−cosh(2u) through u⁶. Separate K/P/E calculations recover the constrained cubic and corrected quartic tensors and agree with the Neumann–Zagier coefficient. Peripheral symplectic rows, one-cusp Hessian compatibility, and one rational two-cusp block determinant 1/16 are finite matrix checks.

The numerical checks use separate cloned mpmath contexts at **60 and 90 decimal digits**. Each tolerance is 10⁻⁽ᵈᵖˢ⁻¹⁵⁾ in the scaled norm |actual−expected|/max(1,|actual|,|expected|); matrices use the maximum absolute entry. The JSON records every residual and the observed difference of the two precision runs. The tolerance reserves fifteen digits for cancellation and numerical operations; actual agreement must pass it. Configured precision is not presented as an achieved error bound.

Section 13 compares the s/t hypergeometric periods, gamma connection matrix and its determinant, Hermitian congruence, beta normalization, area, Wronskian, and curvature −1 density. The branch domain is C minus ((−∞,0]∪[1,∞)), with principal branches positive on (0,1). The nonresonant connection needs δ₀δ₁≠0. An s-only basis needs only δ₀≠0, so the balanced-limit path with δ₁=0 is not accidentally treated as a nonsingular t basis.

Independent Euler-arc quadrature evaluates unit-interval beta-weight integrals. Each integral is split at 1/2. On either half, t=xᵈ/2 or t=1−xᵈ/2 uses the rational endpoint exponent's denominator d. Combining the Jacobian with the singular weight analytically leaves x raised to a nonnegative integer power. This avoids evaluating infinity times zero or losing most digits to the endpoint weight 9/10. Tanh-sinh then integrates smooth finite endpoint values. The integral and special-function formulas are independent representations using the **same mpmath arithmetic backend**, not independent numerical libraries.

Fully balanced weights use their own elliptic/logarithmic basis. Checks include the Frobenius logarithmic series, fusion involution, Hermitian form, elliptic area, Wronskian, and Poincaré density. Differences between two finite series truncations are diagnostics, not rigorous tail bounds. The displayed monodromy matrices are checked for Hermitian preservation; no numerical continuation around loops is performed. No singular nonresonant matrix is specialized to balanced weights.

The screened Section 14 Gram checks are numerical trigonometric evaluations at the fixed weights and h=π/40. They compare the planar factorization, zero principal cofactors, determinant −qε² and off-diagonal cofactor −qε. These checks do not certify matrix rank or realize a hyperbolic tetrahedron.

The JSON records Git commit and full dirty state, source/fixture/test/README and relevant chapter hashes, Python executable/version, mpmath version, precisions, conventions, residuals and elapsed time. It verifies the hashed sources did not change during the run. Dirty author evidence is distinct from a later clean-source artifact and independent review.

No full double-sine or DOZZ evaluation, spectral integration, quantum tail estimate, global Airy conclusion, arbitrary intersection engine, SnapPy call, filled-manifold construction, verified filling volume, or torsion invariant is computed here. Formal series are finite algebra. Numerical agreement is not an interval certificate, proof of convergence, or certification of the geometric inputs.
