"""Reviewer-owned alternate finite formulas; never an interval certificate.

The implementation modules are not imported. Inputs and observed answers are
read from the frozen report. Exact arithmetic and higher-precision comparisons
are recorded separately, and failures are retained before a nonzero exit.
"""
from pathlib import Path
from hashlib import sha256
from fractions import Fraction as F
from datetime import datetime, timezone
from itertools import product
import json
import sys
import time

import mpmath
import sympy as sp

HERE=Path(__file__).resolve().parent
SUBJECT=HERE/'subject-v1'
REPORT_PATH=SUBJECT/'author-result-70-110.json'
report=json.loads(REPORT_PATH.read_bytes())
fixture=report['fixture']
groups=report['groups']
ctx=mpmath.mp.clone()
ctx.dps=250
exact=[]
numeric=[]
failures=[]
coverage={}

def req(condition,message):
    if not condition:raise ArithmeticError(message)

def eq(group,label,actual,expected):
    residue=sp.simplify(sp.sympify(actual)-sp.sympify(expected))
    req(residue==0,group+': '+label+' exact residual '+str(residue))
    exact.append({'group':group,'check':label,'residual':str(residue)})

def close(group,label,actual,expected,digits,scale=None,positive=False):
    a,b=ctx.mpf(actual),ctx.mpf(expected)
    req(ctx.isfinite(a) and ctx.isfinite(b),group+': nonfinite '+label)
    if positive:req(a>0 and b>0,group+': nonpositive '+label)
    s=b if positive else ctx.mpf(1) if scale is None else ctx.mpf(scale)
    req(ctx.isfinite(s) and s>0,group+': invalid comparison scale')
    relative=abs(a-b)/s
    threshold=ctx.power(10,-(digits-15))
    req(relative<=threshold,group+': '+label+' residual '+ctx.nstr(relative,15))
    numeric.append({'group':group,'check':label,'requested_digits':digits,
                    'reference_digits':ctx.dps,'positive_relative':positive,
                    'scale':ctx.nstr(s,40),'absolute_residual':ctx.nstr(abs(a-b),40),
                    'scaled_residual':ctx.nstr(relative,40),'threshold':ctx.nstr(threshold,15)})

def mpfrac(value):
    f=F(str(value));return ctx.mpf(f.numerator)/f.denominator

def loops(key):
    for run in groups[key]['numerical']['runs']:
        yield run,run['requested_decimal_digits']

def q1():
    key='Q1_figure_eight'; z=sp.Symbol('z'); oracles={}
    for n in fixture['quantum']['figure_eight_N']:
        modulus=sp.Poly(sp.cyclotomic_poly(n,z),z)
        partial=sp.Poly(1,z); total=partial
        for k in range(1,n):
            factor=sp.Poly(2-z**k-z**(n-k),z).rem(modulus)
            partial=(partial*factor).rem(modulus)
            total+=partial
        eq(key,f'N={n} terminal product in Q[z]/Phi_N',partial.as_expr(),n*n)
        root=ctx.exp(2*ctx.pi*ctx.j/n)
        value=ctx.polyval([ctx.mpf(int(c)) for c in total.all_coeffs()],root)
        req(abs(ctx.im(value))/abs(value)<ctx.mpf('1e-220'),'cyclotomic reference imaginary residual')
        oracles[n]=ctx.re(value)
    for run,digits in loops(key):
        req([x['N'] for x in run['rows']]==fixture['quantum']['figure_eight_N'],'Q1 input coverage')
        for row in run['rows']:
            close(key,f'N={row["N"]} cyclotomic polynomial evaluation',row['positive_sum'],oracles[row['N']],digits,positive=True)
    coverage[key]='All41N values: exact cyclotomic quotient terminal product and polynomial evaluation, independently of sine/Habiro multiplication.'

def q2():
    key='Q2_klein_geometry'; x,y,z=sp.symbols('x y z')
    items={r['id']:r for r in fixture['quantum']['klein']['polyhedra']}
    for row in groups[key]['exact']['rows']:
        item=items[row['id']]
        for k,actual in enumerate(row['radial_moments_k0_through_4']):
            polynomial=sp.expand((x*x+y*y+z*z)**k)
            if item['kind']=='standard_simplex':
                value=sp.integrate(sp.integrate(sp.integrate(polynomial,(z,0,1-x-y)),(y,0,1-x)),(x,0,1))
            else:
                value=polynomial
                for var,bounds in zip((x,y,z),item['bounds']):
                    value=sp.integrate(value,(var,*map(sp.Rational,bounds)))
            eq(key,f'{row["id"]} nested integral M{2*k}',sp.sympify(actual),value)
        volume=sp.sympify(row['radial_moments_k0_through_4'][0])
        eq(key,row['id']+' curvature sum from volume',sp.sympify(row['curvature_sum']),-3*volume)
        geometry=row['geometry']
        req(len(geometry['edges'])==(6 if item['kind']=='standard_simplex' else 12),'true-edge count')
        if item['kind']=='box':
            bounds=[[sp.Rational(v) for v in interval] for interval in item['bounds']]
            vertices=[[sp.Rational(v) for v in point] for point in geometry['vertices']]
            for j,edge in enumerate(geometry['edges']):
                v,w=[vertices[i] for i in edge['vertices']]
                fixed=[i for i in range(3) if v[i]==w[i]]
                req(len(fixed)==2,'box edge fixed coordinates')
                axis=next(i for i in range(3) if i not in fixed)
                supports=[]
                for i in fixed:
                    req(v[i] in bounds[i],'box coordinate endpoint')
                    supports.append((-1 if v[i]==bounds[i][0] else 1)*v[i])
                eq(key,f'{row["id"]} edge{j} Cartesian length',sp.sympify(edge['L']),bounds[axis][1]-bounds[axis][0])
                eq(key,f'{row["id"]} edge{j} orthogonal face coefficient',sp.sympify(edge['b']),-supports[0]*supports[1])
        for j,truncation in enumerate(row['truncations']):
            r,t=map(sp.Rational,(truncation['r'],truncation['t']));m=truncation['m']
            exact_scalar=1/(1-t)**2-sum((k+1)*t**k for k in range(m+1))
            eq(key,f'{row["id"]} tail{j} rational remainder',sp.sympify(truncation['analytic_geometric_series_tail_bound']),r**3*volume*exact_scalar)
    coverage[key]='All15 radial moments by nested polynomial integration;24 Cartesian box edges; all27 exact scalar remainder evaluations.'

def q3():
    key='Q3_peripheral_filling'; a=sp.Symbol('a')
    tau,c3,c5=map(sp.Rational,fixture['quantum']['peripheral']['formal_v_coefficients'])
    for row in groups[key]['exact']['rows']:
        p,q,rho,sigma=row['basis'];D=p+q*tau
        independent=a/D-q*c3*a**3/D**4+(3*q*q*c3*c3/D**7-q*c5/D**6)*a**5
        eq(key,f'{p},{q} Lagrange reversion coefficients',sp.sympify(row['u_in_a_through_degree_six']),independent)
        eq(key,f'{p},{q} determinant',p*sigma-q*rho,1)
        u=sp.Symbol('u');G=sp.sympify(row['G'])
        eq(key,f'{p},{q} mixed derivative',sp.diff(G,u,a),-sp.Rational(1,2*q))
    for run,digits in loops(key):
        for point_index,point in enumerate(fixture['quantum']['peripheral']['shift_points']):
            u=mpfrac(point['u']);h=ctx.mpc(*map(mpfrac,point['hbar']))
            functions=[lambda x:ctx.mpf(1),lambda x:x,lambda x:x*x+2*x-3,lambda x:ctx.exp(ctx.mpf(2)*x/3)]
            for j,fun in enumerate(functions):
                expected=ctx.exp(ctx.re(u+h)/2)*abs(fun(u+h))
                observed=run['observations'][f'point {point_index}, function {j}: modulus']['value']
                close(key,f'point{point_index},function{j} independent modulus',observed,expected,digits,positive=True)
    coverage[key]='Four slopes: explicit Lagrange reversion and mixed kernel derivative; all12 operator modulus observations each precision.'

def q4():
    key='Q4_charge_curvature'
    for j,row in enumerate(groups[key]['exact']['rows']):
        b2=sp.Rational(row['b_squared']);mu=list(map(sp.Rational,row['mu']))
        gamma=sp.sympify(row['gamma']);beta=list(map(sp.sympify,row['beta']))
        eq(key,f'row{j} total deficits',sum(mu),2)
        eq(key,f'row{j} screening',row['s'],-1)
        eq(key,f'row{j} gamma squared',gamma**2,4*b2)
        for k,weight in enumerate(mu):
            eq(key,f'row{j} charge{k} square',beta[k]**2*b2,weight**2)
            req(0<weight<1 and 0<b2<1,'strict rational moment hypotheses')
            eq(key,f'row{j} first moment margin{k}',sp.sympify(row['first_moment_insertion_margins'][k]),(1-weight)/b2)
    coverage[key]='All9 rational weight/b-squared specializations, positive charge squares and exact first-moment margins; no GMC construction.'

def g1():
    key='G1_torus_unfolding'
    for run,digits in loops(key):
        for row in run['rows']:
            R=ctx.mpf(row['R']);q=ctx.exp(-R)
            tail=R*ctx.log1p(q)-ctx.polylog(2,-q)
            independent=ctx.pi**2/12-tail
            close(key,f'R={row["R"]} dilogarithm finite integral',row['finite_integral'],independent,digits,positive=True)
            close(key,f'R={row["R"]} positive omitted integral',row['signed_omitted_integral'],tail,digits,positive=True)
            req(tail<=(R+1)*q,'Fermi tail inequality')
        for row in run['alternating_sums']:
            exact_sum=sum((F((-1)**(n-1),n*n) for n in range(1,row['M']+1)),F(0))
            eq(key,f'M={row["M"]} Fraction finite Dirichlet sum',sp.Rational(row['exact_rational_sum']),sp.Rational(exact_sum.numerator,exact_sum.denominator))
    coverage[key]='All finite cutoffs independently evaluated by a dilogarithm primitive; exact rational alternating sums.'

def g2():
    key='G2_pants_traces'
    def mul(A,B):return [[sum(A[i][k]*B[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
    def tr(A):return A[0][0]+A[1][1]
    for j,row in enumerate(groups[key]['exact']['matrix_pairs']):
        A,B=[[[F(v) for v in line] for line in row[name]] for name in ('A','B')]
        inv=[[B[1][1],-B[0][1]],[-B[1][0],B[0][0]]]
        value=tr(mul(A,inv))-tr(A)*tr(B)+tr(mul(A,B))
        eq(key,f'pair{j} Fraction trace identity',sp.Rational(value.numerator,value.denominator),0)
    for row in groups[key]['exact']['torus_blocks']:
        t=sp.Rational(row['simple_trace'])
        req([x['topological_label'] for x in row['curves']]==['N_left','N_right','H'],'curve multiplicity labels')
        for j,target in enumerate((3*t,3*t,t*t+2)):eq(key,f't={t} trace{j}',sp.Rational(row['curves'][j]['trace']),target)
    coverage[key]='All6 signed matrix pairs by Fraction arithmetic and all4 three-label torus blocks.'

def g3():
    key='G3_figure_eight_kernel';old_dps=ctx.dps;ctx.dps=350
    try:
        for run,digits in loops(key):
            for row in run['rows']:
                x=mpfrac(row['x']);logx=ctx.log(x);terms=[]
                for j in range(row['N']+1):
                    q=36*ctx.exp(-2*logx)
                    h=q/(1+ctx.sqrt(1-q))
                    if j<row['N']:terms.append((-1)**j*h/ctx.power(2,j+1))
                    else:tail=h/ctx.power(2,row['N']+1)
                    logx=2*logx-ctx.log(9)+ctx.log1p(18*ctx.exp(-2*logx))
                partial=ctx.fsum(terms);prefix=f'x={row["x"]},N={row["N"]}'
                close(key,prefix+' log-coordinate F_N',row['F_N'],partial,digits,positive=True)
                close(key,prefix+' actual positive tail, not relative log',row['positive_B_N'],tail,digits,positive=True)
                absolute_log_error=abs(ctx.mpf(row['log_B_N'])-ctx.log(tail))
                numeric[-1]['absolute_log_difference']=ctx.nstr(absolute_log_error,40)
                req(absolute_log_error<=ctx.power(10,-(digits-15)),'absolute log accuracy insufficient for relative tail')
    finally:ctx.dps=old_dps
    coverage[key]='All28input/depth cases each precision: independent logarithmic iterate recursion; positive tails compared relatively and absolute log errors separately checked at350reference digits.'

def halfplane_distance(d,u,v):
    # Hyperboloid to upper-half-plane: x=X1/(X0-X2), y=1/(X0-X2).
    den1=ctx.cosh(u);den2=ctx.exp(-d)*ctx.cosh(v)
    x1,y1=ctx.sinh(u)/den1,1/den1
    x2,y2=ctx.sinh(v)/den2,1/den2
    separation=ctx.sqrt((x1-x2)**2+(y1-y2)**2)
    return 2*ctx.asinh(separation/(2*ctx.sqrt(y1*y2)))

def g4():
    key='G4_local_distance'
    for run,digits in loops(key):
        for index,row in enumerate(run['rows']):
            d=mpfrac(row['d']);u,v=map(mpfrac,row['u_v'])
            fun=lambda a,b:halfplane_distance(d,a,b)
            close(key,f'row{index} upper-half-plane distance',row['D'],fun(u,v),digits,positive=True)
            for j,order in enumerate(((1,0),(0,1))):
                close(key,f'row{index} half-plane gradient{j}',row['gradient'][j],ctx.diff(fun,(u,v),order),digits)
            for i,j,order in ((0,0,(2,0)),(1,1,(0,2)),(0,1,(1,1))):
                reference=ctx.diff(fun,(u,v),order)
                close(key,f'row{index} half-plane Hessian{i}{j}',row['Hessian'][i][j],reference,digits,scale=abs(reference),positive=i==j)
    coverage[key]='All20geometric points each precision using upper-half-plane asinh distance and its numerical derivatives, independently of Lorentz-acosh implementation.'

def g5():
    key='G5_seams_torus_holonomy'
    for run,digits in loops(key):
        for index,row in enumerate(run['torus_rows']):
            a,b,t=map(mpfrac,(row['a'],row['b'],row['tau']))
            A=ctx.sqrt((ctx.cosh(a)+ctx.cosh(b/2))/(ctx.cosh(a)-1))
            def reference(tau):
                T=A*ctx.cosh(tau/2)
                return 2*ctx.log(T+ctx.sqrt(T*T-1))
            x=2*ctx.cosh(a/2);y=2*A*ctx.cosh(t/2);z=2*A*ctx.cosh((a+t)/2)
            fricke=x*x+y*y+z*z-x*y*z-2
            close(key,f'row{index} Fricke commutator',fricke,-2*ctx.cosh(b/2),digits,scale=2*ctx.cosh(b/2))
            close(key,f'row{index} logarithmic trace length',row['length'],reference(t),digits,positive=True)
            close(key,f'row{index} logarithmic first derivative',row['first_derivative'],ctx.diff(reference,t),digits)
            close(key,f'row{index} logarithmic second derivative',row['second_derivative'],ctx.diff(reference,t,2),digits,positive=True)
        for row in run['large_cuff_minima']:
            old=ctx.dps;ctx.dps=600
            try:
                reference=2*ctx.log(ctx.coth(mpfrac(row['a'])/4))
                close(key,'a=1000 direct coth resolved at600digits',row['stable_length'],reference,digits,positive=True)
            finally:ctx.dps=old
    coverage[key]='All49torus cases each precision: Fricke trace identity and log-eigenvalue derivatives at250digits; extraa1000minimum from direct coth at600digits, no large-cuff derivative claim.'

def g6():
    key='G6_twist_coarea'
    for run,digits in loops(key):
        for index,row in enumerate(run['rows']):
            a,b=map(mpfrac,row['a_b']);s=mpfrac(row['s']);U=ctx.mpf(row['U'])
            A=ctx.sqrt((ctx.cosh(a)+ctx.cosh(b/2))/(ctx.cosh(a)-1))
            T=ctx.tanh(U/2)
            finite=2*A**(-s)*ctx.betainc(ctx.mpf('0.5'),s/2,0,T*T)
            tail=2*A**(-s)*ctx.betainc(s/2,ctx.mpf('0.5'),0,ctx.sech(U/2)**2)
            close(key,f'row{index} incomplete-beta finite integral',row['direct'],finite,digits,positive=True)
            close(key,f'row{index} incomplete-beta versus coarea',row['coarea'],finite,digits,positive=True)
            bound=ctx.mpf(row['analytic_tail'])
            req(tail>0 and tail<=bound*(1+ctx.mpf('1e-120')),'analytic coarea tail bound')
            numeric[-1]['independent_positive_tail']=ctx.nstr(tail,60)
            numeric[-1]['tail_to_analytic_bound']=ctx.nstr(tail/bound,40)
    coverage[key]='All30integrals each precision independently evaluated by incomplete beta; stable exact omitted-tail beta checked against analytic bound. No interval quadrature bound.'

def g7():
    key='G7_twist_partition'
    for run,digits in loops(key):
        for index,row in enumerate(run['terms']):
            a,u=mpfrac(row['a']),mpfrac(row['u'])
            q=ctx.exp(-u)
            # Translate integration to the centered window and factor out tiny q.
            scaled=ctx.quad(lambda w:ctx.exp(-w)/(1+q*ctx.exp(-w))**2,[-a/2,0,a/2])
            close(key,f'term{index} logistic-density integral',row['stable_H'],q*scaled,digits,positive=True)
        for index,row in enumerate(run['partitions']):
            a=mpfrac(row['a']);tau=mpfrac(row['reduced_tau_exact']);n=row['N'];L=(ctx.mpf(n)+ctx.mpf('0.5'))*a
            q=ctx.exp(-L)
            # Logistic CDF tails derived as integrals q*exp(+-tau)/(1+q*exp(+-tau)).
            tail=ctx.fsum(q*ctx.exp(sign*tau)/(1+q*ctx.exp(sign*tau)) for sign in (-1,1))
            close(key,f'partition{index} positive distribution tail',row['positive_logistic_tail'],tail,digits,positive=True)
    coverage[key]='All28Hterms each precision from translated logistic-density quadrature with tiny amplitude factored out; all101positive lattice tails checked.'

def g8():
    key='G8_endpoint_matching'
    for row in groups[key]['exact']['rows']:
        a=F(row['circumference']);left,right=[[F(v) for v in values] for values in row['base_endpoints']]
        differences=[(v-u)%a for u,v in zip(left,right)]
        req((len(set(differences))==1)==row['positions_match'],'endpoint cyclic shifts')
        for points,windings,lifted in zip((left,right),row['windings'],row['lifted_endpoints']):
            for k,(point,winding,value) in enumerate(zip(points,windings,lifted)):
                eq(key,row['id']+f' lifted endpoint{k}',sp.Rational(value),sp.Rational(point.numerator,point.denominator)+winding*sp.Rational(a.numerator,a.denominator))
    for run,digits in loops(key):
        for row in run['rows']:
            d,e,u,v,t,x=[mpfrac(row[k]) for k in ('d','e','u','v','tau','x')]
            derivative=ctx.diff(lambda a:halfplane_distance(d,u,a)+halfplane_distance(e,a+t,v),x)
            close(key,row['id']+' half-plane stationarity',row['derivative'],derivative,digits,scale=2)
    coverage[key]='Both exact endpoint/winding configurations and both stationarity examples each precision using alternate half-plane distance.'

def g9():
    key='G9_cusp_decoration'
    for index,row in enumerate(groups[key]['exact']['cusp_matrices']):
        q,ta,tb=map(F,(row['q'],row['t_a'],row['t_b']));c=(ta+tb)/q
        diagonal=ta/2;upper=(diagonal*diagonal-1)/c
        expected_B=[[diagonal,diagonal*q-upper],[-c,diagonal-c*q]]
        for i,j in product(range(2),repeat=2):
            target=expected_B[i][j]
            eq(key,f'cusp{index} B{i}{j} Fraction formula',sp.Rational(row['B'][i][j]),sp.Rational(target.numerator,target.denominator))
    for index,row in enumerate(groups[key]['exact']['triangles']):
        u,v,w=map(F,row['lambda_lengths']);H=2*(u*u+v*v+w*w)/(u*v*w)
        eq(key,f'triangle{index} decoration',sp.Rational(row['H']),sp.Rational(H.numerator,H.denominator))
    for run,digits in loops(key):
        for index,row in enumerate(run['torus_rows']):
            t,H=mpfrac(row['t']),mpfrac(row['H'])
            length=2*(ctx.log(2*t)-ctx.log(H))
            close(key,f'torus{index} signed decoration',row['signed_length'],length,digits,scale=1+abs(length))
            h=2*ctx.exp(-ctx.acosh(t/2))/t
            close(key,f'torus{index} eigenvalue h',row['weight'],h,digits,positive=True)
    coverage[key]='All27cusp matrices from independent Fraction formulas;3triangle decorations; all16torus signed lengths/weights each precision via hyperbolic eigenvalue form.'

def g10():
    key='G10_boundary_shadows'
    for run,digits in loops(key):
        for row in run['rows']:
            d=mpfrac(row['d']);q=ctx.exp(-d)
            integral=ctx.quad(lambda x:1/(1-q*q*x*x),[0,1])
            close(key,'d='+row['d']+' positive rational-integral shadow',row['positive_shadow'],4*q*integral,digits,positive=True)
    coverage[key]='All6shadows each precision from4q*integral_0^1(1-q^2x^2)^-1dx; tiny q is factored out, independent of log1p/coth evaluation.'

started=time.perf_counter()
for name in ('q1','q2','q3','q4','g1','g2','g3','g4','g5','g6','g7','g8','g9','g10'):
    try:
        globals()[name]()
        print(name+' passed',flush=True)
    except Exception as error:
        failures.append({'stage':name,'type':type(error).__name__,'message':str(error)})
        print(name+' FAILED '+repr(error),flush=True)
output=HERE/(sys.argv[1] if len(sys.argv)>1 else 'independent-oracles-v1.json')
payload={'status':'passed' if not failures else 'failed_review_probe_requires_investigation',
         'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
         'subject_result_sha256':sha256(REPORT_PATH.read_bytes()).hexdigest(),
         'script_sha256':sha256(Path(__file__).read_bytes()).hexdigest(),
         'exact_count':len(exact),'numerical_count':len(numeric),'coverage':coverage,
         'exact':exact,'numerical':numeric,'failures':failures,'elapsed_seconds':time.perf_counter()-started,
         'scope':'Alternate finite formulas with exact arithmetic or250/350/600-digit mpmath references. Same mpmath backend; no independent interval enclosure, global geometry, asymptotic proof or completeness claim.'}
with output.open('x') as file:json.dump(payload,file,indent=2,allow_nan=False);file.write('\n')
print(json.dumps({'status':payload['status'],'exact':len(exact),'numerical':len(numeric),'failures':failures,'elapsed_seconds':payload['elapsed_seconds']}))
if failures:raise SystemExit(1)
