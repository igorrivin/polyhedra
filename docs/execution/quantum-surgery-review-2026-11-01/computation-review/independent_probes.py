"""Reviewer-owned checks; no source edits, installations, or interval claims.

SymPy derives polynomial coefficients directly from the original functions.
Numerical probes use independent series and finite differences, while sharing
mpmath arithmetic with the companion. Fixed points are deliberately bounded.
"""

from datetime import datetime, timezone
import argparse
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import sys

import sympy as sp

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE = Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
manifest=json.loads((HERE.parent/'computation/source-manifest.json').read_text())


def source_state():
    return [{'path':entry['path'],
             'sha256':sha256((ROOT/entry['path']).read_bytes()).hexdigest()}
            for entry in manifest['source_files']]


source_before=source_state()
script_hash_before=sha256(Path(__file__).read_bytes()).hexdigest()
sys.path.insert(0, str(ROOT))
from experiments.quantum_surgery import algebra, exact, periods

fixture = json.loads((ROOT/'experiments/quantum_surgery/fixture.json').read_text())
replay = json.loads((HERE/'replay-result.json').read_text())
checks = []
numerics = []


def sym(value):
    if isinstance(value, exact.Quadratic):
        return sym(value.a) + sym(value.b)*sp.sqrt(value.d)
    if isinstance(value, Q):
        return sp.Rational(value.numerator, value.denominator)
    if isinstance(value, str):
        return sp.Rational(value)
    if isinstance(value, list):
        return [sym(x) for x in value]
    return sp.sympify(value)


def equal(name, actual, expected):
    if isinstance(actual, sp.MatrixBase):
        residual = (actual-expected).applyfunc(sp.simplify)
        passed = residual.is_zero_matrix
    else:
        residual = sp.simplify(actual-expected)
        passed = residual == 0
    if not passed:
        raise AssertionError(f'{name}: {residual}')
    checks.append(name)


def numeric(name, actual, expected, tolerance):
    residual = abs(actual-expected)/max(c.mpf(1), abs(actual), abs(expected))
    if not c.isfinite(residual) or residual > c.mpf(tolerance):
        raise AssertionError(f'{name}: {residual} > {tolerance}')
    numerics.append({'name': name, 'scaled_residual': c.nstr(residual, 18),
                     'tolerance': tolerance})


# Symbolic Fricke expansion begins with sin, not the stored a^2 coefficients.
A, X, Y, Z = sp.symbols('A X Y Z')
x, y, z, trace = -2-A*X, -2-A*Y, -2-A*Z, -2*sp.sin(A/8)
phi = x*x+y*y+z*z+x*y*z-2*trace**2*(x+y+z)+4*trace**2+trace**4-4
expanded = sp.series(phi, A, 0, 5).removeO().expand()
expected = A**2*(X*X+Y*Y+Z*Z-2*X*Y-2*X*Z-2*Y*Z+1)
expected += A**3*(-X*Y*Z+(X+Y+Z)/8)-A**4/768
equal('Fricke from sine through A4, symbolic X,Y,Z', expanded, expected)
u, v = sp.symbols('u v', positive=True)
chart = {X:1/(2*v), Y:(u*u+v*v)/(2*v), Z:((u-1)**2+v*v)/(2*v)}
Z1 = sp.solve(sp.Eq(expanded.coeff(A, 3).subs(chart)
                   + sp.diff(expanded.coeff(A, 2), Z).subs(chart)*sp.Symbol('Z1'), 0),
              sp.Symbol('Z1'))[0]
jac = sp.det(sp.Matrix([[sp.diff(chart[w], s) for s in (u,v)] for w in (X,Y)]))
den0 = 2*(X+Y-Z)
den1 = X*Y-sp.Rational(1,8)-2*Z1
leading = sp.cancel(2*jac/den0.subs(chart))
correction = sp.cancel(-leading*den1.subs(chart)/den0.subs(chart))
fricke = algebra.fricke_checks(fixture)
for index,row in enumerate(fricke['heron_fixtures']):
    values={u:sym(row['u']),v:sym(row['v'])}
    equal(f'Fricke implicit derivative {index}', Z1.subs(values), sym(row['Z1']))
    equal(f'Fricke density leading {index}', leading.subs(values), sym(row['WP_over_A_leading']))
    equal(f'Fricke density correction {index}', correction.subs(values), sym(row['WP_over_A_linear']))

# Independent inverse trig Taylor expansions and Schlaefli integration.
ell = sp.symbols('ell', real=True)
area = sp.series(4*sp.pi-12*sp.acos(sp.cosh(ell)/(1+sp.cosh(ell))), ell, 0, 6).removeO()
defect = sp.series(sp.acos(sp.Rational(1,3))-sp.acos(sp.cosh(ell)/(1+2*sp.cosh(ell))),
                   ell, 0, 6).removeO()
regular = algebra.regular_checks()
for n in (0,1,2):
    equal(f'regular area ell{2*n}', area.expand().coeff(ell,2*n), sym(regular['area_in_ell_squared'][n]))
    equal(f'regular dihedral ell{2*n}', defect.expand().coeff(ell,2*n), sym(regular['dihedral_defect_in_ell_squared'][n]))
volume = sp.integrate(3*ell*sp.diff(defect,ell), (ell,0,ell))
equal('regular Schlaefli volume ell3', volume.coeff(ell,3), 1/(6*sp.sqrt(2)))
equal('regular Schlaefli volume ell5', volume.coeff(ell,5), -sp.Rational(23,480)/sp.sqrt(2))
# Invert A=sqrt(3)*ell^2 - sqrt(3)*ell^4/8 using ell=sqrt(A)/3^(1/4)*(1+k*A).
k = sp.solve(sp.Eq(2*sp.Symbol('k')-1/(8*sp.sqrt(3)),0),sp.Symbol('k'))[0]
relative_area_correction = 3*k + (volume.coeff(ell,5)/volume.coeff(ell,3))/sp.sqrt(3)
equal('regular volume area relative correction', relative_area_correction, -1/(10*sp.sqrt(3)))
a, w = sp.symbols('a w')
saddle = sp.expand((1+a**3*w)**4-(1-w)*(1-a**4*w)**3)
quotient,remainder=sp.div(saddle,w*(a+1)**2,w)
equal('regular saddle symbolic division remainder',remainder,0)
equal('regular saddle symbolic discriminant',sp.discriminant(quotient,w),-a**8*(a+1)**2*(3*a*a-2*a+3))
ae=(1+2*sp.sqrt(2)*sp.I)/3
we=sp.simplify(ae**-5)
equal('regular fold double root, symbolic quotient',quotient.subs({a:ae,w:we}),0)
equal('regular fold derivative, symbolic quotient',sp.diff(quotient,w).subs({a:ae,w:we}),0)
# Differentiate Li_2 through its logarithmic derivative, independently of the polynomial.
Sv=-sp.I*(sp.log(1-w)+3*sp.log(1-a**4*w)-4*sp.log(1+a**3*w))-2*sp.pi
Svv=sp.I*w*sp.diff(Sv,w)
Svvv=sp.I*w*sp.diff(Svv,w)
Sveta=sp.I*a*sp.diff(Sv,a)
equal('regular fold S_vv from potential',Svv.subs({a:ae,w:we}),0)
equal('regular fold S_vvv from potential',Svvv.subs({a:ae,w:we}),54*sp.I)
equal('regular fold S_veta from potential',Sveta.subs({a:ae,w:we}),18*sp.sqrt(2)*sp.I)

# Recover the chosen figure-eight branch using the exact cosh relation.
t = sp.symbols('t')
b3,b5=sp.symbols('b3 b5')
tau=2*sp.sqrt(3)*sp.I
relation=sp.series(sp.cosh((tau*t+b3*t**3+b5*t**5)/2)
                   -(1+sp.cosh(t)-sp.cosh(2*t)),t,0,8).removeO().expand()
c3=sp.solve(sp.Eq(relation.coeff(t,4),0),b3)[0]
c5=sp.solve(sp.Eq(relation.coeff(t,6).subs(b3,c3),0),b5)[0]
surgery=algebra.surgery_checks(fixture)
equal('figure-eight c3 recovered from cosh',c3,sym(surgery['c3']))
equal('figure-eight c5 recovered from cosh',c5,sym(surgery['c5']))
ta,C3,C5,p,q=sp.symbols('ta C3 C5 p q')
co=sp.symbols('k1 k3 k5')
candidate=co[0]*t+co[1]*t**3+co[2]*t**5
composition=sp.series(p*candidate+q*(ta*candidate+C3*candidate**3+C5*candidate**5)-t,t,0,7).removeO().expand()
solutions={}
for n,unknown in zip((1,3,5),co):
    solutions[unknown]=sp.solve(sp.Eq(composition.coeff(t,n).subs(solutions),0),unknown)[0]
candidate=sp.simplify(candidate.subs(solutions))
for index,row in enumerate(surgery['slopes']):
    pp,qq,rho,sigma=row['basis']
    subs={p:pp,q:qq,ta:tau,C3:c3,C5:c5}
    inverse=sp.expand(candidate.subs(subs))
    for n in (1,3,5):
        equal(f'inverse independent symbolic solve {index} a{n}',inverse.coeff(t,n),sym(row['u_in_a'][n]))
    if qq:
        # Integrate the independently solved inverse by the envelope relation,
        # instead of substituting the copied stationary-action formula.
        action=sp.integrate(-inverse/qq,(t,0,t))
        action_theta=sp.expand(action.subs(t,sp.I*t))
        for n in (2,4,6):
            equal(f'action from integrated envelope {index} theta{n}',action_theta.coeff(t,n),sym(row['action_in_theta'][n]))

# Direct constrained optimization of the six Lobachevsky Taylor jets. No use
# of the companion's projected inverse or corrected-quartic formula here.
E=sp.Matrix([[1,0,0],[0,1,0],[-1,-1,0],[0,0,1],[1,-1,1],[-1,1,-2]])
P=sp.Matrix([[0,-1,1],[2,-2,0]])
coordinates=sp.symbols('x0:3')
lam=sp.symbols('lam')
angles=E*sp.Matrix(coordinates)
jet=sum(-d*d/(2*sp.sqrt(3))+sp.Rational(2,9)*d**3-d**4/(9*sp.sqrt(3)) for d in angles)
tensors=algebra.tensor_checks(fixture)
for index,row in enumerate(tensors['slopes']):
    pp,qq=row['slope']
    L=sp.Matrix([[pp,qq]])*P
    stationarity=[sp.diff(jet,x)+lam*L[j] for j,x in enumerate(coordinates)]
    stationarity.append((L*sp.Matrix(coordinates))[0]-t)
    unknowns=list(coordinates)+[lam]
    solved={x:sp.S(0) for x in unknowns}
    for order in (1,2,3):
        coefficients=sp.symbols(f'd{order}_0:4')
        proposal={x:solved[x]+coefficients[j]*t**order for j,x in enumerate(unknowns)}
        equations=[sp.expand(eq.subs(proposal)).coeff(t,order) for eq in stationarity]
        result=sp.solve(equations,coefficients)
        solved={x:sp.expand(proposal[x].subs(result)) for x in unknowns}
    objective=sp.Poly(sp.expand(jet.subs(solved)),t)
    equal(f'constrained Lobachevsky theta2 {index}',objective.coeff_monomial(t**2),-1/(2*sym(row['chi'])))
    equal(f'constrained Lobachevsky theta3 {index}',objective.coeff_monomial(t**3),0)
    equal(f'constrained Lobachevsky theta4 {index}',24*objective.coeff_monomial(t**4),sym(row['corrected_quartic']))

c=periods.context(100)


def mq(value):
    value=Q(value)
    return c.mpf(value.numerator)/value.denominator


def hyp_series(a,b,cc,z,terms=700):
    coefficient=Q(1)
    total=c.mpc(1)
    zpower=c.mpc(1)
    for n in range(1,terms+1):
        coefficient *= (a+n-1)*(b+n-1)/((cc+n-1)*n)
        zpower *= z
        total += mq(coefficient)*zpower
    return total


def area_at(mu,z):
    f=periods.s_basis(c,mu,z)
    H=periods.s_hermitian(c,mu)
    return c.re((f.H*H*f)[0])


def laplacian5(fun,z,h):
    center=fun(z)
    total=c.mpf(0)
    for direction in (1,c.j):
        total += (-fun(z+2*h*direction)+16*fun(z+h*direction)
                  -30*center+16*fun(z-h*direction)-fun(z-2*h*direction))/(12*h*h)
    return total


for row in fixture['period_weights']:
    mu=algebra.weights(row['mu'],nonresonant=True)
    m1,m2,m3,m4=mu
    for zs in fixture['period_z']:
        zz=periods.point(c,zs)
        f=periods.s_basis(c,mu,zz)
        d0=1-m1-m3
        own0=hyp_series(1-m4,m3,m1+m3,zz)
        own1=zz**mq(d0)*hyp_series(m2,1-m1,1+d0,zz)
        label=f"{row['id']} {zs}"
        numeric('direct rational Taylor f0 '+label,own0,f[0],'1e-85')
        numeric('direct rational Taylor f1 '+label,own1,f[1],'1e-85')
        area0=area_at(mu,zz)
        gammas=c.fprod(c.gamma(mq(m))/c.gamma(1-mq(m)) for m in mu)
        density=4*c.pi*c.pi/gammas*abs(zz)**(-2*mq(m1+m3))*abs(1-zz)**(-2*mq(m2+m3))/area0**2
        derivative=-laplacian5(lambda z:c.log(area_at(mu,z)),zz,c.mpf('1e-9'))
        numeric('density direct 5-point real Laplacian '+label,derivative,density,'1e-32')

# Approach the fully balanced basis from both sides of delta0=0. delta1=0
# identically: use only the s basis; t/fusion rejection is checked explicitly.
balanced_records=[]
for zs in fixture['balanced_z']:
    zz=periods.point(c,zs)
    f=2*c.ellipk(zz)/c.pi
    g=2*c.ellipk(1-zz)/c.pi
    ell0=c.log(16)*f-c.pi*g
    area0=2*c.pi**2*c.re(f*c.conj(g))
    for sign in (1,-1):
        dd=Q(sign,10**10)
        mu=((1-dd)/2,(1+dd)/2,(1-dd)/2,(1+dd)/2)
        assert periods.delta(mu)==(dd,Q(0),Q(0))
        fs=periods.s_basis(c,mu,zz)
        H=periods.s_hermitian(c,mu)
        numeric(f'balanced cancellation h0 {zs} {sign}',H[0,0]-c.pi/mq(dd),c.pi*c.log(16),'1e-8')
        numeric(f'balanced cancellation h1 {zs} {sign}',H[1,1]+c.pi/mq(dd),c.pi*c.log(16),'1e-8')
        numeric(f'balanced logarithmic difference {zs} {sign}',(fs[1]-fs[0])/mq(dd),ell0,'1e-8')
        numeric(f'balanced limiting area {zs} {sign}',area_at(mu,zz),area0,'1e-8')
        for fn in (periods.fusion,periods.t_basis):
            try:
                fn(c,mu,*([zz] if fn is periods.t_basis else []))
            except ValueError:
                checks.append(f'balanced path singular {fn.__name__} {zs} {sign}')
            else:
                raise AssertionError('singular connection unexpectedly accepted')
        balanced_records.append({'z':zs,'delta':str(dd),'delta1':'0','delta_infinity':'0'})

# Probe valid cut-plane points outside the fixture disk, at modest precision.
branch_probes=[]
for zs in (['-1/3','1/10'],['5/4','-1/5']):
    result=periods.period_check(fixture['period_weights'][0],zs,60)
    branch_probes.append({'z':zs,'check_count':result['check_count'],
                          'max_scaled_residual':result['max_scaled_residual']})

source_checks=[]
for entry in manifest['source_files']:
    data=(ROOT/entry['path']).read_bytes()
    source_checks.append({'path':entry['path'],'sha256':sha256(data).hexdigest(),
                          'matches_initial_manifest':sha256(data).hexdigest()==entry['sha256']})
result={'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'exact_check_count':len(checks),'exact_checks':checks,
        'numerical_check_count':len(numerics),'numerical_checks':numerics,
        'balanced_path':balanced_records,'extra_branch_probes':branch_probes,
        'source_before':source_before,'source_after':source_state(),
        'review_script_sha256':script_hash_before,
        'source_checks_at_completion':source_checks,
        'scope':'Independent bounded symbolic derivations and finite numerical probes; no interval, global quantum, or filled-manifold certificate.'}
if result['source_before'] != result['source_after']:
    raise AssertionError('Companion sources changed during independent probes')
if script_hash_before != sha256(Path(__file__).read_bytes()).hexdigest():
    raise AssertionError('Reviewer script changed during independent probes')
with args.output.open('x') as handle:
    json.dump(result,handle,indent=2)
    handle.write('\n')
print(f'{len(checks)} independent exact/guard checks, {len(numerics)} numerical checks, {len(branch_probes)} extra branch probes passed')
