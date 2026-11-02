"""Reviewer-owned adverse-input probes; no canonical files are changed.

Coverage omissions are run through the public fixture gate and the affected
group. An accepted mutation is evidence of a gate gap, not of a wrong value in
the frozen author result. Normal and -O executions are separately recorded.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from experiments.quantum_geodesics import common, geodesic_exact, geometry, kernels, klein, normalization, run

baseline = run.load_fixture()
records = []


def attempt(name, function, expected_rejection=True):
    item = {'name': name, 'expected_rejection': expected_rejection}
    try:
        value = function()
        item.update(rejected=False, summary=value)
    except (ArithmeticError, ValueError, TypeError, KeyError, SystemExit) as error:
        item.update(rejected=True, exception=type(error).__name__, message=str(error))
    item['expected_behavior'] = item['rejected'] == expected_rejection
    records.append(item)


def coverage(name, mutate, check):
    data = deepcopy(baseline)
    mutate(data)
    def operation():
        run.validate_fixture(data)
        value = check(data)
        return {'fixture_gate': 'accepted', 'affected_group': value}
    attempt(name, operation)


coverage('Q3_missing_negative_q',
         lambda f: f['quantum']['peripheral'].__setitem__('slopes', f['quantum']['peripheral']['slopes'][:-1]),
         lambda f: {'checks': normalization.peripheral_checks(f['quantum']['peripheral'], f['guarded_dependency_sha256'])['check_count']})
coverage('Q2_three_duplicate_simplexes_replace_boxes',
         lambda f: f['quantum']['klein'].__setitem__('polyhedra', [deepcopy(f['quantum']['klein']['polyhedra'][0]) for _ in range(3)]),
         lambda f: {'checks': klein.exact_checks(f['quantum']['klein'])['check_count']})
coverage('G7_required_large_L_replaced_by_N_zero',
         lambda f: f['geodesic']['partition'].__setitem__('large_partition', {'a': '7', 'tau': '0', 'N': 0}),
         lambda f: {'checks': kernels.twist_checks(f['geodesic']['partition'], 70, 20)['check_count']})
coverage('G8_missing_shifted_nonstationary_case',
         lambda f: f['geodesic']['matching'].__setitem__('stationarity', f['geodesic']['matching']['stationarity'][:1]),
         lambda f: {'checks': geometry.matching_checks(f['geodesic']['matching'], 70, 20)['check_count']})
coverage('G8_missing_inconsistent_endpoint_spacing',
         lambda f: f['geodesic']['matching'].__setitem__('endpoint_lists', f['geodesic']['matching']['endpoint_lists'][:1]),
         lambda f: {'checks': geodesic_exact.position_checks(f['geodesic']['matching'])['check_count']})
coverage('provenance_empty_formula_contracts',
         lambda f: f.__setitem__('formula_contracts', {}),
         lambda f: {'contracts': len(f['formula_contracts'])})
coverage('provenance_empty_accepted_manuscript_map',
         lambda f: f.__setitem__('accepted_manuscript_sha256', {}),
         lambda f: {'observations': len(run.source_state(f)['live_manuscript_observation'])})

coverage('existing_Q1_partial_grid_guard',
         lambda f: f['quantum']['figure_eight_N'].pop(), lambda f: {})
coverage('existing_G10_partial_grid_guard',
         lambda f: f['geodesic']['shadow']['distances'].pop(), lambda f: {})
coverage('existing_Q3_missing_dependency_guard',
         lambda f: f['guarded_dependency_sha256'].pop('experiments/quantum_surgery/exact.py'),
         lambda f: normalization.peripheral_checks(f['quantum']['peripheral'], f['guarded_dependency_sha256']))

for text in ('{"x":1,"x":2}', '{"a":{"x":1,"x":2}}', '{"x":NaN}',
             '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e9999}', '{"x":0.1}'):
    attempt('parse_reject_'+text, lambda text=text: run.parse_fixture(text))
for value in ('nan', 'inf', '-inf', '1/0', 'sqrt(2)', True, 0.1):
    attempt('exact_reject_'+repr(value), lambda value=value: str(common.rational(value)))

for digits in (70, 110):
    ctx = common.context(digits, 20)
    signal = ctx.mpf('1e-1000')
    for label, value in [('zero', ctx.mpf(0)), ('half', signal/2), ('negative', -signal),
                         ('nan', ctx.nan), ('infinity', ctx.inf)]:
        attempt(f'positive_{digits}_{label}', lambda value=value: common.NumericChecks(ctx, digits, 20).positive('reviewer tiny signal', value, signal))
    attempt(f'positive_{digits}_retained', lambda: common.NumericChecks(ctx, digits, 20).positive('retained', signal, signal), False)

ctx = common.context(70, 20)
for name, function in [('h_trace_boundary', lambda: kernels.h_trace(ctx, 2)),
                       ('kernel_boundary', lambda: kernels.kernel_partial(ctx, 6, 4)),
                       ('distance_zero_separation', lambda: geometry.local_distance(ctx, 0, 0, 0)),
                       ('acosh_below_domain', lambda: geometry.acosh_real(ctx, ctx.mpf('.999'))),
                       ('torus_zero_cuff', lambda: geometry.torus_length(ctx, 0, 0, 0)),
                       ('shadow_zero_distance', lambda: kernels.shadow(ctx, 0))]:
    attempt(name, function)

with tempfile.TemporaryDirectory(prefix='quantum-geodesics-review-', dir='/private/tmp') as directory:
    output = Path(directory)/'exclusive.json'
    run.write_result(output, {'sentinel': 7})
    before = output.read_bytes()
    try:
        run.write_result(output, {'sentinel': 8})
    except FileExistsError:
        records.append({'name': 'exclusive_output_creation', 'expected_behavior': output.read_bytes() == before,
                        'rejected': True, 'expected_rejection': True})
    else:
        records.append({'name': 'exclusive_output_creation', 'expected_behavior': False, 'rejected': False})
    missing = Path(directory)/'missing'
    link = Path(directory)/'dangling.json'
    link.symlink_to(missing)
    attempt('dangling_output_symlink', lambda: run.main(['--output', str(link)]))
    records[-1]['missing_target_still_absent'] = not missing.exists()

result = {'schema_version': 1, 'review_role': 'independent adverse-input probe',
          'optimized': bool(sys.flags.optimize), 'source_set_sha256': run.source_state(baseline)['source_set_sha256'],
          'frozen_author_result_sha256': sha256((HERE/'subject-v1/author-result-70-110.json').read_bytes()).hexdigest(),
          'records': records, 'unexpected_acceptances': [r['name'] for r in records if not r['expected_behavior']],
          'scope': 'Mutated fixture objects only; no canonical source/result mutation. Existing frozen coverage is complete.'}
destination = HERE/('negative-controls-optimized-v1.json' if sys.flags.optimize else 'negative-controls-normal-v1.json')
with destination.open('x') as handle:
    json.dump(result, handle, indent=2)
    handle.write('\n')
print(json.dumps({'records': len(records), 'unexpected_acceptances': result['unexpected_acceptances'], 'output': str(destination)}))
