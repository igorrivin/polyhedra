# (A) excess(F_r) <= pi^2 r/g for the induced subcomplex on the vertices in B(p0,r) when the annulus r<|x-p0|<r+g is empty
# (B) Lemma 6.5: excess from the definition (sum of dihedral angles - pi*#triangles) = sum of exterior apex angles
# (C) sharpness: chain of needles in convex position; min excess over ALL subcomplexes = d0; diameter ~ (c/d0)^(n-2)
# (D) weights: cot(Delta/2) <= w_e ;  smallest angle >= min(sqrt3/2, sin thmax)/R
import numpy as np, itertools
from scipy.spatial import Delaunay
from collections import defaultdict
rng=np.random.default_rng(3)
def ang(p,q,r):
    u=q-p; v=r-p; return np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))
def tri_data(P):
    T=[tuple(sorted(t)) for t in Delaunay(P).simplices]
    opp=defaultdict(list)     # edge -> list of (opposite angle, triangle)
    for t in T:
        for k in range(3):
            i,j=[t[m] for m in range(3) if m!=k]
            opp[(i,j)].append((ang(P[t[k]],P[i],P[j]),t))
    return T,opp
worst=0; worst2=0
for trial in range(300):
    m=rng.integers(2,25); q=rng.integers(1,25); r=1.0; g=10**rng.uniform(-1,2)
    S=np.vstack([[0,0],(rng.random((m,2))*2-1)]); S=S[np.linalg.norm(S,axis=1)<=1]
    phi=rng.random(q)*2*np.pi; rad=(r+g)*(1+rng.random(q)*rng.choice([0.01,1,10]))
    Q=np.c_[rad*np.cos(phi),rad*np.sin(phi)]; P=np.vstack([S,Q]); ns=len(S)
    if ns<2: continue
    T,opp=tri_data(P)
    inS=lambda v: v<ns
    apex=sum(a for e,l in opp.items() if inS(e[0]) and inS(e[1]) for (a,t) in l if not all(inS(v) for v in t))
    EF=[e for e in opp if inS(e[0]) and inS(e[1])]; TF=[t for t in T if all(inS(v) for v in t)]
    exc=sum(a for e in EF for (a,t) in opp[e])-np.pi*len(TF)
    assert abs(exc-apex)<1e-9
    if len(EF)==0: continue
    worst=max(worst,apex*g/r/np.pi**2); worst2=max(worst2,apex*g/r/(2*np.pi))
print("(A,B) max over trials of excess*g/(pi^2 r) = %.3f (must be <=1);  excess*g/(2 pi r) = %.3f"%(worst,worst2))
# (C) needle chain
def chain(n,d0,delta=0.01):
    P=[np.array([0.,0.]),np.array([1.,0.])]; base=(0,1); side=1.0   # attach apex on the left of directed base a->b
    for k in range(2,n):
        a,b=P[base[0]],P[base[1]]; s=(np.pi-d0)/2-(n-k)*delta; l=np.pi-d0-s   # angle s at the NEWER base vertex b, l at the older a
        L=np.linalg.norm(b-a); leg_a=L*np.sin(s)/np.sin(d0)                  # |a p| opposite angle at b
        dirv=(b-a)/L; c,sn=np.cos(l),np.sin(l)*side
        p=a+leg_a*np.array([c*dirv[0]-sn*dirv[1],sn*dirv[0]+c*dirv[1]]); P.append(p)
        # longest leg is opposite the larger base angle l (at a): that is the leg b-p ; keep the same side of the new base
        base=(len(P)-1,base[1]); 
    return np.array(P)
for n,d0 in ((8,0.3),(9,0.2),(9,0.1)):
    P=chain(n,d0); T,opp=tri_data(P)
    E=list(opp.keys()); best=9e9; arg=None
    for mask in range(1,2**len(E)-1):
        Es=[E[i] for i in range(len(E)) if mask>>i&1]; Eset=set(Es)
        nt=sum(1 for t in T if all((t[x],t[y]) in Eset for x,y in ((0,1),(0,2),(1,2))))
        ex=sum(a for e in Es for (a,_) in opp[e])-np.pi*nt
        if ex<best: best,arg=ex,Es
    D=max(np.linalg.norm(p-q) for p in P for q in P); short=min(np.linalg.norm(P[i]-P[j]) for (i,j) in E)
    thmax=max(sum(a for a,_ in opp[e]) for e in E)
    print("(C) n=%d d0=%.2f: #tri=%d (chain needs %d), min excess over all %d subcomplexes = %.4f, diam/shortest = %.3e, (1/(2sin(d0/2)))^(n-2) = %.3e, (1+pi^2/d0)^(n-2) = %.3e, theta_max=%.3f"
          %(n,d0,len(T),n-2,2**len(E)-2,best,D/short,(1/(2*np.sin(d0/2)))**(n-2),(1+np.pi**2/d0)**(n-2),thmax))
# (D)
bad=0
for trial in range(200):
    P=rng.random((30,2)); T,opp=tri_data(P)
    for e,l in opp.items():
        if len(l)==2:
            al,be=l[0][0],l[1][0]; w=0.5*(1/np.tan(al)+1/np.tan(be)); D_=al+be
            if D_<np.pi-1e-9 and w<1/np.tan(D_/2)-1e-9: bad+=1
    E=list(opp); short=min(np.linalg.norm(P[i]-P[j]) for i,j in E); R=max(np.linalg.norm(p-q) for p in P for q in P)/short
    thmax=max(a for l in opp.values() for a,_ in l); amin=min(a for l in opp.values() for a,_ in l)
    if amin<min(np.sqrt(3)/2,np.sin(thmax))/R-1e-12: bad+=1
print("(D) violations of  w_e>=cot(Delta_e/2)  or  alpha_min>=min(sqrt3/2,sin(largest face angle))/R :",bad)
