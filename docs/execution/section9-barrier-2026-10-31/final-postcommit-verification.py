"""Final integrity receipt; only verified new-repository AppleDouble metadata may be removed."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = ROOT.parent / 'execution/section9-barrier-2026-10-31'
BASELINE = '014d1c4e70dfdfc852fa542f3a9c469f08dbd618'
SOURCE = json.loads((OUTER / 'source-commit.json').read_text())['source_commit']
ARTIFACT = json.loads((OUTER / 'artifact-commit.json').read_text())['artifact_commit']
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)

def textgit(*args, cwd=ROOT):
    return git(*args, cwd=cwd).decode().strip()

def sibling_identity(path):
    assert not path.is_symlink(), str(path)
    if path.is_file():
        return {'kind': 'file', 'sha256': digest(path)}
    assert path.is_dir(), str(path)
    entries = []
    for child in sorted(path.rglob('*')):
        relative = child.relative_to(path)
        if any(part.startswith('._') for part in relative.parts):
            continue
        assert not child.is_symlink(), str(child)
        entries.append([str(relative), 'file', digest(child)] if child.is_file() else [str(relative), 'directory'])
    return {'kind': 'directory', 'genuine_tree_sha256': sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest(),
            'genuine_entry_count': len(entries), 'exclusion': 'Only ._* metadata is excluded from genuine sibling-tree identity.'}

head = textgit('rev-parse', 'HEAD')
assert textgit('rev-parse', '--show-toplevel') == str(ROOT)
assert textgit('rev-parse', head + '^') == ARTIFACT
assert textgit('rev-parse', ARTIFACT + '^') == SOURCE
assert textgit('rev-parse', SOURCE + '^') == BASELINE
assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
cleanup = []
for candidate in sorted((ROOT / '.git').rglob('._*')):
    assert candidate.is_file() and not candidate.is_symlink(), str(candidate)
    data = candidate.read_bytes()
    assert data[:8] == bytes.fromhex('0005160700020000'), str(candidate)
    sibling = candidate.with_name(candidate.name[2:])
    cleanup.append({'path': str(candidate.relative_to(ROOT)), 'sha256': sha256(data).hexdigest(),
                    'header_hex': data[:26].hex(), 'sibling': str(sibling.relative_to(ROOT)),
                    'sibling_before': sibling_identity(sibling)})
for row in cleanup:
    (ROOT / row['path']).unlink()
for row in cleanup:
    row['sibling_after'] = sibling_identity(ROOT / row['sibling'])
    assert row['sibling_after'] == row['sibling_before']
cleanup_record = {'scope': 'Verified AppleDouble metadata only under consolidated .git; genuine siblings and original repositories unchanged.',
                  'head': head, 'removed_count': len(cleanup), 'entries': cleanup}
history_path = OUTER / 'metadata-cleanup-history.json'
history = json.loads(history_path.read_text()) if history_path.exists() else []
for batch in history:
    assert digest(OUTER / batch['record']) == batch['sha256']
batch_name = f'metadata-cleanup-batch-{len(history) + 1:03d}.json'
assert not (OUTER / batch_name).exists()
(OUTER / batch_name).write_text(json.dumps(cleanup_record, indent=2) + '\n')
history.append({'record': batch_name, 'sha256': digest(OUTER / batch_name), 'head': head, 'removed_count': len(cleanup)})
history_path.write_text(json.dumps(history, indent=2) + '\n')
cleanup_summary = {'scope': cleanup_record['scope'], 'head': head, 'batches': history,
                   'total_removed_count': sum(batch['removed_count'] for batch in history),
                   'remaining_candidates': len(list((ROOT / '.git').rglob('._*')))}
(OUTER / 'final-postcommit-metadata-cleanup.json').write_text(json.dumps(cleanup_summary, indent=2) + '\n')

source_preflight = json.loads((OUTER / 'source-preflight.json').read_text())
for name, expected in source_preflight['sha256'].items():
    assert sha256(git('show', SOURCE + ':' + name)).hexdigest() == expected, name
approved = {}
for filename, key in [('publication-review-manifest.json', 'source_sha256'), ('review-final-manifest.json', 'source_hashes')]:
    approved.update(json.loads((OUTER / filename).read_text())[key])
for name, expected in approved.items():
    assert digest(ROOT / name) == expected == sha256(git('show', 'HEAD:' + name)).hexdigest(), name
artifacts = json.loads((OUTER / 'final-artifact-manifest.json').read_text())['sha256']
for name, expected in artifacts.items():
    assert digest(ROOT / name) == expected == sha256(git('show', ARTIFACT + ':' + name)).hexdigest(), name
    assert sha256(git('show', 'HEAD:' + name)).hexdigest() == expected, name
copied_count = 0
checkpoint = ROOT / 'docs/execution/section9-barrier-2026-10-31'
for filename in ('evidence-copy-manifest.json', 'strict-preview-evidence-copy-manifest.json', 'final-copy-manifest.json'):
    record = json.loads((checkpoint / filename).read_text())
    for row in record['files']:
        dest = Path(row['destination'])
        if not dest.is_absolute():
            dest = ROOT / dest
        assert digest(dest) == row['sha256'] and dest.stat().st_size == row['bytes'], str(dest)
        assert dest.read_bytes() == Path(row['source']).read_bytes(), str(dest)
        copied_count += 1
inventory = json.loads((ROOT / 'audit/2026-10-31/source-inventory.json').read_text())
originals = []
verified = 0
for original in inventory['repositories']:
    path = ROOT.parent / original['path']
    original_head = textgit('rev-parse', 'HEAD', cwd=path)
    assert original_head == original['head'] and not git('status', '--porcelain', cwd=path)
    ancestor = subprocess.run(['git', 'merge-base', '--is-ancestor', original_head, head], cwd=ROOT, env=ENV, capture_output=True)
    assert ancestor.returncode == 0 and not ancestor.stdout and not ancestor.stderr
    for row in original['files']:
        candidate = path / row['path']
        assert digest(candidate) == row['sha256'], str(candidate)
        verified += 1
    originals.append({'path': original['path'], 'head': original_head, 'worktree_clean': True,
                      'head_is_ancestor_of_final': True, 'tracked_sha256_values_verified': len(original['files'])})
assert verified == 953
original_archive = inventory['monograph_archive']
assert digest(ROOT.parent / original_archive['path']) == original_archive['sha256']
source_map = json.loads((ROOT / 'provenance/source-map.json').read_text())
archive = source_map['monograph_archive']
assert digest(ROOT / archive['path']) == archive['sha256'] == original_archive['sha256']
reference = ROOT / 'book/reference/polyhedral_volumes_and_geodesic_identities.pdf'
assert digest(reference) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'
unchanged = {}
for name in ('research/ipoly', 'book/reference', 'provenance', 'audit',
             'docs/execution/2026-10-31', 'docs/execution/numerical-correctness-2026-10-31',
             'docs/execution/section9-chapter-2026-10-31'):
    before = textgit('rev-parse', BASELINE + ':' + name)
    after = textgit('rev-parse', head + ':' + name)
    assert before == after, name
    unchanged[name] = before
unchanged_modules = {}
for path in sorted((ROOT / 'packages/volume-toolkit/ideal_poly_volume_toolkit').rglob('*.py')):
    if path.name.startswith('._') or path.name == 'angle_barrier.py':
        continue
    relative = str(path.relative_to(ROOT))
    assert digest(path) == sha256(git('show', BASELINE + ':' + relative)).hexdigest(), relative
    unchanged_modules[relative] = digest(path)
assert len(unchanged_modules) == 47
assert textgit('remote', '-v') == ''
final_docs = json.loads((OUTER / 'final-documentation-preflight.json').read_text())
for name, expected in final_docs['sha256'].items():
    assert digest(ROOT / name) == expected == sha256(git('show', 'HEAD:' + name)).hexdigest(), name
plain_command = ['git', 'fsck', '--full']
plain = subprocess.run(plain_command, cwd=ROOT, env=ENV, capture_output=True, text=True)
(OUTER / 'final-fsck-plain.stdout').write_text(plain.stdout)
(OUTER / 'final-fsck-plain.stderr').write_text(plain.stderr)
assert plain.returncode == 0 and not plain.stderr
preserved_dangling = []
for line in plain.stdout.splitlines():
    match = re.fullmatch(r'dangling (blob|tree|commit|tag) ([0-9a-f]{40})', line)
    assert match, line
    kind, object_id = match.groups()
    assert textgit('cat-file', '-t', object_id) == kind
    data = git('cat-file', kind, object_id)
    saved = OUTER / f'integrity-object-{object_id}.{kind}'
    if saved.exists():
        assert saved.read_bytes() == data
    else:
        saved.write_bytes(data)
    preserved_dangling.append({'git_object': object_id, 'type': kind, 'notice': line,
                              'preserved_path': str(saved), 'sha256': digest(saved), 'bytes': len(data)})
plain_record = {'command': plain_command, 'returncode': plain.returncode, 'stdout': plain.stdout, 'stderr': plain.stderr,
                'classification': 'Informational dangling-object notices are preserved separately; exit-zero with empty stderr is not corruption.',
                'preserved_objects': preserved_dangling, 'archive_refs_created': [], 'genuine_objects_deleted': []}
(OUTER / 'final-plain-fsck-record.json').write_text(json.dumps(plain_record, indent=2) + '\n')
fsck = subprocess.run(['git', 'fsck', '--full', '--no-dangling'], cwd=ROOT, env=ENV, capture_output=True, text=True)
(OUTER / 'final-fsck.stdout').write_text(fsck.stdout)
(OUTER / 'final-fsck.stderr').write_text(fsck.stderr)
assert fsck.returncode == 0 and not fsck.stdout and not fsck.stderr
assert not list((ROOT / '.git').rglob('._*'))
assert not git('status', '--porcelain') and not git('diff', '--cached', '--name-only')
assert textgit('rev-parse', 'HEAD') == head
assert digest(Path(__file__)) == digest(checkpoint / 'final-postcommit-verification.py')
receipt = {'status': 'final_postcommit_verification_passed', 'verified_at_utc': datetime.now(timezone.utc).isoformat(),
           'final_head': head, 'source_commit': SOURCE, 'artifact_commit': ARTIFACT, 'documentation_commit': head,
           'worktree_clean': True, 'index_clean': True, 'source_and_artifact_commits_are_direct_ancestors': True,
           'source_preflight_hashes_verified_at_source_commit': len(source_preflight['sha256']),
           'current_approved_source_sha256': approved,
           'canonical_artifact_count': len(artifacts), 'canonical_artifact_sha256': artifacts,
           'evidence_copies_verified': copied_count, 'original_repositories': originals,
           'original_tracked_files_verified': verified, 'original_archive_sha256': original_archive['sha256'],
           'supplied_reference_pdf_sha256': digest(reference), 'unchanged_trees_since_baseline': unchanged,
           'existing_maintained_python_modules_unchanged': unchanged_modules,
           'git_remotes': [], 'remote_operations': 'none', 'final_documentation_paths': final_docs['paths'],
           'metadata_cleanup': {'removed_count_in_final_batch': len(cleanup), 'total_removed_count': cleanup_summary['total_removed_count'], 'record': 'final-postcommit-metadata-cleanup.json',
                                'record_sha256': digest(OUTER / 'final-postcommit-metadata-cleanup.json'), 'remaining_candidates': 0},
           'git_fsck': {'command': ['git', 'fsck', '--full', '--no-dangling'], 'returncode': fsck.returncode, 'stdout': fsck.stdout, 'stderr': fsck.stderr},
           'plain_git_fsck': plain_record,
           'closeout_amendment_history_sha256': digest(OUTER / 'closeout-amendment-history.json'),
           'metadata_cleanup_history_sha256': digest(OUTER / 'metadata-cleanup-history.json'),
           'final_generation_checks_sha256': digest(OUTER / 'final-generation-checks.json'),
           'final_detached_replay_sha256': digest(OUTER / 'final-detached-replay.json'),
           'artifact_staging_verification_sha256': digest(OUTER / 'artifact-staging-verification.json'),
           'final_documentation_staging_sha256': digest(OUTER / 'final-documentation-staging.json'),
           'verification_script_sha256': digest(Path(__file__)),
           'limitations': ['Dense binary64 estimates are not floating-point or geometric certificates and imply no scaling law.',
                          'Full package run precedes the narrow fixed-domain reporting fix and retains known optional-dependency failures; final focused tests passed.',
                          'Installed-wheel validation used reviewed working-tree bytes and existing dependencies; no dependency-resolution or clean-source release-wheel claim.',
                          'Browser layout/interaction and external publication were not performed; no remote or push was created.',
                          'Section 9 computational increment is not a full-monograph proof audit.']}
(OUTER / 'final-postcommit-verification.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], 'source_commit': SOURCE, 'artifact_commit': ARTIFACT, 'final_head': head,
                  'canonical_artifact_count': len(artifacts), 'original_tracked_files_verified': verified,
                  'approved_current_source_count': len(approved), 'existing_unchanged_module_count': len(unchanged_modules),
                  'metadata_removed_count': cleanup_summary['total_removed_count'], 'fsck_empty_diagnostics': True,
                  'receipt_sha256': digest(OUTER / 'final-postcommit-verification.json')}, indent=2))
