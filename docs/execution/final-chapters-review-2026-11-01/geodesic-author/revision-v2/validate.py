"""Static validation of R1/R2 only; no scientific experiment or PDF operation."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
REV = Path(__file__).resolve().parent
AUTHOR = REV.parent
REVIEW = AUTHOR.parent/'geodesic-review'
BASE = '151673b1817e66aae493eb7da1be5ddf49adfe0f'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
initial = json.loads((AUTHOR/'author-freeze-manifest.json').read_text())
review = json.loads((REVIEW/'initial-review-manifest.json').read_text())
owned = list(initial['canonical_sources_sha256'])
old = json.loads((REV/'before/book/claims/sections17-22.json').read_text())
new = json.loads((ROOT/'book/claims/sections17-22.json').read_text())
expected_changed = ['book/chapters/19-pants-twists.tex', 'book/chapters/22-cusps-orthospectrum.tex',
                    'book/claims/sections17-22.json']
changed = []
commands = []
label = lambda s: re.findall(r'\\label\{([^}]+)\}', s)
heading = lambda s: re.findall(r'\\(?:section|subsection|subsubsection)\*?\{[^\n]+', s)
display = lambda s: re.findall(r'\\\[.*?\\\]|\\begin\{(?:equation\*?|align\*?|proof)\}.*?\\end\{(?:equation\*?|align\*?|proof)\}', s, re.S)

for filename in owned:
    assert sha(REV/'before'/filename) == initial['canonical_sources_sha256'][filename]
    assert (REV/'after'/filename).read_bytes() == (ROOT/filename).read_bytes()
    if (REV/'before'/filename).read_bytes() != (ROOT/filename).read_bytes():
        changed.append(filename)
    data = (ROOT/filename).read_bytes()
    assert data.endswith(b'\n') and not data.endswith(b'\n\n'), filename
    cmd = ['git', 'diff', '--no-index', '--check', '/dev/null', filename]
    p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    assert p.returncode in (0, 1) and not p.stdout and not p.stderr, filename
    commands.append({'argv': cmd, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
    if filename.endswith('.tex'):
        before, after = (REV/'before'/filename).read_text(), (ROOT/filename).read_text()
        assert label(before) == label(after)
        assert heading(before) == heading(after)
        assert display(before) == display(after), filename
        assert sha(ROOT/filename) == new['chapter_source_snapshots'][filename]
assert changed == expected_changed, changed

# Reject unrelated ledger edits or accidental approval/computation status changes.
left, right = deepcopy(old), deepcopy(new)
for data in (left, right):
    for source in data['sources']:
        if source['key'] == 'MirzSimple':
            source.pop('pins'); source.pop('checked')
        if source['key'] == 'McShanePants':
            source.pop('pins')
    for claim in data['claims']:
        if claim['id'] == '19.01':
            claim.pop('source_pins')
        if claim['id'] == '19.09':
            claim.pop('hypotheses'); claim.pop('exact_formulas'); claim.pop('source_pins')
        if claim['id'] == '22.03':
            claim.pop('proof_summary'); claim.pop('source_pins')
    for filename in expected_changed[:2]:
        data['chapter_source_snapshots'].pop(filename)
assert left == right, 'Unexpected ledger delta'
assert len(new['claims']) == new['claim_count'] == 59
all_owned_labels = [x for f in new['chapter_sources'] for x in label((ROOT/f).read_text())]
assert len(all_owned_labels) == len(set(all_owned_labels)) == 54
assert new['preservation'] == old['preservation']
assert new['preservation']['baseline_label_count'] == 48
assert len(new['preservation']['new_labels']) == 6
assert Counter(new['chapter_labels']+[x for c in new['claims'] for x in c['labels']]) == Counter(all_owned_labels)
for source in new['sources']:
    if source['key'] == 'MirzSimple':
        assert any('Proposition 3.5' in x and '(3.7)' in x and '107' in x for x in source['pins'])
    if source['key'] == 'McShanePants':
        assert 'after Corollary 5, p. 5' in source['pins'][0]

# Preserve all initial author and review evidence, including accepted contract.
assert sha(AUTHOR/'author-freeze-manifest.json') == '38994ff43e952ff42ccafb4d56c44e51c385a0092d156e3d35cdbcf1041d7eec'
for path, expected in initial['outer_evidence_sha256'].items():
    assert sha(AUTHOR/path) == expected, path
for path, expected in review['initial_evidence_sha256'].items():
    assert sha(REVIEW/path) == expected, path
contract_sha = sha(AUTHOR/'companion-contract.md')
assert contract_sha == '2a62a149e7f5f88027329c24ba3a4720407debfed2fb78945350f23b6fce85a6'
assert sha(REVIEW/'companion-contract-review.json') == 'be7debaf190ecd960d0caeca6b82e884407b6da04e72234e16a60762980bc82b'


def expand(path, historical, seen):
    assert path not in seen
    seen.add(path)
    if historical:
        text = subprocess.run(['git', 'show', BASE+':'+path], cwd=ROOT, text=True,
                              capture_output=True, check=True).stdout
    else:
        text = (ROOT/path).read_text()
    def repl(match):
        child = str(Path(path).parent/match.group(1))
        return expand(child if child.endswith('.tex') else child+'.tex', historical, seen)
    return re.sub(r'\\input\{([^}]+)\}', repl, text)


current_seen, base_seen = set(), set()
current = expand('book/main.tex', False, current_seen)
baseline = expand('book/main.tex', True, base_seen)
base_labels, current_labels = label(baseline), label(current)
assert len(current_seen) == 36
assert len(base_labels) == 607
assert len(current_labels) == len(set(current_labels)) == 613
assert [x for x in current_labels if x in base_labels] == base_labels
assert [x for x in current_labels if x not in base_labels] == new['preservation']['new_labels']
bib = lambda text: re.findall(r'\\bibitem(?:\[[^]]*\])?\{([^}]+)\}', text)
assert len(bib(current)) == len(set(bib(current))) == 129
assert bib(current) == bib(baseline)
for filename in new['chapter_sources']:
    text = (ROOT/filename).read_text()
    for cites in re.findall(r'\\cite(?:\[[^]]*\])?\{([^}]+)\}', text):
        assert set(cites.split(',')) <= set(bib(current))
    assert set(re.findall(r'\\(?:ref|eqref)\{([^}]+)\}', text)) <= set(current_labels)
p = subprocess.run(['git', 'diff', '--check'], cwd=ROOT, text=True, capture_output=True)
assert p.returncode == 0 and not p.stdout and not p.stderr
commands.append({'argv': ['git', 'diff', '--check'], 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})

result = {
    'status': 'R1_R2_author_static_validation_passed_targeted_review_pending',
    'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'changed_canonical_paths': changed,
    'unchanged_other_owned_paths': [x for x in owned if x not in changed],
    'whitelisted_ledger_delta_only': True,
    'all_displayed_formulas_and_proof_environments_unchanged': True,
    'all_owned_labels_and_headings_unchanged': True,
    'claim_count': 59, 'owned_labels': 54, 'original_owned_labels': 48, 'existing_added_anchors': 6,
    'global_graph_observation': {'inputs_including_wrapper_and_main': 36, 'labels': 613,
        'baseline_607_labels_preserved_in_order': True, 'additional_labels': new['preservation']['new_labels'],
        'bibliography_keys': 129, 'bibliography_key_sequence_unchanged': True,
        'scope': 'Read-only observation, not approval of other authors or integration.'},
    'all_owned_files_single_final_newline': True,
    'all_initial_author_and_review_evidence_hashes_preserved': True,
    'initial_review_manifest_sha256': sha(REVIEW/'initial-review-manifest.json'),
    'accepted_contract_sha256_unchanged': contract_sha,
    'accepted_contract_review_record_sha256': sha(REVIEW/'companion-contract-review.json'),
    'commands': commands,
    'no_index_exit_note': 'Exit 1 with no diagnostic output is the expected new-file content-difference status; no whitespace errors.',
    'scientific_rerun': 'not performed or needed for this citation-only delta',
    'not_performed': ['PDF build or marker', 'stage or commit', 'installation', 'upload', 'unrelated canonical edits']}
(REV/'validation.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'status': result['status'], 'changed': changed, 'claims': 59, 'labels': 54,
                  'graph_inputs': 36, 'graph_labels': 613, 'bibkeys': 129}))
