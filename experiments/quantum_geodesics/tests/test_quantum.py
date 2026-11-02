"""Mathematical normalization, domain and lost-positive-signal regressions."""

from copy import deepcopy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mpmath
import sympy as sp


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.quantum_geodesics import common, figure_eight, klein, normalization  # noqa: E402


def fixture():
    return json.loads((HERE/"fixture.json").read_text())


class NumericalPolicyTests(unittest.TestCase):
    def test_tiny_positive_signal_rejects_zero_partial_negative_and_nonfinite(self):
        for digits in (70, 110):
            ctx = common.context(digits, 20)
            reference = ctx.mpf("1e-1000")
            for actual in (ctx.mpf(0), reference/2, reference/8, -reference, ctx.nan, ctx.inf):
                with self.subTest(digits=digits, actual=str(actual)):
                    checks = common.NumericChecks(ctx, digits, 20)
                    with self.assertRaises(ArithmeticError):
                        checks.positive("tiny", actual, reference)
                    self.assertEqual(checks.records, [])
            checks = common.NumericChecks(ctx, digits, 20)
            checks.positive("retained", reference, reference)

    def test_cross_precision_cannot_accept_lost_positive_signal(self):
        runs = []
        for digits in (70, 110):
            ctx = common.context(digits)
            checks = common.NumericChecks(ctx, digits)
            checks.observe("tiny", ctx.mpf("1e-500"), positive_signal=True)
            runs.append(checks.result())
        common.precision_comparison(*runs)
        for replacement in ("0", "5e-501", "-1e-500", "nan", "inf"):
            bad = deepcopy(runs)
            bad[0]["observations"]["tiny"]["value"] = replacement
            with self.assertRaises(ArithmeticError):
                common.precision_comparison(*bad)

    def test_guards_and_precision_are_local(self):
        previous = mpmath.mp.dps
        figure_eight.numerical_checks([2, 6, 12], 70, 20)
        self.assertEqual(mpmath.mp.dps, previous)
        for value in (True, 0.1, 1, "nan", "inf", "1/0", "sqrt(2)"):
            with self.assertRaises(ValueError):
                common.rational(value)
        for digits in (39, 151, 70.0, True):
            with self.assertRaises(ValueError):
                common.context(digits)
        with self.assertRaises(ValueError):
            common.NumericChecks(common.context(70, 20), 70, 10)
        ctx = common.context(70)
        for scale in (0, -1, ctx.nan, ctx.inf):
            with self.assertRaises(ArithmeticError):
                common.NumericChecks(ctx, 70).close("invalid scale", 1, 1, scale=scale)


class QuantumIdentityTests(unittest.TestCase):
    def test_small_habiro_values_and_six_divides_maximum_tie(self):
        ctx = common.context(70)
        for n, expected in ((2, 5), (3, 13), (4, 27)):
            value = figure_eight.habiro_le_sum(ctx, n)
            self.assertLess(abs(value-expected), ctx.mpf("1e-65"))
        rows = figure_eight.numerical_checks([5, 6, 12], 70, 20)["rows"]
        self.assertEqual([row["maximum_indices"] for row in rows], [[4], [4, 5], [9, 10]])
        for n in (0, 1, -2, True, 2.0):
            with self.assertRaises(ValueError):
                figure_eight.positive_sum(ctx, n)
            with self.assertRaises(ValueError):
                figure_eight.habiro_le_sum(ctx, n)

    def test_simplex_moments_and_duffy_jacobian(self):
        expected = [sp.Rational(1, 6), sp.Rational(1, 20), sp.Rational(2, 105)]
        self.assertEqual([klein.radial_moment(k, klein.simplex_monomial) for k in range(3)], expected)
        for powers in ((0, 0, 0), (1, 2, 3), (8, 0, 0), (2, 2, 4)):
            self.assertEqual(klein.simplex_monomial(*powers), klein.simplex_duffy_monomial(*powers))
        self.assertEqual(klein.simplex_duffy_monomial(0, 0, 0), sp.Rational(1, 6))

    def test_translation_retained_and_curvature_independent_of_origin(self):
        result = klein.exact_checks(fixture()["quantum"]["klein"])
        rows = {row["id"]: row for row in result["rows"]}
        self.assertEqual(rows["standard_simplex"]["curvature_sum"], -sp.Rational(1, 2))
        self.assertEqual(rows["centered_cube"]["curvature_sum"], -24)
        self.assertEqual(rows["translated_box"]["curvature_sum"], -6)
        shifted = rows["translated_box"]["radial_moments_k0_through_4"]
        centered_bounds = [["-1/2", "1/2"], ["-1", "1"], ["-1/2", "1/2"]]
        centered = klein.radial_moment(1, lambda a, b, c: klein.box_monomial(centered_bounds, (a, b, c)))
        self.assertNotEqual(shifted[1], centered)
        self.assertEqual(shifted[1]-centered, 2*(1+sp.Rational(1, 36)))

    def test_klein_boundary_and_degenerate_geometry_rejected(self):
        for radius in ("1", "2", "0", "nan"):
            with self.assertRaises(ValueError):
                klein.tail_bound(radius, "1/6", "1", 2)
        with self.assertRaises(ValueError):
            klein.box_vertices([["0", "0"], ["0", "1"], ["0", "1"]])
        with self.assertRaises(ValueError):
            klein.polyhedron_geometry([(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)], [[0, 1, 1]])

    def test_half_log_formal_stationarity_and_dependency_guards(self):
        data = fixture()
        result = normalization.peripheral_checks(data["quantum"]["peripheral"], data["guarded_dependency_sha256"])
        u, a = sp.symbols("u a")
        first = result["rows"][0]
        self.assertEqual(sp.simplify(sp.diff(first["G"], u)-(u-a)/2), 0)
        self.assertEqual(sp.simplify(sp.diff(first["phase_Phi"], u)-first["formal_v"]/2), 0)
        guards = dict(data["guarded_dependency_sha256"])
        guards["experiments/quantum_surgery/exact.py"] = "0"*64
        with self.assertRaises(ArithmeticError):
            normalization.guarded_surgery_dependency(guards)
        bad = deepcopy(data["quantum"]["peripheral"])
        bad["slopes"] = [[1, 0, 0, 1]]
        with self.assertRaises(ValueError):
            normalization.peripheral_checks(bad, data["guarded_dependency_sha256"])

    def test_full_log_weyl_factor_is_rejected(self):
        ctx = common.context(70)
        u, hbar = ctx.mpf(1)/3, ctx.mpf(1)/7
        left = ctx.exp((u+hbar)/2)
        wrong = ctx.exp(hbar)*ctx.exp(u/2)
        with self.assertRaises(ArithmeticError):
            common.NumericChecks(ctx, 70).positive("wrong Weyl factor", left, wrong)

    def test_charge_boundaries_and_curvature_factor(self):
        result = normalization.charge_checks(fixture()["quantum"]["charges"])
        self.assertEqual(result["rows"][0]["s"], -1)
        for values in (["1/2"]*3, ["0", "1/2", "1/2", "1"], ["1/3"]*4):
            with self.assertRaises(ValueError):
                normalization.validate_weights(values)
        data = deepcopy(fixture()["quantum"]["charges"])
        data["b_squared"] = ["1"]
        with self.assertRaises(ValueError):
            normalization.charge_checks(data)


class DriverTests(unittest.TestCase):
    def test_duplicate_keys_and_nonfinite_json_tokens_are_rejected(self):
        run = importlib.import_module("experiments.quantum_geodesics.run")
        for text in ('{"schema_version": 1, "schema_version": 1}',
                     '{"outer": {"mu": ["1/2"], "mu": ["1/2"]}}',
                     '{"value": NaN}', '{"value": Infinity}', '{"value": -Infinity}',
                     '{"value": 1e9999}', '{"value": 0.1}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                run.parse_fixture(text)
        self.assertEqual(run.parse_fixture('{"exact": "1/10", "integer": 4}'),
                         {"exact": "1/10", "integer": 4})

    def test_import_safe_and_failure_checks_survive_optimization(self):
        with tempfile.TemporaryDirectory() as directory:
            code = "import runpy; runpy.run_path("+repr(str(HERE/"run.py"))+", run_name='import_probe')"
            completed = subprocess.run([sys.executable, "-O", "-c", code], cwd=directory, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout, "")
            self.assertEqual(list(Path(directory).iterdir()), [])
            code = ("import sys; sys.path.insert(0,"+repr(str(ROOT))+"); "
                    "from experiments.quantum_geodesics.common import context,NumericChecks; "
                    "c=context(70); NumericChecks(c,70).positive('lost',c.mpf(0),c.mpf('1e-500'))")
            completed = subprocess.run([sys.executable, "-O", "-c", code], cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("strictly positive", completed.stderr)

    def test_partial_fixture_and_failed_run_cannot_write_success(self):
        run = importlib.import_module("experiments.quantum_geodesics.run")
        data = fixture()
        data["quantum"]["figure_eight_N"].pop()
        with self.assertRaises(ValueError):
            run.validate_fixture(data)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"failed.json"
            with patch.object(run, "calculate", side_effect=ArithmeticError("injected failed identity")):
                with self.assertRaises(ArithmeticError):
                    run.main(["--output", str(output)])
            self.assertFalse(output.exists())
            with patch.object(run, "source_state", side_effect=[
                    {"sources": [1], "guarded_dependencies": [], "git_commit": "a"},
                    {"sources": [2], "guarded_dependencies": [], "git_commit": "a"}]):
                with patch.object(run, "calculate", return_value={}):
                    with self.assertRaises(ArithmeticError):
                        run.main(["--output", str(output)])
            self.assertFalse(output.exists())
            output.write_text("preserve me\n")
            with self.assertRaises(SystemExit):
                run.main(["--output", str(output)])
            self.assertEqual(output.read_text(), "preserve me\n")


if __name__ == "__main__":
    unittest.main()
