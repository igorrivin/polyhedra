# Finite computational targets for Sections 10–11

This is a specification for a separate implementation role, not an implementation or execution claim. Use the approved source hashes in `freeze-manifest.json`. Keep exact rational or quadratic-field checks distinct from 70/110-digit floating-point comparisons. Every result must record coordinates, branches, precision, residuals, comparison formulas and evidence status. No finite run certifies an asymptotic theorem.

The shared planned implementation path is `experiments/quantum_geodesics/`; planned results are `artifacts/quantum_geodesics/result.json`, and planned execution evidence belongs under `docs/execution/final-chapters-review-2026-11-01/`. These are prospective paths, not existing companion claims. The integrator will attach actual fixture-group IDs and code/result hashes after implementation and independent execution review. Author scratch remains separate evidence.

Use the shared planned precision pair of 70 and 110 decimal digits unless a particular target has a documented reason for another setting. Record actual execution precision and any independent higher-precision oracle separately. The planned precision pair grants no execution approval.

## 1. Positive figure-eight sum

Use `eq:introfigureproduct` for N = 2,…,40 and 60,120. Compute the positive products by a logarithmic recurrence and their sum by log-sum-exp. Independently evaluate the finite Habiro–Lê expression from Murakami, Section 3.2.1, equation (3.1),

`sum_{j=0}^{N-1} product_{k=1}^{j} (q^((N-k)/2)-q^(-(N-k)/2))*(q^((N+k)/2)-q^(-(N+k)/2))`,

at `q=exp(2*pi*i/N)`, with half powers defined as `exp(pi*i*(N±k)/N)` rather than a library principal fractional power of q. Compare the complex result to the positive sum at both precisions; record imaginary residual separately. This is a useful branch check.

Check `P_(N,N-1)=N^2`, the location `floor(5*N/6)` with the adjacent tie when `6` divides N, and `P_max<=J_N<=N*P_max` with explicit precision-scaled residual policy. The proof of the maximum and its inequality is analytic in the chapter; floating-point comparisons do not establish positivity for all N. The polynomial identity `(z-1)*(1+...+z^(N-1))=z^N-1` and its value at1 may be checked with exact integer coefficients for the same finite Ns as a separate exact fixture.

Optionally report `2*pi*log(J_N)/N` beside the target `6*Lambda(pi/3)`. Obtain the target independently from the defining Lobachevsky integral and twice the Bloch–Wigner value at `exp(i*pi/3)`, using compatible branches. Do not demand monotone convergence or reinterpret finite agreement as a proof. This is not a general Jones evaluator.

## 2. Klein volume moments and dihedral curvature

The curvature is -1, coordinates are the Klein ball, and the path is exactly `r*Q`, not the fixed-conformal angle path. Use only inputs satisfying `t=r^2*R^2<1`, with a rational certified upper bound `R^2>=sup_Q|y|^2`.

For the standard simplex `Q={x,y,z>=0;x+y+z<=1}`, the exact monomial integral is

`integral_Q x^a*y^b*z^c = a!*b!*c!/(a+b+c+3)!`.

Derive radial moments by multinomial expansion for k=0,…,4. Check them independently by a Duffy substitution to the unit cube and separate one-variable beta integrals. Required initial values are `V=1/6`, `M2=1/20`, `M4=2/105`, giving `W(rQ)=r^3/6+r^5/10+2*r^7/35+...`.

Also check the centered cube `[-1,1]^3` and at least one rational translated rectangular box by direct separable monomial integration. For the cube, `V=8`, `M2=8`, `M4=152/15`, so coefficients are `8,16,152/5`. Translation changes higher moments and should be retained, not silently recentered. Verify the scalar tail identity exactly, and record the resulting nonnegative remainder bound

`r^3*V*t^(m+1)*(m+2-(m+1)*t)/(1-t)^2`.

An optional independent bounded numerical volume comparison may use the exact Klein density and the Duffy/box coordinates for three small r values. Such a quadrature comparison is numerical evidence; the displayed bound certifies only series truncation, not quadrature error. A full high-dimensional integration campaign is unnecessary.

For the same polyhedra, compute Euclidean outward face normals and support numbers from vertices. Compare the exact Lorentzian-normal cosine to the chapter coefficient

`b_e=-(h_f*h_g+cos(alpha_E)*(h_f^2+h_g^2)/2)/sin(alpha_E)`.

Use exact rational/quadratic arithmetic for the curvature sum. The simplex has three zero coefficients and three `L=sqrt(2), b=-1/(6*sqrt(2))`, so `sum L*b=-1/2=-3*V`. The cube has twelve `L=2,b=-1`, giving `-24=-3*8`. Include a translated box to catch accidental dependence of the summed first-curvature identity on the chosen Klein origin. Interior angles are used; exterior angles reverse the sign. A finite geometric fixture neither proves a regeneration theorem nor asserts global realization from angle data.

## 3. Peripheral shift and filling normalization

Prefer to reuse the already reviewed exact algebra in `experiments/quantum_surgery/` where applicable, recording that dependency. Do not relabel an old run as a fresh replay.

Use multiplier logarithms `u,v`; fixed lift signs aside, `m=exp(u/2)`, `l=exp(v/2)`, `Omega=dv wedge du/2`, `P=v/2`, and `P_hat=hbar*d/du`. A translation is by hbar, so `l_hat*m_hat=exp(hbar/2)*m_hat*l_hat`. Check this on selected polynomial/exponential test functions with explicit shift and multiplication, retaining the half-log convention.

For exact rational slope data `(p,q,rho,sigma)` with `p*sigma-q*rho=1`, include both signs of nonzero q; examples `(1,1,0,1)`, `(5,2,2,1)`, `(-3,2,-2,1)`, `(5,-2,-2,1)`. Check the matrix preserves `dv wedge du`, and differentiate the quadratic G in `eq:introfillingkernel` to recover `dG=b_core*da/2-v*du/2` after solving `v=(a-p*u)/q`. With a formal odd polynomial v and its primitive, check the stationary equation and Hessian `D/(2*q)`. These are formal identities, not geometric fillings or torsion evaluations.

Check the modulus exponent algebra for `hbar_r=4*pi*i/r`: a phase with imaginary part V has modulus `exp(r*V/(4*pi))`. The Fourier normalization is needed to reduce the Gaussian dependence to `D^(-1/2)`; no branch-independent square-root equality should be asserted.

## 4. Charge and curvature factors

Use fixed rational `0<mu_i<1`, `sum mu_i=2` and `b^2` in `(0,1)`, and check algebraically `gamma=2*b`, `beta_i=mu_i/b=2*alpha_i`, `s=(sum alpha_i-Q)/b=-1`, `gamma*sum beta_i=4`, and `Delta(b)=1`. Verify the strict first-moment inequalities in `eq:flatSeibergbounds` for a small declared set of weights. This is a check of the specialization, not construction of GMC or charge continuation.

For the first-moment integrand retain all marks finite and `d^2w=dx*dy`. The curvature factor is `-2*i*partial*barpartial log`; the WP limit is `(2/A)*omega_WP -> omega_CH` at curvature -1. Exact exterior-power factors `(2/A)^d` for d=1,2,3 are a normalization fixture, not a moduli integral evaluation.

## Numerical acceptance and conditioning

Require finite values and report the scale of every comparison. Compare positive figure-eight sums and products through logarithms or relative residuals; an absolute tolerance must not accept a tiny nonzero value as zero. Record complex imaginary residuals divided by the positive reference scale. Precision agreement alone is not an independent oracle.

Do not recover subleading Klein coefficients by subtracting nearly equal full volumes when the residual is below the working-precision budget. Those coefficients have exact rational fixtures. Use moderate r values (for example1/20,1/10,1/5 when the declared radius bound permits them) for optional full-volume checks, compare full values with scaled/relative residuals, and explicitly record both the proven geometric-series tail and the numerical quadrature tolerance. A series bound smaller than the rounding or quadrature uncertainty does not certify the residual. A separate implementation reviewer should reject such under-resolved comparisons.

## Coverage exclusions

No root-of-unity 6j evaluator is required. In particular, do not evaluate a pole and call it Costantino's pole-removed value, or use a generic rounding sequence for Chen–Murakami's refined theorem. No colored-Jones volume conjecture beyond the chapter's analytic figure-eight argument, no infinite fusion spectral tail, no Chern–Simons path integral, no arbitrary quantum thimble decomposition, no global torsion conjecture, no uniform Airy theorem, no noncompact moduli domination, and no regeneration or volume classification is certified by these checks. Section15's already reviewed exact-integrand computation and its limitations remain separate.
