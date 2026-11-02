from pathlib import Path
import hashlib
import json
import re
import subprocess

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE=ROOT.parent/'execution/final-chapters-review-2026-11-01/conventions-author/revision-v3'
OWN=['book/chapters/32-open-questions.tex','book/chapters/appendix-b-conventions.tex','book/claims/section32-appendixb.json']

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def check(condition,message):
    if not condition:
        raise RuntimeError(message)

def write(name,data):
    (HERE/name).write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')

visited=[]
def expand(p,stack=()):
    p=p.resolve()
    check(p not in stack,'Cyclic TeX input')
    check(p.is_relative_to(ROOT),'Input escapes canonical tree')
    visited.append(str(p.relative_to(ROOT)))
    def replace(m):
        s=m.group(1)
        q=p.parent/s
        if not q.suffix:q=q.with_suffix('.tex')
        return expand(q,stack+(p,))
    return re.sub(r'\\(?:input|include)\{([^}]+)\}',replace,p.read_text())

expanded=expand(ROOT/'book/main.tex')
labels=re.findall(r'\\label\{([^}]+)\}',expanded)
bibkeys=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',expanded)
baseline=(HERE.parent.parent/'structure/expanded-entry-before.tex').read_text()
baseline_labels=re.findall(r'\\label\{([^}]+)\}',baseline)
additions=[x for x in labels if x not in baseline_labels]
expected_additions=['eq:figurekerneltail','eq:figurefiniteidentity','eq:localdistancehessian','eq:torustwistderivatives','eq:torusintegraltail','eq:Hpartialsumtail']
check(len(baseline_labels)==607,'Expected 607 structural baseline labels')
check([x for x in labels if x in baseline_labels]==baseline_labels,'Original 607 labels not preserved in order')
check(additions==expected_additions and len(set(labels))==len(labels),'Unexpected concurrent label additions')
check(len(bibkeys)==129 and len(set(bibkeys))==129,'Expected 129 bibliography keys')
ledger=json.loads((ROOT/OWN[2]).read_text())
check(len({c['id'] for c in ledger['claims']})==len(ledger['claims']),'Duplicate claim IDs')
check(len([c for c in ledger['claims'] if 'question_number' in c])==15,'Question coverage')
check(len([c for c in ledger['claims'] if 'row_number' in c])==43,'Convention coverage')
check(len(ledger['original_row_coverage'])==28,'Original row coverage')
own_checks=[]
for rel in OWN:
    p=ROOT/rel; b=p.read_bytes(); t=b.decode()
    check(b.endswith(b'\n') and not b.endswith(b'\n\n'),'Exactly one final newline: '+rel)
    bad=[i for i,l in enumerate(t.splitlines(),1) if l.rstrip()!=l]
    check(not bad,'Trailing whitespace: '+rel)
    entry={'path':rel,'sha256':digest(p),'bytes':len(b),'trailing_whitespace_lines':bad,'exactly_one_final_newline':True}
    if rel.endswith('.tex'):
        before=(HERE/'before'/rel).read_text()
        before_labels=re.findall(r'\\label\{([^}]+)\}',before)
        after_labels=re.findall(r'\\label\{([^}]+)\}',t)
        check(after_labels==before_labels,'Original label/order changed: '+rel)
        entry['preserved_labels']=after_labels
        refkeys=re.findall(r'\\(?:eqref|ref)\{([^}]+)\}',t)
        check(all(x in labels for x in refkeys),'Missing chapter reference')
        cited=[x.strip() for group in re.findall(r'\\cite(?:\[[^]]*\])*\{([^}]+)\}',t) for x in group.split(',')]
        check(all(x in bibkeys for x in cited),'Missing citation')
        entry['references_resolve']=len(refkeys)
        entry['citations_resolve']=cited
        # These two chapters have no verbatim/comment code that would obscure delimiters.
        clean=re.sub(r'(?<!\\)%[^\n]*','',t)
        clean=re.sub(r'\\[{}]','',clean)
        depth=0
        for char in clean:
            if char=='{':depth+=1
            elif char=='}':depth-=1
            check(depth>=0,'Unbalanced TeX closing brace')
        check(depth==0,'Unbalanced TeX opening brace')
        starts=re.findall(r'\\begin\{([^}]+)\}',t)
        ends=re.findall(r'\\end\{([^}]+)\}',t)
        check(sorted(starts)==sorted(ends),'Environment mismatch')
        entry['balanced_braces_and_environments']=True
    own_checks.append(entry)

for f,h in ledger['chapter_source_sha256'].items():
    check(digest(ROOT/f)==h,'Ledger source hash mismatch')
for binding in ledger['prior_review_bindings']:
    for f in binding['matched_files']:
        check(digest(ROOT/f['path'])==f['sha256'],'Prior dependency changed: '+f['path'])
q_before=re.findall(r'\\begin\{question\}\[([^]]+)\]',(HERE/'before'/OWN[0]).read_text())
q_after=re.findall(r'\\begin\{question\}\[([^]]+)\]',(ROOT/OWN[0]).read_text())
check(q_before==q_after,'Question order/title changed')
result_pins=[]
for group in ledger['computational_support_map']:
    if 'result' not in group:
        check(group['status']=='planned_contract_only','Unexecuted support mislabeled')
        continue
    rec=group['result'];check(digest(ROOT/rec['path'])==rec['sha256'],'Result changed')
    data=json.loads((ROOT/rec['path']).read_text())
    for field in group['result_fields']:
        node=data
        for part in field.split('.'):
            check(isinstance(node,dict) and part in node,'Missing result field '+field)
            node=node[part]
    result_pins.append(rec)

dependency_drift=[]
for author in ledger['current_author_dependencies']:
    for f in author['files']:
        if digest(ROOT/f['path'])!=f['sha256']:
            dependency_drift.append({'path':f['path'],'recorded':f['sha256'],'current':digest(ROOT/f['path']),'status':'pending_cross_track_reconciliation'})

diff=subprocess.run(['git','diff','--check','--',*OWN],cwd=ROOT,text=True,capture_output=True)
check(diff.returncode==0,'Tracked diff whitespace error: '+diff.stdout+diff.stderr)
status=subprocess.run(['git','status','--short','--',*OWN],cwd=ROOT,text=True,capture_output=True,check=True)
write('author-static-checks.json',{'status':'passed','scope':'Static source, reference, evidence-path and exact hash checks only; no build, numerical replay or independent mathematical approval.','source_graph_entry':'book/main.tex','current_source_graph_files':len(set(visited)),'source_graph_paths':visited,'current_unique_labels':len(labels),'baseline_labels_preserved_in_order':607,'concurrent_geodesic_additions':additions,'concurrent_additions_status':'Root explicitly accepted separate declaration; independent geodesic review pending.','current_bibliography_keys':len(bibkeys),'own_original_labels_preserved':2,'new_labels':[],'question_titles_and_order_preserved':15,'original_rows_covered':28,'current_rows_audited':43,'claims':len(ledger['claims']),'owned_file_checks':own_checks,'actual_untracked_whitespace_checked':True,'git_diff_check':{'returncode':diff.returncode,'stdout':diff.stdout,'stderr':diff.stderr},'owned_git_status':status.stdout,'recorded_result_hashes_checked':result_pins,'current_author_dependency_drift':dependency_drift})
print(json.dumps({'status':'passed','claims':len(ledger['claims']),'questions':15,'rows':43,'labels':len(labels),'bibkeys':len(bibkeys),'source_graph_files':len(set(visited)),'current_author_dependency_drift':dependency_drift},indent=2))
