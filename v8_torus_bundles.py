# Once-punctured torus bundles, layered (monodromy) triangulation, Gueritaud's parametrization of angle structures:
# one variable w_i in (0,pi) per tetrahedron (cyclic), letters W[i] in {L,R} between tetrahedra i and i+1;
#   z_i = pi - w_i ;  non-hinge (W[i-1]==W[i]):  a_i=(2w_i-w_{i-1}-w_{i+1})/2, b_i=(w_{i-1}+w_{i+1})/2
#                     hinge     (W[i-1]!=W[i]):  a_i=(w_i+w_{i-1}-w_{i+1})/2,  b_i=(w_i-w_{i-1}+w_{i+1})/2
# (table written from memory; validated below against the known volumes 2.0298832, 2.6667448, 2.9891203, 3.6638624).
import numpy as np, mpmath as mp
def Lob(x): return float(mp.clsin(2,2*x))/2
def build(word):
    N=len(word); rows=[]            # each angle = const + coefficient vector on w
    for i in range(N):
        im,ip=(i-1)%N,(i+1)%N
        hinge = word[im]!=word[i]
        c=np.zeros(N); c[i]-=1; rows.append((np.pi,c))                    # z_i
        a=np.zeros(N); b=np.zeros(N)
        if not hinge: a[i]+=1; a[im]-=.5; a[ip]-=.5; b[im]+=.5; b[ip]+=.5
        else:         a[i]+=.5; a[im]+=.5; a[ip]-=.5; b[i]+=.5; b[im]-=.5; b[ip]+=.5
        rows.append((0.0,a)); rows.append((0.0,b))
    C=np.array([r[1] for r in rows]); c0=np.array([r[0] for r in rows]); return C,c0
def start(word):
    N=len(word); hinges=[i for i in range(N) if word[(i-1)%N]!=word[i]]; w=np.full(N,np.pi/2)
    for k,h in enumerate(hinges):
        h2=hinges[(k+1)%len(hinges)]; m=(h2-h)%N or N
        for j in range(1,m): w[(h+j)%N]=np.pi/2+1.0*j*(m-j)/m**2
    return w
def maximize(word,verbose=False):
    C,c0=build(word); w=start(word); ang=c0+C@w; assert ang.min()>0,ang.min()
    V=lambda a: -np.sum(np.where(a>0,a*0,np.inf)) if a.min()<=0 else None
    for it in range(200):
        ang=c0+C@w; g=C.T@(-np.log(2*np.sin(ang))); H=-(C.T*(1/np.tan(ang)))@C
        d=np.linalg.solve(H,-g); t=1.0
        f0=sum(Lob(x) for x in ang) if len(word)<=12 else None
        while (c0+C@(w+t*d)).min()<=0: t*=0.5
        # backtracking on the gradient norm along concave function: accept if directional derivative still nonnegative
        while True:
            a2=c0+C@(w+t*d); g2=C.T@(-np.log(2*np.sin(a2)))
            if g2@d>=-1e-14 or t<1e-12: break
            t*=0.5
        w=w+t*d
        if np.abs(g).max()<1e-9: break      # 1e-12 is below the rounding floor of the gradient for large m (an earlier version ran to the iteration cap for that reason)
    ang=c0+C@w; return w,ang,it,np.abs(g).max()
for word,vol in (("RL",2.0298832128),("RRL",2.6667447834),("RRRL",2.9891202829),("RRLL",3.6638623767)):
    w,ang,it,gn=maximize(word); print("%-5s volume %.10f (known %.10f)  Newton its %d"%(word,sum(Lob(x) for x in ang),vol,it))
print("syllable length m, word R^m L^m:  min angle, m^3*min angle, min z, m*min z, Newton iterations, cond(Hessian), bandwidth of Hessian")
for m in (5,10,20,40,80,160):
    word="R"*m+"L"*m; w,ang,it,gn=maximize(word); C,c0=build(word); H=(C.T*(1/np.tan(ang)))@C
    z=ang[0::3]; nz=np.nonzero(np.abs(H[m//2])>1e-14)[0]
    print("m=%4d  %.3e  %.3f   %.3e  %.3f   its=%3d  cond=%.2e  nonzeros in a row of H: %d  |grad|=%.1e"%(m,ang.min(),m**3*ang.min(),z.min(),m*z.min(),it,np.linalg.cond(H),len(nz),gn))
