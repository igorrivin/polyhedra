# Trace of the barrier continuation: per round, the weight t, centering steps, smallest angle, distance to the solution, and whether the polish succeeds.
import numpy as np, sys
sys.argv=["x","none"]
exec(open('v10_large.py').read().split('if __name__=="__main__":')[0])
def trace(R,mult=100.0):
    s=R; u=np.zeros(s.nI); s.t_la=0; s.nsolve=0; t=1.0; total=0
    print("   round   barrier weight 1/t   centering steps   min angle at centre   max|alpha-alpha*|   polish")
    for rnd in range(1,30):
        c=0
        for it in range(80):
            x=s.al(u); g=s.BvT@(t*np.log(2*np.sin(x))-1/x); d=s.solve(t/np.tan(x)+1/x**2,g); lam=np.sqrt(max(-g@d,0)); c+=1
            Bd=s.Bv@d; neg=Bd<0; tau=min(1.0,0.95*np.min(x[neg]/-Bd[neg])) if neg.any() else 1.0
            while True:
                x2=x+tau*Bd; g2=s.BvT@(t*np.log(2*np.sin(x2))-1/x2)
                if g2@d<=1e-14*abs(g@d)+1e-300 or tau<1e-16: break
                tau*=0.5
            u=u+tau*d
            if lam<0.25: break
        v=u.copy(); good=True; p=0
        for it in range(8):
            x=s.al(v); g=s.BvT@(-np.log(2*np.sin(x)))
            if np.abs(g).max()<1e-10: break
            v=v+(-s.solve(1/np.tan(x),g)); p+=1
            if s.al(v).min()<=0: good=False; break
        ok=good and np.abs(s.BvT@(-np.log(2*np.sin(s.al(v))))).max()<1e-10
        total+=c+p
        print("   %3d        %8.0e          %3d              %.2e            %.1e        %s"%(rnd,1/t,c,s.al(u).min(),np.abs(s.al(u)-s.truev).max(),"converged in %d steps"%p if ok else "failed after %d steps"%p))
        if ok: break
        t*=mult
    print("   total Newton steps %d"%total)
for lab,P in (("multi-scale m=16 (803 points, alpha_min=1.5e-5)",gadget(16)),("random n=4000 (alpha_min=1.8e-4)",np.random.default_rng(1).random((4000,2)))):
    R=Run(P,lab); trace(R)
