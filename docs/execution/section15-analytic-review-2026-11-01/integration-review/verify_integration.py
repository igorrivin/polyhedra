"""Independent Section 15 source, numerical-delta, and preservation checks.

This script only writes evidence beneath its own outer review directory.
No author audit helper or evaluator is imported.
"""
from pathlib import Path
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import collections
import datetime
import hashlib
import json
import os
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
WS = ROOT.parent
EV = WS / 'execution/section15-analytic-review-2026-11-01'
OUT = EV / 'integration-review'
BASE = '3ddf610dbe4578c7828e55f4e9cd92aacaba6df6'
CHAPTER = 'book/chapters/15-quantum-airy.tex'
LEDGER = 'book/claims/section15.json'
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read_json(path):
    return json.loads(path.read_text())

def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd)

def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + '\n')

def identity(name):
    data = (ROOT / name).read_bytes()
    return {'path': name, 'sha256': sha(data), 'bytes': len(data)}

def expand(data, get):
    return re.sub(rb'^\\input\{chapters/([^{}\n]+\.tex)\}\n',
                  lambda m: expand(get('book/chapters/' + m[1].decode()), get),
                  data, flags=re.M)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
assert git('rev-parse', 'HEAD').decode().strip() == BASE
author = read_json(EV / 'math-author/integrated-author-manifest.json')
code = read_json(EV / 'computation/author-handoff.json')
expected = {**author['owned_final_sha256'], **code['code_freeze_sha256']}
assert len(author['owned_final_sha256']) == 8
assert len(code['code_freeze_sha256']) == 4
assert len(expected) == 12
for name, digest in expected.items():
    assert sha((ROOT / name).read_bytes()) == digest, name
source_identities = [identity(name) for name in sorted(expected)]

# Bind the previously approved analytic bytes before examining the delta.
math_approval = read_json(EV / 'math-review/approved-hashes.json')
for name, digest in math_approval['approved_sha256'].items():
    assert sha((EV / 'math-author/integration-baseline' / name).read_bytes()) == digest
for name, digest in math_approval['evidence_sha256'].items():
    assert sha((EV / 'math-review' / name).read_bytes()) == digest
old_chapter = (EV / 'math-author/integration-baseline' / CHAPTER).read_bytes()
new_chapter = (ROOT / CHAPTER).read_bytes()
start = b'\\subsection{Numerical evidence and reproducibility status}'
end = b'\\subsection{Interpretation and scope}'
assert old_chapter.count(start) == new_chapter.count(start) == 1
assert old_chapter.count(end) == new_chapter.count(end) == 1
old_prefix, old_rest = old_chapter.split(start)
new_prefix, new_rest = new_chapter.split(start)
old_numeric, old_suffix = old_rest.split(end)
new_numeric, new_suffix = new_rest.split(end)
assert old_prefix == new_prefix and old_suffix == new_suffix
assert old_numeric != new_numeric

old_ledger = read_json(EV / 'math-author/integration-baseline' / LEDGER)
new_ledger = read_json(ROOT / LEDGER)
old_claims = {row['id']: row for row in old_ledger['claims']}
new_claims = {row['id']: row for row in new_ledger['claims']}
assert len(old_claims) == 13 and len(new_claims) == 14
assert set(new_claims) - set(old_claims) == {'s15.quantum_numerics'}
allowed_claim_changes = {
    's15.normalization': {'computation'},
    's15.strip_estimate': {'computation'},
    's15.airy_column': {'computation'},
    's15.reported_quantum_column': {'computation', 'coverage_gap', 'hypotheses'},
}
claim_delta = {}
for name, old in old_claims.items():
    new = new_claims[name]
    changed = {key for key in set(old) | set(new) if old.get(key) != new.get(key)}
    assert changed == allowed_claim_changes.get(name, set()), (name, changed)
    assert old['status'] == new['status']
    if 'proof' in old:
        assert old['proof'] == new['proof']
    claim_delta[name] = sorted(changed)
top_changes = {key for key in set(old_ledger) | set(new_ledger)
               if key != 'claims' and old_ledger.get(key) != new_ledger.get(key)}
assert top_changes == {'revision_scope', 'status_definitions', 'computational_companion'}
for key, value in old_ledger['status_definitions'].items():
    assert new_ledger['status_definitions'][key] == value

# Recompute table rounding and comparisons from the recorded strings, without
# importing either numerical implementation. Fractions identify exact inputs.
full_path = EV / 'computation/full-v1.json'
ref_path = EV / 'computation-review/independent-whole-q-matrix.json'
assert sha(full_path.read_bytes()) == 'bfb7bf75aa4522e794f2c6000863df786988a67bf92354d41d7075dfcee37a83'
assert sha(ref_path.read_bytes()) == '183f963fef33d642a83c771de942acd3ee5c7bcb99874ccb54455743db3e1045'
full, refs = read_json(full_path), read_json(ref_path)
assert full['source_at_start'] == full['source_at_finish']
assert full['source_at_start']['commit'] == BASE
assert len(full['rows']) == 21 and len(full['comparisons']) == len(refs['rows']) == 7
grouped = collections.defaultdict(dict)
settings = {(60, '1', 12, 0), (90, '1', 14, 0), (90, '5/4', 14, 2)}
for row in full['rows']:
    p = row['parameters']
    key = (Fraction(p['b']), Fraction(p['zeta']))
    setting = (p['digits'], p['contour_real'], p['cutoff'], p['extra_terms'])
    assert setting in settings and setting not in grouped[key]
    grouped[key][setting] = row
assert len(grouped) == 7 and all(set(rows) == settings for rows in grouped.values())
high = {key: rows[(90, '1', 14, 0)] for key, rows in grouped.items()}
history = read_json(ROOT / 'experiments/section15/historical-table.json')
table = re.findall(rb'\$([0-9.]+)\$&\$([01])\$&\$([0-9.]+)\$&\$([0-9.]+)\$\\\\', new_numeric)
assert len(table) == len(history['rows']) == 6
rounding = []
comparison_rows = []
with localcontext() as ctx:
    ctx.prec = 120
    quantum = Decimal('0.000001')
    for fields, historical in zip(table, history['rows']):
        b, zeta, printed_q, printed_q1 = [x.decode() for x in fields]
        assert (b, zeta) == (historical['b'], historical['zeta'])
        row = high[(Fraction(b), Fraction(zeta))]
        rounded_q = format(Decimal(row['Q']).quantize(quantum, rounding=ROUND_HALF_EVEN), 'f')
        rounded_q1 = format(Decimal(row['Airy_Q1']).quantize(quantum, rounding=ROUND_HALF_EVEN), 'f')
        assert printed_q == rounded_q and printed_q1 == rounded_q1
        assert printed_q1 == historical['printed_Q1']
        rounding.append({'b': b, 'zeta': zeta, 'Q_90dps_C1': row['Q'],
                         'rounded_Q': rounded_q, 'rounded_Airy_Q1': rounded_q1,
                         'historical_Q': historical['reported_Q'],
                         'historical_rounding_agrees': rounded_q == historical['reported_Q']})
    assert [r['historical_rounding_agrees'] for r in rounding] == [False, True, True, True, True, True]
    assert rounding[0]['rounded_Q'] == '0.459086'
    low_high, contour = [], []
    for key, rows in grouped.items():
        q = Decimal(rows[(90, '1', 14, 0)]['Q'])
        low_high.append(abs(q - Decimal(rows[(60, '1', 12, 0)]['Q'])))
        contour.append(abs(q - Decimal(rows[(90, '5/4', 14, 2)]['Q'])))
    assert max(low_high) < Decimal('4e-57')
    assert max(contour) < Decimal('1.3e-91')
    # The runner computes these differences before rounding each serialized Q.
    # In particular, the 90-digit Q strings can coincide while their internally
    # evaluated contour difference is nonzero. Preserve both distinct checks.
    recorded_low_high = max(Decimal(row['low_high_precision_absolute_difference'])
                            for row in full['comparisons'])
    recorded_contour = max(Decimal(row['changed_contour_and_D_terms_absolute_difference'])
                          for row in full['comparisons'])
    assert recorded_low_high < Decimal('4e-57')
    assert recorded_contour < Decimal('1.3e-91')
    residuals = [format(Decimal(high[(Fraction(b), Fraction(1))]['scaled_remainder']).quantize(Decimal('0.000000001')), 'f')
                 for b in ['0.0125', '0.00625', '0.003125']]
    assert residuals == ['1.208081684', '1.211366819', '1.208878763']
    for value in residuals:
        assert value.encode() in new_numeric
    neg = high[(Fraction(1, 160), Fraction(-1))]['Q']
    assert Decimal(neg).quantize(Decimal('0.000000000000001')) == Decimal('0.517966671856531')
    assert b'0.517966671856531' in new_numeric
    for row in refs['rows']:
        key = (Fraction(row['b']), Fraction(row['zeta']))
        assert row['integration_warnings'] == []
        delta = abs(Decimal(str(row['Q'])) - Decimal(high[key]['Q']))
        assert delta < Decimal('2e-12')
        comparison_rows.append({'b': row['b'], 'zeta': row['zeta'], 'reference_Q': str(row['Q']),
                                'Q_90dps_C1': high[key]['Q'], 'observed_absolute_difference': str(delta)})
    max_ref = max(Decimal(row['observed_absolute_difference']) for row in comparison_rows)
numeric_report = {
    'generated_at_utc': now, 'decision': 'approved_for_recorded_finite_evidence_scope',
    'analytic_approval_manifest_sha256': sha((EV / 'math-review/approved-hashes.json').read_bytes()),
    'approved_analytic_sha256': math_approval['approved_sha256'],
    'reviewed_final_sha256': {name: expected[name] for name in [CHAPTER, LEDGER]},
    'chapter_delta_confined_to_numerical_subsection': True,
    'analytic_prefix_and_interpretation_suffix_byte_identical': True,
    'ledger_old_analytic_proofs_statuses_and_source_pins_preserved': True,
    'ledger_claim_count': len(new_claims), 'ledger_claim_field_changes': claim_delta,
    'ledger_top_level_changes': sorted(top_changes),
    'full_v1_sha256': sha(full_path.read_bytes()), 'full_v1_source_start_finish_equal': True,
    'full_v1_source_identities': full['source_at_start'],
    'full_v1_rows': 21, 'parameter_pairs': 7, 'table_rows': rounding,
    'maximum_serialized_60_90_difference': str(max(low_high)),
    'maximum_serialized_contour_order_difference': str(max(contour)),
    'maximum_recorded_before_Q_serialization_60_90_difference': str(recorded_low_high),
    'maximum_recorded_before_Q_serialization_contour_order_difference': str(recorded_contour),
    'comparison_precision_note': 'The declared bounds are checked against the runner comparisons computed before Q serialization; rounded serialized Q differences are recorded separately.',
    'zeta1_scaled_remainders_rounded': residuals, 'negative_zeta_Q': neg,
    'independent_reference_sha256': sha(ref_path.read_bytes()),
    'maximum_independent_observed_difference': str(max_ref), 'independent_comparisons': comparison_rows,
    'limitations': [
        'The full-v1 run belongs to its recorded earlier source hashes, not the final corrected code.',
        'Final clean-source full replay remains a separate post-source-commit gate.',
        'Observed numerical agreements do not certify achieved digits or interval quadrature.',
        'Original historical evaluator, raw output and rounding convention remain unrecovered.',
        'No enlargement to arbitrary shapes, unbounded zeta, fixed-volume limits or global invariants.',
    ],
}
save('numeric-delta-review.json', numeric_report)

# Preserve every other baseline path, including materialized LFS payloads.
modified = set(author['owned_final_sha256'])
entries = []
for record in git('ls-tree', '-r', '-z', BASE).split(b'\0'):
    if record:
        fields, path = record.split(b'\t', 1)
        mode, kind, oid = fields.split()
        assert kind == b'blob'
        entries.append((mode, oid, path.decode()))
assert len(entries) == 1851
protected = [row for row in entries if row[2] not in modified]
assert len(protected) == 1843
batch = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT,
                       input=b'\n'.join(row[1] for row in protected) + b'\n',
                       capture_output=True, check=True)
assert not batch.stderr
offset, lfs = 0, 0
preserved = []
for mode, oid, name in protected:
    finish = batch.stdout.index(b'\n', offset)
    found, kind, size = batch.stdout[offset:finish].split()
    assert found == oid and kind == b'blob'
    size, start = int(size), finish + 1
    blob = batch.stdout[start:start + size]
    assert batch.stdout[start + size:start + size + 1] == b'\n'
    offset = start + size + 1
    data = os.readlink(ROOT / name).encode() if mode == b'120000' else (ROOT / name).read_bytes()
    if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
        match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
        assert match and sha(data) == match[1].decode() and len(data) == int(match[2]), name
        lfs += 1
    else:
        assert data == blob, name
    preserved.append({'path': name, 'sha256': sha(data), 'bytes': len(data)})
assert offset == len(batch.stdout) and lfs == 412

inventory = read_json(WS / 'audit/2026-10-31/source-inventory.json')
originals = []
for repo in inventory['repositories']:
    path = WS / repo['path']
    assert git('rev-parse', 'HEAD', cwd=path).decode().strip() == repo['head']
    assert git('status', '--porcelain', cwd=path) == b''
    subprocess.run(['git', 'merge-base', '--is-ancestor', repo['head'], BASE], cwd=ROOT, check=True)
    for row in repo['files']:
        data = (path / row['path']).read_bytes()
        assert sha(data) == row['sha256'] and len(data) == row['bytes'], row['path']
    originals.append({'path': repo['path'], 'head': repo['head'], 'verified_files': len(repo['files'])})
assert sum(row['verified_files'] for row in originals) == 953
archive = inventory['monograph_archive']
data = (WS / archive['path']).read_bytes()
assert sha(data) == archive['sha256'] and len(data) == archive['bytes']
reference_hash = sha((ROOT / 'book/reference/polyhedral_volumes_and_geodesic_identities.pdf').read_bytes())
assert reference_hash == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5'

old_full = expand(git('show', BASE + ':' + MAIN), lambda name: git('show', BASE + ':' + name))
new_full = expand((ROOT / MAIN).read_bytes(), lambda name: (ROOT / name).read_bytes())
label_pattern = rb'\\label\{([^{}]+)\}'
old_labels, new_labels = re.findall(label_pattern, old_full), re.findall(label_pattern, new_full)
assert old_labels == new_labels and len(new_labels) == len(set(new_labels)) == 607
chapter_labels = re.findall(label_pattern, new_chapter)
assert chapter_labels == re.findall(label_pattern, old_chapter) and len(chapter_labels) == 21
ledger_labels = [label for row in new_ledger['claims'] for label in row['labels']]
assert set(ledger_labels) == {label.decode() for label in chapter_labels}
bib_pattern = rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}'
assert re.findall(bib_pattern, old_full) == re.findall(bib_pattern, new_full)
assert len(set(re.findall(bib_pattern, new_full))) == 129

status = git('status', '--porcelain', '--untracked-files=all').decode().splitlines()
assert {line[3:] for line in status} == set(expected), status
subprocess.run(['git', 'diff', '--check'], cwd=ROOT, check=True)
links, deferred = [], set()
planned = {'docs/execution/section15-analytic-review-2026-11-01/README.md',
           'artifacts/section15_quantum/result.json',
           'artifacts/section15-analytic-review-2026-11-01/monograph-working-draft.pdf'}
for name in sorted(path for path in expected if path.endswith('.md')):
    for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', (ROOT / name).read_text()):
        target = match[1].split('#', 1)[0]
        if not target or re.match(r'^[a-zA-Z][\w+.-]*:', target):
            continue
        resolved = (ROOT / name).parent.joinpath(target).resolve()
        # The accepted plan already links absolute local skill instructions.
        # Those links are read-only existing targets, never planned outputs.
        if not resolved.is_relative_to(ROOT):
            assert Path(target).is_absolute() and resolved.exists(), (name, target)
        if not resolved.exists():
            missing = str(resolved.relative_to(ROOT))
            assert missing in planned, (name, target)
            deferred.add(missing)
        links.append({'source': name, 'target': target})
save('integration-checks.json', {
    'generated_at_utc': now, 'checks_passed': True, 'baseline_commit': BASE,
    'source_paths': 12, 'modified_baseline_paths': 8, 'new_paths': 4,
    'source_identities': source_identities, 'baseline_tracked_paths': 1851,
    'protected_baseline_paths': len(protected), 'protected_lfs_files': lfs,
    'protected_inventory_sha256': sha(json.dumps(preserved, sort_keys=True).encode()),
    'original_repositories': originals, 'original_archive_sha256': archive['sha256'],
    'supplied_reference_pdf_sha256': reference_hash,
    'historical_table_sha256': sha((ROOT / 'experiments/section15/historical-table.json').read_bytes()),
    'prior_section15_result_sha256': sha((ROOT / 'artifacts/section15/checks.json').read_bytes()),
    'labels_preserved_in_order': 607, 'chapter_labels_preserved_in_order': 21,
    'bibliography_keys_preserved_in_order': 129, 'section15_ledger_claims': 14,
    'section15_ledger_unique_labels': len(set(ledger_labels)),
    'section15_ledger_label_multiplicities': dict(collections.Counter(ledger_labels)),
    'local_links_checked': len(links), 'planned_missing_targets': sorted(deferred),
    'status_porcelain': status, 'diff_check_passed': True,
    'scope': 'Independent source preservation, numerical delta, label coverage and local links. Final PDF review and clean-source numerical generation are separate gates.',
})
print(json.dumps({'checks_passed': True, 'source_paths': 12, 'protected_baseline_paths': len(protected),
                  'protected_lfs_files': lfs, 'original_files': 953, 'labels': 607,
                  'section15_claims': 14, 'maximum_reference_difference': str(max_ref),
                  'local_links_checked': len(links), 'planned_missing_targets': sorted(deferred)}, indent=2))
