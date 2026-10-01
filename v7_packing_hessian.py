# Circle packing (tangency) in Thurston's variables: radii r_v at the vertices of a triangulation, edge lengths r_i+r_j.
# Claim to verify: with u=log r and K_i = 2pi - (angle sum at i),  dK_i/du_j = -(rho_t+rho_t')/l_ij  (rho = inradius of the two triangles on edge ij),
# and dK_i/du_i = sum_j (rho_t+rho_t')/l_ij : a graph Laplacian with positive conductances |e*|/|e|, e* joining the two incentres.
import numpy as np
from scipy.spatial import Delaunay
from collections import defaultdict
rng=np.random.default_rng(1)
P=rng.random((25,2)); T=[tuple(t) for t in Delaunay(P).simplices]; n=len(P)   # combinatorics only
def anglesums(u):
    r=np.exp(u); th=np.zeros(n)
    for t in T:
        for a in range(3):
            i,j,k=t[a],t[(a+1)%3],t[(a+2)%3]
            lij,lik,ljk=r[i]+r[j],r[i]+r[k],r[j]+r[k]
            th[i]+=np.arccos((lij**2+lik**2-ljk**2)/(2*lij*lik))
    return th
u=np.log(rng.uniform(0.5,2.0,n)); r=np.exp(u)
W=defaultdict(float)
for (i,j,k) in T:
    a,b,c=r[j]+r[k],r[i]+r[k],r[i]+r[j]; s=(a+b+c)/2; rho=np.sqrt((s-a)*(s-b)*(s-c)/s)
    for (p,q) in ((i,j),(j,k),(i,k)): W[frozenset((p,q))]+=rho/(r[p]+r[q])
L=np.zeros((n,n))
for e,w in W.items():
    p,q=tuple(e); L[p,q]-=w; L[q,p]-=w; L[p,p]+=w; L[q,q]+=w
h=1e-6; J=np.zeros((n,n))
for j in range(n):
    d=np.zeros(n); d[j]=h; J[:,j]=(anglesums(u+d)-anglesums(u-d))/(2*h)
print("max | d(angle sum)/du + L | = %.2e   (so dK/du = L);  min conductance %.3f > 0;  symmetric: %.1e"%(np.abs(J+L).max(),min(W.values()),np.abs(J-J.T).max()))
# incentre distance check: rho_t+rho_t' = distance between the two incentres projected ... for tangent circles the incircle touches edge ij at the tangency point of circles i,j,
# so the two incentres and the tangency point are collinear on the perpendicular to ij:  |e*| = rho_t + rho_t'  exactly.
