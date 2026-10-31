"""Read-only independent service checks; includes a known callback regression.

Run from consolidated/packages/volume-toolkit with the supported baseline Python.
Controlled solver returns test a service boundary, not alleged SciPy behavior.
"""

from dataclasses import replace
from hashlib import sha256
import importlib.metadata
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra')
PACKAGE = ROOT / 'consolidated/packages/volume-toolkit'
OUT = ROOT / 'execution/numerical-correctness-2026-10-31'
sys.path.insert(0, str(PACKAGE))

import numpy as np
from jsonschema.validators import validator_for
from ideal_poly_volume_toolkit import geometry, optimization as opt
from ideal_poly_volume_toolkit import volume_threshold as threshold

REGULAR = np.array([math.pi / 2, math.pi / 3])
RIGHT = np.array([math.pi / 2, math.pi / 2])
REGULAR_VOLUME = 1.0149416064096537


def volume(params):
    return geometry.ideal_poly_volume_via_delaunay(
        opt.parameters_to_complex(params, 4), mode='bloch_wigner'
    )


def solver(params, cached, success=True, nfev=3):
    return SimpleNamespace(x=np.array(params), fun=cached, success=success,
                           nit=1, nfev=nfev, message='controlled review probe',
                           jac=np.zeros(2))


def run_controlled(results, **kwargs):
    with patch.object(opt, 'differential_evolution', side_effect=results):
        return opt.optimize_ideal_polyhedron(
            4, n_trials=len(results), maxiter=1, popsize=1, **kwargs
        )


def payload(result):
    data = opt.optimization_result_to_dict(result, source='independent-review')
    validate(data)
    return data


def validate(data):
    schema = json.loads((PACKAGE / 'docs/schemas' /
                         f"optimization-result-v{data['schema_version']}.schema.json").read_text())
    cls = validator_for(schema)
    cls.check_schema(schema)
    cls(schema).validate(data)
    json.dumps(data, allow_nan=False)


manifest = json.loads((OUT / 'optimization-service-summary.json').read_text())
hashes = {p: sha256((PACKAGE / p).read_bytes()).hexdigest()
          for p in manifest['owned_file_sha256']}
evidence = {
    'python': sys.version,
    'cwd': str(Path.cwd()),
    'imports': {m.__name__: str(Path(m.__file__).resolve())
                for m in (opt, geometry, threshold)},
    'versions': {n: importlib.metadata.version(n)
                 for n in ('numpy', 'scipy', 'mpmath', 'jsonschema')},
    'source_sha256': hashes,
    'source_matches_author_manifest': hashes == manifest['owned_file_sha256'],
    'geometry_sha256': sha256(Path(geometry.__file__).read_bytes()).hexdigest(),
}
assert all(str(PACKAGE) in p for p in evidence['imports'].values())
assert evidence['source_matches_author_manifest']

# The poorer true geometry has the better cached score; invalid final candidate
# must not displace the earlier regular tetrahedron.
ranked = run_controlled([
    solver(RIGHT, -1000), solver(REGULAR, -0.01, success=False),
    solver([math.nan, 1], -10000), solver([1.1], -10000),
])
ranked_data = payload(ranked)
assert np.array_equal(ranked.best_params, REGULAR)
assert math.isclose(ranked.best_volume, volume(ranked.best_params), abs_tol=1e-14)
assert np.array_equal(ranked.finite_vertices,
                      opt.parameters_to_complex(ranked.best_params, 4))
assert ranked.trials[1].success is False
assert ranked.trials[2].params.size == 0
assert ranked.trials[3].params.tolist() == [1.1]
assert ranked_data['statistics']['verification_evals'] == 2
evidence['fresh_ranking_and_quarantine'] = ranked_data

# Parallel service polish accepts the better geometry despite the worse cache,
# preserves raw DE nonconvergence and reports both verification evaluations.
with patch.object(opt, 'minimize', return_value=solver(REGULAR, -0.01, nfev=7)):
    polished = run_controlled([solver(RIGHT, -1000, success=False, nfev=11)], workers=2)
assert np.array_equal(polished.best_params, REGULAR)
assert polished.trials[0].success is False
assert polished.trials[0].function_evals == 18
assert polished.trials[0].verification_evals == 2
evidence['parallel_serial_polish'] = payload(polished)

legacy = replace(polished, trials=(replace(polished.trials[0],
                                          validation=None, verification_evals=0),))
legacy_data = payload(legacy)
assert legacy_data['all_trials'][0]['validation']['status'] == 'not_checked'
evidence['manual_legacy_status'] = legacy_data['all_trials'][0]['validation']['status']
try:
    opt.optimization_result_to_dict(polished, source='review', settings={'bad': math.nan})
except ValueError as exc:
    evidence['strict_json_rejection'] = str(exc)
else:
    raise AssertionError('nonfinite settings were accepted')

fixture_path = PACKAGE / 'tests/fixtures/optimization-result-v1.json'
fixture = json.loads(fixture_path.read_text())
validate(fixture)
assert fixture_path.read_bytes() == (ROOT / 'consolidated/docs/execution/2026-10-31/tetrahedron-cli.json').read_bytes()
assert set(fixture) <= set(ranked_data)
assert set(fixture['best']) <= set(ranked_data['best'])
assert set(fixture['all_trials'][0]) <= set(ranked_data['all_trials'][0])
evidence['historical_v1'] = {
    'valid': True, 'byte_identical_to_historical_artifact': True,
    'sha256': sha256(fixture_path.read_bytes()).hexdigest(),
    'schema_sha256': sha256((PACKAGE / 'docs/schemas/optimization-result-v1.schema.json').read_bytes()).hexdigest(),
    'historical_keys_preserved': True,
}

finite = [0j, 1 + 0j, np.exp(1j * math.pi / 3)]
threshold_errors = []
for terms in [math.nan, math.inf, -math.inf, True, np.bool_(False), 0, -2, 1.5]:
    try:
        threshold.get_volume(finite, series_terms=terms)
    except ValueError as exc:
        threshold_errors.append({'series_terms_repr': repr(terms), 'error': str(exc)})
    else:
        raise AssertionError(f'invalid series_terms accepted: {terms!r}')
evidence['additional_series_input_rejections'] = threshold_errors
assert math.isclose(threshold.get_volume(finite), REGULAR_VOLUME, abs_tol=2e-14)
assert math.isclose(threshold.get_volume(finite + [math.inf]), REGULAR_VOLUME, abs_tol=2e-14)

# Small real SciPy run verifies the normal path independently of mocks.
real = opt.optimize_ideal_polyhedron(4, n_trials=1, seed=321, maxiter=5, popsize=4)
assert math.isclose(real.best_volume, volume(real.best_params), abs_tol=1e-14)
assert np.array_equal(real.finite_vertices, opt.parameters_to_complex(real.best_params, 4))
assert real.trials[0].verification_evals == 1
evidence['real_scipy_run'] = payload(real)

# Supported callback mutation during optimization corrupts internal invariants.
# This deliberately does not mutate a completed result after it is returned.
def mutate_callback(trial):
    trial.params[1] = math.pi / 2
    trial.validation['cached_objective'] = -999.0
    trial.validation['reason'] = 'callback overwrote internal evidence'

callback_result = run_controlled(
    [solver(REGULAR, -REGULAR_VOLUME)], trial_callback=mutate_callback
)
callback_data = payload(callback_result)
evidence['callback_mutation_regression'] = {
    'best_volume': callback_result.best_volume,
    'best_params': callback_result.best_params.tolist(),
    'volume_recomputed_from_best_params': volume(callback_result.best_params),
    'volume_recomputed_from_returned_vertices': geometry.ideal_poly_volume_via_delaunay(
        callback_result.finite_vertices, mode='bloch_wigner'),
    'params_match_returned_vertices': bool(np.array_equal(
        opt.parameters_to_complex(callback_result.best_params, 4), callback_result.finite_vertices)),
    'serialized_trial': callback_data['all_trials'][0],
    'v2_schema_accepts_record': True,
    'callback_diagnostics_mutated_internal_record': callback_result.trials[0].validation['cached_objective'] == -999.0,
}
evidence['source_unchanged_during_probe'] = all(
    sha256((PACKAGE / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
)
assert evidence['source_unchanged_during_probe']
(OUT / 'service-review-probe.json').write_text(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
print(json.dumps({
    'ordinary_checks': 'passed',
    'callback_invariant_preserved': evidence['callback_mutation_regression']['params_match_returned_vertices'],
    'evidence': str(OUT / 'service-review-probe.json'),
}, indent=2))
