# Adaptive truncation for Rivin's problem (Section 8): unknown alpha_min, guess a, halve on failure.
# Stage(a): log-barrier path following for  -t V(alpha(u)) - sum log(alpha_c(u)-a)  on P'_a; every Newton system is a Laplacian.
# After each centering a "polish" by pure Newton on V is tried; success = interior critical point (|grad V| tiny, all angles >= a).
import numpy as np
from scipy.spatial import Delaunay
from scipy.optimize import linprog
from collections import defaultdict
def setup(P):
    T=[]
    for t in Delaunay(P).simplices:
        a,b,c=P[t]; 
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0: t=t[[0,2,1]]
        T.append(tuple(int(x) for x in t))
    ang=lambda p,q,r: np.arccos(np.clip(np.dot(q-p,r-p)/np.linalg.norm(q-p)/np.linalg.norm(r-p),-1,1))
    corners=[(i,j,k,ang(P[k],P[i],P[j])) for (a,b,c) in T for (i,j,k) in ((a,b,c),(b,c,a),(c,a,b))]
    cnt=defaultdict(int)
    for (i,j,k,_) in corners: cnt[frozenset((i,j))]+=1
    bv=set(v for e,c in cnt.items() if c==1 for v in e); I=[v for v in range(len(P)) if v not in bv]; idx={v:m for m,v in enumerate(I)}
    B=np.zeros((len(corners),len(I)))
    for r,(i,j,k,_) in enumerate(corners):
        if i in idx: B[r,idx[i]]+=1
        if j in idx: B[r,idx[j]]-=1
    true=np.array([c[3] for c in corners]); var=np.abs(B).sum(1)>0
    return corners,B,true,var,cnt
def maxmargin(corners,true,var,cnt):
    nc=len(corners); c=np.zeros(nc+1); c[-1]=-1; Aeq=[]; beq=[]
    for t in range(nc//3):
        r=np.zeros(nc+1); r[3*t:3*t+3]=1; Aeq.append(r); beq.append(np.pi)
    opp=defaultdict(list)
    for r,(i,j,k,_) in enumerate(corners): opp[frozenset((i,j))].append(r)
    for e,l in opp.items():
        r=np.zeros(nc+1); r[l]=1; Aeq.append(r); beq.append(true[l].sum())          # prescribed dihedral (or boundary) angle
    Aub=[]; bub=[]
    for r in range(nc):
        if var[r]: q=np.zeros(nc+1); q[r]=-1; q[-1]=1; Aub.append(q); bub.append(0)
    res=linprog(c,A_ub=np.array(Aub),b_ub=np.array(bub),A_eq=np.array(Aeq),b_eq=np.array(beq),bounds=[(0,np.pi)]*nc+[(0,None)],method="highs")
    return res.x[:nc],res.x[-1]
def run(P,label,schedule="halve"):
    corners,B,true,var,cnt=setup(P); Bv=B[var]; ref,s=maxmargin(corners,true,var,cnt)
    al=lambda u:(ref+B@u)[var]; gV=lambda u: Bv.T@(-np.log(2*np.sin(al(u))))
    LH=lambda u,t,a: Bv.T@((t/np.tan(al(u))+1/(al(u)-a)**2)[:,None]*Bv)
    amin_true=true[var].min(); L=Bv.T@((1/np.tan(true[var]))[:,None]*Bv)/2
    print("[%s] "%schedule+"%s: %d interior vertices, %d variable corners; true alpha_min=%.2e; max margin s*=%.3e; cond L_II(sol)=%.2e (%.1f bits)"%(label,B.shape[1],var.sum(),amin_true,s,np.linalg.cond(L),np.log2(np.linalg.cond(L))))
    u=np.zeros(B.shape[1]); a=s/2; total=0; traj_min=np.inf; stage=0
    while True:
        stage+=1; t=1.0; steps=0; ok=False
        while t<=1e3/a**2 and not ok:
            for it in range(60):                                   # centering: damped Newton on -tV - sum log(alpha-a)
                x=al(u); g=Bv.T@(t*np.log(2*np.sin(x))-1/(x-a)); H=LH(u,t,a); d=np.linalg.solve(H,-g); lam=np.sqrt(-g@d); steps+=1
                tau=1.0
                while (al(u+tau*d)-a).min()<=0: tau*=0.5
                while True:
                    x2=al(u+tau*d); g2=Bv.T@(t*np.log(2*np.sin(x2))-1/(x2-a))
                    if g2@d<=1e-14 or tau<1e-14: break
                    tau*=0.5
                u=u+tau*d; traj_min=min(traj_min,al(u).min())
                if lam<0.25: break
            v=u.copy(); good=True                                   # polish: pure Newton on V
            for it in range(8):
                x=al(v)
                if x.min()<a: good=False; break
                g=gV(v); 
                if np.abs(g).max()<1e-11: break
                v=v+np.linalg.solve(Bv.T@((1/np.tan(x))[:,None]*Bv),g); steps+=1
                if al(v).min()<=0: good=False; break
            if good and al(v).min()>=a and np.abs(gV(v)).max()<1e-11: ok=True; u=v
            t*=8
        total+=steps; print("   stage %d: a=%.3e  Newton steps %4d  %s"%(stage,a,steps,"SUCCESS" if ok else "failed -> halve a"))
        if ok: break
        a = a/2 if schedule=="halve" else a*a
    err=np.abs(al(u)-true[var]).max()
    print("   total Newton steps %d; max angle error %.1e; smallest angle along the whole trajectory %.2e (final a=%.2e, true alpha_min=%.2e)"%(total,err,traj_min,a,amin_true))
rng=np.random.default_rng(7); run(rng.random((40,2)),"random n=40")
rho,m=3.0,6; Q=[(rho**k)*np.array([np.cos(ph),-np.sin(ph)]) for k,ph in zip(range(1,m+1),[2.2,0.9,2.0,1.1,2.1,1.0])]
run(np.array([[0,0],[1,0],[0.5,rho**m]]+Q),"small-angle example (rho=3, m=6)")
run(np.array([[0,0],[1,0],[0.5,rho**m]]+Q),"small-angle example (rho=3, m=6)","square")
rho=4.0; Q4=[(rho**k)*np.array([np.cos(ph),-np.sin(ph)]) for k,ph in zip(range(1,m+1),[2.2,0.9,2.0,1.1,2.1,1.0])]
run(np.array([[0,0],[1,0],[0.5,rho**m]]+Q4),"small-angle example (rho=4, m=6)")
run(np.array([[0,0],[1,0],[0.5,rho**m]]+Q4),"small-angle example (rho=4, m=6)","square")
rng=np.random.default_rng(11); 
th=np.linspace(0,2*np.pi,13)[:-1]; ring=np.c_[np.cos(th),np.sin(th)]; inner=0.55*np.c_[np.cos(th+0.26),np.sin(th+0.26)]
run(np.vstack([ring,inner,[[0.03,0.02]]]),"well-shaped mesh (two rings + centre)")
