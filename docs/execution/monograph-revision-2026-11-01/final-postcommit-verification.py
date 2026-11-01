#!/usr/bin/env python3
"""Verify this local revision checkpoint and its protected source identities.

The postcommit receipt and any Git metadata-cleanup records are written to the
outer execution directory. The candidate mode performs no Git metadata cleanup.
This is artifact verification, not a fresh numerical replay or PDF build.
"""
from argparse import ArgumentParser
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[3]
CHECKPOINT = ROOT / 'docs/execution/monograph-revision-2026-11-01'
OUT = ROOT.parent / 'execution/monograph-revision-2026-11-01'
BASELINE = 'df952174e55f08a52596d912d9713a9d1e116313'
SOURCE = 'cf34fcbcd0ee867a2dee974d9c952238bc5c6ce6'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)

def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def scientific(data, name):
    value = deepcopy(data)
    del value['provenance']
    if name == 'airy':
        del value['runtime_seconds']
    else:
        del value['elapsed_seconds']
        for row in value['surfaces']:
            del row['elapsed_seconds']
    return value

def identity(path):
    assert not path.is_symlink(), str(path)
    if not path.exists():
        return {'kind': 'absent'}
    if path.is_file():
        return {'kind': 'file', 'sha256': digest(path)}
    entries = []
    for child in sorted(path.rglob('*')):
        relative = child.relative_to(path)
        if any(part.startswith('._') for part in relative.parts):
            continue
        assert not child.is_symlink(), str(child)
        entries.append([str(relative), 'file', digest(child)] if child.is_file()
                       else [str(relative), 'directory'])
    return {'kind': 'directory', 'genuine_entries': len(entries),
            'genuine_tree_sha256': sha256(json.dumps(entries, separators=(',', ':')).encode()).hexdigest()}

def clean_git_metadata(head):
    entries = []
    for path in sorted((ROOT / '.git').rglob('._*')):
        assert path.is_file() and not path.is_symlink(), str(path)
        data = path.read_bytes()
        assert len(data) >= 26 and data[:8] == bytes.fromhex('0005160700020000'), str(path)
        count = int.from_bytes(data[24:26], 'big')
        assert 26 + 12*count <= len(data), str(path)
        for index in range(count):
            offset = 26 + 12*index
            start = int.from_bytes(data[offset+4:offset+8], 'big')
            size = int.from_bytes(data[offset+8:offset+12], 'big')
            assert start + size <= len(data), str(path)
        sibling = path.with_name(path.name[2:])
        entries.append({'path': str(path.relative_to(ROOT)), 'bytes': len(data),
                        'sha256': sha256(data).hexdigest(), 'header_hex': data[:26].hex(),
                        'entry_count': count, 'sibling': str(sibling.relative_to(ROOT)),
                        'sibling_before': identity(sibling)})
    for row in entries:
        (ROOT / row['path']).unlink()
    for row in entries:
        row['sibling_after'] = identity(ROOT / row['sibling'])
        assert row['sibling_before'] == row['sibling_after']
    history_path = OUT / 'git-metadata-cleanup-history.json'
    history = json.loads(history_path.read_text()) if history_path.exists() else []
    for row in history:
        assert digest(OUT / row['record']) == row['sha256']
    name = f'git-metadata-cleanup-{len(history)+1:03d}.json'
    assert not (OUT / name).exists()
    write_json(OUT / name, {'head': head, 'entries': entries, 'removed_count': len(entries),
        'scope': 'Only header/table-verified AppleDouble files under canonical .git; genuine sibling identities unchanged.'})
    history.append({'record': name, 'sha256': digest(OUT / name), 'removed_count': len(entries)})
    write_json(history_path, history)
    return history

def walk_paths(value, key=''):
    if isinstance(value, dict):
        for name, item in value.items():
            yield from walk_paths(item, name)
    elif isinstance(value, list):
        for item in value:
            yield from walk_paths(item, key)
    elif isinstance(value, str) and (key.endswith('_path') or key.endswith('_paths') or key == 'chapter_source'):
        yield value

def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', action='store_true')
    args = parser.parse_args()
    head = git('rev-parse', 'HEAD').decode().strip()
    assert git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)
    assert git('rev-parse', SOURCE+'^').decode().strip() == BASELINE
    assert not git('remote').strip()
    if args.candidate:
        assert head == SOURCE
    else:
        assert git('rev-parse', head+'^').decode().strip() == SOURCE
        assert not git('status', '--porcelain=v1', '--untracked-files=all')
        assert not git('diff', '--cached', '--name-only')
    approved = json.loads((CHECKPOINT/'integration-review/integration-review-manifest.json').read_text())['source_sha256']
    assert len(approved) == 16
    for path, expected in approved.items():
        assert digest(ROOT/path) == expected
        assert sha256(git('show', SOURCE+':'+path)).hexdigest() == expected
        assert sha256(git('show', head+':'+path)).hexdigest() == expected
    candidate = json.loads((CHECKPOINT/'candidate-artifact-manifest.json').read_text())
    assert candidate['source_commit'] == SOURCE and candidate['baseline_commit'] == BASELINE
    assert candidate['approved_source_sha256'] == approved
    for path, row in candidate['artifacts'].items():
        assert digest(ROOT/path) == row['sha256'] and (ROOT/path).stat().st_size == row['bytes']
    for name, path in [('airy','artifacts/section15/checks.json'), ('torus','artifacts/section30/result.json')]:
        current = json.loads((ROOT/path).read_text())
        previous = json.loads((OUT/f'scientific-review/{name}-replay.json').read_text())
        assert current['provenance']['source_commit'] == SOURCE
        assert current['provenance']['repository_dirty_at_start'] is False
        assert current['provenance']['git_status_porcelain_at_start'] == []
        assert scientific(current,name) == scientific(previous,name)
        for source, expected in current['provenance']['source_sha256'].items():
            assert digest(ROOT/source) == expected == sha256(git('show',SOURCE+':'+source)).hexdigest()
    for path, expected in candidate['pdf_tex_input_sha256'].items():
        assert digest(ROOT/path) == expected == sha256(git('show',SOURCE+':'+path)).hexdigest()
    copy_manifest = CHECKPOINT/'evidence-copy-manifest.json'
    assert digest(copy_manifest) == candidate['evidence_copy_manifest_sha256']
    copies = json.loads(copy_manifest.read_text())
    for row in copies['files']:
        assert digest(CHECKPOINT/row['path']) == row['sha256']
        assert (CHECKPOINT/row['path']).read_bytes() == (OUT/row['path']).read_bytes()
    preserved = 0
    allowed_changes = {'book/polyhedral_volumes_and_geodesic_identities.tex', 'book/README.md', 'book/computational-status.md'}
    inventory = json.loads((CHECKPOINT/'structure/baseline-tracked-inventory.json').read_text())
    for row in inventory['files']:
        if row['path'] not in allowed_changes:
            assert digest(ROOT/row['path']) == row['sha256']
            assert (ROOT/row['path']).stat().st_size == row['bytes']
            preserved += 1
    assert preserved == 1053
    original = json.loads((ROOT.parent/'audit/2026-10-31/source-inventory.json').read_text())
    original_count, original_heads = 0, {}
    for repo in original['repositories']:
        path = ROOT.parent/repo['path']
        assert git('rev-parse','HEAD',cwd=path).decode().strip() == repo['head']
        assert not git('status','--porcelain=v1',cwd=path)
        subprocess.run(['git','merge-base','--is-ancestor',repo['head'],head],cwd=ROOT,env=ENV,check=True)
        for row in repo['files']:
            assert digest(path/row['path']) == row['sha256']
            assert (path/row['path']).stat().st_size == row['bytes']
            original_count += 1
        original_heads[repo['path']] = repo['head']
    assert original_count == 953
    archive = original['monograph_archive']
    assert digest(ROOT.parent/archive['path']) == archive['sha256']
    reference = ROOT/'book/reference/polyhedral_volumes_and_geodesic_identities.pdf'
    assert digest(reference) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'
    shared = json.loads((CHECKPOINT/'shared-docs/shared-docs-manifest.json').read_text())
    links = []
    for source in shared['source_sha256']:
        for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', (ROOT/source).read_text()):
            parts = urlsplit(match.group(1).split(' ',1)[0].strip('<>'))
            if not parts.scheme and parts.path:
                target = ((ROOT/source).parent/unquote(parts.path)).resolve()
                assert target.exists(), (source,str(target))
                links.append({'source':source,'target':str(target)})
    assert len(links) == 109
    ledger_paths = set()
    for source in ('book/claims/section15.json','book/claims/section30.json'):
        for path in walk_paths(json.loads((ROOT/source).read_text())):
            assert (ROOT/path).exists(), (source,path)
            ledger_paths.add(path)
    cleanup, fsck = [], []
    if not args.candidate:
        staging = json.loads((OUT/'final-staging-manifest.json').read_text())
        for path, expected in staging['sha256'].items():
            assert digest(ROOT/path) == expected
            assert sha256(git('show',head+':'+path)).hexdigest() == expected
        assert set(git('diff','--name-only',SOURCE,head).decode().splitlines()) == set(staging['sha256'])
        cleanup = clean_git_metadata(head)
        for suffix in ([], ['--no-dangling']):
            argv = ['git','fsck','--full',*suffix]
            result = subprocess.run(argv,cwd=ROOT,env=ENV,capture_output=True,text=True)
            assert result.returncode == 0 and not result.stderr, (argv,result.stdout,result.stderr)
            if suffix:
                assert not result.stdout
            else:
                assert all(re.fullmatch(r'dangling (?:blob|tree|commit|tag) [0-9a-f]{40}',line)
                           for line in result.stdout.splitlines())
            fsck.append({'argv':argv,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
        assert not list((ROOT/'.git').rglob('._*'))
        assert not git('status','--porcelain=v1','--untracked-files=all')
        assert not git('diff','--cached','--name-only')
        assert git('rev-parse','HEAD').decode().strip() == head
    receipt = {'generated_at_utc':datetime.now(timezone.utc).isoformat(),
        'mode':'candidate' if args.candidate else 'final_postcommit', 'all_checks_passed':True,
        'baseline':BASELINE,'source_commit':SOURCE,'head':head,
        'approved_source_files':len(approved),'artifact_sha256':{p:r['sha256'] for p,r in candidate['artifacts'].items()},
        'scientific_values_equal_reviewed_replays':True,'both_results_record_clean_source':True,
        'pdf_matches_reviewed_precommit_bytes_and_committed_inputs':True,'pdf_rebuilt_after_commit':False,
        'evidence_copies_verified':len(copies['files']),'protected_baseline_files':preserved,
        'original_tracked_files_verified':original_count,'original_repository_heads':original_heads,
        'original_archive_sha256':archive['sha256'],'reference_pdf_sha256':digest(reference),
        'shared_document_links_resolved':len(links),'ledger_local_paths_resolved':sorted(ledger_paths),
        'worktree_and_index_clean':not args.candidate,'git_metadata_cleanup_history':cleanup,'git_fsck':fsck,
        'no_remote_operations':True,'scope':'Verification of recorded artifacts and source identities; no new replay, PDF build, browser check or publication.'}
    name = 'candidate-verification.json' if args.candidate else 'final-postcommit-verification.json'
    write_json(OUT/name,receipt)
    print(json.dumps({'mode':receipt['mode'],'head':head,'passed':True,'receipt':str(OUT/name)}))

if __name__ == '__main__':
    main()
