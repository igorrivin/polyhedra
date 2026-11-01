#!/usr/bin/env python3
"""Record the explicitly authorized source-only checkpoint, outside the repository."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent / 'integration-review/revision-v2'
MANIFEST = REVIEW / 'approved-source-manifest.json'
PARENT_APPROVAL = OUT.parent / 'parent-source-approval.json'
BASE = '9c8b61790aaa674902b9d60e80122c318a578bcc'
MANIFEST_HASH = '0fe9b4a314efdd5d1d8c33f448b49d36d998200bcad2d09a0dd12ede5cbf7a2d'
PDF_HASH = '60708f3059284875e611eec6f910fd1086fd74880d84a1f4fc51f6bd356583a3'
KNOWN_DANGLING = {'dba78d2f1770521c3cfaef91091f1c296ec57abd', '4c37b26b85df0662fbc6ab71661713083ac3a7c1'}
COMMAND_LOG = OUT / 'commands.jsonl'
PHASE = sys.argv[1]
COMMAND_OUTPUTS = OUT / 'command-outputs'
COMMAND_OUTPUTS.mkdir(exist_ok=True)
SEQUENCE = len(COMMAND_LOG.read_text().splitlines()) if COMMAND_LOG.exists() else 0
WHITESPACE_CHECKS = []


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ensure(condition, message):
    if not condition:
        raise RuntimeError(message)


def save(name, value):
    path = OUT / name
    ensure(not path.exists(), f'Refusing to overwrite receipt: {path}')
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def run(args, allowed=(0,)):
    global SEQUENCE
    SEQUENCE += 1
    started = utc()
    result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    prefix = f'{SEQUENCE:04d}-{PHASE}'
    stdout_path = COMMAND_OUTPUTS / f'{prefix}.stdout'
    stderr_path = COMMAND_OUTPUTS / f'{prefix}.stderr'
    stdout_path.write_bytes(result.stdout)
    stderr_path.write_bytes(result.stderr)
    record = {
        'sequence': SEQUENCE, 'phase': PHASE, 'started_utc': started,
        'finished_utc': utc(), 'cwd': str(ROOT), 'argv': args,
        'returncode': result.returncode,
        'stdout': {'path': str(stdout_path.relative_to(OUT)), 'bytes': len(result.stdout), 'sha256': sha(result.stdout)},
        'stderr': {'path': str(stderr_path.relative_to(OUT)), 'bytes': len(result.stderr), 'sha256': sha(result.stderr)},
    }
    with COMMAND_LOG.open('a') as log:
        log.write(json.dumps(record, sort_keys=True) + '\n')
    ensure(result.returncode in allowed,
           f'Command failed ({result.returncode}): {args!r}\n{result.stderr.decode(errors="replace")}')
    return result.stdout


def git(*args):
    return run(['git', *args])


def names(raw):
    return [part.decode() for part in raw.split(b'\0') if part]


def approved():
    manifest_bytes = MANIFEST.read_bytes()
    ensure(sha(manifest_bytes) == MANIFEST_HASH, 'Approval manifest hash mismatch')
    manifest = json.loads(manifest_bytes)
    parent_bytes = PARENT_APPROVAL.read_bytes()
    parent = json.loads(parent_bytes)
    rows = manifest['approved_sources']
    paths = [row['path'] for row in rows]
    ensure(manifest['approved'] is True and manifest['open_findings'] == [], 'Independent approval is not clear')
    ensure(manifest['baseline_commit'] == BASE, 'Wrong approved baseline')
    ensure(len(rows) == 33 and len(set(paths)) == 33 and paths == sorted(paths), 'Wrong approved source set')
    ensure(manifest['approved_source_count'] == 33 and manifest['modified_existing_count'] == 8 and manifest['new_count'] == 25, 'Wrong approved source counts')
    expected_checks = {'manifest_hash', 'approved', 'baseline_head', 'exact33path_scope', 'reviewed_pdf_hash', *paths}
    ensure(parent['all_passed'] is True and set(parent['checks']) == expected_checks and all(v is True for v in parent['checks'].values()), 'Parent approval checks differ or failed')
    ensure(parent['approved_source_manifest_sha256'] == MANIFEST_HASH, 'Parent approved another manifest')
    source_set = [{'path': row['path'], 'sha256': row['sha256']} for row in rows]
    ensure(sha(json.dumps(source_set, sort_keys=True, separators=(',', ':')).encode()) == manifest['approved_source_set_sha256'], 'Source-set digest mismatch')
    receipt_checks = []
    for receipt in manifest['receipts']:
        receipt_path = REVIEW / receipt['path']
        digest = sha(receipt_path.read_bytes())
        ensure(digest == receipt['sha256'], f'Independent receipt hash mismatch: {receipt_path}')
        receipt_checks.append({'path': str(receipt_path), 'sha256': digest, 'passed': True})
    pdf_path = Path(manifest['reviewed_pdf']['path'])
    ensure(not pdf_path.is_relative_to(ROOT), 'Reviewed PDF must remain outside canonical repository')
    ensure(manifest['reviewed_pdf']['sha256'] == PDF_HASH and sha(pdf_path.read_bytes()) == PDF_HASH, 'Approved PDF hash mismatch')
    ensure(manifest['reviewed_pdf']['pages'] == 191, 'Approved PDF page metadata differs')
    return manifest, {
        'manifest_path': str(MANIFEST), 'manifest_sha256': MANIFEST_HASH,
        'parent_approval_path': str(PARENT_APPROVAL), 'parent_approval_sha256': sha(parent_bytes),
        'parent_checks_count': len(parent['checks']), 'parent_checks_all_passed': True,
        'independent_receipts': receipt_checks,
        'reviewed_pdf': {'path': str(pdf_path), 'sha256': PDF_HASH, 'pages_per_approval': 191, 'copied': False},
    }


def worktree_bytes(manifest):
    checks = []
    for row in manifest['approved_sources']:
        path = ROOT / row['path']
        ensure(path.resolve().is_relative_to(ROOT) and not path.is_symlink() and path.is_file(), f'Unsafe approved path: {path}')
        data = path.read_bytes()
        ensure(sha(data) == row['sha256'] and len(data) == row['bytes'], f'Worktree bytes differ: {path}')
        checks.append({'path': row['path'], 'sha256': sha(data), 'bytes': len(data), 'passed': True})
    return checks


def head(expected):
    ensure(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT), 'Wrong repository root')
    actual = git('rev-parse', 'HEAD').decode().strip()
    ensure(actual == expected, f'Unexpected HEAD {actual}')
    return actual


def check_status(manifest, staged):
    raw = git('status', '--porcelain=v1', '-z', '--untracked-files=all')
    observed = {}
    for record in names(raw):
        ensure(len(record) >= 4, f'Malformed Git status: {record!r}')
        observed[record[3:]] = record[:2]
    expected = {row['path']: (('M ' if staged else ' M') if row['status'] == 'modified' else ('A ' if staged else '??')) for row in manifest['approved_sources']}
    ensure(observed == expected, f'Wrong status scope: {observed!r}')
    return observed


def whitespace_check(*args):
    exception_path = OUT / 'root-whitespace-exception.json'
    exception = json.loads(exception_path.read_text())
    ensure(exception['approved'] is True and exception['authority'] == '/root'
           and exception['approved_source_manifest_sha256'] == MANIFEST_HASH,
           'Root whitespace exception is absent or refers to another source set')
    raw = run(['git', *args], allowed=(0, 2))
    diagnostics = raw.decode().splitlines()
    ensure(diagnostics == exception['diagnostics'], 'Whitespace findings differ from the five approved exceptions')
    existing = run(['git', 'config', '--get', 'core.whitespace'], allowed=(0, 1)).decode().strip()
    adjusted = existing + ',-blank-at-eof' if existing else '-blank-at-eof'
    clean = git('-c', 'core.whitespace=' + adjusted, *args)
    ensure(clean == b'', 'Other whitespace diagnostics remain')
    record = {'original_command': ['git', *args], 'original_diagnostics': diagnostics,
              'exception_path': str(exception_path), 'exception_sha256': sha(exception_path.read_bytes()),
              'root_decision': exception['decision'], 'root_reason': exception['reason'],
              'prior_core_whitespace': existing or None, 'adjusted_core_whitespace': adjusted,
              'adjusted_check_returncode': 0, 'adjusted_check_output': '',
              'only_blank_at_eof_disabled': True}
    WHITESPACE_CHECKS.append(record)
    return record


def index_bytes(manifest):
    expected = {row['path']: ('M' if row['status'] == 'modified' else 'A') for row in manifest['approved_sources']}
    raw = names(git('diff', '--cached', '--name-status', '-z', '--no-renames'))
    ensure(len(raw) % 2 == 0, 'Malformed staged names')
    actual = dict(zip(raw[1::2], raw[::2]))
    ensure(actual == expected, 'Staged paths or statuses differ from approval')
    whitespace_check('diff', '--cached', '--check')
    checks = []
    for row in manifest['approved_sources']:
        blob = git('cat-file', 'blob', ':' + row['path'])
        materialized = (ROOT / row['path']).read_bytes()
        ensure(blob == materialized and sha(blob) == row['sha256'] and len(blob) == row['bytes'], f'Staged bytes differ: {row["path"]}')
        checks.append({'path': row['path'], 'sha256': sha(blob), 'bytes': len(blob), 'materialized_identical': True})
    return checks


def fsck():
    output = git('fsck', '--full').decode().splitlines()
    permitted = {f'dangling blob {value}' for value in KNOWN_DANGLING}
    ensure(set(output) <= permitted, f'Unexpected fsck output: {output!r}')
    recovery_path = OUT / 'git-sidecar-recovery/removal.json'
    recovery = ({'path': str(recovery_path), 'sha256': sha(recovery_path.read_bytes()),
                 'details': json.loads(recovery_path.read_text())} if recovery_path.exists() else None)
    return {'returncode': 0, 'output': output, 'unexpected_findings': [],
            'cleanup_performed': recovery is not None, 'sidecar_recovery': recovery}


def main():
    manifest, approval = approved()
    rows = manifest['approved_sources']
    paths = [row['path'] for row in rows]
    result = {'phase': PHASE, 'started_utc': utc(), 'baseline_commit': BASE, 'approval': approval}
    if PHASE == 'preflight':
        head(BASE)
        result['worktree_files'] = worktree_bytes(manifest)
        result['status'] = check_status(manifest, False)
        ensure(not git('diff', '--cached', '--name-only', '-z'), 'Unexpected staged changes')
        git('diff', '--check')
        tracked = names(git('ls-files', '-z'))
        ensure(len(tracked) == 1914, 'Wrong baseline tracked count')
        result['baseline_tracked_count'] = len(tracked)
        result['baseline_files'] = []
        for row in rows:
            if row['status'] == 'modified':
                blob = git('cat-file', 'blob', BASE + ':' + row['path'])
                ensure(sha(blob) == row['baseline_sha256'], f'Wrong baseline bytes: {row["path"]}')
                result['baseline_files'].append({'path': row['path'], 'sha256': sha(blob)})
            else:
                ensure(row['status'] == 'new' and row['baseline_sha256'] is None and row['path'] not in tracked, f'New source already tracked: {row["path"]}')
        hooks_config = run(['git', 'config', '--get', 'core.hooksPath'], allowed=(0, 1)).decode().strip()
        hooks_dir = Path(hooks_config) if hooks_config else ROOT / '.git/hooks'
        if not hooks_dir.is_absolute():
            hooks_dir = ROOT / hooks_dir
        active_hooks = sorted(str(path) for path in hooks_dir.iterdir() if path.is_file() and not path.name.endswith('.sample')) if hooks_dir.exists() else []
        inspected_hooks = {
            'post-checkout': '8d606e58cce98604696a4abcf3ae1ebde6f9f31ac72bb0d44e2444cc39f26030',
            'post-commit': 'f3eb4d1f62924c09d481a0563a84b158c66eb2feb3431cfdb3e6760aab4d661d',
            'post-merge': 'cecb594e8fa65831654fc95e96db9f1249e09c52810c6fbb2b428280aac22158',
            'pre-push': 'a52d0510d0f8c75e27852156ec6f7791f0d8ed65fc58fcc368dd1de0a60a1d74',
        }
        ensure({Path(path).name: sha(Path(path).read_bytes()) for path in active_hooks} == inspected_hooks,
               'Git hooks differ from the four inspected standard Git LFS wrappers')
        hook_help = git('lfs', 'post-commit', '-h').decode()
        result['hooks'] = {'configured_path': hooks_config or None,
                           'active_hooks': [{'path': path, 'sha256': sha(Path(path).read_bytes()),
                                             'contents': Path(path).read_text()} for path in active_hooks],
                           'post_commit_local_help': hook_help,
                           'inspection': 'Only standard Git LFS hooks; the post-commit hook adjusts lockable file permissions locally.'}
        result['fsck'] = fsck()
    elif PHASE == 'stage':
        ensure(json.loads((OUT / 'preflight.json').read_text())['passed'] is True, 'Preflight receipt absent')
        head(BASE)
        worktree_bytes(manifest)
        if git('diff', '--cached', '--name-only', '-z'):
            check_status(manifest, True)
        else:
            check_status(manifest, False)
            git('add', '--', *paths)
        result['status'] = check_status(manifest, True)
        result['staged_files'] = index_bytes(manifest)
        result['diff_stat'] = git('diff', '--cached', '--stat').decode()
        result['diff_numstat'] = git('diff', '--cached', '--numstat').decode()
        result['staged_tree'] = git('write-tree').decode().strip()
        print(result['diff_stat'])
    elif PHASE == 'commit':
        staged = json.loads((OUT / 'stage.json').read_text())
        ensure(staged['passed'] is True, 'Staging receipt absent')
        head(BASE)
        worktree_bytes(manifest)
        check_status(manifest, True)
        index_bytes(manifest)
        ensure(git('write-tree').decode().strip() == staged['staged_tree'], 'Staged tree changed since review')
        result['commit_output'] = git('commit', '-m', 'Review counting and mixing chapters and add reproducible diagnostics').decode()
        result['source_commit'] = git('rev-parse', 'HEAD').decode().strip()
        print(result['commit_output'])
    elif PHASE == 'verify':
        committed = json.loads((OUT / 'commit.json').read_text())
        ensure(committed['passed'] is True, 'Commit receipt absent')
        source_commit = committed['source_commit']
        head(source_commit)
        ensure(git('rev-parse', 'HEAD^').decode().strip() == BASE, 'Wrong source commit parent')
        expected = {row['path']: ('M' if row['status'] == 'modified' else 'A') for row in rows}
        changed = names(git('diff-tree', '--no-commit-id', '--name-status', '-r', '-z', '--no-renames', source_commit))
        ensure(len(changed) % 2 == 0 and dict(zip(changed[1::2], changed[::2])) == expected, 'Committed path scope differs')
        git('show', '--format=fuller', '--stat', source_commit)
        whitespace_check('diff-tree', '--check', source_commit + '^', source_commit)
        committed_files = []
        for row in rows:
            blob = git('cat-file', 'blob', source_commit + ':' + row['path'])
            ensure(sha(blob) == row['sha256'] and len(blob) == row['bytes'] and blob == (ROOT / row['path']).read_bytes(), f'Committed bytes differ: {row["path"]}')
            committed_files.append({'path': row['path'], 'sha256': sha(blob), 'bytes': len(blob), 'materialized_identical': True})
        ensure(git('status', '--porcelain=v1', '-z', '--untracked-files=all') == b'', 'Worktree not clean')
        ensure(git('diff', '--cached', '--name-only', '-z') == b'', 'Index not clean')
        tracked = names(git('ls-files', '-z'))
        ensure(len(tracked) == 1939, 'Wrong final tracked count')
        result.update({'source_commit': source_commit, 'source_tree': git('rev-parse', 'HEAD^{tree}').decode().strip(),
                       'parent_commit': BASE, 'changed_path_count': 33, 'modified_existing_count': 8,
                       'new_count': 25, 'tracked_path_count': len(tracked), 'git_status_porcelain': '',
                       'index_clean': True, 'committed_files': committed_files, 'fsck': fsck(),
                       'source_set_sha256': manifest['approved_source_set_sha256'],
                       'numerical_replay_performed': False, 'artifact_generation_performed': False,
                       'canonical_docs_generated': False, 'remote_operation_performed': False})
    else:
        raise RuntimeError(f'Unknown phase: {PHASE}')
    result['whitespace_checks'] = WHITESPACE_CHECKS
    result['finished_utc'] = utc()
    result['passed'] = True
    save(PHASE + '.json', result)
    if PHASE == 'verify':
        result['receipt_files'] = [
            {'path': str((OUT / name).relative_to(OUT.parent)), 'sha256': sha((OUT / name).read_bytes())}
            for name in ('checkpoint.py', 'preflight.json', 'stage.json', 'commit.json', 'verify.json', 'commands.jsonl',
                         'staged-byte-inspection.json', 'root-whitespace-exception.json',
                         'recover_reported_sidecars.py', 'git-sidecar-recovery/inspection.json',
                         'git-sidecar-recovery/removal.json')]
        save('source-checkpoint.json', result)
    print(json.dumps({'phase': PHASE, 'passed': True, 'source_commit': result.get('source_commit'), 'receipt': str(OUT / (PHASE + '.json'))}))


try:
    main()
except Exception as exc:
    failure = {'phase': PHASE, 'failed_utc': utc(), 'passed': False, 'error': str(exc)}
    failure_path = OUT / f'{PHASE}-failure-{SEQUENCE:04d}.json'
    failure_path.write_text(json.dumps(failure, indent=2, sort_keys=True) + '\n')
    raise
