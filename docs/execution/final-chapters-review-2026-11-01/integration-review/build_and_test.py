"""Read-only canonical verification; outputs stay in this review directory."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = ROOT.parent / 'execution/final-chapters-review-2026-11-01'
OUT = OUTER / 'integration-review'
AUTHOR = OUTER / 'integration-author/revision-v2'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def write(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')

def verify_source():
    freeze = json.loads((AUTHOR / 'author-freeze.json').read_text())
    if digest(AUTHOR / 'author-freeze.json') != '174bc16423e1917a7d6ed634e90ac8a47dd5a86cedb551efb67bf86218d03d16':
        raise RuntimeError('Author freeze identity mismatch')
    for group in ('source_sha256', 'tex_input_sha256'):
        for rel, expected in freeze[group].items():
            if digest(ROOT / rel) != expected:
                raise RuntimeError('Canonical source mismatch: ' + rel)
    return freeze

def prepare():
    freeze = verify_source()
    graph = {}
    edges = []
    def visit(rel):
        if rel in graph:
            raise RuntimeError('Repeated or cyclic active source input: ' + rel)
        data = (ROOT / rel).read_bytes()
        graph[rel] = sha256(data).hexdigest()
        # Active sources use literal input paths, not generated input macros.
        text = re.sub(r'(?<!\\)%[^\n]*', '', data.decode())
        for child in re.findall(r'\\(?:input|include)\{([^}]+)\}', text):
            if not child.endswith('.tex'):
                child += '.tex'
            target = (ROOT / 'book' / child).resolve()
            child_rel = str(target.relative_to(ROOT))
            edges.append({'parent': rel, 'literal': child, 'child': child_rel})
            visit(child_rel)
    visit('book/main.tex')
    if graph != freeze['tex_input_sha256']:
        raise RuntimeError('Independently traversed graph differs from author map')
    snap = OUT / 'frozen-source'
    snap.mkdir(exist_ok=False)
    for rel, expected in graph.items():
        dest = snap / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / rel).read_bytes())
        if digest(dest) != expected:
            raise RuntimeError('Snapshot copy mismatch: ' + rel)
    write('tex-input-freeze.json', {'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
          'stage': 'precommit integrated source', 'files': graph, 'edges': edges,
          'author_freeze_sha256': digest(AUTHOR / 'author-freeze.json')})
    marker = json.loads((OUTER / 'pdf-preflight/marker-receipt.json').read_text())
    if marker['returncode'] != 0 or not marker['successful_exactly_once_in_this_increment']:
        raise RuntimeError('Existing marker receipt not successful')
    write('marker-reuse.json', {'prior_marker_receipt': '../pdf-preflight/marker-receipt.json',
          'sha256': digest(OUTER / 'pdf-preflight/marker-receipt.json'),
          'executed_again': False, 'prior_started_at_utc': marker['started_at_utc']})
    print(json.dumps({'frozen_active_inputs': len(graph), 'source_paths': len(freeze['source_sha256'])}))

def command_receipt(name, command, cwd, scope):
    verify_source()
    receipt = {'command': command, 'cwd': str(cwd), 'scope': scope,
               'started_at_utc': datetime.now(timezone.utc).isoformat()}
    start = time.perf_counter()
    with (OUT / (name + '.stdout.txt')).open('x') as stdout, (OUT / (name + '.stderr.txt')).open('x') as stderr:
        result = subprocess.run(command, cwd=cwd, env=ENV, stdout=stdout, stderr=stderr, check=False)
    receipt.update({'returncode': result.returncode, 'elapsed_seconds': time.perf_counter()-start,
                    'finished_at_utc': datetime.now(timezone.utc).isoformat()})
    verify_source()
    receipt['source_unchanged_before_after'] = True
    write(name + '.json', receipt)
    print(json.dumps(receipt))
    if result.returncode:
        raise RuntimeError(name + ' failed')

def build():
    (OUT / 'pdf-build').mkdir(exist_ok=False)
    command_receipt('build-command', ['/Library/TeX/texbin/latexmk', '-norc', '-pdf',
                    '-interaction=nonstopmode', '-halt-on-error', '-file-line-error',
                    '-no-shell-escape', '-outdir=../../pdf-build', 'main.tex'],
                    OUT / 'frozen-source/book', 'Actual precommit integrated build; no marker rerun')

def tests():
    command_receipt('site-tests', ['/tmp/polyhedra-baseline-20261031/bin/python', '-B', '-m',
                    'unittest', 'discover', '-s', 'site/tests', '-v'], ROOT,
                    'Existing focused site test suite, run once; not the dependency-complete toolkit suite')

if __name__ == '__main__':
    {'prepare': prepare, 'build': build, 'tests': tests}[sys.argv[1]]()
