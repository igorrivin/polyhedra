#!/usr/bin/env python3
"""Independent finite exact Section 16 review probes. Standard library only.

This script does not import the companion, solve a manifold, certify an analytic
remainder, evaluate torsion, or compute a quantum invariant.
"""
from collections import Counter
from fractions import Fraction as Q
from pathlib import Path
import hashlib
import json
import sys

NAMES = ('A', 'q', 'c3', 'c5', 'sigma', 'tau', 'a', 'u', 'X', 'Y', 'z')
ZERO = (0,) * len(NAMES)


class P:
    """Sparse Laurent polynomial over Q, with monomial division only."""
    def __init__(self, terms=0):
        if isinstance(terms, P):
            self.d = terms.d.copy()
        elif isinstance(terms, dict):
            self.d = {m: Q(c) for m, c in terms.items() if c}
        else:
            self.d = {ZERO: Q(terms)} if terms else {}

    def __add__(self, other):
        out = self.d.copy()
        for m, c in P(other).d.items():
            out[m] = out.get(m, Q(0)) + c
        return P(out)

    __radd__ = __add__

    def __neg__(self):
        return P({m: -c for m, c in self.d.items()})

    def __sub__(self, other):
        return self + -P(other)

    def __rsub__(self, other):
        return P(other) + -self

    def __mul__(self, other):
        out = {}
        for m, c in self.d.items():
            for n, d in P(other).d.items():
                k = tuple(x + y for x, y in zip(m, n))
                out[k] = out.get(k, Q(0)) + c * d
        return P(out)

    __rmul__ = __mul__

    def __pow__(self, n):
        if n < 0:
            assert len(self.d) == 1
            m, c = next(iter(self.d.items()))
            return P({tuple(n * x for x in m): c ** n})
        out = P(1)
        for _ in range(n):
            out = out * self
        return out

    def __truediv__(self, other):
        return self * (P(other) ** -1)

    def __rtruediv__(self, other):
        return P(other) / self

    def trunc(self, variable, degree):
        k = NAMES.index(variable)
        return P({m: c for m, c in self.d.items() if m[k] <= degree})

    def diff(self, variable):
        k = NAMES.index(variable)
        out = {}
        for m, c in self.d.items():
            if m[k]:
                n = list(m)
                n[k] -= 1
                out[tuple(n)] = c * m[k]
        return P(out)

    def zero(self):
        return not self.d


def variable(name):
    m = [0] * len(NAMES)
    m[NAMES.index(name)] = 1
    return P({tuple(m): Q(1)})


A, q, c3, c5, sigma, tau, a, u, X, Y, z = map(variable, NAMES)
checks = []


def check(name, statement, result):
    ok = result.zero() if isinstance(result, P) else bool(result)
    checks.append({'name': name, 'statement': statement, 'passed': ok})


# Generic formal inversion in filling coordinate a; a=i*theta is then an exact
# substitution, changing the signs of the even powers in the action.
p = A - q * tau
rho = (p * sigma - 1) / q
ui = a / A - q*c3*a**3/A**4 + (3*q**2*c3**2/A**7-q*c5/A**6)*a**5
check('inverse_degree5', 'A*u+q*c3*u^3+q*c5*u^5=a modulo a^7',
      (A*ui + q*c3*ui**3 + q*c5*ui**5-a).trunc('a', 5))
F = tau*ui**2/2+c3*ui**4/4+c5*ui**6/6
action = F + p*ui**2/(2*q)-a*ui/q
expected = -a**2/(2*q*A)+c3*a**4/(4*A**4)+(c5/A**6-3*q*c3**2/A**7)*a**6/6
check('action_degree6', 'Critical action through degree six, before a=i*theta',
      (action-expected).trunc('a', 6))
check('envelope_degree5', 'd S*/da=-u/q through degree five',
      (expected.diff('a')+ui/q).trunc('a', 5))
bi = (sigma*a-ui)/q
bexpect = (rho+sigma*tau)*a/A+c3*a**3/A**4+(c5/A**6-3*q*c3**2/A**7)*a**5
check('covariance_degree5', 'SL2 determinant-one transformed coefficients', bi-bexpect)
v = (a-p*u)/q
b = (sigma*a-u)/q
G = p*u**2/(4*q)-u*a/(2*q)+sigma*a**2/(4*q)
check('canonical_u_derivative', 'G_u=-v/2', G.diff('u')+v/2)
check('canonical_a_derivative', 'G_a=b/2', G.diff('a')-b/2)
check('canonical_invariant', 'G=(a*b-u*v)/4 on the canonical relation', G-(a*b-u*v)/4)
check('canonical_symplectic', 'p*sigma-q*rho=1', p*sigma-q*rho-1)
theta = p*Y+q*z  # Here X=Re(u), Y=Im(u), z=Im(v).
volume_twice = c5-X*z  # c5 is a fresh formal value Im(F) in this check.
imaginary_action = c5+p*X*Y/q-theta*X/q
check('critical_volume_factor', '2(V-V0)=Im(S*) under the angular filling equation', volume_twice-imaginary_action)
check('half_density_squared', '(-G_ua)*D*=(Phi+G)_uu, hence squared ratio=1/D*',
      (-G.diff('u').diff('a'))*(p+q*z)-(p+q*z)/(2*q))

# Elimination of z from z(1-z)=Y and the gluing relation. No divisions at X=1
# are used in this polynomial identity, so continuation across the cusp is clear.
numerator = (X*Y-1)**2-(X*Y-1)*(X**2-1)+Y*(X**2-1)**2
eliminant = X**2*(Y**2+(X**2+X**-2-X-X**-1-2)*Y+1)
check('figure8_eliminant', 'Resultant relation yielding cosh(v/2)=1+cosh(u)-cosh(2u)', numerator-eliminant)

# Solve the cosh coefficients independently, writing v=2*i*sqrt(3)*f(u).
rhs4 = Q(1-2**4, 24)
b3 = (Q(9,24)-rhs4)/3
rhs6 = Q(1-2**6,720)
b5 = (-Q(3,2)*b3*b3+Q(3,2)*b3-Q(27,720)-rhs6)/3
check('figure8_c3', 'f cubic coefficient is 1/3', b3 == Q(1,3))
check('figure8_c5', 'f quintic coefficient is 23/180', b5 == Q(23,180))
f = u+b3*u**3+b5*u**5
lhs = 1-Q(3,2)*f**2+Q(9,24)*f**4-Q(27,720)*f**6
rhs = 1-Q(3,2)*u**2+rhs4*u**4+rhs6*u**6
check('figure8_cosh_degree6', 'All cosh coefficients through u^6 agree exactly', (lhs-rhs).trunc('u',6))


def tr(M):
    return list(map(list, zip(*M)))


def mm(A, B):
    return [[sum((x*y for x,y in zip(row,col)), Q(0)) for col in tr(B)] for row in A]


def inv(M):
    n = len(M)
    a = [[Q(x) for x in row]+[Q(i==j) for j in range(n)] for i,row in enumerate(M)]
    for i in range(n):
        j = next(j for j in range(i,n) if a[j][i])
        a[i],a[j] = a[j],a[i]
        pivot = a[i][i]
        a[i] = [x/pivot for x in a[i]]
        for j in range(n):
            if j != i:
                factor = a[j][i]
                a[j] = [x-factor*y for x,y in zip(a[j],a[i])]
    return [row[n:] for row in a]


def det(M):
    a = [[Q(x) for x in row] for row in M]
    out = Q(1)
    for i in range(len(a)):
        j = next((j for j in range(i,len(a)) if a[j][i]),None)
        if j is None:
            return Q(0)
        if i != j:
            a[i],a[j] = a[j],a[i]
            out = -out
        pivot = a[i][i]
        out *= pivot
        for j in range(i+1,len(a)):
            factor = a[j][i]/pivot
            a[j] = [x-factor*y for x,y in zip(a[j],a[i])]
    return out


# Reuse X,Y for Re(T), Im(T), with Y nonzero. These are generic Laurent
# polynomial identities, not numerical choices of a cusp shape.
g = [[(X**2+Y**2)/(2*Y),-X/(2*Y)],[-X/(2*Y),1/(2*Y)]]
J = [[-X/Y,1/Y],[-(X**2+Y**2)/Y,X/Y]]
omega = [[0,-Q(1,2)],[Q(1,2),0]]
J2 = mm(J,J)
omegaJ = mm(omega,J)
C = [[0,1],[Y,X]]  # (dx,dy) -> (dy,ds).
pullback = mm(mm(tr(C),g),C)
check('boundary_hessian_determinant', 'det(g)=1/4 identically', g[0][0]*g[1][1]-g[0][1]*g[1][0]-Q(1,4))
check('boundary_complex_structure', 'J^2=-I identically', all((J2[i][j]+int(i==j)).zero() for i in range(2) for j in range(2)))
check('boundary_compatibility', 'omega_ang J=g and pullback g=Im(T)|du|^2/2',
      all((omegaJ[i][j]-g[i][j]).zero() and (pullback[i][j]-(Y/2 if i==j else 0)).zero() for i in range(2) for j in range(2)))


E = [[1,0,0],[0,1,0],[-1,-1,0],[0,0,1],[1,-1,1],[-1,1,-2]]
Pmat = [[0,-1,1],[2,-2,0]]
K0 = mm(tr(E),E)  # K=K0/sqrt(3)
K0i = inv(K0)
check('figure8_K', 'K0=E^T E equals the displayed integer matrix', K0==[[4,-1,3],[-1,4,-3],[3,-3,6]])
check('figure8_K_positive', 'Exact positive leading principal minors', all(det([row[:k] for row in K0[:k]])>0 for k in (1,2,3)))
check('figure8_response', 'P K0^-1 P^T=diag(1/3,4)', mm(mm(Pmat,K0i),tr(Pmat))==[[Q(1,3),0],[0,4]])
fixture_results = []
for pp,qq in [(17,3),(13,-4),(2,1),(1,0),(0,1),(-19,5)]:
    L = [[pp*Pmat[0][i]+qq*Pmat[1][i] for i in range(3)]]
    kL = mm(K0i,tr(L))
    chi0 = mm(L,kL)[0][0]
    D = pp*pp+12*qq*qq
    e = [[r[0]/chi0] for r in kL]
    stated_e = [[Q(6*qq-pp,2*D)],[Q(-6*qq-pp,2*D)],[Q(pp-6*qq,2*D)]]
    check(f'e_{pp}_{qq}', 'Independent inverse-Hessian response equals stated e', e==stated_e)
    ee = mm(E,e)
    cubic = Q(4,3)*sum((r[0]**3 for r in ee),Q(0))
    t = mm(tr(E),[[Q(4,3)*r[0]**2] for r in ee])
    R0 = [[K0i[i][j]-kL[i][0]*kL[j][0]/chi0 for j in range(3)] for i in range(3)]
    quartic_over_sqrt3 = -Q(8,9)*sum((r[0]**4 for r in ee),Q(0))+3*mm(mm(tr(t),R0),t)[0][0]
    target = Q(2*(pp**4-72*pp*pp*qq*qq+144*qq**4),D**4)
    check(f'quartic_{pp}_{qq}', 'Cubic vanishes and corrected quartic/sqrt(3) has stated value', cubic==0 and quartic_over_sqrt3==target)
    fixture_results.append({'p':pp,'q':qq,'chi_over_sqrt3':str(chi0),'quartic_over_sqrt3':str(quartic_over_sqrt3)})

# Noncommuting A,B fixtures detect order errors in the multicusp block formula.
for Am,Bm in [([[1,2],[2,-1]],[[3,1],[1,2]]),([[1,2,-1],[2,0,3],[-1,3,2]],[[4,1,0],[1,3,1],[0,1,2]])]:
    h = len(Am)
    Bi = inv(Bm)
    ABi = mm(Am,Bi)
    BiA = mm(Bi,Am)
    ABiA = mm(ABi,Am)
    M = [[(Bm[i][j]+ABiA[i][j])/2 for j in range(h)]+[-ABi[i][j]/2 for j in range(h)] for i in range(h)]
    M += [[-BiA[i][j]/2 for j in range(h)]+[Bi[i][j]/2 for j in range(h)] for i in range(h)]
    check(f'multicusp_{h}', 'Block Hessian symmetric positive definite with determinant 4^-h', M==tr(M) and det(M)==Q(1,4**h) and all(det([row[:k] for row in M[:k]])>0 for k in range(1,2*h+1)))

root = Path(__file__).resolve().parents[3]
chapter = root/'consolidated/book/chapters/16-dehn-filling-response.tex'
ledger_path = root/'consolidated/book/claims/section16.json'
baseline = Path(__file__).resolve().parents[1]/'structure/16-dehn-filling-response.tex'
import re
labels = re.findall(r'\\label\{([^}]+)\}',chapter.read_text())
oldlabels = re.findall(r'\\label\{([^}]+)\}',baseline.read_text())
ledger = json.loads(ledger_path.read_text())
claims = ledger['claims']
assigned = [label for c in claims for label in c['labels']]
check('labels', 'All 53 labels preserved in exact original order', len(labels)==53 and labels==oldlabels)
check('ledger', '26 unique claim IDs cover exactly the 53 chapter labels', len(claims)==26 and len({c['id'] for c in claims})==26 and set(assigned)==set(labels))
report = {
    'evidence_status':'finite exact symbolic and rational fixtures; structural checks',
    'arithmetic':'Python standard-library fractions.Fraction; no floating point',
    'independence':'New review code; no import or execution of author companion',
    'passed':all(c['passed'] for c in checks),
    'check_count':len(checks), 'checks':checks,
    'figure8_f_coefficients':{'u3':str(b3),'u5':str(b5)},
    'figure8_fixtures':fixture_results,
    'label_count':len(labels),'claim_count':len(claims),
    'intentional_label_overlap':{k:v for k,v in Counter(assigned).items() if v>1},
    'frozen_files':{str(p.relative_to(root/'consolidated')):hashlib.sha256(p.read_bytes()).hexdigest() for p in (chapter,ledger_path)},
    'limitations':['No analytic remainder certificate','No geometric cone completion or manifold computation','No torsion or quantum-invariant evaluation','No global contour, noncancellation or simultaneous slope/level estimate'],
}
destination=Path(__file__).with_name('independent-probe-results.json')
destination.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':report['passed'],'check_count':len(checks),'output':str(destination)}))
sys.exit(0 if report['passed'] else 1)
