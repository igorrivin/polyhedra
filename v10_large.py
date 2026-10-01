# Larger instances of Rivin's problem with adaptive truncation (Remark 8.1): sparse linear algebra, cheap failure detection, timings.
import numpy as np, scipy.sparse as sp, time, sys
from scipy.sparse.linalg import splu
from scipy.spatial import Delaunay
from scipy.optimize import linprog
def lawson(P,tri,tol=1e-12):
    # repair Qhull's output at extreme scale ratios: flip every interior edge whose opposite angles add up to more than pi
    T=[list(map(int,t)) for t in tri]; emap={}
    for ti,t in enumerate(T):
        for r in range(3): emap[(t[r],t[(r+1)%3])]=ti
    def ang(k,i,j):
        v1=P[i]-P[k]; v2=P[j]-P[k]; return np.arctan2(abs(v1[0]*v2[1]-v1[1]*v2[0]),v1@v2)
    stack=[e for e in emap if e[0]<e[1]]; flips=0
    while stack:
        i,j=stack.pop()
        if (i,j) not in emap or (j,i) not in emap: continue
        t1,t2=emap[(i,j)],emap[(j,i)]; k=[v for v in T[t1] if v!=i and v!=j][0]; l=[v for v in T[t2] if v!=i and v!=j][0]
        if ang(k,i,j)+ang(l,i,j)>np.pi+tol:
            del emap[(i,j)],emap[(j,i)]; T[t1]=[i,l,k]; T[t2]=[l,j,k]; flips+=1
            for e,tt in (((i,l),t1),((l,k),t1),((k,i),t1),((l,j),t2),((j,k),t2),((k,l),t2)): emap[e]=tt
            stack+=[(i,l),(l,j),(j,k),(k,i)]
    return np.array(T),flips
def setup(P0):
    P=P0
    while True:
        tri=Delaunay(P).simplices.copy(); used=np.unique(tri)
        if len(used)==len(P): break
        P=P[used]
    a,b,c=P[tri[:,0]],P[tri[:,1]],P[tri[:,2]]
    neg=((b[:,0]-a[:,0])*(c[:,1]-a[:,1])-(b[:,1]-a[:,1])*(c[:,0]-a[:,0]))<0; tri[neg]=tri[neg][:,[0,2,1]]
    tri,nfl=lawson(P,tri); setup.info=(len(P0)-len(P),nfl)
    F=len(tri); n=len(P); I_=np.concatenate([tri[:,r] for r in range(3)]); J_=np.concatenate([tri[:,(r+1)%3] for r in range(3)]); K_=np.concatenate([tri[:,(r+2)%3] for r in range(3)])
    v1=P[I_]-P[K_]; v2=P[J_]-P[K_]; ang=np.arctan2(np.abs(v1[:,0]*v2[:,1]-v1[:,1]*v2[:,0]),(v1*v2).sum(1))
    key=np.minimum(I_,J_).astype(np.int64)*n+np.maximum(I_,J_); uk,inv,cntk=np.unique(key,return_inverse=True,return_counts=True)
    bd=np.zeros(n,bool); be=uk[cntk==1]; bd[be//n]=True; bd[be%n]=True; idx=-np.ones(n,int); idx[~bd]=np.arange((~bd).sum())
    rows=np.arange(3*F); mi=idx[I_]>=0; mj=idx[J_]>=0
    B=sp.csr_matrix((np.r_[np.ones(mi.sum()),-np.ones(mj.sum())],(np.r_[rows[mi],rows[mj]],np.r_[idx[I_][mi],idx[J_][mj]])),shape=(3*F,(~bd).sum()))
    var=(mi|mj); return F,ang,inv,len(uk),B,var
def maxmargin(F,ang,inv,E,var):
    nc=3*F; t_rows=np.tile(np.arange(F),3); Aeq=sp.vstack([sp.csr_matrix((np.ones(nc),(t_rows,np.arange(nc))),shape=(F,nc+1)),sp.csr_matrix((np.ones(nc),(inv,np.arange(nc))),shape=(E,nc+1))]).tocsr()
    beq=np.r_[np.full(F,np.pi),np.bincount(inv,weights=ang,minlength=E)]; vi=np.nonzero(var)[0]; m=len(vi)
    Aub=sp.csr_matrix((np.r_[-np.ones(m),np.ones(m)],(np.r_[np.arange(m),np.arange(m)],np.r_[vi,np.full(m,nc)])),shape=(m,nc+1))
    c=np.zeros(nc+1); c[-1]=-1
    res=linprog(c,A_ub=Aub,b_ub=np.zeros(m),A_eq=Aeq,b_eq=beq,bounds=[(0,np.pi)]*nc+[(0,None)],method="highs-ipm")
    return res.x[:nc],res.x[-1]
class Run:
    def __init__(s,P,label):
        t0=time.perf_counter(); s.F,s.true,inv,E,B,var=setup(P); s.t_mesh=time.perf_counter()-t0
        dih=np.bincount(inv,weights=s.true); empty=int((np.abs(B).sum(0)==0).sum())
        s.valid = empty==0 and dih.max()<=np.pi+1e-9
        if sum(setup.info): print("\n[%s: Qhull dropped %d points (removed) and %d edges had to be flipped to make the triangulation Delaunay]"%(label,setup.info[0],setup.info[1]),end="")
        if not s.valid: print("\n%s: INVALID INSTANCE (Qhull dropped %d points, max dihedral - pi = %.1e): skipped"%(label,empty,dih.max()-np.pi)); return
        t0=time.perf_counter(); ref,s.s=maxmargin(s.F,s.true,inv,E,var); s.t_lp=time.perf_counter()-t0
        s.Bv=B[var].tocsr(); s.BvT=s.Bv.T.tocsr(); s.ref=ref[var]; s.truev=s.true[var]; s.label=label; s.nI=B.shape[1]
        print("\n%s: %d points, %d interior, %d variable angles; alpha_min=%.2e; LP margin s=%.2e;  mesh %.2fs, LP %.2fs"%(label,len(P)-setup.info[0],s.nI,var.sum(),s.truev.min(),s.s,s.t_mesh,s.t_lp)); sys.stdout.flush()
    def al(s,u): return s.ref+s.Bv@u
    def solve(s,dvec,g):
        t0=time.perf_counter(); H=(s.BvT@sp.diags(dvec)@s.Bv).tocsc()
        try: lu=splu(H,permc_spec="MMD_AT_PLUS_A",diag_pivot_thresh=0.0,options=dict(SymmetricMode=True))
        except RuntimeError: lu=splu(H)                     # fall back to partial pivoting
        d=lu.solve(-g); s.t_la+=time.perf_counter()-t0; s.nsolve+=1
        if not np.all(np.isfinite(d)): raise RuntimeError("non-finite solve")
        return d
    def adaptive(s,schedule,detect=True):
        u=np.zeros(s.nI); a=s.s/2; s.t_la=0; s.nsolve=0; T0=time.perf_counter(); log=[]
        while True:
            t=1.0; steps=0; ok=False; prev=None; why="budget"
            while t<=1e3/a**2 and not ok:
                for it in range(80):
                    x=s.al(u); g=s.BvT@(t*np.log(2*np.sin(x))-1/(x-a)); d=s.solve(t/np.tan(x)+1/(x-a)**2,g); lam=np.sqrt(max(-g@d,0)); steps+=1
                    Bd=s.Bv@d; neg=Bd<0; tau=min(1.0,0.95*np.min((x[neg]-a)/-Bd[neg])) if neg.any() else 1.0
                    while True:
                        x2=x+tau*Bd; g2=s.BvT@(t*np.log(2*np.sin(x2))-1/(x2-a))
                        if g2@d<=1e-14*abs(g@d)+1e-300 or tau<1e-16: break
                        tau*=0.5
                    u=u+tau*d
                    if lam<0.25: break
                v=u.copy(); good=True
                for it in range(8):
                    x=s.al(v)
                    if x.min()<a: good=False; break
                    g=s.BvT@(-np.log(2*np.sin(x)))
                    if np.abs(g).max()<1e-10: break
                    v=v+(-s.solve(1/np.tan(x),g)); steps+=1          # Newton step for maximizing V:  (B^T cot B) delta = grad V
                    if s.al(v).min()<=0: good=False; break
                if good and s.al(v).min()>=a and np.abs(s.BvT@(-np.log(2*np.sin(s.al(v))))).max()<1e-10: ok=True; u=v; break
                slack=(s.al(u)-a).min()
                if detect and prev is not None and slack<0.1*a and prev/slack>3: why="detected"; break
                prev=slack; t*=8
            log.append((a,steps,ok,why)); s.last_a=a
            if ok: break
            a = a/2 if schedule=="halve" else a*a
        T=time.perf_counter()-T0; err=np.abs(s.al(u)-s.truev).max(); st=[l[1] for l in log]
        print("   %-6s %s: %2d stages, %4d Newton steps (per stage min/median/max %d/%d/%d; last %d), final a=%.1e, time %.2fs (linear algebra %.2fs = %.1f ms/solve), max angle error %.0e"
              %(schedule,"detect" if detect else "nodetect",len(log),sum(st),min(st),int(np.median(st)),max(st),st[-1],a,T,s.t_la,1e3*s.t_la/max(s.nsolve,1),err)); sys.stdout.flush()
def vanilla(s,maxit=2000,tol=1e-10,frac=0.95):
    # plain damped Newton for maximizing V on P(Delta): no truncation, no barrier; line search keeps the angles positive
    u=np.zeros(s.nI); s.t_la=0; s.nsolve=0; T0=time.perf_counter(); traj=np.inf; small=0; taus=[]
    for it in range(maxit):
        x=s.al(u); traj=min(traj,x.min()); g=s.BvT@(-np.log(2*np.sin(x)))
        if np.abs(g).max()<tol: break
        d=-s.solve(1/np.tan(x),g); Bd=s.Bv@d; neg=Bd<0
        tau=min(1.0,frac*np.min(x[neg]/-Bd[neg])) if neg.any() else 1.0
        while True:
            x2=x+tau*Bd; g2=s.BvT@(-np.log(2*np.sin(x2)))
            if g2@d>=-1e-14*abs(g@d)-1e-300 or tau<1e-16: break
            tau*=0.5
        u=u+tau*d; taus.append(tau)
    T=time.perf_counter()-T0; err=np.abs(s.al(u)-s.truev).max(); taus=np.array(taus)
    print("   vanilla Newton: %4d steps (%d of them damped, smallest step length %.1e), time %.2fs (%.1f ms/solve), smallest angle along the trajectory %.2e (alpha_min %.2e), max angle error %.0e%s"
          %(it,int((taus<1).sum()),taus.min() if len(taus) else 1,T,1e3*s.t_la/max(s.nsolve,1),traj,s.truev.min(),err,"" if it<maxit-1 else "  [NOT CONVERGED]")); sys.stdout.flush()
Run.vanilla=vanilla
def penalized(s,kind="log",mult=8.0,t0=1.0,tol=1e-10):
    # maximize t*V - sum phi(alpha_c), phi = -log (barrier, a=0) or phi = alpha^-2 ; t increased by `mult`; polish by undamped Newton on V after each centering. No truncation level, no restarts.
    if kind=="log": ph1=lambda x:-1/x; ph2=lambda x:1/x**2
    elif kind=="logsin": ph1=lambda x:-1/np.tan(x); ph2=lambda x:1/np.sin(x)**2
    else:           ph1=lambda x:-2/x**3; ph2=lambda x:6/x**4
    u=np.zeros(s.nI); s.t_la=0; s.nsolve=0; T0=time.perf_counter(); t=t0; steps=0; traj=np.inf; ok=False
    while not ok and t<1e40:
        for it in range(80):
            x=s.al(u); traj=min(traj,x.min()); g=s.BvT@(t*np.log(2*np.sin(x))+ph1(x)); d=s.solve(t/np.tan(x)+ph2(x),g); lam=np.sqrt(max(-g@d,0)); steps+=1
            Bd=s.Bv@d; neg=Bd<0; tau=min(1.0,0.95*np.min(x[neg]/-Bd[neg])) if neg.any() else 1.0
            while True:
                x2=x+tau*Bd; g2=s.BvT@(t*np.log(2*np.sin(x2))+ph1(x2))
                if g2@d<=1e-14*abs(g@d)+1e-300 or tau<1e-16: break
                tau*=0.5
            u=u+tau*d
            if lam<0.25: break
        v=u.copy(); good=True; pm=np.inf
        for it in range(8):
            x=s.al(v); pm=min(pm,x.min()); g=s.BvT@(-np.log(2*np.sin(x)))
            if np.abs(g).max()<tol: break
            v=v+(-s.solve(1/np.tan(x),g)); steps+=1
            if s.al(v).min()<=0: good=False; break
        if good and np.abs(s.BvT@(-np.log(2*np.sin(s.al(v))))).max()<tol: ok=True; u=v; traj=min(traj,pm)
        t*=mult
    T=time.perf_counter()-T0; err=np.abs(s.al(u)-s.truev).max()
    print("   penalty %-4s x%-4g: %4d Newton steps, time %.2fs, smallest angle along the trajectory %.2e (alpha_min %.2e; ratio %.2f), max angle error %.0e"%(kind,mult,steps,T,traj,s.truev.min(),traj/s.truev.min(),err)); sys.stdout.flush()
Run.penalized=penalized
def gadget(m,per=50,rho=2.0,seed=0):
    rng=np.random.default_rng(seed); pts=[[0,0],[1,0],[0.5,rho**m]]
    for k in range(1,m+1):
        ph=np.pi+0.3+(np.pi-0.6)*rng.random(per); r=rho**k*(0.8+0.4*rng.random(per)); pts+=list(np.c_[r*np.cos(ph),r*np.sin(ph)])
    return np.array(pts)
if __name__=="__main__":
    which=sys.argv[1]
    if which=="random":
        for n in (1000,4000,16000):
            R=Run(np.random.default_rng(1).random((n,2)),"random n=%d"%n)
            for sch in ("halve","square"): R.adaptive(sch)
    if which=="vanilla":
        k=100; g=np.stack(np.meshgrid(np.arange(k),np.arange(k)),-1).reshape(-1,2).astype(float); g+=0.25*np.random.default_rng(2).random(g.shape)
        insts=[("random n=%d"%n,np.random.default_rng(1).random((n,2))) for n in (1000,4000,16000)]+[("jittered grid 100x100",g)]+[("gadget m=%d p=%d"%(m,p),gadget(m,per=p)) for m,p in ((10,50),(16,50),(19,50),(16,500))]
        for lab,P in insts:
            R=Run(P,lab)
            if R.valid: R.vanilla()
    if which in ("pen1","pen2"):
        k=100; g=np.stack(np.meshgrid(np.arange(k),np.arange(k)),-1).reshape(-1,2).astype(float); g+=0.25*np.random.default_rng(2).random(g.shape)
        insts=[("random n=%d"%n,np.random.default_rng(1).random((n,2))) for n in (1000,4000,16000)]+[("jittered grid 100x100",g)] if which=="pen1" else [("gadget m=%d p=%d"%(m,p),gadget(m,per=p)) for m,p in ((10,50),(16,50),(19,50),(16,500))]
        for lab,P in insts:
            R=Run(P,lab)
            if not R.valid: continue
            R.vanilla(frac=0.95); R.vanilla(frac=0.5)
            for kind,mult in (("log",8.0),("log",100.0),("pow2",100.0)): R.penalized(kind,mult)
    if which=="logsin":
        k=100; g=np.stack(np.meshgrid(np.arange(k),np.arange(k)),-1).reshape(-1,2).astype(float); g+=0.25*np.random.default_rng(2).random(g.shape)
        for lab,P in [("random n=4000",np.random.default_rng(1).random((4000,2))),("jittered grid 100x100",g),("gadget m=16 p=50",gadget(16)),("gadget m=19 p=50",gadget(19)),("gadget m=16 p=500",gadget(16,per=500))]:
            R=Run(P,lab)
            if R.valid:
                for kind in ("log","logsin"): R.penalized(kind,100.0)
    if which=="frac":
        k=100; g=np.stack(np.meshgrid(np.arange(k),np.arange(k)),-1).reshape(-1,2).astype(float); g+=0.25*np.random.default_rng(2).random(g.shape)
        for lab,P in (("jittered grid 100x100",g),("random n=4000",np.random.default_rng(1).random((4000,2)))):
            R=Run(P,lab)
            for fr in (0.95,0.5,0.25): print("  fraction-to-boundary %.2f:"%fr,end=""); R.vanilla(frac=fr)
    if which=="biggadget":
        for m,per in ((16,500),(19,200)):
            R=Run(gadget(m,per=per),"gadget m=%d, %d points per scale"%(m,per))
            if not R.valid: continue
            for sch in ("halve","square"):
                try: R.adaptive(sch)
                except RuntimeError as e: print("   %-6s: breakdown (%s)"%(sch,e))
    if which=="gadget":
        for m in [int(x) for x in sys.argv[2:]]:
            R=Run(gadget(m),"gadget m=%d (rho=2, 50 points per scale)"%m)
            if not R.valid: continue
            for sch in ("halve","square"):
                try: R.adaptive(sch)
                except RuntimeError as e: print("   %-6s: breakdown in double precision (%s)"%(sch,e))
            if m==16: R.adaptive("halve",detect=False)
    if which=="grid":
        k=100; g=np.stack(np.meshgrid(np.arange(k),np.arange(k)),-1).reshape(-1,2).astype(float); g+=0.25*np.random.default_rng(2).random(g.shape)
        R=Run(g,"jittered grid 100x100"); R.adaptive("halve"); R.adaptive("square")
