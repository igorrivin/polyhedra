"""Independent identity/static check of a strict combined review export."""
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
from urllib.parse import unquote,urlsplit
import zipfile
ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
E=ROOT.parent/'execution/section9-barrier-2026-10-31'
preview=Path(sys.argv[1]).resolve()
site=preview/'site/section9'
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads(Path(p).read_text())
source=load(E/'publication-review-manifest.json')
for name,expected in source['source_sha256'].items():assert digest(ROOT/name)==expected,name
manifest=load(site/'downloads/chapter-build.json')
assert manifest['pending_evidence']==[]
assert manifest['validation']['pdf_pages']==10
assert manifest['validation']['chapter_overfull_hbox_count']==0
assert manifest['validation']['full_monograph_overfull_hbox_count']==0
for name,expected in manifest['inputs'].items():assert digest(ROOT/name)==expected,name
for name,expected in manifest['output_sha256'].items():assert digest(site/name)==expected,name
for name in ('barrier-review.md','barrier-publication-review.md'):
 original=ROOT/'docs/execution/section9-barrier-2026-10-31'/name
 inspection=site/'downloads/inspection/docs/execution/section9-barrier-2026-10-31'/name
 assert original.read_bytes()==inspection.read_bytes()==(E/name).read_bytes(),name
reports={}
for prefix,page,marker,fixture in [('','index.html','\nconst data = ','fixture.json'),('barrier-','barrier.html','\nconst barrierData = ','barrier-fixtures.json')]:
 result=load(site/('downloads/'+prefix+'result.json'))
 text=(site/page).read_text()
 assert text.count(marker)==1
 embedded,_=json.JSONDecoder().raw_decode(text.split(marker,1)[1])
 assert embedded['report']==result
 assert embedded['fixture']==load(site/('downloads/'+fixture))
 assert result['all_checks_passed'] is True
 for row in result['provenance']['source_files']:
  if row['available']:
   path=Path(row['path']) if row['location_kind']=='external' else ROOT/row['path']
   assert digest(path)==row['sha256'],row['role']
 reports[prefix or 'grid']=result
assert reports['barrier-']['cases']==load('/tmp/polyhedra-barrier-publication-fixed/barrier-result.json')['cases']
assert manifest['computation_result']['sha256']==digest(site/'downloads/result.json')
assert manifest['barrier_computation_result']['sha256']==digest(site/'downloads/barrier-result.json')
zipchecks={}
for filename,prefix,mname in [('section9-reproduction.zip','section9-reproduction/','section9-bundle.json'),('barrier-reproduction.zip','barrier-reproduction/','barrier-bundle.json'),('monograph-source.zip','monograph-source/','source-manifest.json')]:
 with zipfile.ZipFile(site/'downloads'/filename) as z:
  names=z.namelist();assert len(names)==len(set(names))
  m=json.loads(z.read(prefix+mname));payload=m['payload_sha256']
  assert set(names)=={prefix+n for n in payload}|{prefix+mname}
  for name,expected in payload.items():assert sha256(z.read(prefix+name)).hexdigest()==expected,name
  if filename=='section9-reproduction.zip':assert m['origin_provenance']==reports['grid']['provenance']
  if filename=='barrier-reproduction.zip':
   assert m['origin_provenance']==reports['barrier-']['provenance']
   replay=load(E/'publication-detached-replay.json')
   with zipfile.ZipFile(replay['archive']) as old:
    oldm=json.loads(old.read(prefix+mname))
   assert payload==oldm['payload_sha256']
  zipchecks[filename]={'sha256':digest(site/'downloads'/filename),'payload_count':len(payload),'all_payloads_verified':True}
class Parser(HTMLParser):
 def __init__(self,text):
  super().__init__();self.ids=[];self.links=[];self.math=0;self.figures=0;self.feed(text)
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  self.links.extend(a[k] for k in ('href','src') if k in a)
  self.math+=tag=='math';self.figures+=tag=='figure'
html={}
for page in sorted(site.glob('*.html')):
 p=Parser(page.read_text());assert len(p.ids)==len(set(p.ids))
 count=0
 for href in p.links:
  uri=urlsplit(href)
  if uri.scheme or uri.netloc:continue
  target=(page.parent/unquote(uri.path)).resolve() if uri.path else page
  assert target.is_file(),(page.name,href)
  if uri.fragment and target.suffix=='.html':assert unquote(uri.fragment) in Parser(target.read_text()).ids,(page.name,href)
  count+=1
 html[page.name]={'local_targets_checked':count,'mathml':p.math,'figures':p.figures}
assert html['chapter.html']['mathml']==209 and html['chapter.html']['figures']==2
old_visual=load(E/'publication-independent-checks.json')['visual_review']
new_pages={p.name:digest(p) for p in sorted((preview/'chapter-build/rendered-pages').glob('*.png'))}
assert len(new_pages)==10
assert new_pages==old_visual['page_sha256']
record={'status':'approved strict combined dirty preview; final clean-source generation remains a separate release stage','preview':str(preview),'source_commit':manifest['source_commit'],'repository_dirty_at_start':manifest['repository_dirty_at_start'],'pending_evidence':[],'reviewed_source_hashes_match':True,'explicit_reports_and_inspection_copies_match':True,'fixed_core_three_case_records_match_fresh_detached_execution':True,'barrier_payload_hashes_equal_previously_executed_post_fix_zip':True,'numerical_replay_scope':'No additional execution in this check. Exact case/payload identity to fresh post-fix detached replay was verified.','zip_checks':zipchecks,'html_checks':html,'pdf_sha256':digest(site/'downloads/section9.pdf'),'all_ten_rendered_page_hashes_equal_visually_approved_preview':True,'page_sha256':new_pages,'final_site_sha256':{str(p.relative_to(site)):digest(p) for p in sorted(site.rglob('*')) if p.is_file() and not p.name.startswith('._')},'browser_review':'not performed','external_publication':'not performed'}
(E/'barrier-strict-preview-review.json').write_text(json.dumps(record,indent=2)+'\n')
(E/'barrier-strict-preview-review.md').write_text('# Independent strict combined preview review\n\nApproved the strict combined dirty preview at `'+str(preview)+'`. Both independent review reports are present as byte-identical inspection copies and `pending_evidence` is empty. All 17 scoped source hashes still match the frozen publication approval. Both explicit numerical results, embedded page data, fixture copies and numerical/archive provenance agree. All manifested payloads in the three ZIPs pass their hashes; the barrier payloads and all three case records exactly match the previously executed corrected-core detached replay. This identity check is not an additional numerical execution.\n\nAll local HTML targets and fragments pass, with 209 chapter MathML nodes and both figures. The chapter PDF has ten pages and no recorded overfull boxes. All ten rendered PNG hashes equal the pages previously opened and visually approved; no new layout was inferred from text extraction. The final site hash inventory records bytes after both render-only backlinks.\n\nThis closes the strict preliminary export gate without changing the frozen source-review report. Clean-source final generation, final archive replay and postcommit integrity checks remain separate release gates. Browser review and external publication remain unperformed. Exact hashes and paths are in `barrier-strict-preview-review.json`.\n')
print(json.dumps({k:record[k] for k in ('status','pending_evidence','reviewed_source_hashes_match','fixed_core_three_case_records_match_fresh_detached_execution','all_ten_rendered_page_hashes_equal_visually_approved_preview','pdf_sha256')},indent=2))
