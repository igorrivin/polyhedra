"""Reviewer-owned bounded probes; not the maintained companion or a proof oracle."""
from __future__ import annotations

import hashlib
import itertools
import json
import platform
from fractions import Fraction as F
from math import factorial
from pathlib import Path

import mpmath as mp
import sympy as s

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / "consolidated"
REPORT = {"status": "independent_finite_review_probes", "scope": "Exact algebra plus bounded numerical agreement, not interval certification, maintained companion execution, or a global asymptotic theorem.", "python": platform.python_version(), "mpmath": mp.__version__, "sympy": s.__version__, "precisions": [70, 110]}


def radial_moment(k, monomial):
    total = F(0)
    for a in range(k + 1):
        for b in range(k - a + 1):
            c = k - a - b
            total += F(factorial(k), factorial(a) * factorial(b) * factorial(c)) * monomial(2*a, 2*b, 2*c)
    return total


def simplex_monomial(a, b, c):
    return F(factorial(a)*factorial(b)*factorial(c), factorial(a+b+c+3))


def polynomial_unit_cube_integral(expr, variables):
    return sum(coef / s.prod(exponent+1 for exponent in powers) for powers, coef in s.Poly(s.expand(expr), *variables).terms())


u,v,w = s.symbols("u v w")
duffy_radius = u*u + ((1-u)*v)**2 + ((1-u)*(1-v)*w)**2
duffy_jacobian = (1-u)**2*(1-v)
simplex = []
for k in range(5):
    first = radial_moment(k, simplex_monomial)
    second = polynomial_unit_cube_integral(duffy_radius**k*duffy_jacobian, (u,v,w))
    assert s.Rational(first.numerator, first.denominator) == second
    simplex.append({"k": k, "moment": str(first), "duffy_exact": str(second)})
assert [x["moment"] for x in simplex[:3]] == ["1/6", "1/20", "2/105"]
REPORT["simplex_moments"] = simplex

boxes = [((-1,1),(-1,1),(-1,1)), ((F(1,3),F(7,3)), (F(-2,5),F(3,5)), (F(1,7),F(15,7)))]
box_results = []
for box in boxes:
    def mono(a,b,c):
        result = F(1)
        for (lo,hi), exponent in zip(box,(a,b,c)):
            result *= F(F(hi)**(exponent+1)-F(lo)**(exponent+1), exponent+1)
        return result
    shifts = [s.Rational(lo)+s.Rational(hi-lo)*x for (lo,hi),x in zip(box,(u,v,w))]
    jac = s.prod(s.Rational(hi-lo) for lo,hi in box)
    radius = sum(x*x for x in shifts)
    moments = [radial_moment(k,mono) for k in range(5)]
    for k,moment in enumerate(moments):
        assert s.Rational(moment.numerator,moment.denominator) == polynomial_unit_cube_integral(radius**k*jac,(u,v,w))
    volume = mono(0,0,0)
    curvature_sum = F(0)
    coefficients = []
    for axis1,axis2 in itertools.combinations(range(3),2):
        other = ({0,1,2}-{axis1,axis2}).pop()
        length = F(box[other][1]-box[other][0])
        for side1,side2 in itertools.product((0,1), repeat=2):
            hf = F(box[axis1][side1]) * (-1 if side1==0 else 1)
            hg = F(box[axis2][side2]) * (-1 if side2==0 else 1)
            bcoef = -hf*hg
            curvature_sum += length*bcoef
            coefficients.append(str(bcoef))
    assert curvature_sum == -3*volume
    box_results.append({"bounds": [[str(lo),str(hi)] for lo,hi in box], "moments": list(map(str,moments)), "face_b": coefficients, "sum_L_b": str(curvature_sum), "minus_3_volume": str(-3*volume)})
assert box_results[0]["moments"][:3] == ["8","8","152/15"]
REPORT["box_moments_and_curvature"] = box_results

# Derive outward normals from simplex vertices; no hard-coded b coefficients.
vertices = [s.Matrix(x) for x in [(0,0,0),(1,0,0),(0,1,0),(0,0,1)]]
center = sum(vertices,s.zeros(3,1))/4
faces=[]
for face_ids in itertools.combinations(range(4),3):
    a,b,c = [vertices[i] for i in face_ids]
    normal=(b-a).cross(c-a)
    if normal.dot(center-a)>0: normal=-normal
    normal=s.simplify(normal/s.sqrt(normal.dot(normal)))
    faces.append((set(face_ids),normal,s.simplify(normal.dot(a))))
simplex_edges=[]
for (fi,nf,hf),(gi,ng,hg) in itertools.combinations(faces,2):
    shared=sorted(fi&gi)
    if len(shared)!=2: continue
    edge=vertices[shared[1]]-vertices[shared[0]]
    length=s.sqrt(edge.dot(edge));cosine=-nf.dot(ng);sine=s.sqrt(1-cosine*cosine)
    bcoef=s.simplify(-(hf*hg+cosine*(hf*hf+hg*hg)/2)/sine)
    simplex_edges.append((length,bcoef))
assert s.simplify(sum(length*coef for length,coef in simplex_edges)) == -s.Rational(1,2)
REPORT["simplex_dihedral_curvature"] = [{"L":str(length),"b":str(coef)} for length,coef in simplex_edges]

t=s.symbols("t")
tails=[]
for m in range(9):
    poly=sum((k+1)*t**k for k in range(m+1))
    tail=t**(m+1)*(m+2-(m+1)*t)/(1-t)**2
    assert s.cancel(1/(1-t)**2-poly-tail)==0
    tails.append(m)
REPORT["exact_scalar_tail_orders"] = tails
x,y,z=s.symbols("x y z")
vec=s.Matrix([x,y,z]);den=1-x*x-y*y-z*z
metric=s.eye(3)/den+vec*vec.T/den**2
assert s.factor(metric.det()-den**-4)==0
REPORT["klein_metric_determinant"]="(1-x^2-y^2-z^2)^(-4), checked by symbolic matrix determinant"

a=s.symbols("a")
peripheral=[]
for p,q,rho,sigma in [(1,1,0,1),(5,2,2,1),(-3,2,-2,1),(5,-2,-2,1)]:
    assert p*sigma-q*rho==1
    G=F(p,4*q)*u*u-F(1,2*q)*u*a+F(sigma,4*q)*a*a
    vsol=(a-p*u)/q;core=rho*u+sigma*vsol
    assert s.simplify(s.diff(G,u)+vsol/2)==0
    assert s.simplify(s.diff(G,a)-core/2)==0
    vpoly=2*u+3*u**3-5*u**5
    Phi=s.integrate(vpoly/2,u)
    assert s.expand(s.diff(Phi+G,u)-(p*u+q*vpoly-a)/(2*q))==0
    assert s.expand(s.diff(Phi+G,u,2)-(p+q*s.diff(vpoly,u))/(2*q))==0
    assert s.simplify(-s.diff(G,u,a)/s.diff(Phi+G,u,2)-1/(p+q*s.diff(vpoly,u)))==0
    peripheral.append([p,q,rho,sigma])
REPORT["filling_slopes_exact"] = peripheral
REPORT["weyl_derivation"]="For arbitrary f, (lm f)(u)=exp((u+h)/2)f(u+h)=exp(h/2)(ml f)(u); [h*d/du,u]f=h*f."

weightsets=[[F(1,2)]*4,[F(1,4),F(1,2),F(1,2),F(3,4)],[F(2,5)]*5]
charge=[]
for weights in weightsets:
    assert sum(weights)==2 and all(0<x<1 for x in weights)
    for b2 in [F(1,16),F(1,3),F(4,5)]:
        # Multiplying beta<Q by b gives mu<b^2+1.
        bounds=[1/b2]+[1+(1-mu)/b2 for mu in weights]
        assert all(bound>1 for bound in bounds) and all(mu<1+b2 for mu in weights)
        assert (sum(weights)/2-(b2+1))/b2 == -1
        charge.append({"mu":list(map(str,weights)),"b_squared":str(b2),"strict_moment_margins":list(map(str,[bound-1 for bound in bounds]))})
REPORT["charge_specialization_exact"] = charge

numeric=[]
for dps in REPORT["precisions"]:
    with mp.workdps(dps):
        figures=[]
        for N in [2,3,6,7,12,31,40,60,120]:
            logs=[mp.mpf(0)]
            for k in range(1,N): logs.append(logs[-1]+mp.log(4*mp.sin(mp.pi*k/N)**2))
            m=5*N//6;maxlog=logs[m]
            positive=mp.exp(maxlog)*mp.fsum(mp.exp(v-maxlog) for v in logs)
            terms=[mp.mpc(1)];product=mp.mpc(1)
            for k in range(1,N):
                alpha=mp.pi*(N-k)/N;beta=mp.pi*(N+k)/N
                product *= (mp.exp(1j*alpha)-mp.exp(-1j*alpha))*(mp.exp(1j*beta)-mp.exp(-1j*beta))
                terms.append(product)
            independent=mp.fsum(terms)
            relative=abs(independent-positive)/positive
            product_error=abs(mp.exp(logs[-1])/N**2-1)
            maximum_error=max(mp.mpf(0),max(logs)-maxlog)
            assert relative<mp.mpf(10)**(-dps+8)
            assert product_error<mp.mpf(10)**(-dps+8)
            assert maximum_error<mp.mpf(10)**(-dps+8)
            assert positive>=mp.exp(maxlog)*(1-mp.mpf(10)**(-dps+8))
            assert positive<=N*mp.exp(maxlog)*(1+mp.mpf(10)**(-dps+8))
            figures.append({"N":N,"relative_complex_vs_positive":mp.nstr(relative,15),"relative_imaginary":mp.nstr(abs(mp.im(independent))/positive,15),"relative_final_product":mp.nstr(product_error,15),"log_maximum_error":mp.nstr(maximum_error,15),"rate":mp.nstr(2*mp.pi*mp.log(positive)/N,25)})
        # Independent numerical quadrature and dilogarithm value, not an interval bound.
        lamb=mp.quad(lambda theta:-mp.log(2*mp.sin(theta)),[0,mp.pi/6,mp.pi/3])
        target1=6*lamb; target2=2*mp.im(mp.polylog(2,mp.exp(1j*mp.pi/3)))
        assert abs(target1-target2)<mp.mpf(10)**(-dps+8)
        scalar=[]
        for tt in [mp.mpf(1)/1000,mp.mpf(1)/8,mp.mpf(1),mp.mpf(100)]:
            rem=-1/mp.expm1(-tt)-1/tt-mp.mpf(1)/2
            assert 0<rem<=tt/12
            scalar.append({"t":mp.nstr(tt,15),"remainder_divided_by_t":mp.nstr(rem/tt,25)})
        numeric.append({"dps":dps,"figures":figures,"volume_integral":mp.nstr(target1,dps-5),"volume_dilog":mp.nstr(target2,dps-5),"volume_absolute_difference":mp.nstr(abs(target1-target2),15),"q_product_scalar_remainders":scalar})
REPORT["numerical"] = numeric
REPORT["review_input_sha256"]={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/"book/chapters/10-quantum-introduction.tex",ROOT/"book/chapters/11-quantum-degeneration.tex"]}
REPORT["script_sha256"]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(OUT/"independent-probe-results.json").write_text(json.dumps(REPORT,indent=2)+"\n")
print(json.dumps({"status":"passed","output":str(OUT/"independent-probe-results.json"),"precisions":REPORT["precisions"],"numerical_figure_cases":sum(len(x["figures"]) for x in numeric),"exact_moment_cases":15,"exact_charge_cases":len(charge),"scope":REPORT["scope"]},indent=2))
