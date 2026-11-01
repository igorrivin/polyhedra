"""Multiprecision finite period and Gram checks; none are certified bounds.

Every evaluation owns a cloned mpmath context. Euler integrals and special
function evaluations use different formulas but the same arithmetic backend.
"""

from fractions import Fraction as Q
from itertools import permutations

import mpmath

from .algebra import weights
from .exact import rational, require


def context(digits):
    if type(digits) is not int or not 40 <= digits <= 120:
        raise ValueError("this bounded companion supports 40 through 120 decimal digits")
    ctx = mpmath.mp.clone()
    ctx.dps = digits
    return ctx


def mpq(ctx, value):
    if not isinstance(value, Q):
        raise ValueError("multiprecision rational inputs must remain exact Fraction values")
    return ctx.mpf(value.numerator)/value.denominator


def point(ctx, values):
    if not isinstance(values, (list, tuple)) or len(values) != 2:
        raise ValueError("z must have rational-string real and imaginary parts")
    x, y = (rational(s) for s in values)
    if y == 0 and (x <= 0 or x >= 1):
        raise ValueError("z must avoid (-infinity,0] and [1,infinity)")
    return ctx.mpc(mpq(ctx, x), mpq(ctx, y))


def delta(mu):
    return 1-mu[0]-mu[2], 1-mu[1]-mu[2], 1-mu[2]-mu[3]


def s_basis(ctx, mu, z, *, differentiated=False):
    """The s basis only requires delta0!=0; the t basis is a separate chart."""
    if delta(mu)[0] == 0:
        raise ValueError("the s basis is resonant; use the separate logarithmic basis")
    m1, m2, m3, m4 = [mpq(ctx, x) for x in mu]
    d0 = mpq(ctx, delta(mu)[0])
    f0 = ctx.hyp2f1(1-m4, m3, m1+m3, z)
    inner = ctx.hyp2f1(m2, 1-m1, 1+d0, z)
    f1 = z**d0*inner
    if not differentiated:
        return ctx.matrix([f0, f1])
    f0prime = (1-m4)*m3/(m1+m3)*ctx.hyp2f1(2-m4, 1+m3, 1+m1+m3, z)
    f1prime = z**d0*(d0*inner/z+m2*(1-m1)/(1+d0)*ctx.hyp2f1(1+m2, 2-m1, 2+d0, z))
    return ctx.matrix([f0, f1]), ctx.matrix([f0prime, f1prime])


def t_basis(ctx, mu, z):
    swapped = (mu[1], mu[0], mu[2], mu[3])
    return s_basis(ctx, swapped, 1-z)


def fusion(ctx, mu):
    d0, d1, _ = delta(mu)
    if d0 == 0 or d1 == 0:
        raise ValueError("the nonresonant connection matrix needs delta0,delta1!=0")
    m1, m2, m3, m4 = [mpq(ctx, x) for x in mu]
    d0, d1 = mpq(ctx, d0), mpq(ctx, d1)
    G = ctx.gamma
    return ctx.matrix([[G(1-d0)*G(d1)/(G(m1)*G(1-m2)),
                        G(1-d0)*G(-d1)/(G(m3)*G(1-m4))],
                       [G(1+d0)*G(d1)/(G(1-m3)*G(m4)),
                        G(1+d0)*G(-d1)/(G(1-m1)*G(m2))]])


def gamma_ratio(ctx, x):
    return ctx.gamma(x)/ctx.gamma(1-x)


def s_hermitian(ctx, mu):
    d0 = delta(mu)[0]
    if d0 == 0:
        raise ValueError("the diagonal s form is singular at delta0=0")
    m1, m2, m3, m4 = [mpq(ctx, x) for x in mu]
    d0 = mpq(ctx, d0)
    def gr(value):
        return gamma_ratio(ctx, value)

    return ctx.diag([ctx.pi*gr(d0)/(gr(m2)*gr(m4)),
                     ctx.pi*gr(-d0)/(gr(m1)*gr(m3))])


def euler_integral(ctx, alpha, beta, gamma, z):
    """Integrate t^-alpha(1-t)^-beta(1-z*t)^-gamma, with smoothed endpoints.

    Split at 1/2. Substitute t=x^d/2 on the left and t=1-x^d/2
    on the right, using the respective rational endpoint denominator d.
    Combining the Jacobian analytically gives x^[d(1-weight)-1], a
    nonnegative integer power, including a finite value at x=0.
    """
    if any(not isinstance(w, Q) or not 0 < w < 1 for w in (alpha, beta, gamma)):
        raise ValueError("Euler endpoint exponents must be exact fractions in (0,1)")
    a, b, c = [mpq(ctx, value) for value in (alpha, beta, gamma)]
    dl, dr = alpha.denominator, beta.denominator
    el, er = dl*(1-alpha)-1, dr*(1-beta)-1
    require(el.denominator == er.denominator == 1 and el >= 0 and er >= 0,
            "endpoint substitutions did not remove singular powers")

    def left(x):
        t = x**dl/2
        return dl*ctx.power(2, a-1)*x**int(el)*(1-t)**(-b)*(1-z*t)**(-c)

    def right(x):
        distance = x**dr/2
        return dr*ctx.power(2, b-1)*x**int(er)*(1-distance)**(-a)*(1-z+z*distance)**(-c)

    return ctx.quad(left, [0, 1], method="tanh-sinh")+ctx.quad(right, [0, 1], method="tanh-sinh")


def euler_s(ctx, mu, z):
    m1, m2, m3, m4 = mu
    arc0 = euler_integral(ctx, m4, m2, m3, z)
    arc1 = z**mpq(ctx, delta(mu)[0])*euler_integral(ctx, m1, m3, m2, z)
    beta0 = ctx.beta(mpq(ctx, 1-m2), mpq(ctx, 1-m4))
    beta1 = ctx.beta(mpq(ctx, 1-m1), mpq(ctx, 1-m3))
    return ctx.matrix([arc0, arc1]), ctx.diag([beta0, beta1])


def norm(ctx, value):
    entries = list(value) if hasattr(value, "rows") else [value]
    require(all(ctx.isfinite(entry) for entry in entries),
            "numerical norm contains a nonfinite entry")
    return max([abs(entry) for entry in entries]+[ctx.mpf(0)])


def packed(ctx, value):
    return {"real": ctx.nstr(ctx.re(value), ctx.dps, strip_zeros=False),
            "imag": ctx.nstr(ctx.im(value), ctx.dps, strip_zeros=False)}


class NumericChecks:
    def __init__(self, ctx):
        self.ctx = ctx
        self.tolerance = ctx.power(10, -(ctx.dps-15))
        self.residuals = {}

    def close(self, name, actual, expected):
        ctx = self.ctx
        actual_norm = norm(ctx, actual)
        expected_norm = norm(ctx, expected)
        residual = norm(ctx, actual-expected)/max(ctx.mpf(1), actual_norm, expected_norm)
        require(ctx.isfinite(residual) and residual <= self.tolerance,
                f"numerical check failed: {name}, scaled residual {residual}, tolerance {self.tolerance}")
        self.residuals[name] = ctx.nstr(residual, 12)

    def result(self, **values):
        ctx = self.ctx
        worst = max((ctx.mpf(x) for x in self.residuals.values()), default=ctx.mpf(0))
        return {"status": "numerical agreement, not certified", "decimal_digits": ctx.dps,
                "scaled_tolerance": ctx.nstr(self.tolerance, 12),
                "residual_scaling": "abs(actual-expected)/max(1,abs(actual),abs(expected)); matrix max-entry norm",
                "check_count": len(self.residuals), "max_scaled_residual": ctx.nstr(worst, 12),
                "scaled_residuals": self.residuals, **values}


def period_check(row, zs, digits):
    ctx = context(digits)
    checks = NumericChecks(ctx)
    mu = weights(row["mu"], nonresonant=True)
    z = point(ctx, zs)
    d0, d1, di = delta(mu)
    f, fp = s_basis(ctx, mu, z, differentiated=True)
    g = t_basis(ctx, mu, z)
    M = fusion(ctx, mu)
    Hs = s_hermitian(ctx, mu)
    Ht = s_hermitian(ctx, (mu[1], mu[0], mu[2], mu[3]))
    checks.close("hypergeometric-fusion", f, M*g)
    checks.close("connection-determinant", ctx.det(M), mpq(ctx, -d0/d1))
    checks.close("Hermitian-congruence", M.H*Hs*M, Ht)
    require(Hs[0, 0]*Hs[1, 1] < 0, "Hermitian signature is not (1,1)")
    S, Bs = euler_s(ctx, mu, z)
    T, Bt = euler_s(ctx, (mu[1], mu[0], mu[2], mu[3]), 1-z)
    checks.close("independent-s-Euler-arcs", S, Bs*f)
    checks.close("independent-t-Euler-arcs", T, Bt*g)
    def sin(weight):
        return ctx.sin(ctx.pi*mpq(ctx, weight))

    Msine = ctx.matrix([[sin(mu[0]), -sin(mu[2])], [sin(mu[3]), -sin(mu[1])]])/sin(d1)
    checks.close("sine-arc-connection", S, Msine*T)
    checks.close("beta-normalization-of-fusion", Bs*M, Msine*Bt)
    area = ctx.re((f.H*Hs*f)[0])
    area_t = ctx.re((g.H*Ht*g)[0])
    area_arc = (sin(mu[1])*sin(mu[3])*abs(S[0])**2-sin(mu[0])*sin(mu[2])*abs(S[1])**2)/sin(d0)
    require(area > 0, "screened area must be positive at the fixed point")
    checks.close("area-channel-invariance", area, area_t)
    checks.close("Euler-area-normalization", area, area_arc)
    W = f[0]*fp[1]-fp[0]*f[1]
    expected_W = mpq(ctx, d0)*z**(-mpq(ctx, mu[0]+mu[2]))*(1-z)**(-mpq(ctx, mu[1]+mu[2]))
    checks.close("Wronskian", W, expected_W)
    checks.close("period-derivative", fp, ctx.matrix([ctx.diff(lambda zz: s_basis(ctx, mu, zz)[i], z)
                                                     for i in range(2)]))
    gamma_product = ctx.fprod(gamma_ratio(ctx, mpq(ctx, m)) for m in mu)
    checks.close("density-scalar", -Hs[0, 0]*Hs[1, 1]*mpq(ctx, d0)**2, ctx.pi**2/gamma_product)
    density = 4*ctx.pi**2/gamma_product*abs(z)**(-2*mpq(ctx, mu[0]+mu[2]))*abs(1-z)**(-2*mpq(ctx, mu[1]+mu[2]))/area**2
    area_z = (f.H*Hs*fp)[0]
    area_zbarz = ctx.re((fp.H*Hs*fp)[0])
    density_derivative = 4*(abs(area_z)**2/area**2-area_zbarz/area)
    checks.close("density-from-Hermitian-derivatives", density_derivative, density)
    require(density > 0, "density sign failed")
    volume_over_pi = 2*(1-abs(d0)-abs(d1)-abs(di))
    require(volume_over_pi == 4*min((*mu, *(1-w for w in mu))), "exact four-point volume factor failed")
    observables = {"f0": packed(ctx, f[0]), "f1": packed(ctx, f[1]),
                   "g0": packed(ctx, g[0]), "g1": packed(ctx, g[1]),
                   "S0": packed(ctx, S[0]), "S1": packed(ctx, S[1]),
                   "T0": packed(ctx, T[0]), "T1": packed(ctx, T[1]),
                   "area": packed(ctx, area), "density": packed(ctx, density)}
    return checks.result(id=row["id"], mu=row["mu"], z=zs, delta0=str(d0), delta1=str(d1),
                         volume_over_pi=str(volume_over_pi), observables=observables,
                         quadrature="Independent beta-weight Euler arcs, endpoint-denominator substitutions, mpmath tanh-sinh")


def logarithmic_series(ctx, z, terms):
    """Finite Frobenius series. A two-truncation difference is not a tail bound."""
    coefficient, hn, h2n, zpower = ctx.mpf(1), ctx.mpf(0), ctx.mpf(0), ctx.mpc(1)
    total = ctx.mpc(0)
    for n in range(1, terms+1):
        coefficient *= ((ctx.mpf(n)-ctx.mpf("0.5"))/n)**2
        hn += ctx.mpf(1)/n
        h2n += ctx.mpf(1)/(2*n-1)+ctx.mpf(1)/(2*n)
        zpower *= z
        total += 4*coefficient*(h2n-hn)*zpower
    return ctx.hyp2f1(ctx.mpf("0.5"), ctx.mpf("0.5"), 1, z)*ctx.log(z)+total


def balanced_check(zs, digits):
    ctx = context(digits)
    checks = NumericChecks(ctx)
    z = point(ctx, zs)
    require(abs(z) < ctx.mpf("0.4"), "the fixed Frobenius series probe requires |z|<0.4")
    half = ctx.mpf("0.5")
    f, g = (ctx.hyp2f1(half, half, 1, zz) for zz in (z, 1-z))
    K, Kc = ctx.ellipk(z), ctx.ellipk(1-z)
    checks.close("elliptic-f", f, 2*K/ctx.pi)
    checks.close("elliptic-g", g, 2*Kc/ctx.pi)
    beta = ctx.beta(half, half)
    checks.close("balanced-Euler-f", euler_integral(ctx, Q(1, 2), Q(1, 2), Q(1, 2), z), beta*f)
    checks.close("balanced-Euler-g", euler_integral(ctx, Q(1, 2), Q(1, 2), Q(1, 2), 1-z), beta*g)
    L = ctx.log(16)
    ell0, ell1 = L*f-ctx.pi*g, L*g-ctx.pi*f
    terms = 2*digits+20
    short = logarithmic_series(ctx, z, terms)
    long = logarithmic_series(ctx, z, 2*terms)
    checks.close("balanced-logarithmic-Frobenius-series", long, ell0)
    checks.close("balanced-series-two-truncations", short, long)
    M = ctx.matrix([[L, -1], [L*L-ctx.pi**2, -L]])/ctx.pi
    H = ctx.matrix([[2*ctx.pi*L, -ctx.pi], [-ctx.pi, 0]])
    checks.close("balanced-logarithmic-fusion", ctx.matrix([f, ell0]), M*ctx.matrix([g, ell1]))
    checks.close("balanced-fusion-square", M*M, ctx.eye(2))
    checks.close("balanced-fusion-determinant", ctx.det(M), -1)
    checks.close("balanced-Hermitian-congruence", M.T*H*M, H)
    area = 2*ctx.pi**2*ctx.re(f*ctx.conj(g))
    checks.close("balanced-elliptic-area", area, 8*ctx.re(ctx.conj(K)*Kc))
    checks.close("balanced-logarithmic-area", area, ctx.re((ctx.matrix([f, ell0]).H*H*ctx.matrix([f, ell0]))[0]))
    fp = ctx.hyp2f1(half+1, half+1, 2, z)/4
    gp = -ctx.hyp2f1(half+1, half+1, 2, 1-z)/4
    checks.close("balanced-Wronskian", f*gp-fp*g, -1/(ctx.pi*z*(1-z)))
    tau = ctx.j*Kc/K
    tauprime = -ctx.j*ctx.pi/(4*z*(1-z)*K*K)
    checks.close("balanced-tau-derivative", ctx.diff(lambda zz: ctx.j*ctx.ellipk(1-zz)/ctx.ellipk(zz), z), tauprime)
    require(area > 0 and ctx.im(tau) > 0, "balanced area or upper half-plane sign failed")
    density = 4*ctx.pi**2/(abs(z*(1-z))**2*area**2)
    checks.close("balanced-Poincare-density", density, abs(tauprime)**2/ctx.im(tau)**2)
    Hfg = ctx.matrix([[0, ctx.pi**2], [ctx.pi**2, 0]])
    for index, monodromy in enumerate((ctx.matrix([[1, 0], [-2*ctx.j, 1]]),
                                       ctx.matrix([[1, -2*ctx.j], [0, 1]]))):
        checks.close(f"balanced-monodromy-Hermitian-{index}", monodromy.H*Hfg*monodromy, Hfg)
    return checks.result(z=zs, terms=[terms, 2*terms],
                         truncation_note="Observed difference of two finite sums, not a certified tail bound",
                         observables={"f": packed(ctx, f), "g": packed(ctx, g), "ell0": packed(ctx, ell0),
                                      "area": packed(ctx, area), "density": packed(ctx, density), "tau": packed(ctx, tau)},
                         basis="Separate balanced logarithmic/elliptic basis; no singular nonresonant substitution")


def numerical_determinant(ctx, matrix):
    n = matrix.rows
    terms = []
    for p in permutations(range(n)):
        sign = (-1)**sum(p[i] > p[j] for i in range(n) for j in range(i+1, n))
        terms.append(sign*ctx.fprod(matrix[i, p[i]] for i in range(n)))
    return ctx.fsum(terms)


def cofactor(ctx, matrix, row, col):
    minor = ctx.matrix([[matrix[i, j] for j in range(matrix.cols) if j != col]
                        for i in range(matrix.rows) if i != row])
    return (-1)**(row+col)*numerical_determinant(ctx, minor)


def gram_check(row, h_over_pi, digits):
    ctx = context(digits)
    checks = NumericChecks(ctx)
    mu = weights(row["mu"])
    t1, t2, t3, t4 = [ctx.pi*mpq(ctx, x) for x in mu]
    h = ctx.pi*mpq(ctx, rational(h_over_pi))
    if not 0 < h < min(t1, t2, t3, t4)/2:
        raise ValueError("the fixed Gram probe requires a small positive h")
    cos = ctx.cos

    def gram(j, k, shift):
        return ctx.matrix([[1, cos(t2+t3+k*shift), cos(t2), cos(t4-shift)],
                           [cos(t2+t3+k*shift), 1, cos(t3), cos(t1)],
                           [cos(t2), cos(t3), 1, cos(t1+t3+j*shift)],
                           [cos(t4-shift), cos(t1), cos(t1+t3+j*shift), 1]])

    phi = [0, t2+t3, t2, t1+t2+t3]
    planar = ctx.matrix([[cos(a-b) for b in phi] for a in phi])
    checks.close("screened-planar-Gram", gram(0, 0, 0), planar)
    coordinates = ctx.matrix([[ctx.cos(a), ctx.sin(a)] for a in phi])
    checks.close("screened-two-dimensional-factorization", planar, coordinates*coordinates.T)
    checks.close("screened-rank2-determinant", numerical_determinant(ctx, planar), 0)
    require(ctx.sin(t2)**2 > 0, "rank2 witness vanishes")
    table = [((0, 0), (0, 3), cos(t4-h)-cos(t4), ctx.sin(t3)**2),
             ((0, 1), (0, 2), cos(t2)-cos(t2+h), ctx.sin(t1)**2),
             ((1, 0), (1, 3), cos(t1)-cos(t1+h), ctx.sin(t2)**2),
             ((1, 1), (1, 2), cos(t3)-cos(t3+h), ctx.sin(t4-h)**2)]
    determinants = []
    for (j, k), (r, c), epsilon, factor in table:
        matrix = gram(j, k, h)
        prefix = f"screened-{j}{k}"
        checks.close(prefix+"-zero-principal-1", cofactor(ctx, matrix, j, j), 0)
        checks.close(prefix+"-zero-principal-2", cofactor(ctx, matrix, 3-k, 3-k), 0)
        det = numerical_determinant(ctx, matrix)
        checks.close(prefix+"-determinant", det, -factor*epsilon**2)
        checks.close(prefix+"-off-diagonal-cofactor", cofactor(ctx, matrix, r, c), -factor*epsilon)
        require(epsilon > 0 and det < 0 and cofactor(ctx, matrix, r, c) < 0,
                "finite screened Gram signs failed")
        determinants.append(packed(ctx, det))
    return checks.result(id=row["id"], mu=row["mu"], h_over_pi=h_over_pi, determinants=determinants,
                         scope="Numerical fixed trigonometric identities; no tetrahedron realization or rank certification")


def precision_comparison(low, high):
    if high["decimal_digits"] <= low["decimal_digits"]:
        raise ValueError("precision comparison needs strictly increasing precision")
    if low.get("id") != high.get("id") or low.get("mu") != high.get("mu") or low["z"] != high["z"]:
        raise ValueError("precision comparison must use the same fixture and point")
    if low["observables"].keys() != high["observables"].keys():
        raise ValueError("precision comparison must use the same observables")
    ctx = context(high["decimal_digits"])
    checks = NumericChecks(ctx)
    checks.tolerance = ctx.power(10, -(low["decimal_digits"]-15))
    for name, before in low["observables"].items():
        after = high["observables"][name]
        checks.close(name, ctx.mpc(before["real"], before["imag"]), ctx.mpc(after["real"], after["imag"]))
    return checks.result(precisions=[low["decimal_digits"], high["decimal_digits"]],
                         interpretation="Observed agreement of serialized independent precision runs; not a rigorous error bound")
