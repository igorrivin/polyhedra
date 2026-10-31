# Casson-Rivin volume maximization on actual ideal triangulations (from SnapPy), by the barrier method with the log-sine barrier.
# Angle structures: per tetrahedron alpha+beta+gamma=pi, per edge (rows of the gluing matrix) sum = 2pi; no cusp equations.
import warnings; warnings.filterwarnings("ignore")
import numpy as np, snappy, mpmath as mp, sys, time
from scipy.linalg import null_space
from scipy.optimize import linprog
Lob=np.vectorize(lambda x: float(mp.clsin(2,2*x))/2)
def run(M,label,tmax=1e12):
    N=M.num_tetrahedra(); G_=M.gluing_equations(); eq=np.array([[float(G_[i,j]) for j in range(3*N)] for i in range(N)])        # edge equations only
    Aeq=np.vstack([np.kron(np.eye(N),np.ones((1,3))),eq]); beq=np.r_[np.full(N,np.pi),np.full(N,2*np.pi)]; nc=3*N
    c=np.zeros(nc+1); c[-1]=-1
    res=linprog(c,A_ub=np.c_[-np.eye(nc),np.ones(nc)],b_ub=np.zeros(nc),A_eq=np.c_[Aeq,np.zeros(len(beq))],b_eq=beq,bounds=[(0,np.pi)]*nc+[(0,None)])
    if res.status!=0 or res.x[-1]<1e-7:
        print("%-34s N=%2d  %-42s no strict angle structure"%(label,N,M.solution_type())); return
    x=res.x[:nc]; Z=null_space(Aeq); t=1.0; steps=0; T0=time.perf_counter()
    while t<=tmax:
        for it in range(200):
            grad=t*np.log(2*np.sin(x))-1/np.tan(x); H=t/np.tan(x)+1/np.sin(x)**2
            gz=Z.T@grad; dz=np.linalg.solve(Z.T@(H[:,None]*Z),-gz); lam=np.sqrt(max(-gz@dz,0)); d=Z@dz; steps+=1; tau=1.0
            while (x+tau*d).min()<=0: tau*=0.5
            if lam>0.25: tau=min(tau,1/(1+lam))
            x=x+tau*d
            if lam<1e-3: break
        t*=10
    V=Lob(x).sum(); ang=x.reshape(N,3); flat=int(((ang.min(1)<1e-4)).sum())
    print("%-34s N=%2d  %-42s LP margin %.3f | %3d Newton steps %.2fs | max V = %.8f  vol(M) = %.8f  diff %.1e | smallest angle %.1e, tetrahedra with an angle < 1e-4: %d"
          %(label,N,M.solution_type(),res.x[-1],steps,time.perf_counter()-T0,V,float(M.volume()),float(M.volume())-V,x.min(),flat))
    if flat:
        bad=ang[ang.min(1)<1e-4]; print("      angles of the degenerate tetrahedra:",np.round(bad,5).tolist()[:4])
for name in ("m004","m009","m015","m125","s776","v1000","t05000","o9_10000"):
    run(snappy.Manifold(name),name)
# other triangulations of the same manifolds (random Pachner moves): look for non-geometric ones that still carry strict angle structures
import random
found=0
for name in ("m015","m125","s776","v1000","m203"):
    for seed in range(40):
        M=snappy.Manifold(name); 
        for _ in range(seed%5+1): M.randomize()
        if M.solution_type()!="all tetrahedra positively oriented" and M.num_tetrahedra()<=14:
            run(M,"%s, retriangulated #%d"%(name,seed)); found+=1
        if found>=6: break
    if found>=6: break
