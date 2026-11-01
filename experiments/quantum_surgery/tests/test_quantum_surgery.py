"""Domain, convention and failure-path regressions for the bounded companion."""

from copy import deepcopy
from fractions import Fraction as Q
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mpmath


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.quantum_surgery import algebra, exact, periods  # noqa: E402


class ExactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE/"fixture.json").read_text())

    def test_rationals_do_not_accept_binary_floats(self):
        self.assertEqual(exact.rational("0.1"), Q(1, 10))
        for value in (0.1, 1, True):
            with self.assertRaises(ValueError):
                exact.rational(value)
        with self.assertRaises(TypeError):
            exact.Quadratic(0.1, 1, -3)
        with self.assertRaises(TypeError):
            exact.determinant([[1.0, 0], [0, 1]])
        with self.assertRaises(TypeError):
            exact.multiply([Q(1), Q(2)], [0.1, 0.2])

    def test_quadratic_division_sign_and_field_boundaries(self):
        value = exact.Quadratic(1, 2, -3)
        self.assertEqual(1/value, exact.Quadratic(Q(1, 13), -Q(2, 13), -3))
        self.assertEqual(value*value.conjugate(), 13)
        self.assertEqual(value**-2*value**2, 1)
        with self.assertRaises(ZeroDivisionError):
            value/exact.Quadratic(0, 0, -3)
        with self.assertRaises(ValueError):
            value+exact.Quadratic(1, 0, 3)
        with self.assertRaises(ValueError):
            exact.Quadratic(0, 1, 4)

    def test_matrix_pivoting_and_singular_rejection(self):
        matrix = [[0, 1], [1, 2]]
        self.assertEqual(exact.inverse(matrix), [[Q(-2), Q(1)], [Q(1), Q(0)]])
        self.assertEqual(exact.determinant(matrix), -1)
        with self.assertRaises(ValueError):
            exact.inverse([[1, 2], [2, 4]])
        with self.assertRaises(ValueError):
            exact.matmul([[1, 2]], [[1, 2]])

    def test_primitive_oriented_slope_and_action_chart(self):
        algebra.validate_slope(1, -1, 0, 1)
        for basis in ((2, 2, 0, 1), (1, 1, 1, 0), (0, 0, 0, 1), (1.0, 1, 0, 1)):
            with self.assertRaises(ValueError):
                algebra.validate_slope(*basis)
        with self.assertRaises(ValueError):
            algebra.validate_slope(1, 0, 0, 1)
        algebra.validate_slope(1, 0, 0, 1, action=False)
        with self.assertRaises(ValueError):
            algebra.filling_inverse(Q(-1), Q(1), Q(1), 1, 1)

    def test_stationary_action_golden_factors(self):
        result = algebra.surgery_checks(self.fixture)
        first = result["slopes"][0]["action_in_theta"]
        self.assertEqual(first[2], exact.Quadratic(Q(1, 26), -Q(1, 13), -3))
        self.assertEqual(first[4], exact.Quadratic(-Q(44, 28561), Q(73, 171366), -3))
        tensor = algebra.tensor_checks(self.fixture)["slopes"][0]
        self.assertEqual(tensor["corrected_quartic"], exact.Quadratic(0, Q(146, 28561), 3))

    def test_wrong_inverse_coefficient_is_rejected(self):
        original = algebra.filling_inverse

        def corrupt(*args):
            result = original(*args)
            result[3] = -result[3]
            return result

        # No fixture output is accepted if a cubic inverse coefficient changes sign.
        with patch.object(algebra, "filling_inverse", side_effect=corrupt):
            with self.assertRaises(ArithmeticError):
                algebra.surgery_checks(self.fixture)

    def test_exact_sections_and_physical_chart_guards(self):
        for function, args in ((algebra.fricke_checks, (self.fixture,)), (algebra.regular_checks, ()),
                               (algebra.hessian_checks, ())):
            self.assertGreater(function(*args)["check_count"], 5)
        invalid = deepcopy(self.fixture)
        invalid["heron_chart"][0][1] = "0"
        with self.assertRaises(ValueError):
            algebra.fricke_checks(invalid)
        invalid = deepcopy(self.fixture)
        invalid["b_values"] = ["1"]
        with self.assertRaises(ValueError):
            algebra.fricke_checks(invalid)


class PeriodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE/"fixture.json").read_text())

    def test_branch_cut_and_precision_guards(self):
        ctx = periods.context(50)
        for z in (("0", "0"), ("1", "0"), ("-1/3", "0"), ("2", "0"), (0.5, "0")):
            with self.assertRaises(ValueError):
                periods.point(ctx, z)
        periods.point(ctx, ["-1/3", "1/10"])
        for digits in (30, 121, 60.0, True):
            with self.assertRaises(ValueError):
                periods.context(digits)
        with self.assertRaises(ValueError):
            periods.mpq(ctx, 0.1)

    def test_weight_domains_and_operation_specific_resonance(self):
        for mu in (["1/2"]*3, ["0", "1/2", "1/2", "1"], ["1/3"]*4):
            with self.assertRaises(ValueError):
                algebra.weights(mu)
        ctx = periods.context(50)
        z = periods.point(ctx, ["1/3", "0"])
        balanced = algebra.weights(["1/2"]*4)
        with self.assertRaises(ValueError):
            periods.s_basis(ctx, balanced, z)
        # The balanced-limit path has delta0!=0 but delta1=0: s remains usable.
        path = algebra.weights(["2/5", "3/5", "2/5", "3/5"])
        self.assertEqual(periods.delta(path)[:2], (Q(1, 5), Q(0)))
        periods.s_basis(ctx, path, z)
        periods.s_hermitian(ctx, path)
        with self.assertRaises(ValueError):
            periods.t_basis(ctx, path, z)
        with self.assertRaises(ValueError):
            periods.fusion(ctx, path)

    def test_endpoint_smoothing_at_weight_nine_tenths(self):
        ctx = periods.context(60)
        actual = periods.euler_integral(ctx, Q(9, 10), Q(3, 10), Q(1, 2), ctx.mpf(0))
        expected = ctx.beta(ctx.mpf(1)/10, ctx.mpf(7)/10)
        self.assertLess(abs(actual/expected-1), ctx.mpf("1e-55"))
        with self.assertRaises(ValueError):
            periods.euler_integral(ctx, Q(1), Q(1, 2), Q(1, 2), ctx.mpf(0))

    def test_hermitian_signs_and_conjugate_branches(self):
        ctx = periods.context(50)
        z = periods.point(ctx, ["2/5", "1/4"])
        for row in self.fixture["period_weights"]:
            mu = algebra.weights(row["mu"])
            H = periods.s_hermitian(ctx, mu)
            self.assertEqual(ctx.sign(H[0, 0]), 1 if periods.delta(mu)[0] > 0 else -1)
            self.assertLess(H[0, 0]*H[1, 1], 0)
            upper, lower = periods.s_basis(ctx, mu, z), periods.s_basis(ctx, mu, ctx.conj(z))
            self.assertLess(max(abs(lower[i]-ctx.conj(upper[i])) for i in range(2)), ctx.mpf("1e-45"))

    def test_fusion_and_balanced_metrics_preserve_global_precision(self):
        before = mpmath.mp.dps
        period = periods.period_check(self.fixture["period_weights"][1], ["2/5", "-1/4"], 50)
        balanced = periods.balanced_check(["1/4", "1/5"], 50)
        self.assertEqual(mpmath.mp.dps, before)
        self.assertGreater(period["check_count"], 10)
        self.assertGreater(balanced["check_count"], 15)
        with self.assertRaises(ValueError):
            periods.precision_comparison(period, period)
        with self.assertRaises(ArithmeticError):
            periods.NumericChecks(periods.context(50)).close("wrong density factor", 4, 1)
        ctx = periods.context(50)
        for invalid in (ctx.nan, ctx.inf, -ctx.inf, ctx.mpc(1, ctx.nan), ctx.mpc(0, ctx.inf)):
            for side in ("actual", "expected"):
                for position in (None, 0, 1, 2):
                    with self.subTest(invalid=str(invalid), side=side, position=position):
                        if position is None:
                            finite, nonfinite = ctx.mpf(1), invalid
                        else:
                            finite = ctx.matrix([1, 2, 3])
                            nonfinite = finite.copy()
                            nonfinite[position] = invalid
                        actual, expected = ((nonfinite, finite) if side == "actual"
                                            else (finite, nonfinite))
                        checks = periods.NumericChecks(ctx)
                        with self.assertRaisesRegex(ArithmeticError, "nonfinite"):
                            checks.close("nonfinite input", actual, expected)
                        self.assertEqual(checks.residuals, {})
        # Even finite native scalars can have a nonfinite subtraction result.
        checks = periods.NumericChecks(ctx)
        with self.assertRaisesRegex(ArithmeticError, "nonfinite"):
            checks.close("nonfinite difference", 1e308, -1e308)
        self.assertEqual(checks.residuals, {})

    def test_gram_zero_cofactors_and_signs(self):
        for row in self.fixture["period_weights"]:
            self.assertEqual(periods.gram_check(row, "1/40", 50)["check_count"], 19)
        with self.assertRaises(ValueError):
            periods.gram_check(self.fixture["period_weights"][0], "1", 50)


class DriverTests(unittest.TestCase):
    def test_import_has_no_output_and_driver_works_from_another_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            code = "import runpy; runpy.run_path("+repr(str(HERE/"run.py"))+", run_name='import_probe')"
            imported = subprocess.run([sys.executable, "-c", code], cwd=path, capture_output=True, text=True)
            self.assertEqual(imported.returncode, 0, imported.stderr)
            self.assertEqual(imported.stdout, "")
            self.assertEqual(list(path.iterdir()), [])
            output = path/"result.json"
            completed = subprocess.run([sys.executable, str(HERE/"run.py"), "--output", str(output)],
                                       cwd=path, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(output.read_text())
            self.assertTrue(result["checks_passed"])
            self.assertEqual(result["arithmetic"]["precision"], [60, 90])
            self.assertEqual(len(result["nonresonant_periods"]), 6)
            self.assertEqual(len(result["balanced_periods"]), 2)
            self.assertEqual(result["source"]["sources"], result["source_at_completion"]["sources"])

    def test_overwrite_and_failed_check_leave_no_success_output(self):
        run = importlib.import_module("experiments.quantum_surgery.run")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            existing = path/"existing.json"
            existing.write_text("preserve me\n")
            completed = subprocess.run([sys.executable, "-O", str(HERE/"run.py"), "--output", str(existing)],
                                       cwd=path, capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("refusing to overwrite", completed.stderr)
            self.assertEqual(existing.read_text(), "preserve me\n")
            output = path/"failed.json"

            def failed_calculation(_fixture):
                ctx = periods.context(50)
                periods.NumericChecks(ctx).close("injected discrepancy", ctx.mpf(1), ctx.mpf(2))

            with patch.object(run, "calculate", side_effect=failed_calculation):
                with self.assertRaises(ArithmeticError):
                    run.main(["--output", str(output)])
            self.assertFalse(output.exists())
            with patch.object(run, "source_state", side_effect=[{"sources": [1], "git_commit": "a"},
                                                                 {"sources": [2], "git_commit": "a"}]):
                with patch.object(run, "calculate", return_value={}):
                    with self.assertRaises(ArithmeticError):
                        run.main(["--output", str(output)])
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
