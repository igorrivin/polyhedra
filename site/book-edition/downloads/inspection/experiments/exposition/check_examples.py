#!/usr/bin/env python3
"""Exact small examples for the exposition pass; no scientific campaign replay."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sympy as s

ROOT = Path(__file__).resolve().parents[2]
records = []


def equal(section, name, actual, expected):
    residual = s.simplify(actual - expected)
    if residual != 0:
        raise ArithmeticError(f"{section}: {name}: residual {residual}")
    records.append({"section": section, "example": name, "value": str(s.simplify(actual)),
                    "expected": str(expected), "residual": "0", "method": "exact symbolic arithmetic"})


def main():
    q, pi = s.Rational, s.pi
    x, y, z = s.symbols("x y z", real=True)
    ell, h, k, a, b, c, d = s.symbols("ell h k a b c d", positive=True)
    equal("1", "pants parameters for a once-punctured torus", 3*1-3+1, 1)
    equal("2", "regular exterior perimeter", 3*2*pi/3, 2*pi)
    equal("2", "tetrahedral angle-cell dimension", 6-4, 2)
    equal("2", "delta constraint versus arclength", s.sqrt(1+1)/s.sqrt(2), 1)
    equal("3", "angle-domain coordinate area", s.integrate(pi-x, (x, 0, pi)), pi**2/2)
    equal("3", "two orientation sheets at density two", 2*2*pi**2/2, 2*pi**2)
    equal("3", "equilateral cross-ratio density", 1/(q(1,2)*q(2,1)/s.sqrt(3)), s.sqrt(3))
    equal("4", "inverse Poisson block determinant", s.det(s.Matrix([[0, 1/a], [-1/a, 0]])), a**-2)
    equal("5,B", "opening plus deficit at weight one third", 2*pi*(1-q(1,3))+2*pi*q(1,3), 2*pi)
    equal("6", "orbifold cover area", 2*pi/2, pi)
    mu = q(1,3)
    R = x**(1-mu)/(1-mu)
    equal("7", "cone radial coefficient", s.diff(R, x)**2, x**(-2*mu))
    equal("7", "collision rotation order", 1/(1-2*q(1,3)), 3)
    equal("8", "inverse cometric rescaling", 1/(a**-1*k), a/k)
    E = x*x+(x-1)**2
    equal("9", "network minimizing voltage", s.solve(s.diff(E,x), x)[0], q(1,2))
    equal("9", "network minimized energy", E.subs(x,q(1,2)), q(1,2))
    equal("9", "network Gaussian completion of square", E, 2*(x-q(1,2))**2+q(1,2))
    j = q(1,2)
    equal("10", "spin half squared magnitude in hbar squared units", j*(j+1), q(3,4))
    equal("10", "spin half magnitude in hbar units", s.sqrt(j*(j+1)), s.sqrt(3)/2)
    F = s.Matrix([[-q(1,2), s.sqrt(3)/2], [s.sqrt(3)/2, q(1,2)]])
    equal("10", "recoupling matrix orthogonality", sum((F*F.T-s.eye(2)).applyfunc(lambda v:v*v)), 0)
    equal("10", "last-pair singlet probability", F[0,0]**2, q(1,4))
    equal("10", "last-pair triplet probability", F[0,1]**2, q(3,4))
    equal("10", "figure-eight colored Jones N=3", 1+3+9, 13)
    equal("10", "Gaussian integral", s.integrate(s.exp(-k*x*x/(2*h)), (x,-s.oo,s.oo)), s.sqrt(2*pi*h/k))
    equal("11", "cube quadratic moment", s.integrate(x*x+y*y+z*z,(x,-1,1),(y,-1,1),(z,-1,1)), 8)
    equal("11", "Klein cube fifth-order coefficient", 2*8, 16)
    equal("12", "first Fricke density correction at u=v=1", q(1,2)*q(-3,16), q(-3,32))
    equal("13", "four-point delta zero example", 1-q(1,4)-q(1,2), q(1,4))
    equal("13", "logarithmic limiting basis at positive z", s.limit((s.exp(x*s.log(a))-1)/x,x,0), s.log(a))
    B = s.Matrix([[s.sqrt(3),-(s.sqrt(6)-s.sqrt(2))/2],[2,-s.sqrt(2)]])
    equal("14", "nonbalanced fusion determinant", B.det(), -s.sqrt(2))
    G = s.Matrix([[1,-1,0,0],[-1,1,0,0],[0,0,1,-1],[0,0,-1,1]])
    equal("14", "screened Gram characteristic polynomial", (x*s.eye(4)-G).det(), x*x*(x-2)**2)
    equal("15", "quartic correction at cubic scale", q(4,3)-1, q(1,3))
    V = -k*x*x/2-a*y*y/2+c*x*x*y+d*x**4
    equal("16", "quartic correction after transverse optimization", s.expand(V.subs(y,c*x*x/a)).coeff(x,4), d+c*c/(2*a))
    equal("16", "square-cusp Hessian determinant", s.det(s.hessian(-(x*x+y*y)/4,(x,y))), q(1,4))
    P = (s.exp(-x)+s.exp(x-1))/(1-s.exp(-1))
    equal("17", "unfolded integral on a circle", s.integrate(P,(x,0,1)), 2)
    equal("18", "positive pants traces", 3*3+2, 11)
    equal("18", "cusp figure-eight trace", 3*2+3, 9)
    equal("19", "Fermi distance at common seam", s.cosh(0)*s.cosh(0)*s.cosh(d)-s.sinh(0)*s.sinh(0), s.cosh(d))
    equal("20", "coarea example A=2", s.diff(2*s.acosh(2*s.cosh(x/2)),x,2).subs(x,0), 1/s.sqrt(3))
    equal("21", "two endpoint translations agree", (2-1)-(4-3), 0)
    equal("21", "altered endpoint translations disagree", (2-1)-(5-3), -1)
    equal("21", "corner first variation", q(1,2)-q(-1,2), 1)
    equal("21", "normal component at tangent one half", s.sqrt(1-q(1,2)**2), s.sqrt(3)/2)
    equal("22", "intersection lies on first semicircle", (q(3,2)-1)**2+(s.sqrt(3)/2)**2, 1)
    equal("22", "intersection lies on translate", (q(3,2)-2)**2+(s.sqrt(3)/2)**2, 1)
    equal("22", "halving horocycle change", 2*s.log(4/(h/2))-2*s.log(4/h), 2*s.log(2))
    A = s.Matrix([[x,-1],[1,0]])
    equal("23", "double traversal trace", s.trace(A**2), x*x-2)
    equal("23", "triple traversal trace", s.trace(A**3), x**3-3*x)
    equal("24", "primitive disconnected weights", s.gcd(2,3), 1)
    poly = 2+3*x+5*x*x+7*x**3
    equal("24", "four roots of unity select linear coefficient", sum(poly.subs(x,s.I**n)*s.I**(-n) for n in range(4))/4, 3)
    equal("24", "smoothing exponent", q(1,1)/(2+1), q(1,3))
    equal("25", "one-crossing filter", 1-1, 0)
    equal("25", "doubled one-crossing filter", 5-2+1-4, 0)
    equal("25", "simple double traversal filter", 1-4, -3)
    T = s.Matrix([[2,1],[1,2]])
    for n in range(1,6):
        equal("26", f"two-state periodic count n={n}", s.trace(T**n), 3**n+1)
        f = s.Matrix([1,-1])
        equal("26", f"two-state covariance n={n}", (f.T*(T/3)**n*f)[0]/2, q(1,3)**n)
    equal("27", "area preserved by diagonal flow", 2*s.exp(x)*3*s.exp(-x), 6)
    for n, inverse in [(1,1),(2,3),(3,2),(4,4)]:
        equal("27", f"inverse residue {n} modulo 5", (n*inverse)%5, 1)
    equal("28", "quadratic pullback coefficient", (x*x)**3*(2*x)**2, 4*x**8)
    equal("29", "length-weight derivative bound at maximum", (x*s.exp(-x)).subs(x,1), s.exp(-1))
    equal("29", "Gaussian covariance at zero", 1/(2*s.cosh(0)), q(1,2))
    equal("29", "Gaussian covariance at log two", 1/(2*s.cosh(s.log(2))), q(2,5))
    equal("30", "integrable logarithmic modulus", s.integrate(x**-2,(x,1,s.oo)), 1)
    equal("30", "dyadic leading term cancels", c*(2*ell)**2+b*2*ell-4*(c*ell**2+b*ell), -2*b*ell)
    equal("30", "primitive closed interval n=6", sum(s.mobius(k)*(6//k) for k in s.divisors(6)), 2)
    equal("30", "first modular-torus trace replacement", 3*3-3, 6)
    equal("31", "Mertens sum at six", sum(s.mobius(k) for k in range(1,7)), -1)
    alpha,theta = q(2,3),q(1,2)
    cutoff = (2-alpha)/(3-alpha-theta)
    equal("31", "balanced cutoff exponent", cutoff, q(8,11))
    equal("31", "small-divisor error exponent", alpha+cutoff*(1-alpha), q(10,11))
    equal("31", "large-divisor error exponent", 2+cutoff*(theta-2), q(10,11))
    equal("31", "signed multiples at cutoff five", 2*(5//2), 4)
    equal("32", "four-boundary target correction", sum(q(n*n,2) for n in [1,2,3,4]), 15)
    equal("A", "trace Jacobian cancels hyperbolic factor", s.sinh(ell/2)*(-z/(2*s.sinh(ell/2))), -z/2)
    equal("A", "density at absolute Phi_z four", q(2,4), q(1,2))
    files = [Path(__file__), *sorted((ROOT/'book/chapters').glob('*.tex'))]
    result = {"schema_version":1, "purpose":"Exact teaching examples for the whole-monograph exposition pass",
              "source_commit":subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              "source_dirty":bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),
              "source_sha256":{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              "python":platform.python_version(), "sympy":s.__version__,
              "passed":len(records), "checks":records,
              "limits":"Fixed exact algebra and symbolic integrals only. No global theorem, interval quadrature, geometric realization or historical scientific campaign is verified by this script."}
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
