# Does the maximizer of the volume over a combinatorial class ever degenerate by small ANGLES (splitting / needles / flat triangles),
# or only by theta_e -> 0 (faces flattening)?  Random classes; report the smallest angle and the smallest excess at the maximizer.
import numpy as np, sys, itertools
exec(open('v16_horospheres.py').read().split("rng=np.random.default_rng")[0])
from scipy.spatial import Delaunay
rng=np.random.default_rng(5); rows=[]
for trial in range(60):
    n=int(rng.integers(6,12)); P=rng.random((n,2))
    if trial%3==0: P=np.vstack([P[:n-2],P[0]+1e-3*rng.standard_normal((2,2))])      # classes coming from clustered points
    tri=[]
    for t in Delaunay(P).simplices:
        a,b,c=P[t]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0: t=t[[0,2,1]]
        tri.append(tuple(int(v) for v in t))
    out=maximize(tri,tmax=1e11)
    if out is None: continue
    x,s,lab,bverts,steps=out; ang=x.reshape(-1,3)
    rows.append((len(tri),x.min(),s.min(),int((ang.min(1)<1e-3).sum())))
rows=np.array(rows)
print("classes solved: %d (from Delaunay triangulations of 6-11 random points, a third of them with a tight cluster)"%len(rows))
print("maximum on the boundary (some theta_e or boundary slack < 1e-4): %d"%int((rows[:,2]<1e-4).sum()))
print("smallest face angle at the maximizer, over all classes: min %.3f, median %.3f"%(rows[:,1].min(),np.median(rows[:,1])))
print("classes with a triangle having an angle < 1e-3 at the maximizer (needle or flat): %d"%int((rows[:,3]>0).sum()))
print("--- details of the degenerate cases ---")
rng=np.random.default_rng(5)
for trial in range(60):
    n=int(rng.integers(6,12)); P=rng.random((n,2))
    if trial%3==0: P=np.vstack([P[:n-2],P[0]+1e-3*rng.standard_normal((2,2))])
    tri=[]
    for t in Delaunay(P).simplices:
        a,b,c=P[t]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0: t=t[[0,2,1]]
        tri.append(tuple(int(v) for v in t))
    out=maximize(tri,tmax=1e11)
    if out is None: continue
    x,s,lab,bverts,steps=out; ang=x.reshape(-1,3); bad=np.nonzero(ang.min(1)<1e-3)[0]
    if len(bad)==0: continue
    from collections import Counter
    deg=Counter(v for t in tri for v in t)
    print("class with %d triangles: degenerate triangles:"%len(tri))
    for b in bad:
        print("    vertices %s (degrees %s, boundary: %s): angles %s"%(tri[b],[deg[v] for v in tri[b]],[v in bverts for v in tri[b]],np.array2string(ang[b],precision=6)))
