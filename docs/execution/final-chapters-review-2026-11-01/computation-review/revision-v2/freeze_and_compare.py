"""Freeze the repair subject and independently bind its exact limited delta."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
REVIEW = HERE.parent
OUTER = REVIEW.parent
ROOT = OUTER.parents[1]/'consolidated'
AUTHOR = OUTER/'computation/full-v2'
sys.path.insert(0, str(ROOT))
from experiments.quantum_geodesics import run


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def identity(path):
    data = path.read_bytes()
    return {'sha256': sha256(data).hexdigest(), 'bytes': len(data)}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


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


required = {
    'source-freeze.json': '2c89451d7d9f69d18cdd514b8244615498e2d8c5ba6c0963ba63f279c70ed037',
    'author-result-70-110.json': '5f73fce03e43103dc457570bcd90f4722599b5ac0d67a9b9b88d9e00679f0429',
    'scientific-comparison.json': 'b21ec307b97b11b73e83a2d28f37d6c870cf00a286492a1f9cf044b2df7ce617',
}
subject = HERE/'subject'
subject.mkdir(exist_ok=False)
for name, expected in required.items():
    require(identity(AUTHOR/name)['sha256'] == expected, name+' declared hash')
    (subject/name).write_bytes((AUTHOR/name).read_bytes())
for name in ('runtime-file-map.json', 'command-receipts.json'):
    (subject/name).write_bytes((AUTHOR/name).read_bytes())
freeze = json.loads((subject/'source-freeze.json').read_bytes())
result = json.loads((subject/'author-result-70-110.json').read_bytes())
previous = json.loads((REVIEW/'subject-v1/author-result-70-110.json').read_bytes())
source = freeze['source']
require(source == result['source_before'] == result['source_after'] == run.source_state(run.load_fixture()), 'full source before/after/current equality')
require(source['source_set_sha256'] == 'e5bd0a08c64db41e9d6ef5d06d8ef0be8a93bd58a7f4f79e75d7b792098087ed', 'source-set hash')
oldmap = {r['path']: r['sha256'] for r in previous['source_before']['sources']+previous['source_before']['guarded_dependencies']}
newmap = {r['path']: r['sha256'] for r in source['sources']+source['guarded_dependencies']}
require(len(oldmap) == 23 and len(newmap) == 24, 'runtime counts')
changed = sorted(p for p in oldmap.keys() & newmap.keys() if oldmap[p] != newmap[p])
added, removed = sorted(newmap.keys()-oldmap.keys()), sorted(oldmap.keys()-newmap.keys())
require(changed == ['experiments/quantum_geodesics/README.md', 'experiments/quantum_geodesics/run.py'], 'unexpected changed runtime source')
require(added == ['experiments/quantum_geodesics/tests/test_validation.py'] and not removed, 'unexpected added/removed runtime source')
for relative, expected in newmap.items():
    data = (ROOT/relative).read_bytes()
    require(sha256(data).hexdigest() == expected, relative+' live hash')
    target = subject/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
for key in ('groups', 'fixture', 'check_counts', 'arithmetic', 'coverage_limits', 'status', 'checks_passed'):
    require(canonical(result[key]) == canonical(previous[key]), 'scientific field changed: '+key)
require(source['live_manuscript_observation'] == previous['source_before']['live_manuscript_observation'], 'accepted/current manuscript observations changed')
require(source['live_tex_source_observations'] == previous['source_before']['live_tex_source_observations'], 'book TeX observations changed')
profile = json.loads((REVIEW/'required-fixture-profile-v1.json').read_bytes())
require(run.SCIENTIFIC_PROFILE_SHA256 == profile['scientific_profile_sha256'], 'scientific profile pin')
require(run.PROVENANCE_PROFILE_SHA256 == profile['provenance_profile_sha256'], 'provenance profile pin')
fixture = result['fixture']
for role, keys in [('scientific', ('precisions', 'guard_digits', 'quantum', 'geodesic')),
                   ('provenance', ('formula_contracts', 'accepted_manuscript_sha256', 'guarded_dependency_sha256'))]:
    require(sha256(canonical({k: fixture[k] for k in keys})).hexdigest() == profile[role+'_profile_sha256'], role+' canonical digest')

counts = {'exact': 0, 'numerical_formula_comparisons': 0, 'cross_precision_observations': 0}
group_ids = {}
for name, group in result['groups'].items():
    if 'exact' in group:
        require(len(group['exact']['records']) == group['exact']['check_count'], name+' exact count')
        counts['exact'] += len(group['exact']['records'])
    if 'numerical' in group:
        for values in group['numerical']['runs']:
            require(len(values['records']) == values['check_count'], name+' floating count')
            counts['numerical_formula_comparisons'] += len(values['records'])
        cross = group['numerical']['cross_precision']
        require(len(cross['records']) == cross['comparison_count'], name+' cross-precision count')
        counts['cross_precision_observations'] += len(cross['records'])
    group_ids[name] = sha256(canonical(group)).hexdigest()
require(counts == result['check_counts'], 'derived counts')
require(json.loads((subject/'runtime-file-map.json').read_bytes())['files'] == newmap, 'author runtime-map mismatch')

manifest = json.loads((REVIEW/'review-v1-evidence-manifest.json').read_bytes())
for relative, expected in manifest['files'].items():
    require(identity(REVIEW/relative) == expected, 'v1 evidence changed: '+relative)
oracles = json.loads((REVIEW/'independent-oracles-v1.json').read_bytes())
summary = {
    'schema_version': 1, 'recorded_at_utc': datetime.now(timezone.utc).isoformat(),
    'status': 'frozen_exact_bounded_repair_subject', 'source_set_sha256': source['source_set_sha256'],
    'author_records': {name: identity(subject/name) for name in required},
    'accepted_runtime_sha256': newmap, 'runtime_count': len(newmap),
    'changed_existing_paths': changed, 'added_paths': added, 'removed_paths': removed,
    'all_other_runtime_files_unchanged': True,
    'fixture_groups_and_huge_exponent_strings_exactly_equal_to_v1': True,
    'all_result_difference_paths_from_v1': sorted(differences(previous, result)),
    'derived_counts': counts, 'group_sha256': group_ids,
    'author_accepted_manuscript_sha256': fixture['accepted_manuscript_sha256'],
    'author_current_manuscript_sha256': {r['path']: r['current_sha256'] for r in source['live_manuscript_observation']},
    'author_tex_sha256': {r['path']: r['sha256'] for r in source['live_tex_source_observations']},
    'live_observation_maps_unchanged_from_v1': True,
    'all_v1_evidence_preserved': True,
    'oracles': {'reuse': True, 'freshly_rerun': False,
                'script': identity(REVIEW/'independent_oracles.py'), 'result': identity(REVIEW/'independent-oracles-v1.json'),
                'exact_count': oracles['exact_count'], 'numerical_count': oracles['numerical_count'],
                'reason': 'All mathematical modules, fixture, old guarded dependencies and every scientific result string are byte-identical to v1.'},
}
with (HERE/'initial-freeze-and-comparison.json').open('x') as handle:
    json.dump(summary, handle, indent=2)
    handle.write('\n')
print(json.dumps({'status': summary['status'], 'runtime_count': len(newmap), 'changed': changed, 'added': added, 'counts': counts}))
