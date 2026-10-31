# Compatibility of f = -V with the barrier F = -sum log sin(alpha_c) on one triangle (it then adds up over triangles).
# For a1+a2+a3=pi, h1+h2+h3=0, write h_i = sin(a_i) cos(phi_i), phi_i = psi_i - theta, psi = (0, a1+a2, pi+a2)  (h = pairing of a vector with the edge vectors).
#   D2f = sum cot(a_i) h_i^2 = prod sin(a_i) ,   -D3f = sum h_i^3/sin^2(a_i) = (1/4) sum sin(a_i) cos(3 phi_i) ,   D2F = sum h_i^2/sin^2(a_i) = sum cos^2(phi_i)
#   ratio = |D3f| / (D2f sqrt(D2F)).   High precision, and a3 is never formed as pi-a1-a2 (that loses the small angles).
import mpmath as mp, random
mp.mp.dps=250
def parts(a1,a2,th):
    s=a1+a2; psi=[mp.mpf(0),s,mp.pi+a2]; sn=[mp.sin(a1),mp.sin(a2),mp.sin(s)]
    num=abs(sum(sn[i]*mp.cos(3*(psi[i]-th)) for i in range(3)))/4
    return num, sn[0]*sn[1]*sn[2], sum(mp.cos(psi[i]-th)**2 for i in range(3)), sn, psi
def ratio(a1,a2,th):
    num,d2,d2F,_,_=parts(a1,a2,th); return num/(d2*mp.sqrt(d2F))
# check the closed forms against the definitions
random.seed(1)
for _ in range(2):
    a1=mp.mpf(random.uniform(0.1,1.2)); a2=mp.mpf(random.uniform(0.1,1.2)); th=mp.mpf(random.uniform(0,3.14)); num,d2,d2F,sn,psi=parts(a1,a2,th)
    al=[a1,a2,mp.pi-a1-a2]; h=[sn[i]*mp.cos(psi[i]-th) for i in range(3)]
    print("check: sum h=%.0e | D2f %.12f vs %.12f | -D3f %.12f vs %.12f"%(float(sum(h)),sum(mp.cot(al[i])*h[i]**2 for i in range(3)),d2,abs(sum(h[i]**3/mp.sin(al[i])**2 for i in range(3))),num))
best=(mp.mpf(0),None); random.seed(2)
def scan(a1,a2,nth):
    global best
    for k in range(nth):
        th=mp.pi*(k+mp.mpf(1)/3)/nth; r=ratio(a1,a2,th)
        if r>best[0]: best=(r,(a1,a2,th))
for _ in range(1200):
    kind=random.random()
    if kind<0.3: a1=mp.mpf(random.uniform(0.01,1.5)); a2=mp.mpf(random.uniform(0.01,float(mp.pi-a1)-0.01))
    elif kind<0.6: a1=mp.mpf(10)**random.uniform(-30,-1); a2=mp.mpf(random.uniform(0.01,3.0))
    else: a1=mp.mpf(10)**random.uniform(-30,-1); a2=a1*mp.mpf(10)**random.uniform(-8,8)
    if a1+a2<mp.pi: scan(a1,a2,61)
print("sup over the random scan: %.6f at angles (%.3e, %.3e), theta=%.5f"%(best[0],best[1][0],best[1][1],best[1][2]))
for (a1,a2,lab) in ((mp.mpf(10)**-20,mp.mpf(1),"needle"),(mp.mpf(10)**-20,mp.pi/2,"needle, right angle"),(mp.mpf(10)**-20,mp.mpf(10)**-20,"cap, equal small angles"),(mp.mpf(10)**-20,mp.mpf(10)**-26,"cap, unequal small angles"),(mp.pi/3,mp.pi/3,"equilateral"),(mp.pi/2,mp.pi/4,"right isosceles")):
    m=max(ratio(a1,a2,mp.pi*k/4001) for k in range(4001)); print("   %-28s max over theta = %.6f"%(lab,m))
# near theta = pi/2 for caps, where the analysis predicts |3u+s+b|/sqrt(u^2+(u+s)^2+(u+b)^2) <= sqrt 3
a=mp.mpf(10)**-12; b=mp.mpf(10)**-15; s=a+b; m=mp.mpf(0)
for k in range(-4000,4001):
    u=s*k/200; m=max(m,ratio(a,b,mp.pi/2-u))
print("   cap (1e-12,1e-15), theta within 20s of pi/2: max = %.6f ;  sqrt(3) = %.6f"%(m,mp.sqrt(3)))
