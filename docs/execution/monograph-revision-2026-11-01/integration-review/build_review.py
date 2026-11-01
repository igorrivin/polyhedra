#!/usr/bin/env python3
"""Freeze current local TeX sources, build them, and prepare changed-page review."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01/integration-review'
MARKER = Path('/Users/igorrivin/.codex/plugins/cache/openai-primary-runtime/pdf/26.1026.10807/skills/pdf/container_tools/mark_artifact_operation_started.mjs')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def run(name, argv, cwd):
    start = time.monotonic()
    result = subprocess.run(list(map(str, argv)), cwd=cwd, text=True, capture_output=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    (OUT / f'{name}.stdout').write_text(result.stdout)
    (OUT / f'{name}.stderr').write_text(result.stderr)
    record = {'argv': list(map(str, argv)), 'cwd': str(cwd), 'returncode': result.returncode,
              'elapsed_seconds': time.monotonic() - start,
              'stdout': f'{name}.stdout', 'stderr': f'{name}.stderr'}
    (OUT / f'{name}-command.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode:
        raise RuntimeError(f'{name}: exit {result.returncode}; inspect recorded logs')
    return result.stdout


def main():
    assert sys.argv[1:] == ['--sources-frozen'], 'Run only after the root confirms chapter source freeze.'
    OUT.mkdir(parents=True, exist_ok=True)
    spec = importlib.util.spec_from_file_location('review_builder', ROOT / 'site/build_section9.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    graph = builder.source_graph(ROOT)
    snapshot = OUT / 'source'
    for name, data in graph.items():
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    inputs = {name: sha(data) for name, data in graph.items()}
    (OUT / 'pdf-inputs.json').write_text(json.dumps({
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'status': subprocess.check_output(['git', 'status', '--short'], cwd=ROOT, text=True),
        'sha256': inputs,
        'scope': 'Frozen active TeX snapshot. Build validation is not proof verification.'
    }, indent=2) + '\n')

    build = OUT / 'build'
    build.mkdir(exist_ok=True)
    # One required artifact-operation marker, immediately before the first PDF build.
    if not (OUT / 'pdf-operation-marker-command.json').exists():
        run('pdf-operation-marker', ['/opt/homebrew/bin/node', MARKER,
            '--operation-kind', 'create', '--expected-output-count', '1', '--output-format', 'pdf'], OUT)
    run('full-book-build', ['/Library/TeX/texbin/latexmk', '-norc', '-pdf',
        '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
        '-no-shell-escape', f'-outdir={build}', 'main.tex'], snapshot / 'book')

    latex_log = (build / 'main.log').read_text(errors='replace')
    fatal = ('There were undefined references', 'There were undefined citations',
             'Label(s) may have changed', 'multiply-defined labels',
             'Rerun to get cross-references right')
    unresolved = [message for message in fatal if message in latex_log]
    assert not unresolved, unresolved
    assert not re.search(r'LaTeX Warning: (?:Reference|Citation) .+ undefined', latex_log)
    labels, citations = builder.aux_maps((build / 'main.aux').read_text())
    source_labels = [m.decode() for data in graph.values() for m in re.findall(rb'\\label\{([^{}]+)\}', data)]
    assert len(source_labels) == len(set(source_labels))
    assert set(source_labels) <= set(labels), sorted(set(source_labels) - set(labels))
    bib_items = set(re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', b'\n'.join(graph.values())))
    assert {x.decode() for x in bib_items} == set(citations)
    from pypdf import PdfReader
    pdf = build / 'main.pdf'
    reader = PdfReader(pdf)
    sections = {'airy': ('sec:quantumAiry', 'sec:dehnresponse'),
                'torus': ('sec:sharpdiagnostics', 'sec:arithmeticgeometry')}
    page_sets = {}
    for name, (start, end) in sections.items():
        first, last = int(labels[start]['page']), int(labels[end]['page'])
        page_sets[name] = {'first_section_page': first, 'next_section_page': last,
                           'inspected_with_adjacency': list(range(max(1, first - 1), min(len(reader.pages), last + 1) + 1))}
    selected = sorted(set(page for row in page_sets.values() for page in row['inspected_with_adjacency']))
    renders = OUT / 'rendered'
    renders.mkdir(exist_ok=True)
    for page in selected:
        image = renders / f'page-{page:03d}.png'
        run(f'render-{page:03d}', ['/usr/local/bin/gs', '-q', '-dSAFER', '-dBATCH', '-dNOPAUSE',
            '-sDEVICE=png16m', '-r120', f'-dFirstPage={page}', f'-dLastPage={page}',
            f'-sOutputFile={image}', pdf], OUT)
        (renders / f'page-{page:03d}.txt').write_text(reader.pages[page - 1].extract_text())
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'input_sha256': inputs,
        'pdf': str(pdf), 'pdf_sha256': sha(pdf.read_bytes()),
        'pdf_pages': len(reader.pages),
        'source_labels': len(source_labels), 'compiled_labels': len(labels),
        'bibliography_items': len(bib_items), 'compiled_citations': len(citations),
        'undefined_or_duplicate_labels': unresolved,
        'overfull_boxes': re.findall(r'^Overfull .*$', latex_log, re.M),
        'underfull_boxes': re.findall(r'^Underfull .*$', latex_log, re.M),
        'section_pages': page_sets,
        'rendered_sha256': {str(path.relative_to(OUT)): sha(path.read_bytes()) for path in sorted(renders.glob('*.png')) if not path.name.startswith('._')},
        'rendering_tool': 'Ghostscript png16m at 120 dpi; Poppler unavailable',
        'visual_review': 'pending actual image inspection',
        'scope': 'Full-source PDF build and reference convergence; no full-book mathematical review or browser validation.'
    }
    (OUT / 'pdf-build-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in ('pdf', 'pdf_sha256', 'pdf_pages', 'source_labels',
                     'compiled_labels', 'bibliography_items', 'overfull_boxes', 'section_pages')}, indent=2))


if __name__ == '__main__':
    main()
