"""Independent bounded follow-up; preserves the original failure artifacts."""

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

OUT = Path('/Volumes/Lexar/lambda/devel/polyhedra/execution/numerical-correctness-2026-10-31')
original_script = OUT / 'service-review-probe.py'
original_failure = OUT / 'service-review-probe.json'
before = {p.name: sha256(p.read_bytes()).hexdigest()
          for p in (original_script, original_failure)}
source = original_script.read_text()
assert source.count('service-review-probe.json') == 2
replay = source.replace('service-review-probe.json', 'service-review-callback-original-replay.json')
namespace = {'__name__': '__main__', '__file__': str(original_script)}
exec(compile(replay, str(original_script), 'exec'), namespace)

np = namespace['np']
opt = namespace['opt']
patch = namespace['patch']
solver = namespace['solver']
run_controlled = namespace['run_controlled']
payload = namespace['payload']
REGULAR = namespace['REGULAR']
RIGHT = namespace['RIGHT']
REGULAR_VOLUME = namespace['REGULAR_VOLUME']
replayed = json.loads((OUT / 'service-review-callback-original-replay.json').read_text())
case = replayed['callback_mutation_regression']
assert case['params_match_returned_vertices'] is True
assert case['callback_diagnostics_mutated_internal_record'] is False
assert case['best_volume'] == case['volume_recomputed_from_best_params']
assert case['best_volume'] == case['volume_recomputed_from_returned_vertices']
assert case['serialized_trial']['validation']['cached_objective'] == -REGULAR_VOLUME

evidence = {
    'original_artifact_sha256_before': before,
    'original_replay_script_change': 'Only redirect the two output filename occurrences',
    'executed_original_replay_sha256': sha256(replay.encode()).hexdigest(),
    'original_replay_output': 'service-review-callback-original-replay.json',
    'original_callback_case_passed': True,
    'source_sha256': replayed['source_sha256'],
    'imports': replayed['imports'],
    'source_matches_author_manifest': replayed['source_matches_author_manifest'],
    'source_unchanged_during_original_replay': replayed['source_unchanged_during_probe'],
}

cases = []
for delay in (False, True):
    retained = []

    def callback(snapshot):
        retained.append(snapshot)
        if delay and len(retained) == 1:
            return
        for old in retained:
            old.params[:] = np.nan
            old.validation.clear()
            old.validation.update({
                'status': 'rejected',
                'nested_raw_diagnostics': {'values': [np.nan]},
            })
            old.validation['nested_raw_diagnostics']['values'].append(np.inf)

    result = run_controlled([
        solver(REGULAR, -REGULAR_VOLUME, success=False),
        solver(RIGHT, -100, success=True),
    ], trial_callback=callback)
    data = payload(result)
    assert np.array_equal(result.best_params, REGULAR)
    assert np.array_equal(result.finite_vertices, opt.parameters_to_complex(REGULAR, 4))
    assert result.best_volume == namespace['volume'](result.best_params)
    assert [t.success for t in result.trials] == [False, True]
    for trial, snapshot, params, score in zip(
        result.trials, retained, [REGULAR, RIGHT], [-REGULAR_VOLUME, -100]
    ):
        assert snapshot is not trial
        assert not np.shares_memory(snapshot.params, trial.params)
        assert snapshot.validation is not trial.validation
        assert np.array_equal(trial.params, params)
        assert trial.volume == namespace['volume'](trial.params)
        assert trial.validation['status'] == 'verified'
        assert trial.validation['cached_objective'] == score
        assert 'nested_raw_diagnostics' not in trial.validation
    cases.append({'mutate_retained_reference_only_on_later_trial': delay,
                  'all_snapshot_alias_checks_passed': True, 'result': data})
evidence['immediate_and_delayed_nonfinite_mutations'] = cases

# Current production diagnostics contain scalars. Introduce a controlled nested
# diagnostic at construction solely to verify recursive isolation if mutable
# diagnostic values are added later. This synthetic record is not a v2 fixture.
real_trial_type = opt.OptimizationTrial
synthetic_internal = []
synthetic_snapshots = []

def nested_trial_factory(**kwargs):
    kwargs['validation']['synthetic_nested'] = {'scores': [3.0], 'array': np.array([4.0])}
    trial = real_trial_type(**kwargs)
    synthetic_internal.append(trial)
    return trial

def mutate_nested(snapshot):
    synthetic_snapshots.append(snapshot)
    nested = snapshot.validation['synthetic_nested']
    nested['scores'][0] = -99.0
    nested['array'][0] = -98.0

with patch.object(opt, 'OptimizationTrial', side_effect=nested_trial_factory):
    synthetic = run_controlled([solver(REGULAR, -REGULAR_VOLUME)], trial_callback=mutate_nested)
original_nested = synthetic_internal[0].validation['synthetic_nested']
copied_nested = synthetic_snapshots[0].validation['synthetic_nested']
assert original_nested is not copied_nested
assert original_nested['scores'] is not copied_nested['scores']
assert not np.shares_memory(original_nested['array'], copied_nested['array'])
assert original_nested['scores'] == [3.0]
assert original_nested['array'].tolist() == [4.0]
evidence['synthetic_existing_nested_diagnostic_isolation'] = {
    'scope': 'Controlled added diagnostic, not a production schema fixture',
    'nested_mapping_and_list_distinct': True,
    'nested_numpy_array_does_not_share_memory': True,
    'original_scores': original_nested['scores'],
    'original_array': original_nested['array'].tolist(),
    'callback_scores': copied_nested['scores'],
    'callback_array': copied_nested['array'].tolist(),
}
after = {p.name: sha256(p.read_bytes()).hexdigest()
         for p in (original_script, original_failure)}
assert before == after
evidence['original_failure_artifacts_preserved'] = True
evidence['original_artifact_sha256_after'] = after
PACKAGE = namespace['PACKAGE']
assert all(sha256((PACKAGE / p).read_bytes()).hexdigest() == h
           for p, h in replayed['source_sha256'].items())
evidence['owned_source_unchanged_through_followup'] = True
(OUT / 'service-review-callback-recheck.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
print(json.dumps({'independent_callback_followup': 'passed',
                  'original_failure_artifacts_preserved': True}, indent=2))
