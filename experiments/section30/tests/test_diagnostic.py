"""Regression oracles for slope multiplicity, exact traces, and event limits."""

from decimal import Decimal, localcontext
from fractions import Fraction
import importlib.util
import math
from pathlib import Path
import sys
import unittest


DRIVER = Path(__file__).resolve().parents[1] / "run.py"
SPEC = importlib.util.spec_from_file_location("section30_diagnostic", DRIVER)
run = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run
SPEC.loader.exec_module(run)


class DiagnosticTests(unittest.TestCase):
    def test_exact_asymmetric_root(self):
        roots = run.fixture_roots({"traces_qsqrt11": [["5/2", "0"], ["5", "-1/2"], ["4", "0"]]})
        self.assertEqual(roots[0]*roots[1]-roots[2],
                         run.Quadratic(Fraction(17, 2), Fraction(-5, 4)))

    def test_algebraic_signs_without_float(self):
        self.assertEqual(run.Quadratic(Fraction(3), Fraction(-1)).sign(), -1)
        self.assertEqual(run.Quadratic(Fraction(4), Fraction(-1)).sign(), 1)
        self.assertEqual(run.Quadratic(Fraction(-3), Fraction(1)).sign(), 1)
        self.assertEqual(run.Quadratic(Fraction(-4), Fraction(1)).sign(), -1)

    def test_invalid_roots_fail(self):
        with self.assertRaises(ValueError):
            run.fixture_roots({"traces_qsqrt11": [["3", "0"], ["3", "0"], ["4", "0"]]})

    def test_quadratic_cancellation_is_rationalized(self):
        # (10-3sqrt(11))^80 is positive, with norm one; direct evaluation
        # subtracts hundreds of nearly equal leading digits.
        tiny = run.Quadratic(Fraction(1))
        factor = run.Quadratic(Fraction(10), Fraction(-3))
        for _ in range(80):
            tiny = tiny*factor
        with localcontext() as ctx:
            ctx.prec = 50
            actual = tiny.decimal()
            self.assertGreater(actual, 0)
            reference = (Decimal(10)+3*Decimal(11).sqrt())**(-80)
            self.assertLess(abs(actual/reference-1), Decimal("1e-47"))

    def test_canonical_unoriented_slopes(self):
        self.assertEqual(run.canonical_slope(1, -2), (-1, 2))
        self.assertEqual(run.canonical_slope(-1, 0), (1, 0))
        with self.assertRaises(ValueError):
            run.canonical_slope(2, 2)

    def test_equal_root_traces_are_three_curves(self):
        roots = (run.Quadratic(Fraction(3)),)*3
        rows, _ = run.log_spectrum(roots, 2.0)
        self.assertEqual(set(rows), {(1, 0), (0, 1), (1, 1)})
        self.assertEqual(len(set(rows.values())), 1)

    def test_modular_short_spectrum_exact_values(self):
        roots = (run.Quadratic(Fraction(3)),)*3
        evaluate = run.exact_trace_function(roots)
        expected = {(1, 0): 3, (0, 1): 3, (1, 1): 3,
                    (-1, 1): 6, (2, 1): 6, (1, 2): 6,
                    (3, 1): 15, (2, 3): 15, (-1, 2): 15}
        for slope, trace in expected.items():
            self.assertEqual(evaluate(*slope), run.Quadratic(Fraction(trace)))
        floating, _ = run.log_spectrum(roots, 4.0)
        self.assertEqual(set(floating), {s for s, t in expected.items() if t <= 6})

    def test_independent_box_small_cutoff(self):
        roots = (run.Quadratic(Fraction(3)),)*3
        floating, _ = run.log_spectrum(roots, 8)
        exact, _ = run.box_spectrum(roots, 8, 60)
        self.assertEqual(floating.keys(), exact.keys())
        self.assertLess(max(abs(floating[s]-float(exact[s][1])) for s in exact), 1e-13)

    def test_log_length_does_not_overflow(self):
        self.assertEqual(run.length_from_log(1000), 2000)

    def test_simultaneous_half_and_full_events(self):
        # At L=2: a full event contributes -4 and two half events +2.
        # They are one simultaneous jump, never three ordered intermediate states.
        lengths = [2.0, 4.0, 4.0]
        observed = run.block_metrics(lengths, 1.0)
        self.assertEqual(observed["M"], 1.0)
        self.assertAlmostEqual(observed["Q"], math.sqrt(0.5))
        self.assertEqual(observed["event_positions_in_block"], 1)

    def test_block_start_excludes_external_left_limit(self):
        # At T=1, count after all events: N(2)-4N(1)=1-4=-3.
        # The left limit at T is outside the block and cannot enter M(T).
        observed = run.block_metrics([1.0], 1.0)
        self.assertEqual(observed["M"], 3.0)
        self.assertAlmostEqual(observed["Q"], 3/math.sqrt(2))

    def test_prejump_limit_and_exact_integral(self):
        # D=1 on [1,1.5), then D=-3 until 2; half event at 3 is outside.
        observed = run.block_metrics([1.5], 1.0)
        self.assertEqual(observed["M"], 2.0)
        self.assertAlmostEqual(observed["Q"]**2, Fraction(1, 3)+Fraction(3, 2))

    def test_direct_counts_match_all_event_intervals(self):
        for lengths in ([1.0, 1.5, 2.0, 4.0], [2.0]*3 + [4.0]*3,
                        [1.1, 1.2, 1.999, 2.001, 3.0, 7.0]):
            for start in (1.0, 2.0):
                event = run.block_metrics(lengths, start)
                oracle = run.direct_block_metrics(lengths, start)
                for metric in ("M", "Q"):
                    self.assertAlmostEqual(event[metric], oracle[metric], places=13)

    def test_precision_context_restored(self):
        roots = (run.Quadratic(Fraction(3)),)*3
        with localcontext() as ctx:
            ctx.prec = 23
            run.box_spectrum(roots, 4, 60)
            self.assertEqual(ctx.prec, 23)
            self.assertGreater(run.decimal_length(roots[0]), Decimal(0))

    def test_conditional_bounds_zero_radius(self):
        lengths = [1.5, 2.0, 3.0, 3.0, 6.0]
        bounds = run.conditional_maximum_bounds(lengths, 1, "0")
        self.assertEqual(bounds["lower_exact_rational"], bounds["upper_exact_rational"])
        self.assertEqual(bounds["lower_approx"], run.block_metrics(lengths, 1)["M"])

    def test_conditional_bounds_cover_endpoint_perturbations(self):
        from itertools import product
        lengths = [1.5, 2.0, 3.0, 3.0]
        bounds = run.conditional_maximum_bounds(lengths, 1, "0.01")
        for signs in product((-1, 1), repeat=len(lengths)):
            altered = [ell+sign*0.01 for ell, sign in zip(lengths, signs)]
            maximum = run.block_metrics(altered, 1)["M"]
            self.assertGreaterEqual(maximum+1e-14, bounds["lower_approx"])
            self.assertLessEqual(maximum-1e-14, bounds["upper_approx"])


if __name__ == "__main__":
    unittest.main()
