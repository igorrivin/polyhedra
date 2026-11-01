from pathlib import Path
from hashlib import sha256
from fractions import Fraction
from decimal import Decimal
import re,json
O=Path(__file__).resolve().parent;E=O.parent;R=O.parents[2]/'consolidated'
def h(p):return sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):(O/p).write_text(json.dumps(v,indent=2)+'\n')
finitepath=E/'computation/revision-v2/author-result-60-90-v2.json';toruspath=E/'torus-campaign/full8192-author-v2/result.json';assert h(finitepath)=='2a5680cf8e91db3668099ffdb5e19bc3bb984f89cd121395fbcd856a6da7fc71';assert h(toruspath)=='770315039a907e3adab3169081e1f3e84d07d7301e29a26fcf0b7e281af73521'
f=read(finitepath);t=read(toruspath);assert f['checks_passed'] and t['checks_passed'];assert f['check_counts']=={'exact':4054,'numerical_formula_comparisons':354,'cross_precision_observations':297}
assert 'Ran 38 tests' in (E/'computation-review/revision-v2/focused-tests.log').read_text();assert not read(E/'computation-review/approved-manifest.json')['approved']
assert f['exact']['trace_coefficients']['maximum_k']==12;assert f['exact']['finite_Euler_convolution']['cutoff']==14;assert len(f['exact']['SL2_words']['fixtures'])==4
source=(R/'book/chapters/30-sharp-diagnostics.tex').read_text();table=source.split('Historical report and reproduced printed values.')[1].split('\\end{tabular}')[0]
printed={int(x[0]):x[1:] for x in re.findall(r'(?m)^(\d+) & ([\d.]+) & ([\d.]+) & ([\d.]+) & ([\d.]+)',table)};assert len(printed)==4
rows=[];surfaces=[]
for i,s in enumerate(t['surfaces']):
 assert s['count_through_cutoff']==[18191508,18486116][i];assert len(s['blocks'])==10;assert [x['T'] for x in s['blocks']]==[2**i for i in range(2,12)]
 p=s['precision_samples'];assert p['sample_count']==[151,126][i]==len(p['samples']);assert p['near_final_declared_sample_count']==36
 near=[x for x in p['samples'] if any('declared_twelve_nearest_below_final_cutoff_per_sector' == r for r in x['selection_reasons'])];assert len(near)==36;assert len({tuple(x['slope']) for x in near})==36
 worst=max(Decimal(x['native_absolute_residual']) for x in p['samples']);assert worst==Decimal(p['maximum_native_absolute_residual']);assert worst<Decimal('1.2e-9');assert not p['every_node_error_certified']
 widths=[]
 for w in s['conditional_M_bounds']:
  width=Fraction(w['upper_exact_rational'])-Fraction(w['lower_exact_rational']);assert width==Fraction(w['width_exact_rational']);widths.append(width)
 assert max(widths)<Fraction(['1.232e-6','5.613e-7'][i]);assert len(widths)==10
 for b in s['blocks']:
  if b['T'] in printed:
   vals=[f"{b['M']['value']:.4f}",f"{b['Q']:.4f}"];assert vals==list(printed[b['T']][2*i:2*i+2]);rows.append({'surface':s['surface'],'T':b['T'],'M_Q_printed':vals})
 assert s['fixed64_validation']['all_four_slope_sets_equal'];assert s['fixed64_validation']['exact_trace_pairs_equal_frozen']
 surfaces.append({'surface':s['surface'],'count':s['count_through_cutoff'],'blocks':10,'sample_count':p['sample_count'],'near8192_distinct_samples':len(near),'worst_sampled_binary64_difference':str(worst),'maximum_conditional_M_width_exact':str(max(widths)),'maximum_conditional_M_width_approx':float(max(widths)),'all_point_rows':len(s['counts']),'fixed64_count':s['fixed64_validation']['curve_count']})
assert not t['certified'] and not t['recovered_historical_provenance'];assert not t['sensitivity_hypotheses']['hypotheses_certified']
# Every newly named finite-result group resolves to an actual reviewed author-result group.
groups=[]
def walk(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k in ['result_groups','implemented_result_groups']:groups.extend(x)
   walk(x)
 elif isinstance(v,list):
  for x in v:walk(x)
for name in ['sections23-25.json','sections26-29.json','section30.json','section31.json']:
 j=read(R/'book/claims'/name);walk(j);assert j['computational_companion']['reviewer_replay_counts']==dict(f['check_counts'],focused_tests=38)
 for p in ['approval_manifest_sha256','approved_source_set_sha256']:
  actual=h(E/'computation-review/revision-v2/approved-manifest-v2.json') if p=='approval_manifest_sha256' else read(E/'computation-review/revision-v2/approved-manifest-v2.json')[p];assert j['computational_companion'][p]==actual
for g in set(groups):
 a,b=g.split('.');assert b in f[a],g
# Pin actual entire main delta to the approved six-entry bibliography patch, apart from path headers.
diff=(O/'main-after-extraction.diff').read_text().splitlines();approved=(E/'dynamics-author/revision-v2/bibliography-only.diff').read_text().splitlines();assert diff[2:]==approved[2:]
write('numerical-delta-approval.json',{'decision':'approve_prose_and_ledger_delta_against_reviewed_author_evidence','finite_author_result':{'path':str(finitepath),'sha256':h(finitepath),'counts':f['check_counts'],'focused_independent_tests':38,'rejected_v1_preserved':True},'torus_author_result':{'path':str(toruspath),'sha256':h(toruspath),'phase':t['phase'],'source_state':'original v2 author run, not relabeled as final v3 clean-source replay','surfaces':surfaces,'four_printed_rows_at_four_decimals':rows},'finite_result_groups_resolve':sorted(set(groups)),'bibliography_delta_matches_reviewed_six_entry_patch':True,'limits':['No new numerical replay performed in integration review.','Final clean-source finite and full8192 repaired-parser replays remain postcommit gates.','Exact stored-binary64 arithmetic does not certify the true spectrum, event order, pruning or completeness.','Sensitivity is conditional on uniform listed-length error and completeness/no-entry.','Hyperbolic units and systole rescaling are explicit.','No recovered historical precision provenance, asymptotic inference, or recent-preprint proof/formalization approval.']})
# Explicit future target whitelist; no catch-all missing-link allowance.
future_artifacts=['artifacts/counting_mixing/result.json','artifacts/torus_campaign/result.json','artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf']
cp='docs/execution/counting-mixing-review-2026-11-01';future_docs=[cp,cp+'/README.md',cp+'/algebra-review/approved-hash-manifest.json',cp+'/algebra-review/review-report.md',cp+'/algebra-review/source-audit.md',cp+'/arithmetic-review/analytic-claim-review.json',cp+'/arithmetic-review/review-decisions.json',cp+'/arithmetic-review/review.md',cp+'/computation-review/revision-v2/approved-manifest-v2.json',cp+'/computation-review/revision-v2/review-v2.md',cp+'/dynamics-review/review-report.md',cp+'/dynamics-review/targeted-acceptance-v2.json',cp+'/dynamics-review/targeted-acceptance-v2.md']
scan=read(O/'link-scan.json');unallowed=sorted(set(scan['unique_missing_targets'])-set(future_artifacts+future_docs));assert not unallowed,unallowed
checkpoint_sources=[]
for p in future_docs[2:]:
 source=E/p.removeprefix(cp+'/');assert source.is_file();checkpoint_sources.append({'future_path':p,'existing_outer_source':str(source),'sha256':h(source)})
write('link-check-receipt.json',{'decision':'pass_with_explicit_postcommit_targets','references_checked':len(scan['references']),'current_existing_references':sum(x['exists'] for x in scan['references']),'missing_targets':scan['unique_missing_targets'],'allowed_future_artifact_paths':future_artifacts,'allowed_future_checkpoint_targets':future_docs,'existing_checkpoint_source_evidence':checkpoint_sources,'unexpected_missing_targets':unallowed,'scope':'Markdown local links, chapter TeX path references, and repository-relative ledger path fields; external URLs were not refetched and final artifact targets are not asserted to exist.'})
print('numerical prose/ledger evidence passed; explicit future links passed')
