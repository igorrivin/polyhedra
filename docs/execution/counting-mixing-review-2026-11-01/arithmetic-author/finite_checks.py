"""Small exact audit fixtures; no asymptotic or numerical torus assertion."""
from fractions import Fraction as F
from math import gcd, floor, ceil
from pathlib import Path
import json

def mobius(n):
    value, p = 1, 2
    while p*p <= n:
        if n % p == 0:
            n //= p
            value = -value
            if n % p == 0:
                return 0
        p += 1
    return -value if n > 1 else value

def mertens(x):
    return sum(mobius(n) for n in range(1, floor(x)+1))

def phi(n):
    return sum(gcd(k,n)==1 for k in range(1,n+1))

checks = {'primitive_inversion': 0, 'large_divisor_reversal': 0,
          'square_totient': 0, 'row_divisor': 0, 'dyadic_polynomial': 0,
          'power_balance': 0, 'exact_block_metric': 0}
for shape in ('square', 'diamond'):
    gauge = (lambda p,q: max(abs(p),abs(q))) if shape=='square' else (lambda p,q: abs(p)+abs(q))
    for L in [F(n,d) for d in (1,2,3) for n in range(d,25)]:
        points = [(p,q) for p in range(-ceil(L),ceil(L)+1)
                  for q in range(-ceil(L),ceil(L)+1) if (p or q)]
        def all_points(u):
            return sum(gauge(p,q)<=u for p,q in points)
        primitive = sum(gauge(p,q)<=L and gcd(p,q)==1 for p,q in points)
        assert primitive == sum(mobius(d)*all_points(L/d) for d in range(1,floor(L)+1))
        checks['primitive_inversion'] += 1
        for D in range(1,floor(L)+1):
            lhs = sum(mobius(d)*all_points(L/d) for d in range(D+1,floor(L)+1))
            rhs = sum(mertens(L/gauge(p,q))-mertens(D) for p,q in points if gauge(p,q)<=L/D)
            assert lhs==rhs
            checks['large_divisor_reversal'] += 1
        if shape=='square' and L.denominator==1:
            assert primitive == 8*sum(phi(n) for n in range(1,int(L)+1))
            checks['square_totient'] += 1

for n in range(1,31):
    for a in [F(k,3) for k in range(-15,16)]:
        for width in (F(0),F(1,4),F(1),F(7,3),F(5)):
            b=a+width
            direct=sum(gcd(k,n)==1 for k in range(ceil(a),floor(b)+1))
            divisors=sum(mobius(d)*(floor(b/d)-ceil(a/d)+1) for d in range(1,n+1) if n%d==0)
            assert direct==divisors
            checks['row_divisor']+=1

for a,b,c in [(F(2,3),F(-5,7),F(4)),(F(0),F(3),F(-8))]:
    N=lambda u:a*u*u+b*u+c
    E=lambda u:b*u+c
    D=lambda u:N(2*u)-4*N(u)
    for L in (F(1),F(3,2),F(7)):
        for k in range(1,9):
            rhs=F(1,4**k)*E(2**k*L)-sum((F(1,4**(j+1))*D(2**j*L) for j in range(k)),F(0))
            assert rhs==E(L)
            checks['dyadic_polynomial']+=1

alpha=F(2,3)
for theta, expected in [(F(1,2),F(10,11)),(F(7,8),F(34,35)),(F(11,12),F(50,51))]:
    d=(2-alpha)/(3-alpha-theta)
    kappa=(2-alpha*theta)/(3-alpha-theta)
    assert alpha+d*(1-alpha)==2-d*(2-theta)==kappa==expected
    assert 0<d<1
    checks['power_balance']+=1

lengths=list(map(F,[2,2,4,5,8]));T=F(2);end=2*T
N=lambda u:sum(ell<=u for ell in lengths)
Nleft=lambda u:sum(ell<u for ell in lengths)
D=lambda u:N(2*u)-4*N(u)
Dleft=lambda u:Nleft(2*u)-4*Nleft(u)
events=sorted({T,end}|{v for ell in lengths for v in (ell,ell/2) if T<=v<=end})
maximum=max([abs(D(v))/v for v in events]+[abs(Dleft(v))/v for v in events if v>T])
q2=sum(D((a+b)/2)**2*(1/a-1/b) for a,b in zip(events,events[1:]))/T
assert maximum==F(5,2) and q2==F(49,20)
checks['exact_block_metric']+=1

result={'status':'exact_finite_author_audit_checks_not_asymptotic_proofs',
        'checks':checks,'total':sum(checks.values()),
        'event_fixture':{'lengths':[2,2,4,5,8],'T':2,'M':str(maximum),'Q_squared':str(q2)}}
Path(__file__).with_name('finite-check-results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
