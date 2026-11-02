"""Independent integration audit; no canonical writes or scientific replay."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = ROOT.parent / 'execution/final-chapters-review-2026-11-01'
OUT = OUTER / 'integration-review'
AUTHOR = OUTER / 'integration-author/revision-v2'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
BASELINE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
FUTURE = 'docs/execution/final-chapters-review-2026-11-01/'

def require(value, message):
    if not value:
        raise RuntimeError(message)

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_bytes())

def write(name, value):
    if (OUT / name).exists():
        require(read(OUT / name)==value,'Existing reviewer receipt differs: '+name)
        return
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False)
        stream.write('\n')

def git(*args, root=ROOT, binary=False, allow=()):
    result = subprocess.run(['git', '-c', 'core.filemode=false', *args], cwd=root,
                            env=ENV, capture_output=True, check=False)
    require(result.returncode == 0 or result.returncode in allow,
            'Git command failed: ' + repr(args) + '\n' + result.stderr.decode())
    return result.stdout if binary else result.stdout.decode()

def pin(path, record):
    require(path.is_file(), 'Missing pinned file: ' + str(path))
    require(digest(path) == record['sha256'], 'Hash mismatch: ' + str(path))
    if 'bytes' in record:
        require(path.stat().st_size == record['bytes'], 'Size mismatch: ' + str(path))

def pointer(value, path):
    for part in path.removeprefix('/').split('/'):
        part = part.replace('~1','/').replace('~0','~')
        value = value[int(part)] if isinstance(value,list) else value[part]
    return value

def delta(a,b,p=''):
    if a == b:
        return []
    if isinstance(a,dict) and isinstance(b,dict):
        out=[]
        for key in sorted(a.keys() | b.keys()):
            newp=p+'/'+key.replace('~','~0').replace('/','~1')
            if key not in a or key not in b:
                out.append({'pointer':newp,'before':a.get(key),'after':b.get(key)})
            else: out.extend(delta(a[key],b[key],newp))
        return out
    if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
        return [item for i,(x,y) in enumerate(zip(a,b)) for item in delta(x,y,p+'/'+str(i))]
    return [{'pointer':p,'before':a,'after':b}]

def strings(value,p=''):
    if isinstance(value,dict):
        for key,item in value.items():
            yield from strings(item,p+'/'+key.replace('~','~0').replace('/','~1'))
    elif isinstance(value,list):
        for i,item in enumerate(value): yield from strings(item,p+'/'+str(i))
    elif isinstance(value,str): yield p,value

def migrate(value):
    if isinstance(value,dict): return {k:migrate(v) for k,v in value.items()}
    if isinstance(value,list): return [migrate(v) for v in value]
    if isinstance(value,str):
        for prefix in ['../execution/final-chapters-review-2026-11-01/','execution/final-chapters-review-2026-11-01/']:
            if value.startswith(prefix): return (FUTURE+value[len(prefix):]).removesuffix(' (outer workspace)')
    return value

def main():
    freeze=read(AUTHOR/'author-freeze.json')
    pin(AUTHOR/'author-freeze.json', {'sha256':'174bc16423e1917a7d6ed634e90ac8a47dd5a86cedb551efb67bf86218d03d16','bytes':18216})
    for rel,record in freeze['evidence'].items(): pin(AUTHOR/rel,record)
    for rel,record in freeze['accepted_input_evidence'].items(): pin(OUTER/rel,record)
    for key in ['source_sha256','tex_input_sha256']:
        for rel,h in freeze[key].items(): pin(ROOT/rel,{'sha256':h})
    require(git('rev-parse','--show-toplevel').strip()==str(ROOT),'Wrong Git root')
    require(git('rev-parse','HEAD').strip()==BASELINE,'HEAD changed')
    index=git('ls-files','--stage','-z',binary=True)
    require(index==(OUTER/'structure/baseline-git-index.zlist').read_bytes(),'Index changed')
    baseline=read(OUTER/'structure/baseline-tracked-inventory.json')
    structure=read(OUTER/'structure/structure-manifest.json')
    pin(OUTER/'structure/baseline-tracked-inventory.json',structure['evidence_files']['baseline-tracked-inventory.json'])
    tree=git('ls-tree','-rz','--full-tree','HEAD',binary=True)
    require(tree==(OUTER/'structure/baseline-git-tree.zlist').read_bytes(),'Baseline Git tree changed')
    tracked={row['path']:row for row in baseline['files']}
    actual_modified=[p for p in git('diff','--name-only','HEAD','-z',binary=True).decode().split('\0') if p]
    actual_untracked=[p for p in git('ls-files','--others','--exclude-standard','-z',binary=True).decode().split('\0') if p]
    actual_source=set(actual_modified+actual_untracked)
    require(actual_source==set(freeze['source_sha256']),'Actual proposed source path set differs from freeze')
    require(len(actual_modified)==6 and len(actual_untracked)==34,'Unexpected modified/new source counts')
    unaffected=[]; lfs=[]
    for rel,row in tracked.items():
        if rel in actual_modified: continue
        path=ROOT/rel
        pin(path,{'sha256':row['materialized_sha256'],'bytes':row['materialized_bytes']})
        unaffected.append(rel)
        if row['materialized_lfs']: lfs.append(row)
    require(len(unaffected)==2267,'Unexpected unaffected baseline count')
    require(len(lfs)==412,'Unexpected LFS count')
    # Resolve each pointer from its immutable Git object, not from filesystem mode bits.
    batch=subprocess.run(['git','cat-file','--batch'],cwd=ROOT,env=ENV,
                         input=''.join(row['git_blob']+'\n' for row in lfs).encode(),capture_output=True,check=True).stdout
    offset=0
    for row in lfs:
        end=batch.index(b'\n',offset); header=batch[offset:end].decode().split(); size=int(header[2]); offset=end+1
        blob=batch[offset:offset+size]; offset+=size+1
        require(header[0]==row['git_blob'] and header[1]=='blob','LFS batch object identity')
        require(sha256(blob).hexdigest()==row['git_blob_sha256'],'LFS pointer blob mismatch')
        oid=re.search(rb'^oid sha256:([a-f0-9]{64})$',blob,re.M)
        size_match=re.search(rb'^size (\d+)$',blob,re.M)
        require(oid is not None and size_match is not None,'Invalid LFS pointer')
        require(oid.group(1).decode()==row['materialized_sha256'] and int(size_match.group(1))==row['materialized_bytes'],'LFS materialization differs from pointer')
    # Audit originals directly, independently of the imported baseline.
    originals=read(ROOT/'audit/2026-10-31/source-inventory.json')
    original_records=[]
    for repository in originals['repositories']:
        original_root=ROOT.parent/repository['path']
        head=git('rev-parse','HEAD',root=original_root).strip()
        require(head==repository['head'],'Original repository HEAD drift')
        require(git('status','--porcelain=v1',root=original_root).strip()==repository['status_porcelain'],'Original repository status drift')
        for row in repository['files']: pin(original_root/row['path'],row)
        original_records.append({'path':str(original_root),'head':head,'files_verified':len(repository['files'])})
    archive=read(ROOT/'provenance/source-map.json')['monograph_archive']
    pin(ROOT/archive['path'],archive)
    outer_archive=ROOT.parent/'polyhedra_moduli_quantum_monograph_sources.zip'
    pin(outer_archive,archive)
    # Preserve original source graph and extraction evidence, with recursive equality.
    for key,dirname in [('baseline_source_graph','baseline-source-graph'),('extracted_source_graph','extracted-source-graph')]:
        for rel,row in structure[key].items(): pin(OUTER/'structure'/dirname/rel,row)
    for rel,row in structure['evidence_files'].items(): pin(OUTER/'structure'/rel,row)
    before=(OUTER/'structure/expanded-entry-before.tex').read_bytes()
    after=(OUTER/'structure/expanded-entry-after.tex').read_bytes()
    require(before==after and sha256(before).hexdigest()==structure['expanded_entry_before_sha256'],'Extraction expansion preservation')
    write('preservation-receipt.json',{'baseline_commit':BASELINE,'tracked_files':len(tracked),'unchanged_baseline_count':len(unaffected),
          'unchanged_baseline_paths':unaffected,'materialized_lfs_count':len(lfs),'lfs_git_pointers_verified':True,
          'original_repositories':original_records,'original_files_verified':sum(r['files_verified'] for r in original_records),
          'original_and_preserved_archive_sha256':archive['sha256'],'index_unchanged':True,
          'baseline_source_graph_and_extraction_evidence_preserved':True,
          'mode_note':'Read-only -c core.filemode=false; exFAT physical modes are not Git modes. All 34 proposed new source files must later be committed 100644.'})
    # Exact accepted mathematical snapshots and reversible integrated source deltas.
    approvals=[read(OUTER/'quantum-review/final-acceptance.json'),read(OUTER/'geodesic-review/revision-v2/final-acceptance.json'),read(OUTER/'conventions-review/revision-v3/final-acceptance.json')]
    accepted_maps=[approvals[0]['accepted_canonical_sha256'],approvals[1]['canonical_sources_sha256'],approvals[2]['accepted_canonical_sha256']]
    for mapping in accepted_maps:
        for rel,h in mapping.items(): pin(AUTHOR/'before'/rel,{'sha256':h})
    layout=read(AUTHOR/'P01-layout-delta.json')
    restored=[]
    for mapping in accepted_maps[:2]:
        for rel,h in mapping.items():
            if not rel.endswith('.tex'): continue
            current=(ROOT/rel).read_text()
            marker='\n\n\\paragraph{Computational support.}\n'
            require(current.count(marker)==1,'Ambiguous computational paragraph '+rel)
            recovered=current.split(marker)[0]+'\n'
            if rel==layout['path']:
                require(recovered.count(layout['after'])==1,'Layout replacement mismatch')
                recovered=recovered.replace(layout['after'],layout['before'],1)
            require(sha256(recovered.encode()).hexdigest()==h,'Mathematical source changed '+rel)
            restored.append(rel)
    def normalized_math(s):
        s=s.replace('\\begin{aligned}','').replace('\\end{aligned}','').replace('\\qquad','').replace('\\\\','').replace('&','')
        return re.sub(r'\s+','',s)
    require(normalized_math(layout['before'])==normalized_math(layout['after']),'P01 mathematical tokens differ')
    c32='book/chapters/32-open-questions.tex'
    pre=(AUTHOR/'before'/c32).read_text(); cur=(ROOT/c32).read_text(); marker='\\paragraph{Computational support.}'
    require(pre.split(marker)[0]==cur.split(marker)[0],'Section32 changes before support paragraph')
    suffix='finite length and event data.'
    require(pre.count(suffix)==cur.count(suffix)==1 and pre.split(suffix)[1]==cur.split(suffix)[1],
            'Section32 changes beyond declared support-paragraph insertion')
    appendix='book/chapters/appendix-b-conventions.tex'
    require((ROOT/appendix).read_bytes()==(AUTHOR/'before'/appendix).read_bytes(),'Appendix B changed')
    mainrel='book/polyhedral_volumes_and_geodesic_identities.tex'
    premain=(AUTHOR/'before'/mainrel).read_text(); curmain=(ROOT/mainrel).read_text()
    require(curmain==premain.replace('{https://arxiv.org/abs/1706.04887}{arXiv:1706.04887}', '{https://arxiv.org/abs/1706.04887v3}{arXiv:1706.04887v3}'),'Unexpected main source integration delta')
    names=['book/claims/sections10-11.json','book/claims/sections17-22.json','book/claims/section32-appendixb.json']
    ledgers=[read(ROOT/n) for n in names]
    old=[read(AUTHOR/'before'/n) for n in names]
    allowed_claim=[{'computational_coverage'},{'computational_coverage'},{'computational_support','dependency_review_states','independent_review_boundary'}]
    all_deltas={}; claim_receipts=[]
    for name,prior,now,allowed in zip(names,old,ledgers,allowed_claim):
        require(len(prior['claims'])==len(now['claims']),'Claim count changed')
        for a,b in zip(prior['claims'],now['claims']):
            require({k:v for k,v in a.items() if k not in allowed}=={k:v for k,v in b.items() if k not in allowed},'Mathematical claim fields changed '+a['id'])
            claim_receipts.append({'ledger':name,'claim_id':a['id'],'mathematical_fields_preserved':True,'status':b['status']})
        all_deltas[name]=delta(prior,now)
    write('independent-ledger-deltas.json',all_deltas)
    # Author delta representation expands added dictionaries; compare actual JSON values at every declared pointer.
    declared=read(AUTHOR/'ledger-json-deltas.json')
    for name,rows in declared.items():
        now=read(ROOT/name); prior=read(AUTHOR/'before'/name)
        for row in rows:
            try: a=pointer(prior,row['pointer'])
            except (KeyError,IndexError): a=None
            try: b=pointer(now,row['pointer'])
            except (KeyError,IndexError): b=None
            require(a==row.get('before') and b==row.get('after'),'Declared delta value mismatch '+name+row['pointer'])
    q,g,c=ledgers; oldc=old[2]
    for ledger,key in [(q,'chapter_source_sha256'),(q,'reviewed_dependency_sha256'),(g,'chapter_source_snapshots'),(c,'chapter_source_sha256')]:
        for rel,h in ledger[key].items(): pin(ROOT/rel,{'sha256':h})
    for ledger,accepted in zip(ledgers,accepted_maps):
        require(ledger['independent_review']['accepted_preintegration_sha256']==accepted,'Historical mathematical snapshot map changed')
    for entry in c['current_author_dependencies']:
        for row in entry['files']: pin(ROOT/row['path'],row)
        expected=q if entry['track']=='quantum' else g
        require(entry['mathematical_review']==expected['independent_review'],'Conventions current mathematical dependency mismatch')
    require(c['historical_author_dependencies']==migrate(oldc['current_author_dependencies']),'Historical dependency snapshot drift')
    require(c['historical_author_dependency_reconciliation']==migrate(oldc['dependency_reconciliation']),'Historical reconciliation drift')
    require(c['computational_support_map'][:7]==oldc['computational_support_map'][:7],'Older result records changed')
    for entry in c['computational_support_map'][:7]: pin(ROOT/entry['result']['path'],entry['result'])
    comp=read(OUTER/'computation-review/revision-v2/final-acceptance.json')
    for rel,h in comp['accepted_runtime_sha256'].items(): pin(ROOT/rel,{'sha256':h})
    pin(OUTER/comp['accepted_author_result']['path'],comp['accepted_author_result'])
    result=read(OUTER/comp['accepted_author_result']['path'])
    require(set(result['groups'])==set(comp['accepted_group_names']),'Result group names mismatch')
    groups={**q['computational_companion']['groups'],**g['computational_companion']['groups']}
    require(set(groups)==set(result['groups']),'Ledger group coverage mismatch')
    counts={'exact':0,'numerical_formula_comparisons':0,'cross_precision_observations':0}
    for name,meta in groups.items():
        require(meta['result_pointer']=='/groups/'+name,'Result pointer mismatch '+name)
        item=pointer(result,meta['result_pointer']); exact=item.get('exact',{}); numerical=item.get('numerical',{})
        require(meta['exact_checks']==exact.get('check_count',0),'Exact count mismatch '+name)
        counts['exact']+=exact.get('check_count',0)
        expected_labels=item.get('labels',exact.get('labels',numerical.get('runs',[{}])[0].get('labels',[])))
        require(meta['formula_labels_in_result']==expected_labels,'Group formula labels mismatch '+name)
        require(len(meta['numerical_runs'])==len(numerical.get('runs',[])),'Run count mismatch '+name)
        for run in meta['numerical_runs']:
            actual=pointer(result,run['result_pointer'])
            for key,value in run.items():
                if key!='result_pointer': require(actual[key]==value,'Numerical metadata mismatch '+name+'/'+key)
            counts['numerical_formula_comparisons']+=actual['check_count']
        cross=numerical.get('cross_precision',{})
        n=cross.get('comparison_count',0)
        require(meta['cross_precision_observations']==n,'Cross precision count mismatch '+name)
        counts['cross_precision_observations']+=n
        for rel in meta['code_files']: require(rel in comp['accepted_runtime_sha256'],'Unapproved group code path '+rel)
    require(counts==comp['derived_check_counts'],'Derived result totals mismatch')
    for entry in c['computational_support_map'][7:]:
        for item in entry['groups']: require(item==groups[item['group']],'Conventions group metadata differs')
    # Full ordered source labels/references and bibliography, independent of the author count.
    source_graph=read(OUT/'tex-input-freeze.json')['files']
    def expand(rel):
        text=(ROOT/rel).read_text()
        return re.sub(r'\\input\{([^}]+)\}',lambda m:expand('book/'+(m[1] if m[1].endswith('.tex') else m[1]+'.tex')),text)
    expanded=expand('book/main.tex')
    labels=re.findall(r'\\label\{([^}]+)\}',expanded)
    bibkeys=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',expanded)
    oldlabels=structure['label_order']; additions=[x for x in labels if x not in set(oldlabels)]
    require(len(labels)==len(set(labels))==613,'Duplicate or wrong source label count')
    require([x for x in labels if x in set(oldlabels)]==oldlabels,'Original ordered labels changed')
    require(additions==['eq:figurekerneltail','eq:figurefiniteidentity','eq:localdistancehessian','eq:torustwistderivatives','eq:torusintegraltail','eq:Hpartialsumtail'],'Unexpected new anchors')
    require(bibkeys==structure['bibliography_order'],'Bibliography order/keys changed')
    refs=re.findall(r'\\(?:eqref|ref|autoref|pageref)\{([^}]+)\}',expanded)
    cites=[key.strip() for match in re.findall(r'\\cite\w*\*?(?:\[[^]]*\])*\{([^}]+)\}',expanded) for key in match.split(',')]
    require(not(set(refs)-set(labels)),'Unresolved TeX reference')
    require(not(set(cites)-set(bibkeys)),'Unresolved citation')
    # Dependency/claim IDs, including precise ledger JSON pointers.
    dependencies=[]; external_dependencies=[]
    for name,ledger in zip(names,ledgers):
        ids={x['id'] for x in ledger['claims']}
        for claim in ledger['claims']:
            for label in claim.get('labels',[]): require(label in labels,'Claim label missing '+label)
            for dep in claim.get('dependencies',[]):
                if dep.startswith('book/'):
                    rel,_,anchor=dep.partition('#'); require((ROOT/rel).is_file(),'Dependency file missing '+dep)
                    if anchor:
                        data=read(ROOT/rel)
                        if anchor.startswith('/'): pointer(data,anchor)
                        else:
                            matches=[x for x in data['claims'] if x['id']==anchor]
                            require(len(matches)==1,'Dependency claim missing '+dep)
                            if dep in claim.get('inherited_statuses',{}): require(claim['inherited_statuses'][dep]==matches[0]['status'],'Inherited claim status mismatch '+dep)
                    dependencies.append({'claim':claim['id'],'dependency':dep})
                elif dep in ids: dependencies.append({'claim':claim['id'],'dependency':dep})
                else: external_dependencies.append({'claim':claim['id'],'dependency':dep})
            if 'computational_coverage' in claim:
                cov=claim['computational_coverage']
                require(set(cov['implemented_result_groups'])<=set(groups),'Unknown computational group')
                for p in cov['result_pointers']: pointer(result,p)
                require(bool(cov['implemented_result_groups']) or cov.get('status')=='no_direct_fixture_in_this_companion'
                        or cov.get('maintained_companion_implementation')=='no_direct_fixture_for_this_claim',
                        'Unmapped claim computational status')
            if 'computational_support' in claim:
                require(set(claim['computational_support'])<={x['id'] for x in c['computational_support_map']},'Unknown conventions support ID')
    # Exact pending targets only. Ledger strings and TeX path literals are independently scanned.
    pending_rows=read(AUTHOR/'pending-artifact-links.json')['targets']; pending={x['path']:x for x in pending_rows}
    require(len(pending)==14,'Pending target count mismatch')
    for rel,row in pending.items():
        require(not(ROOT/rel).exists(),'Pending target unexpectedly already exists '+rel)
        if 'outer_path' in row:
            require((OUTER/row['outer_path']).exists(),'Pending evidence target missing '+rel)
            if 'sha256' in row: pin(OUTER/row['outer_path'],row)
    links=[]; seen_pending=set()
    def check_path(path,origin,fragment=''):
        path=path.resolve(); relative=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)
        state='exists' if path.exists() else 'pending_exact_target' if relative in pending else 'missing'
        require(state!='missing','Unresolved local target '+origin+' -> '+relative)
        if state=='pending_exact_target': seen_pending.add(relative)
        links.append({'origin':origin,'target':relative,'fragment':fragment,'state':state})
        if fragment and path.is_file() and path.suffix=='.json':
            data=read(path)
            if fragment.startswith('/'): pointer(data,fragment)
            elif 'claims' in data: require(any(x['id']==fragment for x in data['claims']),'Unknown linked claim ID')
    for rel in freeze['source_sha256']:
        if rel.endswith('.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',(ROOT/rel).read_text()):
                target=target.strip('<>'); parsed=urlsplit(target)
                if parsed.scheme or not parsed.path: continue
                check_path((ROOT/rel).parent/unquote(parsed.path),rel,unquote(parsed.fragment))
        elif rel.endswith('.tex'):
            for literal in re.findall(r'\\path\{([^}]+)\}',(ROOT/rel).read_text()):
                path=(ROOT/literal) if (ROOT/literal).exists() or literal in pending else (ROOT/'book'/literal)
                check_path(path,rel+' TeX path')
    for name,ledger in zip(names,ledgers):
        for jpath,value in strings(ledger):
            # Only literal root-relative file references, not prose containing a path.
            if value.startswith(('book/','experiments/','docs/','artifacts/')) and not re.search(r'\s',value):
                filename,_,anchor=value.partition('#')
                check_path(ROOT/filename,name+jpath,anchor)
    for rel in ['artifacts/quantum_geodesics/result.json','artifacts/final-chapters-review-2026-11-01/monograph-working-draft.pdf']:
        check_path(ROOT/rel,'declared final artifact')
    require(seen_pending==set(pending),'Pending exception list does not equal observed missing targets')
    write('local-link-and-dependency-receipt.json',{'local_references':links,'local_reference_count':len(links),'dependencies':dependencies,
          'dependency_occurrences':len(dependencies),'external_or_narrative_dependencies':external_dependencies,
          'pending_exact_targets':pending_rows,'no_prefix_wide_exception':True})
    whitespace=[]
    for rel in sorted(actual_source):
        cmd=['git','-c','core.filemode=false','-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab','diff','--check']
        if rel in tracked: cmd+=['HEAD','--',rel]
        else: cmd+=['--no-index','/dev/null',str(ROOT/rel)]
        checked=subprocess.run(cmd,cwd=ROOT,env=ENV,capture_output=True,text=True,check=False)
        require(checked.returncode in (0,1) and not checked.stdout and not checked.stderr,'Whitespace check failed '+rel+' '+checked.stdout+checked.stderr)
        whitespace.append({'path':rel,'returncode':checked.returncode,'diagnostics':[]})
    write('source-verification.json',{'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
          'author_freeze_sha256':digest(AUTHOR/'author-freeze.json'),'author_evidence_files_verified':len(freeze['evidence']),
          'approved_source_sha256':freeze['source_sha256'],'actual_modified_paths':sorted(actual_modified),'actual_untracked_paths':sorted(actual_untracked),
          'active_TeX_inputs':source_graph,'ordered_labels':labels,'added_labels':additions,'bibliography_keys':bibkeys,
          'reference_occurrences':len(refs),'citation_occurrences':len(cites),'accepted_mathematical_bodies_recovered_exactly':restored,
          'P01_normalized_mathematical_tokens_identical':True,'P01_numbered_equations_before_after':[layout['before'].count('\\begin{equation}'),layout['after'].count('\\begin{equation}')],
          'all_186_mathematical_claims':claim_receipts,'claim_counts':[len(x['claims']) for x in ledgers],
          'runtime_files_unchanged':comp['accepted_runtime_sha256'],'immutable_author_result':comp['accepted_author_result'],
          'derived_group_counts':counts,'group_names':list(groups),'current_dependencies_bound_after_quantum_geodesic_hashes':True,
          'historical_snapshots_and_older_result_records_preserved':True,'whitespace_checks':whitespace,
          'scientific_replay_performed':False,'canonical_edits_performed':False})
    print(json.dumps({'source_paths':len(actual_source),'unaffected_baseline':len(unaffected),'LFS':len(lfs),'claims':len(claim_receipts),
          'groups':len(groups),'labels':len(labels),'bibliography':len(bibkeys),'local_references':len(links),'pending_exact_targets':len(pending),
          'dependencies':len(dependencies),'original_files':sum(x['files_verified'] for x in original_records)}))

if __name__=='__main__':
    main()
