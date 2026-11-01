"""Extract Sections 23--29 and 31 with byte-preserving recursive expansion.

Run once without arguments; --verify-only checks the frozen evidence against
the pinned Git baseline and reports whether live source still matches it.
This is structural source preservation, not a proof or build check.
"""
from __future__ import annotations

from argparse import ArgumentParser
from datetime import datetime, timezone
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = Path(__file__).resolve().parent
BASELINE = '9c8b61790aaa674902b9d60e80122c318a578bcc'
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'
ENTRY = 'book/main.tex'
EXISTING_30 = 'book/chapters/30-sharp-diagnostics.tex'
INPUT = re.compile(rb'^\\(?:input|include)\{([^{}\r\n]+)\}\n', re.M)
SECTIONS = (
    (23, '23-trace-coefficients.tex', 'sec:coefficientdistributions',
     r'\section{Simple multicurve coefficients of a twisted trace formula}',
     r'\section{Quantitative counting and coefficient cancellation}'),
    (24, '24-quantitative-counting.tex', 'sec:quantitativecounting',
     r'\section{Quantitative counting and coefficient cancellation}',
     r'\section{Global coefficient filters and a length-valued Euler product}'),
    (25, '25-global-coefficient-filters.tex', 'sec:globalfilters',
     r'\section{Global coefficient filters and a length-valued Euler product}',
     r'\monographpart{Mapping-class dynamics and mixing}'),
    (26, '26-counting-to-mixing.tex', 'sec:countmixing',
     r'\section{When counting errors imply mixing}',
     r'\section{Filling-pair coefficients and a weighted mixing converse}'),
    (27, '27-weighted-mixing-converse.tex', 'sec:pairconverse',
     r'\section{Filling-pair coefficients and a weighted mixing converse}',
     r'\section{Genus two: compact polyhedra and a marked-torus model}'),
    (28, '28-genus-two-model.tex', 'sec:genus2markedtorus',
     r'\section{Genus two: compact polyhedra and a marked-torus model}',
     r'\section{From simple-curve coefficients to controlled observables}'),
    (29, '29-controlled-observables.tex', 'sec:coefficientobservables',
     r'\section{From simple-curve coefficients to controlled observables}',
     r'\monographpart{Sharp counting and arithmetic}'),
    (31, '31-arithmetic-remainder.tex', 'sec:arithmeticgeometry',
     r'\section{Arithmetic cancellation and the geometric remainder}',
     r'\monographpart{Open problems and conjectural directions}'),
)


def digest(data):
    return sha256(data).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def labels(data):
    return [value.decode() for value in re.findall(rb'\\label\{([^{}]+)\}', data)]


def bibitems(data):
    return [value.decode() for value in re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', data)]


def source_graph():
    spec = importlib.util.spec_from_file_location('section9_source_graph', ROOT/'site/build_section9.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.source_graph(ROOT)


def expand(graph, entry=ENTRY, active=()):
    assert entry not in active, entry
    data = graph[entry]
    # The source-graph checker validates literal paths; the current active graph
    # uses exactly one standalone input per line, as in prior structural gates.
    uncommented = re.sub(rb'(?<!\\)%[^\n]*', b'', data)
    assert len(re.findall(rb'\\(?:input|include)\b', uncommented)) == len(INPUT.findall(data)), entry

    def replacement(match):
        name = Path(match[1].decode())
        if name.suffix != '.tex':
            name = name.with_suffix('.tex')
        return expand(graph, str(Path('book')/name), (*active, entry))

    return INPUT.sub(replacement, data)


def snapshot_graph(directory, graph):
    for name, data in graph.items():
        path = directory/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def read_graph(directory, manifest):
    graph = {}
    for name, record in manifest.items():
        data = (directory/name).read_bytes()
        assert len(data) == record['bytes'] and digest(data) == record['sha256'], name
        graph[name] = data
    return graph


def graph_manifest(graph):
    return {name: {'bytes': len(data), 'sha256': digest(data)} for name, data in graph.items()}


def baseline_inventory():
    """Bind each materialized baseline file to its Git blob or LFS identity."""
    entries = []
    for row in git('ls-tree', '-r', '-z', BASELINE).split(b'\0'):
        if row:
            fields, path = row.split(b'\t', 1)
            mode, kind, oid = fields.split()
            assert kind == b'blob' and mode != b'120000'
            entries.append((mode, oid, path.decode()))
    packed = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                            input=b'\n'.join(row[1] for row in entries)+b'\n',
                            capture_output=True, check=True)
    assert not packed.stderr
    offset, inventory = 0, []
    for mode, oid, name in entries:
        end = packed.stdout.index(b'\n', offset)
        found, kind, length = packed.stdout[offset:end].split()
        assert found == oid and kind == b'blob'
        start, size = end+1, int(length)
        blob = packed.stdout[start:start+size]
        assert packed.stdout[start+size:start+size+1] == b'\n'
        offset = start+size+1
        data = (ROOT/name).read_bytes()
        record = {'path': name, 'git_mode': mode.decode(), 'git_blob': oid.decode(),
                  'bytes': len(data), 'sha256': digest(data)}
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
            assert match and digest(data) == match[1].decode() and len(data) == int(match[2]), name
            record['materialized_lfs'] = True
        else:
            assert data == blob, name
        inventory.append(record)
    assert offset == len(packed.stdout) and len(inventory) == 1914
    return inventory


def section_map(expanded):
    body = expanded.split(b'\\appendix', 1)[0]
    matches = list(re.finditer(rb'^\\section\{([^\n]+)\}\n\\label\{([^{}]+)\}', body, re.M))
    assert len(matches) == 32
    result = {}
    for index, match in enumerate(matches):
        number = index + 1
        end = matches[index+1].start() if index+1 < len(matches) else len(body)
        result[str(number)] = {'number': number, 'title': match[1].decode(),
                               'section_label': match[2].decode(),
                               'labels': labels(body[match.start():end])}
    return result


def verify_frozen():
    report = json.loads((OUT/'structure-manifest.json').read_text())
    assert report['baseline_commit'] == BASELINE
    before = read_graph(OUT/'baseline-source-graph', report['baseline_source_graph'])
    after = read_graph(OUT/'extracted-source-graph', report['extracted_source_graph'])
    for name, data in before.items():
        assert data == git('show', f'{BASELINE}:{name}'), name
    restored = after[MAIN]
    for _, name, _, _, _ in SECTIONS:
        path = 'book/chapters/'+name
        marker = ('\\input{chapters/'+name+'}\n').encode()
        assert restored.count(marker) == 1
        restored = restored.replace(marker, after[path], 1)
    assert restored == before[MAIN]
    full_before, full_after = expand(before), expand(after)
    manuscript_before, manuscript_after = expand(before, MAIN), expand(after, MAIN)
    assert full_before == full_after == (OUT/'expanded-entry-before.tex').read_bytes() == (OUT/'expanded-entry-after.tex').read_bytes()
    assert manuscript_before == manuscript_after
    assert digest(full_before) == report['expanded_entry_before_sha256'] == report['expanded_entry_after_sha256']
    assert digest(manuscript_before) == report['expanded_manuscript_before_sha256'] == report['expanded_manuscript_after_sha256']
    assert labels(full_before) == labels(full_after) == report['label_order']
    assert len(labels(full_before)) == len(set(labels(full_before))) == 607
    assert bibitems(full_before) == bibitems(full_after) == report['bibliography_order']
    assert len(bibitems(full_before)) == len(set(bibitems(full_before))) == 129
    assert section_map(full_before) == section_map(full_after) == report['all_numbered_sections']
    assert before[EXISTING_30] == after[EXISTING_30]
    assert all(after[name] == data for name, data in before.items() if name != MAIN)
    for name, item in report['evidence_files'].items():
        data = (OUT/name).read_bytes()
        assert digest(data) == item['sha256'] and len(data) == item['bytes'], name
    live = {name: (ROOT/name).read_bytes() == data for name, data in after.items()}
    inventory = json.loads((OUT/'baseline-tracked-inventory.json').read_text())['files']
    changes = [item['path'] for item in inventory
               if digest((ROOT/item['path']).read_bytes()) != item['sha256']]
    result = {'frozen_extraction_verified': True, 'baseline_commit': BASELINE,
              'expanded_entry_sha256': digest(full_after),
              'expanded_manuscript_sha256': digest(manuscript_after),
              'labels_preserved_in_order': 607, 'bibliography_items_preserved_in_order': 129,
              'sections_23_through_31_preserved': True,
              'live_active_graph_matches_structural_snapshot': all(live.values()),
              'live_changed_baseline_tracked_paths': changes,
              'scope': 'Frozen byte equivalence only; no mathematical, numerical, PDF, or publication claim.'}
    print(json.dumps(result, indent=2))


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    if args.verify_only:
        verify_frozen()
        return
    assert git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT)
    assert git('rev-parse', 'HEAD').decode().strip() == BASELINE
    assert not git('status', '--porcelain', '--untracked-files=all')
    assert not (OUT/'structure-manifest.json').exists()
    before = source_graph()
    assert len(before) == 18
    inventory = baseline_inventory()
    baseline = before[MAIN]
    extracted, payloads, sections = baseline, {}, {}
    for number, name, label, first, last in SECTIONS:
        first, last = first.encode(), last.encode()
        assert baseline.count(first) == baseline.count(last) == 1
        a, b = baseline.index(first), baseline.index(last)
        assert a < b
        data = baseline[a:b]
        path = 'book/chapters/'+name
        marker = ('\\input{chapters/'+name+'}\n').encode()
        assert labels(data)[0] == label and not (ROOT/path).exists()
        assert b'\\monographpart{' not in data and not INPUT.search(data)
        assert extracted.count(data) == 1
        extracted = extracted.replace(data, marker, 1)
        payloads[path] = data
        sections[str(number)] = {'number': number, 'path': path, 'section_label': label,
            'baseline_start_line': baseline[:a].count(b'\n')+1,
            'baseline_end_line': baseline[:b].count(b'\n'),
            'bytes': len(data), 'sha256': digest(data), 'labels': labels(data),
            'input_line': marker.decode(),
            'terminal_newline_count': len(data)-len(data.rstrip(b'\n'))}
    after = {**before, MAIN: extracted, **payloads}
    full_before, full_after = expand(before), expand(after)
    manuscript_before, manuscript_after = expand(before, MAIN), expand(after, MAIN)
    assert full_before == full_after and manuscript_before == manuscript_after
    assert labels(full_before) == labels(full_after)
    assert len(labels(full_before)) == len(set(labels(full_before))) == 607
    assert bibitems(full_before) == bibitems(full_after)
    assert len(bibitems(full_before)) == len(set(bibitems(full_before))) == 129
    numbered = section_map(full_before)
    assert numbered == section_map(full_after)
    assert re.findall(rb'^\\monographpart.*$', baseline, re.M) == re.findall(rb'^\\monographpart.*$', extracted, re.M)
    sections['30'] = {'number': 30, 'path': EXISTING_30,
        'section_label': numbered['30']['section_label'], 'unchanged_existing_chapter': True,
        'bytes': len(before[EXISTING_30]), 'sha256': digest(before[EXISTING_30]),
        'labels': labels(before[EXISTING_30])}
    snapshot_graph(OUT/'baseline-source-graph', before)
    snapshot_graph(OUT/'extracted-source-graph', after)
    (OUT/'expanded-entry-before.tex').write_bytes(full_before)
    (OUT/'expanded-entry-after.tex').write_bytes(full_after)
    write_json(OUT/'baseline-tracked-inventory.json', {'baseline_commit': BASELINE, 'files': inventory})
    for name, data in payloads.items():
        (ROOT/name).write_bytes(data)
    (ROOT/MAIN).write_bytes(extracted)
    assert source_graph() == after
    changed = [item['path'] for item in inventory
               if digest((ROOT/item['path']).read_bytes()) != item['sha256']]
    assert changed == [MAIN], changed
    untracked = [name.decode() for name in git('ls-files', '--others', '--exclude-standard', '-z').split(b'\0') if name]
    assert set(untracked) == set(payloads), untracked
    assert not git('diff', '--cached', '--name-only')
    assert git('rev-parse', 'HEAD').decode().strip() == BASELINE
    diff_check = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, capture_output=True, text=True)
    assert diff_check.returncode == 0, diff_check.stdout+diff_check.stderr
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
        'label_order': labels(full_after), 'label_count': 607, 'unique_label_count': 607,
        'bibliography_order': bibitems(full_after), 'bibliography_count': 129,
        'all_numbered_sections': numbered,
        'sections_23_through_31': {str(n): sections[str(n)] for n in range(23,32)},
        'source_changes': changes,
        'baseline_source_graph': graph_manifest(before),
        'extracted_source_graph': graph_manifest(after),
        'baseline_inventory_files': len(inventory),
        'baseline_materialized_lfs_files': sum(item.get('materialized_lfs', False) for item in inventory),
        'unchanged_prior_tracked_files': len(inventory)-1,
        'changed_prior_tracked_paths': changed, 'new_source_paths': sorted(untracked),
        'existing_section_30_unchanged': True,
        'part_headings_identical_and_retained_in_main': True,
        'git_diff_check_passed': True, 'index_unchanged': True, 'head_unchanged': True,
        'command': 'python3 '+str(OUT/'extract_chapters.py'),
        'verification_command': 'python3 '+str(OUT/'extract_chapters.py')+' --verify-only',
        'scope': 'Source structure and preservation only. No mathematical edits, builds, commits, network operations, uploads, or canonical artifacts.',
    }
    evidence_names = ['extract_chapters.py', 'baseline-tracked-inventory.json',
                      'expanded-entry-before.tex', 'expanded-entry-after.tex']
    report['evidence_files'] = {name: {'sha256': digest((OUT/name).read_bytes()),
        'bytes': (OUT/name).stat().st_size} for name in evidence_names}
    write_json(OUT/'structure-manifest.json', report)
    print(json.dumps({key: report[key] for key in (
        'baseline_commit', 'expanded_entry_before_sha256', 'expanded_entry_after_sha256',
        'expanded_manuscript_before_sha256', 'expanded_manuscript_after_sha256',
        'label_count', 'bibliography_count', 'baseline_inventory_files',
        'baseline_materialized_lfs_files', 'unchanged_prior_tracked_files',
        'changed_prior_tracked_paths', 'new_source_paths')}, indent=2))


if __name__ == '__main__':
    main()
