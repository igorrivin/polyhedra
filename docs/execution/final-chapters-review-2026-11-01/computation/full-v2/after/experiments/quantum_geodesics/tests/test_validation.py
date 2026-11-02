"""CR01/CR02: complete accepted coverage and locally bound provenance gates."""

from copy import deepcopy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parents[1]
ROOT = HERE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.quantum_geodesics import run  # noqa: E402


class ProfileValidationTests(unittest.TestCase):
    def reject_before_calculation(self, data):
        """A bad profile cannot reach source collection, calculate, or result writing."""
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/"must-not-exist.json"
            with patch.object(run, "load_fixture", return_value=data):
                with patch.object(run, "source_state") as state:
                    with patch.object(run, "calculate") as calculate:
                        with self.assertRaises(ValueError):
                            run.main(["--output", str(output)])
                        state.assert_not_called()
                        calculate.assert_not_called()
            self.assertFalse(output.exists())

    def altered(self, mutate):
        data = run.load_fixture()
        mutate(data)
        self.reject_before_calculation(data)

    def test_CR01_missing_negative_q_slope(self):
        self.altered(lambda f: f["quantum"]["peripheral"]["slopes"].pop())

    def test_CR01_three_duplicate_simplexes_replace_both_boxes(self):
        self.altered(lambda f: f["quantum"]["klein"].update(
            polyhedra=[deepcopy(f["quantum"]["klein"]["polyhedra"][0]) for _ in range(3)]))

    def test_CR01_large_partition_replaced_by_N_zero(self):
        self.altered(lambda f: f["geodesic"]["partition"].update(large_partition={"a": "7", "tau": "0", "N": 0}))

    def test_CR01_missing_shifted_nonstationary_case(self):
        self.altered(lambda f: f["geodesic"]["matching"]["stationarity"].pop())

    def test_CR01_missing_inconsistent_endpoint_spacing(self):
        self.altered(lambda f: f["geodesic"]["matching"]["endpoint_lists"].pop())

    def test_CR02_missing_formula_contracts(self):
        self.altered(lambda f: f.update(formula_contracts={}))

    def test_CR02_missing_accepted_source_map(self):
        self.altered(lambda f: f.update(accepted_manuscript_sha256={}))

    def test_CR02_wrong_quantum_acceptance_hash(self):
        self.altered(lambda f: f["formula_contracts"]["quantum"].update(review_acceptance_sha256="0"*64))

    def test_CR02_wrong_quantum_source_freeze_hash(self):
        self.altered(lambda f: f["formula_contracts"]["quantum"].update(accepted_source_freeze_sha256="0"*64))

    def test_CR02_wrong_geodesic_contract_acceptance_hash(self):
        self.altered(lambda f: f["formula_contracts"]["geodesic"].update(review_acceptance_sha256="0"*64))

    def test_CR02_wrong_geodesic_source_acceptance_hash(self):
        self.altered(lambda f: f["formula_contracts"]["geodesic"].update(final_source_review_sha256="0"*64))

    def test_CR02_wrong_geodesic_accepted_source_set_hash(self):
        self.altered(lambda f: f["formula_contracts"]["geodesic"].update(accepted_source_set_sha256="0"*64))

    def test_CR02_wrong_accepted_manuscript_pin(self):
        self.altered(lambda f: f["accepted_manuscript_sha256"].update({"book/chapters/10-quantum-introduction.tex": "0"*64}))

    def test_unchanged_complete_profile_succeeds_independent_of_dict_order(self):
        data = run.load_fixture()
        self.assertIs(run.validate_fixture(data), data)
        reordered = {key: data[key] for key in reversed(data)}
        self.assertIs(run.validate_fixture(reordered), reordered)
        self.assertEqual(len(data["accepted_manuscript_sha256"]), 14)
        self.assertEqual(len(data["guarded_dependency_sha256"]), 3)

    def test_omissions_and_duplicates_cover_other_scientific_grids(self):
        paths = [
            ("Q1", ("quantum", "figure_eight_N")),
            ("Q3_shifts", ("quantum", "peripheral", "shift_points")),
            ("Q4", ("quantum", "charges", "weights")),
            ("G1", ("geodesic", "unfolding", "alternating_depths")),
            ("G2", ("geodesic", "traces", "shear_seeds")),
            ("G3", ("geodesic", "kernel", "inputs")),
            ("G4", ("geodesic", "distance", "endpoints")),
            ("G5", ("geodesic", "holonomy", "large_cuff_minima")),
            ("G6", ("geodesic", "integrals", "pairs")),
            ("G7_windows", ("geodesic", "partition", "uniform_windows")),
            ("G9", ("geodesic", "cusp", "decoration_rescalings")),
            ("G10", ("geodesic", "shadow", "distances")),
        ]
        for name, path in paths:
            for operation in ("omit", "duplicate"):
                with self.subTest(group=name, operation=operation):
                    data = run.load_fixture()
                    value = data
                    for key in path:
                        value = value[key]
                    if operation == "omit":
                        value.pop()
                    else:
                        value.append(deepcopy(value[0]))
                    self.reject_before_calculation(data)

    def test_substitutions_and_extra_profile_fields_rejected(self):
        mutations = [
            lambda f: f["geodesic"]["matching"]["endpoint_lists"][0]["left_windings"].__setitem__(0, 1),
            lambda f: f["geodesic"]["guard_digits"].update(kernel=99),
            lambda f: f["quantum"]["charges"].update(extra_unreviewed_weights=[]),
            lambda f: f["quantum"].pop("charges"),
            lambda f: f.update(precisions=[70.0, 110]),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                self.altered(mutate)

    def test_missing_extra_and_altered_provenance_fields_rejected(self):
        mutations = [
            lambda f: f["formula_contracts"].pop("geodesic"),
            lambda f: f["formula_contracts"].update(unreviewed={}),
            lambda f: f["formula_contracts"]["quantum"].update(review_evidence_manifest_sha256="0"*64),
            lambda f: f["formula_contracts"]["geodesic"].update(independent_probe_result_sha256="0"*64),
            lambda f: f["formula_contracts"]["quantum"].update(path="../outside.md"),
            lambda f: f["accepted_manuscript_sha256"].pop("book/chapters/11-quantum-degeneration.tex"),
            lambda f: f["accepted_manuscript_sha256"].update({"book/chapters/unreviewed.tex": "0"*64}),
            lambda f: f["guarded_dependency_sha256"].pop("experiments/quantum_surgery/exact.py"),
            lambda f: f["guarded_dependency_sha256"].update({"experiments/quantum_surgery/exact.py": "0"*64}),
            lambda f: f["guarded_dependency_sha256"].update({"unreviewed.py": "0"*64}),
        ]
        for index, mutate in enumerate(mutations):
            with self.subTest(mutation=index):
                self.altered(mutate)

    def test_all_six_local_provenance_files_are_bound_by_bytes(self):
        filenames = ["quantum-targets.md", "quantum-mathematical-acceptance.json", "quantum-source-freeze.json",
                     "geodesic-targets.md", "geodesic-contract-acceptance.json", "geodesic-source-acceptance.json"]
        original = Path.read_bytes
        for filename in filenames:
            target = HERE/"contracts"/filename

            def altered_bytes(path):
                data = original(path)
                return data+b"\n" if path == target else data

            with self.subTest(filename=filename), patch.object(Path, "read_bytes", altered_bytes):
                self.reject_before_calculation(run.load_fixture())

    def test_source_observer_rejects_malformed_accepted_map(self):
        data = run.load_fixture()
        data["accepted_manuscript_sha256"] = {}
        with self.assertRaises(ValueError):
            run.source_state(data)

    def test_later_live_manuscript_edits_remain_separate_observations(self):
        data = run.load_fixture()
        relative = "book/chapters/10-quantum-introduction.tex"
        target = ROOT/relative
        original = Path.read_bytes

        def changed_live_source(path):
            contents = original(path)
            return contents+b"\n% later authorized computational prose pointer\n" if path == target else contents

        with patch.object(Path, "read_bytes", changed_live_source):
            state = run.source_state(data)
        observation = next(row for row in state["live_manuscript_observation"] if row["path"] == relative)
        self.assertEqual(observation["accepted_contract_source_sha256"], data["accepted_manuscript_sha256"][relative])
        self.assertFalse(observation["matches_accepted_snapshot"])
        self.assertNotEqual(observation["current_sha256"], observation["accepted_contract_source_sha256"])


if __name__ == "__main__":
    unittest.main()
