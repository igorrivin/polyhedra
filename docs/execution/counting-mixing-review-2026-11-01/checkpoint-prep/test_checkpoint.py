"""Focused adversarial tests for checkpoint gates, including python -O runs.

Uses preserved author JSON as schema fixtures; does not call either experiment,
touch canonical source, build a PDF, or represent a clean scientific replay.
"""
import ast
import copy
from hashlib import sha256
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from checkpoint_lib import (
    CheckpointError, counting_comparison, load_json, masked, merge_hashes, relative_path,
    source_state, torus_report_comparison,
)

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent


class ScientificMutationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.counting = load_json(OUTER / "computation/revision-v2/author-result-60-90-v2.json")
        cls.torus = load_json(OUTER / "torus-campaign/full8192-author-v2/result.json")

    def test_finite_exact_self_comparison(self):
        self.assertTrue(counting_comparison(self.counting, self.counting)["identical_scientific_payload"])

    def test_torus_exact_self_comparison(self):
        self.assertEqual(torus_report_comparison(self.torus, self.torus)["blocks"], 20)

    def test_only_declared_elapsed_field_may_change(self):
        changed = copy.deepcopy(self.counting)
        changed["elapsed_seconds"] += 1
        self.assertTrue(counting_comparison(self.counting, changed)["identical_scientific_payload"])
        changed["exact"]["scientific_time"] = "unknown scientific field must survive"
        with self.assertRaises(CheckpointError):
            counting_comparison(self.counting, changed)

    def test_finite_count_mutation_rejected(self):
        changed = copy.deepcopy(self.counting)
        changed["check_counts"]["exact"] += 1
        with self.assertRaises(CheckpointError):
            counting_comparison(self.counting, changed)

    def test_false_success_type_rejected(self):
        changed = copy.deepcopy(self.counting)
        changed["checks_passed"] = 1
        with self.assertRaises(CheckpointError):
            counting_comparison(self.counting, changed)

    def test_unexpected_source_state_field_rejected(self):
        changed = copy.deepcopy(self.counting)
        changed["source"]["silently_lost_field"] = 1
        changed["source_at_completion"]["silently_lost_field"] = 1
        with self.assertRaises(CheckpointError):
            counting_comparison(changed, changed)

    def test_missing_allowed_field_rejected(self):
        changed = copy.deepcopy(self.counting)
        del changed["generated_at_utc"]
        with self.assertRaises(CheckpointError):
            counting_comparison(self.counting, changed)

    def test_torus_scientific_count_mutation_rejected(self):
        changed = copy.deepcopy(self.torus)
        changed["surfaces"][0]["count_through_cutoff"] += 1
        with self.assertRaises(CheckpointError):
            torus_report_comparison(self.torus, changed)

    def test_torus_conditional_envelope_mutation_rejected(self):
        changed = copy.deepcopy(self.torus)
        changed["surfaces"][0]["conditional_M_bounds"][0]["width_approx"] += 1
        with self.assertRaises(CheckpointError):
            torus_report_comparison(self.torus, changed)

    def test_torus_unknown_timing_key_rejected_even_on_both_sides(self):
        changed = copy.deepcopy(self.torus)
        changed["surfaces"][0]["timing_seconds"]["scientific_time"] = 1
        with self.assertRaises(CheckpointError):
            torus_report_comparison(changed, changed)

    def test_torus_stream_hash_mutation_rejected(self):
        changed = copy.deepcopy(self.torus)
        changed["surfaces"][0]["raw_streams"][0]["sha256"] = "0" * 64
        with self.assertRaises(CheckpointError):
            torus_report_comparison(self.torus, changed)

    def test_torus_unknown_provenance_field_not_dropped(self):
        changed = copy.deepcopy(self.torus)
        changed["provenance"]["new_science_field"] = "must compare"
        with self.assertRaises(CheckpointError):
            torus_report_comparison(self.torus, changed)

    def test_pointer_exclusion_cannot_be_missing_or_overlap(self):
        for pointers in (["/x/missing"], ["/x", "/x/y"]):
            with self.assertRaises(CheckpointError):
                masked({"x": {"y": 1}}, pointers)


class DirectSourceMutationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="gate-test-", dir=HERE)
        self.root = Path(self.temp.name)
        self.env = {**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                    "GIT_AUTHOR_NAME": "Checkpoint fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                    "GIT_COMMITTER_NAME": "Checkpoint fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid"}
        self.run_git("init", "-q")
        (self.root / "source.py").write_text("fixed source\n")
        self.run_git("add", "source.py")
        self.run_git("commit", "-qm", "source fixture")
        self.commit = self.run_git("rev-parse", "HEAD").strip()
        self.expected = {"source.py": sha256((self.root / "source.py").read_bytes()).hexdigest()}

    def tearDown(self):
        self.temp.cleanup()

    def run_git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, env=self.env, text=True)

    def test_clean_source_accepts(self):
        self.assertEqual(source_state(self.root, self.commit, self.expected)["status_porcelain"], "")

    def test_file_mutation_rejected_directly_even_without_status_gate(self):
        (self.root / "source.py").write_text("changed source\n")
        with self.assertRaises(CheckpointError):
            source_state(self.root, self.commit, self.expected, clean=False)

    def test_head_mutation_rejected_even_when_source_bytes_match(self):
        self.run_git("commit", "--allow-empty", "-qm", "new HEAD with same tree")
        with self.assertRaises(CheckpointError):
            source_state(self.root, self.commit, self.expected)

    def test_untracked_output_breaks_clean_source_requirement(self):
        (self.root / "output.json").write_text("{}\n")
        with self.assertRaises(CheckpointError):
            source_state(self.root, self.commit, self.expected)

    def test_forged_expected_digest_rejected_against_git_blob(self):
        changed = "changed source\n"
        (self.root / "source.py").write_text(changed)
        with self.assertRaises(CheckpointError):
            source_state(self.root, self.commit, {"source.py": sha256(changed.encode()).hexdigest()}, clean=False)


class InputBoundaryTests(unittest.TestCase):
    def test_unfinished_contract_cannot_claim_success(self):
        from verify_checkpoint import approved_contract
        with self.assertRaises(CheckpointError):
            approved_contract(HERE, {"schema_version": 1, "ready": False})

    def test_duplicate_and_nonfinite_JSON_rejected(self):
        for payload in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":1e400}'):
            with tempfile.NamedTemporaryFile(mode="w", dir=HERE) as handle:
                handle.write(payload)
                handle.flush()
                with self.assertRaises(CheckpointError):
                    load_json(handle.name)

    def test_path_traversal_and_sidecar_rejected(self):
        for name in ("../elsewhere", "/absolute", "sub/._sidecar"):
            with self.assertRaises(CheckpointError):
                relative_path(HERE, name)

    def test_conflicting_hash_domains_rejected(self):
        with self.assertRaises(CheckpointError):
            merge_hashes({"same": "one"}, {"same": "other"})

    def test_acceptance_programs_have_no_removable_assert_gates(self):
        for name in ("checkpoint_lib.py", "verify_checkpoint.py", "run_clean_replay.py", "compare_replays.py"):
            nodes = ast.walk(ast.parse((HERE / name).read_text()))
            self.assertFalse(any(isinstance(node, ast.Assert) for node in nodes), name)


if __name__ == "__main__":
    unittest.main()
