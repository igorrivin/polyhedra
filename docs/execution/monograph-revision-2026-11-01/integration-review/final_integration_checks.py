#!/usr/bin/env python3
"""Independent integration checks for the frozen precommit revision."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01/integration-review'
BASE = 'df952174e55f08a52596d912d9713a9d1e116313'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    shared = json.loads((OUT.parent / 'shared-docs/shared-docs-manifest.json').read_text())
    for path, expected in shared['source_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected, path
    pdf = json.loads((OUT / 'pdf-build-review.json').read_text())
    for path, expected in pdf['input_sha256'].items():
        assert sha((ROOT / path).read_bytes()) == expected, path
    assert sha(Path(pdf['pdf']).read_bytes()) == pdf['pdf_sha256']
    assert pdf['source_labels'] == pdf['compiled_labels'] == 607
    assert pdf['compiled_citations'] == pdf['bibliography_items'] == 126
    assert not pdf['overfull_boxes'] and not pdf['undefined_or_duplicate_labels']

    inventory = json.loads((OUT.parent / 'structure/baseline-tracked-inventory.json').read_text())
    allowed_changed = {'book/polyhedral_volumes_and_geodesic_identities.tex',
                       'book/README.md', 'book/computational-status.md'}
    changed, preserved = [], []
    for row in inventory['files']:
        data = (ROOT / row['path']).read_bytes()
        if len(data) == row['bytes'] and sha(data) == row['sha256']:
            preserved.append(row['path'])
        else:
            changed.append(row['path'])
    assert set(changed) == allowed_changed, changed
    tracked_changes = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
    assert set(tracked_changes) == allowed_changed | {'README.md', 'INTEGRATION_PLAN.md'}, tracked_changes

    original_inventory = json.loads((ROOT.parent / 'audit/2026-10-31/source-inventory.json').read_text())
    original_count = 0
    original_heads = {}
    for repo in original_inventory['repositories']:
        path = ROOT.parent / repo['path']
        head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=path, text=True).strip()
        assert head == repo['head']
        original_heads[repo['path']] = head
        for row in repo['files']:
            data = (path / row['path']).read_bytes()
            assert len(data) == row['bytes'] and sha(data) == row['sha256'], str(path / row['path'])
            original_count += 1
    assert original_count == 953
    archive = ROOT.parent / 'polyhedra_moduli_quantum_monograph_sources.zip'
    archive_sha = sha(archive.read_bytes())
    assert archive_sha == '8f28b07686ea579a7dfb7b88ccef5c12bdd50b6e328737d5a8a79f6e06ba92dc'

    current = (ROOT / 'book/polyhedral_volumes_and_geodesic_identities.tex').read_bytes()
    for section in ('09-volume-hessians', '15-quantum-airy', '30-sharp-diagnostics'):
        token = f'\\input{{chapters/{section}.tex}}\n'.encode()
        assert current.count(token) == 1
        current = current.replace(token, (ROOT / f'book/chapters/{section}.tex').read_bytes())
    old = (OUT.parent / 'structure/baseline-main.tex').read_bytes()
    old = old.replace(b'\\input{chapters/09-volume-hessians.tex}\n',
                      (OUT.parent / 'structure/09-volume-hessians.tex').read_bytes())
    old_labels = re.findall(rb'\\label\{([^{}]+)\}', old)
    new_labels = re.findall(rb'\\label\{([^{}]+)\}', current)
    assert old_labels == new_labels and len(new_labels) == len(set(new_labels)) == 607
    retained_tables = {}
    for chapter in ('15-quantum-airy.tex', '30-sharp-diagnostics.tex'):
        previous = (OUT.parent / 'structure' / chapter).read_text()
        actual = (ROOT / 'book/chapters' / chapter).read_text()
        old_rows = re.findall(r'(?m)^.*&.*\\\\\s*$', previous[previous.index('\\midrule'):previous.index('\\bottomrule')])
        # Section15 has an earlier array, but its only midrule/bottomrule pair is the historical table.
        new_rows = re.findall(r'(?m)^.*&.*\\\\\s*$', actual[actual.index('\\midrule'):actual.index('\\bottomrule')])
        assert old_rows == new_rows, chapter
        retained_tables[chapter] = len(old_rows)

    pending_allowed = {'docs/execution/monograph-revision-2026-11-01/README.md',
                       'artifacts/section15/checks.json', 'artifacts/section30/result.json'}
    links = []
    pending = []
    for path in shared['source_sha256']:
        text = (ROOT / path).read_text()
        for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', text):
            target = match.group(1).split(' ', 1)[0].strip('<>')
            parts = urlsplit(target)
            if parts.scheme or not parts.path:
                continue
            destination = ((ROOT / path).parent / unquote(parts.path)).resolve()
            entry = {'source': path, 'target': str(destination.relative_to(ROOT)) if destination.is_relative_to(ROOT) else str(destination)}
            links.append(entry)
            if not destination.exists():
                assert entry['target'] in pending_allowed, entry
                pending.append(entry)
    assert len(links) == 109 and len(pending) == 6

    old_status = subprocess.check_output(['git', 'show', f'{BASE}:book/computational-status.md'], cwd=ROOT, text=True)
    new_status = (ROOT / 'book/computational-status.md').read_text()
    assert old_status.split('## Section 9:', 1)[1].split('## Section 15:', 1)[0] == new_status.split('## Section 9:', 1)[1].split('## Section 15:', 1)[0]
    assert 'This edition does\nnot claim that the advertised diagnostic archive accompanies the book.' in (ROOT / 'book/chapters/30-sharp-diagnostics.tex').read_text()
    assert 'not verified quadrature error bounds' in (ROOT / 'book/chapters/15-quantum-airy.tex').read_text()
    assert 'no further upload attempt is part of the current revision work' in (ROOT / 'INTEGRATION_PLAN.md').read_text()
    source_paths = set(shared['source_sha256']) | {'book/polyhedral_volumes_and_geodesic_identities.tex',
                    'book/chapters/15-quantum-airy.tex', 'book/chapters/30-sharp-diagnostics.tex',
                    'book/claims/section15.json', 'book/claims/section30.json'}
    for directory in ('experiments/section15', 'experiments/section30'):
        source_paths.update(str(path.relative_to(ROOT)) for path in (ROOT / directory).rglob('*')
                            if path.is_file() and not path.name.startswith('._') and '__pycache__' not in path.parts)
    assert len(source_paths) == 16
    whitespace = []
    for path in sorted(source_paths):
        for number, line in enumerate((ROOT / path).read_text().splitlines(), 1):
            if line.rstrip() != line:
                whitespace.append({'path': path, 'line': number})
    assert not whitespace, whitespace
    pages = sorted(set(page for row in pdf['section_pages'].values() for page in row['inspected_with_adjacency']))
    assert pages == list(range(68, 76)) + list(range(155, 167))
    result = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_commit': BASE,
        'verdict': 'approved for the bounded local source increment; clean result generation and final checkpoint remain separate',
        'source_sha256': {path: sha((ROOT / path).read_bytes()) for path in sorted(source_paths)},
        'shared_docs_manifest_sha256': sha((OUT.parent / 'shared-docs/shared-docs-manifest.json').read_bytes()),
        'protected_baseline_files_unchanged': len(preserved),
        'intentional_changed_inventory_paths': changed,
        'original_tracked_files_unchanged': original_count,
        'original_heads': original_heads,
        'original_archive_sha256': archive_sha,
        'all_607_labels_preserved_in_order': True,
        'historical_table_rows_preserved': retained_tables,
        'shared_doc_local_link_occurrences': len(links),
        'existing_link_occurrences': len(links) - len(pending),
        'pending_targets_for_final_generation': pending,
        'authored_whitespace_issues': whitespace,
        'pdf_sha256': pdf['pdf_sha256'],
        'pdf_pages': pdf['pdf_pages'],
        'visual_review': {'pages_actually_viewed': pages, 'unresolved_findings': [],
            'observations': ['Tables and equations legible and contained within margins.',
              'Historical and replacement results visibly distinguished.',
              'Computational paths wrap without clipping.',
              'Chapter transitions, figure and page numbering inspected.',
              'No overlap, broken symbols or overfull boxes observed in the inspected pages.']},
        'anti_pattern_findings': [],
        'boundaries': ['This is a precommit PDF built from recorded frozen source hashes.',
            'The other 159 PDF pages were not visually reviewed in this pass.',
            'Full-book mathematical review, exact quantum-integral reproduction and length-8192 replay remain incomplete.',
            'No site/scientific artifact regeneration, browser test, upload, deployment or publication was performed.',
            'The three pending local targets must exist and be verified after clean result generation and checkpoint assembly.']
    }
    (OUT / 'final-integration-review.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('verdict', 'protected_baseline_files_unchanged',
          'original_tracked_files_unchanged', 'all_607_labels_preserved_in_order',
          'historical_table_rows_preserved', 'shared_doc_local_link_occurrences',
          'existing_link_occurrences', 'pdf_pages', 'pdf_sha256')}, indent=2))


if __name__ == '__main__':
    main()
