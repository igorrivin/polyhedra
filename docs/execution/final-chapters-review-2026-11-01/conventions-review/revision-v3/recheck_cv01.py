"""Targeted independent static recheck of CV01; does not execute experiments."""
from pathlib import Path
import hashlib
import json
import re

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
REVIEW = ROOT.parent/'execution/final-chapters-review-2026-11-01/conventions-review'
OUT = REVIEW/'revision-v3'
AUTHOR = REVIEW.parent/'conventions-author/revision-v3'
EXPECTED = {
 'book/chapters/32-open-questions.tex':'50fc264bbfc55fc19cb79dc09aa7a828b2cba479f6b3afb1c62459e0d31c9b5d',
 'book/chapters/appendix-b-conventions.tex':'b57a96b3f141e0d372b26dbb710d1ec0fa8e8a4a8ac8f0dd04b4ce0432f99a74',
 'book/claims/section32-appendixb.json':'488298ff34c229222010d03452f18e4f3855b9c7026589c74a28fbece04f3a9e',
}
issues=[]
def sha(data):return hashlib.sha256(data).hexdigest()
def js(path):return json.loads(path.read_text())
def check(condition,name,detail=None):
 if not condition:issues.append({'check':name,'detail':detail})
def pin(path,digest,size=None):
 data=path.read_bytes()
 check(sha(data)==digest and (size is None or len(data)==size),'hash/size identity',str(path))
freeze=js(AUTHOR/'freeze-manifest.json')
pin(AUTHOR/'freeze-manifest.json','839ad986f3162e849c362c3c43c666913fd601fbfea55d9264c41a3b5d1affe4')
prior=js(REVIEW/'independent-static-verification.json')
pin(REVIEW/'review-manifest.json','0fbbfc5c63d3e9b59cc3f8a506d202a057ae0dcb907eff5a411316537c63c3c1')
for path,e in js(REVIEW/'review-manifest.json')['evidence'].items():pin(REVIEW/path,e['sha256'],e['bytes'])
for e in freeze['evidence']:pin(AUTHOR/e['path'],e['sha256'],e['bytes'])
preserved=js(AUTHOR/'preserved-evidence-before.json')['files']
for e in preserved:pin(REVIEW.parent/e['path'],e['sha256'],e['bytes'])
for path,digest in EXPECTED.items():
 pin(ROOT/path,digest)
 check((ROOT/path).read_bytes()==(AUTHOR/'after'/path).read_bytes(),'live equals frozen after',path)
 pin(AUTHOR/'before'/path,prior['requested_subject_hashes'][path])
 for where in ['before','after']:
  data=(AUTHOR/where/path).read_bytes()
  dest=OUT/where/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)

# Reuse the prior verification only after rechecking its hash-bound inputs.
current_owned={(ROOT/p).resolve():d for p,d in EXPECTED.items()}
for row in prior['pin_results']:
 p=ROOT.parent/row['path']
 if p.resolve() in current_owned:pin(p,current_owned[p.resolve()])
 else:pin(p,row['sha256'],row['bytes'])

old=js(AUTHOR/'before/book/claims/section32-appendixb.json')
new=js(ROOT/'book/claims/section32-appendixb.json')
def delta(a,b,path=''):
 if type(a) is not type(b):return [{'path':path,'change':'updated'}]
 if isinstance(a,dict):
  result=[]
  for key in sorted(a.keys()|b.keys()):
   if key not in a:result.append({'path':path+'/'+key,'change':'added'})
   elif key not in b:result.append({'path':path+'/'+key,'change':'removed'})
   else:result.extend(delta(a[key],b[key],path+'/'+key))
  return result
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':path,'change':'updated'}]
  return [v for i,(x,y) in enumerate(zip(a,b)) for v in delta(x,y,path+'/'+str(i))]
 return [] if a==b else [{'path':path,'change':'updated'}]
changes=delta(old,new)
check(len(changes)==7 and changes==freeze['changed_json_paths']==js(AUTHOR/'delta.json')['changed_json_paths'],'exact seven JSON changes',changes)
check(old['claims'][1:]==new['claims'][1:],'other 65 claims unchanged')
for key in old:
 if key not in {'claims','chapter_source_sha256'}:check(old[key]==new[key],'other metadata unchanged',key)
check(new['chapter_source_sha256']=={p:d for p,d in EXPECTED.items() if p.endswith('.tex')},'chapter source pins')
q1=new['claims'][0]
check(q1['id']=='s32.q01' and q1['status']=='open_target' and q1['publication_gate'] is False,'Q1 remains open and no publication gate')
check(q1['dependency_labels']==['eq:hyperidealdensity','eq:basevolumes','sec:hyperideal'],'correct positive-boundary locator')
check(q1['source_keys']==['Zonneveld'],'primary source key')
src=js(ROOT/'book/claims/sections1-6.json')
record=q1['source_statement_locator']['inherited_source_record']
path,pointer=record.split('#');resolved=js(ROOT/path)
for part in pointer.strip('/').split('/'):resolved=resolved[part]
check(resolved==src['sources']['Zonneveld'],'inherited Zonneveld source pointer resolves')
check(resolved['location']=='Theorem 3','source locator is Theorem 3')
dep=next(c for c in src['claims'] if c['id']=='s4.tree_density')
check(any('Zonneveld Theorem3: positive boundaries' in e for e in dep['evidence']),'bundled claim contains positive-boundary sequel')
check('Its BMZ origin-cusp hypotheses' in q1['dependency_usage']['book/claims/sections1-6.json#s4.tree_density'],'dependency-use disambiguation')

oldtext=(AUTHOR/'before/book/chapters/32-open-questions.tex').read_text()
newtext=(ROOT/'book/chapters/32-open-questions.tex').read_text()
oldpara='''hyperideal coordinates? The tree decomposition~\\eqref{eq:treevolume}
provides a separate volume calculation; it does not identify its
coordinates with the hyperideal angle cells.'''
newpara='''hyperideal coordinates? The positive-boundary extension described in
Section~\\ref{sec:hyperideal} uses a selected pair $L_1<L_2$ to give a
full-measure decomposition into tree and double-tree cells
\\cite[Theorem~3]{Zonneveld}. Equal-length volume values follow by
continuity. These spine/tree cells are not identified with the
hyperideal angle cells.'''
check(oldtext.count(oldpara)==1 and oldtext.replace(oldpara,newpara)==newtext,'only exact requested paragraph changed')
check((ROOT/'book/chapters/appendix-b-conventions.tex').read_bytes()==(AUTHOR/'before/book/chapters/appendix-b-conventions.tex').read_bytes(),'Appendix B byte-identical')

graph=[]
def expand(path):
 graph.append(path);text=(ROOT/path).read_text()
 return re.sub(r'\\(?:input|include)\{([^}]+)\}',lambda m:expand(str(Path(path).parent/(m[1] if m[1].endswith('.tex') else m[1]+'.tex'))),text)
expanded=expand('book/main.tex')
labels=re.findall(r'\\label\{([^}]+)\}',expanded)
bib=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',expanded)
check(graph==prior['graph'] and len(graph)==36,'36-file graph unchanged')
check(len(labels)==len(set(labels))==613,'613 unique labels')
check(len(bib)==len(set(bib))==129,'129 bibliography keys')
check(re.findall(r'\\label\{([^}]+)\}',oldtext)==re.findall(r'\\label\{([^}]+)\}',newtext),'owned labels unchanged')
check(re.findall(r'\\begin\{question\}\[([^]]+)\]',newtext)==prior['questions'],'15 titles and order preserved')
for ref in re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',newtext):check(ref in labels,'reference resolves',ref)
for cite in re.findall(r'\\cite(?:\[[^]]*\])*\{([^}]+)\}',newtext):
 for key in cite.split(','):check(key in bib,'citation resolves',key)
for path in EXPECTED:
 data=(ROOT/path).read_text()
 check(data.endswith('\n') and not data.endswith('\n\n') and all(x==x.rstrip() for x in data.splitlines()),'owned whitespace',path)

result={'status':'PASS' if not issues else 'FINDINGS','issues':issues,'reviewed_author_freeze_sha256':sha((AUTHOR/'freeze-manifest.json').read_bytes()),'accepted_subject_sha256':EXPECTED,'source_paragraph_delta_only':True,'changed_json_paths':changes,'other_claims_unchanged':65,'prior_pin_occurrences_rechecked':len(prior['pin_results']),'prior_evidence_inventory_preserved':len(preserved),'original_reviewer_manifest_preserved':True,'source_record':resolved,'dependency_use':q1['dependency_usage'],'graph_files':len(graph),'labels':len(labels),'bibliography_keys':len(bib),'inherited_initial_review':'../review-report.md and ../claim-coverage.json, exact identities in ../review-manifest.json','scope':'Targeted source/metadata review; no numerical execution or whole-external-proof audit.'}
(OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'source_record','dependency_use','changed_json_paths'}},indent=2))
if issues:raise SystemExit(1)
