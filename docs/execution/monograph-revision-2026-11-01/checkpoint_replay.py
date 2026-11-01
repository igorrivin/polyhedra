#!/usr/bin/env python3
"""Run both reviewed fixed experiments without dirtying their source checkout."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01'
PYTHON = '/tmp/polyhedra-baseline-20261031/bin/python'
SOURCE = json.loads((OUT / 'source-checkpoint.json').read_text())

def state():
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=all'], cwd=ROOT, text=True)
    assert head == SOURCE['source_commit'] and not status
    return {'commit': head, 'dirty': False}

records = []
for name, script in [('airy', 'experiments/section15/check.py'), ('torus', 'experiments/section30/run.py')]:
    before = state()
    destination = OUT / f'clean-source-{name}.json'
    assert not destination.exists(), destination
    argv = [PYTHON, str(ROOT / script), '--output', str(destination)]
    start = time.perf_counter()
    result = subprocess.run(argv, cwd='/private/tmp', capture_output=True, text=True,
                            env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    after = state()
    (OUT / f'clean-source-{name}.stdout').write_text(result.stdout)
    (OUT / f'clean-source-{name}.stderr').write_text(result.stderr)
    record = {'argv': argv, 'cwd': '/private/tmp', 'environment_overrides': {'PYTHONDONTWRITEBYTECODE': '1'},
              'returncode': result.returncode, 'elapsed_seconds': time.perf_counter()-start,
              'before': before, 'after': after,
              'stdout': f'clean-source-{name}.stdout', 'stderr': f'clean-source-{name}.stderr'}
    records.append(record)
    (OUT / 'clean-source-replay-commands.json').write_text(json.dumps(records, indent=2) + '\n')
    assert result.returncode == 0, record
    assert destination.is_file()
    print(json.dumps({'experiment': name, 'output': str(destination),
                      'sha256': sha256(destination.read_bytes()).hexdigest(), 'clean_before_and_after': True}))
(OUT / 'clean-source-replay-state.json').write_text(json.dumps({
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'source_commit': SOURCE['source_commit'], 'both_runs_from_clean_source': True,
    'canonical_outputs_not_yet_copied': True,
}, indent=2) + '\n')
