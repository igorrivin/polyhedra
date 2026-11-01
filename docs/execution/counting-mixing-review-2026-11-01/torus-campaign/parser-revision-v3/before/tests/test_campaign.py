"""Independent failure, endpoint, multiplicity, and exact-arithmetic regressions."""
from fractions import Fraction
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("new_torus_campaign", HERE / "run.py")
run = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = run
spec.loader.exec_module(run)


class NativeCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="torus-campaign-tests-")
        cls.folder = Path(cls.temp.name)
        cls.binary = cls.folder / "campaign"
        subprocess.run(["/usr/bin/clang++", *run.FLAGS, str(HERE / "campaign.cpp"),
                        "-o", str(cls.binary)], check=True, capture_output=True)
        cls.oracle = run.load_frozen_driver()
        cls.serial = 0

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def metric(self, lengths, start, epsilon="1e-6", expect_success=True):
        type(self).serial += 1
        path = self.folder / str(self.serial)
        path.write_text("\n".join(map(str, lengths)))
        output = path.with_suffix(".json")
        completed = subprocess.run([str(self.binary), "metrics", str(path), str(start),
                                    str(output), epsilon, "1"], text=True, capture_output=True)
        if not expect_success:
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output.exists())
            return
        self.assertEqual(completed.returncode, 0, completed.stderr)
        return json.loads(output.read_text())

    def test_hand_computed_simultaneous_events(self):
        # Both full and half streams coincide at2 and4; the left limit at2
        # is excluded. Independent exact fixture: M=5/2 and Q^2=49/20.
        row = self.metric([2, 2, 4, 5, 8], 2, "0")
        self.assertEqual(Fraction(row["block"]["M"]["exact_rational_for_stored_events"]), Fraction(5, 2))
        self.assertAlmostEqual(row["block"]["Q_squared"], 49/20, places=14)
        self.assertEqual(row["sensitivity"]["lower_exact_rational"], "5/2")
        self.assertEqual(row["sensitivity"]["upper_exact_rational"], "5/2")

    def test_initial_external_left_limit_is_excluded(self):
        row = self.metric([1], 1, "0")["block"]
        self.assertEqual(row["M"]["value"], 3)
        self.assertAlmostEqual(row["Q_squared"], 4.5, places=14)

    def test_prejump_and_terminal_value_both_count(self):
        row = self.metric([1.5], 1, "0")["block"]
        self.assertEqual(row["M"]["value"], 2)
        self.assertAlmostEqual(row["Q_squared"], 11/6, places=14)
        terminal = self.metric([2, 2, 2], 1, "0")["block"]
        self.assertEqual(terminal["M"]["value"], 4.5)
        self.assertEqual(terminal["M"]["side"], "value_after_group")

    def test_nearby_unequal_events_are_never_tolerance_merged(self):
        lengths = [1.5, math.nextafter(1.5, math.inf), 3, 3, 6]
        row = self.metric(lengths, 1)
        reference = self.oracle.block_metrics(lengths, 1)
        self.assertEqual(row["block"]["event_positions_in_block"], reference["event_positions_in_block"])
        self.assertAlmostEqual(row["block"]["M"]["value"], reference["M"], places=14)
        self.assertAlmostEqual(row["block"]["Q"], reference["Q"], places=14)

    def test_four_stream_exact_fractions_match_python_oracle(self):
        # Non-dyadic binary64 values and endpoints straddling1 and2 test the
        # denominator conversion as well as independent uncertain-event order.
        for lengths in ([1, 1.0000001, 1.5, 2, 4],
                        [1.1, 1.2, 1.9999999, 2.0000001, 3, 7],
                        [2, 2, 4, 5, 8]):
            for start in (1, 2):
                row = self.metric(lengths, start)
                reference = self.oracle.conditional_maximum_bounds(lengths, start, "1e-6")
                for key in ("lower_exact_rational", "upper_exact_rational"):
                    self.assertEqual(Fraction(row["sensitivity"][key]), Fraction(reference[key]))

    def test_nonfinite_nonpositive_and_range_inputs_fail(self):
        for lengths in ([float("nan")], [float("inf")], [0], [-1], [0.9], [8194]):
            self.metric(lengths, 1, expect_success=False)
        self.metric([1, 2], 0, expect_success=False)
        self.metric([1, 2], 4096, expect_success=False)

    def test_root_and_cutoff_gates(self):
        for roots, cutoff in (([3, 3, 4], 64), ([float("nan"), 3, 3], 64),
                              ([3, 3, 3], 63), ([3, 3, 3], 16384)):
            prefix = self.folder / ("bad-"+str(self.serial))
            type(self).serial += 1
            result = subprocess.run([str(self.binary), "campaign", "invalid", str(cutoff), str(prefix),
                                     *map(str, roots), "0"], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(Path(str(prefix)+".native.json").exists())

    def test_equal_root_multiplicity_and_exclusive_outputs(self):
        prefix = self.folder / "multiplicity"
        command = [str(self.binary), "campaign", "modular", "64", str(prefix), "3", "3", "3", "1"]
        first = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        result = json.loads(Path(str(prefix)+".native.json").read_text())
        rows = {tuple(r["slope"]): r for r in result["curves_through_64"]}
        self.assertEqual(result["count_through_cutoff"], 1104)
        self.assertEqual(result["root_count"], 3)
        self.assertEqual({rows[s]["length_binary64"] for s in ((1, 0), (0, 1), (1, 1))},
                         {rows[1, 0]["length_binary64"]})
        self.assertEqual(sum(result["sector_counts"])+3, 1104)
        old_hash = run.digest(Path(str(prefix)+".native.json"))
        second = subprocess.run(command, capture_output=True)
        self.assertNotEqual(second.returncode, 0)
        self.assertEqual(run.digest(Path(str(prefix)+".native.json")), old_hash)

    def test_path_reconstruction_and_independent_traces(self):
        fixture = json.loads((run.OLD / "fixture.json").read_text())
        for record in fixture["surfaces"]:
            roots = self.oracle.fixture_roots(record)
            exact = self.oracle.exact_trace_function(roots)
            for slope in ((1, 0), (1, 1), (-1, 1), (9, 2), (-2, 9), (5, 8), (101, 1)):
                from decimal import localcontext, Decimal
                with localcontext() as ctx:
                    ctx.prec = 100
                    reference = self.oracle.decimal_length(exact(*slope))
                    observed = run.direct_path_length(record, slope, 100)
                    self.assertLess(abs(reference-observed), Decimal("1e-90"))
        with self.assertRaises(ValueError):
            run.sector_path((2, 2))


if __name__ == "__main__":
    unittest.main()
