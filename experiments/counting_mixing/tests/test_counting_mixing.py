"""Regression oracles for normalization, multiplicities, finite bounds and failures."""

import copy
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
import tempfile
import unittest

import mpmath


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.counting_mixing import algebra, arithmetic, dynamics, exact, numerics, run  # noqa: E402


class AlgebraTests(unittest.TestCase):
    def test_trace_polynomial_normalization_and_coefficients(self):
        polys = exact.chebyshev(exact.X, 12)
        self.assertEqual(polys[0], {exact.ZERO: 2})
        self.assertEqual(polys[8][(2, 0, 0)], -16)
        self.assertEqual(polys[12][(2, 0, 0)], -36)
        self.assertEqual(polys[11][(1, 0, 0)], -11)

    def test_cuff_identification_collects_degrees(self):
        trace = exact.add(exact.mul(exact.X, exact.Y), exact.scale(exact.Z, -1))
        second = exact.identify_cuffs(exact.chebyshev(trace, 2)[2])
        self.assertEqual(second, {(4, 0, 0): 1, (2, 0, 1): -2, (0, 0, 2): 1, (0, 0, 0): -2})
        self.assertNotIn((1, 1, 0), second)

    def test_global_functional_is_not_common_trace_evaluation(self):
        weights = algebra.moment_weights(12)
        self.assertEqual((weights[0], weights[1], weights[4]), (2, 1, 5))
        self.assertNotEqual(algebra.linear_weight(exact.power(exact.X, 4), weights), weights[1]**4)
        with self.assertRaises(ValueError):
            algebra.linear_weight(exact.power(exact.X, 13), weights)

    def test_direct_noncommuting_word_oracle(self):
        result = algebra.matrix_checks([{"id": "fixture", "A": [[1, 1], [0, 1]], "B": [[1, 0], [1, 1]]}])
        row = result["fixtures"][0]
        self.assertEqual(row["word_traces"], [4, 8, 10])
        self.assertEqual(row["Adams_defect"], 2)

    def test_support_counts_parallel_copies(self):
        result = algebra.support_checks([2, 3], 14, 60)
        self.assertEqual(result["one_support_count"], 14)
        self.assertEqual(result["one_copy_count"], 3)
        self.assertEqual(sum(exact.mobius(d) for d in exact.divisors(6)), 0)
        self.assertNotEqual(sum(Q(exact.mobius(d), d) for d in exact.divisors(6)), 0)

    def test_finite_euler_empty_atom_and_wrong_adams(self):
        result = algebra.euler_checks(14)
        self.assertEqual(result["wrong_Adams_empty_atoms"][4], -1)
        empty = {row["length"]: item["coefficient"] for row in result["coefficients_by_length"]
                 for item in row["polynomial"] if item["powers_xyz"] == [0, 0, 0]}
        self.assertEqual(empty, {0: 1})

    def test_length_convolution_accumulates_before_support(self):
        left = {2: exact.X, 3: exact.X}
        right = {2: exact.ONE, 3: exact.scale(exact.ONE, -1)}
        result = algebra.convolve(left, right, 6)
        self.assertNotIn(5, result)
        self.assertEqual(algebra.coefficient_atoms(result, (1, 0, 0)), {4: 1, 6: -1})


class DynamicsTests(unittest.TestCase):
    def test_scalar_count_does_not_imply_mixing(self):
        result = dynamics.scalar_checks([3], 3)
        rows = result["periodic_examples"][0]["values"]
        self.assertEqual([row["path_count"] for row in rows], [6, 18, 54])
        self.assertEqual([row["closed_trace"] for row in rows], [0, 18, 0])
        self.assertEqual([row["stationary_correlation"] for row in rows], [-1, 1, -1])

    def test_bruhat_c5_exact_residue_multiplicity(self):
        row = dynamics.bruhat_checks(5, [[1, 1]])["rows"][-1]
        self.assertEqual(row["frequency_residues"][0]["root_of_unity_coefficients"], {0: 2, 2: 1, 3: 1})
        self.assertEqual(row["adaptive_statistic"], 1)
        self.assertEqual(row["adaptive_continuous_means"], [0, 0])

    def test_terminal_formal_algebra_keeps_rate_zero_separate(self):
        result = dynamics.terminal_algebra_checks([
            {"h": 1, "r": 2, "c": "3/2"}, {"h": 2, "r": 2, "c": "3/2"}])
        self.assertEqual(result["rows"][0]["integrand_exponential_terms"], [{"rate": -1, "coefficient": Q(-3, 2)}])
        self.assertEqual(result["rows"][1]["primitive_modulo_constants"], [])

    def test_proved_coordinate_box_finds_large_shear_vectors(self):
        vectors, bounds = dynamics.primitive_vectors([[1, 20], [0, 1]], 1)
        self.assertEqual(bounds, [21, 1])
        self.assertEqual(set(vectors), {(-20, 1), (20, -1), (-1, 0), (1, 0)})

    def test_primitive_ellipse_boundary_and_signs(self):
        vectors, _ = dynamics.primitive_vectors([[1, 0], [0, 1]], 1)
        self.assertEqual(set(vectors), {(1, 0), (-1, 0), (0, 1), (0, -1)})
        smaller, _ = dynamics.primitive_vectors([[1, 0], [0, 1]], "3/4")
        self.assertEqual(smaller, [])

    def test_gaussian_algebra_and_signed_rank_one_factor(self):
        result = dynamics.gaussian_exact_checks([[1, 2]], [1, 2])
        self.assertEqual(result["affine_norm_coefficients"][0]["S1_squared_times_ab_3_over_2"], Q(9, 8))
        self.assertEqual(result["rank_one_truncated_sums"][0]["bare_sum_inverse_a2_plus_b2"], 2)


class ArithmeticTests(unittest.TestCase):
    def test_mobius_square_and_cutoff_boundary(self):
        result = arithmetic.mobius_checks(["3/2", "2"])
        self.assertEqual([row["primitive_signed_square_vectors"] for row in result["square_rows"]], [8, 16])
        row = next(row for row in result["tail_rows"] if row["gauge"] == "square" and row["L"] == 2 and row["D"] == 1)
        self.assertEqual(row["boundary_zero_terms"], 16)
        self.assertEqual(row["tail"], -8)

    def test_grouped_events_and_exact_integral(self):
        result = arithmetic.block_metrics([2, 2, 4, 5, 8], 2)
        self.assertEqual(result["M"], Q(5, 2))
        self.assertEqual(result["Q_squared"], Q(49, 20))
        final = result["event_groups"][-1]
        self.assertEqual((final["position"], final["half"], final["full"], final["D_actual"]), (4, 1, 1, -7))

    def test_simultaneous_events_have_no_intermediate_state(self):
        result = arithmetic.block_metrics([2, 4, 4], 1)
        self.assertEqual(result["M"], 1)
        self.assertEqual(result["Q_squared"], Q(1, 2))

    def test_external_left_limit_at_block_start_is_excluded(self):
        result = arithmetic.block_metrics(["1/2", "1/2", 2], 1)
        self.assertEqual(result["M"], 5)  # The external left limit would incorrectly give 6.
        self.assertEqual(result["maximizers"][0]["side"], "actual")

    def test_actual_value_at_block_end_is_included(self):
        result = arithmetic.block_metrics([4], 1)
        self.assertEqual(result["M"], Q(1, 2))
        self.assertEqual(result["Q_squared"], 0)
        self.assertEqual(result["maximizers"][0]["position"], 2)

    def test_nearby_events_are_never_tolerance_merged(self):
        lengths = [Q(2), Q(20000000000001, 10000000000000), Q(4)]
        result = arithmetic.block_metrics(lengths, 1)
        self.assertEqual(len(result["event_groups"]), 2)
        reference = arithmetic.direct_block_metrics(lengths, 1)
        self.assertEqual(result["M"], reference["M"])
        self.assertEqual(result["Q_squared"], reference["Q_squared"])

    def test_signed_multiples_keep_equal_length_classes(self):
        result = arithmetic.dyadic_checks([2, 2, 4, 5, 8], [2], [1, 3])
        self.assertEqual(result["signed_multiples"][0]["signed_multiples"], 10)

    def test_row_zero_negative_and_fractional_endpoints(self):
        self.assertEqual(arithmetic.row_count(0, 0, 1), 1)
        self.assertEqual(arithmetic.row_count(0, 0, 2), 0)
        self.assertEqual(arithmetic.row_count(-4, -1, 6), 1)
        self.assertEqual(arithmetic.row_count("1/3", "2/3", 1), 0)

    def test_exact_power_balance(self):
        self.assertEqual(arithmetic.balance("2/3", "11/12"), (Q(16, 17), Q(50, 51)))
        with self.assertRaises(ValueError):
            arithmetic.balance("2/3", 1)


class NumericalTests(unittest.TestCase):
    def test_affine_gaussian_normalization_and_rotation(self):
        ctx = numerics.context(40)
        result = numerics.gaussian_checks(ctx, [[1, 1]], [0])
        row = result["rows"][0]
        self.assertLess(abs(ctx.mpf(row["L2_squared"])-ctx.mpf("0.5")), ctx.mpf("1e-30"))
        self.assertEqual(ctx.mpf(row["rotation_derivative_squared"]), 0)
        self.assertLess(abs(ctx.mpf(row["correlations"][0]["quadrature"])-ctx.mpf("0.5")), ctx.mpf("1e-30"))

    def test_rank_two_keeps_both_determinant_signs(self):
        ctx = numerics.context(40)
        result = numerics.rank_two_checks(ctx, [0], 20, [1])
        row = result["rows"][0]
        ratio = ctx.mpf(row["k_series"])/ctx.mpf(row["radial_orbits"][0]["closed_integral"])
        self.assertGreater(ratio, ctx.mpf("2"))
        self.assertLess(ratio, ctx.mpf("2.001"))

    def test_tiny_orbit_requires_relative_accuracy_and_rejects_mutants(self):
        ctx = numerics.context(60)
        alpha, k = 2*ctx.pi*ctx.cosh(2), 3
        scaled, scaled_tail = numerics.orbit_integral(ctx, alpha, k, 20, scaled=True)
        amplitude = ctx.exp(-2*alpha*k)
        actual, tail = amplitude*scaled, amplitude*scaled_tail
        expected = ctx.pi**2*amplitude/(alpha*k*ctx.zeta(2))
        self.assertLess(abs(actual/expected-1), ctx.mpf("1e-50"))
        self.assertGreater(scaled, ctx.mpf("0.08"))
        self.assertLess(actual, ctx.mpf("1e-62"))
        for factor in (ctx.mpf(0), ctx.mpf("0.5"), ctx.mpf(-1), ctx.mpf(2)):
            with self.subTest(factor=str(factor)), self.assertRaises(AssertionError):
                numerics.PositiveNumericChecks(ctx).close(
                    "tiny radial mutant", factor*actual, expected, analytic_tail_allowance=tail)

    def test_positive_covariance_log_and_orbit_sum_conventions(self):
        ctx = numerics.context(60)
        result = numerics.rank_two_checks(ctx, [2], 24, [3])
        row = result["rows"][0]
        expected = ctx.mpf(row["k_series"])
        self.assertEqual(result["observation_policy"], "strictly_positive_relative")
        self.assertEqual(len(result["observations"]), 5)
        for field in ("k_series", "log_series", "two_sign_orbit_sum"):
            value = ctx.mpf(row[field])
            self.assertGreater(value, 0)
            self.assertLess(abs(value/expected-1), ctx.mpf("1e-50"))
            for factor in (ctx.mpf(0), ctx.mpf("0.5"), ctx.mpf(-1), ctx.mpf(2)):
                with self.subTest(field=field, factor=str(factor)), self.assertRaises(AssertionError):
                    numerics.PositiveNumericChecks(ctx).close("covariance mutant", factor*value, expected)

    def test_every_positive_cross_precision_observation_rejects_mutants(self):
        low = numerics.rank_two_checks(numerics.context(60), [2], 24, [3])
        high = numerics.rank_two_checks(numerics.context(90), [2], 24, [3])
        comparison = numerics.precision_comparison(low, high)
        self.assertEqual(comparison["observation_policy"], "strictly_positive_relative")
        ctx = numerics.context(90)
        self.assertLess(ctx.mpf(comparison["maximum_relative_difference"]), ctx.mpf("1e-50"))
        for key, value in low["observations"].items():
            for factor in (ctx.mpf(0), ctx.mpf("0.5"), ctx.mpf(-1), ctx.mpf(2)):
                changed = copy.deepcopy(low)
                changed["observations"][key] = numerics.number(ctx, factor*ctx.mpf(value))
                with self.subTest(observation=key, factor=str(factor)), self.assertRaises(AssertionError):
                    numerics.precision_comparison(changed, high)

    def test_positive_tail_allowance_cannot_hide_a_relative_defect(self):
        ctx = numerics.context(60)
        expected = ctx.mpf("1e-63")
        with self.assertRaises(AssertionError):
            numerics.PositiveNumericChecks(ctx).close(
                "oversized tail", expected/2, expected, analytic_tail_allowance=expected)
        for value in (0, -1):
            with self.assertRaises(AssertionError):
                numerics.PositiveNumericChecks(ctx).observe("invalid positive signal", value)

    def test_genuine_zeros_keep_absolute_treatment(self):
        low_checks, high_checks = numerics.NumericChecks(numerics.context(60)), numerics.NumericChecks(numerics.context(90))
        for checks in (low_checks, high_checks):
            checks.close("genuine zero", 0, 0)
            checks.observe("zero", 0)
        result = numerics.precision_comparison(low_checks.result(), high_checks.result())
        self.assertEqual(result["maximum_scaled_difference"], "0.0")

    def test_analytic_tail_formulas_dominate_known_finite_tails(self):
        q, n = Q(1, 2), 3
        series_bound, log_bound = numerics.series_tail_bounds(q, n)
        finite_series_tail = sum(Q(sum(exact.divisors(k)), k)*q**k for k in range(n+1, 30))
        finite_log_tail = sum(q**(j*m)/m for j in range(n+1, 30) for m in range(1, 30))
        self.assertGreater(series_bound, finite_series_tail)
        self.assertGreater(log_bound, finite_log_tail)
        with self.assertRaises(ValueError):
            numerics.series_tail_bounds(1, 3)

    def test_removable_terminal_case(self):
        ctx = numerics.context(40)
        result = numerics.terminal_checks(ctx, [{"h": 1, "r": 1, "c": "3/2", "M": "5/3", "T": 3}])
        self.assertEqual(ctx.mpf(result["rows"][0]["integral"]), 0)

    def test_nonfinite_comparisons_fail_and_context_is_local(self):
        original = mpmath.mp.dps
        ctx = numerics.context(40)
        with self.assertRaises(AssertionError):
            numerics.NumericChecks(ctx).close("NaN", ctx.nan, 0)
        with self.assertRaises(AssertionError):
            numerics.number(ctx, ctx.inf)
        self.assertEqual(mpmath.mp.dps, original)


class ValidationAndProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = json.loads((run.HERE/"fixture.json").read_text())

    def test_shipped_fixture_validates(self):
        self.assertIs(run.validate_fixture(self.fixture), self.fixture)

    def test_exact_input_rejects_float_bool_nonfinite_and_bad_denominator(self):
        for value in (0.5, True, float("nan"), "nan", "inf", "1/0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exact.rational(value)

    def test_invalid_geometric_and_arithmetic_domains_fail(self):
        for matrix in ([[1, 0], [0, 2]], [[1, 0]], [["nan", 0], [0, 1]]):
            with self.assertRaises(ValueError):
                exact.matrix(matrix)
        for lengths, start in (([0], 1), ([-1], 1), ([1], 0), (["nan"], 1)):
            with self.assertRaises(ValueError):
                arithmetic.block_metrics(lengths, start)
        with self.assertRaises(ValueError):
            arithmetic.row_count(2, 1, 3)
        with self.assertRaises(ValueError):
            arithmetic.lattice_points(1, "unknown")

    def test_malformed_fixture_rejected_before_computation(self):
        for key, value in (("precisions", [90, 60]), ("gaussian_pairs", [[1, 0]]),
                           ("rank_one_boxes", [8, 4]), ("endpoint_frequencies", [[1.0, 2]]),
                           ("gaussian_times", ["nan"]), ("matrix_power_maximum", True),
                           ("schema_version", True), ("formula_contracts", {})):
            altered = copy.deepcopy(self.fixture)
            altered[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                run.validate_fixture(altered)

    def test_source_input_or_head_drift_refuses_success(self):
        baseline = {"git_commit": "a", "sources": [{"path": "fixture.json", "sha256": "x"}]}
        for modified in ({"git_commit": "b", "sources": baseline["sources"]},
                         {"git_commit": "a", "sources": [{"path": "fixture.json", "sha256": "y"}]}):
            with self.assertRaises(AssertionError):
                run.verify_source_unchanged(baseline, modified)

    def test_exclusive_writer_and_nonfinite_serialization(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"result.json"
            run.write_result(output, {"value": Q(1, 3)})
            with self.assertRaises(FileExistsError):
                run.write_result(output, {"value": 2})
            self.assertEqual(json.loads(output.read_text()), {"value": "1/3"})
            nonfinite = Path(directory)/"nonfinite.json"
            with self.assertRaises(ValueError):
                run.write_result(nonfinite, {"value": float("nan")})
            self.assertFalse(nonfinite.exists())


if __name__ == "__main__":
    unittest.main()
