from pathlib import Path
import json, hashlib, sys
import sympy as sp
import mpmath as mp
OUT=Path(__file__).parent
exact=[]
float_results=[]
def exact_check(name,expr):
    reduced=sp.factor(expr)
    if reduced!=0: raise RuntimeError((name,str(reduced)))
    exact.append(name)
def record(name,observed,reference,tol,scale=1):
    err=abs(observed-reference)/scale
    if err>tol: raise RuntimeError((name,mp.nstr(err,12),mp.nstr(tol,12)))
    float_results.append({'name':name,'dps':mp.mp.dps,'scaled_residual':mp.nstr(err,12),'tolerance':mp.nstr(tol,12)})
# Hyperbolic substitutions make derivative numerator identities rational.
x,y,q=sp.symbols('x y q',positive=True)
C=(q+1/q)/2; sd=(q-1/q)/2
cu=(x+1/x)/2; su=(x-1/x)/2; cv=(y+1/y)/2; sv=(y-1/y)/2
z=C*cu*cv-su*sv
zu=sp.diff(z,x)*x; zv=sp.diff(z,y)*y
zuu=sp.diff(zu,x)*x; zvv=sp.diff(zv,y)*y; zuv=sp.diff(zu,y)*y
exact_check('G4 Huu numerator',zuu*(z*z-1)-z*zu*zu-sd*sd*z*cv*cv)
exact_check('G4 Hvv numerator',zvv*(z*z-1)-z*zv*zv-sd*sd*z*cu*cu)
exact_check('G4 Huv numerator',zuv*(z*z-1)-z*zu*zv+sd*sd*cu*cv)
exact_check('G4 Hessian determinant numerator',sd**4*((z*cv**2)*(z*cu**2)-cu**2*cv**2)-sd**4*cu**2*cv**2*(z*z-1))
# Finite F_N cancellation for formal, independent symbols h_0,...,h_N.
for n in (1,2,3,4,12,40):
    h=sp.symbols('h:'+str(n+1))
    fn=sum((-1)**k*sp.Rational(1,2**(k+1))*h[k] for k in range(n))
    fn_shift=sum((-1)**k*sp.Rational(1,2**(k+1))*h[k+1] for k in range(n))
    exact_check('G3 formal telescope N='+str(n),2*fn+fn_shift-h[0]-(-1)**(n-1)*sp.Rational(1,2**n)*h[n])
# Six exact independent determinant-one signed matrices.
matrices=[sp.Matrix([[1,1],[1,2]]),sp.Matrix([[2,1],[1,1]]),sp.Matrix([[-1,2],[1,-3]]),sp.Matrix([[3,-2],[-1,1]]),sp.Matrix([[-2,1],[1,-1]]),sp.Matrix([[1,-3],[2,-5]])]
for i,a in enumerate(matrices):
    b=matrices[(i+2)%len(matrices)]
    exact_check('G2 determinant '+str(i),a.det()-1)
    exact_check('G2 trace polarization '+str(i),sp.trace(a*b.inv())-sp.trace(a)*sp.trace(b)+sp.trace(a*b))
# Cusp matrices and triangle mutation identities; rational independent construction.
for qv,ta,tb in [(1,2,3),(2,3,5),(3,5,2)]:
    lower=sp.Rational(ta+tb,qv)
    A=sp.Matrix([[sp.Rational(ta,2),(sp.Rational(ta,2)**2-1)/lower],[lower,sp.Rational(ta,2)]])
    P=sp.Matrix([[1,qv],[0,1]])
    B=A.inv()*P
    exact_check('G9 A determinant '+str((qv,ta,tb)),A.det()-1)
    exact_check('G9 B trace '+str((qv,ta,tb)),sp.trace(B)+tb)
for uv,vv,wv in [(1,1,1),(1,2,3),(2,3,5)]:
    u,v,w=map(sp.Rational,(uv,vv,wv)); H=2*(u*u+v*v+w*w)/(u*v*w)
    tx,ty,tz=H*u/2,H*v/2,H*w/2
    exact_check('G9 Markov '+str((u,v,w)),tx*tx+ty*ty+tz*tz-tx*ty*tz)
    up=(v*v+w*w)/u
    exact_check('G9 flip H '+str((u,v,w)),2*(up*up+v*v+w*w)/(up*v*w)-H)
# Exact uniform-density window partition with boundary contacts.
for av,tv in [(sp.Rational(1,2),0),(sp.Rational(2),1),(sp.Rational(3,5),sp.Rational(3,10))]:
    total=0
    for n in range(-10,11):
        center=tv+n*av; total+=max(0,min(1,center+av/2)-max(-1,center-av/2))/2
    exact_check('G7 uniform window '+str((av,tv)),total-1)
for dps in (70,110):
    mp.mp.dps=dps; tol=mp.mpf(10)**(-(dps-15))
    def hs(t):return (4/t**2)/(1+mp.sqrt(1-4/t**2))
    def D(d,u,v):
        p=[mp.cosh(u),mp.sinh(u),mp.mpf(0)]
        r=[mp.cosh(d)*mp.cosh(v),mp.sinh(v),mp.sinh(d)*mp.cosh(v)]
        return mp.acosh(p[0]*r[0]-p[1]*r[1]-p[2]*r[2])
    for d,u,v in [(mp.mpf('.03'),1,-2),(mp.mpf('.5'),0,0),(mp.mpf(2),-3,2),(mp.mpf(7),4,4)]:
        z=mp.cosh(D(d,u,v)); den=mp.sqrt(z*z-1)
        analytic=mp.sinh(d)**2/den**3*mp.matrix([[z*mp.cosh(v)**2,-mp.cosh(u)*mp.cosh(v)],[-mp.cosh(u)*mp.cosh(v),z*mp.cosh(u)**2]])
        numerical=mp.matrix([[mp.diff(lambda t:D(d,t,v),u,2),mp.diff(lambda t:mp.diff(lambda r:D(d,t,r),v),u)],[mp.diff(lambda t:mp.diff(lambda r:D(d,r,t),u),v),mp.diff(lambda t:D(d,u,t),v,2)]])
        record('G4 Hessian '+str((d,u,v)),mp.norm(numerical-analytic),0,tol)
    for a,b,u in [(mp.mpf('.2'),0,0),(mp.mpf(1),mp.mpf('.7'),mp.mpf('.5')),(mp.mpf(3),4,-4)]:
        delta=(1+mp.cosh(b/2))/(2*mp.sinh(a/2)**2); A=mp.sqrt(1+delta)
        M=mp.matrix([[mp.exp(a/2),0],[0,mp.exp(-a/2)]])
        def BM(t):return mp.matrix([[mp.exp(t/2)*A,mp.exp(t/2)*mp.sqrt(delta)],[mp.exp(-t/2)*mp.sqrt(delta),mp.exp(-t/2)*A]])
        B=BM(u); comm=M*B*(M**-1)*(B**-1)
        record('G5 commutator '+str((a,b,u)),comm[0,0]+comm[1,1],-2*mp.cosh(b/2),tol)
        def length(t):
            B=BM(t);return 2*mp.acosh((B[0,0]+B[1,1])/2)
        Q=delta+(1+delta)*mp.sinh(u/2)**2
        record('G5 second derivative '+str((a,b,u)),mp.diff(length,u,2),A*delta*mp.cosh(u/2)/(2*Q**mp.mpf('1.5')),tol)
        # An independent finite coarea integral, split at A and powers of ten.
        U=mp.mpf(12); end=A*mp.sinh(U/2)
        for s in (mp.mpf('.5'),mp.mpf(2),mp.mpf(3)):
            direct=mp.quad(lambda t:mp.cosh(length(t)/2)**(-s),[-U,0,U])
            lengthside=mp.quad(lambda y:4*(A*A+y*y)**(-(s+1)/2),[0,A,end])
            record('G6 coarea '+str((a,b,s)),direct,lengthside,tol)
            gamma_value=2*mp.sqrt(mp.pi)*mp.gamma(s/2)/(A**s*mp.gamma((s+1)/2))
            bound=2**(s+2)/(s*A**s)*mp.exp(-s*U/2)
            if not(-tol<=gamma_value-direct<=bound+tol):raise RuntimeError('G6 tail failure')
            if s==2:record('G6 finite s2 '+str((a,b)),direct,4*mp.tanh(U/2)/A**2,tol)
    for R in (12,30,60):
        finite=mp.quad(lambda t:t*mp.exp(-t)/(1+mp.exp(-t)),[0,1,R])
        remainder=mp.pi**2/12-finite;bound=(R+1)*mp.exp(-R)
        if not(-tol<=remainder<=bound+tol):raise RuntimeError('G1 finite tail')
        float_results.append({'name':'G1 finite Fermi tail R='+str(R),'dps':dps,'remainder':mp.nstr(remainder,16),'analytic_tail':mp.nstr(bound,16),'status':'numerical comparison not enclosure'})
    for xs in ('6.00000000000000000001','6.01','9','11','30','1000'):
        xx=mp.mpf(xs)
        for n in (4,12,40):
            orbit=[xx]
            for _ in range(n):orbit.append(orbit[-1]**2/9+2)
            terms=[hs(t/3) for t in orbit]
            fn=mp.fsum((-1)**k*mp.mpf(2)**(-k-1)*terms[k] for k in range(n))
            shifted=mp.fsum((-1)**k*mp.mpf(2)**(-k-1)*terms[k+1] for k in range(n))
            rhs=(-1)**(n-1)*mp.mpf(2)**(-n)*terms[n]
            record('G3 finite residual '+xs+' N='+str(n),2*fn+shifted-terms[0],rhs,tol,terms[0])
            bound=mp.mpf(2)**(-n-1)*terms[n]
            if not(terms[0]/4-bound-tol<=fn<=terms[0]/2+bound+tol):raise RuntimeError('G3 positivity bracket')
            if abs(rhs)<tol*terms[0]:float_results[-1]['conditioning']='cancellation-limited; formal coefficient identity supplies exact equality'
            float_results[-1]['log_analytic_tail']=mp.nstr(mp.log(bound),20)
    for a,tau,n in [(mp.mpf('.1'),mp.mpf('.05'),0),(mp.mpf('.7'),mp.mpf('-.14'),12),(mp.mpf(7),mp.mpf('2.59'),150)]:
        def H(u):
            e=mp.exp(-abs(u));return 2*mp.sinh(a/2)*e/(1+2*mp.cosh(a/2)*e+e*e)
        P=mp.fsum(H(tau+k*a) for k in range(-n,n+1)); L=(n+mp.mpf('.5'))*a
        tail=mp.exp(-L-tau)/(1+mp.exp(-L-tau))+mp.exp(-L+tau)/(1+mp.exp(-L+tau))
        record('G7 finite partition '+str((a,tau,n)),P+tail,1,tol)
        float_results[-1]['positive_tail']=mp.nstr(tail,18)
        if not(tail>0 and tail<=2*mp.cosh(tau)*mp.exp(-L)+tol*tail):raise RuntimeError('G7 tail')
    for ds in ('.1','.7','2','8','100','1000'):
        d=mp.mpf(ds); ex=mp.exp(-d)
        left=2*mp.log1p(2*ex/(1-ex)); zz=2*ex/(1+ex*ex)
        right=mp.log1p(zz)-mp.log1p(-zz)
        record('G10 stable shadow d='+ds,left,right,tol,4*ex)
        if not(left>0):raise RuntimeError('G10 positivity')
    for H in (mp.mpf('.1'),mp.mpf(1),mp.mpf(20)):
        t=mp.mpf(3); d=2*mp.log(2*t/H)
        record('G9 decoration '+str(H),1-mp.sqrt(1-16*mp.exp(-d)/H**2),hs(t),tol)
    # A position match can fail the independent first-variation requirement.
    def total(v):return D(mp.mpf('.5'),mp.mpf('.8'),v)+D(mp.mpf('.7'),v,0)
    derivative=mp.diff(total,0)
    if abs(derivative)<mp.mpf('.01'):raise RuntimeError('G8 lost nonstationary example')
    float_results.append({'name':'G8 matched x=0 with shifted incoming endpoint','dps':dps,'derivative':mp.nstr(derivative,25),'interpretation':'positions match but directions do not'})
result={'status':'all_independent_finite_probes_passed','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'python':sys.version,'sympy':sp.__version__,'mpmath':mp.__version__,'exact_check_count':len(exact),'exact_checks':exact,'floating_check_count':len(float_results),'floating_checks':float_results,'limitations':['Finite representative probes do not implement the full companion contract.','Floating values, derivatives and quadrature are not interval certificates.','Exact symbolic identities are distinct from sampled inequalities and analytic tail bounds.','No complete curve enumeration or global identity was computed.']}
(OUT/'independent-probe-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['exact_checks','floating_checks']},indent=2))
