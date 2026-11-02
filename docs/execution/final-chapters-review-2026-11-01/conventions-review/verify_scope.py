"""Independent static identity and dependency review; no numerical replay."""
from pathlib import Path
import collections
import hashlib
import json
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/final-chapters-review-2026-11-01/conventions-review'
AUTHOR = OUT.parent / 'conventions-author'
BASE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
EXPECTED = {
    'book/chapters/32-open-questions.tex': 'c831bf85ab0c6cb7f5ed46509212ce5dc1549c05c5723be3c035c928a409fc21',
    'book/chapters/appendix-b-conventions.tex': 'b57a96b3f141e0d372b26dbb710d1ec0fa8e8a4a8ac8f0dd04b4ce0432f99a74',
    'book/claims/section32-appendixb.json': '0bf0a62df0e81ae502d0408935cb1fee80b0db9a85be8e0d58c73367773dfd5a',
}
issues, pins, source_pins, deps, fields = [], [], {}, [], []
def sha(data): return hashlib.sha256(data).hexdigest()
def require(ok, description, detail=None):
    if not ok: issues.append({'check': description, 'detail': detail})
def read_json(path): return json.loads(path.read_text())
def pin(base, entry, where):
    p = base / entry['path']
    if not p.is_file():
        issues.append({'check': 'missing pinned file', 'where': where, 'path': str(p)})
        return
    data = p.read_bytes()
    row = {'where': where, 'path': str(p.relative_to(ROOT.parent)), 'sha256': sha(data), 'bytes': len(data),
           'hash_match': sha(data) == entry['sha256'], 'size_match': 'bytes' not in entry or len(data) == entry['bytes']}
    pins.append(row)
    require(row['hash_match'] and row['size_match'], 'pin mismatch', row)
def recursive_pins(obj, base, where):
    if isinstance(obj, dict):
        if isinstance(obj.get('path'), str) and isinstance(obj.get('sha256'), str): pin(base, obj, where)
        for k, v in obj.items(): recursive_pins(v, base, where+'/'+k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj): recursive_pins(v, base, where+'/'+str(i))

ledger = read_json(ROOT/'book/claims/section32-appendixb.json')
initial = read_json(AUTHOR/'freeze-manifest.json')
final = read_json(AUTHOR/'revision-v2/freeze-manifest.json')
require(sha((AUTHOR/'revision-v2/freeze-manifest.json').read_bytes()) == 'ad43dfcb8eb18fa04a3f60ec88186066f873e132c0e9884459f1e91f18a84025', 'requested author freeze identity')
for path, digest in EXPECTED.items():
    pin(ROOT, {'path':path, 'sha256':digest}, 'review_subject')
    require((ROOT/path).read_bytes()==(AUTHOR/'revision-v2/after'/path).read_bytes(), 'canonical equals final snapshot',path)
for version, manifest, base in [('initial',initial,AUTHOR),('revision-v2',final,AUTHOR/'revision-v2')]:
    for e in manifest['evidence']: pin(base,e,version+'/evidence')
for e in initial['before_sources']: pin(AUTHOR/'before',e,'original_source')
recursive_pins(ledger, ROOT, 'ledger')
for path,digest in ledger['chapter_source_sha256'].items(): pin(ROOT,{'path':path,'sha256':digest},'chapter_source_sha256')

def approval_map(value):
    if isinstance(value, list): return {x['path']:x['sha256'] for x in value}
    return {k:(v['sha256'] if isinstance(v,dict) else v) for k,v in value.items()}
approval_counts = {}
for binding in ledger['prior_review_bindings']:
    manifest = read_json(ROOT/binding['review_manifest']['path'])
    approved = approval_map(manifest[binding['approval_field']])
    approval_counts[binding['id']] = len(binding['matched_files'])
    for entry in binding['matched_files']:
        require(approved.get(entry['path']) == entry['sha256'], 'prior approval field mismatch', entry['path'])
        source_pins[entry['path']] = entry['sha256']
for track in ledger['current_author_dependencies']:
    for entry in track['files']: source_pins[entry['path']] = entry['sha256']
    freeze=read_json(ROOT/track['freeze_manifest']['path'])
    actual=approval_map(freeze.get('canonical_files',freeze.get('files',[])))
    if not actual and 'sources' in freeze: actual=approval_map(freeze['sources'])
    if not actual and 'canonical_sources_sha256' in freeze:actual=freeze['canonical_sources_sha256']
    for entry in track['files']:
        require(actual.get(entry['path'])==entry['sha256'], 'track freeze mismatch',entry['path'])
    if 'independent_review_record' in track:
        accepted=read_json(ROOT/track['independent_review_record']['path'])['accepted_canonical_sha256']
        for entry in track['files']:
            require(accepted.get(entry['path'])==entry['sha256'],'accepted quantum source mismatch',entry['path'])

input_re=re.compile(r'\\(?:input|include)\{([^}]+)\}')
def file_text(path, baseline=False):
    if baseline:
        return subprocess.run(['git','show',f'{BASE}:{path}'],cwd=ROOT,check=True,capture_output=True,text=True).stdout
    return (ROOT/path).read_text()
def expand(path, baseline=False, visited=None):
    if visited is None: visited=[]
    visited.append(path)
    text=file_text(path,baseline)
    def sub(m):
        rel=m.group(1)
        if not rel.endswith('.tex'):rel+='.tex'
        candidate=str(Path(path).parent/rel)
        return expand(candidate,baseline,visited)[0]
    return input_re.sub(sub,text),visited
expanded,graph=expand('book/main.tex')
baseline,bgraph=expand('book/main.tex',True)
labels=lambda t:re.findall(r'\\label\{([^}]+)\}',t)
current_labels,baseline_labels=labels(expanded),labels(baseline)
added=[x for x in current_labels if x not in baseline_labels]
expected_added=['eq:figurekerneltail','eq:figurefiniteidentity','eq:localdistancehessian','eq:torustwistderivatives','eq:torusintegraltail','eq:Hpartialsumtail']
require(len(graph)==36 and len(set(graph))==36,'source graph count',graph)
require(len(current_labels)==613 and len(set(current_labels))==613,'current label total')
require(len(baseline_labels)==607,'baseline label total')
require([x for x in current_labels if x in baseline_labels]==baseline_labels,'ordered baseline label preservation')
require(set(added)==set(expected_added),'six explicit geodesic additions',added)
bibkeys=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',expanded)
require(len(bibkeys)==129 and len(set(bibkeys))==129,'bibliography key count')
label_sources={}
for path in graph:
    for label in labels(file_text(path)):label_sources[label]=path
require(len(ledger['claims'])==66 and len({c['id'] for c in ledger['claims']})==66,'66 unique claims')
claim_ids={c['id'] for c in ledger['claims']}
claimed_sources=set()
cache={}
for claim in ledger['claims']:
    for src in claim['dependency_sources']:
        require(src in source_pins or src in EXPECTED,'unbound dependency source',{'claim':claim['id'],'source':src})
        claimed_sources.add(src)
    for label in claim['dependency_labels']:
        require(label in label_sources,'missing dependency label',{'claim':claim['id'],'label':label})
        require(label_sources.get(label) in claim['dependency_sources'],'label missing declared dependency source',{'claim':claim['id'],'label':label,'actual':label_sources.get(label)})
    for dep in claim['dependencies']:
        path,cid=dep.split('#')
        require(path in source_pins,'unbound claim ledger',dep)
        if path not in cache:cache[path]={c['id']:c for c in read_json(ROOT/path)['claims']}
        dc=cache[path].get(cid)
        require(dc is not None,'missing claim pointer',dep)
        inherited=claim.get('inherited_statuses',{}).get(dep)
        if inherited is not None:require(inherited==dc['status'],'inherited claim status mismatch',{'dep':dep,'expected':dc['status'],'actual':inherited})
        deps.append({'claim':claim['id'],'dependency':dep,'status':dc['status'],'inherited_status':inherited})
    for key in claim.get('source_keys',[]):require(key in bibkeys,'missing source bibkey',key)

owned={p:(ROOT/p).read_text() for p in EXPECTED if p.endswith('.tex')}
for path,text in owned.items():
    old=(AUTHOR/'before'/path).read_text()
    require(labels(old)==labels(text),'owned label preservation',path)
    require(text.endswith('\n') and not text.endswith('\n\n'),'single final newline',path)
    require(not any(line.rstrip()!=line for line in text.splitlines()),'owned whitespace',path)
    for refs in re.findall(r'\\(?:eqref|ref|pageref|autoref)\*?\{([^}]+)\}',text):
        for ref in refs.split(','):require(ref.strip() in current_labels,'owned reference missing',ref)
    for cites in re.findall(r'\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}',text):
        for key in cites.split(','):require(key.strip() in bibkeys,'owned citation missing',key)
qre=r'\\begin\{question\}\[([^]]+)\]'
old_questions=re.findall(qre,(AUTHOR/'before/book/chapters/32-open-questions.tex').read_text())
questions=re.findall(qre,owned['book/chapters/32-open-questions.tex'])
require(questions==old_questions and len(questions)==15,'all question titles and order')
qclaims=[c for c in ledger['claims'] if 'question_number' in c]
require([c['title'] for c in qclaims]==questions and all(c['status']=='open_target' and c['publication_gate'] is False for c in qclaims),'open question ledger coverage')
def table_rows(text):
    body=text.split('\\endhead',1)[1].split('\\bottomrule',1)[0]
    return [tuple(x.strip() for x in row.strip().split('&',1)) for row in body.split('\\\\') if row.strip()]
rows=table_rows(owned['book/chapters/appendix-b-conventions.tex'])
old_rows=table_rows((AUTHOR/'before/book/chapters/appendix-b-conventions.tex').read_text())
row_claims=[c for c in ledger['claims'] if 'row_number' in c]
require(len(rows)==len(row_claims)==43,'all 43 convention rows')
for i,(row,c) in enumerate(zip(rows,row_claims),1):
    require(c['row_number']==i and c['quantity']==row[0] and c['statement']==row[1],'printed row ledger identity',c['id'])
coverage=ledger['original_row_coverage']
require(len(old_rows)==len(coverage)==28,'28 original rows')
require([r[0] for r in old_rows]==[c['original_quantity'] for c in coverage],'original coverage order')
for c in coverage:require(c['current_claim'] in claim_ids,'old row maps to a claim',c)
row_numbers={c['id']:c['row_number'] for c in row_claims}
mapped_rows=[row_numbers[c['current_claim']] for c in coverage]
require(len(set(mapped_rows))==28 and mapped_rows==sorted(mapped_rows),'original row order and unique coverage')
for support in ledger['computational_support_map']:
    if support['status']=='planned_contract_only':
        for group in support['groups']:
            for label in group['labels']:require(label in label_sources,'planned group formula label exists',label)
        continue
    for key in ['driver','readme']:require((ROOT/support[key]).is_file(),'support code/readme exists',support[key])
    data=read_json(ROOT/support['result']['path'])
    for key in support['result_fields']:
        cur=data;found=True
        for part in key.split('.'):
            if isinstance(cur,dict) and part in cur:cur=cur[part]
            else:found=False;break
        fields.append({'support':support['id'],'field':key,'present':found})
        require(found,'result field exists',fields[-1])
planned=[s for s in ledger['computational_support_map'] if s['status']=='planned_contract_only']
require(sum(len(s['groups']) for s in planned)==14,'14 planned companion groups')
require(len(ledger['computational_support_map'])-len(planned)==7,'seven existing result records')

before=read_json(AUTHOR/'revision-v2/before/book/claims/section32-appendixb.json')
allowed_top={'author_review','claims','computational_support_map','current_author_dependencies','external_source_policy','pending_dependencies','dependency_reconciliation'}
changed_top={k for k in before.keys()|ledger.keys() if before.get(k)!=ledger.get(k)}
require(changed_top<=allowed_top,'metadata-only top-level delta',sorted(changed_top))
for old,new in zip(before['claims'],ledger['claims']):
    changed={k for k in old.keys()|new.keys() if old.get(k)!=new.get(k)}
    require(changed<= {'dependencies','inherited_statuses','dependency_review_states','independent_review_boundary'},'claim content unchanged by v2',{'id':new['id'],'changed':sorted(changed)})
for path in owned:require((AUTHOR/'revision-v2/before'/path).read_bytes()==(ROOT/path).read_bytes(),'v2 chapter bytes unchanged',path)
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
        return [item for i,(x,y) in enumerate(zip(a,b)) for item in delta(x,y,path+'/'+str(i))]
    return [] if a==b else [{'path':path,'change':'updated'}]
actual_delta=delta(before,ledger)
declared_delta=read_json(AUTHOR/'revision-v2/metadata-delta.json')['changed_json_paths']
require(actual_delta==declared_delta,'exact declared metadata delta',{'actual':actual_delta,'declared':declared_delta} if actual_delta!=declared_delta else None)
for track in initial['author_dependency_snapshots']:
    for entry in track['files']:
        path=entry['path']
        if path.endswith('.tex'):
            data=(ROOT/path).read_bytes()
            expected=sha(data+b'\n') if track['track']=='geodesic-author' else sha(data)
            require(expected==entry['sha256'],'previous chapter observation reconciliation',path)

result={
 'scope':'Independent identity, dependency and structural checks only; no numerical replay, proof certification, build, commit or upload.',
 'status':'PASS' if not issues else 'FINDINGS', 'issues':issues,
 'requested_subject_hashes':EXPECTED,
 'author_freeze_sha256':sha((AUTHOR/'revision-v2/freeze-manifest.json').read_bytes()),
 'pins_checked':len(pins),'pin_results':pins,'prior_approval_counts':approval_counts,
 'prior_approved_files':sum(approval_counts.values()),'claim_count':len(ledger['claims']),
 'dependency_pointer_occurrences':len(deps),'unique_dependency_pointers':len({d['dependency'] for d in deps}),
 'dependency_results':deps,'result_field_checks':fields,
 'graph':graph,'graph_file_count':len(graph),'baseline_graph_file_count':len(bgraph),
 'baseline_labels':len(baseline_labels),'current_labels':len(current_labels),'added_labels':added,
 'bibliography_keys':len(bibkeys),'questions':questions,'convention_rows':len(rows),'original_rows':len(old_rows),
 'narrative_claims':len(ledger['claims'])-len(qclaims)-len(row_claims),
 'original_coverage':coverage,'metadata_delta_top_level':sorted(changed_top),
 'metadata_delta_paths':len(actual_delta),
}
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'independent-static-verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in {'pin_results','dependency_results','result_field_checks','graph','questions','original_coverage'}},indent=2))
