"""Endpoint and serialization regressions at the solver/service boundary.

Controlled solver results exercise defensive contracts. They are not claims
that ordinary SciPy produces inconsistent objectives or malformed endpoints.
"""

from dataclasses import replace
from fractions import Fraction
import json
import math
from pathlib import Path
from types import SimpleNamespace

from jsonschema.validators import validator_for
import numpy as np
import pytest

from ideal_poly_volume_toolkit import optimization as opt
from ideal_poly_volume_toolkit import optimization_cli
from ideal_poly_volume_toolkit import volume_threshold as threshold


ROOT = Path(__file__).resolve().parents[1]
REGULAR = np.array([math.pi / 2, math.pi / 3])
REGULAR_VOLUME = 1.0149416064096537


def solver_result(params=REGULAR, *, fun=-REGULAR_VOLUME, success=True):
    return SimpleNamespace(
        x=np.array(params), fun=fun, success=success,
        message="controlled solver return", nit=1, nfev=7,
    )


def run_results(monkeypatch, *results, n_vertices=4, workers=1, trial_callback=None):
    returns = iter(results)
    monkeypatch.setattr(opt, "differential_evolution", lambda *a, **k: next(returns))
    return opt.optimize_ideal_polyhedron(
        n_vertices, n_trials=len(results), maxiter=1, popsize=1, workers=workers,
        trial_callback=trial_callback,
    )


def validate_payload(payload):
    schema_path = ROOT / f"docs/schemas/optimization-result-v{payload['schema_version']}.schema.json"
    schema = json.loads(schema_path.read_text())
    cls = validator_for(schema)
    cls.check_schema(schema)
    cls(schema).validate(payload)
    json.dumps(payload, allow_nan=False)


def test_cached_score_is_diagnostic_and_endpoint_is_recomputed(monkeypatch):
    result = run_results(monkeypatch, solver_result(fun=-100.0))
    assert result.best_volume == pytest.approx(REGULAR_VOLUME, abs=2e-14)
    trial = result.trials[0]
    assert trial.success is True
    assert trial.function_evals == 7
    assert trial.verification_evals == 1
    assert trial.validation["status"] == "verified"
    assert trial.validation["cached_objective"] == -100.0
    assert trial.validation["objective_difference"] == pytest.approx(100 - REGULAR_VOLUME)
    payload = opt.optimization_result_to_dict(result, source="test")
    assert payload["schema_version"] == 2
    assert payload["statistics"]["verification_evals"] == 1
    validate_payload(payload)


@pytest.mark.parametrize("retain_until_later_trial", [False, True])
def test_callback_mutation_preserves_verified_results(monkeypatch, retain_until_later_trial):
    retained = []

    def mutate_callback(trial):
        retained.append(trial)
        if retain_until_later_trial and len(retained) == 1:
            return
        # Edit both the current snapshot and any retained earlier snapshot.
        for snapshot in retained:
            snapshot.params[:] = [math.pi / 2, math.pi / 2]
            snapshot.validation["cached_objective"] = -999.0
            snapshot.validation["reason"] = "callback changed its diagnostic copy"
            snapshot.validation["status"] = "rejected"
            snapshot.validation["raw_diagnostics"] = {"scores": [math.nan]}
            snapshot.validation["raw_diagnostics"]["scores"].append(math.inf)

    right = np.array([math.pi / 2, math.pi / 2])
    result = run_results(
        monkeypatch, solver_result(success=False), solver_result(right, fun=-100.0),
        trial_callback=mutate_callback,
    )
    assert len(retained) == 2
    assert result.best_volume == pytest.approx(REGULAR_VOLUME, abs=2e-14)
    np.testing.assert_array_equal(result.best_params, REGULAR)
    np.testing.assert_array_equal(
        result.finite_vertices, opt.parameters_to_complex(result.best_params, 4),
    )
    assert -opt.negative_volume_objective(result.best_params, 4) == result.best_volume
    assert opt.ideal_poly_volume_via_delaunay(
        result.finite_vertices, mode="bloch_wigner",
    ) == result.best_volume
    assert [trial.success for trial in result.trials] == [False, True]
    for trial, expected_params, cached in zip(result.trials, [REGULAR, right], [-REGULAR_VOLUME, -100.0]):
        np.testing.assert_array_equal(trial.params, expected_params)
        assert trial.volume == -opt.negative_volume_objective(trial.params, 4)
        assert trial.validation["status"] == "verified"
        assert trial.validation["cached_objective"] == cached
        assert trial.validation["reason"] == "Canonical volume and complete boundary reconstruction passed"
        assert "raw_diagnostics" not in trial.validation
    payload = opt.optimization_result_to_dict(result, source="callback-mutation-test")
    assert payload["best"]["params"] == REGULAR.tolist()
    for serialized, trial in zip(payload["all_trials"], result.trials):
        assert serialized == trial.as_dict()
        assert serialized["validation"]["status"] == "verified"
    validate_payload(payload)


@pytest.mark.parametrize("bad", [
    [math.nan, 1.0], [math.inf, 1.0], [[1.0, 2.0]],
    ["not a number", "1"], [1 + 2j, 1j], [True, False],
])
def test_malformed_high_score_cannot_displace_valid_candidate(monkeypatch, bad):
    result = run_results(monkeypatch, solver_result(), solver_result(bad, fun=-100.0))
    assert result.best_volume == pytest.approx(REGULAR_VOLUME, abs=2e-14)
    rejected = result.trials[1]
    assert rejected.volume is None
    assert rejected.validation["status"] == "rejected"
    assert rejected.validation["invalid_params_repr"]
    assert rejected.params.size == 0
    assert rejected.verification_evals == 0
    payload = opt.optimization_result_to_dict(result, source="test")
    assert payload["all_trials"][1]["valid"] is False
    assert payload["all_trials"][1]["success"] is True  # raw solver status retained
    validate_payload(payload)


def test_finite_out_of_bounds_and_degenerate_endpoints_are_rejected(monkeypatch):
    result = run_results(
        monkeypatch, solver_result(),
        solver_result([-1.0, 1.0], fun=-100.0),
        solver_result([math.pi / 2, 0.0], fun=-100.0),
    )
    assert result.best_volume == pytest.approx(REGULAR_VOLUME)
    assert result.trials[1].volume is None
    assert "bounds" in result.trials[1].validation["reason"]
    assert result.trials[1].params.tolist() == [-1.0, 1.0]
    assert result.trials[2].volume is None
    assert result.trials[2].verification_evals == 1


def test_unused_duplicate_vertex_is_rejected_before_ranking(monkeypatch):
    good = np.array([math.pi / 2, math.pi / 3, math.pi / 2, 4 * math.pi / 3])
    duplicate = np.tile(REGULAR, 2)
    result = run_results(
        monkeypatch, solver_result(good), solver_result(duplicate, fun=-100), n_vertices=5,
    )
    assert result.trials[0].volume is not None
    assert result.trials[1].volume is None
    assert "every finite vertex" in result.trials[1].validation["reason"]


def test_valid_unconverged_candidate_is_retained(monkeypatch):
    result = run_results(monkeypatch, solver_result(success=False))
    assert result.trials[0].success is False
    assert result.trials[0].volume == pytest.approx(REGULAR_VOLUME)
    assert result.trials[0].validation["status"] == "verified"


def test_nonfinite_cached_score_does_not_invalidate_verified_geometry(monkeypatch):
    result = run_results(monkeypatch, solver_result(fun=math.nan, success=False))
    trial = result.trials[0]
    assert trial.volume == pytest.approx(REGULAR_VOLUME)
    assert trial.validation["cached_objective"] is None
    assert trial.validation["cached_objective_repr"] == "nan"
    validate_payload(opt.optimization_result_to_dict(result, source="test"))


def test_complex_cached_score_is_preserved_as_malformed_diagnostic(monkeypatch):
    result = run_results(monkeypatch, solver_result(fun=np.complex128(-2 + 3j)))
    diagnostic = result.trials[0].validation
    assert diagnostic["cached_objective"] is None
    assert "3j" in diagnostic["cached_objective_repr"]
    validate_payload(opt.optimization_result_to_dict(result, source="test"))


def test_polish_must_improve_recomputed_volume_not_cached_score(monkeypatch):
    polished = solver_result([math.pi / 2, math.pi / 2], fun=-100.0)
    polished.jac = np.zeros(2)
    monkeypatch.setattr(opt, "minimize", lambda *a, **k: polished)
    result = run_results(monkeypatch, solver_result(), workers=2)
    assert result.best_volume == pytest.approx(REGULAR_VOLUME)
    np.testing.assert_array_equal(result.best_params, REGULAR)
    assert result.trials[0].function_evals == 14
    assert result.trials[0].verification_evals == 2
    assert "did not improve" in result.trials[0].validation["polish"]


def test_invalid_parallel_endpoint_skips_polish(monkeypatch):
    def no_polish(*args, **kwargs):
        raise AssertionError("invalid endpoint must not reach local minimize")
    monkeypatch.setattr(opt, "minimize", no_polish)
    with pytest.raises(RuntimeError, match="valid configuration"):
        run_results(monkeypatch, solver_result([math.nan, 1]), workers=2)


def test_legacy_manual_record_is_not_claimed_freshly_verified(monkeypatch):
    result = run_results(monkeypatch, solver_result())
    legacy_trial = replace(result.trials[0], verification_evals=0, validation=None)
    legacy = replace(result, trials=(legacy_trial,))
    payload = opt.optimization_result_to_dict(legacy, source="test")
    assert payload["all_trials"][0]["validation"]["status"] == "not_checked"
    validate_payload(payload)
    with pytest.raises(ValueError, match="JSON compliant"):
        opt.optimization_result_to_dict(result, source="test", settings={"invalid": math.nan})


def test_preserved_v1_fixture_remains_valid():
    # Byte-copy of the original baseline CLI artifact, not rewritten as v2.
    fixture = json.loads((ROOT / "tests/fixtures/optimization-result-v1.json").read_text())
    assert fixture["schema_version"] == 1
    validate_payload(fixture)


def test_cli_distinguishes_solver_flag_and_candidate_validation(monkeypatch, tmp_path, capsys):
    returns = iter([solver_result([math.nan, 1], fun=-100), solver_result(success=False)])
    monkeypatch.setattr(opt, "differential_evolution", lambda *a, **k: next(returns))
    output = tmp_path / "result.json"
    assert optimization_cli.main([
        "--vertices", "4", "--trials", "2", "--maxiter", "1",
        "--popsize", "1", "--workers", "1", "--output", str(output),
    ]) == 0
    text = capsys.readouterr().out
    assert "Solver converged: True" in text
    assert "Solver converged: False" in text
    assert "Candidate validation: rejected" in text
    assert "Candidate validation: verified" in text
    payload = json.loads(output.read_text())
    assert payload["all_trials"][0]["valid"] is False
    assert payload["all_trials"][1]["valid"] is True
    validate_payload(payload)


@pytest.mark.parametrize("bad", [math.nan, complex(1, math.nan), complex(math.nan, 1)])
def test_threshold_nan_vertex_is_not_infinity(bad):
    with pytest.raises(ValueError, match="NaN"):
        threshold.get_volume([0j, 1 + 0j, np.exp(1j * math.pi / 3), bad])


@pytest.mark.parametrize("bad", [math.nan, math.inf, -math.inf, True, np.bool_(False), 1j])
def test_threshold_rejects_undefined_or_nonreal_threshold(bad):
    vertices = [0j, 1 + 0j, np.exp(1j * math.pi / 3), np.inf]
    with pytest.raises(ValueError, match="finite real"):
        threshold.volume_exceeds_threshold(vertices, bad)


@pytest.mark.parametrize("bad", [True, np.bool_(True), 0, -1, 1.5])
def test_threshold_approximation_requires_positive_integer_terms(bad):
    with pytest.raises(ValueError, match="series_terms"):
        threshold.get_volume([0j, 1 + 0j, 1j], series_terms=bad)


def test_threshold_preserves_implicit_infinity_and_numerical_comparison():
    finite = [0j, 1 + 0j, np.exp(1j * math.pi / 3)]
    assert threshold.get_volume(finite) == pytest.approx(REGULAR_VOLUME, abs=2e-14)
    assert threshold.get_volume(finite + [np.inf]) == pytest.approx(REGULAR_VOLUME, abs=2e-14)
    assert threshold.volume_exceeds_threshold(finite, Fraction(1, 2)) is True
    with pytest.raises(ValueError, match="at most one"):
        threshold.get_volume(finite + [np.inf, np.inf])
