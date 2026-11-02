from pathlib import Path
import json,hashlib,re,difflib,datetime,shutil
OUT=Path(__file__).parent
REVIEW=OUT.parent
BASE=REVIEW.parent
ROOT=BASE.parents[1]/'consolidated'
AUTHOR=BASE/'geodesic-author'
REV=AUTHOR/'revision-v2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(ok,message):
 if not ok:raise RuntimeError(message)
v2= json.loads((REV/'author-freeze-manifest-v2.json').read_text())
initial=json.loads((REVIEW/'initial-review-manifest.json').read_text())
author_initial=json.loads((AUTHOR/'author-freeze-manifest.json').read_text())
require(sha(REV/'author-freeze-manifest-v2.json')=='cf8a8f172a81a4cfb4090b44b65fc067cf70768b30ecfc80a858317649a44fb3','v2 author manifest mismatch')
require(sha(REVIEW/'initial-review-manifest.json')=='7386b5e022db352f9d5ce9506eeb907f46458baf6a2cac6029260fc6e90763f4','initial review manifest changed')
for p,h in initial['initial_evidence_sha256'].items():require(sha(REVIEW/p)==h,'initial reviewer evidence changed: '+p)
for p,h in author_initial['outer_evidence_sha256'].items():require(sha(AUTHOR/p)==h,'initial author evidence changed: '+p)
for p,h in v2['revision_evidence_sha256'].items():require(sha(REV/p)==h,'author v2 evidence mismatch: '+p)
actual={p:sha(ROOT/p) for p in v2['canonical_sources_sha256']}
require(actual==v2['canonical_sources_sha256'],'live source hash mismatch')
setsha=hashlib.sha256(json.dumps(actual,sort_keys=True,separators=(',',':')).encode()).hexdigest()
require(setsha=='b35883296116e459a702e0bc28b4f429875e2cec2cffb22910f02e5d0e8e87f9','final source set mismatch')
for p in actual:
 require((REV/'before'/p).read_bytes()==(REVIEW/'frozen-initial'/p).read_bytes(),'before mismatch: '+p)
 require((REV/'after'/p).read_bytes()==(ROOT/p).read_bytes(),'after/live mismatch: '+p)
 dst=OUT/'frozen-final'/p;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/p,dst)
changed=[p for p,h in actual.items() if initial['actual_reviewed_sources_sha256'][p]!=h]
require(changed==['book/chapters/19-pants-twists.tex','book/chapters/22-cusps-orthospectrum.tex','book/claims/sections17-22.json'],'unexpected changed path set')
# Require the source delta to be exactly the two reviewed replacements.
p19='book/chapters/19-pants-twists.tex'
old19='different roles there. Dehn--Thurston estimates compare combinatorial and\ngeometric length for simple multicurves\n\\cite[Theorem 3.4 and equation (3.6)]{MirzSimple}. The work'
new19='different roles there. Dehn--Thurston coordinates and the definition of\ncombinatorial length for simple multicurves are given in\n\\cite[Theorem 3.4 and equation (3.6)]{MirzSimple}. The comparison with\ngeometric length for an $L$-bounded pants decomposition is\n\\cite[Proposition 3.5 and equation (3.7), p.~107]{MirzSimple}. The work'
p22='book/chapters/22-cusps-orthospectrum.tex'
old22='\\cite{McShane}\\cite[Theorem 3 and the following measure discussion,\npp.~3--4]{McShanePants}.'
new22='\\cite{McShane}\\cite[Theorem 3, p.~4, and the paragraph after\nCorollary 5, p.~5]{McShanePants}.'
for p,before,after in [(p19,old19,new19),(p22,old22,new22)]:
 src=(REVIEW/'frozen-initial'/p).read_text()
 require(src.count(before)==1,'replacement anchor not unique: '+p)
 require(src.replace(before,after)==(ROOT/p).read_text(),'non-citation source delta: '+p)
# Independently list every changed JSON leaf rather than trusting the author's diff.
def changes(a,b,path=()):
 if type(a)!=type(b):return [(path,a,b)]
 if isinstance(a,dict):
  require(set(a)==set(b),'ledger key set changed: '+str(path))
  return [d for k in a for d in changes(a[k],b[k],path+(k,))]
 if isinstance(a,list):
  if len(a)!=len(b):return [(path,a,b)]
  return [d for k in range(len(a)) for d in changes(a[k],b[k],path+(k,))]
 return [] if a==b else [(path,a,b)]
old=json.loads((REVIEW/'frozen-initial/book/claims/sections17-22.json').read_text())
new=json.loads((ROOT/'book/claims/sections17-22.json').read_text())
ledger_delta=changes(old,new)
sourceidx={s['key']:i for i,s in enumerate(old['sources'])};claimidx={c['id']:i for i,c in enumerate(old['claims'])}
allowed=[('sources',sourceidx['MirzSimple'],'pins'),('sources',sourceidx['MirzSimple'],'checked'),('sources',sourceidx['McShanePants'],'pins'),('claims',claimidx['19.01'],'source_pins'),('claims',claimidx['19.09'],'hypotheses'),('claims',claimidx['19.09'],'exact_formulas'),('claims',claimidx['19.09'],'source_pins'),('claims',claimidx['22.03'],'proof_summary'),('claims',claimidx['22.03'],'source_pins'),('chapter_source_snapshots',p19),('chapter_source_snapshots',p22)]
require(all(any(path[:len(prefix)]==prefix for prefix in allowed) for path,_,_ in ledger_delta),'unexpected ledger field change')
require(new['chapter_source_snapshots']=={p:actual[p] for p in new['chapter_sources']},'ledger chapter hashes not current')
require(len(new['claims'])==59 and [c['id'] for c in new['claims']]==[c['id'] for c in old['claims']],'claim coverage changed')
labels=[]
for p in new['chapter_sources']:
 before=re.findall(r'\\label\{([^}]+)\}',(REVIEW/'frozen-initial'/p).read_text())
 after=re.findall(r'\\label\{([^}]+)\}',(ROOT/p).read_text())
 require(before==after,'label order changed: '+p)
 labels+=after
require(len(labels)==54 and len(set(labels))==54,'owned-label count changed')
require(set(labels)==set(new['chapter_labels']+[l for c in new['claims'] for l in c['labels']]),'owned label coverage gap')
require(new['computational_companion']==old['computational_companion'],'companion ledger scope changed')
require(sha(AUTHOR/'companion-contract.md')=='2a62a149e7f5f88027329c24ba3a4720407debfed2fb78945350f23b6fce85a6','contract changed')
require(sha(REVIEW/'companion-contract-review.json')=='be7debaf190ecd960d0caeca6b82e884407b6da04e72234e16a60762980bc82b','contract acceptance changed')
# Produce a new final coverage binding, preserving every initial record.
claims=json.loads((REVIEW/'initial-claim-review.json').read_text())
for c in claims['coverage']:
 c['source_pin_decision']='accepted_at_recorded_access_scope'
 if c['id']=='19.09':c['review_note']='R1 closed. The revised prose and ledger distinguish Theorem 3.4/(3.6) coordinates/definition from Proposition 3.5/(3.7), p.107, length comparison and now state the L-bounded hypothesis explicitly. All other mathematical review notes remain applicable.'
 if c['id']=='22.03':c['review_note']='R2 closed. The revised prose/source record/claim pin Theorem 3 to printed p.4 and the measure-zero paragraph after Corollary 5 to printed p.5. The no-geodesic-boundary scope and mathematical statements are unchanged.'
 c['final_ledger_sha256']=actual['book/claims/sections17-22.json']
claims['source_set_sha256']=setsha
(OUT/'final-claim-coverage.json').write_text(json.dumps(claims,indent=2)+'\n')
labelcov=json.loads((REVIEW/'initial-label-review.json').read_text())
for row in labelcov['labels']:row['source_sha256']=actual[row['source']]
labelcov['source_set_sha256']=setsha
(OUT/'final-label-coverage.json').write_text(json.dumps(labelcov,indent=2)+'\n')
result={'status':'passed_independent_targeted_revision_verification','script_sha256':sha(Path(__file__)),'recorded_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'canonical_sources_sha256':actual,'canonical_source_set_sha256':setsha,'changed_paths':changed,'source_delta_exactly_two_reviewed_replacements':True,'ledger_changed_leaves':[{'path':list(p),'before':a,'after':b} for p,a,b in ledger_delta],'initial_author_and_review_evidence_unchanged':True,'all_v2_snapshot_and_evidence_hashes_match':True,'claims':59,'owned_labels':54,'contract_unchanged':True,'contract_acceptance_unchanged':True,'no_scientific_rerun':True,'no_canonical_edits':True}
(OUT/'independent-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['canonical_sources_sha256','ledger_changed_leaves']},indent=2))
