"""One-time byte-preserving extraction from the recorded research commit."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess


ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EVIDENCE = Path(__file__).resolve().parent
BASELINE = 'df952174e55f08a52596d912d9713a9d1e116313'
MAIN = Path('book/polyhedral_volumes_and_geodesic_identities.tex')
CHAPTERS = (
    (
        Path('book/chapters/15-quantum-airy.tex'),
        br'\section{A uniform quantum Airy transition for the regular family}',
        br'\section{Dehn filling, variational response, and quantum surgery}',
    ),
    (
        Path('book/chapters/30-sharp-diagnostics.tex'),
        br'\section{Diagnosing the sharp remainder without fitting its main term}',
        br'\section{Arithmetic cancellation and the geometric remainder}',
    ),
)


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def labels(data: bytes) -> list[str]:
    return [x.decode() for x in re.findall(rb'\\label\{([^}]+)\}', data)]


def main() -> None:
    baseline = subprocess.check_output(
        ['git', 'show', f'{BASELINE}:{MAIN.as_posix()}'], cwd=ROOT
    )
    assert (ROOT / MAIN).read_bytes() == baseline, 'Main source drifted before extraction'
    chapter9 = subprocess.check_output(
        ['git', 'show', f'{BASELINE}:book/chapters/09-volume-hessians.tex'], cwd=ROOT
    )
    assert (ROOT / 'book/chapters/09-volume-hessians.tex').read_bytes() == chapter9
    result = baseline
    sections = {}
    for path, start, end in CHAPTERS:
        assert baseline.count(start) == baseline.count(end) == 1
        first, last = baseline.index(start), baseline.index(end)
        assert last > first
        payload = baseline[first:last]
        marker = b'\\input{' + path.relative_to('book').as_posix().encode() + b'}\n'
        assert result.count(payload) == 1
        assert not (ROOT / path).exists(), f'Refusing to overwrite {path}'
        (ROOT / path).write_bytes(payload)
        (EVIDENCE / path.name).write_bytes(payload)
        result = result.replace(payload, marker, 1)
        sections[path.as_posix()] = {
            'sha256': digest(payload),
            'bytes': len(payload),
            'lines': len(payload.splitlines()),
            'baseline_start_line': baseline[:first].count(b'\n') + 1,
            'baseline_end_line': baseline[:last].count(b'\n'),
            'labels': labels(payload),
            'input_line': marker.decode(),
        }
    reconstructed = result
    for path, *_ in CHAPTERS:
        marker = sections[path.as_posix()]['input_line'].encode()
        assert reconstructed.count(marker) == 1
        reconstructed = reconstructed.replace(marker, (ROOT / path).read_bytes())
    assert reconstructed == baseline
    marker9 = b'\\input{chapters/09-volume-hessians.tex}\n'
    assert baseline.count(marker9) == reconstructed.count(marker9) == 1
    before_expansion = baseline.replace(marker9, chapter9)
    after_expansion = reconstructed.replace(marker9, chapter9)
    assert before_expansion == after_expansion
    before_labels = labels(before_expansion)
    after_labels = labels(after_expansion)
    assert before_labels == after_labels
    assert len(before_labels) == len(set(before_labels)) == 607
    (ROOT / MAIN).write_bytes(result)
    (EVIDENCE / 'baseline-main.tex').write_bytes(baseline)
    (EVIDENCE / 'extracted-main.tex').write_bytes(result)
    (EVIDENCE / '09-volume-hessians.tex').write_bytes(chapter9)
    report = {
        'operation': 'byte-preserving chapter extraction, before substantive revisions',
        'baseline_commit': BASELINE,
        'root': str(ROOT),
        'main_path': MAIN.as_posix(),
        'baseline_main_sha256': digest(baseline),
        'extracted_main_sha256': digest(result),
        'reconstructed_main_sha256': digest(reconstructed),
        'full_expansion_sha256': digest(after_expansion),
        'full_expansion_bytes': len(after_expansion),
        'exact_main_reconstruction': reconstructed == baseline,
        'exact_full_expansion': before_expansion == after_expansion,
        'label_count': len(after_labels),
        'unique_label_count': len(set(after_labels)),
        'labels_in_identical_order': before_labels == after_labels,
        'duplicate_labels': [label for label, count in Counter(after_labels).items() if count > 1],
        'sections': sections,
        'claim_scope': 'Source equivalence only; no proof review or numerical replay.',
    }
    (EVIDENCE / 'extraction.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in (
        'baseline_commit', 'baseline_main_sha256', 'extracted_main_sha256',
        'full_expansion_sha256', 'exact_main_reconstruction',
        'exact_full_expansion', 'label_count', 'unique_label_count',
    )}, indent=2))


if __name__ == '__main__':
    main()
