"""Independent matrix-word and exact event probes for the bounded torus driver."""
from pathlib import Path
from fractions import Fraction as F
from itertools import combinations_with_replacement, product
import importlib.util
import hashlib
import json
import math
import re
import sys
import mpmath as mp

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT=ROOT.parent/'execution/monograph-revision-2026-11-01/scientific-review'
spec=importlib.util.spec_from_file_location('reviewed_torus',ROOT/'experiments/section30/run.py')
run=importlib.util.module_from_spec(spec);sys.modules[spec.name]=run;spec.loader.exec_module(run)
paths=['book/chapters/30-sharp-diagnostics.tex','book/claims/section30.json',
       'experiments/section30/README.md','experiments/section30/run.py',
       'experiments/section30/fixture.json','experiments/section30/tests/test_diagnostic.py']
hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
fixture=json.loads((ROOT/paths[4]).read_text())
result={'source_sha256':hashes,'matrix_word_checks':[]}

def mul(x,y):
    a,b,c,d=x;e,f,g,h=y
    return (a*e+b*g,a*f+b*h,c*e+d*g,c*f+d*h)

def tr(x):
    return x[0]+x[3]

def qvalue(value):
    # Direct high-precision evaluation is safe for this bounded small-word check.
    return mp.mpf(value.a.numerator)/value.a.denominator+mp.sqrt(11)*mp.mpf(value.b.numerator)/value.b.denominator

with mp.workdps(110):
    for record in fixture['surfaces']:
        roots=run.fixture_roots(record)
        x,y,z=map(qvalue,roots)
        eigen=(x+mp.sqrt(x*x-4))/2
        b11=(z-y/eigen)/(eigen-1/eigen)
        b22=(eigen*y-z)/(eigen-1/eigen)
        B=(b11,mp.mpf(1),b11*b22-1,b22)
        A=(eigen,mp.mpf(0),mp.mpf(0),1/eigen)
        assert abs(tr(A)-x)<mp.mpf('1e-100')
        assert abs(tr(B)-y)<mp.mpf('1e-100')
        assert abs(tr(mul(A,B))-z)<mp.mpf('1e-100')
        exact=run.exact_trace_function(roots)
        maximum=mp.mpf(0);count=0;short_slopes=set()
        # A rational straight line on the punctured square torus gives a
        # balanced primitive word. Floors count horizontal crossings between
        # consecutive vertical crossings. No Farey recursion is used here.
        for q in range(19):
            for p in range(-18,19):
                if math.gcd(p,q)!=1 or (q==0 and p!=1):
                    continue
                if q==0:
                    W=A
                else:
                    W=(mp.mpf(1),mp.mpf(0),mp.mpf(0),mp.mpf(1))
                    for j in range(q):
                        k=((j+1)*p)//q-(j*p)//q
                        D=(eigen**k,mp.mpf(0),mp.mpf(0),eigen**(-k))
                        W=mul(W,mul(D,B))
                observed=tr(W);expected=qvalue(exact(p,q))
                residual=abs(observed/expected-1)
                assert residual<mp.mpf('1e-90'),(record['id'],p,q,residual)
                maximum=max(maximum,residual);count+=1
                if 2*mp.acosh(observed/2)<=6:
                    short_slopes.add((p,q))
        # The proven box bound for length6 is max(|p|,q)<15, fully inside
        # the independent matrix-word box of18.
        floating,_=run.log_spectrum(roots,6)
        assert set(floating)==short_slopes
        result['matrix_word_checks'].append({'surface':record['id'],'primitive_words':count,
                 'maximum_relative_trace_residual':mp.nstr(maximum,25),'tolerance':'1e-90',
                 'length6_count':len(short_slopes),'matrix_box_coordinate_bound':18,
                 'source_of_words':'direct floor crossing sequence, not Farey recursion'})

def rational_metrics(lengths,start):
    """Exact independently recomputed counts, including endpoint conventions."""
    lengths=list(map(F,lengths));start=F(start);end=2*start
    points={start,end}
    for ell in lengths:
        points.update(x for x in (ell/2,ell) if start<x<end)
    points=sorted(points)
    maximum=F(0);integral=F(0)
    for x in points:
        D=sum(ell<=2*x for ell in lengths)-4*sum(ell<=x for ell in lengths)
        maximum=max(maximum,F(abs(D),1)/x)
        if x>start:
            D=sum(ell<2*x for ell in lengths)-4*sum(ell<x for ell in lengths)
            maximum=max(maximum,F(abs(D),1)/x)
    for a,b in zip(points,points[1:]):
        x=(a+b)/2
        D=sum(ell<=2*x for ell in lengths)-4*sum(ell<=x for ell in lengths)
        integral+=D*D*(1/a-1/b)
    return maximum,integral/start

event_cases=0;max_M_error=0;max_Q2_error=0
levels=[F(k,2) for k in range(1,9)]
for n in range(5):
    for lengths in combinations_with_replacement(levels,n):
        for start in (F(1,2),F(1),F(2)):
            exact_M,exact_Q2=rational_metrics(lengths,start)
            observed=run.block_metrics([float(x) for x in lengths],float(start))
            M_error=abs(observed['M']-float(exact_M))
            Q2_error=abs(observed['Q']**2-float(exact_Q2))
            assert M_error<1e-13
            assert Q2_error<1e-12
            max_M_error=max(max_M_error,M_error);max_Q2_error=max(max_Q2_error,Q2_error)
            event_cases+=1
result['exact_event_cases']={'cases':event_cases,'max_M_error':max_M_error,'max_Q_squared_error':max_Q2_error,
                            'includes':'multiplicities, simultaneous opposite jumps, all endpoint placements, empty lists'}

sensitivity_cases=0
vectors=[[],[1],[2],[F(1,2),1,2,4],[1,F(3,2),3,3],[F(7,8),1,F(9,8),2],
         [2,2,2,2],[1,1,2,2],[F(31,16),2,F(33,16),4]]
for values in vectors:
    for start in (F(1,2),F(1),F(2)):
        for radius in (F(0),F(1,16),F(1,4)):
            bounds=run.conditional_maximum_bounds([float(x) for x in values],start,radius)
            lo,hi=F(bounds['lower_exact_rational']),F(bounds['upper_exact_rational'])
            for choices in product((-1,0,1),repeat=len(values)):
                altered=[F(x)+direction*radius for x,direction in zip(values,choices)]
                true_M,_=rational_metrics(altered,start)
                assert lo<=true_M<=hi,(values,start,radius,choices,lo,true_M,hi)
                sensitivity_cases+=1
result['conditional_interval_cases']=sensitivity_cases

baseline=(OUT.parent/'structure/30-sharp-diagnostics.tex').read_text()
current=(ROOT/paths[0]).read_text()
assert re.findall(r'\\label\{([^}]+)\}',baseline)==re.findall(r'\\label\{([^}]+)\}',current)
for row in re.findall(r'^\d+ &.*\\\\$',baseline,re.M):
    assert row in current,row
for env in ('proof','proposition'):
    pattern=r'\\begin\{'+env+r'\}[\s\S]*?\\end\{'+env+r'\}'
    assert re.findall(pattern,baseline)==re.findall(pattern,current)
for p,h in hashes.items():
    assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
result['preservation']={'labels':22,'all_proofs_and_propositions_unchanged':True,
                        'historical_table_rows_preserved':True,'all_source_hashes_unchanged_during_probe':True}
result['boundaries']=['No length8192 replay','Numerical matrix traces, not exact matrix certificates',
                     'Conditional M bounds for fixed curve membership and assumed radius',
                     'No complete Section30 proof audit or event-location certificate']
result['primary_source']='https://warwick.ac.uk/fac/sci/maths/people/staff/brian_bowditch/bhb-markoff.pdf'
(OUT/'torus-independent.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
print(json.dumps({'matrix_words':sum(x['primitive_words'] for x in result['matrix_word_checks']),
                  'event_cases':event_cases,'conditional_cases':sensitivity_cases,'preservation_passed':True}))
