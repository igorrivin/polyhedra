# Checks for the volume section:
#  (1) leading-trailing coordinates u on interior vertices keep triangle sums and dihedral sums fixed
#  (2) grad V = log-holonomy, vanishes at the geometric structure; Hess V = -2 L_II (cotan Laplacian of CURRENT angles)
#  (3) Newton's method on V recovers the geometric angles; each step is a Laplacian solve
#  (4) Bobenko-Springborn dual weight identity: sin(th)/(cosh(rho_k-rho_j)-cos(th)) = 1/w_e
import numpy as np, mpmath as mp
from scipy.spatial import Delaunay
rng=np.random.default_rng(7)
def Lob(t): return float(mp.clsin(2,2*t))/2
P=rng.random((40,2)); tri=Delaunay(P).simplices
T=[]
for t in tri:
    a,b,c=P[t]; 
    if np.cross(b-a,c-a)<0: t=t[[0,2,1]]
    T.append(tuple(t))
n=len(P)
def ang(p,q,r): # angle at p
    u=q-p; v=r-p; return np.arccos(np.dot(u,v)/np.linalg.norm(u)/np.linalg.norm(v))
# corners: (i,j,k) cyclic, corner at k opposite directed edge i->j
corners=[]; 
for (a,b,c) in T:
    for (i,j,k) in ((a,b,c),(b,c,a),(c,a,b)):
        corners.append((i,j,k,ang(P[k],P[i],P[j])))
from collections import defaultdict
edgecount=defaultdict(int)
for (i,j,k,al) in corners: edgecount[frozenset((i,j))]+=1
bverts=set(); 
for e,cn in edgecount.items():
    if cn==1: bverts|=set(e)
I=[v for v in range(n) if v not in bverts]; idx={v:m for m,v in enumerate(I)}
def alpha(u):  # u: dict on interior vertices (0 on boundary)
    U=np.zeros(n); 
    for v,m in idx.items(): U[v]=u[m]
    return np.array([al+U[i]-U[j] for (i,j,k,al) in corners])
def V(u): return sum(Lob(a) for a in alpha(u))
def grad(u):
    a=alpha(u); g=np.zeros(len(I))
    for (i,j,k,_),ac in zip(corners,a):
        d=-np.log(2*np.sin(ac))
        if i in idx: g[idx[i]]+=d
        if j in idx: g[idx[j]]-=d
    return g
def lap(u):
    a=alpha(u); L=np.zeros((len(I),len(I)))
    for (i,j,k,_),ac in zip(corners,a):
        w=0.5/np.tan(ac)
        for p,q,s in ((i,i,1),(j,j,1),(i,j,-1),(j,i,-1)):
            if p in idx and q in idx: L[idx[p],idx[q]]+=s*w
    return L
u0=np.zeros(len(I))
# (1) constraints preserved
u=0.02*rng.standard_normal(len(I)); a0=alpha(u0); a1=alpha(u)
tri_sum=max(abs(a1[3*t:3*t+3].sum()-np.pi) for t in range(len(T)))
dih0=defaultdict(float); dih1=defaultdict(float)
for (i,j,k,_),x,y in zip(corners,a0,a1): dih0[frozenset((i,j))]+=x; dih1[frozenset((i,j))]+=y
print("(1) max change of triangle sums %.1e, of dihedral angles %.1e"%(tri_sum,max(abs(dih0[e]-dih1[e]) for e in dih0)))
# (2) gradient at geometric structure, FD checks
print("(2) |grad V| at the geometric structure: %.2e"%np.abs(grad(u0)).max())
g=grad(u); h=1e-5; m=3; e=np.zeros(len(I)); e[m]=h
print("    FD check of grad: %.3e vs %.3e"%((V(u+e)-V(u-e))/(2*h),g[m]))
H_fd=np.array([(grad(u+h*np.eye(len(I))[q])-grad(u-h*np.eye(len(I))[q]))/(2*h) for q in range(len(I))])
print("    rel. error |Hess_FD + 2 L(alpha(u))|/|2L| = %.2e"%(np.abs(H_fd+2*lap(u)).max()/np.abs(2*lap(u)).max()))
# (3) Newton
amin=alpha(u0).min(); u=0.2*amin*rng.standard_normal(len(I)); print('    min angle of the mesh %.3f; start: min angle %.3f'%(amin,alpha(u).min()))
assert alpha(u).min()>0
for it in range(7):
    g=grad(u); print("(3) Newton it %d: |grad|=%.2e  |u|_inf=%.2e  V=%.12f"%(it,np.abs(g).max(),np.abs(u).max(),V(u)))
    u=u+np.linalg.solve(2*lap(u),g)
# (4) BS identity
def circ(a,b,c):
    A=np.array([b-a,c-a]); rhs=0.5*np.array([np.dot(b,b)-np.dot(a,a),np.dot(c,c)-np.dot(a,a)]); ctr=np.linalg.solve(A,rhs); return np.linalg.norm(ctr-a)
opp=defaultdict(list)
for t,(a,b,c) in enumerate(T):
    R=circ(P[a],P[b],P[c])
    for (i,j,k) in ((a,b,c),(b,c,a),(c,a,b)): opp[frozenset((i,j))].append((ang(P[k],P[i],P[j]),R))
err=0
for e,l in opp.items():
    if len(l)==2:
        (al,R1),(be,R2)=l; th=np.pi-al-be; w=0.5*(1/np.tan(al)+1/np.tan(be))
        err=max(err,abs(np.sin(th)/(np.cosh(np.log(R1/R2))-np.cos(th))-1/w)/(1/w))
print("(4) max rel. error of  sin(th)/(cosh(drho)-cos th) = 1/w_e : %.1e"%err)
