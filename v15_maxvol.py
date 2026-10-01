# Maximal volume in a combinatorial class = maximize V over the three-family polytope
#   (T) triangle sums = pi, (V) interior vertex sums = 2pi, (E) alpha_e+beta_e <= pi on interior edges, boundary vertex sums <= pi, alpha > 0.
# Barrier: F = -sum log sin(alpha_c) - sum log(slack of each inequality).  By Proposition 5.8 (which is per triangle and ignores the other constraints)
# -tV+F is self-concordant for all t, so the barrier method applies whether the maximum is interior or on the boundary (a flattened face).
import numpy as np, mpmath as mp
from scipy.linalg import null_space
from scipy.optimize import linprog
Lob=lambda x: float(mp.clsin(2,2*x))/2
def solve_class(tris,name,tmax=1e12):
    verts=sorted(set(v for t in tris for v in t)); F=len(tris); nc=3*F
    corner=lambda t,k: 3*t+k                                   # angle of triangle t at its k-th vertex
    from collections import defaultdict
    ecount=defaultdict(list)
    for t,tr in enumerate(tris):
        for k in range(3): ecount[frozenset((tr[(k+1)%3],tr[(k+2)%3]))].append(corner(t,k))     # corner opposite that edge
    bverts=set(v for e,l in ecount.items() if len(l)==1 for v in e)
    Aeq=[];beq=[]
    for t in range(F): r=np.zeros(nc); r[3*t:3*t+3]=1; Aeq.append(r); beq.append(np.pi)
    G=[];g=[];lab=[]
    for v in verts:
        r=np.zeros(nc)
        for t,tr in enumerate(tris):
            for k in range(3):
                if tr[k]==v: r[corner(t,k)]=1
        if v in bverts: G.append(r); g.append(np.pi); lab.append("vertex %s"%v)
        else: Aeq.append(r); beq.append(2*np.pi)
    for e,l in ecount.items():
        if len(l)==2: r=np.zeros(nc); r[l]=1; G.append(r); g.append(np.pi); lab.append("edge %s%s"%tuple(sorted(e)))
    Aeq=np.array(Aeq); beq=np.array(beq); G=np.array(G); g=np.array(g)
    # strictly feasible start: maximize the margin
    c=np.zeros(nc+1); c[-1]=-1
    res=linprog(c,A_ub=np.vstack([np.c_[G,np.ones(len(g))],np.c_[-np.eye(nc),np.ones(nc)]]),b_ub=np.r_[g,np.zeros(nc)],A_eq=np.c_[Aeq,np.zeros(len(beq))],b_eq=beq,bounds=[(0,np.pi)]*nc+[(0,None)])
    x=res.x[:nc]; Z=null_space(Aeq); t=1.0; steps=0
    print("%s: %d angles, tangent space of dimension %d, %d inequality constraints, LP margin %.3f"%(name,nc,Z.shape[1],len(g),res.x[-1]))
    while t<=tmax:
        for it in range(100):
            s=g-G@x; grad=t*np.log(2*np.sin(x))-1/np.tan(x)+G.T@(1/s); H=np.diag(t/np.tan(x)+1/np.sin(x)**2)+G.T@np.diag(1/s**2)@G
            gz=Z.T@grad; Hz=Z.T@H@Z; dz=np.linalg.solve(Hz,-gz); lam=np.sqrt(max(-gz@dz,0)); d=Z@dz; steps+=1
            tau=1.0
            while (x+tau*d).min()<=0 or (g-G@(x+tau*d)).min()<=0: tau*=0.5
            tau=min(tau,1/(1+lam)) if lam>0.25 else tau          # damped Newton step for self-concordant functions
            x=x+tau*d
            if lam<1e-3: break
        t*=10
    s=g-G@x; V=sum(Lob(a) for a in x)
    print("   after %d Newton steps (t up to %.0e): V = %.8f ; smallest angle %.4f ; slacks of the inequalities:"%(steps,t/10,V,x.min()))
    print("   "+", ".join("%s: %.2e"%(l,sv) for l,sv in zip(lab,s)))
    return V
v3=3*Lob(np.pi/3); v8=8*Lob(np.pi/4)
# octahedron with one vertex at infinity: square b1..b4 with centre o
V=solve_class([("o","b1","b2"),("o","b2","b3"),("o","b3","b4"),("o","b4","b1")],"octahedron"); print("   regular ideal octahedron: %.8f"%v8)
# three tetrahedra in a chain (twice-stacked tetrahedron), vertex e at infinity: quadrilateral b,c,a,d with diagonal cd, and f inside the triangle c,a,d
V=solve_class([("b","c","d"),("f","d","c"),("f","c","a"),("f","a","d")],"three stacked tetrahedra"); print("   3 v_3 = %.8f  (three regular ideal tetrahedra: the edge cd is flat)"%(3*v3))
