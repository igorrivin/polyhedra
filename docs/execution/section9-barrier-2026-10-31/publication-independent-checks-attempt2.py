"""Read-only source, artifact and independent reference checks for review."""
from fractions import Fraction
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit
import mpmath as mp

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EVIDENCE=ROOT.parent/'execution/section9-barrier-2026-10-31'
PREVIEW=Path('/var/folders/07/k5d5zt815j92q33gdb61j1280000gn/T/polyhedra-barrier-integration-preview-20261031-baylv1cs')
SITE=PREVIEW/'site/section9'
old=lambda name: subprocess.check_output(['git','show','014d1c4e70dfdfc852fa542f3a9c469f08dbd618:'+name],cwd=ROOT).decode()
chapter_path='book/chapters/09-volume-hessians.tex'
chapter=(ROOT/chapter_path).read_text()
original=old(chapter_path)
checks={}
patterns={
 'labels':r'\\label\{([^}]+)\}',
 'inline_math':r'(?<!\\)\$(?!\$).*?(?<!\\)\$',
 'display_math':r'\\\[.*?\\\]',
 'numbered_math_environments':r'\\begin\{(?:equation|align)\*?\}.*?\\end\{(?:equation|align)\*?\}',
 'proof_environments':r'\\begin\{proof\}.*?\\end\{proof\}',
 'proposition_environments':r'\\begin\{proposition\}.*?\\end\{proposition\}',
 'tikz_figures':r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',
 'citations':r'\\cite(?:\[[^]]*\])?\{[^}]+\}',
}
for name,pattern in patterns.items():
 a,b=re.findall(pattern,original,re.S),re.findall(pattern,chapter,re.S)
 assert a==b,name
 checks[name]={'unchanged':True,'count':len(b)}
original_ledger=json.loads(old('book/claims/section9.json'))
ledger=json.loads((ROOT/'book/claims/section9.json').read_text())
assert len(original_ledger['claims'])==len(ledger['claims'])==26
for a,b in zip(original_ledger['claims'],ledger['claims']):
 for key in ('id','hypotheses','labels','review_evidence','source_evidence','status'):
  assert a.get(key)==b.get(key),(a['id'],key)
checks['claims']={'count':26,'proof_status_hypotheses_labels_and_review_evidence_unchanged':True}

class Parse(HTMLParser):
 def __init__(self,text):
  super().__init__();self.ids=[];self.links=[];self.math=0;self.figures=0;self.feed(text)
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if 'id' in attrs:self.ids.append(attrs['id'])
  for key in ('href','src'):
   if key in attrs:self.links.append(attrs[key])
  self.math+=tag=='math';self.figures+=tag=='figure'
parsed={p:Parse(p.read_text()) for p in SITE.glob('*.html')}
htmlchecks={}
for page,doc in parsed.items():
 assert len(doc.ids)==len(set(doc.ids)),str(page)
 local=0
 for value in doc.links:
  uri=urlsplit(value)
  if uri.scheme or uri.netloc:continue
  target=(page.parent/unquote(uri.path)).resolve() if uri.path else page.resolve()
  assert target.is_file(),(page.name,value)
  if uri.fragment and target.suffix=='.html':
   target_doc=parsed.get(target) or Parse(target.read_text())
   assert unquote(uri.fragment) in target_doc.ids,(page.name,value)
  local+=1
 htmlchecks[page.name]={'local_links_and_resources':local,'mathml':doc.math,'figures':doc.figures,'unique_ids':len(doc.ids)}
assert htmlchecks['chapter.html']['mathml']==209
assert htmlchecks['chapter.html']['figures']==2
chapterdoc=parsed[SITE/'chapter.html']
assert set(re.findall(patterns['labels'],chapter))<=set(chapterdoc.ids)
assert len([x for x in chapterdoc.ids if x.startswith('ref-')])==12
checks['static_html']=htmlchecks

# Rebuild the three mathematical maximum values using complex shape geometry
# and Bloch-Wigner, independently of the driver and production angle routines.
mp.mp.dps=90
bw=lambda z:mp.im(mp.polylog(2,z))+mp.arg(1-z)*mp.log(abs(z))
points=[mp.mpc(0,0),mp.mpc(4,0),mp.mpc(4,3),mp.mpc(0,3),mp.mpc(1,mp.mpf('.5'))]
faces=[(4,0,1),(4,1,2),(4,2,3),(4,3,0)]
triangle=bw(mp.mpc(mp.mpf('.5'),mp.sqrt(3)/2))
disk=mp.fsum(bw((points[c]-points[a])/(points[b]-points[a])) for a,b,c in faces)
a,b=mp.mpf('.1'),mp.mpf(1)
boundary=bw(mp.sin(b)/mp.sin(mp.pi-a-b)*mp.exp(mp.j*a))
refs={'regular-triangle':triangle,'asymmetric-disk':disk,'boundary-maximum':boundary}
reported=json.loads((SITE/'downloads/barrier-result.json').read_text())
comparison={}
for case in reported['cases']:
 expected=mp.mpf(case['reference']['exact_space_maximum_volume_decimal'])
 delta=abs(refs[case['id']]-expected)
 assert delta<mp.mpf('1e-63')
 comparison[case['id']]={'independent_Bloch_Wigner_maximum':mp.nstr(refs[case['id']],75),'difference_from_report':mp.nstr(delta,20)}
xy=[(Fraction(0),Fraction(0)),(Fraction(4),Fraction(0)),(Fraction(4),Fraction(3)),(Fraction(0),Fraction(3)),(Fraction(1),Fraction(1,2))]
cot=[]
for face in faces:
 row=[]
 for k in range(3):
  p,q,r=(xy[face[j%3]] for j in (k,k+1,k+2))
  u,v=([q[j]-p[j] for j in range(2)],[r[j]-p[j] for j in range(2)])
  row.append(sum(x*y for x,y in zip(u,v))/abs(u[0]*v[1]-u[1]*v[0]))
 cot.append(row)
barrier_derivative=sum(row[1]-row[2] for row in cot)
assert barrier_derivative==Fraction(-28,15)
boundary_derivative=mp.log(4*mp.sin(mp.mpf('.1'))/mp.sin(1))
assert boundary_derivative<0
checks['independent_references']={'method':'90-digit complex Bloch-Wigner values using direct geometric shapes; exact rational cotangent derivative; no imports from driver or toolkit','maxima':comparison,'disk_barrier_derivative_exact':str(barrier_derivative),'boundary_right_derivative':mp.nstr(boundary_derivative,75),'interpretation':'multiprecision numerical comparisons, not interval enclosures'}
checks['visual_review']={'pdf_sha256':sha256((SITE/'downloads/section9.pdf').read_bytes()).hexdigest(),'pages_inspected':list(range(1,11)),'observations':'All ten rendered pages independently opened and visually inspected; no observed clipping, collisions, unreadable formulas, or missing glyphs. Computational addendum is legible on page 9.','page_sha256':{p.name:sha256(p.read_bytes()).hexdigest() for p in sorted((PREVIEW/'chapter-build/rendered-pages').glob('*.png'))}}
checks['scope']='Independent dirty-preview review. Core fix and strict final export still pending at the time of this script; old preview source and PDF hashes retained.'
(EVIDENCE/'publication-independent-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
print(json.dumps(checks,indent=2))
