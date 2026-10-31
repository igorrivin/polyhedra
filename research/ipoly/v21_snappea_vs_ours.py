# SnapPea's kernel (Newton on the gluing equations, dense linear algebra, C) against the barrier method and plain Newton for the
# Casson-Rivin volume functional (Python, sparse KKT systems solved by SuperLU), on the same geometric triangulations.
import warnings; warnings.filterwarnings("ignore")
import sys, threading; sys.setrecursionlimit(1000000); threading.stack_size(1024*1024*1024)
import numpy as np, scipy.sparse as sp, time, sys, snappy, mpmath as mp
from scipy.sparse.linalg import splu
from scipy.optimize import linprog
from snappy.snap.t3mlite import Mcomplex
PAIR={3:0,12:0,5:1,10:1,9:2,6:2}                       # opposite edges E01/E23, E02/E13, E03/E12 -> the three angle pairs
Lob=np.vectorize(lambda x: float(mp.clsin(2,2*x))/2)
def equations(T):
    # tetrahedron equations and edge equations for the angles; the c redundancies (one per cusp) are removed EXACTLY by dropping
    # c edge rows chosen so that the remaining rows are independent (pivot columns of the c x E matrix of edge-ends per cusp)
    mc=Mcomplex(T); N=len(mc.Tetrahedra); rows=[];cols=[]; c=len(mc.Vertices); E=len(mc.Edges)
    for i,e in enumerate(mc.Edges):
        for co in e.Corners: rows.append(i); cols.append(3*co.Tetrahedron.Index+PAIR[co.Subsimplex])
    Ae=sp.csr_matrix((np.ones(len(rows)),(rows,cols)),shape=(E,3*N)); Ae.sum_duplicates()
    ends=np.zeros((c,E))
    for i,e in enumerate(mc.Edges):
        for v in e.Vertices: ends[v.Index,i]+=1
    from scipy.linalg import qr
    _,_,piv=qr(ends,pivoting=True); drop=set(int(j) for j in piv[:c]); keep=[i for i in range(E) if i not in drop]
    At=sp.csr_matrix((np.ones(3*N),(np.repeat(np.arange(N),3),np.arange(3*N))),shape=(N,3*N))
    A=sp.vstack([At,Ae[keep]]).tocsr(); b=np.r_[np.full(N,np.pi),np.full(len(keep),2*np.pi)]
    equations.check=(E,c,Ae[list(drop)],)
    return A,b,N
def snappea_time(T):
    t0=time.perf_counter(); T2=snappy.Triangulation(T); t1=time.perf_counter(); M=T.with_hyperbolic_structure(); v=float(M.volume()); t2=time.perf_counter()
    return (t2-t1)-(t1-t0), v, M.solution_type()
class Solver:
    def __init__(s,A,b): s.A=A.tocsr(); s.AT=A.T.tocsr(); s.b=b; s.n=A.shape[1]; s.m=A.shape[0]; s.eps=1e-10; s.nsolve=0; s.t_la=0
    def kkt(s,Hd,g):                                    # solve  H d + A^T lam = -g,  A d = 0  (A of full row rank)
        t0=time.perf_counter()
        K=sp.bmat([[sp.diags(Hd),s.AT],[s.A,None]],format="csc")
        d=splu(K).solve(np.r_[-g,np.zeros(s.m)])[:s.n]; s.t_la+=time.perf_counter()-t0; s.nsolve+=1; return d
    def lp_start(s):
        t0=time.perf_counter(); c=np.zeros(s.n+1); c[-1]=-1
        Aub=sp.hstack([-sp.identity(s.n),sp.csr_matrix(np.ones((s.n,1)))]); Aeq=sp.hstack([s.A,sp.csr_matrix((s.m,1))])
        r=linprog(c,A_ub=Aub,b_ub=np.zeros(s.n),A_eq=Aeq,b_eq=s.b,bounds=[(0,np.pi)]*s.n+[(0,None)],method="highs")
        return r.x[:s.n], r.x[-1], time.perf_counter()-t0
    def plain(s,x,tol=1e-9,maxit=300):
        t0=time.perf_counter(); s.nsolve=0; s.t_la=0
        for k in range(1,maxit+1):
            g=-np.log(2*np.sin(x)); d=s.kkt(1/np.tan(x),-g)      # ascent direction for V: H d = g with H = diag(cot)
            if np.abs(s.A@d).max()>1e-6: pass
            neg=d<0; tau=min(1.0,0.95*np.min(x[neg]/-d[neg])) if neg.any() else 1.0
            while True:
                if (-np.log(2*np.sin(x+tau*d)))@d>=-1e-14*abs(g@d) or tau<1e-16: break
                tau*=0.5
            x=x+tau*d
            if np.abs(d).max()<tol: break                        # the Newton step is negligible (quadratic convergence: V then accurate to ~tol^2)
        return x,k,time.perf_counter()-t0
    def barrier(s,x,mult=10.0,tol=1e-9):
        t0=time.perf_counter(); s.nsolve=0; s.t_la=0; t=1.0; steps=0
        while t<1e30:
            for it in range(100):
                g=t*np.log(2*np.sin(x))-1/np.tan(x); d=s.kkt(t/np.tan(x)+1/np.sin(x)**2,g); lam2=-g@d; steps+=1
                neg=d<0; tau=min(1.0,0.95*np.min(x[neg]/-d[neg])) if neg.any() else 1.0
                while True:
                    x2=x+tau*d
                    if (t*np.log(2*np.sin(x2))-1/np.tan(x2))@d<=1e-14*abs(g@d) or tau<1e-16: break
                    tau*=0.5
                x=x+tau*d
                if lam2<0.25**2: break
            v=x.copy(); ok=True
            for it in range(8):                                    # polish: plain Newton on V
                gv=-np.log(2*np.sin(v)); dv=s.kkt(1/np.tan(v),-gv); steps+=1
                if (v+dv).min()<=0: ok=False; break
                v=v+dv
                if np.abs(dv).max()<tol: break
            if ok and np.abs(dv).max()<tol: return v,steps,time.perf_counter()-t0
            t*=mult
        return x,steps,time.perf_counter()-t0
def compare(T,label):
    tsn,vol,st=snappea_time(T); A,b,N=equations(T); S=Solver(A,b); x0,marg,tlp=S.lp_start()
    xb,kb,tb=S.barrier(x0.copy()); lab=S.t_la; xp,kp,tp=S.plain(x0.copy()); lap=S.t_la
    print("%-34s N=%5d | SnapPea %7.3fs (%s) | LP %6.2fs | barrier %3d steps %7.2fs (LA %5.2fs) err %.0e | plain %3d steps %6.2fs err %.0e"
          %(label,N,tsn,"ok" if st.startswith("all tetrahedra positively") else st,tlp,kb,tb,lab,abs(Lob(xb).sum()-vol),kp,tp,abs(Lob(xp).sum()-vol))); sys.stdout.flush()
def main():
    which=sys.argv[1]
    if which=="covers":
        T=snappy.Triangulation(BASE_ISOSIG)
        for d in [int(v) for v in sys.argv[2:]]: compare(T.covers(d,cover_type='cyclic')[0],"cyclic cover of m015, degree %d"%d)
    if which=="links":
        import spherogram, random
        for k in [int(v) for v in sys.argv[2:]]:
            random.seed(k); L=spherogram.random_link(k); M=L.exterior()
            for tries in range(30):
                if M.solution_type().startswith("all tetrahedra positively"): break
                M.randomize()
            if not M.solution_type().startswith("all tetrahedra positively"): print("random link with %d crossings: no geometric triangulation found (%s)"%(k,M.solution_type())); continue
            compare(snappy.Triangulation(M),"random link, %d crossings"%k)

if __name__=="__main__":
    BASE_ISOSIG='m015'
    main()
