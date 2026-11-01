"""Build and render the frozen active TeX graph entirely outside canonical."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/section15-analytic-review-2026-11-01/integration-review'
MARKER = Path('/Users/igorrivin/.codex/plugins/cache/openai-primary-runtime/pdf/26.1026.10807/skills/pdf/container_tools/mark_artifact_operation_started.mjs')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def run(name, argv, cwd):
    started = time.monotonic()
    result = subprocess.run(list(map(str, argv)), cwd=cwd, text=True, capture_output=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1',
                                 'PATH': '/Library/TeX/texbin:' + os.environ['PATH']})
    (OUT / f'{name}.stdout').write_text(result.stdout)
    (OUT / f'{name}.stderr').write_text(result.stderr)
    receipt = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'returncode': result.returncode,
               'elapsed_seconds': time.monotonic() - started,
               'stdout': f'{name}.stdout', 'stderr': f'{name}.stderr',
               'ended_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    save(f'{name}-command.json', receipt)
    if result.returncode:
        raise RuntimeError(f'{name} failed; see the command receipt')
    return result.stdout

assert sys.argv[1:] == ['--sources-frozen']
checks = json.loads((OUT / 'integration-checks.json').read_text())
assert checks['checks_passed'] and len(checks['source_identities']) == 12
for row in checks['source_identities']:
    assert sha((ROOT / row['path']).read_bytes()) == row['sha256'], row['path']
spec = importlib.util.spec_from_file_location('section15_pdf_source_graph', ROOT / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
graph = builder.source_graph(ROOT)
snapshot = OUT / 'source'
assert not snapshot.exists(), 'Never replace a frozen PDF source snapshot silently'
for name, data in graph.items():
    target = snapshot / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
inputs = {name: sha(data) for name, data in graph.items()}
save('pdf-inputs.json', {
    'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'baseline_commit': checks['baseline_commit'], 'source_graph_files': len(graph),
    'sha256': inputs, 'graph_builder': 'site/build_section9.py:source_graph',
    'graph_builder_sha256': sha((ROOT / 'site/build_section9.py').read_bytes()),
    'scope': 'All literal active local TeX inputs, frozen byte-for-byte outside canonical before the build.',
})
build = OUT / 'build'
build.mkdir(exist_ok=True)
assert not (OUT / 'pdf-operation-marker-command.json').exists(), 'Marker may run exactly once'
# No command intervenes between the successful skill marker and the first build.
run('pdf-operation-marker', ['/opt/homebrew/bin/node', MARKER,
    '--operation-kind', 'create', '--expected-output-count', '1', '--output-format', 'pdf'], OUT)
run('full-book-build', ['/Library/TeX/texbin/latexmk', '-norc', '-pdf',
    '-interaction=nonstopmode', '-halt-on-error', '-file-line-error', '-no-shell-escape',
    f'-outdir={build}', 'main.tex'], snapshot / 'book')

log = (build / 'main.log').read_text(errors='replace')
fatal = ['There were undefined references', 'There were undefined citations',
         'Label(s) may have changed', 'multiply-defined labels',
         'Rerun to get cross-references right', 'Missing character:']
unresolved = [text for text in fatal if text in log]
assert not unresolved, unresolved
assert not re.search(r'LaTeX Warning: (?:Reference|Citation) .+ undefined', log)
labels, citations = builder.aux_maps((build / 'main.aux').read_text())
source_labels = [match.decode() for data in graph.values()
                 for match in re.findall(rb'\\label\{([^{}]+)\}', data)]
assert len(source_labels) == len(set(source_labels)) == len(labels) == 607
assert set(source_labels) == set(labels)
bibs = {match.decode() for data in graph.values()
        for match in re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', data)}
assert bibs == set(citations) and len(bibs) == 129
from pypdf import PdfReader
pdf = build / 'main.pdf'
reader = PdfReader(pdf)
texts = [' '.join(page.extract_text().split()) for page in reader.pages]
first = int(labels['sec:quantumAiry']['page'])
next_section = int(labels['sec:dehnresponse']['page'])
section_pages = list(range(first, next_section + 1))
section_with_adjoining = list(range(max(1, first - 1), min(len(reader.pages), next_section + 1) + 1))
toc_start = next(page for page, text in enumerate(texts, 1) if page < 12 and 'Contents' in text)
intro_start = int(labels['sec:monographintro']['page'])
contents_pages = list(range(toc_start, intro_start))
assert contents_pages and all(page < 12 for page in contents_pages)
bib_start = [page for page, text in enumerate(texts, 1)
             if text.startswith('References') or 'References [1]' in text]
assert len(bib_start) == 1, bib_start
bibliography_pages = list(range(bib_start[0], len(reader.pages) + 1))
selected = sorted(set(section_with_adjoining + contents_pages + bibliography_pages))
renders = OUT / 'rendered'
renders.mkdir(exist_ok=True)
for page in selected:
    png = renders / f'page-{page:03d}.png'
    run(f'render-{page:03d}', ['/usr/local/bin/gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE',
        '-sDEVICE=png16m', '-r120', f'-dFirstPage={page}', f'-dLastPage={page}',
        f'-sOutputFile={png}', pdf], OUT)
    (renders / f'page-{page:03d}.txt').write_text(reader.pages[page - 1].extract_text())
for name, digest in inputs.items():
    assert sha((ROOT / name).read_bytes()) == digest, name
for row in checks['source_identities']:
    assert sha((ROOT / row['path']).read_bytes()) == row['sha256'], row['path']
report = {
    'generated_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'input_sha256': inputs, 'pdf': str(pdf), 'pdf_sha256': sha(pdf.read_bytes()),
    'pdf_pages': len(reader.pages), 'source_labels': len(source_labels),
    'compiled_labels': len(labels), 'bibliography_items': len(bibs),
    'compiled_citations': len(citations), 'undefined_or_duplicate_labels': unresolved,
    'overfull_boxes': re.findall(r'^Overfull .*$', log, re.M),
    'underfull_boxes': re.findall(r'^Underfull .*$', log, re.M),
    'other_warnings': re.findall(r'^(?:LaTeX|Package .*|pdfTeX) Warning:.*$', log, re.M),
    'section_pages': {'section15': {'first_section_page': first,
                      'next_section_page': next_section, 'all_section_pages': section_pages,
                      'with_adjoining_pages': section_with_adjoining}},
    'contents_pages': contents_pages, 'bibliography_pages': bibliography_pages,
    'selected_pages': selected,
    'rendered_sha256': {str(path.relative_to(OUT)): sha(path.read_bytes())
                       for path in sorted(renders.glob('page-*.png'))},
    'build_command_receipt': 'full-book-build-command.json',
    'build_command_receipt_sha256': sha((OUT / 'full-book-build-command.json').read_bytes()),
    'marker_receipt': 'pdf-operation-marker-command.json',
    'marker_receipt_sha256': sha((OUT / 'pdf-operation-marker-command.json').read_bytes()),
    'rendering_tool': 'Ghostscript png16m at 120 dpi; Poppler absent; approved fallback, no installation',
    'visual_review': 'pending actual image inspection',
    'scope': 'Full active-source PDF build and reference convergence; selected-page visual review covers Section15, adjoining pages, contents and shifted bibliography. This is not a whole-book visual or mathematical review.',
}
save('pdf-build-review.json', report)
print(json.dumps({key: report[key] for key in [
    'pdf', 'pdf_sha256', 'pdf_pages', 'source_labels', 'compiled_labels', 'bibliography_items',
    'overfull_boxes', 'underfull_boxes', 'other_warnings', 'section_pages',
    'contents_pages', 'bibliography_pages', 'selected_pages']}, indent=2))
