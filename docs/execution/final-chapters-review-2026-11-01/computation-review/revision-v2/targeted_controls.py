"""Independent before-calculation regression probes for CR01 and CR02.

All mutations are in memory or mocked reads. No canonical file is changed.
Run normally and with -O, writing separate reviewer-owned evidence.
"""
from copy import deepcopy
from contextlib import nullcontext
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
sys.path.insert(0, str(ROOT))
from experiments.quantum_geodesics import run

fixture = run.load_fixture()
records = []


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def replace(data, path, value):
    target = data
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def retrieve(data, path):
    for key in path:
        data = data[key]
    return data


def reject(name, data, reader_patch=None, category='additional'):
    with tempfile.TemporaryDirectory(prefix='quantum-geodesics-v2-review-', dir='/private/tmp') as directory:
        output = Path(directory)/'must-not-exist.json'
        with patch.object(run, 'load_fixture', return_value=data), patch.object(run, 'source_state') as state, patch.object(run, 'calculate') as calculation:
            with reader_patch if reader_patch is not None else nullcontext():
                try:
                    run.main(['--output', str(output)])
                except (ValueError, FileNotFoundError) as error:
                    exception, message = type(error).__name__, str(error)
                else:
                    raise ArithmeticError(name+': malformed profile was accepted')
        require(not state.called and not calculation.called and not output.exists(), name+': failure reached source/calculation/output')
    records.append({'name': name, 'category': category, 'rejected': True, 'exception': exception,
                    'message': message, 'before_source_and_calculation': True, 'no_output': True})


original = [
    ('Q3_missing_negative_q', ('quantum', 'peripheral', 'slopes'), fixture['quantum']['peripheral']['slopes'][:-1]),
    ('Q2_three_duplicate_simplexes_replace_boxes', ('quantum', 'klein', 'polyhedra'), [deepcopy(fixture['quantum']['klein']['polyhedra'][0]) for _ in range(3)]),
    ('G7_required_large_L_replaced_by_N_zero', ('geodesic', 'partition', 'large_partition'), {'a': '7', 'tau': '0', 'N': 0}),
    ('G8_missing_shifted_nonstationary_case', ('geodesic', 'matching', 'stationarity'), fixture['geodesic']['matching']['stationarity'][:1]),
    ('G8_missing_inconsistent_endpoint_spacing', ('geodesic', 'matching', 'endpoint_lists'), fixture['geodesic']['matching']['endpoint_lists'][:1]),
    ('provenance_empty_formula_contracts', ('formula_contracts',), {}),
    ('provenance_empty_accepted_manuscript_map', ('accepted_manuscript_sha256',), {}),
    ('wrong_quantum_acceptance_hash', ('formula_contracts', 'quantum', 'review_acceptance_sha256'), '0'*64),
    ('wrong_quantum_source_freeze_hash', ('formula_contracts', 'quantum', 'accepted_source_freeze_sha256'), '0'*64),
    ('wrong_geodesic_contract_acceptance_hash', ('formula_contracts', 'geodesic', 'review_acceptance_sha256'), '0'*64),
    ('wrong_geodesic_source_acceptance_hash', ('formula_contracts', 'geodesic', 'final_source_review_sha256'), '0'*64),
    ('wrong_geodesic_accepted_source_set_hash', ('formula_contracts', 'geodesic', 'accepted_source_set_sha256'), '0'*64),
    ('wrong_accepted_manuscript_pin', ('accepted_manuscript_sha256', 'book/chapters/10-quantum-introduction.tex'), '0'*64),
]
for name, path, replacement in original:
    data = deepcopy(fixture)
    replace(data, path, deepcopy(replacement))
    reject(name, data, category='original_finding')


def arrays(value, path=()):
    result = []
    if isinstance(value, dict):
        for key, child in value.items():
            result.extend(arrays(child, path+(key,)))
    elif isinstance(value, list):
        if value:
            result.append(path)
        for index, child in enumerate(value):
            result.extend(arrays(child, path+(index,)))
    return result


scientific = {key: fixture[key] for key in run.SCIENTIFIC_PROFILE_KEYS}
for path in arrays(scientific):
    for action in ('remove_last', 'duplicate_first'):
        data = deepcopy(fixture)
        value = retrieve(data, path)
        if action == 'remove_last':
            value.pop()
        else:
            value.append(deepcopy(value[0]))
        reject('/'.join(map(str, path))+':'+action, data, category='every_scientific_array')

for map_name in ('accepted_manuscript_sha256', 'guarded_dependency_sha256'):
    for key in fixture[map_name]:
        data = deepcopy(fixture)
        del data[map_name][key]
        reject(map_name+':remove:'+key, data, category='every_source_or_dependency_pin')
    data = deepcopy(fixture)
    data[map_name]['unreviewed/path'] = '0'*64
    reject(map_name+':extra', data, category='every_source_or_dependency_pin')

for group, contract in fixture['formula_contracts'].items():
    for field in contract:
        data = deepcopy(fixture)
        del data['formula_contracts'][group][field]
        reject('contract:'+group+':remove:'+field, data, category='every_contract_field')
for path, value in [(('schema_version',), True), (('schema_version',), 2), (('scope',), ''),
                    (('scope',), []), (('guard_digits',), 19), (('precisions',), [70.0, 110]),
                    (('formula_contracts',), []), (('geodesic', 'guard_digits', 'kernel'), 99)]:
    data = deepcopy(fixture)
    replace(data, path, value)
    reject('schema_or_setting:'+str(path)+':'+repr(value), data, category='schema_and_settings')

files = ['quantum-targets.md', 'quantum-mathematical-acceptance.json', 'quantum-source-freeze.json',
         'geodesic-targets.md', 'geodesic-contract-acceptance.json', 'geodesic-source-acceptance.json']
original_read = Path.read_bytes
for filename in files:
    target = run.HERE/'contracts'/filename
    for mode in ('changed', 'missing'):
        def mocked_read(path, target=target, mode=mode):
            if path == target:
                if mode == 'missing':
                    raise FileNotFoundError('reviewer injected missing local provenance '+str(target))
                return original_read(path)+b'\n'
            return original_read(path)
        reject('local_copy:'+filename+':'+mode, deepcopy(fixture),
               patch.object(Path, 'read_bytes', mocked_read), category='six_local_provenance_bindings')

require(run.validate_fixture(deepcopy(fixture)) == fixture, 'valid fixture rejected')
reordered = {key: fixture[key] for key in reversed(fixture)}
require(run.validate_fixture(reordered) == fixture, 'dictionary order changed accepted profile')
validity = {'unchanged_profile_accepted': True, 'dictionary_order_irrelevant': True,
            'original_corruptions_rejected': len(original), 'targeted_rejections': len(records)}

baseline = run.source_state(fixture)
changed_paths = ['book/chapters/17-unfolding-constant-series.tex', 'book/claims/sections10-11.json']
target_paths = {ROOT/path for path in changed_paths}
def later_edit(path):
    data = original_read(path)
    return data+b'\n' if path in target_paths else data
with patch.object(Path, 'read_bytes', later_edit):
    modified = run.source_state(fixture)
    run.verify_source_unchanged(modified, run.source_state(fixture))
require(modified['sources'] == baseline['sources'] and modified['guarded_dependencies'] == baseline['guarded_dependencies'], 'live-edit test altered runtime observation')
observed_changes = []
for before, after in zip(baseline['live_manuscript_observation'], modified['live_manuscript_observation']):
    if before != after:
        require(after['path'] in changed_paths and not after['matches_accepted_snapshot'], 'unexpected manuscript observation')
        require(after['accepted_contract_source_sha256'] == before['accepted_contract_source_sha256'], 'accepted identity mutated by live source')
        observed_changes.append(after['path'])
require(set(observed_changes) == set(changed_paths), 'later edits did not appear in current map')
try:
    run.verify_source_unchanged(baseline, modified)
except ArithmeticError:
    midrun_change_rejected = True
else:
    raise ArithmeticError('mid-run manuscript change not rejected')
validity.update(later_live_manuscript_changes_observed=True, live_changed_paths=changed_paths,
                unchanged_observation_of_later_edit_passes=True, midrun_source_change_rejected=midrun_change_rejected,
                canonical_source_untouched=(baseline == run.source_state(fixture)))
require(validity['canonical_source_untouched'], 'canonical source changed during probes')
result = {'schema_version': 1, 'status': 'passed', 'optimized': bool(sys.flags.optimize),
          'source_set_sha256': baseline['source_set_sha256'], 'script_sha256': sha256(Path(__file__).read_bytes()).hexdigest(),
          'records': records, 'positive_and_observation_controls': validity,
          'scope': 'Independent driver gate probes only; mutations and changed/missing-file tests are in-memory mocks. No source edits or fresh alternate numerical oracle claim.'}
output = HERE/('targeted-controls-optimized.json' if sys.flags.optimize else 'targeted-controls-normal.json')
with output.open('x') as handle:
    json.dump(result, handle, indent=2)
    handle.write('\n')
print(json.dumps({'status': result['status'], 'optimized': result['optimized'], **validity}))
