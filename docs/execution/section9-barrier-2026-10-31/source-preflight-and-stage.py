"""Verify the approved, explicit source/evidence scope, then stage it locally."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = Path(__file__).resolve().parent
BASELINE = '014d1c4e70dfdfc852fa542f3a9c469f08dbd618'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

manifest_path = OUTER / 'source-evidence-staging-manifest.json'
assert digest(manifest_path) == 'c84f98c739889ac079d4a07046e00e4b8e0b2146cc052e34b41ea7d2c27284c7'
manifest = json.loads(manifest_path.read_text())
assert git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)
assert git('rev-parse', 'HEAD').decode().strip() == BASELINE
assert not git('diff', '--cached', '--name-only')
expected = {row['path']: row['sha256'] for row in manifest['files']}
assert len(expected) == len(manifest['files']) == 127
for row in manifest['files']:
    path = ROOT / row['path']
    assert path.stat().st_size == row['bytes'] and digest(path) == row['sha256'], row['path']
approved = {}
for name, field in [('publication-review-manifest.json', 'source_sha256'),
                    ('review-final-manifest.json', 'source_hashes')]:
    approved.update(json.loads((OUTER / name).read_text())[field])
for name, value in approved.items():
    assert digest(ROOT / name) == value, name
copied = []
for name in ('evidence-copy-manifest.json', 'strict-preview-evidence-copy-manifest.json'):
    record = json.loads((OUTER / name).read_text())
    assert (ROOT / 'docs/execution/section9-barrier-2026-10-31' / name).read_bytes() == (OUTER / name).read_bytes()
    for row in record['files']:
        source, dest = Path(row['source']), Path(row['destination'])
        assert source.read_bytes() == dest.read_bytes()
        assert digest(dest) == row['sha256'] and dest.stat().st_size == row['bytes']
        copied.append(str(dest.relative_to(ROOT)))
normal = manifest['normal_add_paths']
forced = manifest['force_add_only_paths']
assert set(normal).isdisjoint(forced) and set(normal) | set(forced) == set(expected)
changed = set(git('diff', '--name-only').decode().splitlines())
untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
assert changed | untracked == set(normal), sorted((changed | untracked) ^ set(normal))
preflight = {'baseline_commit': BASELINE, 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
             'staging_manifest_sha256': digest(manifest_path), 'paths': list(expected), 'sha256': expected,
             'approved_source_sha256': approved, 'copied_evidence_paths_verified': copied,
             'named_archival_whitespace_exceptions': manifest['named_archival_whitespace_exceptions']}
(OUTER / 'source-preflight.json').write_text(json.dumps(preflight, indent=2) + '\n')
subprocess.run(['git', 'add', '--', *normal], cwd=ROOT, check=True)
subprocess.run(['git', 'add', '-f', '--', *forced], cwd=ROOT, check=True)
assert set(git('diff', '--cached', '--name-only').decode().splitlines()) == set(expected)
for name, value in expected.items():
    assert sha256(git('show', ':' + name)).hexdigest() == value
check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, capture_output=True, text=True)
(OUTER / 'source-staging-whitespace.log').write_text(check.stdout + check.stderr)
diagnostics = [line for line in check.stdout.splitlines() if ': trailing whitespace.' in line or ': new blank line at EOF.' in line or ': space before tab in indent.' in line]
exception_paths = {row['path'] for row in manifest['named_archival_whitespace_exceptions']}
assert diagnostics and all(line.split(':', 1)[0] in exception_paths for line in diagnostics), diagnostics
assert {line.split(':', 1)[0] for line in diagnostics} == exception_paths
assert not check.stderr and check.returncode == 2
record = {'status': 'explicit_source_staging_verified', 'staged_path_count': len(expected),
          'normal_add_count': len(normal), 'explicit_force_add_count': len(forced),
          'staged_hashes_match_preflight': True, 'cached_diff_check_returncode': check.returncode,
          'cached_diff_check_exception_paths': sorted(exception_paths),
          'cached_diff_check_diagnostic_count': len(diagnostics),
          'cached_diff_check_log_sha256': digest(OUTER / 'source-staging-whitespace.log'),
          'disposition': 'Only the three explicitly approved archival byte-preservation exceptions remain; no authored-source whitespace exception.'}
(OUTER / 'source-staging-verification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps(record, indent=2))
