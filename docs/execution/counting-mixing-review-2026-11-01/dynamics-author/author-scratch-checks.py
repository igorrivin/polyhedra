"""Exact finite author probes, separate from the planned root-owned companion."""
import json
from pathlib import Path
import platform
import sympy as s

J = s.Matrix([[0,-1],[1,0]])
A = s.diag(1,-1)
W = s.Matrix([[0,1],[1,0]])
assert J*A-A*J == 2*W
x,y,a,b,t,h,r = s.symbols('x y a b t h r', real=True)
f = s.exp(-s.pi*(a*x*x+b*y*y))
assert s.simplify(-y*s.diff(f,x)+x*s.diff(f,y)-2*s.pi*(a-b)*x*y*f) == 0
C = s.exp(-r*t)
assert s.simplify(s.diff(s.exp(h*t)*C,t)-s.exp(h*t)*(h*C+s.diff(C,t))) == 0
ones = s.Matrix([1,1])
v = s.Matrix([1,-1])
checks = 0
for m in (2,3,5):
    matrix = s.Matrix([[0,m],[m,0]])
    P = matrix/m
    for n in range(1,33):
        power = matrix**n
        assert (ones.T*power*ones)[0] == 2*m**n
        assert s.trace(power) == m**n+(-m)**n
        assert (v.T*(P**n)*v)[0]/2 == (-1)**n
        checks += 3
report = dict(status='passed',evidence='exact finite arithmetic and symbolic identities',python=platform.python_version(),sympy=s.__version__,matrix_inputs={'m':[2,3,5],'n_inclusive':[1,32]},matrix_identity_count=checks,symbolic_identity_count=3,limits='Author scratch probes only. These do not execute experiments/counting_mixing, create artifacts/counting_mixing/result.json, prove uniform mixing, or certify numerical Gaussian quadrature.')
path = Path(__file__).with_name('author-scratch-result.json')
path.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
