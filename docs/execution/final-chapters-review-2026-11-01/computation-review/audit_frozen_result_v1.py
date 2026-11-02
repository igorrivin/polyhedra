"""Independently audit frozen result records and exact reviewer replay identity."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import mpmath

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


author_path = HERE/'subject-v1/author-result-70-110.json'
reviewer_path = HERE/'independent-replay-result.json'
author = json.loads(author_path.read_bytes())
reviewer = json.loads(reviewer_path.read_bytes())
changed = sorted(differences(author, reviewer))
require(changed == ['/generated_at_utc', '/runtime/elapsed_seconds'], 'unexpected replay scientific/source difference')
source = author['source_before']
require(source == author['source_after'] == reviewer['source_before'] == reviewer['source_after'], 'source maps differ')
require(source == run.source_state(run.load_fixture()), 'source changed since independent replay')
ctx = mpmath.mp.clone()
ctx.dps = 300
counts = {'exact': 0, 'numerical_formula_comparisons': 0, 'cross_precision_observations': 0}
group_records = {}
for name, group in author['groups'].items():
    entry = {'exact': 0, 'numerical_formula_comparisons': 0, 'cross_precision_observations': 0,
             'precision_runs': []}
    if 'exact' in group:
        records = group['exact']['records']
        require(len(records) == group['exact']['check_count'], name+' exact count')
        for record in records:
            require(record.get('exact_residual') == '0' or record.get('exact_condition') is True, name+' failed exact record')
        entry['exact'] = len(records)
    if 'numerical' in group:
        numerical = group['numerical']
        for values in numerical['runs']:
            records = values['records']
            require(len(records) == values['check_count'], name+' numerical count')
            tolerance = ctx.mpf(values['scaled_tolerance'])
            d, guard, actual = (values[k] for k in ('requested_decimal_digits', 'guard_digits', 'actual_decimal_digits'))
            require(actual == d+guard, name+' actual precision')
            require(abs(tolerance/ctx.power(10, -(d-15))-1) < ctx.mpf('1e-80'), name+' tolerance')
            positive_records = bounded_records = 0
            worst_relative = ctx.mpf(0)
            for record in records:
                scale, residual, relative = (ctx.mpf(record[k]) for k in ('scale', 'absolute_residual', 'scaled_residual'))
                require(all(ctx.isfinite(v) for v in (scale, residual, relative)) and scale > 0 and residual >= 0 and relative >= 0,
                        name+' invalid residual or scale')
                if 'analytic_bound' in record:
                    bound = ctx.mpf(record['analytic_bound'])
                    budget = ctx.mpf(record['uncertified_floating_budget'])
                    require(bound >= 0 and budget > 0 and ctx.isfinite(bound) and ctx.isfinite(budget), name+' invalid separate bound')
                    require(residual <= (bound+budget)*(1+ctx.mpf('1e-60')), name+' bounded residual')
                    bounded_records += 1
                else:
                    require(relative <= tolerance, name+' scaled residual exceeds threshold')
                    worst_relative = max(worst_relative, relative)
                positive_records += bool(record['positive_signal'])
            for item in values['observations'].values():
                value = ctx.mpf(item['value'])
                require(ctx.isfinite(value), name+' nonfinite observation')
                if item['positive_signal']:
                    require(value > 0, name+' positive observation lost')
            entry['precision_runs'].append({'requested': d, 'guards': guard, 'actual': actual,
                                            'records': len(records), 'positive_relative_records': positive_records,
                                            'analytic_bound_records': bounded_records,
                                            'maximum_unbounded_scaled_residual': ctx.nstr(worst_relative, 40)})
            entry['numerical_formula_comparisons'] += len(records)
        comparison = numerical['cross_precision']
        require(len(comparison['records']) == comparison['comparison_count'], name+' cross-precision count')
        require(comparison['comparison_count'] == len(numerical['runs'][0]['observations']) == len(numerical['runs'][1]['observations']), name+' observation coverage')
        for record in comparison['records']:
            require(ctx.isfinite(ctx.mpf(record['scaled_residual'])) and 0 <= ctx.mpf(record['scaled_residual']) <= ctx.mpf(comparison['scaled_tolerance']), name+' cross-precision residual')
        entry['cross_precision_observations'] = len(comparison['records'])
    for key in counts:
        counts[key] += entry[key]
    group_records[name] = entry
require(counts == author['check_counts'] == {'exact': 1342, 'numerical_formula_comparisons': 4266, 'cross_precision_observations': 509}, 'total count mismatch')

contracts = ROOT/'experiments/quantum_geodesics/contracts'
f = author['fixture']
expected_provenance = {
    'quantum-targets.md': f['formula_contracts']['quantum']['sha256'],
    'quantum-source-freeze.json': f['formula_contracts']['quantum']['accepted_source_freeze_sha256'],
    'quantum-mathematical-acceptance.json': f['formula_contracts']['quantum']['review_acceptance_sha256'],
    'geodesic-targets.md': f['formula_contracts']['geodesic']['sha256'],
    'geodesic-contract-acceptance.json': f['formula_contracts']['geodesic']['review_acceptance_sha256'],
    'geodesic-source-acceptance.json': f['formula_contracts']['geodesic']['final_source_review_sha256'],
}
for file, expected in expected_provenance.items():
    require(identity(contracts/file)['sha256'] == expected, file+' does not match provenance')

result = {
    'status': 'passed_independent_v1_record_and_replay_audit',
    'author_result': identity(author_path), 'reviewer_result': identity(reviewer_path),
    'replay_changed_paths': changed, 'scientific_results_exactly_equal_as_JSON_strings': True,
    'before_after_current_source_equal': True, 'source_set_sha256': source['source_set_sha256'],
    'derived_counts': counts, 'groups': group_records,
    'runtime_sha256': {r['path']: r['sha256'] for r in source['sources']+source['guarded_dependencies']},
    'author_manuscript_sha256': {r['path']: r['current_sha256'] for r in source['live_manuscript_observation']},
    'author_tex_sha256': {r['path']: r['sha256'] for r in source['live_tex_source_observations']},
    'live_TeX_scope': '46 observed book TeX files: 36 active inputs and 10 preserved inactive figure/preamble fragments',
    'local_provenance_sha256': expected_provenance,
    'source_stage': 'dirty author/reviewer source; not a clean-source checkpoint replay',
    'limits': ['No interval enclosure or achieved-digit guarantee.',
               'Analytic truncation bounds remain distinct from uncertified roundoff and quadrature.',
               'Current fixture is complete; negative-control validation findings remain separately open.'],
}
with (HERE/'result-audit-v1.json').open('x') as handle:
    json.dump(result, handle, indent=2)
    handle.write('\n')
print(json.dumps({'status': result['status'], 'counts': counts, 'changed_paths': changed}))
