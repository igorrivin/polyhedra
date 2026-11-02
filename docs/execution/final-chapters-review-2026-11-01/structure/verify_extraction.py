"""Read-only independent verification of the frozen final-chapter extraction.

No extractor code is imported. Baseline source bytes are fetched anew from
the pinned Git tree. A line-walking recursion expands inputs independently
of the extractor's byte-range splice and regular-expression substitution.
All gates remain active with Python optimization enabled.
"""
from __future__ import annotations

from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = Path(__file__).resolve().parent
BASELINE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
ENTRY = 'book/main.tex'
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'


class VerificationError(RuntimeError):
    """The independent source-preservation check failed."""


def check(condition, message):
    if not condition:
        raise VerificationError(message)


def sha(data):
    return sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(
        ['git', *args], cwd=ROOT, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def independently_expand(reader, entry=ENTRY):
    files, edges = {}, []

    def walk(name, parents):
        check(name not in parents, f'cycle: {name}')
        raw = reader(name)
        check(name not in files or files[name] == raw, f'unstable source: {name}')
        files[name] = raw
        chunks = []
        for number, line in enumerate(raw.splitlines(keepends=True), 1):
            visible = re.sub(rb'(?<!\\)%[^\n]*', b'', line)
            if not re.search(rb'\\(?:input|include)\b', visible):
                chunks.append(line)
                continue
            match = re.fullmatch(rb'\\(input|include)\{([^{}\r\n]+)\}\n', line)
            check(match is not None, f'unsupported include line: {name}:{number}')
            target = PurePosixPath(match[2].decode('utf-8'))
            check(not target.is_absolute() and '..' not in target.parts and
                  not re.search(r'[\\#$~]', str(target)), f'unsafe include: {target}')
            if target.suffix != '.tex':
                target = target.with_suffix('.tex')
            child = str(PurePosixPath('book') / target)
            edges.append({'parent': name, 'line': number,
                          'input': match[2].decode(), 'child': child})
            chunks.append(walk(child, (*parents, name)))
        return b''.join(chunks)

    return walk(entry, ()), files, edges


def tokens(data):
    return {
        'labels': [m.decode() for m in re.findall(rb'\\label\{([^{}]+)\}', data)],
        'bibliography': [m.decode() for m in re.findall(
            rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', data)],
        'section_headers': [line.decode() for line in data.splitlines()
                            if line.startswith(b'\\section{')],
        'parts': [line.decode() for line in data.splitlines()
                  if line.startswith(b'\\monographpart{')],
    }


def main():
    report = json.loads((OUT / 'structure-manifest.json').read_text())
    check(report['baseline_commit'] == BASELINE, 'manifest baseline mismatch')
    check(git('rev-parse', 'HEAD').decode().strip() == BASELINE, 'HEAD changed')
    check(git('ls-files', '--stage', '-z') ==
          (OUT / 'baseline-git-index.zlist').read_bytes(), 'Git index changed')
    check(sha(git('ls-files', '--stage', '-z')) == report['baseline_index_sha256'],
          'Git index digest mismatch')
    for name, identity in report['evidence_files'].items():
        data = (OUT / name).read_bytes()
        check(len(data) == identity['bytes'] and sha(data) == identity['sha256'],
              f'evidence digest mismatch: {name}')
    baseline, git_graph, git_edges = independently_expand(
        lambda name: git('show', f'{BASELINE}:{name}'))
    extracted, frozen_graph, frozen_edges = independently_expand(
        lambda name: (OUT / 'extracted-source-graph' / name).read_bytes())
    current, live_graph, live_edges = independently_expand(
        lambda name: (ROOT / name).read_bytes())
    check(baseline == extracted, 'Git baseline/frozen recursive bytes differ')
    check(baseline == current, 'Git baseline/live recursive bytes differ')
    check(baseline == (OUT / 'expanded-entry-before.tex').read_bytes() ==
          (OUT / 'expanded-entry-after.tex').read_bytes(), 'expanded evidence mismatch')
    check(sha(baseline) == report['expanded_entry_before_sha256'] ==
          report['expanded_entry_after_sha256'], 'expanded digest mismatch')
    check(len(baseline) == report['expanded_entry_bytes'], 'expanded size mismatch')
    check(len(git_graph) == 26 and len(frozen_graph) == len(live_graph) == 36,
          'source graph size mismatch')
    check(len(git_edges) == 25 and len(frozen_edges) == len(live_edges) == 35,
          'include edge count mismatch')
    for graph, key, directory in (
            (git_graph, 'baseline_source_graph', 'baseline-source-graph'),
            (frozen_graph, 'extracted_source_graph', 'extracted-source-graph')):
        check(set(graph) == set(report[key]), f'graph membership mismatch: {key}')
        for name, data in graph.items():
            check(data == (OUT / directory / name).read_bytes(),
                  f'frozen graph byte mismatch: {name}')
            identity = report[key][name]
            check(len(data) == identity['bytes'] and sha(data) == identity['sha256'],
                  f'graph identity mismatch: {name}')
    check(frozen_graph == live_graph, 'live graph differs from frozen graph')
    edge_key = lambda edge: (edge['parent'], edge['line'], edge['child'], edge['input'])
    check(sorted(git_edges, key=edge_key) ==
          sorted(report['baseline_include_edges'], key=edge_key), 'baseline edge manifest')
    check(sorted(frozen_edges, key=edge_key) ==
          sorted(report['extracted_include_edges'], key=edge_key), 'extracted edge manifest')
    before_tokens, after_tokens = tokens(baseline), tokens(extracted)
    check(before_tokens == after_tokens, 'label/section/bibliography/part order changed')
    check(len(before_tokens['labels']) == len(set(before_tokens['labels'])) == 607,
          'label count/uniqueness mismatch')
    check(before_tokens['labels'] == report['label_order'], 'label order manifest')
    check(len(before_tokens['bibliography']) ==
          len(set(before_tokens['bibliography'])) == 129, 'bibliography count/uniqueness')
    check(before_tokens['bibliography'] == report['bibliography_order'],
          'bibliography order manifest')
    check(len(before_tokens['section_headers']) == 34 and len(before_tokens['parts']) == 7,
          'section/appendix/part count mismatch')
    main_before, main_after = git_graph[MAIN], frozen_graph[MAIN]
    check(tokens(main_before)['parts'] == tokens(main_after)['parts'],
          'part headings were moved or altered')
    check(main_before.count(b'\\appendix\n') == main_after.count(b'\\appendix\n') == 1,
          'appendix marker moved or altered')
    check(main_before.split(b'\\begin{thebibliography}', 1)[1] ==
          main_after.split(b'\\begin{thebibliography}', 1)[1], 'bibliography main bytes')
    check([line for line in main_before.splitlines() if line == b'\\clearpage'] ==
          [line for line in main_after.splitlines() if line == b'\\clearpage'],
          'boundary clearpage commands moved')
    check(not tokens(main_after)['section_headers'], 'unnested section remains in main')
    check(all(frozen_graph[name] == data for name, data in git_graph.items() if name != MAIN),
          'existing graph source changed')
    extraction_map = json.loads((OUT / 'extraction-map.json').read_text())
    check(extraction_map == report['extractions'] and len(extraction_map) == 10,
          'extraction map mismatch')
    for row in extraction_map:
        name = row['path']
        data = frozen_graph[name]
        check(main_before[row['baseline_start_byte_inclusive']:
                          row['baseline_end_byte_exclusive']] == data,
              f'Git range differs from extracted file: {name}')
        check(sha(data) == row['sha256'] and len(data) == row['bytes'],
              f'extraction map identity: {name}')
        check(tokens(data)['labels'] == row['labels'], f'extraction labels: {name}')
    inventory = json.loads((OUT / 'baseline-tracked-inventory.json').read_text())
    check(inventory['baseline_commit'] == BASELINE and len(inventory['files']) == 2273,
          'baseline inventory identity/count mismatch')
    tree_rows = []
    for line in git('ls-tree', '-r', '-z', BASELINE).split(b'\0'):
        if line:
            fields, name = line.split(b'\t', 1)
            mode, kind, oid = fields.split()
            check(kind == b'blob', 'nonblob tracked path')
            tree_rows.append((name.decode(), mode.decode(), oid.decode()))
    check(tree_rows == [(item['path'], item['git_mode'], item['git_blob'])
                        for item in inventory['files']], 'Git tree inventory mismatch')
    changed = []
    for item in inventory['files']:
        data = (ROOT / item['path']).read_bytes()
        if len(data) != item['materialized_bytes'] or sha(data) != item['materialized_sha256']:
            changed.append(item['path'])
    check(changed == [MAIN], f'out-of-scope tracked changes: {changed}')
    new_paths = [name.decode() for name in
                 git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if name]
    check(set(new_paths) == set(report['new_source_paths']) ==
          {row['path'] for row in extraction_map}, 'unexpected untracked paths')
    check(not git('diff', '--cached', '--name-only'), 'staged changes present')
    git('diff', '--check')
    manuscript_before, _, _ = independently_expand(
        lambda name: git('show', f'{BASELINE}:{name}'), MAIN)
    manuscript_after, _, _ = independently_expand(
        lambda name: (OUT / 'extracted-source-graph' / name).read_bytes(), MAIN)
    check(manuscript_before == manuscript_after and
          sha(manuscript_before) == report['expanded_manuscript_before_sha256'] ==
          report['expanded_manuscript_after_sha256'], 'expanded manuscript mismatch')
    print(json.dumps({
        'independent_verification_passed': True,
        'baseline_rebuilt_from_git': BASELINE,
        'expansion_algorithm': 'independent recursive line walk; no extractor imports',
        'python_optimization_does_not_remove_gates': True,
        'expanded_entry_sha256': sha(baseline),
        'expanded_entry_bytes': len(baseline),
        'expanded_manuscript_sha256': sha(manuscript_before),
        'baseline_source_files': len(git_graph),
        'extracted_source_files': len(frozen_graph),
        'baseline_include_edges': len(git_edges),
        'extracted_include_edges': len(frozen_edges),
        'labels_preserved_in_order': 607,
        'bibliography_keys_preserved_in_order': 129,
        'numbered_sections_preserved_in_order': 32,
        'appendices_preserved_in_order': ['A', 'B'],
        'part_headings_retained_in_main': 7,
        'baseline_tracked_paths_checked': 2273,
        'unchanged_baseline_tracked_paths': 2272,
        'changed_baseline_tracked_paths': changed,
        'new_chapter_paths': sorted(new_paths),
        'live_graph_matches_frozen_extraction': True,
        'head_and_index_unchanged': True,
        'scope': 'Source preservation only; no build, proof audit, numerical replay, '
                 'PDF verification, commit, or publication claim.',
    }, indent=2))


if __name__ == '__main__':
    main()
