from pathlib import Path
from hashlib import sha256
from PIL import Image, ImageDraw
from pypdf import PdfReader
import json,subprocess,datetime,re
O=Path(__file__).resolve().parent;P=O/'pdf-build/main.pdf';toc=(O/'pdf-build/main.toc').read_text();start=int(re.search(r'numberline \{23\}[^\n]+?\}\{(\d+)\}',toc).group(1))-1;end=int(re.search(r'numberline \{32\}[^\n]+?\}\{(\d+)\}',toc).group(1));refs=int(re.search(r'\{References\}\{(\d+)\}',toc).group(1))-1;last=len(PdfReader(P).pages);pages=[*range(1,9),*range(start,end+1),*range(refs,last+1)];renders=O/'rendered-pages';renders.mkdir(exist_ok=True);receipts=[]
for start,end in [(1,8),(start,end),(refs,last)]:
 temp=renders/f'range-{start}';temp.mkdir(exist_ok=True)
 cmd=['/usr/local/bin/gs','-dSAFER','-dBATCH','-dNOPAUSE','-sDEVICE=png16m','-r120','-dTextAlphaBits=4','-dGraphicsAlphaBits=4',f'-dFirstPage={start}',f'-dLastPage={end}',f'-sOutputFile={temp}/page-%03d.png',str(P)]
 p=subprocess.run(cmd,capture_output=True,text=True);receipts.append({'argv':cmd,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});assert p.returncode==0
 imgs=sorted(p for p in temp.glob('*.png') if not p.name.startswith('._'));assert len(imgs)==end-start+1
 for num,img in enumerate(imgs,start):img.rename(renders/f'page-{num:03d}.png')
 # Preserve generated macOS metadata in the range directory.
contact=O/'contact-sheets';contact.mkdir(exist_ok=True);sheets=[]
for offset in range(0,len(pages),6):
 group=pages[offset:offset+6];canvas=Image.new('RGB',(1500,2025),'#ddd');draw=ImageDraw.Draw(canvas)
 for k,p in enumerate(group):
  im=Image.open(renders/f'page-{p:03d}.png');im.thumbnail((730,975));x=(k%2)*750+10;y=(k//2)*675+25
  # 120-dpi letter page scaled to 475x615, one contact slot 750x675.
  im.thumbnail((730,635));x=(k%2)*750+(750-im.width)//2;canvas.paste(im,(x,y));draw.text(((k%2)*750+20,(k//2)*675+5),f'PDF / printed page {p}',fill='black')
 path=contact/f'sheet-{offset//6+1:02d}.png';canvas.save(path);sheets.append({'path':str(path.relative_to(O)),'pages':group,'sha256':sha256(path.read_bytes()).hexdigest()})
log=(O/'pdf-build/main.log').read_text();pdfhash=sha256(P.read_bytes()).hexdigest();r=PdfReader(P)
manifest={'generated_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_pdf_path':str(P),'source_pdf_sha256':pdfhash,'pdf_page_count':len(r.pages),'rendered_page_coverage':pages,'render_dpi':120,'renderer':'/usr/local/bin/gs','commands':receipts,'images':[{'page':p,'path':f'rendered-pages/page-{p:03d}.png','sha256':sha256((renders/f'page-{p:03d}.png').read_bytes()).hexdigest()} for p in pages],'contact_sheets':sheets,'overfull_count':log.count('Overfull'),'underfull_count':log.count('Underfull'),'undefined_reference_or_citation':bool(re.search('(?:Reference|Citation).*undefined|There were undefined references',log)),'visual_inspection_status':'pending_actual_inspection'}
(O/'pdf-render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({k:v for k,v in manifest.items() if k not in ['commands','images','contact_sheets','rendered_page_coverage']},indent=2))
