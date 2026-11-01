"""Replay the frozen structural extraction without rewriting active sources."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


root = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
evidence = Path(__file__).resolve().parent
record = json.loads((evidence / 'extraction.json').read_text())
baseline = subprocess.check_output(
    ['git', 'show', f"{record['baseline_commit']}:{record['main_path']}"], cwd=root
)
assert baseline == (evidence / 'baseline-main.tex').read_bytes()
extracted = (evidence / 'extracted-main.tex').read_bytes()
assert sha256(extracted).hexdigest() == record['extracted_main_sha256']
restored = extracted
section_counts = {}
for path, section in record['sections'].items():
    payload = (evidence / Path(path).name).read_bytes()
    assert sha256(payload).hexdigest() == section['sha256']
    marker = section['input_line'].encode()
    assert restored.count(marker) == 1
    restored = restored.replace(marker, payload)
    section_counts[path] = len(re.findall(rb'\\label\{([^}]+)\}', payload))
assert restored == baseline
chapter9 = subprocess.check_output(
    ['git', 'show', f"{record['baseline_commit']}:book/chapters/09-volume-hessians.tex"],
    cwd=root,
)
assert chapter9 == (evidence / '09-volume-hessians.tex').read_bytes()
marker9 = b'\\input{chapters/09-volume-hessians.tex}\n'
expanded = restored.replace(marker9, chapter9)
assert expanded == baseline.replace(marker9, chapter9)
assert sha256(expanded).hexdigest() == record['full_expansion_sha256']
labels = re.findall(rb'\\label\{([^}]+)\}', expanded)
assert len(labels) == len(set(labels)) == record['label_count'] == 607
result = {
    'baseline_commit': record['baseline_commit'],
    'frozen_main_reconstructs_baseline_bytes': True,
    'frozen_full_expansion_reconstructs_baseline_bytes': True,
    'label_count': len(labels),
    'unique_label_count': len(set(labels)),
    'duplicate_labels': [label.decode() for label, count in Counter(labels).items() if count > 1],
    'section_label_counts': section_counts,
    'live_main_still_equals_structural_snapshot': (
        root / record['main_path']
    ).read_bytes() == extracted,
    'scope': 'Frozen extraction evidence only. Later chapter revisions have independent review status.',
}
print(json.dumps(result, indent=2))
