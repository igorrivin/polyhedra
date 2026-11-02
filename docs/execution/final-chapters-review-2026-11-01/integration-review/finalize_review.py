"""Record completed human-visible inspection and exact precommit acceptance."""
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER=ROOT.parent/'execution/final-chapters-review-2026-11-01'
OUT=OUTER/'integration-review'
AUTHOR=OUTER/'integration-author/revision-v2'

def read(path): return json.loads(path.read_bytes())
def digest(path): return sha256(path.read_bytes()).hexdigest()
def require(value,message):
    if not value: raise RuntimeError(message)
def write(name,value):
    with (OUT/name).open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')
def identity(path): return {'sha256':digest(path),'bytes':path.stat().st_size}

source=read(OUT/'source-verification.json');build=read(OUT/'pdf-build-receipt.json')
render=read(OUT/'render-manifest.json');freeze=read(OUT/'tex-input-freeze.json')
full_pages=[31,40,41,49,50,52,53,54,95,97,99,100,102,103,104,105,106,107,108,109,186,189,191,192,195]
inspected=sorted(set(render['pages_rendered'])|{31})
require(len(inspected)==57 and len(full_pages)==25,'Visual coverage counts')
visual={
 'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'decision':'approved_precommit_integrated_PDF_for_requested_increment',
 'pdf':build['pdf'],
 'render_manifest':{'path':'render-manifest.json',**identity(OUT/'render-manifest.json')},
 'supplemental_warning_render':{'path':'historical-warning-render.json',**identity(OUT/'historical-warning-render.json')},
 'contact_sheets_actually_inspected':[{'path':x['path'],'pages':x['pages'],'sha256':x['sha256']} for x in render['contact_sheets']],
 'individually_inspected_at_original_raster_size':full_pages,
 'all_visually_inspected_pages':inspected,
 'page_count_visually_inspected':len(inspected),
 'pages_not_visually_resampled':[x for x in range(1,build['pdf']['pages']+1) if x not in inspected],
 'section_ranges_and_neighbor_transitions':render['section_ranges_from_final_toc'],
 'coverage_description':'All pages in Sections 10-11, 17-22, 32, and Appendix B, inclusive next-section transition pages; Appendix A transition and body; frontmatter/TOC/list of figures; all bibliography pages; preceding pages 38, 94, 185; unchanged Section 9 warning page 31.',
 'required_open_findings':[],
 'resolved_findings':[{'id':'P01','page':102,'equation':'19.3',
   'finding':'Single two-row aligned display, one number, intact Hessian and determinant, no overrun or overlap.',
   'normalized_math_tokens_verified_identical':True}],
 'underfull_assessment':[
   {'section':'9','page':31,'badness':1014,'status':'unchanged historical warning; proof paragraph readable, no clipping'},
   {'section':'20','page':104,'badness':1178,'status':'readable modest word spacing near boundary-equation sentence; no required defect'},
   {'section':'32','page':189,'badness':3907,'status':'support paragraph has stretched opening line, remains readable; no collision with Appendix A'}],
 'visual_observations':[
   'No clipping, missing glyphs, overlapping equation numbers, cropped formulas, or broken tables observed in the inspected pages.',
   'The object/parameter tables on pages 40 and 50 and convention tables on pages 191-192 were inspected individually at full raster size.',
   'The repaired Mirzakhani locator and L-bounded hypothesis are visible on page 103; the McShane Theorem 3 and post-Corollary-5 locator are visible on page 107.',
   'Question 32.1 retains selected positive lengths L1 < L2 and the equal-length continuity extension on page 186.',
   'Computational support paragraphs retain legible literal file paths and finite-evidence limits.',
   'Frontmatter, TOC, boundary pages, Appendix A/B transitions, and references have consistent headers, footers, and page numbering.',
   'The bibliography Chen-Murakami entry displays the v3 pin on page 195.'],
 'limits':'57 of 199 pages visually inspected; contact sheets establish layout coverage and 25 individual page images cover critical formulas/tables. No all-page visual or full-book editorial certification.'}
write('visual-review.json',visual)

# Reconcile every changed top-level metadata field against the bounded author scope.
ledger_names=['sections10-11','sections17-22','section32-appendixb']
top_allowed=[{'chapter_source_sha256','claims','computational_companion','independent_review','integration'},
 {'author_review','chapter_source_snapshots','claims','computational_companion','independent_review','integration','revision_review','unresolved_limits'},
 {'chapter_source_sha256','claims','computational_boundary','computational_support_map','current_author_dependencies','dependency_reconciliation',
  'external_source_policy','historical_author_dependencies','historical_author_dependency_reconciliation','independent_review','path_convention','pending_dependencies','structural_baseline'}]
deltas=read(OUT/'independent-ledger-deltas.json');metadata=[]
for name,allowed in zip(ledger_names,top_allowed):
    rel='book/claims/'+name+'.json';rows=deltas[rel]
    actual={r['pointer'].split('/')[1] for r in rows}
    require(actual<=allowed,'Unexpected ledger top-level change '+name)
    metadata.append({'ledger':rel,'changed_top_level_fields':sorted(actual),'independent_delta_count':len(rows)})
before_files=[p for p in (AUTHOR/'before').rglob('*') if p.is_file() and not p.name.startswith('._')]
owned_changed=[];unchanged=[]
for path in before_files:
    rel=str(path.relative_to(AUTHOR/'before'))
    require((AUTHOR/'after'/rel).read_bytes()==(ROOT/rel).read_bytes(),'After snapshot does not match live '+rel)
    (unchanged if path.read_bytes()==(ROOT/rel).read_bytes() else owned_changed).append(rel)
require(len(owned_changed)==18 and unchanged==['book/chapters/appendix-b-conventions.tex'],'Owned integration delta set mismatch')
pattern_hits=[]
patterns=[r'\b(?:TODO|FIXME|TBD)\b',r'<<<<<<<|>>>>>>>|=======',r'(?i)(?:postcommit|post.commit|source_commit|final_result_sha256|final_pdf_sha256)']
for rel in source['approved_source_sha256']:
    if rel.endswith(('.tex','.md','.json')):
        for number,line in enumerate((ROOT/rel).read_text().splitlines(),1):
            for pattern in patterns:
                if re.search(pattern,line):pattern_hits.append({'path':rel,'line':number,'text':line,'pattern':pattern})
require(not pattern_hits,'Unreviewed marker or future identity field')
comp=read(OUTER/'computation-review/revision-v2/final-acceptance.json')
inactive={rel:h for rel,h in comp['author_tex_sha256'].items() if rel not in freeze['files']}
require(len(inactive)==10,'Inactive observed fragments')
for rel,h in inactive.items():require(digest(ROOT/rel)==h,'Inactive fragment changed '+rel)
semantic={
 'decision':'approved_bounded_source_metadata_and_clarity_delta',
 'owned_changed_files':sorted(owned_changed),'unchanged_owned_snapshot':unchanged,
 'ledger_metadata_delta_audit':metadata,
 'mathematical_claim_fields_statuses_and_hypotheses_preserved':186,
 'source_mathematics':'Eight quantum/geodesic chapter bodies recovered byte-for-byte after removing appended support paragraphs and reversing P01. Section32 changes confined to its support paragraph. AppendixB accepted bytes unchanged.',
 'citation_repairs':'Mirzakhani Theorem3.4/(3.6) versus Proposition3.5/(3.7) p107 with L-bounded pants; McShane Theorem3 p4 and measure-zero paragraph after Corollary5 p5; Section32 positive-boundary Zonneveld extension and continuity retained.',
 'current_dependency_order':'Current quantum and geodesic source/ledger hashes finish before conventions dependency hashes; historical mathematical snapshots and historical author observations remain distinct.',
 'no_circular_source_or_final_result_identity':'Source holds old baseline identity and fixed reviewed dirty author-result identity only; future final source commit/result/PDF identities belong to later receipts.',
 'evidence_scope':'Finite exact algebra, floating comparisons, cross-precision observations, analytic truncation and uncertified numerical error remain separate. No general proof promotion, achieved-digit certificate, total interval error, or fresh full external-proof audit.',
 'precision_and_counts':{'derived_counts':source['derived_group_counts'],'requested':[70,110],'ordinary_actual':[90,130],'G3_actual':[170,210],'G5_actual':[150,190],'acceptance_scales':['1e-55','1e-95'],'achieved_digit_certification':False},
 'prior_oracles':'400 exact and 1322 numerical independent oracle checks explicitly reused by unchanged mathematical and fixture identity, not rerun here.',
 'status_and_clarity':'Five shared documents accurately identify all 32 sections and both appendices as bounded chapter passes while retaining later cross-chapter editorial, full local web/browser/release, metadata/credits/licensing, and final upload gates. Optional-dependency full-suite limitations and unrecovered originals remain explicit.',
 'inactive_observed_TeX_fragments':inactive,'companion_observed_TeX_files':46,'active_TeX_inputs':36,
 'physical_AppleDouble_sidecars':'Ignored ._ files are filesystem metadata, not active TeX inputs or proposed Git source paths; left untouched.',
 'anti_pattern_scan':{'patterns':patterns,'hits':pattern_hits},
 'required_open_findings':[]}
write('source-delta-and-clarity-review.json',semantic)

tests=read(OUT/'site-tests.json');testlog=(OUT/'site-tests.stderr.txt').read_text()
require(tests['returncode']==0 and re.search(r'Ran 25 tests\b',testlog) and testlog.rstrip().endswith('OK'),'Site suite evidence mismatch')
write('test-review.json',{'command_receipt':{'path':'site-tests.json',**identity(OUT/'site-tests.json')},
 'stdout':{'path':'site-tests.stdout.txt',**identity(OUT/'site-tests.stdout.txt')},
 'stderr':{'path':'site-tests.stderr.txt',**identity(OUT/'site-tests.stderr.txt')},
 'tests_run':25,'result':'passed','execution_count':1,'scope':'Existing site suite only; no full toolkit/dependency-complete suite or scientific campaign rerun.'})

# Recheck exact live and frozen identities at the approval boundary.
for rel,h in source['approved_source_sha256'].items():require(digest(ROOT/rel)==h,'Live source drift before acceptance '+rel)
for rel,h in freeze['files'].items():require(digest(ROOT/rel)==h and digest(OUT/'frozen-source'/rel)==h,'Active source drift before acceptance '+rel)
for rel,h in comp['accepted_runtime_sha256'].items():require(digest(ROOT/rel)==h,'Runtime drift before acceptance '+rel)
require(digest(OUTER/comp['accepted_author_result']['path'])==comp['accepted_author_result']['sha256'],'Author result drift')
require(digest(Path(build['pdf']['path']))==build['pdf']['sha256'],'PDF drift')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
require(head=='151673b1817e66aae493eb7da1be5ddf49adfe0f','HEAD changed before acceptance')
readme='''# Final integration review

The exact forty-path integrated source is approved for the later source checkpoint. There are no required open findings. This approval covers the bounded source/ledger delta, preservation, focused site tests, and the actual precommit PDF build and requested layout review.

The final integrated build has 199 pages. Its SHA256 is `5bb873e52a4fe668d74f6137150d5e1180f75d6ed1c93bff21724e5b8bcf4c83`; the source file is `pdf-build/main.pdf` (1,522,690 bytes). It was built from the frozen thirty-six active TeX inputs. This is a precommit build, not a postcommit replay. The later canonical copy may occur only after all thirty-six input hashes match the committed source, and must be byte-for-byte identical.

Fifty-seven actual pages were inspected: pages 1-7, 31, 38-54, 94-110, and 185-199. Fourteen contact sheets cover the requested chapter ranges and transitions. Twenty-five critical pages were also inspected individually at original raster size. All other pages were not visually resampled. P01 is resolved: equation 19.3 on page 102 has one number and a readable two-row Hessian/determinant display with identical normalized mathematical tokens. The Section 9, Section 20, and Section 32 underfull warnings remain legible and require no repair. There are no overfull boxes, undefined references/citations, duplicate labels, or missing-character warnings.

Independent checks preserve 607 ordered original labels plus six anchors, 129 bibliography keys, all 186 mathematical claim fields, and all twenty-four runtime files. Fourteen result groups, 241 dependency occurrences, and 720 local references resolve, with exactly fourteen individually enumerated pending artifact/curation targets. All 2,267 unaffected baseline files and 412 materialized LFS files match the baseline inventory/Git pointers. The 953 original repository files, original heads, ZIP, original source graph and extraction evidence are preserved. Default whitespace checks cover the six modified and thirty-four new source paths. New files must later use Git mode 100644; exFAT physical modes were not treated as Git modes.

The supported Python site suite ran once and passed all 25 tests. No numerical campaign or full toolkit suite was rerun. Reviewer audit-script development encountered schema assumptions about added JSON delta fields and geodesic coverage names; these were corrected in reviewer-only code. The recorded failed audit attempts are tooling development, not canonical-source defects. No acceptance is inferred from those failed attempts.

`final-acceptance.json` binds the forty-path map at `/approved_source_sha256`, the active TeX map at `/approved_active_tex_sha256`, the PDF at `/precommit_pdf`, and the exact receipts at `/evidence`. `source-verification.json` retains per-claim status and source details; `independent-ledger-deltas.json` lists actual JSON changes. `visual-review.json` provides exact page coverage and assessments.

The source commit, fresh clean-source numerical generation, canonical artifact copying, and candidate-checkpoint approval remain later gates. The full cross-chapter editorial pass, web/browser/dependency-complete release checks, credits and licensing remain later work. Upload remains the final later publication step.
'''
with (OUT/'review-report.md').open('x') as stream:stream.write(readme)
evidence_names=['build_and_test.py','audit_source.py','inspect_pdf.py','finalize_review.py','tex-input-freeze.json','marker-reuse.json',
 'build-command.json','build-command.stdout.txt','build-command.stderr.txt','pdf-build-receipt.json','render-manifest.json',
 'historical-warning-render.json','visual-review.json','source-verification.json','independent-ledger-deltas.json',
 'preservation-receipt.json','local-link-and-dependency-receipt.json','source-delta-and-clarity-review.json','test-review.json',
 'site-tests.json','site-tests.stdout.txt','site-tests.stderr.txt','audit-attempt-2.stdout.txt','audit-attempt-2.stderr.txt',
 'audit-attempt-3.stdout.txt','audit-attempt-3.stderr.txt','pdf-inspection.stdout.txt','pdf-inspection.stderr.txt','review-report.md']
acceptance={
 'schema_version':1,'recorded_at_utc':datetime.now(timezone.utc).isoformat(),
 'decision':'approved_exact_source_integration_and_precommit_PDF_for_later_checkpoint',
 'source_integration_approved':True,'precommit_pdf_build_and_visual_approved':True,'required_open_findings':[],
 'baseline_HEAD':head,'author_freeze':{'path':'../integration-author/revision-v2/author-freeze.json',**identity(AUTHOR/'author-freeze.json')},
 'approved_source_sha256':source['approved_source_sha256'],'approved_source_path_count':40,
 'approved_active_tex_sha256':freeze['files'],'active_tex_input_count':36,
 'precommit_pdf':build['pdf'],'approved_runtime_sha256':comp['accepted_runtime_sha256'],
 'immutable_reviewed_author_result':comp['accepted_author_result'],
 'mathematical_claim_counts':[61,59,66],'mathematical_fields_and_statuses_preserved':True,
 'labels':{'original_ordered':607,'new':6,'unique_total':613},'bibliography_keys':129,
 'checks':{'local_reference_occurrences':720,'dependency_occurrences':241,'pending_exact_targets':14,'result_groups':14,
           'unaffected_baseline_files':2267,'materialized_LFS_files':412,'original_repository_files':953,'site_tests_passed':25,
           'site_test_execution_count':1,'visual_pages':57,'individual_full_raster_pages':25},
 'postcommit_build_or_clean_replay_claimed':False,'canonical_edits_or_artifact_copy_performed':False,
 'marker_rerun':False,'source_staging_or_commit':False,'upload_or_deployment':False,
 'later_copy_gate':'Before copying this PDF byte-for-byte to the canonical artifact path, prove every approved_active_tex_sha256 entry matches the later committed source; retain precommit origin explicitly.',
 'pending_later_gates':['source commit','fresh clean-source companion generation and scientific comparison','curated canonical artifact transfer','candidate checkpoint approval','full cross-chapter editorial and local web/browser/release work','credits and licensing','final later upload'],
 'evidence':{name:identity(OUT/name) for name in evidence_names}}
write('final-acceptance.json',acceptance)
print(json.dumps({'final_acceptance':identity(OUT/'final-acceptance.json'),'report':identity(OUT/'review-report.md'),
                  'pdf':build['pdf'],'source_map_pointer':'/approved_source_sha256','tex_map_pointer':'/approved_active_tex_sha256',
                  'required_open_findings':[]}))
