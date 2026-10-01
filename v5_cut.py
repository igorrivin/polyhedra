import numpy as np
from scipy.spatial import Delaunay
from collections import defaultdict
rng=np.random.default_rng(5)
def ang(p,q,r):
    u=q-p; v=r-p; return np.arccos(np.clip(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v),-1,1))
worst=0
for trial in range(200):
    m=rng.integers(3,20); S=rng.random((m,2))*2-1; S=S[np.linalg.norm(S,axis=1)<1]; ns=len(S)
    q=rng.integers(6,30); phi=np.sort(rng.random(q)*2*np.pi); rad=3+3*rng.random(q)
    ring2=np.c_[20*np.cos(np.linspace(0,6.28,9)[:-1]),20*np.sin(np.linspace(0,6.28,9)[:-1])]   # outer layer so that the cut edges are interior edges
    P=np.vstack([S,np.c_[rad*np.cos(phi),rad*np.sin(phi)],ring2])
    if ns<2 or np.diff(np.r_[phi,phi[0]+2*np.pi]).max()>2.5: continue
    T=[tuple(sorted(t)) for t in Delaunay(P).simplices]; opp=defaultdict(list)
    for t in T:
        for k in range(3):
            i,j=[t[x] for x in range(3) if x!=k]; opp[(i,j)].append(ang(P[t[k]],P[i],P[j]))
    inS=lambda v:v<ns
    exc=sum(sum(opp[e]) for e in opp if inS(e[0]) and inS(e[1]))-np.pi*sum(1 for t in T if all(inS(v) for v in t))
    cut=[e for e in opp if inS(e[0])!=inS(e[1])]
    assert all(len(opp[e])==2 for e in cut)
    worst=max(worst,abs(sum(np.pi-sum(opp[e]) for e in cut)-(2*np.pi+2*exc)))
print("max | sum_{cut} theta(e) - (2 pi + 2 excess(F)) | = %.2e"%worst)
