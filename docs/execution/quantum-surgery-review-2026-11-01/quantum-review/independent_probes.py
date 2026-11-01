"""Independent bounded probes; no imports from the authored companion.
Exact symbolic checks and separately labelled mpmath observations, not spectral proofs.
"""
import json, hashlib, platform
from pathlib import Path
import sympy as sp
import mpmath as mp

OUT=Path(__file__).resolve().parent
exact=[]
def check(name, expr):
    val=sp.simplify(sp.expand(expr))
    if val != 0:
        raise AssertionError((name,val))
    exact.append(name)

A,X,Y,Z,u,v=sp.symbols('A X Y Z u v', nonzero=True)
a2=sp.series(4*sp.sin(A/8)**2,A,0,7).removeO()
x,y,z=[-2-A*q for q in (X,Y,Z)]
phi=x*x+y*y+z*z+x*y*z-2*a2*(x+y+z)+4*a2+a2*a2-4
p=sp.series(phi/A**2,A,0,3).removeO()
q0=X*X+Y*Y+Z*Z-2*(X*Y+X*Z+Y*Z)+1
q1=-X*Y*Z+(X+Y+Z)/8
check('Fricke coefficients through A^2',p-(q0+A*q1-A*A/768))
x0=1/(2*v); y0=(u*u+v*v)/(2*v); z0=((u-1)**2+v*v)/(2*v)
z1=(1-u)*(v*v-u*(1-u))/(16*v*v)
check('Heron quadric',q0.subs({X:x0,Y:y0,Z:z0}))
check('Z1 implicit coefficient',(sp.diff(q0,Z)*z1+q1).subs({X:x0,Y:y0,Z:z0}))
jac=sp.diff(x0,u)*sp.diff(y0,v)-sp.diff(x0,v)*sp.diff(y0,u)
check('Heron coordinate Jacobian',jac-u/(2*v**3))
corr=-(x0*y0-sp.Rational(1,8)-2*z1)/(2*(x0+y0-z0))
check('WP first correction',corr+(1+u*u+v*v)/(16*v))

# Virasoro Gram coefficients, independent of Euler/connection calculation.
b=sp.Rational(3,5); Q=b+1/b; c=1+6*Q*Q
mu=list(map(sp.Rational,['1/3','2/3','1/4','3/4']))
al=[m/(2*b) for m in mu]
D=lambda a:a*(Q-a)
h1,h2,h3,h4=map(D,al)
d0=1-mu[0]-mu[2]
for j in (0,1):
    hi=D(al[0]+al[2]+j*b)
    left=hi+h3-h1; right=hi+h2-h4
    n1=left*right/(2*hi)
    gram=sp.Matrix([[4*hi+c/2,6*hi],[6*hi,4*hi*(2*hi+1)]])
    vl=sp.Matrix([hi+2*h3-h1,left*(left+1)])
    vr=sp.Matrix([hi+2*h2-h4,right*(right+1)])
    n2=(vl.T*gram.inv()*vr)[0]
    aa,bb,cc=(1-mu[3],mu[2],mu[0]+mu[2]) if j==0 else (mu[1],1-mu[0],1+d0)
    ee=mu[1]*mu[2]/(2*b*b)
    check(f'Virasoro level 1 channel {j}',n1-(aa*bb/cc+ee))
    check(f'Virasoro level 2 channel {j}',n2-(aa*(aa+1)*bb*(bb+1)/(2*cc*(cc+1))+ee*aa*bb/cc+ee*(ee+1)/2))

# Gram identities at an exact radical fixture, all four j,k cases.
th=[sp.pi*m for m in mu]; ch=sp.Rational(99,101); sh=sp.Rational(20,101)
def cosshift(t,n):
    return sp.expand_trig(sp.cos(t))*ch+(-n)*sp.expand_trig(sp.sin(t))*sh if n else sp.cos(t)
def G(j,k):
    return sp.Matrix([[1,cosshift(th[1]+th[2],k),sp.cos(th[1]),cosshift(th[3],-1)],
      [cosshift(th[1]+th[2],k),1,sp.cos(th[2]),sp.cos(th[0])],
      [sp.cos(th[1]),sp.cos(th[2]),1,cosshift(th[0]+th[2],j)],
      [cosshift(th[3],-1),sp.cos(th[0]),cosshift(th[0]+th[2],j),1]])
for j in (0,1):
 for k in (0,1):
    g=G(j,k)
    check(f'Gram zero cofactor first {j}{k}',g.minor_submatrix(j,j).det())
    check(f'Gram zero cofactor second {j}{k}',g.minor_submatrix(3-k,3-k).det())
    if (j,k)==(0,0):
        ii,jj=0,3; eps=cosshift(th[3],-1)-sp.cos(th[3]); fac=sp.sin(th[2])**2
    elif (j,k)==(0,1):
        ii,jj=0,2; eps=sp.cos(th[1])-cosshift(th[1],1);fac=sp.sin(th[0])**2
    elif (j,k)==(1,0):
        ii,jj=1,3; eps=sp.cos(th[0])-cosshift(th[0],1);fac=sp.sin(th[1])**2
    else:
        ii,jj=1,2; eps=sp.cos(th[2])-cosshift(th[2],1);fac=(sp.sin(th[3])*ch-sp.cos(th[3])*sh)**2
    check(f'Gram determinant {j}{k}',g.det()+fac*eps**2)
    check(f'Gram off diagonal cofactor {j}{k}',g.cofactor(ii,jj)+fac*eps)

# Exact fold polynomial and rational local derivatives.
a,uu=sp.symbols('a uu')
poly=a**8*(a*a-2*a+3)*uu**2-3*a**4*(a-1)**2*uu+3*a*a-2*a+1
check('Regular saddle polynomial factorization',(1+a**3*uu)**4-(1-uu)*(1-a**4*uu)**3-uu*(a+1)**2*poly)
check('Regular saddle discriminant',sp.discriminant(poly,uu)+a**8*(a+1)**2*(3*a*a-2*a+3))
ae=(1+2*sp.sqrt(2)*sp.I)/3; ue=(241+22*sp.sqrt(2)*sp.I)/243
check('Fold root lift',ue*ae**5-1)
check('Fold double root',poly.subs({a:ae,uu:ue}))
check('Fold double root derivative',sp.diff(poly,uu).subs({a:ae,uu:ue}))
svv=-uu/(1-uu)-3*a**4*uu/(1-a**4*uu)-4*a**3*uu/(1+a**3*uu)
svvv=sp.I*uu*sp.diff(svv,uu)
sveta=-12*(a**3*uu/(1+a**3*uu)+a**4*uu/(1-a**4*uu))
check('Fold second derivative',svv.subs({a:ae,uu:ue}))
check('Fold cubic derivative 54i',svvv.subs({a:ae,uu:ue})-54*sp.I)
check('Fold mixed derivative 18sqrt2i',sveta.subs({a:ae,uu:ue})-18*sp.sqrt(2)*sp.I)
ell=sp.symbols('ell', positive=True)
cosh=sp.cosh(ell)
beta=sp.acos(cosh/(1+cosh)); eta=sp.acos(cosh/(1+2*cosh))
area=sp.series(4*sp.pi-12*beta,ell,0,6).removeO()
t=sp.series(sp.acos(sp.Rational(1,3))-eta,ell,0,6).removeO()
check('Regular area Taylor',area-(sp.sqrt(3)*ell**2-sp.sqrt(3)*ell**4/8))
check('Regular dihedral Taylor',t-(ell**2/(12*sp.sqrt(2))-23*ell**4/(1152*sp.sqrt(2))))
W=sp.integrate(3*ell*sp.diff(t,ell),(ell,0,ell))
check('Schlafli volume Taylor',W-(ell**3/(6*sp.sqrt(2))-23*ell**5/(480*sp.sqrt(2))))

mp.mp.dps=80
num=[]
def observe(name,err,tol='1e-65'):
    e=abs(err); ok=e<mp.mpf(tol)
    num.append({'name':name,'absolute_residual':mp.nstr(e,12),'tolerance':tol,'passed':ok})
    if not ok: raise AssertionError((name,e))

def setup(mu):
    m1,m2,m3,m4=mu; d0=1-m1-m3; d1=1-m2-m3
    g=mp.gamma;gr=lambda x:g(x)/g(1-x)
    M=mp.matrix([[g(1-d0)*g(d1)/(g(m1)*g(1-m2)),g(1-d0)*g(-d1)/(g(m3)*g(1-m4))],
                 [g(1+d0)*g(d1)/(g(1-m3)*g(m4)),g(1+d0)*g(-d1)/(g(1-m1)*g(m2))]])
    hs=[mp.pi*gr(d0)/(gr(m2)*gr(m4)),mp.pi*gr(-d0)/(gr(m1)*gr(m3))]
    ht=[mp.pi*gr(d1)/(gr(m1)*gr(m4)),mp.pi*gr(-d1)/(gr(m2)*gr(m3))]
    return d0,d1,M,hs,ht
fixtures=[['.2','.6','.35','.85'],['.7','.55','.4','.35'],['.25','.6','.55','.6'],['.6','.55','.6','.25']]
zs=[mp.mpc('.3','.2'),mp.mpc('.7','-.4')]
for n,ss in enumerate(fixtures):
    ms=list(map(mp.mpf,ss));m1,m2,m3,m4=ms;d0,d1,M,hs,ht=setup(ms)
    f=lambda zz:mp.matrix([mp.hyp2f1(1-m4,m3,m1+m3,zz),zz**d0*mp.hyp2f1(m2,1-m1,1+d0,zz)])
    g=lambda zz:mp.matrix([mp.hyp2f1(1-m4,m3,m2+m3,1-zz),(1-zz)**d1*mp.hyp2f1(1-m2,m1,1+d1,1-zz)])
    observe(f'Fusion determinant {n}',mp.det(M)+d0/d1)
    observe(f'Hermitian congruence {n}',mp.norm(M.T*mp.diag(hs)*M-mp.diag(ht)))
    for iz,zz in enumerate(zs):
        observe(f'Period connection {n} z{iz}',mp.norm(f(zz)-M*g(zz)))
        ff=f(zz);df=mp.matrix([mp.diff(lambda z:f(z)[j],zz) for j in (0,1)])
        observe(f'Wronskian {n} z{iz}',ff[0]*df[1]-df[0]*ff[1]-d0*zz**(-m1-m3)*(1-zz)**(-m2-m3))
    # TV finite rescaling, sign-sensitive real normalization.
    ns=[mp.gamma(1-d0)*mp.gamma(m2)*mp.gamma(m4),mp.gamma(1+d0)*mp.gamma(m1)*mp.gamma(m3)]
    nt=[mp.gamma(1-d1)*mp.gamma(m1)*mp.gamma(m4),mp.gamma(1+d1)*mp.gamma(m2)*mp.gamma(m3)]
    sig=[mp.sin(mp.pi*m) for m in ms];d=[mp.sin(mp.pi*x) for x in (d0,d1)]
    B=mp.matrix([[sig[1],-sig[3]],[sig[2],-sig[0]]])/d[1]
    observe(f'TV analytic finite matrix {n}',mp.norm(mp.diag([1/x for x in ns])*M*mp.diag(nt)-B))
    U=mp.sign(d[1])/mp.sqrt(abs(d[0]*d[1]))*mp.matrix([[mp.sqrt(sig[0]*sig[1]),-mp.sqrt(sig[2]*sig[3])],[mp.sqrt(sig[2]*sig[3]),-mp.sqrt(sig[0]*sig[1])]])
    observe(f'TV absolute-root matrix {n}',mp.norm(mp.diag([mp.sqrt(abs(x)) for x in hs])*M*mp.diag([1/mp.sqrt(abs(x)) for x in ht])-U))
    observe(f'TV indefinite congruence {n}',mp.norm(U.T*mp.diag([mp.sign(d[0]),-mp.sign(d[0])])*U-mp.diag([mp.sign(d[1]),-mp.sign(d[1])])))

# Balanced log derivative, symmetric difference avoids O(delta) bias.
zz=mp.mpc('.31','.17');delta=mp.mpf('1e-25')
f=mp.hyp2f1(mp.mpf('.5'),mp.mpf('.5'),1,zz)
g=mp.hyp2f1(mp.mpf('.5'),mp.mpf('.5'),1,1-zz)
logsol=mp.log(16)*f-mp.pi*g

def coalescence(d):
    # mu1=mu3=(1-d)/2, mu2=mu4=(1+d)/2
    q=(1-d)/2;r=(1+d)/2
    ff0=mp.hyp2f1(q,q,1-d,zz)
    ff1=zz**d*mp.hyp2f1(r,r,1+d,zz)
    return ff1-ff0
observe('Balanced derivative block',(coalescence(delta)-coalescence(-delta))/(2*delta)-logsol,'1e-47')
L=mp.log(16);F=mp.matrix([[L,-1],[L*L-mp.pi**2,-L]])/mp.pi
H=mp.matrix([[2*mp.pi*L,-mp.pi],[-mp.pi,0]])
observe('Logarithmic involution',mp.norm(F*F-mp.eye(2)))
observe('Logarithmic Hermitian congruence',mp.norm(F.T*H*F-H))
etaE=mp.acos(mp.mpf(1)/3);ae=mp.exp(1j*etaE);ue=ae**-5
sv=-1j*mp.log(1-ue)-3j*mp.log(1-ae**4*ue)+4j*mp.log(1+ae**3*ue)-2*mp.pi
observe('Fold first derivative on principal local branch',sv)
# Exact quantum shift quotient is checked as a sine identity and in a small-b sequence.
rat=(1+ae**3*ue)**4/((1-ae**4*ue)**3*(1-ue))
for bb in [mp.mpf('.01'),mp.mpf('.003'),mp.mpf('.001')]:
    alpha=(mp.pi-etaE)/(2*mp.pi*bb);w=(4*mp.pi-5*etaE)/(2*mp.pi*bb);Q=bb+1/bb
    quotient=(2*mp.sin(mp.pi*bb*(w-3*alpha)))**4/((2*mp.sin(mp.pi*bb*(4*alpha-w-bb)))**3*(2*mp.sin(mp.pi*bb*(2*Q-w-bb))))
    num.append({'name':'Quantum sine quotient limit','b':str(bb),'absolute_error_to_classical':mp.nstr(abs(quotient-rat),12),'status':'observed convergence, not a tail bound'})
result={'scope':'Independent bounded exact algebra and floating-point checks; no companion import, spectral evaluation, rigorous interval enclosure or global Airy proof.', 'python':platform.python_version(),'sympy':sp.__version__,'mpmath':mp.__version__,'dps':mp.mp.dps,'exact_checks':exact,'numerical_checks':num,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
(OUT/'independent-probe-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'exact_passes':len(exact),'numerical_passes':sum(x.get('passed',False) for x in num),'convergence_observations':sum('b' in x for x in num),'max_tested_residual':max((float(x['absolute_residual']) for x in num if 'absolute_residual' in x),default=0),'output':str(OUT/'independent-probe-results.json')},indent=2))
