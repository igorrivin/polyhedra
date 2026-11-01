"""Independent scientific review probes; no canonical source changes."""
from pathlib import Path
from fractions import Fraction
import importlib.util
import hashlib
import json
import re
import subprocess
import sys

import mpmath as mp

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EVIDENCE = ROOT.parent / 'execution/monograph-revision-2026-11-01'
OUT = EVIDENCE / 'scientific-review'
manifest_path = EVIDENCE / 'airy-author-manifest.json'
manifest = json.loads(manifest_path.read_text())
assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == 'd3f8b34658061d075ae27106538f21e544f0d78fa4654e29cf2a0087dcbb240e'
for name, expected in manifest['source_sha256'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name

chapter = (ROOT/'book/chapters/15-quantum-airy.tex').read_text()
baseline = (EVIDENCE/'structure/15-quantum-airy.tex').read_text()
old_marker = r'\subsection{A numerical check of the exact integral}'
new_marker = r'\subsection{Numerical evidence and reproducibility status}'
assert baseline.split(old_marker)[0] == chapter.split(new_marker)[0]
assert baseline.split(r'\subsection{Interpretation and scope}')[1] == chapter.split(r'\subsection{Interpretation and scope}')[1]
assert re.findall(r'\\label\{([^}]+)\}', baseline) == re.findall(r'\\label\{([^}]+)\}', chapter)
old_rows = re.findall(r'^\$[0-9.]+\$&\$[01]\$&.*$', baseline, re.M)
new_rows = re.findall(r'^\$[0-9.]+\$&\$[01]\$&.*$', chapter, re.M)
assert old_rows == new_rows and len(old_rows) == 6

spec = importlib.util.spec_from_file_location('reviewed_airy', ROOT/'experiments/section15/check.py')
author = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = author
spec.loader.exec_module(author)
fixture = json.loads((ROOT/'experiments/section15/historical-table.json').read_text())
results = {'source_sha256': manifest['source_sha256'], 'preservation': {
    'analytic_proof_bytes_unchanged': True, 'interpretation_bytes_unchanged': True,
    'all_original_rows_unchanged': True, 'labels': 21}, 'probes': []}

with mp.workdps(100):
    eta = mp.acos(mp.mpf(1)/3)
    v = 4*mp.pi-5*eta
    def angles(x, e):
        return ((x-3*mp.pi+3*e)/2, (4*mp.pi-4*e-x)/2,
                (4*mp.pi-x)/2, (mp.pi-e)/2)
    def gv(x, e):
        a,b,c,s = angles(x,e)
        return 4*mp.log(2*mp.sin(a))-3*mp.log(2*mp.sin(b))-mp.log(2*mp.sin(c))
    def ge(x, e):
        a,b,c,s = angles(x,e)
        return 12*mp.log(2*mp.sin(a))-12*mp.log(2*mp.sin(b))+6*mp.log(mp.sin(s)/mp.sin(3*s))
    def amplitude(x, e):
        a,b,c,s = angles(x,e)
        return (2*mp.sin(a))**(-2)*(mp.sin(c)/mp.sin(b))**mp.mpf('1.5')*(mp.sin(s)/mp.sin(3*s))**3
    derivative_probes = {
        'G_v': (gv(v,eta), 0),
        'G_eta': (ge(v,eta), 0),
        'G_vv': (mp.diff(lambda x: gv(x,eta),v), 0),
        'G_vvv': (mp.diff(lambda x: gv(x,eta),v,2), 54),
        'G_vvvv': (mp.diff(lambda x: gv(x,eta),v,3), -648*mp.sqrt(2)),
        'G_v_eta': (mp.diff(lambda e: gv(v,e),eta),18*mp.sqrt(2)),
        'G_vv_eta': (mp.diff(lambda e: mp.diff(lambda x: gv(x,e),v),eta),-18),
        'G_eta_eta': (mp.diff(lambda e: ge(v,e),eta),36*mp.sqrt(2)),
        'A': (amplitude(v,eta),mp.mpf(9)/4),
        'log_A_v': (mp.diff(lambda x: mp.log(amplitude(x,eta)),v),7*mp.sqrt(2))}
    for name,(actual,expected) in derivative_probes.items():
        residual = abs(actual-expected)
        assert residual < mp.mpf('1e-85'), (name,residual)
        results['probes'].append({'name': name,'method':'direct trigonometric expressions and numerical differentiation at 100 digits',
                                 'residual':mp.nstr(residual,20), 'tolerance':'1e-85'})
    # A third formula: integrate the oriented, displaced cubic contour directly.
    # DLMF 9.5.4 supplies the contour representation; at Re(Y)=1 the Gaussian
    # modulus decays as exp(-y^2). This remains numerical integration, not an enclosure.
    contours=[]
    for zeta in (0,1):
        def f(y):
            Y=1+mp.j*y
            return mp.exp(Y**3/3-zeta*Y)
        values={}
        for k in (0,1,2,4):
            integrand=lambda y: mp.re((1+mp.j*y)**k*f(y))
            # Conjugate symmetry, upward contour and factor 1/(2pi i).
            values[k]=mp.quad(integrand,[0,1,2,4,6,9,12,16])/mp.pi
        ai,aip=mp.airyai(zeta),mp.airyai(zeta,1)
        assert abs(values[0]-ai)<mp.mpf('1e-80')
        assert abs(values[1]+aip)<mp.mpf('1e-80')
        integrated=(7*mp.sqrt(2)/3*values[1]-mp.sqrt(2)/3*values[4]
                    +zeta/(6*mp.sqrt(2))*values[2]+mp.sqrt(2)/4*zeta*zeta*values[0])
        residual=abs(integrated+3*mp.sqrt(2)*aip)
        assert residual<mp.mpf('1e-80'), residual
        contours.append({'zeta':zeta,'Ai_residual':mp.nstr(abs(values[0]-ai),20),
                         'first_correction_residual':mp.nstr(residual,20),'truncation':16,
                         'tolerance':'1e-80','exact_quantum_integral':False})
    results['displaced_cubic_contour_probes']=contours

# Property checks of exact field arithmetic with rationals, independent pair formulas.
field=author.Q2
for a in range(-3,4):
    for b in range(-3,4):
        x=field(Fraction(a,3),Fraction(b,5))
        if a or b:
            assert x/x==field(Fraction(1))
        assert x*x == field(Fraction(a*a,9)+Fraction(2*b*b,25),Fraction(2*a*b,15))
        assert (x+field(Fraction(2),Fraction(-1)))-field(Fraction(2),Fraction(-1))==x
results['exact_field_cases']=49
results['evidence_boundary']='Finite identities, numerical cubic-contour probes and six approximation rows only; not the exact double-sine integral or the uniform theorem.'
results['primary_sources']=['https://dlmf.nist.gov/9.2','https://dlmf.nist.gov/9.4','https://dlmf.nist.gov/9.5']
(OUT/'airy-independent.json').write_text(json.dumps(results,indent=2,allow_nan=False)+'\n')
print(json.dumps({'preservation_passed':True,'derivative_probes':len(derivative_probes),
                  'cubic_contour_probes':len(contours),'field_cases':49}))
