"""Verify the local Sites checkpoint; remove only verified canonical Git sidecars."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
RAW = ROOT.parent / 'execution/sites-preview-2026-11-01'
CHECKPOINT = ROOT / 'docs/execution/sites-preview-2026-11-01'
MIRROR = ROOT.parent / 'publishing/polyhedra-reading-preview-20261101'
BASELINE = '800219f78bdacaf77639cf4d38ff27d4b7342faa'
SOURCE = 'e79d4cee5b9fd7f999054617406ecebb1b9677cd'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)


def textgit(*args, cwd=ROOT):
    return git(*args, cwd=cwd).decode().strip()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def identity(path):
    assert not path.is_symlink(), str(path)
    if not path.exists():
        return {'kind': 'absent'}
    if path.is_file():
        return {'kind': 'file', 'sha256': digest(path)}
    assert path.is_dir(), str(path)
    entries = []
    for child in sorted(path.rglob('*')):
        relative = child.relative_to(path)
        if any(part.startswith('._') for part in relative.parts):
            continue
        assert not child.is_symlink(), str(child)
        entries.append([str(relative), 'file', digest(child)] if child.is_file()
                       else [str(relative), 'directory'])
    return {'kind': 'directory', 'genuine_entry_count': len(entries),
            'genuine_tree_sha256': sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest(),
            'exclusion': 'Only ._* entries are excluded from genuine sibling-tree identity.'}


head = textgit('rev-parse', 'HEAD')
assert textgit('rev-parse', '--show-toplevel') == str(ROOT)
assert textgit('rev-parse', head + '^') == SOURCE
assert textgit('rev-parse', SOURCE + '^') == BASELINE
assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
cleanup = []
for candidate in sorted((ROOT / '.git').rglob('._*')):
    assert candidate.is_file() and not candidate.is_symlink(), str(candidate)
    data = candidate.read_bytes()
    assert len(data) >= 26 and data[:8] == bytes.fromhex('0005160700020000'), str(candidate)
    entry_count = int.from_bytes(data[24:26], 'big')
    assert 26 + 12 * entry_count <= len(data), str(candidate)
    for entry in range(entry_count):
        start = 26 + 12 * entry
        offset = int.from_bytes(data[start + 4:start + 8], 'big')
        size = int.from_bytes(data[start + 8:start + 12], 'big')
        assert offset + size <= len(data), str(candidate)
    sibling = candidate.with_name(candidate.name[2:])
    cleanup.append({'path': str(candidate.relative_to(ROOT)), 'bytes': len(data),
                    'sha256': sha256(data).hexdigest(), 'header_hex': data[:26].hex(),
                    'entry_count': entry_count, 'sibling': str(sibling.relative_to(ROOT)),
                    'sibling_before': identity(sibling)})
for row in cleanup:
    (ROOT / row['path']).unlink()
for row in cleanup:
    row['sibling_after'] = identity(ROOT / row['sibling'])
    assert row['sibling_after'] == row['sibling_before']
history_path = RAW / 'git-metadata-cleanup-history.json'
history = json.loads(history_path.read_text()) if history_path.exists() else []
for batch in history:
    assert digest(RAW / batch['record']) == batch['sha256']
batch_name = f'git-metadata-cleanup-batch-{len(history) + 1:03d}.json'
assert not (RAW / batch_name).exists()
cleanup_record = {'scope': 'Verified AppleDouble metadata only under consolidated .git; no original Git directories or genuine objects removed.',
                  'head': head, 'removed_count': len(cleanup), 'entries': cleanup}
write_json(RAW / batch_name, cleanup_record)
history.append({'record': batch_name, 'sha256': digest(RAW / batch_name),
                'head': head, 'removed_count': len(cleanup)})
write_json(history_path, history)

source_stage = json.loads((RAW / 'source-staging-manifest.json').read_text())
for name, expected in source_stage['sha256'].items():
    assert sha256(git('show', SOURCE + ':' + name)).hexdigest() == expected, name
approved = json.loads((CHECKPOINT / 'author-final-manifest.json').read_text())['source_sha256']
assert len(approved) == 9
for name, expected in approved.items():
    assert digest(ROOT / name) == expected == sha256(git('show', 'HEAD:' + name)).hexdigest(), name
science = json.loads((ROOT / 'docs/execution/section9-barrier-2026-10-31/final-artifact-manifest.json').read_text())['sha256']
for name, expected in science.items():
    assert digest(ROOT / name) == expected == sha256(git('show', 'HEAD:' + name)).hexdigest(), name
assert len(science) == 46
stage = json.loads((RAW / 'final-staging-manifest.json').read_text())
for name, expected in stage['sha256'].items():
    assert digest(ROOT / name) == expected == sha256(git('show', 'HEAD:' + name)).hexdigest(), name
copied = 0
for manifest_name in ('evidence-copy-manifest.json', 'final-copy-manifest.json'):
    for row in json.loads((CHECKPOINT / manifest_name).read_text())['files']:
        destination = Path(row['destination'])
        assert digest(destination) == row['sha256'] and destination.stat().st_size == row['bytes']
        assert destination.read_bytes() == Path(row['source']).read_bytes()
        copied += 1
changes = textgit('diff', '--name-only', BASELINE, head).splitlines()
for name in changes:
    assert (name in approved or name.startswith('docs/execution/sites-preview-2026-11-01/')
            or name.startswith('artifacts/sites-preview/') or name == 'README.md'), name
unchanged = {}
for name in ('packages', 'research', 'book', 'provenance', 'audit', 'experiments',
             'site/section9', 'artifacts/section9', 'docs/execution/section9-barrier-2026-10-31',
             'docs/execution/section9-chapter-2026-10-31', 'docs/execution/numerical-correctness-2026-10-31',
             'docs/execution/2026-10-31'):
    before = textgit('rev-parse', BASELINE + ':' + name)
    assert before == textgit('rev-parse', head + ':' + name), name
    unchanged[name] = before

inventory = json.loads((ROOT.parent / 'audit/2026-10-31/source-inventory.json').read_text())
originals = []
verified = 0
for original in inventory['repositories']:
    path = ROOT.parent / original['path']
    original_head = textgit('rev-parse', 'HEAD', cwd=path)
    assert original_head == original['head'] and not git('status', '--porcelain', cwd=path)
    ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', original_head, head],
                              cwd=ROOT, env=ENV, capture_output=True)
    assert ancestor.returncode == 0 and not ancestor.stdout and not ancestor.stderr
    for row in original['files']:
        candidate = path / row['path']
        assert digest(candidate) == row['sha256'] and candidate.stat().st_size == row['bytes']
        verified += 1
    originals.append({'path': original['path'], 'head': original_head, 'worktree_clean': True,
                      'head_is_ancestor_of_final': True, 'tracked_files_verified': len(original['files'])})
assert verified == 953
original_archive = inventory['monograph_archive']
assert digest(ROOT.parent / original_archive['path']) == original_archive['sha256']
preserved_archive = json.loads((ROOT / 'provenance/source-map.json').read_text())['monograph_archive']
assert digest(ROOT / preserved_archive['path']) == preserved_archive['sha256'] == original_archive['sha256']
reference = ROOT / 'book/reference/polyhedral_volumes_and_geodesic_identities.pdf'
assert digest(reference) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'
assert not textgit('remote', '-v')

export = json.loads((CHECKPOINT / 'final-export-verification.json').read_text())
physical_files = set()
for path in (MIRROR / 'dist').rglob('*'):
    assert not path.is_symlink(), str(path)
    relative = path.relative_to(MIRROR / 'dist')
    assert not any(part.startswith('._') or part in ('.DS_Store', '__MACOSX', '.git') for part in relative.parts)
    if path.is_file():
        physical_files.add(str(relative))
        assert digest(path) == export['payload_sha256'][str(relative)], str(relative)
assert physical_files == set(export['payload_sha256']) and len(physical_files) == 49
preview_manifest = json.loads((MIRROR / 'dist/preview-manifest.json').read_text())
assert preview_manifest['research_source'] == {'commit': SOURCE, 'dirty': False, 'status_porcelain': []}
assert preview_manifest['numerical_source_commit'] == 'c1f100b957166b93eca0d214586322d5af71b9cf'
candidate = json.loads((ROOT / 'artifacts/sites-preview/manifest.json').read_text())
candidate_path = ROOT / candidate['archive']['path']
assert digest(candidate_path) == candidate['archive']['sha256']
assert candidate_path.stat().st_size == candidate['archive']['bytes']
archive_review = json.loads((CHECKPOINT / 'final-archive-verification.json').read_text())
assert archive_review['archive_sha256'] == digest(candidate_path)
assert archive_review['file_count'] == 50 and archive_review['payload_files_identical_to_clean_export'] == 49
assert archive_review['research_source_commit'] == SOURCE and archive_review['site_source_commit'] is None
state = json.loads((CHECKPOINT / 'site-status-after-packaging.json').read_text())
assert state['project_id'] == 'appgprj_6ae6b5b94abc8191aa00dfe244adcf37'
assert state['latest_version_number'] == 0 and state['current_live_url'] is None
assert state['current_preview_url'] is None and state['current_user_role'] == 'owner'
assert state['access_mode'] == 'custom' and state['allowed_user_roles'] == ['owner']
assert state['allowed_group_count'] == 0

plain_command = ['git', 'fsck', '--full']
plain = subprocess.run(plain_command, cwd=ROOT, env=ENV, capture_output=True, text=True)
(RAW / 'final-fsck-plain.stdout').write_text(plain.stdout)
(RAW / 'final-fsck-plain.stderr').write_text(plain.stderr)
assert plain.returncode == 0 and not plain.stderr
preserved = []
for line in plain.stdout.splitlines():
    match = re.fullmatch(r'dangling (blob|tree|commit|tag) ([0-9a-f]{40})', line)
    assert match, line
    kind, object_id = match.groups()
    assert textgit('cat-file', '-t', object_id) == kind
    data = git('cat-file', kind, object_id)
    saved = RAW / f'integrity-object-{object_id}.{kind}'
    if saved.exists():
        assert saved.read_bytes() == data
    else:
        saved.write_bytes(data)
    preserved.append({'git_object': object_id, 'type': kind, 'notice': line,
                      'preserved_path': str(saved), 'sha256': digest(saved), 'bytes': len(data)})
plain_record = {'command': plain_command, 'returncode': plain.returncode,
                'stdout': plain.stdout, 'stderr': plain.stderr,
                'classification': 'Informational dangling-object notices retained; exit zero with empty stderr.',
                'preserved_objects': preserved, 'archive_refs_created': [], 'genuine_objects_deleted': []}
write_json(RAW / 'final-plain-fsck-record.json', plain_record)
fsck_command = ['git', 'fsck', '--full', '--no-dangling']
fsck = subprocess.run(fsck_command, cwd=ROOT, env=ENV, capture_output=True, text=True)
(RAW / 'final-fsck.stdout').write_text(fsck.stdout)
(RAW / 'final-fsck.stderr').write_text(fsck.stderr)
assert fsck.returncode == 0 and not fsck.stdout and not fsck.stderr
assert not list((ROOT / '.git').rglob('._*'))
assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
assert textgit('rev-parse', 'HEAD') == head
assert digest(Path(__file__)) == digest(CHECKPOINT / Path(__file__).name)

receipt = {
    'status': 'final_postcommit_verification_passed_offline_candidate_only',
    'verified_at_utc': datetime.now(timezone.utc).isoformat(),
    'baseline': BASELINE, 'source_commit': SOURCE, 'artifact_and_closeout_commit': head,
    'final_head': head, 'two_commits_are_direct_descendants_of_baseline': True,
    'worktree_clean': True, 'index_clean': True,
    'source_staging_hashes_verified_at_source_commit': len(source_stage['sha256']),
    'approved_source_sha256': approved, 'scientific_artifacts_verified': len(science),
    'scientific_artifact_sha256': science, 'evidence_copies_verified': copied,
    'final_staged_files_verified': len(stage['sha256']),
    'original_repositories': originals, 'original_tracked_files_verified': verified,
    'original_archive_sha256': original_archive['sha256'],
    'supplied_reference_pdf_sha256': digest(reference),
    'unchanged_trees_since_baseline': unchanged, 'scoped_changed_paths': changes,
    'preview_manifest_sha256': export['preview_manifest_sha256'],
    'final_dist_file_count': len(physical_files), 'archive': candidate['archive'],
    'archive_verification_sha256': digest(CHECKPOINT / 'final-archive-verification.json'),
    'site_project_id': state['project_id'], 'site_source_commit': None,
    'site_status_after_packaging_sha256': digest(CHECKPOINT / 'site-status-after-packaging.json'),
    'git_remotes': [], 'remote_operations': 'No canonical remote or push; the official mirror source-open attempt failed at Git-host DNS.',
    'metadata_cleanup': {'generated_dist_removed_count': export['metadata_removed_count'],
                         'git_removed_count_in_final_batch': len(cleanup),
                         'git_total_removed_count': sum(batch['removed_count'] for batch in history),
                         'git_history_sha256': digest(history_path), 'git_batches': history,
                         'remaining_git_candidates': 0},
    'plain_git_fsck': plain_record,
    'git_fsck_no_dangling': {'command': fsck_command, 'returncode': fsck.returncode,
                            'stdout': fsck.stdout, 'stderr': fsck.stderr},
    'final_staging_manifest_sha256': digest(RAW / 'final-staging-manifest.json'),
    'verification_script_sha256': digest(Path(__file__)),
    'limitations': ['Offline candidate only: no pushed Sites source commit, saved version or deployment.',
                    'Registered Site is owner-private; source synchronization is blocked by git.chatgpt-team.site DNS.',
                    'Archive format retains the recorded mtime and com.apple.provenance PAX headers; metadata sidecar payload files are absent.',
                    'Browser rendering and interaction were not tested.',
                    'Numerics and PDF bytes were preserved, not regenerated or replayed in this presentation increment.',
                    'Section 9 review does not extend to the full monograph.']}
write_json(RAW / 'final-postcommit-verification.json', receipt)
print(json.dumps({'status': receipt['status'], 'source_commit': SOURCE,
                  'final_head': head, 'archive_sha256': candidate['archive']['sha256'],
                  'scientific_artifacts_verified': len(science), 'original_tracked_files_verified': verified,
                  'approved_source_count': len(approved), 'git_metadata_removed': sum(batch['removed_count'] for batch in history),
                  'plain_fsck_informational_dangling_count': len(preserved),
                  'receipt_sha256': digest(RAW / 'final-postcommit-verification.json')}, indent=2))
