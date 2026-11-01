#!/usr/bin/env python3
"""Independent read-only reconstruction and baseline inventory verification."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
from datetime import datetime, timezone

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01/integration-review'
STRUCT = OUT.parent / 'structure'
BASE = 'df952174e55f08a52596d912d9713a9d1e116313'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(*argv):
    return subprocess.check_output(['git', *argv], cwd=ROOT)


def main():
    original = git('show', f'{BASE}:book/polyhedral_volumes_and_geodesic_identities.tex')
    extracted = (STRUCT / 'extracted-main.tex').read_bytes()
    reconstructed = extracted
    for name in ('15-quantum-airy.tex', '30-sharp-diagnostics.tex'):
        needle = f'\\input{{chapters/{name}}}\n'.encode()
        assert reconstructed.count(needle) == 1
        reconstructed = reconstructed.replace(needle, (STRUCT / name).read_bytes())
    assert reconstructed == original
    old9 = git('show', f'{BASE}:book/chapters/09-volume-hessians.tex')
    assert old9 == (STRUCT / '09-volume-hessians.tex').read_bytes()
    fully_expanded = original.replace(b'\\input{chapters/09-volume-hessians.tex}\n', old9)
    labels = re.findall(rb'\\label\{([^{}]+)\}', fully_expanded)
    assert len(labels) == len(set(labels)) == 607

    inv = json.loads((STRUCT / 'baseline-tracked-inventory.json').read_text())
    entries = {}
    for raw in git('ls-tree', '-r', '-z', BASE, '--', *inv['tracked_trees']).split(b'\0'):
        if not raw:
            continue
        metadata, path = raw.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        assert kind == 'blob'
        entries[path.decode()] = {'mode': mode, 'git_blob': oid}
    assert len(entries) == inv['tracked_file_count'] == 1056
    assert set(entries) == {row['path'] for row in inv['files']}
    batch = git('cat-file', '--batch') if not entries else subprocess.check_output(
        ['git', 'cat-file', '--batch'], cwd=ROOT,
        input=''.join(row['git_blob'] + '\n' for row in entries.values()).encode())
    offset = 0
    blobs = {}
    for path, row in entries.items():
        end = batch.index(b'\n', offset)
        oid, kind, size = batch[offset:end].decode().split()
        assert oid == row['git_blob'] and kind == 'blob'
        start = end + 1
        size = int(size)
        blobs[path] = batch[start:start + size]
        offset = start + size + 1
        assert batch[offset - 1:offset] == b'\n'
    assert offset == len(batch)

    lfs = 0
    changes = []
    for row in inv['files']:
        path = row['path']
        assert row['mode'] == entries[path]['mode']
        assert row['git_blob'] == entries[path]['git_blob']
        blob = blobs[path]
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            pointer = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize (\d+)\n', blob)
            assert pointer, path
            assert row['sha256'] == pointer[1].decode() and row['bytes'] == int(pointer[2]), path
            lfs += 1
        else:
            assert row['sha256'] == sha(blob) and row['bytes'] == len(blob), path
        current = (ROOT / path).read_bytes()
        if sha(current) != row['sha256']:
            changes.append(path)

    spec = importlib.util.spec_from_file_location('section9_builder_review', ROOT / 'site/build_section9.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    graph = module.source_graph(ROOT)
    assert set(graph) == {'book/main.tex', 'book/polyhedral_volumes_and_geodesic_identities.tex',
                          'book/chapters/09-volume-hessians.tex', 'book/chapters/15-quantum-airy.tex',
                          'book/chapters/30-sharp-diagnostics.tex'}
    current_labels = [m.decode() for data in graph.values() for m in re.findall(rb'\\label\{([^{}]+)\}', data)]
    assert len(current_labels) == len(set(current_labels)), 'duplicate current source labels'
    assert set(m.decode() for m in labels) <= set(current_labels), 'original label lost'
    plan = (ROOT / 'INTEGRATION_PLAN.md').read_text()
    headers = re.findall(r'^### Phase (\d+) — (.+)$', plan, re.M)
    expected = [('6', 'Generate and verify the local edition'),
                ('7', 'Verify the complete local release'),
                ('8', 'Upload and publish the verified edition')]
    assert headers[-3:] == expected
    assert 'no further upload attempt is part of the current revision work' in plan
    assert 'remaining Sections 10–11, 17–22 and 32 and both appendices' in plan
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'baseline_commit': BASE,
        'exact_reconstruction': True,
        'original_main_sha256': sha(original),
        'fully_expanded_sha256': sha(fully_expanded),
        'original_labels': len(labels),
        'current_labels': len(current_labels),
        'inventory_verified_against_git_blobs_and_lfs_pointers': len(entries),
        'lfs_pointer_count': lfs,
        'currently_changed_inventory_paths': changes,
        'current_source_graph_sha256': {path: sha(data) for path, data in graph.items()},
        'plan_sha256': sha(plan.encode()),
        'final_phases': headers[-3:],
        'scope': 'Source reconstruction, preservation inventory, include-graph and release ordering only; no mathematical replay or PDF verification.'
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'structure-review.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
