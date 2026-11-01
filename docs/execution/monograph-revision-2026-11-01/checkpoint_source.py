#!/usr/bin/env python3
"""Commit only the sixteen source files independently approved by this increment."""
from pathlib import Path
from hashlib import sha256
from datetime import datetime, timezone
import json
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01'
BASELINE = 'df952174e55f08a52596d912d9713a9d1e116313'
APPROVALS = {
    'scientific-review/scientific-review-manifest.json': 'b0d62dc5a35b10f2ae27741d92add5cee2c06240bdee9c49226e8d7716dc1acc',
    'integration-review/integration-review-manifest.json': 'cd29a0c39c7f0564cef7f5edb9c3c5ad42991c0c9b70261d959050bf37a7288d',
    'integration-review/independent-integration-review.md': 'ead8b968b489283c73c7a66671ffb64e29cd883f8710cf0923d1245386a17fee',
}
commands = []

def git(*args, allowed_failure=None):
    result = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    item = {'argv': ['git', *args], 'cwd': str(ROOT), 'returncode': result.returncode,
            'stderr': result.stderr.decode()}
    if args[0] == 'show':
        item.update(stdout_sha256=sha256(result.stdout).hexdigest(), stdout_bytes=len(result.stdout))
    else:
        item['stdout'] = result.stdout.decode()
    commands.append(item)
    (OUT / 'source-checkpoint-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    if result.returncode and not (allowed_failure and allowed_failure(result)):
        raise RuntimeError(f'Git command failed: {args!r}')
    return result.stdout

for path, expected in APPROVALS.items():
    assert sha256((OUT / path).read_bytes()).hexdigest() == expected, path
review = json.loads((OUT / 'integration-review/integration-review-manifest.json').read_text())
sources = review['source_sha256']
assert len(sources) == 16
assert not review['unresolved_product_findings']
assert git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)
assert git('rev-parse', 'HEAD').decode().strip() == BASELINE
assert not git('remote').strip()
initial_staged = set(git('diff', '--cached', '--name-only').decode().splitlines())
assert not initial_staged or initial_staged == set(sources)
status = git('status', '--porcelain=v1', '-z', '--untracked-files=all').split(b'\0')
observed = {entry[3:].decode() for entry in status if entry}
assert observed == set(sources), (observed - set(sources), set(sources) - observed)
for path, expected in sources.items():
    assert sha256((ROOT / path).read_bytes()).hexdigest() == expected, path
git('diff', '--check')
git('add', '--', *sorted(sources))
staged = set(git('diff', '--cached', '--name-only', '-z').decode().strip('\0').split('\0'))
assert staged == set(sources)
for path, expected in sources.items():
    assert sha256(git('show', ':' + path)).hexdigest() == expected, path
expected_eof = ('book/chapters/15-quantum-airy.tex:512: new blank line at EOF.\n'
                'book/chapters/30-sharp-diagnostics.tex:672: new blank line at EOF.\n')
for name in ('15-quantum-airy.tex', '30-sharp-diagnostics.tex'):
    assert (OUT / 'structure' / name).read_bytes().endswith(b'\n\n')
    assert (ROOT / 'book/chapters' / name).read_bytes().endswith(b'\n\n')
git('diff', '--cached', '--check', allowed_failure=lambda r:
    r.returncode == 2 and r.stdout.decode() == expected_eof and not r.stderr)
(OUT / 'source-whitespace-exceptions.json').write_text(json.dumps({
    'observed': expected_eof.splitlines(),
    'reason': 'Preserved original extraction tails; no approved source bytes changed.',
    'only_allowed_notices': True,
    'first_attempt_commands': 'source-checkpoint-first-attempt-commands.json'
}, indent=2) + '\n')
git('commit', '-m', 'Revise Airy and torus evidence with independently checked companions')
head = git('rev-parse', 'HEAD').decode().strip()
assert git('rev-parse', 'HEAD^').decode().strip() == BASELINE
assert not git('status', '--porcelain=v1', '--untracked-files=all').strip()
record = {'generated_at_utc': datetime.now(timezone.utc).isoformat(),
          'baseline_commit': BASELINE, 'source_commit': head,
          'review_approval_sha256': APPROVALS, 'source_sha256': sources,
          'clean_after_commit': True, 'remote_count': 0,
          'scope': 'Local approved source commit only; no push or publication.'}
(OUT / 'source-checkpoint.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'source_commit': head, 'source_files': len(sources), 'clean': True}))
