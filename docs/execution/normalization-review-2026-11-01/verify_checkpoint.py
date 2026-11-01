#!/usr/bin/env python3
"""Verify the local checkpoint; no numerical replay, PDF build or mutation.

Receipts are written outside the checkout. Candidate mode requires the clean
source commit plus exactly the declared new artifact files. Final mode requires
their direct-child commit and a clean index/worktree. Original-repository
checks use this workspace's preserved source inventory and original trees.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT = Path(__file__).resolve().parent
OUT = ROOT.parent / 'execution/normalization-review-2026-11-01'
BASELINE = 'ad63b7ac9821040cb69e19c61bfbc46c68eff1a3'
SOURCE = '2a91e9f33b2b2e4ed3ae8ec9863870f91c22a83f'
MANIFEST = 'docs/execution/normalization-review-2026-11-01/candidate-artifact-manifest.json'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}


def digest(data):
    return sha256(data).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)


def read_json(path):
    return json.loads(path.read_text())


def expand(data, getter):
    return re.sub(rb'^\\input\{chapters/([^{}\n]+\.tex)\}\n',
                  lambda m: expand(getter('book/chapters/' + m[1].decode()), getter),
                  data, flags=re.M)


def protected_files(approved):
    entries = []
    for row in git('ls-tree', '-r', '-z', BASELINE).split(b'\0'):
        if row:
            fields, path = row.split(b'\t', 1)
            mode, kind, oid = fields.split()
            assert kind == b'blob'
            entries.append((mode, oid, path.decode()))
    assert len(entries) == 1719
    modified = {path for _, _, path in entries if path in approved}
    assert len(modified) == 6
    rows = [row for row in entries if row[2] not in modified]
    process = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT, env=ENV,
                             input=b'\n'.join(row[1] for row in rows)+b'\n',
                             capture_output=True, check=True)
    assert not process.stderr
    offset, lfs_count = 0, 0
    for mode, oid, path in rows:
        end = process.stdout.index(b'\n', offset)
        found, kind, length = process.stdout[offset:end].split()
        assert found == oid and kind == b'blob'
        start, size = end+1, int(length)
        blob = process.stdout[start:start+size]
        assert process.stdout[start+size:start+size+1] == b'\n'
        offset = start+size+1
        current = os.readlink(ROOT/path).encode() if mode == b'120000' else (ROOT/path).read_bytes()
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
            assert match and digest(current) == match[1].decode() and len(current) == int(match[2]), path
            lfs_count += 1
        else:
            assert current == blob, path
    assert offset == len(process.stdout)
    assert len(rows) == 1713 and lfs_count == 412
    return len(rows), lfs_count


def original_files():
    inventory = read_json(ROOT.parent/'audit/2026-10-31/source-inventory.json')
    count = 0
    for repository in inventory['repositories']:
        directory = ROOT.parent/repository['path']
        assert git('rev-parse', 'HEAD', cwd=directory).decode().strip() == repository['head']
        assert not git('status', '--porcelain', cwd=directory)
        subprocess.run(['git', 'merge-base', '--is-ancestor', repository['head'], SOURCE],
                       cwd=ROOT, env=ENV, check=True)
        for item in repository['files']:
            data = (directory/item['path']).read_bytes()
            assert digest(data) == item['sha256'] and len(data) == item['bytes'], item['path']
            count += 1
    assert count == 953
    archive = inventory['monograph_archive']
    data = (ROOT.parent/archive['path']).read_bytes()
    assert digest(data) == archive['sha256'] and len(data) == archive['bytes']
    assert digest((ROOT/'book/reference/polyhedral_volumes_and_geodesic_identities.pdf').read_bytes()) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'
    return count


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', action='store_true')
    args = parser.parse_args()
    head = git('rev-parse', 'HEAD').decode().strip()
    assert git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)
    assert git('rev-parse', SOURCE+'^').decode().strip() == BASELINE
    assert not git('remote').strip()
    manifest = read_json(ROOT/MANIFEST)
    assert manifest['source_commit'] == SOURCE and manifest['baseline_commit'] == BASELINE
    approved = read_json(CHECKPOINT/'integration-review/review-manifest.json')['approved_source_sha256']
    assert manifest['approved_source_sha256'] == approved and len(approved) == 21
    for path, expected in approved.items():
        assert digest((ROOT/path).read_bytes()) == expected
        assert digest(git('show', SOURCE+':'+path)) == expected
        assert digest(git('show', head+':'+path)) == expected
    artifact_paths = set(manifest['files']) | {MANIFEST}
    assert not git('diff', '--cached', '--name-only')
    if args.candidate:
        assert head == SOURCE
        assert not git('diff', '--name-only')
        assert set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == artifact_paths
    else:
        assert git('rev-parse', head+'^').decode().strip() == SOURCE
        assert not git('status', '--porcelain', '--untracked-files=all')
        assert set(git('diff-tree', '--no-commit-id', '--name-only', '-r', head).decode().splitlines()) == artifact_paths
    for path, row in manifest['files'].items():
        data = (ROOT/path).read_bytes()
        assert digest(data) == row['sha256'] and len(data) == row['bytes'], path
        if not args.candidate:
            assert git('show', head+':'+path) == data, path
    copies = read_json(CHECKPOINT/'evidence-copy-manifest.json')
    for row in copies['files']:
        current = (CHECKPOINT/row['path']).read_bytes()
        assert digest(current) == row['sha256'] and len(current) == row['bytes']
        assert current == (OUT/row['path']).read_bytes()
    result = read_json(ROOT/'artifacts/normalizations/result.json')
    reference = read_json(CHECKPOINT/'computation-review/replay.json')
    comparison = read_json(CHECKPOINT/'clean-source/scientific-comparison.json')
    assert comparison['excluded_json_paths'] == ['/generated_at_utc', '/elapsed_seconds', '/source']
    def scientific(data):
        return {k: v for k, v in data.items() if '/'+k not in comparison['excluded_json_paths']}
    assert scientific(result) == scientific(reference) and result['checks_passed'] is True
    assert result['source']['git_commit'] == SOURCE and result['source']['git_dirty'] is False
    assert result['source']['git_status_porcelain'] == []
    for row in result['source']['sources']:
        assert approved[row['path']] == row['sha256']
        assert digest(git('show', SOURCE+':'+row['path'])) == row['sha256']
    pdf = read_json(CHECKPOINT/'integration-review/review-manifest.json')['pdf']
    assert digest((ROOT/'artifacts/normalization-review-2026-11-01/monograph-working-draft.pdf').read_bytes()) == pdf['sha256']
    for path, expected in pdf['input_sha256'].items():
        assert digest((ROOT/path).read_bytes()) == digest(git('show', SOURCE+':'+path)) == expected
    main_path = 'book/polyhedral_volumes_and_geodesic_identities.tex'
    old = expand(git('show', BASELINE+':'+main_path), lambda path: git('show', BASELINE+':'+path))
    current = expand((ROOT/main_path).read_bytes(), lambda path: (ROOT/path).read_bytes())
    labels = re.findall(rb'\\label\{([^{}]+)\}', current)
    assert labels == re.findall(rb'\\label\{([^{}]+)\}', old)
    assert len(labels) == len(set(labels)) == 607
    claims = []
    for name in ('sections1-6.json', 'sections7-8.json'):
        ledger = read_json(ROOT/'book/claims'/name)
        for claim in ledger['claims']:
            assert all(label.encode() in labels for label in claim['labels'])
            claims.append(claim['id'])
    assert len(claims) == len(set(claims)) == 41
    protected, lfs_count = protected_files(approved)
    originals = original_files()
    docs = {ROOT/path for path in approved if path.endswith('.md')}
    docs.update(CHECKPOINT.rglob('*.md'))
    links = 0
    for path in docs:
        if path.name.startswith('._'):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            target = target.strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            assert (path.parent/unquote(parsed.path)).resolve().exists(), (str(path), target)
            links += 1
    fsck = subprocess.run(['git', 'fsck', '--full'], cwd=ROOT, env=ENV,
                          capture_output=True, text=True)
    assert fsck.returncode == 0 and not fsck.stderr, (fsck.stdout, fsck.stderr)
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'candidate' if args.candidate else 'postcommit', 'checks_passed': True,
        'baseline_commit': BASELINE, 'source_commit': SOURCE, 'head': head,
        'source_paths_verified': len(approved), 'artifact_paths_verified': len(artifact_paths),
        'copied_evidence_files_verified': len(copies['files']),
        'candidate_manifest_sha256': digest((ROOT/MANIFEST).read_bytes()),
        'result_sha256': digest((ROOT/'artifacts/normalizations/result.json').read_bytes()),
        'pdf_sha256': pdf['sha256'], 'pdf_inputs_verified': len(pdf['input_sha256']),
        'clean_source_result': True, 'scientific_comparison_equal': True,
        'labels_preserved': len(labels), 'claims': len(claims),
        'protected_baseline_files': protected, 'materialized_lfs_files': lfs_count,
        'original_files': originals, 'local_links_checked': links,
        'index_clean': True, 'worktree_clean': not args.candidate,
        'git_fsck_returncode': fsck.returncode, 'git_fsck_stdout': fsck.stdout,
        'git_fsck_stderr': fsck.stderr, 'git_metadata_cleanup_performed': False,
        'scope': 'Identity, provenance, preservation and local-link verification; no new numerical replay, PDF build, visual inspection or browser check.'
    }
    OUT.mkdir(exist_ok=True)
    receipt = OUT/('candidate-verification.json' if args.candidate else 'final-postcommit-verification.json')
    receipt.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('mode', 'checks_passed', 'head',
        'source_paths_verified', 'artifact_paths_verified', 'local_links_checked')}, indent=2))


if __name__ == '__main__':
    main()
