"""Inspect the actual precommit build and render all targeted chapter ranges."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from PIL import Image, ImageDraw
from pypdf import PdfReader

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT=ROOT.parent/'execution/final-chapters-review-2026-11-01/integration-review'
SNAP=OUT/'frozen-source'
BUILD=OUT/'pdf-build'

def digest(path): return sha256(path.read_bytes()).hexdigest()
def require(value,message):
    if not value: raise RuntimeError(message)
def write(name,value):
    with (OUT/name).open('x') as stream:
        json.dump(value,stream,indent=2);stream.write('\n')

freeze=json.loads((OUT/'tex-input-freeze.json').read_text())
for rel,h in freeze['files'].items():
    require(digest(ROOT/rel)==h and digest(SNAP/rel)==h,'Frozen input mismatch '+rel)
recorded=set(); external=[]
for line in (BUILD/'main.fls').read_text().splitlines():
    if line.startswith('INPUT '):
        raw=Path(line[6:]);path=((SNAP/'book'/raw) if not raw.is_absolute() else raw).resolve()
        if path.is_relative_to(SNAP) and path.suffix=='.tex': recorded.add(str(path.relative_to(SNAP)))
        elif path.suffix=='.tex' and not path.is_relative_to(BUILD): external.append(str(path))
require(recorded==set(freeze['files']),'Recorder custom input mismatch')
aux=(BUILD/'main.aux').read_text(); toc=(BUILD/'main.toc').read_text(); log=(BUILD/'main.log').read_text()
labels=re.findall(r'\\newlabel\{([^}]+)\}',aux); keys=re.findall(r'\\bibcite\{([^}]+)\}',aux)
expected_labels=[]; expected_keys=[]
for rel in freeze['files']:
    text=(SNAP/rel).read_text()
    expected_labels+=re.findall(r'\\label\{([^}]+)\}',text)
    expected_keys+=re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}',text)
require(len(labels)==len(set(labels))==613 and set(labels)==set(expected_labels),'Compiled label mismatch')
require(len(keys)==len(set(keys))==129 and keys==expected_keys,'Compiled bibliography mismatch')
pdf=BUILD/'main.pdf';reader=PdfReader(pdf)
require(reader.page_labels==[str(i) for i in range(1,len(reader.pages)+1)],'PDF labels differ from physical pages')
sections=[]
for line in toc.splitlines():
    match=re.match(r'\\contentsline \{section\}\{\\numberline \{([^}]+)\}(.*)\}\{(\d+)\}\{[^}]+\}',line)
    if match: sections.append({'section':match[1],'title':match[2],'start_page':int(match[3])})
reference=re.search(r'\\contentsline \{section\}\{References\}\{(\d+)\}',toc)
require(reference is not None,'References TOC entry missing')
reference_start=int(reference[1])
selected_sections=['10','11','17','18','19','20','21','22','32','A','B']
ranges=[]
for index,item in enumerate(sections):
    if item['section'] in selected_sections:
        next_page=sections[index+1]['start_page'] if index+1<len(sections) else reference_start
        # Include the next section start because two sections may share a page.
        ranges.append({**item,'through_page_including_next_transition':next_page})
pages=set(range(1,8))|set(range(reference_start,len(reader.pages)+1))
for item in ranges:
    pages.update(range(item['start_page'],item['through_page_including_next_transition']+1))
for first in [39,95,186]: pages.add(first-1)
pages=sorted(pages)
versions={}
for name,command in [('latexmk',['/Library/TeX/texbin/latexmk','-v']),('pdflatex',['/Library/TeX/texbin/pdflatex','--version']),('ghostscript',['/usr/local/bin/gs','--version'])]:
    versions[name]=subprocess.check_output(command,text=True).splitlines()[:4]
warnings=[]
for match in re.finditer(r'(Overfull|Underfull) \\[hv]box[^\n]*',log):
    warnings.append({'warning':match[0],'context':log[max(0,match.start()-100):match.start()+450]})
receipt={'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'stage':'actual precommit integrated source build',
         'build_command_receipt':{'path':'build-command.json','sha256':digest(OUT/'build-command.json')},
         'pdf':{'path':str(pdf),'sha256':digest(pdf),'bytes':pdf.stat().st_size,'pages':len(reader.pages)},
         'tex_input_freeze_sha256':digest(OUT/'tex-input-freeze.json'),'recorder_active_custom_inputs':sorted(recorded),
         'active_input_count':len(recorded),'external_TeX_inputs':sorted(set(external)),'compiled_unique_labels':len(labels),
         'compiled_unique_bibliography_keys':len(keys),'overfull_count':len(re.findall(r'Overfull \\[hv]box',log)),
         'underfull_count':len(re.findall(r'Underfull \\[hv]box',log)),
         'undefined_reference_or_citation':bool(re.search(r'undefined references|Reference .* undefined|Citation .* undefined',log)),
         'multiply_defined_labels':bool(re.search(r'multiply defined',log)),
         'missing_character_warning':bool(re.search(r'Missing character',log)),'box_warnings':warnings,
         'versions':versions,'P01_aux_record':next(line for line in aux.splitlines() if r'\newlabel{eq:localdistancehessian}' in line),
         'source_matches_live_and_snapshot_after_build':True,'postcommit_build':False,
         'visual_approval':'separate visual-review.json after actual image inspection'}
require(receipt['overfull_count']==0 and not any(receipt[k] for k in ['undefined_reference_or_citation','multiply_defined_labels','missing_character_warning']),'Required build diagnostic failed')
write('pdf-build-receipt.json',receipt)
images=OUT/'rendered';images.mkdir(exist_ok=False)
manifest={'pdf':receipt['pdf'],'renderer':'/usr/local/bin/gs','resolution_dpi':130,'section_ranges_from_final_toc':ranges,
          'frontmatter_and_TOC_pages':list(range(1,8)),'bibliography_pages':list(range(reference_start,len(reader.pages)+1)),
          'pages_rendered':pages,'commands':[],'images':[],'contact_sheets':[]}
for page in pages:
    target=images/f'page-{page:03d}.png'
    command=['/usr/local/bin/gs','-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=png16m','-r130',f'-dFirstPage={page}',f'-dLastPage={page}','-sOutputFile='+str(target),str(pdf)]
    done=subprocess.run(command,capture_output=True,text=True,check=False)
    manifest['commands'].append({'page':page,'command':command,'returncode':done.returncode,'stdout':done.stdout,'stderr':done.stderr})
    require(done.returncode==0,'PDF render failed at page '+str(page))
    manifest['images'].append({'page':page,'path':str(target),'sha256':digest(target),'bytes':target.stat().st_size})
for offset in range(0,len(pages),4):
    subset=pages[offset:offset+4]
    sheet=Image.new('RGB',(1400,1880),'#dddddd');draw=ImageDraw.Draw(sheet)
    for index,page in enumerate(subset):
        image=Image.open(images/f'page-{page:03d}.png').convert('RGB');image.thumbnail((680,900))
        x=(index%2)*700+10;y=(index//2)*940+30
        sheet.paste(image,(x,y));draw.text((x,y-22),'PDF page '+str(page),fill='black')
    name=f'contact-{offset//4+1:02d}.png';sheet.save(images/name)
    manifest['contact_sheets'].append({'path':str(images/name),'pages':subset,'sha256':digest(images/name)})
write('render-manifest.json',manifest)
print(json.dumps({'pdf':receipt['pdf'],'rendered_pages':pages,'contact_sheets':len(manifest['contact_sheets']),'ranges':ranges}))
