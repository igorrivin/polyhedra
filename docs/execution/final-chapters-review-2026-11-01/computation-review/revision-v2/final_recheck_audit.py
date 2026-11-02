"""Bind the targeted repair review to the actual author and reviewer results."""
import ast
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
sys.path.insert(0, str(ROOT))
from experiments.quantum_geodesics import run


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def identity(path):
    data = path.read_bytes()
    return {'sha256': sha256(data).hexdigest(), 'bytes': len(data)}


def differences(left, right, path=''):
    if type(left) is not type(right):
        return [path]
    if isinstance(left, dict):
        return ([path+'/'+k for k in left.keys() ^ right.keys()]
                + [p for k in left.keys() & right.keys() for p in differences(left[k], right[k], path+'/'+k)])
    if isinstance(left, list):
        if len(left) != len(right):
            return [path]
        return [p for i, (a, b) in enumerate(zip(left, right)) for p in differences(a, b, path+'/'+str(i))]
    return [] if left == right else [path]


author = json.loads((HERE/'subject/author-result-70-110.json').read_bytes())
reviewer = json.loads((HERE/'independent-replay-result.json').read_bytes())
freeze = json.loads((HERE/'subject/source-freeze.json').read_bytes())
initial = json.loads((HERE/'initial-freeze-and-comparison.json').read_bytes())
diffs = sorted(differences(author, reviewer))
require(diffs == ['/generated_at_utc', '/runtime/elapsed_seconds'], 'unexpected author/reviewer difference')
current = run.source_state(run.load_fixture())
require(current == author['source_before'] == author['source_after'] == reviewer['source_before'] == reviewer['source_after'] == freeze['source'], 'source observations changed')
for relative, expected in initial['accepted_runtime_sha256'].items():
    require(identity(ROOT/relative)['sha256'] == expected, 'runtime changed: '+relative)
    require(identity(HERE/'subject'/relative)['sha256'] == expected, 'subject snapshot changed: '+relative)

old_manifest = json.loads((HERE.parent/'review-v1-evidence-manifest.json').read_bytes())
for relative, expected in old_manifest['files'].items():
    require(identity(HERE.parent/relative) == expected, 'v1 evidence changed: '+relative)
require(identity(HERE.parent/'review-v1.json')['sha256'] == freeze['independent_review_sha256'], 'author pin to v1 decision')
require(identity(HERE.parent/'review-v1-evidence-manifest.json')['sha256'] == freeze['independent_review_manifest_sha256'], 'author pin to v1 manifest')
require(identity(HERE.parent/'required-fixture-profile-v1.json')['sha256'] == freeze['independent_required_profile_sha256'], 'author pin to v1 profile')

normal = json.loads((HERE/'targeted-controls-normal.json').read_bytes())
optimized = json.loads((HERE/'targeted-controls-optimized.json').read_bytes())
require(normal['records'] == optimized['records'], 'optimized rejection behavior changed')
require(normal['positive_and_observation_controls'] == optimized['positive_and_observation_controls'], 'optimized positive/observation behavior changed')
require(len(normal['records']) == 253 and all(r['rejected'] and r['before_source_and_calculation'] and r['no_output'] for r in normal['records']), 'targeted gate failures')
commands = json.loads((HERE/'command-receipts.json').read_bytes())
require(all(c['returncode'] == 0 for c in commands['commands']), 'independent command failed')
test_counts = {}
for mode in ('normal', 'optimized'):
    log = (HERE/('tests-'+mode+'.stderr.txt')).read_text()
    match = re.search(r'Ran (\d+) tests', log)
    require(match is not None and int(match.group(1)) == 50 and log.rstrip().endswith('OK'), mode+' test receipt')
    test_counts[mode] = int(match.group(1))
production_asserts = []
for file in (ROOT/'experiments/quantum_geodesics').rglob('*.py'):
    if 'tests' not in file.parts:
        production_asserts.extend({'path': str(file.relative_to(ROOT)), 'line': node.lineno}
                                  for node in ast.walk(ast.parse(file.read_text())) if isinstance(node, ast.Assert))
require(not production_asserts, 'runtime assertions introduced')

summary = {'schema_version': 1, 'status': 'passed_targeted_independent_recheck',
           'source_set_sha256': current['source_set_sha256'],
           'author_result': identity(HERE/'subject/author-result-70-110.json'),
           'independent_replay_result': identity(HERE/'independent-replay-result.json'),
           'replay_difference_paths': diffs, 'scientific_strings_exactly_equal': True,
           'full_source_before_after_current_equal': True, 'all_v1_evidence_preserved': True,
           'source_freeze_and_profile_links_match': True,
           'targeted_rejections_per_mode': len(normal['records']),
           'targeted_categories': dict(Counter(r['category'] for r in normal['records'])),
           'positive_and_observation_controls': normal['positive_and_observation_controls'],
           'normal_and_optimized_probe_records_equal': True, 'test_counts': test_counts,
           'ruff': 'passed', 'production_assert_count': len(production_asserts),
           'derived_counts': initial['derived_counts'], 'oracle_reuse': initial['oracles'],
           'closed_findings': ['CR01', 'CR02'], 'open_required_findings': [],
           'source_stage': 'dirty author and independent reviewer replay; clean-source checkpoint remains separate'}
with (HERE/'final-recheck-audit.json').open('x') as handle:
    json.dump(summary, handle, indent=2)
    handle.write('\n')
print(json.dumps({'status': summary['status'], 'closed': summary['closed_findings'],
                  'tests': test_counts, 'targeted_rejections_per_mode': len(normal['records']),
                  'replay_difference_paths': diffs}))
