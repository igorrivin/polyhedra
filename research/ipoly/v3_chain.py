import numpy as np
from scipy.spatial import Delaunay
from collections import defaultdict
def ang(p,q,r):
    u=q-p; v=r-p; return np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))
def chain(n,d0,delta):
    P=[np.array([0.,0.]),np.array([1.,0.])]; older,newer=0,1; ref=np.array([0.5,-1.0])  # first apex goes above the x-axis
    for k in range(1,n-1):                      # triangle T_k, apex = vertex k+1
        s=(np.pi-d0)/2-(n-k)*delta; l=np.pi-d0-s
        q,c=P[older],P[newer]; L=np.linalg.norm(c-q); d=(c-q)/L
        side=-np.sign(np.cross(np.append(d,0),np.append(ref-q,0))[2])      # opposite to the reference point
        rot=np.array([[np.cos(l),-side*np.sin(l)],[side*np.sin(l),np.cos(l)]])
        p=q+L*np.sin(s)/np.sin(d0)*(rot@d); P.append(p)
        ref=q; older,newer=newer,len(P)-1
    return np.array(P)
for n,d0 in ((8,0.3),(10,0.2),(10,0.1),(10,0.02)):
    delta=min(0.02,(np.pi/4-d0/2)/n); P=chain(n,d0,delta)
    T=[tuple(sorted(t)) for t in Delaunay(P).simplices]
    opp=defaultdict(list)
    for t in T:
        for k in range(3):
            i,j=[t[m] for m in range(3) if m!=k]; opp[(i,j)].append(ang(P[t[k]],P[i],P[j]))
    E=list(opp); best=9e9
    for mask in range(1,2**len(E)-1):
        Eset={E[i] for i in range(len(E)) if mask>>i&1}
        nt=sum(1 for t in T if (t[0],t[1]) in Eset and (t[0],t[2]) in Eset and (t[1],t[2]) in Eset)
        best=min(best,sum(sum(opp[e]) for e in Eset)-np.pi*nt)
    chain_ok=sorted(T)==sorted(tuple(sorted((k-1,k,k+1))) for k in range(1,n-1))
    short=min(np.linalg.norm(P[i]-P[j]) for i,j in E); D=max(np.linalg.norm(p-q) for p in P for q in P)
    print("n=%2d d0=%.2f: Delaunay = needle chain: %s (%d triangles); min excess over all %d subcomplexes = %.6f; diam/shortest = %.3e; lower (0.7/sin d0)^(n-2) = %.2e; upper 2(1+pi^2/d0)^(n-2) = %.2e; max dihedral = %.3f"
      %(n,d0,chain_ok,len(T),2**len(E)-2,best,D/short,(0.7/np.sin(d0))**(n-2),2*(1+np.pi**2/d0)**(n-2),max(sum(v) for v in opp.values())))
