"""Fresh fixed-source combined preview; canonical generated artifacts are untouched."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path.cwd()).resolve()
outer = Path(__file__).resolve().parent
checkpoint = root / 'docs/execution/section9-barrier-2026-10-31'
expected_core = 'd782aff2a23c9073c6f7cf02666cc0ec3f4446f28185c7474116fcf42edbbd07'
assert sha256((root / 'packages/volume-toolkit/ideal_poly_volume_toolkit/angle_barrier.py').read_bytes()).hexdigest() == expected_core
for name in ('barrier-review.md', 'barrier-publication-review.md'):
    assert (checkpoint / name).read_bytes() == (outer / name).read_bytes(), name
preview = Path(tempfile.mkdtemp(prefix='polyhedra-barrier-strict-preview-20261031-'))
site = preview / 'site/section9'
record = {'started_at_utc': datetime.now(timezone.utc).isoformat(), 'preview_root': str(preview), 'site_dir': str(site),
          'scope': 'Strict evidence-complete dirty-source preview; final clean-source generation follows source commit',
          'fixed_core_sha256': expected_core, 'commands': []}
(outer / 'strict-preview-location.json').write_text(json.dumps(record, indent=2) + '\n')
python = '/tmp/polyhedra-baseline-20261031/bin/python'
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONPATH': str(root / 'packages/volume-toolkit')}
commands = [
    ('grid-run', [python, 'experiments/section9/run.py', '--output', str(preview / 'result.json'), '--site-dir', str(site)]),
    ('barrier-run', [python, 'experiments/section9/barrier_run.py', '--output', str(preview / 'barrier-result.json'), '--site-dir', str(site)]),
    ('chapter-build', [python, 'site/build_section9.py', '--output-dir', str(site), '--computation-result', str(preview / 'result.json'),
                       '--barrier-result', str(preview / 'barrier-result.json'), '--work-dir', str(preview / 'chapter-build')]),
    ('grid-render-only', [python, 'experiments/section9/run.py', '--render-result', str(preview / 'result.json'), '--site-dir', str(site),
                          '--chapter-page', str(site / 'chapter.html'), '--book-source-archive', str(site / 'downloads/monograph-source.zip')]),
    ('barrier-render-only', [python, 'experiments/section9/barrier_run.py', '--render-result', str(preview / 'barrier-result.json'),
                             '--site-dir', str(site), '--chapter-page', str(site / 'chapter.html')]),
]
report_snapshots = {}
for name, command in commands:
    print(json.dumps({'starting': name, 'preview': str(preview)}), flush=True)
    log = outer / ('strict-preview-' + name + '.log')
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT)
    record['commands'].append({'name': name, 'command': command, 'returncode': result.returncode, 'log': str(log)})
    (outer / 'strict-preview-location.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode:
        print(log.read_text(), flush=True)
        raise SystemExit(result.returncode)
    if name == 'chapter-build':
        report_snapshots = {filename: (preview / filename).read_bytes() for filename in ('result.json', 'barrier-result.json')}
    print(json.dumps({'completed': name, 'returncode': result.returncode}), flush=True)
for filename, data in report_snapshots.items():
    assert (preview / filename).read_bytes() == data
record['both_reports_preserved_by_render_only'] = True
record['report_sha256'] = {name: sha256(data).hexdigest() for name, data in report_snapshots.items()}
record['completed_at_utc'] = datetime.now(timezone.utc).isoformat()
(outer / 'strict-preview-location.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'completed_preview': str(preview), 'report_sha256': record['report_sha256']}, indent=2), flush=True)
