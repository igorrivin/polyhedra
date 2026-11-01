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
OUT = ROOT.parent / 'execution/quantum-surgery-review-2026-11-01'
BASELINE = 'bf260eaab047d9047602ece652e5a7e43625d3f6'
SOURCE = '514bc30b0d86a0a38b2ede1cb9dfb261a6b2995a'
MANIFEST = 'docs/execution/quantum-surgery-review-2026-11-01/candidate-artifact-manifest.json'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}



def require(condition, message="Checkpoint invariant failed"):
    """Keep every verification gate active under Python optimization."""
    if not condition:
        raise RuntimeError(message)

def digest(data):
    return sha256(data).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)


def read_json(path):
    return json.loads(path.read_text())


def row_hashes(rows):
    result = {row['path']: row['sha256'] for row in rows}
    require(len(result) == len(rows), 'Invariant failed: len(result) == len(rows)')
    return result


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
            require(kind == b'blob', "Invariant failed: kind == b'blob'")
            entries.append((mode, oid, path.decode()))
    require(len(entries) == 1782, 'Invariant failed: len(entries) == 1782')
    modified = {path for _, _, path in entries if path in approved}
    require(len(modified) == 6, 'Invariant failed: len(modified) == 6')
    rows = [row for row in entries if row[2] not in modified]
    process = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT, env=ENV,
                             input=b'\n'.join(row[1] for row in rows)+b'\n',
                             capture_output=True, check=True)
    require(not process.stderr, 'Invariant failed: not process.stderr')
    offset, lfs_count = 0, 0
    for mode, oid, path in rows:
        end = process.stdout.index(b'\n', offset)
        found, kind, length = process.stdout[offset:end].split()
        require(found == oid and kind == b'blob', "Invariant failed: found == oid and kind == b'blob'")
        start, size = end+1, int(length)
        blob = process.stdout[start:start+size]
        require(process.stdout[start+size:start+size+1] == b'\n', "Invariant failed: process.stdout[start+size:start+size+1] == b'\\n'")
        offset = start+size+1
        current = os.readlink(ROOT/path).encode() if mode == b'120000' else (ROOT/path).read_bytes()
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
            require(match and digest(current) == match[1].decode() and len(current) == int(match[2]), path)
            lfs_count += 1
        else:
            require(current == blob, path)
    require(offset == len(process.stdout), 'Invariant failed: offset == len(process.stdout)')
    require(len(rows) == 1776 and lfs_count == 412, 'Invariant failed: len(rows) == 1776 and lfs_count == 412')
    return len(rows), lfs_count


def original_files():
    inventory = read_json(ROOT.parent/'audit/2026-10-31/source-inventory.json')
    count = 0
    for repository in inventory['repositories']:
        directory = ROOT.parent/repository['path']
        require(git('rev-parse', 'HEAD', cwd=directory).decode().strip() == repository['head'], "Invariant failed: git('rev-parse', 'HEAD', cwd=directory).decode().strip() == repository['head']")
        require(not git('status', '--porcelain', cwd=directory), "Invariant failed: not git('status', '--porcelain', cwd=directory)")
        subprocess.run(['git', 'merge-base', '--is-ancestor', repository['head'], SOURCE],
                       cwd=ROOT, env=ENV, check=True)
        for item in repository['files']:
            data = (directory/item['path']).read_bytes()
            require(digest(data) == item['sha256'] and len(data) == item['bytes'], item['path'])
            count += 1
    require(count == 953, 'Invariant failed: count == 953')
    archive = inventory['monograph_archive']
    data = (ROOT.parent/archive['path']).read_bytes()
    require(digest(data) == archive['sha256'] and len(data) == archive['bytes'], "Invariant failed: digest(data) == archive['sha256'] and len(data) == archive['bytes']")
    require(digest((ROOT/'book/reference/polyhedral_volumes_and_geodesic_identities.pdf').read_bytes()) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5', "Invariant failed: digest((ROOT/'book/reference/polyhedral_volumes_and_geodesic_identities.pdf').read_bytes()) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'")
    return count


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', action='store_true')
    parser.add_argument('--receipt', type=Path,
                        help='new receipt path under the outer execution directory')
    args = parser.parse_args()
    head = git('rev-parse', 'HEAD').decode().strip()
    require(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT), "Invariant failed: git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)")
    require(git('rev-parse', SOURCE+'^').decode().strip() == BASELINE, "Invariant failed: git('rev-parse', SOURCE+'^').decode().strip() == BASELINE")
    require(git('rev-list', '--parents', '-n', '1', SOURCE).decode().split() == [SOURCE, BASELINE], 'Source must have exactly the baseline as its sole parent')
    require(not git('remote').strip(), "Invariant failed: not git('remote').strip()")
    manifest = read_json(ROOT/MANIFEST)
    require(manifest['source_commit'] == SOURCE and manifest['baseline_commit'] == BASELINE, "Invariant failed: manifest['source_commit'] == SOURCE and manifest['baseline_commit'] == BASELINE")
    integration = read_json(CHECKPOINT/'integration-review/approved-source-manifest.json')
    require(integration['decision'] == 'approved_for_bounded_local_integration_and_pdf_review', "Invariant failed: integration['decision'] == 'approved_for_bounded_local_integration_and_pdf_review'")
    require(integration['baseline_commit'] == BASELINE, "Invariant failed: integration['baseline_commit'] == BASELINE")
    approved = row_hashes(integration['files'])
    require(manifest['approved_source_sha256'] == approved and len(approved) == 20, "Invariant failed: manifest['approved_source_sha256'] == approved and len(approved) == 20")
    final20 = read_json(CHECKPOINT/'computation/nonfinite-guard-correction/source-20-path-manifest.json')
    require(row_hashes(final20['files']) == approved, "Invariant failed: row_hashes(final20['files']) == approved")
    require(digest((CHECKPOINT/'computation/nonfinite-guard-correction/source-20-path-manifest.json').read_bytes()) == '8cc7e0195650fd5e7994f2b56eb86550755f61377f851d5847002e033fe4afed', "Invariant failed: digest((CHECKPOINT/'computation/nonfinite-guard-correction/source-20-path-manifest.json').read_bytes()) == '8cc7e0195650fd5e7994f2b56eb86550755f61377f851d5847002e033fe4afed'")
    require(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', SOURCE).decode().splitlines()) == set(approved), "Invariant failed: set(git('diff-tree', '--no-commit-id', '--name-only', '-r', SOURCE).decode().splitlines()) == set(approved)")
    baseline_paths = set(git('ls-tree', '-r', '--name-only', BASELINE).decode().splitlines())
    require(len(baseline_paths) == 1782, 'Invariant failed: len(baseline_paths) == 1782')
    require(len(set(approved) & baseline_paths) == 6 and len(set(approved)-baseline_paths) == 14, 'Invariant failed: len(set(approved) & baseline_paths) == 6 and len(set(approved)-baseline_paths) == 14')
    for row in integration['independent_approvals'].values():
        data = (CHECKPOINT/row['path']).read_bytes()
        require(digest(data) == row['sha256'] and len(data) == row['bytes'], "Invariant failed: digest(data) == row['sha256'] and len(data) == row['bytes']")
    review_manifest = read_json(CHECKPOINT/'integration-review/review-manifest.json')
    require(review_manifest['source_approval']['sha256'] == digest((CHECKPOINT/'integration-review/approved-source-manifest.json').read_bytes()), "Invariant failed: review_manifest['source_approval']['sha256'] == digest((CHECKPOINT/'integration-review/approved-source-manifest.json').read_bytes())")
    require(review_manifest['independent_approvals'] == integration['independent_approvals'], "Invariant failed: review_manifest['independent_approvals'] == integration['independent_approvals']")
    quantum = read_json(CHECKPOINT/'quantum-review/approved-hashes.json')
    require(quantum['status'] == 'independently_approved_with_explicit_scope_limits', "Invariant failed: quantum['status'] == 'independently_approved_with_explicit_scope_limits'")
    require({p:r['sha256'] for p,r in quantum['files'].items()} == {p:approved[p] for p in quantum['files']}, "Invariant failed: {p:r['sha256'] for p,r in quantum['files'].items()} == {p:approved[p] for p in quantum['files']}")
    surgery = read_json(CHECKPOINT/'surgery-review/approved-file-hashes.json')
    require(surgery['decision'] == 'approved_with_explicit_scope_limits', "Invariant failed: surgery['decision'] == 'approved_with_explicit_scope_limits'")
    require(surgery['canonical_files'] == {p:approved[p] for p in surgery['canonical_files']}, "Invariant failed: surgery['canonical_files'] == {p:approved[p] for p in surgery['canonical_files']}")
    code = read_json(CHECKPOINT/'computation-review/approval-manifest.json')
    require(code['verdict'] == 'approved_after_nonfinite_matrix_guard_correction', "Invariant failed: code['verdict'] == 'approved_after_nonfinite_matrix_guard_correction'")
    runtime = row_hashes(code['approved_source_files']+code['chapter_and_main_at_replay'])
    require(len(runtime) == 13 and runtime == {p:approved[p] for p in runtime}, 'Invariant failed: len(runtime) == 13 and runtime == {p:approved[p] for p in runtime}')
    checkpoint = read_json(CHECKPOINT/'checkpoint/source-checkpoint.json')
    require(checkpoint['source_commit'] == SOURCE and checkpoint['baseline_commit'] == BASELINE, "Invariant failed: checkpoint['source_commit'] == SOURCE and checkpoint['baseline_commit'] == BASELINE")
    require(checkpoint['approved_source_sha256'] == approved, "Invariant failed: checkpoint['approved_source_sha256'] == approved")
    stage = read_json(CHECKPOINT/'checkpoint/source-stage.json')
    require(set(stage['staged_paths']) == set(approved) and stage['staged_source_sha256'] == approved, "Invariant failed: set(stage['staged_paths']) == set(approved) and stage['staged_source_sha256'] == approved")
    exceptions = read_json(CHECKPOINT/'checkpoint/source-whitespace-exceptions.json')['exceptions']
    require(len(exceptions) == 4, 'Invariant failed: len(exceptions) == 4')
    for row in exceptions:
        data = (ROOT/row['path']).read_bytes()
        n = len(data)-len(data.rstrip(b'\n'))
        require(row['sha256'] == approved[row['path']] == digest(data), "Invariant failed: row['sha256'] == approved[row['path']] == digest(data)")
        require(n == row['approved_terminal_newlines'] == row['original_terminal_newlines'], "Invariant failed: n == row['approved_terminal_newlines'] == row['original_terminal_newlines']")
        require(row['terminal_bytes_hex'] == (b'\n'*n).hex(), "Invariant failed: row['terminal_bytes_hex'] == (b'\\n'*n).hex()")
        require(all(line == b'' for line in data.splitlines()[row['line']-1:]), "Invariant failed: all(line == b'' for line in data.splitlines()[row['line']-1:])")
    for path, expected in approved.items():
        require(digest((ROOT/path).read_bytes()) == expected, 'Invariant failed: digest((ROOT/path).read_bytes()) == expected')
        require(digest(git('show', SOURCE+':'+path)) == expected, "Invariant failed: digest(git('show', SOURCE+':'+path)) == expected")
        require(digest(git('show', head+':'+path)) == expected, "Invariant failed: digest(git('show', head+':'+path)) == expected")
    artifact_paths = set(manifest['files']) | {MANIFEST}
    require(MANIFEST not in manifest['files'], "Invariant failed: MANIFEST not in manifest['files']")
    require(all(not any(part.startswith('._') for part in Path(path).parts) for path in artifact_paths), "Invariant failed: all(not any(part.startswith('._') for part in Path(path).parts) for path in artifact_paths)")
    actual_artifacts = {str(path.relative_to(ROOT)) for path in CHECKPOINT.rglob('*')
                        if path.is_file() and not path.name.startswith('._')}
    actual_artifacts.update({'artifacts/quantum_surgery/result.json',
                            'artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf'})
    require(actual_artifacts == artifact_paths, 'Invariant failed: actual_artifacts == artifact_paths')
    require(not git('diff', '--cached', '--name-only'), "Invariant failed: not git('diff', '--cached', '--name-only')")
    if args.candidate:
        require(head == SOURCE, 'Invariant failed: head == SOURCE')
        require(not git('diff', '--name-only'), "Invariant failed: not git('diff', '--name-only')")
        require(set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == artifact_paths, "Invariant failed: set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == artifact_paths")
    else:
        require(git('rev-parse', head+'^').decode().strip() == SOURCE, "Invariant failed: git('rev-parse', head+'^').decode().strip() == SOURCE")
        require(git('rev-list', '--parents', '-n', '1', head).decode().split() == [head, SOURCE], 'Artifact commit must have exactly source as its sole parent')
        require(not git('status', '--porcelain', '--untracked-files=all'), "Invariant failed: not git('status', '--porcelain', '--untracked-files=all')")
        require(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', head).decode().splitlines()) == artifact_paths, "Invariant failed: set(git('diff-tree', '--no-commit-id', '--name-only', '-r', head).decode().splitlines()) == artifact_paths")
    for path, row in manifest['files'].items():
        data = (ROOT/path).read_bytes()
        require(digest(data) == row['sha256'] and len(data) == row['bytes'], path)
        if not args.candidate:
            require(git('show', head+':'+path) == data, path)
    copies = read_json(CHECKPOINT/'evidence-copy-manifest.json')
    for row in copies['files']:
        current = (CHECKPOINT/row['path']).read_bytes()
        require(digest(current) == row['sha256'] and len(current) == row['bytes'], "Invariant failed: digest(current) == row['sha256'] and len(current) == row['bytes']")
        require(current == (OUT/row['path']).read_bytes(), "Invariant failed: current == (OUT/row['path']).read_bytes()")
    require(copies['source_commit'] == SOURCE, "Invariant failed: copies['source_commit'] == SOURCE")
    for path,row in copies['artifacts'].items():
        data = (ROOT/path).read_bytes()
        require(len(data) == row['bytes'] and digest(data) == row['sha256'], "Invariant failed: len(data) == row['bytes'] and digest(data) == row['sha256']")
        require(data == (OUT/row['outer_source']).read_bytes(), "Invariant failed: data == (OUT/row['outer_source']).read_bytes()")
    result = read_json(ROOT/'artifacts/quantum_surgery/result.json')
    reference_path = CHECKPOINT/'computation-review/replay-result-final.json'
    reference = read_json(reference_path)
    comparison = read_json(CHECKPOINT/'clean-source/scientific-comparison.json')
    require(comparison['excluded_json_paths'] == ['/generated_at_utc', '/elapsed_seconds', '/source', '/source_at_completion'], "Invariant failed: comparison['excluded_json_paths'] == ['/generated_at_utc', '/elapsed_seconds', '/source', '/source_at_completion']")
    def scientific(data):
        return {k: v for k, v in data.items() if '/'+k not in comparison['excluded_json_paths']}
    require(scientific(result) == scientific(reference) and result['checks_passed'] is True, "Invariant failed: scientific(result) == scientific(reference) and result['checks_passed'] is True")
    require(comparison['source_commit'] == SOURCE and comparison['scientific_fields_equal'] is True, "Invariant failed: comparison['source_commit'] == SOURCE and comparison['scientific_fields_equal'] is True")
    require(comparison['clean_result_sha256'] == digest((ROOT/'artifacts/quantum_surgery/result.json').read_bytes()), "Invariant failed: comparison['clean_result_sha256'] == digest((ROOT/'artifacts/quantum_surgery/result.json').read_bytes())")
    require(comparison['independent_replay_path'] == 'computation-review/replay-result-final.json', "Invariant failed: comparison['independent_replay_path'] == 'computation-review/replay-result-final.json'")
    require(comparison['independent_replay_sha256'] == digest(reference_path.read_bytes()), "Invariant failed: comparison['independent_replay_sha256'] == digest(reference_path.read_bytes())")
    require(code['final_independent_replay']['sha256'] == digest(reference_path.read_bytes()), "Invariant failed: code['final_independent_replay']['sha256'] == digest(reference_path.read_bytes())")
    require(result['source'] == result['source_at_completion'], "Invariant failed: result['source'] == result['source_at_completion']")
    for name in ('source','source_at_completion'):
        state = result[name]
        require(state['git_commit'] == SOURCE and state['git_dirty'] is False, "Invariant failed: state['git_commit'] == SOURCE and state['git_dirty'] is False")
        require(state['git_status_porcelain'] == [], "Invariant failed: state['git_status_porcelain'] == []")
        require(row_hashes(state['sources']) == runtime and len(state['sources']) == 13, "Invariant failed: row_hashes(state['sources']) == runtime and len(state['sources']) == 13")
        for row in state['sources']:
            data = git('show', SOURCE+':'+row['path'])
            require(approved[row['path']] == row['sha256'] == digest(data), "Invariant failed: approved[row['path']] == row['sha256'] == digest(data)")
            require(row['bytes'] == len(data), "Invariant failed: row['bytes'] == len(data)")
    command = read_json(CHECKPOINT/'clean-source/run-command.json')
    require(command['returncode'] == 0 and command['clean_before'] and command['clean_after'], "Invariant failed: command['returncode'] == 0 and command['clean_before'] and command['clean_after']")
    require(command['source_commit'] == SOURCE, "Invariant failed: command['source_commit'] == SOURCE")
    pdf = integration['pdf']
    pdf_inputs = integration['pdf_inputs']
    require(len(pdf_inputs) == 18 and pdf['pages'] == 186, "Invariant failed: len(pdf_inputs) == 18 and pdf['pages'] == 186")
    require(digest((ROOT/'artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf').read_bytes()) == pdf['sha256'], "Invariant failed: digest((ROOT/'artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf').read_bytes()) == pdf['sha256']")
    require(pdf_inputs == read_json(CHECKPOINT/'integration-review/pdf-inputs.json')['sha256'], "Invariant failed: pdf_inputs == read_json(CHECKPOINT/'integration-review/pdf-inputs.json')['sha256']")
    for path, expected in pdf_inputs.items():
        require(digest((ROOT/path).read_bytes()) == digest(git('show', SOURCE+':'+path)) == expected, "Invariant failed: digest((ROOT/path).read_bytes()) == digest(git('show', SOURCE+':'+path)) == expected")
    visual = read_json(CHECKPOINT/'integration-review/visual-review.json')
    require(visual['pdf_sha256'] == pdf['sha256'] and not visual['findings'], "Invariant failed: visual['pdf_sha256'] == pdf['sha256'] and not visual['findings']")
    require(visual['inspected_page_count'] == len(visual['inspected_pages']) == 56, "Invariant failed: visual['inspected_page_count'] == len(visual['inspected_pages']) == 56")
    main_path = 'book/polyhedral_volumes_and_geodesic_identities.tex'
    old = expand(git('show', BASELINE+':'+main_path), lambda path: git('show', BASELINE+':'+path))
    current = expand((ROOT/main_path).read_bytes(), lambda path: (ROOT/path).read_bytes())
    labels = re.findall(rb'\\label\{([^{}]+)\}', current)
    require(labels == re.findall(rb'\\label\{([^{}]+)\}', old), "Invariant failed: labels == re.findall(rb'\\\\label\\{([^{}]+)\\}', old)")
    require(len(labels) == len(set(labels)) == 607, 'Invariant failed: len(labels) == len(set(labels)) == 607')
    claims = []
    for name in ('sections12-14.json', 'section16.json'):
        ledger = read_json(ROOT/'book/claims'/name)
        for claim in ledger['claims']:
            require(all(label.encode() in labels for label in claim['labels']), "Invariant failed: all(label.encode() in labels for label in claim['labels'])")
            claims.append(claim['id'])
    require(len(claims) == len(set(claims)) == 56, 'Invariant failed: len(claims) == len(set(claims)) == 56')
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
            require((path.parent/unquote(parsed.path)).resolve().exists(), (str(path), target))
            links += 1
    fsck = subprocess.run(['git', 'fsck', '--full'], cwd=ROOT, env=ENV,
                          capture_output=True, text=True)
    require(fsck.returncode == 0 and not fsck.stderr, (fsck.stdout, fsck.stderr))
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'candidate' if args.candidate else 'postcommit', 'checks_passed': True,
        'baseline_commit': BASELINE, 'source_commit': SOURCE, 'head': head,
        'source_paths_verified': len(approved), 'artifact_paths_verified': len(artifact_paths),
        'copied_evidence_files_verified': len(copies['files']),
        'candidate_manifest_sha256': digest((ROOT/MANIFEST).read_bytes()),
        'result_sha256': digest((ROOT/'artifacts/quantum_surgery/result.json').read_bytes()),
        'pdf_sha256': pdf['sha256'], 'pdf_inputs_verified': len(pdf_inputs),
        'pdf_pages': pdf['pages'], 'visually_reviewed_pages': 56,
        'runtime_source_hashes_verified': len(runtime), 'clean_source_states_verified': 2,
        'clean_source_result': True, 'scientific_comparison_equal': True,
        'labels_preserved': len(labels), 'claims': len(claims),
        'protected_baseline_files': protected, 'materialized_lfs_files': lfs_count,
        'original_files': originals, 'local_links_checked': links,
        'index_clean': True, 'worktree_clean': not args.candidate,
        'git_fsck_returncode': fsck.returncode, 'git_fsck_stdout': fsck.stdout,
        'git_fsck_stderr': fsck.stderr, 'git_metadata_cleanup_by_this_verifier': False,
        'scope': 'Identity, provenance, preservation and local-link verification; no new numerical replay, PDF build, visual inspection or browser check.'
    }
    OUT.mkdir(exist_ok=True)
    receipt = args.receipt or OUT/('candidate-verification.json' if args.candidate else 'final-postcommit-verification.json')
    require(receipt.resolve().is_relative_to(OUT.resolve()), 'Receipt must remain under the outer execution directory')
    if args.receipt is None and receipt.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = receipt.with_name(receipt.stem+'-'+stamp+receipt.suffix)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x') as handle:
        handle.write(json.dumps(report, indent=2)+'\n')
    print(json.dumps({key: report[key] for key in ('mode', 'checks_passed', 'head',
        'source_paths_verified', 'artifact_paths_verified', 'local_links_checked')}, indent=2))
    print('Receipt: '+str(receipt))


if __name__ == '__main__':
    main()
