"""Compare every strict-preview page to the parent's exact approved page images."""
from hashlib import sha256
import json
from pathlib import Path

outer = Path(__file__).resolve().parent
approved = json.loads((outer / 'parent-preview-visual-review.json').read_text())
location = json.loads((outer / 'strict-preview-location.json').read_text())
run, site = Path(location['preview_root']), Path(location['site_dir'])
images = {p.name: sha256(p.read_bytes()).hexdigest() for p in sorted((run / 'chapter-build/rendered-pages').glob('page-*.png'))}
changed = [name for name in sorted(set(images) | set(approved['page_sha256']))
           if images.get(name) != approved['page_sha256'].get(name)]
result = {'scope': 'Rendered-byte comparison to the parent-approved ten-page PDF layout; no browser review',
          'approved_preview_pdf_sha256': approved['pdf_sha256'],
          'strict_preview_pdf_sha256': sha256((site / 'downloads/section9.pdf').read_bytes()).hexdigest(),
          'strict_preview_pdf_path': str(site / 'downloads/section9.pdf'),
          'page_sha256': images, 'approved_page_sha256': approved['page_sha256'],
          'page_count': len(images), 'changed_pages': changed,
          'all_rendered_pages_identical': not changed,
          'visual_review_disposition': 'Identical to all ten parent-reviewed page images' if not changed else 'Changed pages require fresh visual inspection'}
(outer / 'strict-preview-visual-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: v for k, v in result.items() if 'page_sha256' not in k}, indent=2))
assert not changed and len(images) == 10
