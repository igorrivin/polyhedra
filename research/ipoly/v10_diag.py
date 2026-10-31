import numpy as np, scipy.sparse as sp, sys
sys.argv=["x","none"]
exec(open('v10_large.py').read().split('if __name__=="__main__":')[0])
for m in (10,16,19,22):
    P=gadget(m); F,ang,inv,E,B,var=setup(P); Bv=B[var]; x=ang[var]
    L=(Bv.T@sp.diags(1/np.tan(x))@Bv).toarray()/2; ev=np.linalg.eigvalsh(L)
    w=1/np.tan(x); print("m=%d: alpha_min=%.2e  cond(L_II at the solution)=%.2e = 2^%.1f ; largest cot %.2e ; formula log2(n^2 tan(thmax/2)/a^2) with a=alpha_min: %.1f bits"%(m,x.min(),ev[-1]/ev[0],np.log2(ev[-1]/ev[0]),w.max(),np.log2(len(P)**2*np.tan(max(np.bincount(inv,weights=ang))/2 if False else 1)/x.min()**2)))
