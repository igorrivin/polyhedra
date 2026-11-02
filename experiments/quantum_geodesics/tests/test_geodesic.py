"""Geodesic identity, branch, tail and conditioning regressions."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import mpmath
import sympy as sp


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.quantum_geodesics import (  # noqa: E402
    common, geodesic_exact, geometry, kernels, run, twist_integrals,
)


def fixture():
    return json.loads((HERE/"fixture.json").read_text())["geodesic"]


class ExactGeodesicTests(unittest.TestCase):
    def test_signed_trace_identity_retains_equal_length_labels(self):
        result = geodesic_exact.trace_checks(fixture()["traces"])
        curves = result["torus_blocks"][0]["curves"]
        self.assertEqual([row["trace"] for row in curves], [9, 9, 11])
        self.assertEqual(len({row["topological_label"] for row in curves}), 3)
        data = deepcopy(fixture()["traces"])
        data["shear_seeds"] = data["shear_seeds"][:2]
        with self.assertRaises(ValueError):
            geodesic_exact.trace_checks(data)

    def test_formal_kernel_and_partition_telescope_without_numerical_tail(self):
        result = geodesic_exact.kernel_telescope([1, 4, 180])
        self.assertEqual(result["rows"][0]["remaining_coefficient"], sp.Rational(1, 2))
        self.assertEqual(result["rows"][1]["remaining_coefficient"], -sp.Rational(1, 16))
        partition = geodesic_exact.partition_checks(fixture()["partition"])
        self.assertTrue(partition["uniform_windows"])
        self.assertEqual(geodesic_exact.uniform_window(sp.Rational(2), sp.Rational(2)), 0)
        self.assertEqual(geodesic_exact.reduce_twist("7", "261.59"), (sp.Rational(259, 100), 37))
        self.assertEqual(geodesic_exact.reduce_twist("2", "1"), (-1, 1))

    def test_hessian_identities_reduce_hyperbolic_relations(self):
        self.assertEqual(geodesic_exact.hessian_checks()["check_count"], 4)

    def test_windings_and_cyclic_spacing_are_retained(self):
        result = geodesic_exact.position_checks(fixture()["matching"])
        self.assertTrue(result["rows"][0]["positions_match"])
        self.assertFalse(result["rows"][1]["positions_match"])
        self.assertNotEqual(result["rows"][0]["base_endpoints"], result["rows"][0]["lifted_endpoints"])
        corrupt = deepcopy(fixture()["matching"])
        corrupt["endpoint_lists"][1]["expected_match"] = True
        with self.assertRaises(ArithmeticError):
            geodesic_exact.position_checks(corrupt)

    def test_cusp_matrix_sign_and_markov_flip(self):
        result = geodesic_exact.cusp_checks(fixture()["cusp"])
        row = result["cusp_matrices"][0]
        self.assertEqual(sp.Matrix(row["B"]).trace(), -row["t_b"])
        triangle = result["triangles"][0]
        self.assertEqual(triangle["H"], 6)
        self.assertEqual(triangle["traces"], [3, 3, 3])
        self.assertEqual(triangle["flipped_u"], 2)


class KernelConditioningTests(unittest.TestCase):
    def test_stable_h_retains_large_trace_signal(self):
        ctx = common.context(70, 20)
        t = ctx.mpf("1e1000")
        stable = kernels.h_trace(ctx, t)
        self.assertGreater(stable, 0)
        self.assertEqual(1-ctx.sqrt(1-4/(t*t)), 0)
        common.NumericChecks(ctx, 70, 20).positive("scaled h", t*t*stable, ctx.mpf(2))

    def test_kernel_near_six_and_unresolved_tail_are_distinguished(self):
        data = {"inputs": ["6.00000000000000000001", "1000"], "depths": [4, 180], "simple_traces": ["3"]}
        result = kernels.kernel_checks(data, 70, 100)
        rows = result["rows"]
        self.assertTrue(any("cancellation-limited" in row["residual_status"] for row in rows))
        ctx = common.context(70, 100)
        for row in rows:
            self.assertGreater(ctx.mpf(row["positive_B_N"]), 0)
            self.assertTrue(ctx.isfinite(ctx.mpf(row["log_B_N"])))
        partial, tail, _, _ = kernels.kernel_partial(ctx, ctx.mpf(9), 4)
        shifted = kernels.kernel_partial(ctx, ctx.mpf(11), 4)[0]
        self.assertLess(abs((2*partial+shifted-kernels.h_trace(ctx, ctx.mpf(3)))/(-2*tail)-1), ctx.mpf("1e-100"))

    def test_kernel_and_real_branch_domains_reject_nonfinite_and_boundary(self):
        ctx = common.context(70)
        for bad in (ctx.nan, ctx.inf, -ctx.inf, ctx.mpc(3, 1)):
            for function, args in ((kernels.h_trace, (bad,)), (kernels.kernel_partial, (bad, 4)),
                                   (kernels.h_twist, (ctx.mpf(1), bad)), (kernels.shadow, (bad,))):
                with self.subTest(function=function.__name__, value=str(bad)), self.assertRaises(ValueError):
                    function(ctx, *args)
        for t in (-1, 0, 2):
            with self.assertRaises(ValueError):
                kernels.h_trace(ctx, t)
        with self.assertRaises(ValueError):
            kernels.kernel_partial(ctx, 6, 4)
        with self.assertRaises(ValueError):
            geometry.acosh_real(ctx, ctx.mpf(".999999999999999999"))
        with self.assertRaises(ValueError):
            kernels.partition_tail(ctx, 1, 1, 4)

    def test_twist_and_shadow_tiny_tails_never_use_zero_reference(self):
        ctx = common.context(70, 20)
        H = kernels.h_twist(ctx, ctx.mpf(7), ctx.mpf(1000))
        tail, length = kernels.partition_tail(ctx, ctx.mpf(7), ctx.mpf("2.59"), 150)
        self.assertGreater(H, 0)
        self.assertGreater(tail, 0)
        self.assertGreater(length, 1000)
        self.assertEqual(ctx.tanh((1000+ctx.mpf(7)/2)/2)-ctx.tanh((1000-ctx.mpf(7)/2)/2), 0)
        self.assertEqual(1-(ctx.tanh((ctx.mpf("2.59")+length)/2)-ctx.tanh((ctx.mpf("2.59")-length)/2))/2, 0)
        shadow = kernels.shadow(ctx, ctx.mpf(1000))
        self.assertGreater(shadow, 0)
        self.assertEqual(2*ctx.log(ctx.coth(500)), 0)
        common.NumericChecks(ctx, 70, 20).positive("scaled large shadow", shadow/(4*ctx.exp(-1000)), ctx.mpf(1))
        for positive in (H, tail, shadow):
            for corrupt in (ctx.mpf(0), positive/2, -positive):
                with self.assertRaises(ArithmeticError):
                    common.NumericChecks(ctx, 70, 20).positive("lost tiny signal", corrupt, positive)

    def test_shadow_circle_and_orientation_factors(self):
        result = kernels.shadow_checks({"distances": [".1", "8", "1000"]}, 70, 20)
        self.assertIn("cancellation-limited", result["rows"][-1]["direct_route_status"])
        ctx = common.context(70, 20)
        row = result["rows"][0]
        self.assertEqual(ctx.mpf(row["unoriented_arc_two_shadows"]), 2*ctx.mpf(row["positive_shadow"]))


class LocalGeometryTests(unittest.TestCase):
    def test_small_cuff_matrix_reference_and_large_cuff_minimum(self):
        ctx = common.context(70, 80)
        a, b = ctx.mpf("1e-12"), ctx.mpf(".7")
        X, B = geometry.torus_matrices(ctx, a, b, ctx.mpf(".5"))
        value = geometry.trace(X*B*X**-1*B**-1)
        target = -2*ctx.cosh(b/2)
        common.NumericChecks(ctx, 70, 80).close("small cuff commutator", value, target, scale=abs(target))
        minimum = geometry.torus_length(ctx, ctx.mpf(1000), ctx.mpf(0), ctx.mpf(0))
        self.assertGreater(minimum, 0)
        self.assertEqual(geometry.matrix_length(ctx, ctx.mpf(1000), ctx.mpf(0), ctx.mpf(0)), 0)
        common.NumericChecks(ctx, 70, 80).positive("scaled positive minimum", minimum/(4*ctx.exp(-500)), ctx.mpf(1))

    def test_distance_derivatives_and_orientation(self):
        result = geometry.distance_checks({"distances": [".03", "2"], "endpoints": [["0", "0"], ["1", "-2"]]}, 70, 20)
        self.assertEqual(len(result["rows"]), 4)
        ctx = common.context(70)
        self.assertNotEqual(geometry.local_distance(ctx, 1, 1, 2), geometry.local_distance(ctx, 1, 1, -2))

    def test_geometry_and_integral_invalid_domains(self):
        ctx = common.context(70)
        invalid_calls = [(geometry.local_distance, (0, 0, 0)), (geometry.torus_delta, (0, 0)),
                         (geometry.torus_delta, (1, -1)), (geometry.seam_distance, (1, 0, 0)),
                         (geometry.seam_distance, (1, 1, -1)),
                         (twist_integrals.twist_integrals, (1, 0, 0, 12)),
                         (twist_integrals.twist_integrals, (1, 0, 2, 0))]
        for function, args in invalid_calls:
            with self.subTest(function=function.__name__, args=args), self.assertRaises(ValueError):
                function(ctx, *args)
        for bad in (ctx.nan, ctx.inf, ctx.mpc(1, 1)):
            with self.assertRaises(ValueError):
                geometry.local_distance(ctx, 1, bad, 0)
            with self.assertRaises(ValueError):
                geometry.torus_delta(ctx, bad, 0)

    def test_finite_coarea_s2_tail_and_sublevel_endpoints(self):
        data = {"pairs": [["1", "0"]], "powers": ["2"], "cutoffs": [12], "sublevel_offsets": [".1", "2"]}
        result = twist_integrals.integral_checks(data, 70, 20)
        ctx = common.context(70, 20)
        row = result["rows"][0]
        self.assertGreater(ctx.mpf(row["exact_s2_tail_stable"]), 0)
        self.assertEqual(result["sublevels"][0]["width"], "0.0")
        self.assertEqual(result["sublevels"][1]["width"], "0.0")
        with self.assertRaises(ArithmeticError):
            common.NumericChecks(ctx, 70, 20).positive("wrong coarea multiplicity", ctx.mpf(row["coarea"])/2, ctx.mpf(row["direct"]))

    def test_position_match_does_not_force_stationarity_and_cusp_length_can_be_negative(self):
        result = geometry.matching_checks(fixture()["matching"], 70, 20)
        self.assertEqual(result["rows"][0]["derivative"], "0.0")
        self.assertLess(common.context(70).mpf(result["rows"][1]["derivative"]), 0)
        result = geometry.cusp_numerics(fixture()["cusp"], 70, 20)
        row = next(row for row in result["torus_rows"] if row["t"] == "3" and row["H"] == "20")
        self.assertLess(common.context(70).mpf(row["signed_length"]), 0)


class FullDriverPolicyTests(unittest.TestCase):
    def test_partial_geodesic_coverage_and_changed_git_observation_rejected(self):
        data = run.load_fixture()
        data["geodesic"]["shadow"]["distances"].pop()
        with self.assertRaises(ValueError):
            run.validate_fixture(data)
        before = {"sources": [1], "guarded_dependencies": [2], "git_commit": "a", "git_dirty": True,
                  "git_status_porcelain": [" M one"], "live_tex_source_observations": [3]}
        after = deepcopy(before)
        after["git_status_porcelain"] = [" M two"]
        with self.assertRaises(ArithmeticError):
            run.verify_source_unchanged(before, after)
        after = deepcopy(before)
        after["live_tex_source_observations"] = [4]
        with self.assertRaises(ArithmeticError):
            run.verify_source_unchanged(before, after)

    def test_geodesic_imports_preserve_global_precision_and_have_no_output(self):
        previous = mpmath.mp.dps
        geometry.distance_checks({"distances": [".5"], "endpoints": [["0", "0"]]}, 70, 20)
        self.assertEqual(mpmath.mp.dps, previous)
        code = ("import sys; sys.path.insert(0,"+repr(str(ROOT))+"); import mpmath; p=mpmath.mp.dps; "
                "from experiments.quantum_geodesics import geodesic_exact,geometry,kernels,twist_integrals; "
                "assert mpmath.mp.dps==p")
        completed = subprocess.run([sys.executable, "-c", code], cwd="/private/tmp", capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")


if __name__ == "__main__":
    unittest.main()
