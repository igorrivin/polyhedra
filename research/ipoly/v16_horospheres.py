# Check of the criterion for an INTERIOR maximum of the volume over a combinatorial class:
# horospheres tangent along all edges  <=>  |v-w|^2 = d_v d_w on every edge, with d constant on the boundary (= vertices adjacent to infinity).
import numpy as np, sys
from scipy.spatial import Delaunay
from scipy.linalg import null_space
from scipy.optimize import linprog
from collections import defaultdict
def maximize(tris,tmax=1e13):
    verts=sorted(set(v for t in tris for v in t)); F=len(tris); nc=3*F; ecount=defaultdict(list)
    for t,tr in enumerate(tris):
        for k in range(3): ecount[frozenset((tr[(k+1)%3],tr[(k+2)%3]))].append(3*t+k)
    bverts=set(v for e,l in ecount.items() if len(l)==1 for v in e); Aeq=[];beq=[];G=[];g=[];lab=[]
    for t in range(F): r=np.zeros(nc); r[3*t:3*t+3]=1; Aeq.append(r); beq.append(np.pi)
    for v in verts:
        r=np.zeros(nc)
        for t,tr in enumerate(tris):
            for k in range(3):
                if tr[k]==v: r[3*t+k]=1
        if v in bverts: G.append(r); g.append(np.pi); lab.append(("v",v))
        else: Aeq.append(r); beq.append(2*np.pi)
    for e,l in ecount.items():
        if len(l)==2: r=np.zeros(nc); r[l]=1; G.append(r); g.append(np.pi); lab.append(("e",tuple(sorted(e))))
    Aeq=np.array(Aeq);beq=np.array(beq);G=np.array(G);g=np.array(g)
    c=np.zeros(nc+1); c[-1]=-1
    res=linprog(c,A_ub=np.vstack([np.c_[G,np.ones(len(g))],np.c_[-np.eye(nc),np.ones(nc)]]),b_ub=np.r_[g,np.zeros(nc)],A_eq=np.c_[Aeq,np.zeros(len(beq))],b_eq=beq,bounds=[(0,np.pi)]*nc+[(0,None)])
    if res.status!=0 or res.x[-1]<1e-9: return None
    x=res.x[:nc]; Z=null_space(Aeq); t=1.0; steps=0
    while t<=tmax:
        for it in range(100):
            s=g-G@x; grad=t*np.log(2*np.sin(x))-1/np.tan(x)+G.T@(1/s); H=np.diag(t/np.tan(x)+1/np.sin(x)**2)+G.T@np.diag(1/s**2)@G
            gz=Z.T@grad; dz=np.linalg.solve(Z.T@H@Z,-gz); lam=np.sqrt(max(-gz@dz,0)); d=Z@dz; steps+=1; tau=1.0
            while (x+tau*d).min()<=0 or (g-G@(x+tau*d)).min()<=0: tau*=0.5
            if lam>0.25: tau=min(tau,1/(1+lam))
            x=x+tau*d
            if lam<1e-3: break
        t*=10
    return x,g-G@x,lab,bverts,steps
def layout(tris,x):
    pos={}; t0=tris[0]; a,b,c=t0; A,B,C=x[0],x[1],x[2]; pos[a]=np.array([0.,0.]); pos[b]=np.array([1.,0.])
    done={0}; 
    def place(i,j,k,ai,aj):            # triangle (i,j,k) counterclockwise, i and j placed, angles at i and j known
        L=np.linalg.norm(pos[j]-pos[i]); ak=np.pi-ai-aj; lik=L*np.sin(aj)/np.sin(ak); d=(pos[j]-pos[i])/L
        rot=np.array([[np.cos(ai),-np.sin(ai)],[np.sin(ai),np.cos(ai)]]); return pos[i]+lik*(rot@d)
    pos[c]=place(a,b,c,A,B); err=0
    while len(done)<len(tris):
        for t,tr in enumerate(tris):
            if t in done: continue
            for k in range(3):
                i,j,kk=tr[k],tr[(k+1)%3],tr[(k+2)%3]
                if i in pos and j in pos:
                    p=place(i,j,kk,x[3*t+k],x[3*t+(k+1)%3])
                    if kk in pos: err=max(err,np.linalg.norm(p-pos[kk]))
                    else: pos[kk]=p
                    done.add(t); break
    return pos,err
rng=np.random.default_rng(int(sys.argv[1]) if len(sys.argv)>1 else 0); found=0
for trial in range(40):
    n=int(rng.integers(7,11)); P=rng.random((n,2)); tri=[]
    for t in Delaunay(P).simplices:
        a,b,c=P[t]
        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])<0: t=t[[0,2,1]]
        tri.append(tuple(int(v) for v in t))
    out=maximize(tri)
    if out is None: continue
    x,s,lab,bverts,steps=out; interior=s.min()>1e-3
    pos,err=layout(tri,x); edges=sorted(set(tuple(sorted((tr[k],tr[(k+1)%3]))) for tr in tri for k in range(3)))
    verts=sorted(pos); col={v:i for i,v in enumerate(verts)}; M=np.zeros((len(edges)+len(bverts)-1,len(verts))); rhs=np.zeros(len(M))
    for r,(v,w) in enumerate(edges): M[r,col[v]]=1; M[r,col[w]]=1; rhs[r]=2*np.log(np.linalg.norm(pos[v]-pos[w]))
    bl=sorted(bverts)
    for q in range(len(bl)-1): M[len(edges)+q,col[bl[q]]]=1; M[len(edges)+q,col[bl[q+1]]]=-1          # d constant on the boundary
    u=np.linalg.lstsq(M,rhs,rcond=None)[0]; resid=np.abs(M@u-rhs).max()
    print("class with %2d vertices, %2d triangles: %s maximum (smallest slack %.1e, %d Newton steps); layout closes up to %.0e; residual of the tangency equations %.1e"%(n,len(tri),"INTERIOR" if interior else "boundary",s.min(),steps,err,resid))
    found+=interior
    if found>=3 and trial>=8: break
