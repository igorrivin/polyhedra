# Verify, from the definitions, the closed forms behind the compatibility of -V with the log-sine barrier on one triangle:
#   h_i = lam*sin(a_i)*cos(phi_i)  (phi_i = psi_i - theta, psi = (0, a1+a2, pi+a2))  parametrizes all h with h1+h2+h3=0, and
#   D2f = lam^2 * prod sin(a_i),   D3f = +-lam^3 * prod sin(a_i) * cos(phi1+phi2+phi3),   D2F = lam^2 * sum cos^2(phi_i),
# hence |D3f| <= sqrt(3) D2f sqrt(D2F) because |cos(phi1+phi2+phi3)| <= |cos phi1|+|cos phi2|+|cos phi3|.
import numpy as np
rng=np.random.default_rng(0); worst=0; err=0; sc=0
for _ in range(200000):
    a1=rng.uniform(0.02,3.0); a2=rng.uniform(0.01,np.pi-a1-0.01); a=np.array([a1,a2,np.pi-a1-a2])
    h=rng.standard_normal(3); h-=h.mean()
    d2=np.sum(h*h/np.tan(a)); d3=-np.sum(h**3/np.sin(a)**2); d2F=np.sum(h*h/np.sin(a)**2); d3F=-2*np.sum(np.cos(a)*h**3/np.sin(a)**3)
    psi=np.array([0,a1+a2,np.pi+a2]); M=np.c_[np.cos(psi),np.sin(psi)]; sol=np.linalg.lstsq(M,h/np.sin(a),rcond=None)[0]; lam=np.hypot(*sol); th=np.arctan2(sol[1],sol[0]); phi=psi-th
    err=max(err,abs(d2-lam**2*np.prod(np.sin(a)))/d2,abs(abs(d3)-lam**3*np.prod(np.sin(a))*abs(np.cos(phi.sum())))/(lam**3*np.prod(np.sin(a))),abs(d2F-lam**2*np.sum(np.cos(phi)**2))/d2F)
    worst=max(worst,abs(d3)/(d2*np.sqrt(d2F)))
    t=10**rng.uniform(-3,6); sc=max(sc,abs(t*d3+d3F)/(2*(t*d2+d2F)**1.5))
print("max relative error of the three closed forms: %.1e"%err)
print("sup |D3f|/(D2f sqrt(D2F)) over 2e5 random samples: %.4f  (sqrt 3 = %.4f)"%(worst,np.sqrt(3)))
print("sup |D3(t f+F)| / (2 (D2(t f+F))^1.5) over random t in [1e-3,1e6]: %.4f  (self-concordance needs <= 1)"%sc)
