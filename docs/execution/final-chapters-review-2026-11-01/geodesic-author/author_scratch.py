"""Finite author checks, not the maintained or independently reviewed companion.

All writes are confined to this outer evidence directory. Exact assertions are
finite symbolic algebra; mpmath comparisons are floating, never enclosures.
"""
from pathlib import Path
import hashlib
import json
import platform

import mpmath as mp
import sympy as sp

HERE = Path(__file__).resolve().parent
exact = []


def eq(group, name, value):
    residual = sp.factor(value)
    assert residual == 0, (group, name, residual)
    exact.append({"group": group, "name": name, "residual": "0"})


# G2: independent rational determinant-one matrices.
for k in range(1, 7):
    A = sp.Matrix([[1, k], [k, 1 + k*k]])
    B = (-1 if k % 2 else 1)*sp.Matrix([[1 + 2*k, k], [2, 1]])
    eq("G2", f"trace_identity_{k}", sp.trace(A*B.inv())-
       sp.trace(A)*sp.trace(B)+sp.trace(A*B))
a, b = sp.symbols("a b")
u, v = 2*a+b, a+2*b
eq("G2", "paired_inverse_a", (2*u-v)/3-a)
eq("G2", "paired_inverse_b", (2*v-u)/3-b)

# G3: finite coefficient telescoping is exact and independent of h evaluation.
for n in (1, 2, 4, 12, 40, 180):
    hs = sp.symbols(f"h0:{n+1}")
    fn = sum((-1)**j*sp.Rational(1, 2**(j+1))*hs[j] for j in range(n))
    shifted = sum((-1)**j*sp.Rational(1, 2**(j+1))*hs[j+1] for j in range(n))
    eq("G3", f"finite_coefficients_N{n}",
       2*fn+shifted-hs[0]-(-1)**(n-1)*sp.Rational(1, 2**n)*hs[n])

# G4: exponent coordinates impose all hyperbolic relations exactly.
r, U, V = sp.symbols("r U V", positive=True)
C, sd = (r+1/r)/2, (r-1/r)/2
cu, su, cv, sv = (U+1/U)/2, (U-1/U)/2, (V+1/V)/2, (V-1/V)/2
z = C*cu*cv-su*sv
zu, zv = U*sp.diff(z, U), V*sp.diff(z, V)
zuu, zuv = U*sp.diff(zu, U), V*sp.diff(zu, V)
eq("G4", "z_uu", zuu-z)
eq("G4", "diagonal_numerator", z*z-zu*zu-1-sd*sd*cv*cv)
eq("G4", "mixed_numerator", zuv*(z*z-1)-z*zu*zv+sd*sd*cu*cv)
eq("G4", "hessian_determinant_numerator",
   (z*cv*cv)*(z*cu*cu)-(cu*cv)**2-(z*z-1)*cu*cu*cv*cv)

# G5: symbolic commutator from independent matrices.
x, w, AA, k = sp.symbols("x w AA k", nonzero=True)
M = sp.diag(x, 1/x)
B0 = sp.Matrix([[AA, k], [k, AA]])
B = sp.diag(w, 1/w)*B0
B_inv = sp.Matrix([[AA, -k], [-k, AA]])*sp.diag(1/w, w)
comm = sp.trace(M*B*M.inv()*B_inv)
eq("G5", "torus_commutator", comm-(2*(AA*AA-k*k)-(x-1/x)**2*k*k))
eq("G5", "torus_trace", sp.trace(B)-AA*(w+1/w))

# G7: finite tanh coefficients and a different compact-support density.
for n in (0, 1, 4, 12, 50):
    ts = sp.symbols(f"T0:{2*n+2}")
    eq("G7", f"finite_tanh_coefficients_N{n}",
       sum((ts[j+1]-ts[j])/2 for j in range(2*n+1))-(ts[-1]-ts[0])/2)
for aa in (sp.Rational(1, 3), sp.Rational(2), sp.Rational(5, 2)):
    for tt in (0, aa/2, -aa/2, aa/3):
        masses = []
        for n in range(-20, 21):
            low, high = tt+n*aa-aa/2, tt+n*aa+aa/2
            masses.append(max(sp.Rational(0), min(high, 1)-max(low, -1))/2)
        eq("G7", f"uniform_density_{aa}_{tt}", sum(masses)-1)

# G8: endpoint positions alone, including an inconsistent spacing.
circ = sp.Rational(5)
xs = [sp.Rational(0), sp.Rational(1), sp.Rational(3)]
ys = [sp.Rational(2), sp.Rational(3), sp.Rational(0)]
assert all((yy-xx-2) % circ == 0 for xx, yy in zip(xs, ys))
bad = [sp.Rational(2), sp.Rational(3), sp.Rational(1)]
assert any((yy-xx-2) % circ != 0 for xx, yy in zip(xs, bad))
exact.append({"group": "G8", "name": "matching_and_failed_spacing", "residual": "exact predicates"})

# G9: signed cusp lifts and decorated triangle identities.
for q in (1, 2, 3):
    for ta, tb in ((2, 2), (2, 5), (3, 5), (5, 3)):
        cc = sp.Rational(ta+tb, q)
        top = sp.Rational(ta, 2)
        A = sp.Matrix([[top, (top*top-1)/cc], [cc, top]])
        P = sp.Matrix([[1, q], [0, 1]])
        BB = A.inv()*P
        eq("G9", f"cusp_det_{q}_{ta}_{tb}", A.det()-1)
        eq("G9", f"cusp_traceB_{q}_{ta}_{tb}", sp.trace(BB)+tb)
        eq("G9", f"cusp_qc_{q}_{ta}_{tb}", q*cc-ta-tb)
for uu, vv, ww in ((1, 1, 1), (1, 2, 3), (2, 3, 5)):
    uu, vv, ww = map(sp.Rational, (uu, vv, ww))
    hh = 2*(uu*uu+vv*vv+ww*ww)/(uu*vv*ww)
    xx, yy, zz = hh*uu/2, hh*vv/2, hh*ww/2
    eq("G9", f"markov_{uu}_{vv}_{ww}", xx*xx+yy*yy+zz*zz-xx*yy*zz)
    uf = (vv*vv+ww*ww)/uu
    eq("G9", f"flip_H_{uu}_{vv}_{ww}", 2*(uf*uf+vv*vv+ww*ww)/(uf*vv*ww)-hh)


def run_numeric(dps):
    mp.mp.dps = dps
    groups = {f"G{i}": {"comparisons": 0, "max_scaled_residual": mp.mpf(0)} for i in range(1, 11)}
    notes = []
    tolerance = mp.power(10, -(dps-15))

    def close(g, actual, expected, relative=False):
        scale = abs(expected) if relative else max(mp.mpf(1), abs(expected))
        assert scale > 0
        res = abs(actual-expected)/scale
        assert res < tolerance, (g, dps, mp.nstr(res, 8), mp.nstr(tolerance, 8))
        groups[g]["comparisons"] += 1
        groups[g]["max_scaled_residual"] = max(groups[g]["max_scaled_residual"], res)

    def h(t):
        return (4/(t*t))/(1+mp.sqrt(1-4/(t*t)))

    def D(d, u, v):
        return mp.acosh(mp.cosh(d)*mp.cosh(u)*mp.cosh(v)-mp.sinh(u)*mp.sinh(v))

    def grad(d, u, v):
        z = mp.cosh(d)*mp.cosh(u)*mp.cosh(v)-mp.sinh(u)*mp.sinh(v)
        ss = mp.sqrt(z*z-1)
        return ((mp.cosh(d)*mp.sinh(u)*mp.cosh(v)-mp.cosh(u)*mp.sinh(v))/ss,
                (mp.cosh(d)*mp.cosh(u)*mp.sinh(v)-mp.sinh(u)*mp.cosh(v))/ss)

    # G1 finite integral compared with a known value plus its analytic tail.
    I = mp.pi**2/12
    for R in (12, 30, 60):
        val = mp.quad(lambda xx: xx*mp.exp(-xx)/(1+mp.exp(-xx)), [0, 1, R])
        tail = (R+1)*mp.exp(-R)
        assert -tolerance <= I-val <= tail+tolerance
        groups["G1"]["comparisons"] += 1
    M = 1000
    alt = mp.fsum((-1)**(j-1)/mp.mpf(j*j) for j in range(1, M+1))
    assert 0 < I-alt < mp.mpf(1)/(M+1)**2
    groups["G1"]["comparisons"] += 1

    # G3 separate cancellation-limited residual and retained positive bound.
    for x0 in ("6.00000000000000000001", "6.01", "7", "9", "11", "30", "1000"):
        for n in (4, 12, 40, 180):
            xx = mp.mpf(x0)
            hs = []
            for j in range(n+1):
                hs.append(h(xx/3))
                xx = xx*xx/9+2
            fn = mp.fsum((-1)**j*mp.power(2, -j-1)*hs[j] for j in range(n))
            shifted = mp.fsum((-1)**j*mp.power(2, -j-1)*hs[j+1] for j in range(n))
            rhs = (-1)**(n-1)*mp.power(2, -n)*hs[n]
            bound = mp.power(2, -n-1)*hs[n]
            lhs = 2*fn+shifted-hs[0]
            close("G3", lhs, rhs)
            assert bound > 0
            assert hs[0]/4-bound-tolerance <= fn <= hs[0]/2+bound+tolerance
            cancellation = abs(rhs) < tolerance*hs[0]
            if x0 in ("6.00000000000000000001", "1000") and n == 180:
                notes.append({"group": "G3", "x": x0, "N": n,
                    "log_bound": mp.nstr(mp.log(bound), 18),
                    "positive_bound_retained": bool(bound > 0),
                    "cancellation_limited": bool(cancellation),
                    "finite_residual_verification": "exact coefficient identity plus floating absolute comparison"})
    for tt in (mp.mpf(10), mp.mpf("1e100"), mp.exp(1000)):
        scaled = tt*tt*h(tt)
        assert 2-tolerance <= scaled <= 4+tolerance
        groups["G3"]["comparisons"] += 1

    # G4 independent numerical derivatives of the Lorentz-distance formula.
    for dd in map(mp.mpf, (".03", ".5", "2", "7")):
        for uu, vv in ((0, 0), (1, -2), (-3, 2), (mp.mpf(".1"), mp.mpf(".2")), (4, 4)):
            gg = grad(dd, uu, vv)
            close("G4", mp.diff(lambda w: D(dd, w, vv), uu), gg[0])
            close("G4", mp.diff(lambda w: D(dd, uu, w), vv), gg[1])
            zz = mp.cosh(D(dd, uu, vv))
            ss = mp.sqrt(zz*zz-1)
            fac = mp.sinh(dd)**2/ss**3
            h11, h12, h22 = fac*zz*mp.cosh(vv)**2, -fac*mp.cosh(uu)*mp.cosh(vv), fac*zz*mp.cosh(uu)**2
            close("G4", mp.diff(lambda w: D(dd, w, vv), uu, 2), h11)
            close("G4", mp.diff(lambda w: grad(dd, uu, w)[0], vv), h12)
            close("G4", h11*h22-h12*h12, mp.sinh(dd)**4*mp.cosh(uu)**2*mp.cosh(vv)**2/ss**4)
            assert h11 > 0 and h11*h22-h12*h12 > 0

    # G5 seam and torus matrices, length derivatives calculated from matrices.
    for af, bf, cf in ((".2", ".7", "0"), ("1", "1", "0"), ("1", "2", "3"), ("8", ".5", "4")):
        aa, bb, cc = map(mp.mpf, (af, bf, cf))
        dd = mp.acosh((mp.cosh(cc/2)+mp.cosh(aa/2)*mp.cosh(bb/2))/(mp.sinh(aa/2)*mp.sinh(bb/2)))
        X = mp.matrix([[mp.exp(aa/2), 0], [0, mp.exp(-aa/2)]])
        J = mp.matrix([[mp.cosh(dd/2), mp.sinh(dd/2)], [mp.sinh(dd/2), mp.cosh(dd/2)]])
        Y = J*mp.matrix([[mp.exp(-bb/2), 0], [0, mp.exp(bb/2)]])*J**-1
        XY = X*Y
        close("G5", XY[0, 0]+XY[1, 1], -2*mp.cosh(cc/2))
    for aa, bb in ((mp.mpf(".2"), mp.mpf(0)), (mp.mpf(1), mp.mpf(".7")), (mp.mpf(3), mp.mpf(4))):
        A = mp.sqrt((mp.cosh(aa)+mp.cosh(bb/2))/(mp.cosh(aa)-1))
        X = mp.matrix([[mp.exp(aa/2), 0], [0, mp.exp(-aa/2)]])
        B0 = mp.matrix([[A, mp.sqrt(A*A-1)], [mp.sqrt(A*A-1), A]])

        def matB(uu):
            return mp.matrix([[mp.exp(uu/2), 0], [0, mp.exp(-uu/2)]])*B0

        def ell(uu):
            B = matB(uu)
            return 2*mp.acosh((B[0, 0]+B[1, 1])/2)

        for uu in map(mp.mpf, ("-4", "-.5", "0", ".5", "4")):
            B = matB(uu)
            comm = X*B*X**-1*B**-1
            close("G5", comm[0, 0]+comm[1, 1], -2*mp.cosh(bb/2))
            Q = A*A*mp.cosh(uu/2)**2-1
            lp = A*mp.sinh(uu/2)/mp.sqrt(Q)
            lpp = A*(A*A-1)*mp.cosh(uu/2)/(2*Q**mp.mpf("1.5"))
            close("G5", mp.diff(ell, uu), lp)
            close("G5", mp.diff(ell, uu, 2), lpp)
            assert abs(lp) < 1 and lpp > 0

    # G6 finite quadratures with separate analytic tails, using y coarea.
    A = mp.mpf("1.7")
    for ss in (mp.mpf(".5"), mp.mpf(2), mp.mpf(3)):
        for UU in (12, 30):
            lhs = 2*mp.quad(lambda uu: (A*mp.cosh(uu/2))**(-ss), [0, 1, UU])
            ymax = A*mp.sinh(mp.mpf(UU)/2)
            points = [mp.mpf(0), A]
            yy = 10*A
            while yy < ymax:
                points.append(yy)
                yy *= 10
            points.append(ymax)
            rhs = mp.quad(lambda yy: 4*(A*A+yy*yy)**(-(ss+1)/2), points)
            close("G6", lhs, rhs)
            total = 2*mp.sqrt(mp.pi)*mp.gamma(ss/2)/(A**ss*mp.gamma((ss+1)/2))
            tail = mp.power(2, ss+2)/(ss*A**ss)*mp.exp(-ss*UU/2)
            assert -tolerance <= total-lhs <= tail+tolerance
            if ss == 2:
                close("G6", lhs, 4*mp.tanh(mp.mpf(UU)/2)/(A*A))

    # G7 positive tiny terms and tails, without cancellation-based acceptance.
    for aa in map(mp.mpf, (".1", ".7", "2", "7")):
        for uu in map(mp.mpf, (".2", "3", "100", "1000")):
            qq = mp.exp(-abs(uu))
            stable = 2*mp.sinh(aa/2)*qq/(1+2*mp.cosh(aa/2)*qq+qq*qq)
            direct = mp.sinh(aa/2)/(mp.cosh(uu)+mp.cosh(aa/2))
            close("G7", stable, direct, relative=True)
            assert stable > 0
        tt = mp.mpf(".37")*aa
        for nn in (0, 1, 4, 12, 50):
            partial = mp.fsum(mp.sinh(aa/2)/(mp.cosh(tt+j*aa)+mp.cosh(aa/2)) for j in range(-nn, nn+1))
            LL = (mp.mpf(nn)+mp.mpf(".5"))*aa
            closed = (mp.tanh((tt+LL)/2)-mp.tanh((tt-LL)/2))/2
            close("G7", partial, closed)
            logistic = sum(mp.exp(-zz)/(1+mp.exp(-zz)) for zz in (LL+tt, LL-tt))
            assert 0 < logistic <= 2*mp.cosh(tt)*mp.exp(-LL)*(1+tolerance)
    LL, tt = mp.mpf(1001), mp.mpf(".37")
    tail = sum(mp.exp(-zz)/(1+mp.exp(-zz)) for zz in (LL+tt, LL-tt))
    rounded_tail = 1-(mp.tanh((tt+LL)/2)-mp.tanh((tt-LL)/2))/2
    assert tail > 0 and rounded_tail == 0
    notes.append({"group": "G7", "L": "1001", "positive_tail": mp.nstr(tail, 18),
                  "rounded_subtractive_tail": "0", "status": "subtractive route rejected"})

    # G8 position matching alone need not make the action stationary.
    d1, d2, tau = mp.mpf(".5"), mp.mpf("1.2"), mp.mpf(".4")
    for vv in (mp.mpf(0), mp.mpf(1)):
        action = lambda xx: D(d1, 0, xx)+D(d2, xx+tau, vv)
        analytic = grad(d1, 0, 0)[1]+grad(d2, tau, vv)[0]
        close("G8", mp.diff(action, 0), analytic)
    assert abs(mp.diff(lambda xx: D(d1, 0, xx)+D(d2, xx, 1), 0)) > mp.mpf(".1")

    # G9 signed truncation and decoration invariance.
    for tt in map(mp.mpf, (3, 4, 5, 10)):
        for HH in map(mp.mpf, (".1", "1", "6", "20")):
            dd = 2*mp.log(2*tt/HH)
            weight = 1-mp.sqrt(1-16*mp.exp(-dd)/(HH*HH))
            close("G9", weight, h(tt), relative=True)
            kscale = mp.mpf(3)
            close("G9", mp.exp(-(dd-2*mp.log(kscale)))/(kscale*HH)**2,
                  mp.exp(-dd)/(HH*HH), relative=True)
    assert 2*mp.log(mp.mpf(6)/20) < 0

    # G10 independent circle data, then stable tiny-positive checks.
    for dd in map(mp.mpf, (".1", ".7", "2", "8")):
        center, radius = mp.coth(dd), 1/mp.sinh(dd)
        geom = mp.log((center+radius)/(center-radius))
        close("G10", geom, 2*mp.log(mp.coth(dd/2)), relative=True)
    for dd in (100, 1000):
        qq = mp.exp(-dd)
        stable = 2*mp.log1p(2*qq/(1-qq))
        zz = 2*qq/(1+qq*qq)
        independent = mp.log1p(zz)-mp.log1p(-zz)
        close("G10", stable, independent, relative=True)
        assert stable > 0
        direct = 2*mp.log(mp.coth(mp.mpf(dd)/2))
        if dd == 1000:
            assert direct == 0
            notes.append({"group": "G10", "d": str(dd), "positive_shadow": mp.nstr(stable, 18),
                "scaled_by_4_exp_minus_d": mp.nstr(stable/(4*qq), 18),
                "subtractive_value": "0", "status": "subtractive route rejected"})

    return {"decimal_digits": dps, "scaled_tolerance": mp.nstr(tolerance, 6),
        "groups": {g: {"comparisons": d["comparisons"],
                        "max_scaled_residual": mp.nstr(d["max_scaled_residual"], 12)}
                   for g, d in groups.items()}, "conditioning_observations": notes}


result = {"status": "author_finite_checks_passed_not_independent_review",
          "scope": "Representative finite checks; does not implement the full maintained companion contract.",
          "evidence_classes": {"exact": "finite symbolic identities",
                               "numerical": "uncertified floating comparisons at stated precision",
                               "tails": "evaluations of analytically proved bounds, not interval enclosures"},
          "versions": {"python": platform.python_version(), "sympy": sp.__version__, "mpmath": mp.__version__},
          "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          "exact_count": len(exact), "exact": exact,
          "numeric": [run_numeric(70), run_numeric(110)]}
(HERE/"author-scratch-result.json").write_text(json.dumps(result, indent=2)+"\n")
print(json.dumps({"status": result["status"], "exact_count": len(exact),
                  "numerical_comparisons": [sum(g["comparisons"] for g in run["groups"].values())
                                            for run in result["numeric"]]}))
