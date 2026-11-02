"""Extract the remaining ten monograph units without changing source bytes.

Production gates deliberately use exceptions, including under python -O.
The separate verify_extraction.py independently expands pinned Git sources.
This script performs no build, mathematical revision, staging, or commit.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = Path(__file__).resolve().parent
BASELINE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
PYTHON = '/tmp/polyhedra-baseline-20261031/bin/python'
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'
ENTRY = 'book/main.tex'
INPUT = re.compile(rb'^\\(?:input|include)\{([^{}\r\n]+)\}\n', re.M)
SECTIONS = (
    ('10', '10-quantum-introduction.tex', 'sec:quantumintro',
     r'\section{A geometric introduction to the quantum constructions}',
     r'\section{Polyhedral degeneration and quantum volume asymptotics}'),
    ('11', '11-quantum-degeneration.tex', 'sec:quantumdegeneration',
     r'\section{Polyhedral degeneration and quantum volume asymptotics}',
     r'\input{chapters/12-quantum-boundary-measure.tex}'),
    ('17', '17-unfolding-constant-series.tex', 'sec:unfolding',
     r'\section{Unfolding and the problem of finding constant series}',
     r'\section{Figure-eight curves and simple lifts}'),
    ('18', '18-figure-eight-curves.tex', 'sec:figures',
     r'\section{Figure-eight curves and simple lifts}',
     r'\section{Cutting into pants and varying twists}'),
    ('19', '19-pants-twists.tex', 'sec:twists',
     r'\section{Cutting into pants and varying twists}',
     r'\section{An exact torus twist calculation and a constant orbit series}'),
    ('20', '20-torus-twist-series.tex', 'sec:exacttwist',
     r'\section{An exact torus twist calculation and a constant orbit series}',
     r'\section{Matching across cuffs: positions and directions}'),
    ('21', '21-cuff-matching.tex', 'sec:matching',
     r'\section{Matching across cuffs: positions and directions}',
     r'\section{Cusps, McShane gaps, and the orthospectrum}'),
    ('22', '22-cusps-orthospectrum.tex', 'sec:cusps',
     r'\section{Cusps, McShane gaps, and the orthospectrum}',
     '\\clearpage\n\\input{chapters/23-trace-coefficients.tex}'),
    ('32', '32-open-questions.tex', 'sec:questions',
     r'\section{Questions suggested by the calculations}',
     r'\appendix'),
    ('B', 'appendix-b-conventions.tex', 'app:conventions',
     r'\section{Conventions at a glance}',
     '\\clearpage\n\\begin{thebibliography}{999}'),
)


class GateError(RuntimeError):
    """A preservation or scope gate failed."""


def require(condition, message):
    if not condition:
        raise GateError(message)


def digest(data):
    return sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(
        ['git', *args], cwd=ROOT, env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                     allow_nan=False) + '\n', encoding='utf-8')


def labels(data):
    return [item.decode() for item in re.findall(rb'\\label\{([^{}]+)\}', data)]


def bibitems(data):
    return [item.decode() for item in re.findall(
        rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', data)]


def graph_manifest(graph):
    return {name: {'bytes': len(data), 'sha256': digest(data)}
            for name, data in graph.items()}


def source_graph():
    spec = importlib.util.spec_from_file_location(
        'canonical_source_graph', ROOT / 'site/build_section9.py')
    require(spec is not None and spec.loader is not None, 'source graph loader')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.source_graph(ROOT)


def expand(graph, entry=ENTRY, active=()):
    require(entry not in active, f'cyclic include: {entry}')
    require(entry in graph, f'missing graph entry: {entry}')
    data = graph[entry]
    uncommented = re.sub(rb'(?<!\\)%[^\n]*', b'', data)
    require(len(re.findall(rb'\\(?:input|include)\b', uncommented)) ==
            len(INPUT.findall(data)), f'nonstandalone include: {entry}')

    def replacement(match):
        name = Path(match[1].decode())
        require(not name.is_absolute() and '..' not in name.parts,
                f'external include: {name}')
        if name.suffix != '.tex':
            name = name.with_suffix('.tex')
        return expand(graph, str(Path('book') / name), (*active, entry))

    return INPUT.sub(replacement, data)


def graph_edges(graph):
    return [{'parent': name, 'line': data[:match.start()].count(b'\n') + 1,
             'input': match[1].decode(),
             'child': str(Path('book') / Path(match[1].decode()).with_suffix('.tex'))}
            for name, data in graph.items() for match in INPUT.finditer(data)]


def snapshot_graph(directory, graph):
    for name, data in graph.items():
        path = OUT / directory / name
        path.parent.mkdir(parents=True, exist_ok=True)
        require(not path.exists(), f'existing snapshot: {path}')
        path.write_bytes(data)


def baseline_inventory():
    """Compare every materialized tracked file with its Git blob or LFS OID."""
    tree = git('ls-tree', '-r', '-z', BASELINE)
    (OUT / 'baseline-git-tree.zlist').write_bytes(tree)
    rows = []
    for row in tree.split(b'\0'):
        if not row:
            continue
        fields, name = row.split(b'\t', 1)
        mode, kind, oid = fields.split()
        require(kind == b'blob' and mode != b'120000',
                f'unsupported tracked entry: {name!r}')
        rows.append((mode, oid, name.decode()))
    require(len(rows) == 2273, f'expected 2273 tracked files, found {len(rows)}')
    process = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'})
    require(process.stdin is not None and process.stdout is not None and
            process.stderr is not None, 'Git batch streams unavailable')
    inventory = []
    try:
        for mode, oid, name in rows:
            process.stdin.write(oid + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            require(len(header) == 3 and header[0] == oid and header[1] == b'blob',
                    f'Git batch identity mismatch: {name}')
            size = int(header[2])
            blob = process.stdout.read(size)
            require(len(blob) == size and process.stdout.read(1) == b'\n',
                    f'Git batch framing mismatch: {name}')
            path = ROOT / name
            require(path.is_file() and not path.is_symlink(),
                    f'missing/nonregular materialized path: {name}')
            data = path.read_bytes()
            record = {'path': name, 'git_mode': mode.decode(),
                      'git_blob': oid.decode(), 'git_blob_bytes': size,
                      'git_blob_sha256': digest(blob),
                      'materialized_bytes': len(data),
                      'materialized_sha256': digest(data)}
            if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                match = re.fullmatch(
                    rb'version https://git-lfs.github.com/spec/v1\n'
                    rb'oid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
                require(match is not None, f'unsupported LFS pointer: {name}')
                require(digest(data) == match[1].decode() and
                        len(data) == int(match[2]), f'LFS materialization: {name}')
                record.update(materialized_lfs=True, lfs_oid=match[1].decode(),
                              lfs_size=int(match[2]))
            else:
                require(data == blob, f'materialized/Git mismatch: {name}')
                record['materialized_lfs'] = False
            inventory.append(record)
        process.stdin.close()
        require(process.stdout.read() == b'', 'unexpected Git batch tail')
        stderr = process.stderr.read()
        require(process.wait() == 0 and not stderr, f'Git batch failure: {stderr!r}')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
    return inventory


def section_order(expanded):
    require(expanded.count(b'\\appendix\n') == 1, 'appendix marker count')
    body, appendices = expanded.split(b'\\appendix\n', 1)
    pattern = re.compile(rb'^\\section\{([^\n]+)\}\n\\label\{([^{}]+)\}', re.M)
    numbered, appendix_sections = list(pattern.finditer(body)), list(pattern.finditer(appendices))
    require(len(numbered) == 32 and len(appendix_sections) == 2,
            'expected 32 numbered sections and two appendices')
    result = []
    for text, matches, names in ((body, numbered, [str(n) for n in range(1, 33)]),
                                 (appendices, appendix_sections, ['A', 'B'])):
        for index, match in enumerate(matches):
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            result.append({'number': names[index], 'title': match[1].decode(),
                           'section_label': match[2].decode(),
                           'labels': labels(text[match.start():end])})
    return result


def main():
    require(len(sys.argv) == 1, 'run the independent verify_extraction.py to verify')
    require(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT),
            'wrong Git repository root')
    require(git('rev-parse', 'HEAD').decode().strip() == BASELINE, 'wrong baseline HEAD')
    status = git('status', '--porcelain=v1', '--untracked-files=all')
    require(not status, f'baseline must be clean: {status.decode()}')
    require(not (OUT / 'structure-manifest.json').exists(), 'extraction already recorded')
    index_before = git('ls-files', '--stage', '-z')
    (OUT / 'baseline-git-index.zlist').write_bytes(index_before)
    (OUT / 'baseline-git-status.txt').write_bytes(status)
    before = source_graph()
    require(len(before) == 26 and len(graph_edges(before)) == 25,
            'baseline graph must have 26 source files and 25 include edges')
    inventory = baseline_inventory()
    baseline = before[MAIN]
    require(all(data == git('show', f'{BASELINE}:{name}')
                for name, data in before.items()), 'baseline graph/Git mismatch')
    ranges, payloads, maps = [], {}, []
    for number, filename, label, start_marker, end_marker in SECTIONS:
        first, last = start_marker.encode(), end_marker.encode()
        require(baseline.count(first) == 1 and baseline.count(last) == 1,
                f'nonunique section boundary: {number}')
        start, end = baseline.index(first), baseline.index(last)
        require(start < end and (not ranges or ranges[-1][1] <= start),
                f'overlapping or reversed extraction: {number}')
        data = baseline[start:end]
        path = 'book/chapters/' + filename
        marker = ('\\input{chapters/' + filename + '}\n').encode()
        require(not (ROOT / path).exists(), f'new chapter already exists: {path}')
        require(labels(data) and labels(data)[0] == label,
                f'wrong first section label: {number}')
        require(len(re.findall(rb'^\\section\{', data, re.M)) == 1,
                f'extraction must contain one section: {number}')
        require(not re.search(rb'\\(?:monographpart|appendix|input|include)\b', data)
                and b'\\begin{thebibliography}' not in data,
                f'forbidden structural command in extraction: {number}')
        require(data.endswith(b'\n') and b'\r' not in data,
                f'noncanonical extraction line ending: {number}')
        ranges.append((start, end, marker))
        payloads[path] = data
        maps.append({'number': number, 'path': path, 'section_label': label,
                     'baseline_start_byte_inclusive': start,
                     'baseline_end_byte_exclusive': end,
                     'baseline_start_line': baseline[:start].count(b'\n') + 1,
                     'baseline_end_line': baseline[:end].count(b'\n'),
                     'start_marker': start_marker, 'end_marker_excluded': end_marker,
                     'bytes': len(data), 'sha256': digest(data), 'labels': labels(data),
                     'input_line': marker.decode(),
                     'terminal_newline_count': len(data) - len(data.rstrip(b'\n'))})
    chunks, cursor = [], 0
    for start, end, marker in ranges:
        chunks.extend((baseline[cursor:start], marker))
        cursor = end
    chunks.append(baseline[cursor:])
    extracted = b''.join(chunks)
    after = {**before, MAIN: extracted, **payloads}
    full_before, full_after = expand(before), expand(after)
    manuscript_before, manuscript_after = expand(before, MAIN), expand(after, MAIN)
    require(full_before == full_after and manuscript_before == manuscript_after,
            'recursive byte equivalence failed before writing')
    require(len(after) == 36 and len(graph_edges(after)) == 35,
            'extracted graph must have 36 source files and 35 include edges')
    label_order, bibliography_order = labels(full_before), bibitems(full_before)
    require(len(label_order) == len(set(label_order)) == 607, 'label count/uniqueness')
    require(len(bibliography_order) == len(set(bibliography_order)) == 129,
            'bibliography count/uniqueness')
    require(label_order == labels(full_after) and bibliography_order == bibitems(full_after),
            'label or bibliography order changed')
    sections = section_order(full_before)
    require(sections == section_order(full_after), 'section order changed')
    part_lines = re.findall(rb'^\\monographpart.*\n', baseline, re.M)
    require(len(part_lines) == 7 and part_lines ==
            re.findall(rb'^\\monographpart.*\n', extracted, re.M), 'part headings changed')
    require(re.findall(rb'^\\(?:appendix|clearpage)\b.*\n', baseline, re.M) ==
            re.findall(rb'^\\(?:appendix|clearpage)\b.*\n', extracted, re.M),
            'appendix marker or boundary page commands changed')
    require(baseline.split(b'\\begin{thebibliography}', 1)[1] ==
            extracted.split(b'\\begin{thebibliography}', 1)[1], 'bibliography bytes changed')
    require(not re.search(rb'^\\section\{', extracted, re.M),
            'a numbered section remains in main')
    snapshot_graph('baseline-source-graph', before)
    snapshot_graph('extracted-source-graph', after)
    (OUT / 'expanded-entry-before.tex').write_bytes(full_before)
    (OUT / 'expanded-entry-after.tex').write_bytes(full_after)
    write_json('baseline-tracked-inventory.json',
               {'baseline_commit': BASELINE, 'files': inventory})
    write_json('extraction-map.json', maps)
    write_json('source-order.json', {'label_order': label_order,
                                   'bibliography_order': bibliography_order,
                                   'sections': sections,
                                   'part_lines': [line.decode() for line in part_lines]})
    # All baseline evidence exists before the only eleven canonical writes.
    for name, data in payloads.items():
        (ROOT / name).write_bytes(data)
    (ROOT / MAIN).write_bytes(extracted)
    require(source_graph() == after, 'live graph differs from planned extraction')
    changed = [item['path'] for item in inventory
               if digest((ROOT / item['path']).read_bytes()) != item['materialized_sha256']]
    require(changed == [MAIN], f'out-of-scope tracked changes: {changed}')
    untracked = [name.decode() for name in
                 git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if name]
    require(set(untracked) == set(payloads), f'unexpected untracked files: {untracked}')
    require(git('ls-files', '--stage', '-z') == index_before, 'Git index changed')
    require(git('rev-parse', 'HEAD').decode().strip() == BASELINE, 'HEAD changed')
    diff_check = subprocess.run(['git', 'diff', '--check'], cwd=ROOT,
                                capture_output=True, text=True)
    require(diff_check.returncode == 0, diff_check.stdout + diff_check.stderr)
    main_diff = git('diff', '--no-ext-diff', '--', MAIN)
    (OUT / 'source-only-main.diff').write_bytes(main_diff)
    diff_parts = [main_diff]
    for name in payloads:
        new_file_diff = subprocess.run(
            ['git', 'diff', '--no-ext-diff', '--no-index', '--', '/dev/null', name],
            cwd=ROOT, capture_output=True)
        require(new_file_diff.returncode == 1 and not new_file_diff.stderr,
                f'new-file diff failure: {name}')
        diff_parts.append(new_file_diff.stdout)
    (OUT / 'source-only.diff').write_bytes(b''.join(diff_parts))
    (OUT / 'final-git-status.txt').write_bytes(
        git('status', '--porcelain=v1', '--untracked-files=all'))
    (OUT / 'chosen-files.txt').write_text('\n'.join([MAIN, *payloads]) + '\n')
    changes = {MAIN: {'status': 'modified', 'before_sha256': digest(baseline),
                      'after_sha256': digest(extracted), 'bytes': len(extracted)}}
    changes.update({name: {'status': 'new', 'before_sha256': None,
                           'after_sha256': digest(data), 'bytes': len(data)}
                    for name, data in payloads.items()})
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'operation': 'byte-preserving extraction before mathematical revision',
        'baseline_commit': BASELINE, 'canonical_root': str(ROOT),
        'entry_path': ENTRY, 'main_path': MAIN,
        'expanded_entry_before_sha256': digest(full_before),
        'expanded_entry_after_sha256': digest(full_after),
        'expanded_entry_bytes': len(full_after),
        'expanded_manuscript_before_sha256': digest(manuscript_before),
        'expanded_manuscript_after_sha256': digest(manuscript_after),
        'expanded_manuscript_bytes': len(manuscript_after),
        'exact_recursive_byte_equivalence': True,
        'label_order': label_order, 'label_count': 607, 'unique_label_count': 607,
        'bibliography_order': bibliography_order, 'bibliography_count': 129,
        'section_order': sections, 'extractions': maps, 'source_changes': changes,
        'baseline_source_graph': graph_manifest(before),
        'extracted_source_graph': graph_manifest(after),
        'baseline_include_edges': graph_edges(before),
        'extracted_include_edges': graph_edges(after),
        'baseline_source_file_count': len(before), 'extracted_source_file_count': len(after),
        'baseline_include_edge_count': 25, 'extracted_include_edge_count': 35,
        'baseline_inventory_files': len(inventory),
        'baseline_materialized_lfs_files': sum(item['materialized_lfs'] for item in inventory),
        'unchanged_prior_tracked_files': len(inventory) - 1,
        'changed_prior_tracked_paths': changed, 'new_source_paths': sorted(untracked),
        'all_existing_chapters_unchanged': True,
        'part_headings_identical_and_retained_in_main': True,
        'appendix_marker_and_boundary_page_commands_retained_in_main': True,
        'bibliography_identical_and_retained_in_main': True,
        'git_diff_check_passed': True, 'index_unchanged': True, 'head_unchanged': True,
        'baseline_index_sha256': digest(index_before),
        'command': PYTHON + ' ' + str(OUT / 'extract_chapters.py'),
        'independent_verification_command': PYTHON + ' -O ' + str(OUT / 'verify_extraction.py'),
        'scope': 'Source structure and preservation only. No mathematical edits, builds, '
                 'numerical replay, staging, commits, network operations, uploads, or '
                 'canonical generated artifacts. Existing external originals were not written.',
    }
    evidence_names = ['extract_chapters.py', 'verify_extraction.py',
                      'baseline-tracked-inventory.json', 'baseline-git-tree.zlist',
                      'baseline-git-index.zlist', 'baseline-git-status.txt',
                      'expanded-entry-before.tex', 'expanded-entry-after.tex',
                      'extraction-map.json', 'source-order.json', 'chosen-files.txt',
                      'source-only-main.diff', 'source-only.diff', 'final-git-status.txt']
    report['evidence_files'] = {name: {'bytes': (OUT / name).stat().st_size,
                                       'sha256': digest((OUT / name).read_bytes())}
                                for name in evidence_names}
    write_json('structure-manifest.json', report)
    print(json.dumps({key: report[key] for key in (
        'baseline_commit', 'expanded_entry_before_sha256', 'expanded_entry_after_sha256',
        'expanded_entry_bytes', 'label_count', 'bibliography_count',
        'baseline_source_file_count', 'extracted_source_file_count',
        'baseline_inventory_files', 'baseline_materialized_lfs_files',
        'unchanged_prior_tracked_files', 'changed_prior_tracked_paths',
        'new_source_paths')}, indent=2))


if __name__ == '__main__':
    main()
