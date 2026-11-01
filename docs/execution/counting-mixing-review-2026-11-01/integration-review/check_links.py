from pathlib import Path
import json,re,urllib.parse
O=Path(__file__).resolve().parent; R=O.parents[2]/'consolidated'; E=O.parent
src=json.loads((O/'source-delta-manifest.json').read_text());references=[]
def record(p,link,base):
 link=urllib.parse.unquote(link.strip('<>'));u=urllib.parse.urlsplit(link)
 if u.scheme or link.startswith('#'):return
 q=(base/u.path).resolve()
 if not q.is_relative_to(R):return
 references.append({'source':p,'target':str(q.relative_to(R)),'fragment':u.fragment,'exists':q.exists()})
def leaves(v):
 if isinstance(v,dict):
  for x in v.values():yield from leaves(x)
 elif isinstance(v,list):
  for x in v:yield from leaves(x)
 elif isinstance(v,str):yield v
for f in src['files']:
 p=f['path'];q=R/p
 if q.suffix=='.md':
  for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)',q.read_text()):record(p,link,q.parent)
 if q.suffix=='.tex':
  for link in re.findall(r'\\path\{([^}]+)\}',q.read_text()):record(p,link,R)
 if p.startswith('book/claims/'):
  for s in leaves(json.loads(q.read_text())):
   if re.match(r'^(?:artifacts|book|docs|experiments|packages|research)/[^\s]+$',s):record(p,s,R)
missing=sorted({x['target'] for x in references if not x['exists']})
(O/'link-scan.json').write_text(json.dumps({'references':references,'unique_missing_targets':missing},indent=2)+'\n')
print('reference count',len(references));print('missing targets',len(missing));print('\n'.join(missing))
