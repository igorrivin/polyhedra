"""Copy only verified final outputs and named evidence, then stage the artifact checkpoint."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = Path(__file__).resolve().parent
CHECKPOINT = ROOT / 'docs/execution/section9-barrier-2026-10-31'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)

location = json.loads((OUTER / 'final-generation-location.json').read_text())
checks = json.loads((OUTER / 'final-generation-checks.json').read_text())
replay = json.loads((OUTER / 'final-detached-replay.json').read_text())
assert checks['all_checks_passed'] and replay['status'] == 'both_fresh_detached_replays_passed'
assert checks['source_commit'] == replay['source_commit'] == location['source_commit']
assert git('rev-parse', 'HEAD').decode().strip() == location['source_commit']
assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
temporary = Path(location['preview_root'])
site = temporary / 'site/section9'
artifact_sources = {f'site/section9/{name}': site / name for name in checks['final_site_asset_sha256']}
artifact_sources.update({f'artifacts/section9/{name}': temporary / name for name in ('result.json', 'barrier-result.json')})
artifact_hashes = {name: digest(path) for name, path in artifact_sources.items()}
for name, expected in checks['final_site_asset_sha256'].items():
    assert digest(site / name) == expected
for name, expected in checks['report_sha256'].items():
    assert digest(temporary / name) == expected
old_files = {str(p.relative_to(ROOT / 'site/section9')) for p in (ROOT / 'site/section9').rglob('*')
             if p.is_file() and not p.name.startswith('._')}
obsolete = old_files - set(checks['final_site_asset_sha256'])
assert obsolete == {'downloads/inspection/docs/execution/section9-chapter-2026-10-31/companion_reference_probes.py'}
removed = []
for name in sorted(obsolete):
    relative = 'site/section9/' + name
    path = ROOT / relative
    assert digest(path) == sha256(git('show', 'HEAD:' + relative)).hexdigest()
    removed.append({'path': relative, 'sha256': digest(path), 'reason': 'Obsolete generated inspection copy absent from the strict export; original frozen checkpoint source is preserved.'})
record = {'source_commit': location['source_commit'], 'copied_at_utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Verified final reports/site outputs and explicitly named generation evidence; originals untouched.', 'files': [], 'removed_generated_inspection_copies': removed}

def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    assert destination.read_bytes() == source.read_bytes()
    record['files'].append({'source': str(source), 'destination': str(destination.relative_to(ROOT)),
                            'sha256': digest(destination), 'bytes': destination.stat().st_size})

for name, source in artifact_sources.items():
    copy(source, ROOT / name)
for row in removed:
    (ROOT / row['path']).unlink()
artifact_manifest = {'source_commit': location['source_commit'], 'scope': 'All canonical numerical reports and site files after both backlink refreshes',
                     'canonical_artifact_count': len(artifact_hashes), 'sha256': artifact_hashes,
                     'pdf_pages_match_independently_inspected_layout': True,
                     'page_sha256': checks['rendered_page_sha256']}
(OUTER / 'final-artifact-manifest.json').write_text(json.dumps(artifact_manifest, indent=2) + '\n')
evidence_names = [
    'source-evidence-staging-manifest.json', 'source-staging-normal-paths.txt', 'source-staging-ignored-paths.txt',
    'source-preflight-and-stage.py', 'source-preflight.json', 'source-staging-verification.json', 'source-commit.json',
    'checkpoint-harness-history.json', 'final-generation-run.py', 'final-generation-location.json',
    'final-generation-grid-run.log', 'final-generation-barrier-run.log', 'final-generation-chapter-build.log',
    'final-generation-grid-render-only.log', 'final-generation-barrier-render-only.log',
    'final-generation-checks.py', 'final-generation-checks.json', 'final-generation-checks.log', 'final-build-manifest.json',
    'final-detached-replay.py', 'final-detached-replay.json', 'final-detached-grid.log', 'final-detached-barrier.log',
    'final-artifact-manifest.json', 'final-copy-and-stage.py',
    'final-copy-and-stage-attempt-1.py', 'final-copy-and-stage-attempt-1.log',
]
for name in evidence_names:
    copy(OUTER / name, CHECKPOINT / name)
(OUTER / 'final-copy-manifest.json').write_text(json.dumps(record, indent=2) + '\n')
(CHECKPOINT / 'final-copy-manifest.json').write_bytes((OUTER / 'final-copy-manifest.json').read_bytes())
paths = [row['destination'] for row in record['files']] + [str((CHECKPOINT / 'final-copy-manifest.json').relative_to(ROOT))]
paths += [row['path'] for row in removed]
actual_changes = set(git('diff', '--name-only').decode().splitlines())
untracked = set(git('ls-files', '--others', '--exclude-standard').decode().splitlines())
assert actual_changes | untracked <= set(paths)
normal, forced = [], []
for name in paths:
    ignored = subprocess.run(['git', 'check-ignore', '-q', '--', name], cwd=ROOT).returncode
    assert ignored in (0, 1)
    (forced if ignored == 0 else normal).append(name)
subprocess.run(['git', 'add', '--', *normal], cwd=ROOT, check=True)
if forced:
    subprocess.run(['git', 'add', '-f', '--', *forced], cwd=ROOT, check=True)
staged = git('diff', '--cached', '--name-only').decode().splitlines()
assert set(staged) <= set(paths)
for name in staged:
    path = ROOT / name
    if path.is_file():
        assert digest(path) == sha256(git('show', ':' + name)).hexdigest()
    else:
        assert name in {row['path'] for row in removed}
check = subprocess.run(['git', 'diff', '--cached', '--check'], cwd=ROOT, text=True, capture_output=True)
(OUTER / 'artifact-staging-whitespace.log').write_text(check.stdout + check.stderr)
assert not check.stderr
diagnostics = [line for line in check.stdout.splitlines() if ': trailing whitespace.' in line or ': new blank line at EOF.' in line or ': space before tab in indent.' in line]
assert diagnostics in ([], ['site/section9/chapter.html:42: trailing whitespace.']), diagnostics
assert check.returncode == (2 if diagnostics else 0)
assert diagnostics or not check.stdout
verification = {'status': 'artifact_staging_verified', 'source_commit': location['source_commit'],
                'staged_paths': staged, 'staged_count': len(staged), 'canonical_artifact_count': len(artifact_hashes),
                'normal_add_paths': normal, 'explicit_force_add_only_paths': forced,
                'all_staged_bytes_verified': True, 'removed_generated_inspection_copies': removed,
                'whitespace_check_returncode': check.returncode,
                'named_generated_whitespace_exception': {'path': 'site/section9/chapter.html', 'line': 42,
                    'sha256': digest(ROOT / 'site/section9/chapter.html'), 'diagnostic': diagnostics[0] if diagnostics else None,
                    'reason': 'Unmodified Pandoc output; exception applies only if this exact diagnostic occurs.'} if diagnostics else None,
                'whitespace_log_sha256': digest(OUTER / 'artifact-staging-whitespace.log')}
(OUTER / 'artifact-staging-verification.json').write_text(json.dumps(verification, indent=2) + '\n')
print(json.dumps({'status': verification['status'], 'staged_count': len(staged), 'canonical_artifact_count': len(artifact_hashes),
                  'normal_add_count': len(normal), 'force_add_count': len(forced), 'removed_generated_copy_count': len(removed),
                  'generated_whitespace_diagnostic': diagnostics}, indent=2))
