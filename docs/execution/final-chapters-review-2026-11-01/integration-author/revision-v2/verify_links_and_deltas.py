"""Read-only follow-up checks for the authored integration freeze."""
from hashlib import sha256
from pathlib import Path
import json
import re
import subprocess

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER=ROOT.parent/'execution/final-chapters-review-2026-11-01'
OUT=OUTER/'integration-author/revision-v2'
REL='docs/execution/final-chapters-review-2026-11-01/'


def require(condition,message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def encode(data):
    return (json.dumps(data,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()


def migrate(value):
    if isinstance(value,dict): return {k:migrate(v) for k,v in value.items()}
    if isinstance(value,list): return [migrate(v) for v in value]
    if isinstance(value,str):
        for prefix in ['../execution/final-chapters-review-2026-11-01/','execution/final-chapters-review-2026-11-01/']:
            if value.startswith(prefix): return (REL+value[len(prefix):]).removesuffix(' (outer workspace)')
    return value


inventory=json.loads((OUT/'source-inventory.json').read_text())
for name,expected in inventory['source_sha256'].items():
    require(digest(ROOT/name)==expected,'current source drift '+name)
q=json.loads((ROOT/'book/claims/sections10-11.json').read_text())
g=json.loads((ROOT/'book/claims/sections17-22.json').read_text())
c=json.loads((ROOT/'book/claims/section32-appendixb.json').read_text())
oldc=json.loads((OUT/'before/book/claims/section32-appendixb.json').read_text())
for ledger,key in [(q,'chapter_source_sha256'),(g,'chapter_source_snapshots'),(c,'chapter_source_sha256'),(q,'reviewed_dependency_sha256')]:
    for name,expected in ledger[key].items(): require(digest(ROOT/name)==expected,'live dependency hash '+name)
for record in c['current_author_dependencies']:
    for row in record['files']:
        path=ROOT/row['path']
        require(digest(path)==row['sha256'] and path.stat().st_size==row['bytes'],'current integrated binding '+row['path'])
require(c['historical_author_dependencies']==migrate(oldc['current_author_dependencies']),'historical dependency observations changed')
require(c['historical_author_dependency_reconciliation']==migrate(oldc['dependency_reconciliation']),'historical reconciliation changed')
require(c['computational_support_map'][:7]==oldc['computational_support_map'][:7],'prior seven result records')
for row in c['computational_support_map'][:7]:
    result=row['result']; path=ROOT/result['path']
    require(digest(path)==result['sha256'] and path.stat().st_size==result['bytes'],'prior result drift '+result['path'])

# Complete dependency ID lookup; inherited mathematical statuses stay exact.
dependency_count=0
for name,ledger in [('sections10-11',q),('sections17-22',g),('section32-appendixb',c)]:
    local_ids={x['id'] for x in ledger['claims']}
    for claim in ledger['claims']:
        for dep in claim.get('dependencies',[]):
            if dep.startswith('book/'):
                filename,_,anchor=dep.partition('#'); path=ROOT/filename
                require(path.is_file(),'missing dependency '+dep)
                if anchor:
                    data=json.loads(path.read_text())
                    if anchor.startswith('/'):
                        value=data
                        for part in anchor[1:].split('/'):
                            value=value[part.replace('~1','/').replace('~0','~')]
                    else:
                        matching=[x for x in data['claims'] if x['id']==anchor]
                        require(len(matching)==1,'dependency claim '+dep)
                        if dep in claim.get('inherited_statuses',{}):
                            require(claim['inherited_statuses'][dep]==matching[0]['status'],'inherited status '+dep)
                dependency_count+=1
            elif dep in local_ids:
                dependency_count+=1

pending={}
links=[]
def target(path,origin):
    path=path.resolve()
    require(path.is_relative_to(ROOT) or path.is_file(),'local reference escapes/nonexistent '+str(path))
    if not path.is_relative_to(ROOT):
        links.append({'from':origin,'target':str(path),'status':'existing external local file'})
        return
    relative=str(path.relative_to(ROOT))
    if path.exists():
        links.append({'from':origin,'target':relative,'status':'exists'})
        return
    if relative.startswith(REL):
        outer=OUTER/relative[len(REL):]
        if outer.exists():
            record={'path':relative,'status':'pending byte-preserving evidence curation','outer_path':str(outer.relative_to(OUTER))}
            if outer.is_file(): record.update({'sha256':digest(outer),'bytes':outer.stat().st_size})
        else:
            require(relative==REL+'README.md','unresolved checkpoint target '+relative)
            record={'path':relative,'status':'pending authored checkpoint index; no completion claimed'}
    elif relative in ['artifacts/quantum_geodesics/result.json','artifacts/final-chapters-review-2026-11-01/monograph-working-draft.pdf']:
        record={'path':relative,'status':'pending final artifact; generation identity belongs to later receipt'}
    else:
        raise RuntimeError('unresolved local reference '+relative+' from '+origin)
    pending[relative]=record
    links.append({'from':origin,'target':relative,'status':record['status']})

docs=['README.md','book/README.md','book/computational-status.md','docs/INTEGRATION_STATUS.md','INTEGRATION_PLAN.md']
for name in docs:
    text=(ROOT/name).read_text()
    for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
        if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',link) or link.startswith('#'): continue
        value=link.split('#',1)[0].strip('<>')
        if not value: continue
        target((ROOT/name).parent/value,name)

# Curated file/path pins in current ledgers. Historical maps are snapshots and
# intentionally are not compared to later live chapter bytes here.
def path_values(value,pointer=''):
    if isinstance(value,dict):
        if isinstance(value.get('path'),str) and value['path'].startswith(REL):
            yield value['path'],pointer+'/path'
        for key,item in value.items():
            if key!='path': yield from path_values(item,pointer+'/'+key)
    elif isinstance(value,list):
        for i,item in enumerate(value): yield from path_values(item,pointer+'/'+str(i))
    elif isinstance(value,str) and value.startswith(REL) and not any(char in value for char in [' ', '\n']):
        yield value,pointer
for name,ledger in [('sections10-11',q),('sections17-22',g),('section32-appendixb',c)]:
    for value,pointer in path_values(ledger): target(ROOT/value,name+pointer)
for artifact in ['artifacts/quantum_geodesics/result.json','artifacts/final-chapters-review-2026-11-01/monograph-working-draft.pdf']:
    target(ROOT/artifact,'declared final artifact path')

# Every accepted source/result group is linked to its exact result field.
approval=json.loads((OUTER/'computation-review/revision-v2/final-acceptance.json').read_text())
result=json.loads((OUTER/approval['accepted_author_result']['path']).read_text())
for ledger in [q,g]:
    for name,record in ledger['computational_companion']['groups'].items():
        require(name in result['groups'] and record['result_pointer']=='/groups/'+name,'group pointer '+name)
        for filename in record['code_files']: require((ROOT/filename).is_file(),'code pointer '+filename)
    for claim in ledger['claims']:
        cov=claim['computational_coverage']
        require(set(cov['implemented_result_groups'])<=set(result['groups']),'unsupported group '+claim['id'])
support_ids={record['id'] for record in c['computational_support_map']}
for claim in c['claims']:
    require(set(claim.get('computational_support',[]))<=support_ids,'support ID '+claim['id'])

# Preserve final citation repairs and prove the source delta exactly reversible.
for file in ['10-quantum-introduction.tex','11-quantum-degeneration.tex','17-unfolding-constant-series.tex','18-figure-eight-curves.tex','19-pants-twists.tex','20-torus-twist-series.tex','21-cuff-matching.tex','22-cusps-orthospectrum.tex']:
    name='book/chapters/'+file
    old=(OUT/'before'/name).read_text(); now=(ROOT/name).read_text()
    marker='\n\n\\paragraph{Computational support.}\n'
    require(now.count(marker)==1,'support paragraph marker '+name)
    restored=now.split(marker)[0]+'\n'
    if file=='19-pants-twists.tex':
        delta=json.loads((OUT/'P01-layout-delta.json').read_text())
        require(restored.count(delta['after'])==1,'P01 current display')
        restored=restored.replace(delta['after'],delta['before'],1)
    require(restored==old,'noncomputational source bytes changed '+name)

(OUT/'pending-artifact-links.json').write_bytes(encode({'scope':'exact currently absent local targets; no prefix-wide exemption','targets':list(pending.values())}))
(OUT/'local-reference-check.json').write_bytes(encode({'status':'author_static_reference_checks_passed','checked_links':links,'dependency_occurrences_checked':dependency_count,'pending_exact_targets':len(pending),'older_results_hashed_not_replayed':7,'mathematical_source_restoration_passed':8,'current_dependency_maps_verified':True,'historical_dependency_observations_preserved':True}))
print(json.dumps({'status':'author_static_reference_checks_passed','local_link_occurrences':len(links),'pending_exact_targets':len(pending),'dependency_occurrences':dependency_count}))
