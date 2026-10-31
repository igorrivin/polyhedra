# What the "stupid" algorithm does when the maximum is on the boundary: plain damped Newton on V over the three-family polytope
# (null-space Newton direction, line search that keeps every constraint strictly satisfied, fraction-to-boundary 0.95), versus the barrier method.
import numpy as np, mpmath as mp
from scipy.linalg import null_space
from scipy.optimize import linprog
from collections import defaultdict
Lob=np.vectorize(lambda x: float(mp.clsin(2,2*x))/2)
def build(tris):
    verts=sorted(set(v for t in tris for v in t)); F=len(tris); nc=3*F; ecount=defaultdict(list)
    for t,tr in enumerate(tris):
        for k in range(3): ecount[frozenset((tr[(k+1)%3],tr[(k+2)%3]))].append(3*t+k)
    bverts=set(v for e,l in ecount.items() if len(l)==1 for v in e); Aeq=[];beq=[];G=[];g=[]
    for t in range(F): r=np.zeros(nc); r[3*t:3*t+3]=1; Aeq.append(r); beq.append(np.pi)
    for v in verts:
        r=np.zeros(nc)
        for t,tr in enumerate(tris):
            for k in range(3):
                if tr[k]==v: r[3*t+k]=1
        if v in bverts: G.append(r); g.append(np.pi)
        else: Aeq.append(r); beq.append(2*np.pi)
    for e,l in ecount.items():
        if len(l)==2: r=np.zeros(nc); r[l]=1; G.append(r); g.append(np.pi)
    Aeq=np.array(Aeq);beq=np.array(beq);G=np.array(G);g=np.array(g); c=np.zeros(nc+1); c[-1]=-1
    res=linprog(c,A_ub=np.vstack([np.c_[G,np.ones(len(g))],np.c_[-np.eye(nc),np.ones(nc)]]),b_ub=np.r_[g,np.zeros(nc)],A_eq=np.c_[Aeq,np.zeros(len(beq))],b_eq=beq,bounds=[(0,np.pi)]*nc+[(0,None)])
    return res.x[:nc],null_space(Aeq),G,g
def plain(x,Z,G,g,Vstar,steps=400):
    out=[]
    for k in range(1,steps+1):
        grad=-np.log(2*np.sin(x)); Hd=1/np.tan(x); gz=Z.T@grad; dz=np.linalg.solve(Z.T@(Hd[:,None]*Z),gz); d=Z@dz     # ascent direction for V
        tau=1.0; s=g-G@x; Gd=G@d; neg=Gd>0
        if neg.any(): tau=min(tau,0.95*np.min(s[neg]/Gd[neg]))
        neg2=d<0
        if neg2.any(): tau=min(tau,0.95*np.min(x[neg2]/-d[neg2]))
        while True:                                   # do not pass the maximum along the line
            x2=x+tau*d
            if (-np.log(2*np.sin(x2)))@d>=-1e-14 or tau<1e-16: break
            tau*=0.5
        x=x+tau*d
        if k in (5,10,20,50,100,200,400): out.append((k,Vstar-Lob(x).sum(),(g-G@x).min(),x.min()))
    return out
for name,tris,Vstar in (("three stacked tetrahedra",[("b","c","d"),("f","d","c"),("f","c","a"),("f","a","d")],3*3*float(mp.clsin(2,2*np.pi/3))/2),
                        ("octahedron (interior maximum)",[("o","b1","b2"),("o","b2","b3"),("o","b3","b4"),("o","b4","b1")],8*float(mp.clsin(2,np.pi/2))/2)):
    x,Z,G,g=build(tris); print(name+":  step | V* - V | smallest slack of an inequality | smallest angle")
    for k,gap,sl,am in plain(x,Z,G,g,Vstar): print("   %4d | %.2e | %.2e | %.2e"%(k,gap,sl,am))
# random classes (as in v16): plain Newton against the barrier method, on the cases where the maximum is on the boundary
import sys
sys.argv=["x"]
exec(open('v16_horospheres.py').read().split("rng=np.random.default_rng")[0].split("def layout")[0].replace("def maximize","def barrier_max"))
from scipy.spatial import Delaunay
rng=np.random.default_rng(5); shown=0
print("random classes with a boundary maximum:  V(barrier) | V(plain Newton, 400 steps) | difference | smallest slack (barrier / plain)")
for trial in range(60):
    n=int(rng.integers(6,12)); P=rng.random((n,2))
    if trial%3==0: P=np.vstack([P[:n-2],P[0]+1e-3*rng.standard_normal((2,2))])
    tri=[]
    for t in Delaunay(P).simplices:
        a,b,c=P[t]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0: t=t[[0,2,1]]
        tri.append(tuple(int(v) for v in t))
    out=barrier_max(tri,tmax=1e11)
    if out is None: continue
    xb,sb,lab,bverts,steps=out
    if sb.min()>1e-4: continue
    x,Z,G,g=build(tri); Vb=Lob(xb).sum()
    res=plain(x,Z,G,g,Vb,steps=400); gap=res[-1][1]; sp=res[-1][2]
    print("   %d triangles: %.8f | %.8f | %+.1e | %.1e / %.1e"%(len(tri),Vb,Vb-gap,-gap,sb.min(),sp)); shown+=1
    if shown>=8: break
