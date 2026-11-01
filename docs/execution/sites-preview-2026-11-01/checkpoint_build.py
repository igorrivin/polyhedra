"""Build from a clean research commit and sanitize only generated sidecars."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import os
import subprocess

OUTER = Path('/Volumes/Lexar/lambda/devel/polyhedra')
ROOT = OUTER / 'consolidated'
RAW = OUTER / 'execution/sites-preview-2026-11-01'
MIRROR = OUTER / 'publishing/polyhedra-reading-preview-20261101'
DIST = MIRROR / 'dist'
PYTHON = '/tmp/polyhedra-baseline-20261031/bin/python'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
source = git('rev-parse', 'HEAD')
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
commands = []
for label, argv in [
    ('final-preview-build', [PYTHON, 'site/build_preview.py', '--output-dir', str(DIST), '--require-clean']),
    ('final-search-checks', ['node', 'site/tests/test_preview_search.cjs', str(DIST / 'search-index.json')]),
]:
    assert not git('status', '--porcelain')
    result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True)
    log = RAW / (label + '.log')
    log.write_text(result.stdout + result.stderr)
    record = {'argv': argv, 'cwd': str(ROOT), 'environment': {'PYTHONDONTWRITEBYTECODE': '1'},
              'returncode': result.returncode, 'source_commit': source,
              'log_sha256': digest(log), 'worktree_clean_before': True,
              'worktree_clean_after': not bool(git('status', '--porcelain'))}
    write_json(RAW / (label + '-command.json'), record)
    commands.append(record)
    assert result.returncode == 0 and record['worktree_clean_after'], label
assert git('rev-parse', 'HEAD') == source
assert not DIST.is_symlink()
manifest = json.loads((DIST / 'preview-manifest.json').read_text())
assert manifest['research_source']['commit'] == source and manifest['research_source']['dirty'] is False
assert manifest['research_source']['status_porcelain'] == []
assert manifest['numerical_source_commit'] == 'c1f100b957166b93eca0d214586322d5af71b9cf'
author = json.loads((RAW / 'author-final-manifest.json').read_text())
assert digest(RAW / 'author-preview-manifest.json') == author['preview_manifest_sha256']
reviewed = json.loads((RAW / 'author-preview-manifest.json').read_text())
assert manifest['output_sha256'] == reviewed['output_sha256']
expected = dict(manifest['output_sha256'])
expected['preview-manifest.json'] = digest(DIST / 'preview-manifest.json')
assert len(expected) == 49
for name, value in expected.items():
    path = DIST / name
    assert not path.is_symlink() and path.is_file() and digest(path) == value, name
for name, value in manifest['input_sha256'].items():
    assert digest(ROOT / name) == value, name
assert len(manifest['input_sha256']) == 46

removals = []
for path in sorted(DIST.rglob('*')):
    assert not path.is_symlink(), str(path)
    relative = path.relative_to(DIST).as_posix()
    if path.name.startswith('._'):
        assert path.is_file(), relative
        data = path.read_bytes()
        assert len(data) >= 26 and data[:8] == bytes.fromhex('0005160700020000'), relative
        entries = int.from_bytes(data[24:26], 'big')
        assert len(data) >= 26 + 12 * entries, relative
        sibling = path.with_name(path.name[2:])
        removals.append({'path': relative, 'sha256': sha256(data).hexdigest(), 'bytes': len(data),
                         'header_hex': data[:26].hex(), 'entry_count': entries,
                         'genuine_sibling': str(sibling.relative_to(DIST)),
                         'genuine_sibling_exists': sibling.exists(),
                         'genuine_sibling_sha256': digest(sibling) if sibling.is_file() else None})
    elif path.is_file():
        assert relative in expected, relative
    else:
        assert path.name not in ('.git', '.DS_Store', '__MACOSX', '.openai'), relative
for row in removals:
    path = DIST / row['path']
    assert digest(path) == row['sha256']
    path.unlink()
for name, value in expected.items():
    assert digest(DIST / name) == value, name
actual = {p.relative_to(DIST).as_posix() for p in DIST.rglob('*') if p.is_file()}
assert actual == set(expected)
assert not any(p.is_symlink() or p.name.startswith('._') or p.name in ('.DS_Store', '__MACOSX', '.git')
               for p in DIST.rglob('*'))
cleanup = {'scope': 'Generated deployment dist only; no original source metadata or genuine payload removed',
           'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'directory': str(DIST),
           'removed_count': len(removals), 'removed': removals,
           'all_49_genuine_payload_hashes_unchanged': True, 'payload_sha256': expected}
write_json(RAW / 'final-dist-metadata-cleanup.json', cleanup)
hosting = json.loads((MIRROR / '.openai/hosting.json').read_text())
assert hosting == {'project_id': 'appgprj_6ae6b5b94abc8191aa00dfe244adcf37', 'static': {'directory': 'dist'}}
assert digest(MIRROR / '.gitignore') == digest(ROOT / 'site/preview/source.gitignore')
assert not git('status', '--porcelain') and git('rev-parse', 'HEAD') == source
record = {'status': 'ready_for_offline_package_not_deployed', 'source_commit': source,
          'research_worktree_clean': True, 'mirror': str(MIRROR), 'dist': str(DIST),
          'preview_manifest_sha256': digest(DIST / 'preview-manifest.json'),
          'payload_sha256': expected, 'payload_file_count': len(expected),
          'scientific_inputs_verified': 46, 'validation': manifest['validation'],
          'all_48_payloads_match_independently_reviewed_export': True,
          'pdf_sha256': manifest['pdf']['sha256'], 'commands': commands,
          'metadata_removed_count': len(removals),
          'metadata_cleanup_sha256': digest(RAW / 'final-dist-metadata-cleanup.json'),
          'hosting_manifest_sha256': digest(MIRROR / '.openai/hosting.json'),
          'publication': 'None: source synchronization is blocked by the recorded Git-host DNS failure.',
          'browser_verification': 'Not performed; static and search-logic checks only.'}
write_json(RAW / 'final-export-verification.json', record)
print(json.dumps({'status': record['status'], 'source_commit': source,
                  'payload_file_count': len(expected), 'metadata_removed_count': len(removals),
                  'preview_manifest_sha256': record['preview_manifest_sha256']}, indent=2))
