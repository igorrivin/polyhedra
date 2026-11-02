"""Exercise the author's read-only verifier on in-memory corruptions only."""
from __future__ import annotations

from contextlib import redirect_stdout
import importlib.util
import io
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
AUTHOR = Path('/Volumes/Lexar/lambda/devel/polyhedra/execution/final-chapters-review-2026-11-01/structure')
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
spec = importlib.util.spec_from_file_location('reviewed_verifier', AUTHOR / 'verify_extraction.py')
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load reviewed verifier')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
results = []


def rejected(name, action, expected):
    try:
        with redirect_stdout(io.StringIO()):
            action()
    except module.VerificationError as error:
        if expected not in str(error):
            raise RuntimeError(f'{name}: wrong rejection: {error}') from error
        results.append({'case': name, 'result': 'rejected as required', 'error': str(error)})
    else:
        raise RuntimeError(f'{name}: invalid input accepted')


def virtual_change(path, name, expected):
    original = Path.read_bytes

    def patched(self):
        data = original(self)
        return data + b'% in-memory reviewer corruption\n' if self == path else data

    try:
        Path.read_bytes = patched
        rejected(name, module.main, expected)
    finally:
        Path.read_bytes = original


virtual_change(AUTHOR / 'extracted-source-graph/book/chapters/10-quantum-introduction.tex',
               'modified frozen source', 'Git baseline/frozen recursive bytes differ')
virtual_change(ROOT / 'book/chapters/10-quantum-introduction.tex',
               'modified live source', 'Git baseline/live recursive bytes differ')
virtual_change(ROOT / '.github/workflows/ci.yml',
               'modified unrelated tracked file', 'out-of-scope tracked changes')
virtual_change(AUTHOR / 'baseline-tracked-inventory.json',
               'modified inventory receipt', 'evidence digest mismatch')
for target in ('../escape.tex', '/tmp/escape.tex', 'chapters/$dynamic.tex'):
    payload = ('\\input{' + target + '}\n').encode()
    rejected('unsafe include ' + target,
             lambda payload=payload: module.independently_expand(lambda _: payload),
             'unsafe include')
rejected('include cycle',
         lambda: module.independently_expand(lambda _: b'\\input{main.tex}\n'), 'cycle')
rejected('inline include',
         lambda: module.independently_expand(lambda _: b'text \\input{main.tex}\n'),
         'unsupported include line')
print(json.dumps({'optimization': sys.flags.optimize, 'all_rejections_passed': True,
                  'canonical_or_author_evidence_writes': False, 'cases': results}, indent=2))
