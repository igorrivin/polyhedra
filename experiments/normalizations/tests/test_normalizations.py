"""Independent finite regressions for the normalization companion."""

from fractions import Fraction as Q
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


HERE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("normalization_checks", HERE/"run.py")
checks = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checks)


class NormalizationTests(unittest.TestCase):
    def test_exact_inputs_and_invalid_weights(self):
        self.assertEqual(checks.rational("0.3"), Q(3, 10))
        for value in (0.3, 1, True, None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                checks.rational(value)
        invalid = ((Q(0), Q(1, 2), Q(3, 4), Q(3, 4)),
                   (Q(1), Q(1, 3), Q(1, 3), Q(1, 3)),
                   (Q(1, 4),)*4, (0.5,)*4, (Q(2, 7),)*7)
        for weights in invalid:
            with self.subTest(weights=weights), self.assertRaises(ValueError):
                checks.validate_weights(weights, flat=True)
        with self.assertRaises(ValueError):
            checks.wp_from_weights((Q(1, 2),)*4)
        with self.assertRaises(ValueError):
            checks.in_final_chamber((Q(1, 2),)*4, 0.5)

    def test_tetrahedron_and_stack_factors(self):
        result = checks.normalization_checks()
        self.assertEqual(result["perimeter_minor_determinant"], -2)
        self.assertEqual(result["disintegrated_one_sheet_over_pi2"], Q(1, 4))
        self.assertEqual(result["disintegrated_two_sheets_over_pi2"], Q(1, 2))
        self.assertEqual(result["WP_two_sheets_over_pi2"], 2)
        zero = result["base_volume_fixtures"][0]
        self.assertEqual(zero["V11_stack_over_pi2"], Q(1, 12))
        self.assertEqual(zero["V11_effective_over_pi2"], Q(1, 6))
        self.assertEqual(result["large_cone_example"]["corrected_over_pi2"], Q(1, 4))

    def test_boundary_matrix_and_psi_relations(self):
        keys = checks.boundaries(5)
        def unit(key):
            return {k: Q(k == key) for k in keys}
        self.assertEqual(len(keys), 10)
        self.assertEqual(checks.pairing(unit((0, 1)), unit((0, 1))), -1)
        self.assertEqual(checks.pairing(unit((0, 1)), unit((2, 3))), 1)
        self.assertEqual(checks.pairing(unit((0, 1)), unit((1, 2))), 0)
        result = checks.intersection_checks()
        self.assertEqual(result["n5_integral_kappa_squared"], 5)
        # A distinct derivation of the averaged formula: explicitly average
        # the fixed-auxiliary relation over every pair of auxiliary marks.
        for n in (4, 5):
            for i in range(n):
                others = [j for j in range(n) if j != i]
                representatives = [checks.psi_class(n, i, (j, k))
                                   for j in others for k in others if j < k]
                explicit = {key: sum(row[key] for row in representatives)/len(representatives)
                            for key in checks.boundaries(n)}
                self.assertEqual(explicit, checks.average_psi(n, i))

    def test_light_triple_uses_complement_boundary_only_once(self):
        mu = tuple(map(Q, ("1/5", "3/10", "2/5", "1/2", "3/5")))
        light, balanced = checks.wall_data(mu)
        self.assertEqual(light[(3, 4)], (0, 1, 2))
        self.assertEqual(sum(mu[i] for i in light[(3, 4)]), Q(9, 10))
        self.assertNotIn((0, 1, 2), checks.boundaries(5))
        self.assertEqual(len(light), len(set(light)))
        self.assertEqual(balanced, ((2, 4),))
        with self.assertRaises(ValueError):
            checks.wall_data((Q(1, 5),)*5)

    def test_balanced_wall_and_strict_final_chamber(self):
        equal = (Q(1, 2),)*4
        light, balanced = checks.wall_data(equal)
        self.assertFalse(light)
        self.assertEqual(len(balanced), 3)
        self.assertEqual(checks.final_chamber(equal), (Q(1), False))
        self.assertTrue(checks.in_final_chamber(equal, Q(1)))
        self.assertFalse(checks.in_final_chamber(equal, Q(1001, 1000)))
        printed = tuple(map(Q, (".3", ".4", ".6", ".7")))
        self.assertEqual(checks.final_chamber(printed), (Q(1, 11), True))
        for epsilon, expected in ((Q(0), False), (Q(1, 12), True),
                                  (Q(1, 11), False), (Q(1, 10), False)):
            self.assertEqual(checks.in_final_chamber(printed, epsilon), expected)
        # Beyond that wall the direct class changes polynomial. The chamber
        # predicate is substantive, even though polynomials agree on the wall.
        epsilon = Q(1, 5)
        weights = tuple(w+epsilon*(1-w) for w in printed)
        self.assertNotEqual(checks.wp_from_weights(weights),
                            checks.evaluate_polynomial(checks.wp_polynomial(printed), 4*epsilon))

    def test_n4_closed_values_and_nonuniform_balanced_limit(self):
        equal = (Q(1, 2),)*4
        self.assertEqual(checks.wp_polynomial(equal), {1: Q(1), 2: Q(-1, 8)})
        self.assertEqual(checks.mcmullen_volume(equal)[0], 2)
        printed = tuple(map(Q, (".3", ".4", ".6", ".7")))
        self.assertEqual(checks.wp_polynomial(printed), {1: Q(3, 5), 2: Q(9, 40)})
        self.assertEqual(checks.mcmullen_volume(printed)[0], Q(6, 5))
        for delta in (Q(1, 10), Q(1, 100)):
            mu = (Q(1, 2)-delta,)*2+(Q(1, 2)+delta,)*2
            self.assertEqual(checks.wp_polynomial(mu), {1: 1-2*delta, 2: delta/2})
            self.assertEqual(checks.final_chamber(mu), (2*delta/(1+2*delta), True))
            self.assertEqual(checks.mcmullen_volume(mu)[0], 2-4*delta)

    def test_n5_uniform_dimension_and_volume_factors(self):
        mu = (Q(2, 5),)*5
        B, Xi = checks.flat_classes(mu)
        self.assertEqual(checks.pairing(B, B), Q(1, 5))
        self.assertEqual(checks.pairing(B, Xi), Q(1, 10))
        self.assertEqual(checks.pairing(Xi, Xi), Q(1, 20))
        self.assertEqual(checks.wp_polynomial(mu), {2: Q(2, 5), 3: Q(1, 5), 4: Q(1, 40)})
        self.assertEqual(checks.mcmullen_volume(mu),
                         (Q(8, 5), {3: Q(3, 5), 4: Q(-2), 5: Q(2)},
                          {3: 25, 4: 10, 5: 1}))
        self.assertEqual(checks.final_chamber(mu), (Q(1, 6), True))
        # Here a=1/2, epsilon=1/12 and w_i=9/20. This explicit rational
        # value catches both a mistaken pi normalization and a missing 2!.
        self.assertEqual(checks.wp_from_weights((Q(9, 20),)*5), Q(81, 640))

    def test_partition_enumeration_and_all_fixed_flat_inputs(self):
        for n, count in ((4, 15), (5, 52)):
            partitions = list(checks.set_partitions(tuple(range(n))))
            canonical = {tuple(sorted(tuple(sorted(block)) for block in partition))
                         for partition in partitions}
            self.assertEqual(len(partitions), count)
            self.assertEqual(len(canonical), count)
        fixture = json.loads((HERE/"fixture.json").read_text())
        for record in fixture["flat_weights"]:
            result = checks.flat_fixture(record)
            self.assertEqual(result["CH_over_pi_d_from_partitions"],
                             result["CH_over_pi_d_from_intersections"])

    def test_gram_pfaffian_and_fricke_sign(self):
        result = checks.gram_pfaffian_checks()
        self.assertEqual(result["gram_determinant"], -135)
        self.assertEqual(result["gram_density_coefficient"], Q(10, 3))
        self.assertEqual(result["skew_determinant"], 144)
        fixture = json.loads((HERE/"fixture.json").read_text())
        results = [checks.fricke_fixture(record) for record in fixture["sl2_fixtures"]]
        self.assertEqual(results[0]["Phi_z"], 3)
        self.assertEqual(results[0]["twist_numerator"], -3)
        self.assertFalse(results[-1]["chart_nondegenerate"])
        broken = dict(fixture["sl2_fixtures"][0], A=[["2", "1"], ["0", "1"]])
        with self.assertRaises(ValueError):
            checks.fricke_fixture(broken)

    def test_f_curve_probes_have_bounded_scope(self):
        fixture = json.loads((HERE/"fixture.json").read_text())
        for row in fixture["f_curve_probes"]:
            result = checks.f_curve_probe(tuple(map(Q, row["mu"])), row["parts"])
            self.assertEqual(result["beta_at_zero_pairing"], 0)
        with self.assertRaises(ValueError):
            checks.f_curve_pairings(6, [[0, 1], [1, 2], [3], [4, 5]])
        with self.assertRaises(ValueError):
            checks.wp_polynomial((Q(1, 3),)*6)

    def test_cli_from_other_cwd_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"result.json"
            command = [sys.executable, "-B", str(HERE/"run.py"), "--output", str(output)]
            completed = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            data = json.loads(output.read_text())
            self.assertTrue(data["checks_passed"])
            self.assertIn("git_status_porcelain", data["source"])
            self.assertEqual(len(data["flat_fixtures"]), 6)
            original = output.read_bytes()
            repeated = subprocess.run(command, cwd=directory, capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("refusing to overwrite", repeated.stderr)
            self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
