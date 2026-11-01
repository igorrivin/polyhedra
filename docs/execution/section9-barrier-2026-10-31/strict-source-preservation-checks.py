"""Mechanical preservation checks; this is not a fresh mathematical proof audit."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else Path.cwd()).resolve()
OUT = Path(__file__).resolve().parent
BASELINE = '014d1c4e70dfdfc852fa542f3a9c469f08dbd618'
CHAPTER = 'book/chapters/09-volume-hessians.tex'
LEDGER = 'book/claims/section9.json'
old = subprocess.check_output(['git', '-C', str(ROOT), 'show', BASELINE + ':' + CHAPTER]).decode()
new = (ROOT / CHAPTER).read_text()
patterns = {
    'ordered_labels': r'\\label\{([^{}]+)\}',
    'numbered_environment_order': r'\\begin\{(equation|align|proposition|figure)\}',
    'proof_and_proposition_bytes': r'\\begin\{(?:proof|proposition)\}.*?\\end\{(?:proof|proposition)\}',
    'display_math_bytes': r'\\\[.*?\\\]',
    'numbered_math_bytes': r'\\begin\{(?:equation|align)\}.*?\\end\{(?:equation|align)\}',
    'tikz_bytes': r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}',
}
checks = {}
for key, pattern in patterns.items():
    a, b = re.findall(pattern, old, re.S), re.findall(pattern, new, re.S)
    checks[key] = {'unchanged': a == b, 'count': len(b),
                   'baseline_sha256': sha256(json.dumps(a).encode()).hexdigest(),
                   'current_sha256': sha256(json.dumps(b).encode()).hexdigest()}
    assert a == b, key
def inline_math(text):
    delimiters = []
    for position, character in enumerate(text):
        if character != '$':
            continue
        backslashes, j = 0, position - 1
        while j >= 0 and text[j] == '\\':
            backslashes += 1
            j -= 1
        if backslashes % 2 == 0:
            delimiters.append(position)
    assert len(delimiters) % 2 == 0
    return [text[a:b + 1] for a, b in zip(delimiters[::2], delimiters[1::2])]
a, b = inline_math(old), inline_math(new)
assert a == b
checks['inline_math_bytes'] = {'unchanged': True, 'count': len(b),
    'baseline_sha256': sha256(json.dumps(a).encode()).hexdigest(),
    'current_sha256': sha256(json.dumps(b).encode()).hexdigest()}
before = json.loads(subprocess.check_output(['git', '-C', str(ROOT), 'show', BASELINE + ':' + LEDGER]))
after = json.loads((ROOT / LEDGER).read_bytes())
fields = ('id', 'labels', 'label', 'status', 'hypotheses', 'review_evidence', 'source_evidence')
a = [{k: c[k] for k in fields if k in c} for c in before['claims']]
b = [{k: c[k] for k in fields if k in c} for c in after['claims']]
assert a == b and len(b) == 26
checks['claim_proof_status_and_hypotheses'] = {'unchanged': True, 'count': len(b)}
spec = importlib.util.spec_from_file_location('chapter_builder', ROOT / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
labels = [label for data in builder.source_graph(ROOT).values()
          for label in builder.LABEL_RE.findall(builder.uncomment(data.decode()))]
assert len(labels) == len(set(labels)) == 607
checks['full_monograph_labels'] = {'count': len(labels), 'unique': len(set(labels))}
result = {'baseline_commit': BASELINE, 'scope': 'Mechanical byte preservation; not a mathematical re-review',
          'chapter_before_sha256': sha256(old.encode()).hexdigest(),
          'chapter_after_sha256': sha256(new.encode()).hexdigest(),
          'ledger_after_sha256': sha256((ROOT / LEDGER).read_bytes()).hexdigest(),
          'checks': checks, 'all_checks_passed': True}
(OUT / 'strict-source-preservation-checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
