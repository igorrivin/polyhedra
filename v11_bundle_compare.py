# Vanilla damped Newton versus adaptive truncation on the punctured-torus bundles R^m L^m (where a naive vanilla run had needed ~200 steps).
import numpy as np, time, sys
from scipy.optimize import linprog
exec(open('v8_torus_bundles.py').read().split('for word,vol in')[0])      # build(), start()
def lp_start(C,c0):
    N=C.shape[1]; res=linprog(np.r_[np.zeros(N),-1],A_ub=np.c_[-C,np.ones(len(c0))],b_ub=c0,bounds=[(0,np.pi)]*N+[(0,None)],method="highs"); return res.x[:N],res.x[-1]
def vanilla(C,c0,w,tol=1e-9,maxit=1500):
    traj=np.inf; T0=time.perf_counter()
    for it in range(maxit):
        x=c0+C@w; traj=min(traj,x.min()); g=C.T@(-np.log(2*np.sin(x)))
        if np.abs(g).max()<tol: break
        d=np.linalg.solve((C.T*(1/np.tan(x)))@C,g); Cd=C@d; neg=Cd<0; tau=min(1.0,0.95*np.min(x[neg]/-Cd[neg])) if neg.any() else 1.0
        while True:
            x2=x+tau*Cd; g2=C.T@(-np.log(2*np.sin(x2)))
            if g2@d>=-1e-14*abs(g@d) or tau<1e-16: break
            tau*=0.5
        w=w+tau*d
    return it,time.perf_counter()-T0,traj,(c0+C@w).min()
def adaptive(C,c0,w,s,schedule,tol=1e-9):
    a=s/2; total=0; stages=0; T0=time.perf_counter()
    amin_floor=1e-13
    while True:
        stages+=1; t=1.0; ok=False; prev=None
        while t<=1e3/a**2 and not ok:
            for it in range(80):
                x=c0+C@w; g=C.T@(t*np.log(2*np.sin(x))-1/(x-a)); d=np.linalg.solve((C.T*(t/np.tan(x)+1/(x-a)**2))@C,-g); lam=np.sqrt(max(-g@d,0)); total+=1
                Cd=C@d; neg=Cd<0; tau=min(1.0,0.95*np.min((x[neg]-a)/-Cd[neg])) if neg.any() else 1.0
                while True:
                    x2=x+tau*Cd; g2=C.T@(t*np.log(2*np.sin(x2))-1/(x2-a))
                    if g2@d<=1e-14*abs(g@d) or tau<1e-16: break
                    tau*=0.5
                w=w+tau*d
                if lam<0.25: break
            v=w.copy(); good=True
            for it in range(8):
                x=c0+C@v
                if x.min()<a: good=False; break
                g=C.T@(-np.log(2*np.sin(x)))
                if np.abs(g).max()<tol: break
                v=v+np.linalg.solve((C.T*(1/np.tan(x)))@C,g); total+=1
                if (c0+C@v).min()<=0: good=False; break
            if good and (c0+C@v).min()>=a and np.abs(C.T@(-np.log(2*np.sin(c0+C@v)))).max()<tol: ok=True; w=v; break
            slack=(c0+C@w-a).min()
            if prev is not None and slack<0.1*a and prev/slack>3: break
            prev=slack; t*=8
        if ok: break
        a = a/2 if schedule=="halve" else a*a
        if a<amin_floor: return stages,total,time.perf_counter()-T0,float("nan")
    return stages,total,time.perf_counter()-T0,a
print("word R^m L^m: alpha_min | LP margin s | vanilla from LP point: steps, time, smallest angle on trajectory | vanilla from the naive start of v8 | adaptive squaring: stages/steps/time | adaptive halving")
for m in [int(v) for v in sys.argv[1:]]:
    word="R"*m+"L"*m; C,c0=build(word); w0,s=lp_start(C,c0)
    it,T,traj,amin=vanilla(C,c0,w0.copy()); it2,T2,traj2,_=vanilla(C,c0,start(word))
    st,tot,Ta,af=adaptive(C,c0,w0.copy(),s,"square"); sth,toth,Tah,afh=adaptive(C,c0,w0.copy(),s,"halve")
    print("m=%3d: %.2e | %.2e | %4d steps %.2fs traj-min %.1e | naive start: %4d steps %.2fs traj-min %.1e | square %d/%d/%.2fs (a=%.0e) | halve %d/%d/%.2fs"%(m,amin,s,it,T,traj,it2,T2,traj2,st,tot,Ta,af,sth,toth,Tah)); sys.stdout.flush()
