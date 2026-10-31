# Can a face angle be exponentially small while min excess d0 and max dihedral stay moderate?  (then kappa is exponentially large)
import numpy as np
from scipy.spatial import Delaunay
from collections import defaultdict
def ang(p,q,r):
    u=q-p; v=r-p; return np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))
for rho,m in ((3.0,5),(3.0,6),(4.0,6)):
    H=rho**m
    Q=[ (rho**k)*np.array([np.cos(ph),-np.sin(ph)]) for k,ph in zip(range(1,m+1),[2.2,0.9,2.0,1.1,2.1,1.0,1.9])]
    P=np.array([[0,0],[1,0],[0.5,H]]+Q)
    T=[tuple(sorted(t)) for t in Delaunay(P).simplices]; opp=defaultdict(list)
    for t in T:
        for k in range(3):
            i,j=[t[x] for x in range(3) if x!=k]; opp[(i,j)].append(ang(P[t[k]],P[i],P[j]))
    E=list(opp); ne=len(E); Es=np.array([sum(opp[e]) for e in E]); tri_masks=[sum(1<<E.index(e) for e in ((t[0],t[1]),(t[0],t[2]),(t[1],t[2]))) for t in T]
    best=9e9
    for mask in range(1,2**ne-1):
        ex=sum(Es[i] for i in range(ne) if mask>>i&1)-np.pi*sum(1 for tm in tri_masks if mask&tm==tm)
        if ex<best: best=ex
    w=[0.5*sum(1/np.tan(a) for a in opp[e]) for e in E if len(opp[e])==2]
    print("rho=%.0f n=%d: (0,1,2) is a triangle: %s; smallest face angle %.2e; min excess d0=%.3f; max dihedral %.3f; interior weights in [%.2e, %.2e]"
          %(rho,len(P),(0,1,2) in T,min(a for l in opp.values() for a in l),best,Es.max(),min(w),max(w)))
