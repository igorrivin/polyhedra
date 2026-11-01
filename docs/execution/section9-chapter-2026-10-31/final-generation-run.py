"""Recorded local release execution; paths intentionally pin this checkpoint."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import os
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = ROOT.parent / 'execution/section9-chapter-2026-10-31'
BUILD = Path('/tmp/polyhedra-section9-final-20261031')
PYTHON = '/tmp/polyhedra-baseline-20261031/bin/python'
SOURCE = '1bafb83d2ec152f1f8eac75b2be0e3c4b796198e'

def clean():
    assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == SOURCE
    assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)

clean()
assert not BUILD.exists(), 'Fresh build directory is required.'
BUILD.mkdir()
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPATH=str(ROOT / 'packages/volume-toolkit'),
           MPLCONFIGDIR='/tmp/polyhedra-mpl-20261031', GRADIO_ANALYTICS_ENABLED='False')
site = BUILD / 'site/section9'
result = BUILD / 'result.json'
commands = [
    ('final-numerical-run', [PYTHON, 'experiments/section9/run.py', '--output', str(result), '--site-dir', str(site)]),
    ('final-chapter-build', [PYTHON, 'site/build_section9.py', '--output-dir', str(site), '--computation-result', str(result), '--work-dir', str(BUILD / 'chapter-build')]),
    ('final-render-only', [PYTHON, 'experiments/section9/run.py', '--render-result', str(result), '--site-dir', str(site), '--chapter-page', str(site / 'chapter.html'), '--book-source-archive', str(site / 'downloads/monograph-source.zip')]),
]
records = []
first_result = None
for name, command in commands:
    clean()
    started = datetime.now(timezone.utc).isoformat()
    completed = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
    log = OUTER / (name + '.log')
    log.write_text('$ ' + ' '.join(command) + '\n' + completed.stdout + completed.stderr)
    records.append({'operation': name, 'command': command, 'cwd': str(ROOT), 'started_at_utc': started,
                    'returncode': completed.returncode, 'log': str(log), 'log_sha256': sha256(log.read_bytes()).hexdigest()})
    (OUTER / 'final-generation-run.json').write_text(json.dumps({'source_commit': SOURCE, 'records': records}, indent=2) + '\n')
    assert completed.returncode == 0, str(log)
    if first_result is None:
        first_result = result.read_bytes()
    else:
        assert result.read_bytes() == first_result, 'Stored numerical report was mutated.'
    clean()
    print(json.dumps({'completed': name, 'log': str(log)}), flush=True)
report = json.loads(first_result)
assert report['all_checks_passed']
assert report['provenance']['source_commit'] == SOURCE
assert report['provenance']['repository_dirty_at_start'] is False
assert len(report['checks']) == 12
manifest = json.loads((site / 'downloads/chapter-build.json').read_text())
assert manifest['source_commit'] == SOURCE and manifest['repository_dirty_at_start'] is False
assert not manifest['pending_evidence'] and not manifest['preliminary']
print(json.dumps({'status': 'clean_source_generation_passed', 'source_commit': SOURCE,
                  'build_directory': str(BUILD), 'result_sha256': sha256(first_result).hexdigest()}), flush=True)
