from pathlib import Path
from hashlib import sha256
import json,re,subprocess,shutil,difflib,datetime,zipfile
ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra'); R=ROOT/'consolidated'; E=ROOT/'execution/counting-mixing-review-2026-11-01'; O=E/'integration-review/revision-v2'; B=E/'integration-author/snapshots/before'; BASE='9c8b61790aaa674902b9d60e80122c318a578bcc'
def h(p):
 d=sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):d.update(b)
 return d.hexdigest()
def read(p):return json.loads(p.read_text())
def write(name,v): (O/name).write_text(json.dumps(v,indent=2)+'\n')
def git(*a,cwd=R): return subprocess.check_output(['git',*a],cwd=cwd).decode().strip()
def check(c,msg):
 if not c: raise AssertionError(msg)
check(git('rev-parse','HEAD')==BASE,'HEAD drift')
inventory=read(E/'structure/baseline-tracked-inventory.json')['files']; existing={x['path']:x for x in inventory}; changed=[]; unchanged=[]; missing=[]
for f in inventory:
 p=R/f['path']
 if not p.exists():missing.append(f['path'])
 elif h(p)!=f['sha256']:changed.append(f['path'])
 else: unchanged.append(f['path'])
new=git('ls-files','--others','--exclude-standard','-z').split('\0'); new=[p for p in new if p]
expected_existing={'INTEGRATION_PLAN.md','README.md','book/README.md','book/chapters/30-sharp-diagnostics.tex','book/claims/section30.json','book/computational-status.md','book/polyhedral_volumes_and_geodesic_identities.tex','docs/INTEGRATION_STATUS.md'}
check(set(changed)==expected_existing,(changed,'changed scope'));check(not missing,missing);check(len(new)==25,('new count',new)); check(len(inventory)==1914,'baselinecount')
source_paths=sorted(changed+new);write('source-delta-manifest.json',{'baseline_commit':BASE,'existing_modified_count':len(changed),'new_count':len(new),'files':[{ 'path':p,'status':'modified' if p in existing else 'new','sha256':h(R/p),'bytes':(R/p).stat().st_size,'baseline_sha256':existing.get(p,{}).get('sha256')} for p in source_paths]})
# Recheck original external repositories and archive independently.
orig=read(ROOT/'audit/2026-10-31/source-inventory.json'); originals=[]
for repo in orig['repositories']:
 p=ROOT/repo['path']; mismatches=[x['path'] for x in repo['files'] if not (p/x['path']).is_file() or h(p/x['path'])!=x['sha256']]
 check(not mismatches,mismatches); check(git('rev-parse','HEAD',cwd=p)==repo['head'],'original head drift')
 originals.append({'path':repo['path'],'head':repo['head'],'checked_files':len(repo['files']),'mismatches':mismatches,'status':git('status','--porcelain',cwd=p)})
a=orig['monograph_archive'];check(h(ROOT/a['path'])==a['sha256'],'archive drift')
with zipfile.ZipFile(ROOT/a['path']) as z:
 check(all(sha256(z.read(x['member'])).hexdigest()==x['sha256'] for x in a['members']),'archive members drift')
write('preservation-receipt.json',{'baseline_commit':BASE,'baseline_tracked_count':len(inventory),'unchanged_baseline_paths':unchanged,'authorized_modified_paths':changed,'missing_paths':missing,'materialized_lfs_verified':sum(x.get('materialized_lfs',False) for x in inventory),'original_repositories':originals,'original_archive':{'path':a['path'],'sha256':h(ROOT/a['path']),'verified_members':len(a['members'])},'scope':'All baseline materialized file bytes verified; no cleanup, canonical edits, commit or upload.'})
# Reconstruct active TeX graph and expanded ordering with strict book-local resolution.
pat=re.compile(r'^\\(?:input|include)\{([^}]+)\}\n',re.M)
def expand(root,rel='book/main.tex',stack=(),graph=None):
 if graph is None:graph={}
 check(rel not in stack,'cyclic TeX input');p=root/rel;s=p.read_text();graph[rel]={'sha256':h(p),'bytes':p.stat().st_size}
 def repl(m):
  q=(root/'book'/m.group(1)).resolve()
  if not q.suffix:q=q.with_suffix('.tex')
  check(q.is_relative_to((root/'book').resolve()),'external input');return expand(root,str(q.relative_to(root)),stack+(rel,),graph)[0]
 return pat.sub(repl,s),graph
expanded,graph=expand(R);before,baselinegraph=expand(E/'structure/baseline-source-graph');extracted,extgraph=expand(E/'structure/extracted-source-graph')
check(before==extracted,'structural extraction expansion drift')
labels=lambda s:re.findall(r'\\label\{([^}]+)\}',s)
bibs=lambda s:re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',s)
check(labels(expanded)==labels(before),'label order drift');check(len(labels(expanded))==607,'label count');check(bibs(expanded)==bibs(before),'bibliography key order drift');check(len(bibs(expanded))==129,'bib count');check(len(graph)==26,'graph count');check(set(graph)==set(extgraph),'active graph difference')
# Prior approvals pin each before-integration mathematical chapter and ledger.
a=read(E/'algebra-review/approved-hash-manifest.json');d=read(E/'dynamics-review/targeted-acceptance-v2.json');ar=read(E/'arithmetic-review/review-decisions.json');co=read(E/'computation-review/revision-v2/approved-manifest-v2.json')
approved={p:v['sha256'] for p,v in a['approved_files'].items()};approved.update({x['path']:x['sha256'] for x in d['approved_canonical_files']});approved.update({p:v for p,v in ar['approved_exact_source_sha256'].items() if p.startswith('book/')})
for p,v in approved.items():check(h(B/p)==v,('review snapshot mismatch',p))
code={x['path']:x['sha256'] for x in co['approved_sources']};code.update({p:v for p,v in ar['approved_exact_source_sha256'].items() if p.startswith('experiments/')});check(len(code)==14,'code count')
for p,v in code.items():check(h(R/p)==v,('reviewed code drift',p))
applied=read(E/'integration-author/layout-revision-v2/applied-source-manifest-v2.json');check(h(E/'integration-author/layout-revision-v2/applied-source-v2.diff')==applied['applied_diff_sha256'],'applied diff hash');check(h(E/'integration-author/layout-revision-v2/preservation-v2.json')==applied['preservation_check_sha256'],'preservation hash')
for p,v in applied['files'].items(): check(h(R/p)==v['canonical_sha256'] and h(B/p)==v['before_sha256'],('application hash',p))
proof=re.compile(r'\\begin\{(proof|theorem|lemma|proposition|corollary)\}.*?\\end\{\1\}',re.S);proofs={};ledger_checks={};deltas=[]
def leaves(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'before':a,'after':b}]
 if isinstance(a,dict):return sum([leaves(a.get(k),b.get(k),path+'/'+k) for k in sorted(set(a)|set(b))],[])
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':path,'before':a,'after':b}]
  return sum([leaves(x,y,path+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))],[])
 return [] if a==b else [{'path':path,'before':a,'after':b}]
for p in approved:
 if p.endswith('.tex'):
  old=(B/p).read_text();now=(R/p).read_text();pa=[m.group() for m in proof.finditer(old)];pn=[m.group() for m in proof.finditer(now)];check(pa==pn,('formal block drift',p));proofs[p]=len(pa)
 else:
  old=read(B/p);now=read(R/p);protected=[]
  for c0,c1 in zip(old['claims'],now['claims']):
   fields=[k for k in c0 if k in ['id','labels','status','proof_status','hypotheses','claim','statement','source_pin','source_pins']]
   check(all(c0[k]==c1.get(k) for k in fields),('ledger protected drift',p,c0.get('id')));protected.append({k:c1[k] for k in fields})
  check(len(old['claims'])==len(now['claims']),('claim count drift',p));ledger_checks[p]={'count':len(protected),'protected_claim_fields':protected};deltas.append({'path':p,'changes':leaves(old,now)})
write('ledger-deltas.json',deltas);write('ledger-snapshot-check.json',{'total_claims':sum(v['count'] for v in ledger_checks.values()),'files':ledger_checks,'formal_blocks_preserved':proofs})
write('source-identity-receipt.json',{'approved_mathematical_before_hashes':approved,'reviewed_code_hashes_unchanged':code,'integration_files_checked':len(applied['files']),'integration_files_changed':len(applied['changed_files']),'labels':labels(expanded),'label_count':len(labels(expanded)),'bibliography_keys':bibs(expanded),'bibliography_key_count':len(bibs(expanded)),'labels_and_bibkeys_same_as_baseline_order':True,'active_graph_count':len(graph),'active_graph_path_set_same_as_extraction':True})
for p in graph:
 out=O/'frozen-source'/p;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/p,out);check(h(out)==graph[p]['sha256'],'freeze copy')
write('tex-input-freeze.json',{'captured_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline_commit':BASE,'source_state':'reviewed precommit working source; not a postcommit build','source_root':str(O/'frozen-source'),'count':len(graph),'files':graph})
(O/'expanded-reviewed-source.tex').write_text(expanded)
main='book/polyhedral_volumes_and_geodesic_identities.tex';s0=(E/'structure/extracted-source-graph'/main).read_text();s1=(R/main).read_text();patch=''.join(difflib.unified_diff(s0.splitlines(True),s1.splitlines(True),fromfile='a/'+main,tofile='b/'+main));(O/'main-after-extraction.diff').write_text(patch)
check(h(R/main)==d['bibliography_scope']['main_sha256_inspected'],'main source not pinned by metadata review')
write('initial-verification-summary.json',{'passed':True,'modified_existing':len(changed),'new':len(new),'unchanged_baseline':len(unchanged),'lfs':sum(x.get('materialized_lfs',False) for x in inventory),'original_file_counts':[x['checked_files'] for x in originals],'reviewed_code_files':len(code),'formal_blocks':sum(proofs.values()),'claims':sum(v['count'] for v in ledger_checks.values()),'labels':len(labels(expanded)),'bibkeys':len(bibs(expanded)),'tex_inputs':len(graph)})
print(json.dumps(read(O/'initial-verification-summary.json'),indent=2))
