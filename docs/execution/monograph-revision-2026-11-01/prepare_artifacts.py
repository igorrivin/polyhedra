#!/usr/bin/env python3
"""Preserve reviewed computation/PDF bytes and curate a compact checkpoint."""
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01'
CHECKPOINT = ROOT / 'docs/execution/monograph-revision-2026-11-01'
SOURCE = json.loads((OUT / 'source-checkpoint.json').read_text())

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def scientific(data, name):
    value = deepcopy(data)
    del value['provenance']
    if name == 'airy':
        del value['runtime_seconds']
    else:
        del value['elapsed_seconds']
        for surface in value['surfaces']:
            del surface['elapsed_seconds']
    return value

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == SOURCE['source_commit']
assert not subprocess.check_output(['git', 'status', '--porcelain=v1'], cwd=ROOT).strip()
comparisons = {}
artifacts = {}
for name, target in [('airy', 'artifacts/section15/checks.json'), ('torus', 'artifacts/section30/result.json')]:
    source = OUT / f'clean-source-{name}.json'
    current = json.loads(source.read_text())
    reference = OUT / f'scientific-review/{name}-replay.json'
    approved = json.loads(reference.read_text())
    assert current['provenance']['source_commit'] == SOURCE['source_commit']
    assert current['provenance']['repository_dirty_at_start'] is False
    assert current['provenance']['git_status_porcelain_at_start'] == []
    for path, expected in current['provenance']['source_sha256'].items():
        assert digest(ROOT / path) == expected
        committed = subprocess.check_output(['git', 'show', SOURCE['source_commit'] + ':' + path], cwd=ROOT)
        assert sha256(committed).hexdigest() == expected
    assert scientific(current, name) == scientific(approved, name), name
    comparisons[name] = {
        'fresh_sha256': digest(source), 'reviewed_replay_sha256': digest(reference),
        'all_scientific_fields_equal': True,
        'excluded_json_paths': ['/provenance', '/runtime_seconds'] if name == 'airy' else
            ['/provenance', '/elapsed_seconds', '/surfaces/*/elapsed_seconds'],
        'source_commit': SOURCE['source_commit'], 'dirty_at_start': False,
        'source_hashes_match_commit': True,
    }
    destination = ROOT / target
    assert not destination.exists(), destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    artifacts[target] = {'sha256': digest(destination), 'bytes': destination.stat().st_size,
                         'origin': str(source.relative_to(OUT))}

pdf_report = json.loads((OUT / 'integration-review/pdf-build-review.json').read_text())
pdf_source = OUT / 'integration-review/build/main.pdf'
assert digest(pdf_source) == pdf_report['pdf_sha256'] == '44e428ddbc625231f483748a9bfce914b4d4fc987a0c34b6201003e6dc87cacd'
for path, expected in pdf_report['input_sha256'].items():
    assert digest(ROOT / path) == expected
    assert sha256(subprocess.check_output(['git', 'show', SOURCE['source_commit'] + ':' + path], cwd=ROOT)).hexdigest() == expected
pdf_target = 'artifacts/monograph-revision-2026-11-01/monograph-working-draft.pdf'
destination = ROOT / pdf_target
assert not destination.exists()
destination.parent.mkdir(parents=True, exist_ok=True)
destination.write_bytes(pdf_source.read_bytes())
artifacts[pdf_target] = {'sha256': digest(destination), 'bytes': destination.stat().st_size,
                         'origin': 'integration-review/build/main.pdf'}
write_json(OUT / 'clean-source-scientific-comparison.json', {
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': SOURCE['source_commit'], 'comparisons': comparisons,
    'pdf': {'sha256': digest(destination), 'precommit_build': True,
            'all_five_tex_input_hashes_match_source_commit': True,
            'rebuilt_or_rerendered_after_commit': False,
            'input_sha256': pdf_report['input_sha256']},
})

selected = set()
for path in OUT.iterdir():
    if not path.is_file() or path.name.startswith('._'):
        continue
    name = path.name
    if name.startswith(('airy-author-', 'torus-author-', 'torus-unit-tests.', 'torus-ruff.',
                        'torus-final-replay.', 'clean-source-')) or name in (
        'source-checkpoint.json', 'source-checkpoint-commands.json',
        'source-whitespace-exceptions.json', 'checkpoint_source.py', 'checkpoint_replay.py',
        'prepare_artifacts.py'):
        # The clean numerical outputs have one canonical copy under artifacts/.
        if name not in ('clean-source-airy.json', 'clean-source-torus.json'):
            selected.add(path.relative_to(OUT))
for directory in ('structure', 'shared-docs', 'scientific-review'):
    for path in (OUT / directory).rglob('*'):
        if path.is_file() and not any(p.startswith('._') or p == '__pycache__' for p in path.relative_to(OUT).parts):
            selected.add(path.relative_to(OUT))
for path in (OUT / 'integration-review').iterdir():
    if path.is_file() and not path.name.startswith(('._', 'render-')):
        selected.add(path.relative_to(OUT))
for name in ('main.aux', 'main.log'):
    selected.add(Path('integration-review/build') / name)
selected.difference_update({Path('torus-author-result.json'),
                            Path('scientific-review/torus-replay.json')})

copies = []
CHECKPOINT.mkdir(parents=True, exist_ok=True)
for relative in sorted(selected):
    source, destination = OUT / relative, CHECKPOINT / relative
    assert not source.is_symlink()
    destination.parent.mkdir(parents=True, exist_ok=True)
    assert not destination.exists(), destination
    destination.write_bytes(source.read_bytes())
    assert source.read_bytes() == destination.read_bytes()
    copies.append({'path': str(relative), 'sha256': digest(destination), 'bytes': destination.stat().st_size})
omitted = []
for source in sorted(OUT.rglob('*')):
    relative = source.relative_to(OUT)
    if source.is_file() and relative not in selected and not any(p.startswith('._') or p == '__pycache__' for p in relative.parts):
        omitted.append({'path': str(relative), 'sha256': digest(source), 'bytes': source.stat().st_size})
write_json(CHECKPOINT / 'evidence-copy-manifest.json', {
    'source_evidence_root': str(OUT), 'destination': str(CHECKPOINT), 'files': copies,
    'outer_only_at_packaging': omitted,
    'scope': 'Selected evidence copied byte-for-byte. Original reports/manifests describe the full outer evidence tree. Rendered pages, duplicate source snapshots, intermediate runs and most build products remain there; the PDF and final computations have one canonical artifact copy.',
})
candidate = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
             'baseline_commit': SOURCE['baseline_commit'], 'source_commit': SOURCE['source_commit'],
             'approved_source_sha256': SOURCE['source_sha256'], 'artifacts': artifacts,
             'scientific_comparison': comparisons,
             'pdf_build_scope': 'Precommit PDF, copied without changes; all five TeX inputs match the committed source. No postcommit rebuild or new visual inspection is claimed.',
             'pdf_tex_input_sha256': pdf_report['input_sha256'],
             'evidence_copy_manifest_sha256': digest(CHECKPOINT / 'evidence-copy-manifest.json')}
write_json(CHECKPOINT / 'candidate-artifact-manifest.json', candidate)
write_json(OUT / 'candidate-artifact-manifest.json', candidate)
print(json.dumps({'source_commit': SOURCE['source_commit'], 'artifact_count': len(artifacts),
                  'evidence_files_copied': len(copies), 'outer_only_files': len(omitted),
                  'candidate_manifest_sha256': digest(CHECKPOINT / 'candidate-artifact-manifest.json')}))
