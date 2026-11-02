"""Independent, read-only review of the pinned eleven-path source extraction.

No implementation/evidence modules are imported. The expected write set and
baseline are pinned here; complete baseline content comes from Git objects.
Only stdout is written. Run with Python -B (and optionally -O).
"""
from __future__ import annotations

import ast
from hashlib import sha256
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EVIDENCE = ROOT.parent / 'execution/final-chapters-review-2026-11-01/structure'
BASE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
MANIFEST_SHA = '36192abd41a5a214cb1565fe7a0daf7f7e35c07ed5e9a39ff3b92adc3e794f75'
ENTRY = 'book/main.tex'
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'
NEW = tuple('book/chapters/' + name for name in (
    '10-quantum-introduction.tex', '11-quantum-degeneration.tex',
    '17-unfolding-constant-series.tex', '18-figure-eight-curves.tex',
    '19-pants-twists.tex', '20-torus-twist-series.tex', '21-cuff-matching.tex',
    '22-cusps-orthospectrum.tex', '32-open-questions.tex',
    'appendix-b-conventions.tex',
))
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS='0', PYTHONDONTWRITEBYTECODE='1')


class ReviewFailure(RuntimeError):
    pass


def need(value, message):
    if not value:
        raise ReviewFailure(message)


def sha(data):
    return sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, env=ENV)


def read_local(base, name):
    rel = PurePosixPath(name)
    need(not rel.is_absolute() and '..' not in rel.parts, 'unsafe local path')
    path = base
    for part in rel.parts:
        path = path / part
        need(not path.is_symlink(), f'symlink path component: {path}')
    need(path.resolve().is_relative_to(base.resolve()), f'path escape: {path}')
    need(stat.S_ISREG(path.stat().st_mode), f'nonregular path: {path}')
    return path.read_bytes()


def commands(data):
    """Lex literal TeX controls, skipping escaped symbols and comments."""
    pos = 0
    while pos < len(data):
        byte = data[pos]
        if byte == 37:  # unescaped percent starts a comment
            stop = data.find(b'\n', pos)
            pos = len(data) if stop == -1 else stop + 1
        elif byte == 92:
            start = pos
            pos += 1
            stop = pos
            while stop < len(data) and (65 <= data[stop] <= 90 or 97 <= data[stop] <= 122):
                stop += 1
            if stop == pos:
                pos += 1  # escaped nonletter, including backslash or percent
            else:
                yield start, stop, data[pos:stop]
                pos = stop
        else:
            pos += 1


def inputs(data):
    found = []
    for start, stop, word in commands(data):
        if word not in (b'input', b'include'):
            continue
        need(word == b'input', 'unexpected include command with page semantics')
        end = data.find(b'\n', stop)
        need(end >= 0 and (start == 0 or data[start - 1] == 10),
             'include must occupy a whole line with a final newline')
        arg = data[stop:end]
        need(arg.startswith(b'{') and arg.endswith(b'}'), 'nonliteral input')
        target = arg[1:-1].decode('ascii')
        need(re.fullmatch(r'[A-Za-z0-9_./-]+', target) is not None, 'unsafe input name')
        parts = PurePosixPath(target)
        need(not parts.is_absolute() and '..' not in parts.parts, 'input path escape')
        need(parts.suffix == '.tex', 'unexpected input suffix')
        found.append((start, end + 1, 'book/' + target))
    return found


def expand(reader, entry=ENTRY):
    graph, edges = {}, []

    def visit(name, chain):
        need(name not in chain, f'input cycle: {name}')
        data = reader(name)
        need(name not in graph or graph[name] == data, f'unstable graph input: {name}')
        graph[name] = data
        pieces, cursor = [], 0
        for start, end, child in inputs(data):
            edges.append({'parent': name, 'child': child,
                          'line': data[:start].count(b'\n') + 1})
            pieces.extend((data[cursor:start], visit(child, chain + (name,))))
            cursor = end
        pieces.append(data[cursor:])
        return b''.join(pieces)

    return visit(entry, ()), graph, edges


def main():
    need(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT), 'wrong root')
    need(git('rev-parse', 'HEAD').decode().strip() == BASE, 'wrong HEAD')
    initial_status = git('status', '--porcelain=v1', '--untracked-files=all')
    initial_index = git('ls-files', '--stage', '-z')
    physical_modes_reliable = git('config', '--get', 'core.filemode').strip() == b'true'
    initial_evidence = {str(p.relative_to(EVIDENCE)): sha(p.read_bytes())
                        for p in EVIDENCE.rglob('*') if p.is_file()}
    need(initial_evidence['structure-manifest.json'] == MANIFEST_SHA, 'manifest pin changed')
    tree = git('ls-tree', '-r', '-z', BASE)
    entries = []
    for row in tree.split(b'\0'):
        if row:
            header, name = row.split(b'\t', 1)
            mode, kind, oid = header.split()
            need(kind == b'blob' and mode in (b'100644', b'100755'), 'unsupported Git mode')
            entries.append((name.decode(), mode.decode(), oid.decode()))
    need(len(entries) == 2273, 'tracked path count')
    expected_index = b''.join((mode + ' ' + oid + ' 0\t' + name).encode() + b'\0'
                              for name, mode, oid in entries)
    need(initial_index == expected_index, 'index differs from pinned Git tree')
    need(not git('diff', '--cached', '--name-only'), 'staged changes')
    need(initial_index == (EVIDENCE / 'baseline-git-index.zlist').read_bytes(),
         'recorded baseline index differs')
    blobs, inventory, changed, lfs_count = {}, [], [], 0
    with subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT, env=ENV,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE) as proc:
        need(proc.stdin is not None and proc.stdout is not None and proc.stderr is not None,
             'missing Git batch pipes')
        for name, mode, oid in entries:
            proc.stdin.write(oid.encode() + b'\n')
            proc.stdin.flush()
            response = proc.stdout.readline().split()
            need(len(response) == 3 and response[:2] == [oid.encode(), b'blob'],
                 'Git batch response')
            size = int(response[2])
            blob = proc.stdout.read(size)
            need(len(blob) == size and proc.stdout.read(1) == b'\n', 'Git batch framing')
            blobs[name] = blob
            local = read_local(ROOT, name)
            physical_mode = (ROOT / name).stat().st_mode
            if physical_modes_reliable:
                need(bool(physical_mode & 0o111) == (mode == '100755'),
                     f'executable-bit drift: {name}')
            pointer = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\n'
                                   rb'oid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
            if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
                need(pointer is not None, f'unsupported LFS pointer: {name}')
            if pointer is not None:
                lfs_count += 1
                expected_sha, expected_size = pointer[1].decode(), int(pointer[2])
            else:
                expected_sha, expected_size = sha(blob), len(blob)
            actual_sha = sha(local)
            if expected_sha != actual_sha or expected_size != len(local):
                changed.append(name)
            inventory.append({'path': name, 'git_mode': mode, 'git_blob': oid,
                              'physical_mode': oct(stat.S_IMODE(physical_mode)),
                              'materialized_lfs': pointer is not None,
                              'expected_bytes': expected_size, 'expected_sha256': expected_sha,
                              'actual_bytes': len(local), 'actual_sha256': actual_sha})
        proc.stdin.close()
        need(proc.stdout.read() == b'', 'extra Git batch output')
        error = proc.stderr.read()
        need(proc.wait() == 0 and not error, 'Git batch exit')
    need(changed == [MAIN], f'out-of-scope tracked changes: {changed}')
    need(lfs_count == 412, 'LFS path count')
    untracked = [p.decode() for p in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if p]
    need(set(untracked) == set(NEW), f'untracked scope: {untracked}')
    for name in NEW:
        need(name not in blobs, f'new file already tracked: {name}')
        if physical_modes_reliable:
            need(not (ROOT / name).stat().st_mode & 0o111, f'new source executable: {name}')
    before, old_graph, old_edges = expand(blobs.__getitem__)
    after, new_graph, new_edges = expand(lambda name: read_local(ROOT, name))
    frozen, frozen_graph, frozen_edges = expand(lambda name: read_local(EVIDENCE / 'extracted-source-graph', name))
    need(before == after == frozen, 'expanded source bytes differ')
    need((len(old_graph), len(new_graph), len(old_edges), len(new_edges)) == (26, 36, 25, 35),
         'source graph sizes')
    need(new_graph == frozen_graph and new_edges == frozen_edges, 'live/frozen graph differ')
    need(set(new_graph) - set(old_graph) == set(NEW), 'source graph membership')
    for name, content in old_graph.items():
        need(content == read_local(EVIDENCE / 'baseline-source-graph', name),
             f'baseline graph snapshot differs from Git: {name}')
        if name != MAIN:
            need(content == new_graph[name], f'existing graph node changed: {name}')
    need(before == (EVIDENCE / 'expanded-entry-before.tex').read_bytes()
         == (EVIDENCE / 'expanded-entry-after.tex').read_bytes(), 'expanded receipts differ')
    need(sha(before) == 'cd9c97a260ddc34cc8f420e4e030a6ad44c8b5af82c7f491db91c9e5b850faea'
         and len(before) == 633773, 'expanded source identity')
    manuscript, _, _ = expand(blobs.__getitem__, MAIN)
    current_manuscript, _, _ = expand(lambda name: read_local(ROOT, name), MAIN)
    need(manuscript == current_manuscript, 'expanded manuscript bytes differ')
    original_main = blobs[MAIN]
    live_main = new_graph[MAIN]
    restored, cursor, slices, warnings = [], 0, [], []
    for start, end, child in inputs(live_main):
        if child not in NEW:
            continue
        content = new_graph[child]
        need(original_main.count(content) == 1, f'nonunique original extraction: {child}')
        offset = original_main.index(content)
        if slices:
            need(slices[-1]['end_byte'] <= offset, 'extractions overlap or reorder')
        restored.extend((live_main[cursor:start], content))
        cursor = end
        slices.append({'path': child, 'start_byte': offset, 'end_byte': offset + len(content),
                       'start_line': original_main[:offset].count(b'\n') + 1,
                       'bytes': len(content), 'sha256': sha(content),
                       'terminal_newlines': len(content) - len(content.rstrip(b'\n'))})
        need(len(re.findall(rb'^\\section\{', content, re.M)) == 1, 'chapter boundary')
        need(not inputs(content), 'nested new input')
        need(not re.search(rb'\\(?:newcommand|renewcommand|providecommand|def|gdef|edef|xdef|let|newtheorem|DeclareMathOperator)\b', content),
             f'definition moved into chapter: {child}')
        check = subprocess.run(['git', 'diff', '--no-ext-diff', '--no-index', '--check',
                                '--', '/dev/null', child], cwd=ROOT, env=ENV,
                               capture_output=True, text=True)
        expected = re.fullmatch(re.escape(child) + r':([0-9]+): new blank line at EOF\.\n', check.stdout)
        need(check.returncode == 3 and not check.stderr and expected is not None,
             f'unexpected new-file whitespace finding: {child}: {check.stdout!r}')
        need(content.endswith(b'\n\n'), 'EOF warning has no inherited blank line')
        need(not any(re.search(rb'[ \t]+$', line) for line in content.splitlines()),
             f'trailing spaces/tabs: {child}')
        warnings.append({'path': child, 'git_exit_code': check.returncode,
                         'output': check.stdout, 'status': 'inherited baseline separator bytes; retained'})
    restored.append(live_main[cursor:])
    need(len(slices) == 10 and b''.join(restored) == original_main,
         'main is not exactly the ten replacements')
    tracked_whitespace = subprocess.run(['git', 'diff', '--no-ext-diff', '--check'],
                                        cwd=ROOT, env=ENV, capture_output=True, text=True)
    need(tracked_whitespace.returncode == 0 and not tracked_whitespace.stdout
         and not tracked_whitespace.stderr, 'tracked diff whitespace')
    labels = re.findall(rb'\\label\{([^{}]+)\}', before)
    bibkeys = re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', before)
    need(len(labels) == len(set(labels)) == 607, 'labels count/uniqueness')
    need(len(bibkeys) == len(set(bibkeys)) == 129, 'bibliography count/uniqueness')
    body, appendices = before.split(b'\\appendix\n')
    sections = re.findall(rb'^\\section\{([^\n]+)\}\n\\label\{([^{}]+)\}', body, re.M)
    apps = re.findall(rb'^\\section\{([^\n]+)\}\n\\label\{([^{}]+)\}', appendices, re.M)
    need(len(sections) == 32 and len(apps) == 2, 'sections/appendices count')
    parts = re.findall(rb'^\\monographpart[^\n]*', original_main, re.M)
    need(len(parts) == 7 and parts == re.findall(rb'^\\monographpart[^\n]*', live_main, re.M),
         'part count/order changed')
    ast_report = {}
    for name in ('extract_chapters.py', 'verify_extraction.py'):
        raw = (EVIDENCE / name).read_bytes()
        syntax = ast.parse(raw, filename=name)
        assertion_count = sum(isinstance(node, ast.Assert) for node in ast.walk(syntax))
        need(assertion_count == 0, f'optimization-removable assertions in {name}')
        ast_report[name] = {'sha256': sha(raw), 'assert_nodes': assertion_count}
    need(git('status', '--porcelain=v1', '--untracked-files=all') == initial_status,
         'status changed during review')
    need(git('ls-files', '--stage', '-z') == initial_index, 'index changed during review')
    final_evidence = {str(p.relative_to(EVIDENCE)): sha(p.read_bytes())
                      for p in EVIDENCE.rglob('*') if p.is_file()}
    need(initial_evidence == final_evidence, 'author evidence changed during review')
    print(json.dumps({
        'approval': 'PASS: exact structural extraction; inherited EOF blank lines retained',
        'baseline_commit': BASE, 'author_manifest_sha256': MANIFEST_SHA,
        'python': sys.version, 'optimization': sys.flags.optimize,
        'expanded_entry_sha256': sha(before), 'expanded_entry_bytes': len(before),
        'expanded_manuscript_sha256': sha(manuscript), 'expanded_manuscript_bytes': len(manuscript),
        'baseline_tracked_paths': len(entries), 'unchanged_tracked_paths': len(entries) - 1,
        'materialized_lfs_verified_directly_against_pinned_git': lfs_count,
        'changed_tracked_paths': changed, 'new_source_paths': sorted(untracked),
        'index_sha256': sha(initial_index), 'staged_changes': False,
        'graph_file_counts': [len(old_graph), len(new_graph)],
        'graph_edge_counts': [len(old_edges), len(new_edges)],
        'label_count': len(labels), 'bibliography_count': len(bibkeys),
        'numbered_sections': len(sections), 'appendices': len(apps), 'part_count': len(parts),
        'whole_expansion_and_reconstructed_main_are_exact': True,
        'physical_path_confinement_and_git_index_modes_checked': True,
        'physical_modes_reliable': physical_modes_reliable,
        'physical_mode_note': 'This checkout is on exFAT with core.filemode=false; Git index modes match the pinned tree. Physical file modes are recorded, not interpreted as changes.',
        'tracked_diff_check_passed': True, 'new_file_whitespace': warnings,
        'independently_located_extractions': slices,
        'author_scripts_ast': ast_report,
        'source_graph': {name: {'bytes': len(raw), 'sha256': sha(raw)} for name, raw in new_graph.items()},
        'source_edges': new_edges, 'tracked_inventory': inventory,
        'author_evidence_hashes': initial_evidence,
        'scope': 'Pure source preservation and structural review; no build, PDF, proof audit, numerical replay, stage, commit, install, upload or publication.',
    }, indent=2) + '\n')


if __name__ == '__main__':
    main()
