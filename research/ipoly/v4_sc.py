import numpy as np
rng=np.random.default_rng(11)
cot=lambda x:1/np.tan(x)
# f = -(Lob(a1)+Lob(a2)+Lob(a3)) on a1+a2+a3=pi ; D2f[h,h]=sum cot(ai) hi^2 ; D3f[h,h,h]=-sum hi^3/sin^2(ai) ; barrier F=-sum log ai
sup_sc=0; sup_comp=0; arg=None
for trial in range(400000):
    e=rng.exponential(size=3)*10**rng.uniform(-6,0,size=3); a=np.pi*e/e.sum()      # includes points very close to the boundary
    h=rng.standard_normal(3)*a**rng.uniform(0,1.5); h-=h.mean()                    # tangent direction, various scalings
    if rng.random()<0.3: h=a-np.array([0,0,np.pi])*(a.argmax()==np.arange(3))      # near-scaling directions
    h=h-h.mean()
    d2=np.sum(cot(a)*h*h); d3=-np.sum(h**3/np.sin(a)**2); d2F=np.sum(h*h/a**2)
    if d2<=0: continue
    sup_sc=max(sup_sc,abs(d3)/d2**1.5)
    r=abs(d3)/(d2*np.sqrt(d2F))
    if r>sup_comp: sup_comp,arg=r,(a.copy(),h.copy())
print("sup |D3f|/(D2f)^{3/2}  over samples: %.1f   (unbounded near the boundary: -V is NOT self-concordant)"%sup_sc)
print("sup |D3f|/(D2f*sqrt(D2F)) over samples: %.3f  at angles %s"%(sup_comp,np.round(arg[0],6)))
# analytic blow-up along (t,2t,pi-3t), h=(1,-1,0)
for t in (1e-2,1e-4,1e-6):
    a=np.array([t,2*t,np.pi-3*t]); h=np.array([1.,-1.,0.])
    print("   t=%.0e: ratio %.1f  (0.408/sqrt(t) = %.1f)"%(t,abs(np.sum(h**3/np.sin(a)**2))/np.sum(cot(a)*h*h)**1.5,0.408/np.sqrt(t)))
# dual (Bobenko-Springborn) weights: w(x)=sin(th)/(cosh x-cos th); sup |w'|/w = 1/sin(th) for th<pi/2, <1 otherwise
for th in (0.3,1.0,np.pi/2,2.5):
    x=np.linspace(-30,30,600001); w=np.sin(th)/(np.cosh(x)-np.cos(th)); dw=-np.sin(th)*np.sinh(x)/(np.cosh(x)-np.cos(th))**2
    print("   theta=%.2f: sup|w'|/w = %.4f ; 1/sin(theta) = %.4f"%(th,np.max(np.abs(dw)/w),1/np.sin(th)))
