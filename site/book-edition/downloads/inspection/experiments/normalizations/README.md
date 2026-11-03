# Fixed normalization checks

This companion checks finite arithmetic in [Sections 1–8](../../book/chapters/01-volume-normalization.tex) and [Appendix A](../../book/chapters/appendix-a-fricke.tex). It uses Python's standard library and exact `Fraction` values. No dependencies or package installation are needed.

From the repository root, with Python 3.10 or newer:

```sh
python experiments/normalizations/run.py --output /tmp/normalization-checks.json
python -m unittest discover -s experiments/normalizations/tests -v
```

The output path must be new and its parent directory must already exist. The driver resolves source inputs relative to its own file, works from another directory, makes no network calls, and fails with a nonzero status on a failed check. Importing the module does not run the experiment. The JSON records the actual Git commit and dirty state, source hashes, exact inputs and outputs, Python version, elapsed time, and coverage limits. Its arithmetic uses no floating point; elapsed time is a wall-clock measurement. Initial author runs with a dirty tree are development evidence, separate from the later clean-source artifact.

The fixed checks cover:

- The tetrahedral perimeter minor of determinant −2, the disintegrated factor 1/2, angle triangle, two oriented sheets, and WP multiplier 4. Base volumes distinguish the torus stack convention from its effective quotient: the sphere/torus ratios are 24 and 12, respectively.
- Strict light subsets for the pure-cone genus-zero wall class, with each boundary bipartition counted once. The large-cone example has naive volume −π²/4 and wall correction π²/2. Balanced subsets have weight exactly 1 and contribute no light-side term.
- Six flat-weight fixtures: four with n=4 and two with n=5, including a light triple whose complement is the pair boundary used as a generator. The n=5 intersection matrix has self-intersection −1, intersection 1 for disjoint pairs, and 0 for distinct overlapping pairs. Fixed auxiliary-mark representatives of ψ are checked against their independently averaged coefficients. The identities ψᵢ²=1, ψᵢψⱼ=2, κ₁ψᵢ=3, and κ₁²=5 are then recovered.
- The top intersection of the flat class compared with McMullen's independent set-partition formula, plus direct evaluations of the AMN wall class compared with the final-chamber polynomial. Coefficients use **a=A/π**, **V_WP/π^(2d)**, and **V_CH/π^d**, where d=n−3 and the CH metric has holomorphic sectional curvature −1. For five equal weights 2/5, the outputs are V_CH/π²=8/5 and V_WP/π⁴=2a²/5+a³/5+a⁴/40, with strict chamber 0<a<1.
- Three specified n=6 F-curve pairings, a symmetric qᵢⱼ=2 Gram/density conversion, a 4×4 Pfaffian, and three rational SL₂ trace/twist identities, including a degenerate trace-coordinate chart.

For flat weights μ with sum 2, the path is wᵢ=μᵢ+ε(1−μᵢ), ε=a/[2(n−2)]. It requires 0<ε≤1. Every strictly light subset further imposes ε<(1−μ_I)/(|I|−μ_I). The driver reports whether the resulting upper endpoint is strict; it does not silently include a wall or extrapolate the final polynomial past it. The equal n=4 fixture has no light subsets and permits the physical endpoint ε=1. The balanced perturbations show why the quadratic coefficient and chamber width need not approach their balanced values uniformly.

The intersection rules and external geometric theorems are mathematical inputs. These tests can catch signs, factors, factorials, complement duplication, and chamber errors in finite formulas. They do not prove those geometric inputs, a general divisor identity, or a local metric/convergence theorem. The n=6 probes do not provide a general intersection engine. The SL₂ fixtures do not assert global hyperbolic surface realization. The symmetric Gram fixture does not evaluate a full hyperideal cell integral.

The manuscript supplies the source and hypothesis audit: AMN's cone-wall formula in [Section 5](../../book/chapters/05-boundary-cone-continuation.tex), Mondello's bracket normalization in [Section 4](../../book/chapters/04-hyperideal-integrand.tex), and Koziarz–Nguyen and McMullen's compactified volume formulas and the flat-limit convention in [Section 8](../../book/chapters/08-wp-flat-limit.tex). The companion checks those explicitly stated formulas at fixed inputs; it does not fetch or verify external papers while running.
