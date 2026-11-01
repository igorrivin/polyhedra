"""Recorded author checks; independent review is a separate phase."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE = Path(__file__).resolve().parent
PYTHON = '/tmp/polyhedra-baseline-20261031/bin/python'
SOURCES = [
    'book/chapters/30-sharp-diagnostics.tex',
    'book/claims/section30.json',
    'experiments/section30/run.py',
    'experiments/section30/fixture.json',
    'experiments/section30/README.md',
    'experiments/section30/tests/test_diagnostic.py',
]
before = {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
commands = []
specifications = [
    ('torus-unit-tests', [PYTHON, '-m', 'unittest', 'discover', '-s',
                          'experiments/section30/tests', '-v'], ROOT),
    ('torus-ruff', ['/opt/anaconda3/bin/ruff', 'check', 'experiments/section30'], ROOT),
    ('torus-final-replay', [PYTHON, str(ROOT/'experiments/section30/run.py'),
                           '--output', str(HERE/'torus-author-result.json')], Path('/private/tmp')),
]
for name, argv, cwd in specifications:
    start = time.perf_counter()
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True,
                               env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    (HERE/f'{name}.stdout').write_text(completed.stdout)
    (HERE/f'{name}.stderr').write_text(completed.stderr)
    commands.append({'name': name, 'argv': argv, 'cwd': str(cwd),
                     'exit_code': completed.returncode,
                     'elapsed_seconds': time.perf_counter()-start})
    if completed.returncode:
        (HERE/'torus-author-commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        raise SystemExit(completed.returncode)
(HERE/'torus-author-commands.json').write_text(json.dumps(commands, indent=2)+'\n')
after = {p: sha256((ROOT/p).read_bytes()).hexdigest() for p in SOURCES}
assert after == before
chapter = (ROOT/SOURCES[0]).read_text()
baseline = (HERE/'structure/30-sharp-diagnostics.tex').read_text()
labels = lambda s: re.findall(r'\\label\{([^}]+)\}', s)
assert labels(chapter) == labels(baseline)
table = lambda s: re.findall(r'\\begin\{tabular\}\{r r r r r\}.*?\\end\{tabular\}', s, re.S)[0]
assert table(chapter) == table(baseline)
ledger = json.loads((ROOT/SOURCES[1]).read_text())
assert all(label in labels(chapter) for claim in ledger['claims'] for label in claim['labels'])
whitespace = {}
for name in SOURCES:
    whitespace[name] = [i for i, line in enumerate((ROOT/name).read_text().splitlines(), 1)
                        if line.rstrip() != line]
assert not any(whitespace.values())
snapshots = HERE/'torus-author-source'
snapshots.mkdir(exist_ok=True)
for name in SOURCES:
    target = snapshots/name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT/name).read_bytes())
report = json.loads((HERE/'torus-author-result.json').read_text())
manifest = {
    'role': 'author_checks_not_independent_review',
    'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    'baseline_commit': 'df952174e55f08a52596d912d9713a9d1e116313',
    'source_sha256': before,
    'sources_unchanged_during_checks': before == after,
    'baseline_labels_preserved_in_order': True,
    'chapter_label_count': len(labels(chapter)),
    'historical_table_bytes_preserved': True,
    'ledger_labels_resolve': True,
    'source_whitespace_check_passed': True,
    'all_recorded_commands_passed': all(c['exit_code'] == 0 for c in commands),
    'result_sha256': sha256((HERE/'torus-author-result.json').read_bytes()).hexdigest(),
    'result_source_sha256_matches': all(before[p] == h for p, h in report['provenance']['source_sha256'].items()),
    'summary': [{k: v for k, v in surface.items() if k != 'curves'}
                for surface in report['surfaces']],
    'limits': ['Author checks are not independent review.',
               'No full length8192 replay, theorem audit, interval length proof, source commit or publication.',
               'Fixed-list sensitivity assumes its error radius and no entering omitted curves.'],
}
assert manifest['result_source_sha256_matches']
(HERE/'torus-author-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
print(json.dumps({'checks_passed': True, 'source_sha256': before,
                  'manifest': str(HERE/'torus-author-manifest.json')}))
