"""Synthetic gate fixtures only: these tests do not replay monograph science."""
from __future__ import annotations

import contextlib
import copy
from hashlib import sha256
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import checkpoint_lib as lib
import compare_replays as compare
import run_clean_replay as replay
import verify_checkpoint as verify

HERE = Path(__file__).resolve().parent
DRIVER = '''# Synthetic gate fixture; not a scientific experiment.
from pathlib import Path
import json
import sys
output = Path(sys.argv[-1])
control = json.loads((output.parent / "control.json").read_text())
if control["mode"] == "command_failure":
    raise SystemExit(7)
data = json.loads((output.parent / "candidate-template.json").read_text())
if control["mode"] == "wrong_result":
    data["source_before"]["git_dirty"] = True
with output.open("x") as handle:
    json.dump(data, handle)
if control["mode"] in ("spec_drift", "approval_drift"):
    path = output.parent / ("spec.json" if control["mode"] == "spec_drift" else "integration.json")
    changed = json.loads(path.read_text())
    changed["unused_note"] = "changed during command"
    path.write_text(json.dumps(changed))
if control["mode"] == "runtime_drift":
    Path(__file__).write_text(Path(__file__).read_text() + "# changed during command\\n")
'''


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def synthetic_git(root, *args):
    return subprocess.check_output(["git", "-c", "user.name=Checkpoint Gate Fixture",
                                    "-c", "user.email=synthetic@example.invalid", "-c", "commit.gpgsign=false",
                                    "-c", "core.hooksPath=/dev/null", *args], cwd=root, env=lib.ENV, text=True).strip()


class GateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="synthetic-gate-", dir=HERE)
        self.base = Path(self.temp.name)
        self.root, self.outer = self.base / "repository", self.base / "outer"
        self.root.mkdir()
        self.outer.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, graph_mode="connected"):
        synthetic_git(self.root, "init", "-q")
        (self.root / "README.md").write_text("Synthetic gate fixture only.\n")
        (self.root / "dependency.txt").write_text("Synthetic frozen dependency.\n")
        inactive_tex = {}
        for index in range(10):
            name = f"book/figures/inactive{index}.tex"
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"Synthetic preserved inactive figure fragment {index}.\n")
            inactive_tex[name] = lib.digest(path)
        synthetic_git(self.root, "add", ".")
        synthetic_git(self.root, "commit", "-qm", "synthetic baseline")
        baseline = synthetic_git(self.root, "rev-parse", "HEAD")
        path = self.root / lib.DRIVER
        path.parent.mkdir(parents=True)
        path.write_text(DRIVER)
        tex = {}
        if graph_mode != "no_entry_point":
            main = self.root / "book/main.tex"
            content = {"absolute": "\\input{/tmp/outside}", "outside": "\\input{../outside}",
                       "repeated": "\\input{input0.tex}\\input{input0.tex}",
                       "unsupported": "\\input input0.tex"}.get(graph_mode, "\\input{input0.tex}")
            main.write_text(content + "\n")
            tex["book/main.tex"] = lib.digest(main)
        for index in range(36 if graph_mode == "no_entry_point" else 35):
            name = f"book/input{index}.tex"
            path = self.root / name
            path.parent.mkdir(exist_ok=True)
            suffix = ""
            if graph_mode != "no_entry_point" and index < 34 and not (graph_mode == "disconnected" and index == 0):
                suffix = f"\\input{{input{index + 1}.tex}}\n"
            if graph_mode == "cycle" and index == 34:
                suffix = "\\input{main.tex}\n"
            path.write_text(f"Synthetic TeX input {index}.\n" + suffix)
            tex[name] = lib.digest(path)
        runtime = {lib.DRIVER: lib.digest(self.root / lib.DRIVER),
                   "dependency.txt": lib.digest(self.root / "dependency.txt")}
        approved = {**tex, lib.DRIVER: runtime[lib.DRIVER]}
        observed_tex = {**inactive_tex, **tex}
        guards = {**approved, **runtime, **observed_tex}
        synthetic_git(self.root, "add", ".")
        synthetic_git(self.root, "commit", "-qm", "synthetic source")
        source = synthetic_git(self.root, "rev-parse", "HEAD")
        groups = [f"Q{i}_synthetic" for i in range(1, 5)] + [f"G{i}_synthetic" for i in range(1, 11)]
        counts = {"exact": 14, "numerical_formula_comparisons": 0, "cross_precision_observations": 0}
        observations = {"book/input0.tex": tex["book/input0.tex"]}
        def rows(names):
            return [{"path": name, **lib.identity(self.root / name)} for name in sorted(names)]
        sources, dependencies = rows([lib.DRIVER]), rows(["dependency.txt"])
        state = {"git_commit": baseline, "git_dirty": True, "git_status_porcelain": ["?? synthetic-development"],
                 "sources": sources, "guarded_dependencies": dependencies,
                 "source_set_sha256": sha256(lib.encode({"sources": sources, "dependencies": dependencies})).hexdigest(),
                 "live_manuscript_observation": [{"path": p, "accepted_contract_source_sha256": h,
                                                   "current_sha256": h, "matches_accepted_snapshot": True}
                                                  for p, h in observations.items()],
                 "live_tex_source_observations": [{"path": p, "sha256": h} for p, h in sorted(observed_tex.items())],
                 "scope": "Synthetic source metadata; no science or manuscript review."}
        reference = {"schema_version": 1, "generated_at_utc": "2026-11-01T00:00:00+00:00", "checks_passed": True,
                     "status": "synthetic passing-gate fixture only", "source_before": state, "source_after": copy.deepcopy(state),
                     "runtime": {"elapsed_seconds": 1.0, "python_version": "synthetic-version", "mpmath_version": "synthetic"},
                     "fixture": {"precisions": [70, 110], "accepted_manuscript_sha256": observations},
                     "groups": {name: {"exact": [{"synthetic_identity": "1=1"}]} for name in groups},
                     "check_counts": counts, "scope": "Synthetic fixture. No scientific result is claimed."}
        candidate = copy.deepcopy(reference)
        candidate["generated_at_utc"] = "2026-11-02T00:00:00+00:00"
        candidate["runtime"]["elapsed_seconds"] = 2.0
        for key in ("source_before", "source_after"):
            candidate[key].update({"git_commit": source, "git_dirty": False, "git_status_porcelain": []})
        dump(self.outer / "reference.json", reference)
        dump(self.outer / "candidate-template.json", candidate)
        integration = {"decision": "synthetic_approve", "hashes": approved, "unused_note": "original"}
        computation = {"decision": "synthetic_approve", "hashes": runtime,
                       "reference_identity": lib.identity(self.outer / "reference.json"),
                       "manuscript": observations, "observed_tex": observed_tex, "groups": groups}
        dump(self.outer / "integration.json", integration)
        dump(self.outer / "computation.json", computation)
        def pin(name):
            return {"path": name, "identity": lib.identity(self.outer / name),
                    "required_values": {"/decision": "synthetic_approve"}}
        spec = {"schema_version": 1, "ready": True, "unresolved": [], "root": str(self.root), "outer": str(self.outer),
                "python": sys.executable, "baseline_commit": baseline, "source_commit": source,
                "source_approval": {**pin("integration.json"), "source_sha256_pointer": "/hashes"},
                "computation_approval": {**pin("computation.json"), "runtime_sha256_pointer": "/hashes",
                                         "reference_identity_pointer": "/reference_identity",
                                         "reference_manuscript_sha256_pointer": "/manuscript", "expected_groups_pointer": "/groups",
                                         "reference_tex_observation_sha256_pointer": "/observed_tex"},
                "approved_source_sha256": approved, "tex_input_sha256": tex, "runtime_sha256": runtime,
                "reference_manuscript_sha256": observations, "manuscript_observation_sha256": observations,
                "reference_tex_observation_sha256": observed_tex, "tex_observation_sha256": observed_tex,
                "allowed_tex_observation_changes": [],
                "allowed_manuscript_changes": [], "replay_guard_sha256": guards,
                "expected_groups": groups, "expected_check_counts": counts,
                "reference": {"path": "reference.json", "identity": lib.identity(self.outer / "reference.json")},
                "output": "result.json", "unused_note": "original"}
        dump(self.outer / "spec.json", spec)
        return baseline, spec, reference, candidate

    def test_strict_json_rejects_duplicate_nonfinite_and_partial_input(self):
        for payload in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}', '{"a":1e999}', '{"a":'):
            with self.subTest(payload=payload), self.assertRaises((lib.CheckpointError, ValueError)):
                lib.parse_json(payload)

    def test_CR01_exact_decimal_round_trip_policy_and_scalar_types(self):
        for token in ("1e-999", "1.0000000000000001", "9007199254740993.0"):
            with self.subTest(token=token), self.assertRaisesRegex(lib.CheckpointError, "round-trip without loss"):
                lib.parse_json(token)
        for token in ("0.1", "1e-200", "1.25", "9007199254740992.0", "0.0"):
            with self.subTest(token=token):
                parsed = lib.parse_json(token)
                self.assertIs(type(parsed), float)
                self.assertEqual(lib.encode(lib.parse_json(lib.encode(parsed))), lib.encode(parsed))
        for left, right in (("true", "1"), ('"1.0"', "1.0"), ("1", "1.0"),
                            ("9007199254740993", "9007199254740992"), ('"1e-999"', '"0.0"')):
            with self.subTest(left=left, right=right):
                self.assertNotEqual(lib.encode(lib.parse_json(left)), lib.encode(lib.parse_json(right)))

    def raw_comparison_case(self, left, right, success=False):
        """Exercise strict parsing through full CLI comparison and its receipt."""
        baseline, spec, reference, candidate = self.fixture()
        if success:
            reference["runtime"]["elapsed_seconds"] = 1e-200
            candidate["runtime"]["elapsed_seconds"] = 0.25
        for name, value, token in (("reference.json", reference, left), ("result.json", candidate, right)):
            value["unknown_scientific_number"] = "RAW_NUMBER_PLACEHOLDER"
            raw = json.dumps(value).replace('"RAW_NUMBER_PLACEHOLDER"', token)
            (self.outer / name).write_text(raw + "\n")
        # These are synthetic approved identities; no real review is fabricated.
        spec["reference"]["identity"] = lib.identity(self.outer / "reference.json")
        code = json.loads((self.outer / "computation.json").read_text())
        code["reference_identity"] = spec["reference"]["identity"]
        dump(self.outer / "computation.json", code)
        spec["computation_approval"]["identity"] = lib.identity(self.outer / "computation.json")
        dump(self.outer / "spec.json", spec)
        receipt = self.outer / "raw-comparison.json"
        argv = [compare.__file__, "--spec", str(self.outer / "spec.json"), "--receipt", str(receipt)]
        with patch.object(lib, "BASELINE", baseline), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            if success:
                compare.main()
            else:
                with self.assertRaisesRegex(lib.CheckpointError, "round-trip without loss"):
                    compare.main()
        # Receipt remains ordinary strict JSON, including tiny valid timings.
        row = lib.parse_json(receipt.read_bytes())
        self.assertEqual(row["checks_passed"], success)
        self.assertEqual(row["exit_status"], 0 if success else 1)
        self.assertEqual(lib.encode(lib.parse_json(lib.encode(row))), lib.encode(row))
        if success:
            excluded = {r["pointer"]: r for r in row["excluded_values"]}
            self.assertEqual(excluded["/runtime/elapsed_seconds"]["before"], 1e-200)
            self.assertEqual(excluded["/runtime/elapsed_seconds"]["after"], 0.25)
        else:
            self.assertIn("round-trip without loss", row["failure"])
            self.assertTrue(row["failure_stage"])

    def test_CR01_underflow_reference_fails_with_serialized_receipt(self):
        self.raw_comparison_case("1e-999", "0.0")

    def test_CR01_underflow_candidate_fails_with_serialized_receipt(self):
        self.raw_comparison_case("0.0", "1e-999")

    def test_CR01_close_decimal_reference_fails_with_serialized_receipt(self):
        self.raw_comparison_case("1.0000000000000001", "1.0")

    def test_CR01_close_decimal_candidate_fails_with_serialized_receipt(self):
        self.raw_comparison_case("1.0", "1.0000000000000001")

    def test_CR01_integer_boundary_reference_fails_with_serialized_receipt(self):
        self.raw_comparison_case("9007199254740993.0", "9007199254740992.0")

    def test_CR01_integer_boundary_candidate_fails_with_serialized_receipt(self):
        self.raw_comparison_case("9007199254740992.0", "9007199254740993.0")

    def test_CR01_lossless_decimal_and_timing_receipt_success_control(self):
        self.raw_comparison_case("0.1", "0.10", success=True)

    def test_exact_pointer_exclusions_reject_duplicates_overlap_and_missing(self):
        for pointers in (["/a", "/a"], ["/a", "/a/b"], ["/missing"]):
            with self.subTest(pointers=pointers), self.assertRaises(lib.CheckpointError):
                lib.masked({"a": {"b": 1}}, pointers)

    def test_approval_shapes_reject_duplicate_paths(self):
        with self.assertRaises(lib.CheckpointError):
            lib.mapped_hashes({"a": [{"path": "x", "sha256": "0" * 64}] * 2}, "/a", "path-record-list")

    def test_outer_path_and_existing_receipt_are_protected(self):
        path = self.outer / "receipt.json"
        path.write_text("Preserved earlier evidence.\n")
        frozen = lib.identity(path)
        for target in (path, self.root / "forbidden.json", self.outer / ".." / "escaped.json"):
            with self.subTest(target=target), self.assertRaises(lib.CheckpointError):
                with lib.receipt_record(self.outer, target, {}):
                    self.fail("unsafe/existing receipt entered")
        self.assertEqual(lib.identity(path), frozen)
        self.assertFalse((self.root / "forbidden.json").exists())

    def test_failure_receipt_survives_guard_exception(self):
        path = self.outer / "failed.json"
        with self.assertRaises(lib.CheckpointError):
            with lib.receipt_record(self.outer, path, {"stage": "synthetic_guard"}):
                lib.require(False, "synthetic expected rejection")
        row = lib.parse_json(path.read_bytes())
        self.assertFalse(row["checks_passed"])
        self.assertEqual(row["exit_status"], 1)
        self.assertEqual(row["failure_stage"], "synthetic_guard")

    def test_unready_template_fails_before_command_and_retains_receipt(self):
        spec = lib.parse_json((HERE / "replay-spec.unready.json").read_bytes())
        spec.update({"root": str(self.root), "outer": str(self.outer)})
        dump(self.outer / "spec.json", spec)
        receipt = self.outer / "receipt.json"
        with patch.object(sys, "argv", ["run_clean_replay.py", "--spec", str(self.outer / "spec.json"), "--receipt", str(receipt)]), \
                self.assertRaisesRegex(lib.CheckpointError, "unfinished"):
            replay.main()
        row = lib.parse_json(receipt.read_bytes())
        self.assertFalse(row["command_executed"])
        self.assertFalse(row["checks_passed"])

    def test_only_individually_checked_changed_metadata_is_excluded(self):
        baseline, spec, reference, candidate = self.fixture()
        with patch.object(lib, "BASELINE", baseline):
            result = lib.finite_comparison(reference, candidate, spec)
        expected = {"/generated_at_utc", "/runtime/elapsed_seconds"}
        expected |= {f"/{phase}/{key}" for phase in ("source_before", "source_after")
                     for key in ("git_commit", "git_dirty", "git_status_porcelain")}
        self.assertEqual(set(result["excluded_exact_JSON_pointers"]), expected)
        self.assertTrue(all("sources" not in p and "groups" not in p for p in expected))

    def test_science_unknown_fields_versions_and_fixture_changes_are_rejected(self):
        baseline, spec, reference, candidate = self.fixture()
        changes = [lambda r: r["groups"]["Q1_synthetic"].update({"new_scientific_field": "changed"}),
                   lambda r: r["runtime"].update({"mpmath_version": "changed"}),
                   lambda r: r["fixture"].update({"guard_digits": 99}),
                   lambda r: r.update({"unrecognized_new_field": "changed"}),
                   lambda r: r["check_counts"].update({"exact": 15})]
        for change in changes:
            data = copy.deepcopy(candidate)
            change(data)
            with self.subTest(change=change), patch.object(lib, "BASELINE", baseline), self.assertRaises(lib.CheckpointError):
                lib.finite_comparison(reference, data, spec)

    def test_runtime_hash_changes_are_not_metadata_exclusions(self):
        baseline, spec, reference, candidate = self.fixture()
        for phase in ("source_before", "source_after"):
            candidate[phase]["sources"][0]["sha256"] = "0" * 64
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "runtime source hashes"):
            lib.finite_comparison(reference, candidate, spec)

    def test_precise_integration_manuscript_delta_is_allowed(self):
        baseline, spec, reference, candidate = self.fixture()
        name, old = "book/input0.tex", "a" * 64
        spec["reference_manuscript_sha256"] = {name: old}
        spec["allowed_manuscript_changes"] = [name]
        spec["reference_tex_observation_sha256"] = {**spec["reference_tex_observation_sha256"], name: old}
        spec["allowed_tex_observation_changes"] = [name]
        for report in (reference, candidate):
            report["fixture"]["accepted_manuscript_sha256"] = {name: old}
            for phase in ("source_before", "source_after"):
                row = report[phase]["live_manuscript_observation"][0]
                row["accepted_contract_source_sha256"] = old
                row["current_sha256"] = old if report is reference else spec["manuscript_observation_sha256"][name]
                row["matches_accepted_snapshot"] = report is reference
                if report is reference:
                    next(r for r in report[phase]["live_tex_source_observations"] if r["path"] == name)["sha256"] = old
        with patch.object(lib, "BASELINE", baseline):
            lib.ready_spec(spec)
            result = lib.finite_comparison(reference, candidate, spec)
        self.assertEqual(len(result["excluded_exact_JSON_pointers"]), 14)

    def test_unapproved_or_wrong_snapshot_manuscript_change_rejected(self):
        baseline, spec, reference, candidate = self.fixture()
        for phase in ("source_before", "source_after"):
            candidate[phase]["live_manuscript_observation"][0]["current_sha256"] = "a" * 64
            candidate[phase]["live_manuscript_observation"][0]["matches_accepted_snapshot"] = False
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "stage snapshot"):
            lib.finite_comparison(reference, candidate, spec)
        spec["allowed_manuscript_changes"] = ["book/input0.tex"]
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "actual stage-specific"):
            lib.ready_spec(spec)

    def test_partial_groups_and_unpinned_group_renaming_are_rejected(self):
        baseline, spec, reference, candidate = self.fixture()
        for report in (reference, candidate):
            report["groups"] = {p: row for p, row in report["groups"].items() if p.startswith("Q")}
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "coverage"):
            lib.finite_comparison(reference, candidate, spec)
        spec["expected_groups"][0] = "Q1_changed"
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "exact group names"):
            lib.approved_spec(spec)

    def test_source_before_after_drift_is_rejected(self):
        baseline, spec, reference, candidate = self.fixture()
        reference["source_after"]["git_status_porcelain"].append(" M changed-during-author-run")
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "metadata changed"):
            lib.finite_comparison(reference, candidate, spec)

    def test_CR01_source_state_scalar_type_changes_fail_before_metadata_exclusions(self):
        baseline, spec, reference, candidate = self.fixture()
        changes = [lambda r: r["source_after"].update({"git_dirty": 0}),
                   lambda r: r["source_after"]["sources"][0].update(
                       {"bytes": float(r["source_after"]["sources"][0]["bytes"])})]
        for change in changes:
            data = copy.deepcopy(candidate)
            change(data)
            with self.subTest(change=change), patch.object(lib, "BASELINE", baseline), \
                    self.assertRaisesRegex(lib.CheckpointError, "source metadata changed"):
                lib.finite_comparison(reference, data, spec)

    def replay_case(self, mode, fail):
        baseline, spec, _, _ = self.fixture()
        dump(self.outer / "control.json", {"mode": mode})
        if mode == "dirty_before":
            (self.root / "unexpected.txt").write_text("Synthetic prelaunch dirt.\n")
        if mode == "existing_output":
            (self.outer / "result.json").write_text("Preserved prior result.\n")
        if mode == "output_escape":
            spec["output"] = str(self.root / "forbidden-result.json")
            dump(self.outer / "spec.json", spec)
        original = lib.identity(self.outer / "spec.json")
        receipt = self.outer / "receipt.json"
        argv = ["run_clean_replay.py", "--spec", str(self.outer / "spec.json"), "--receipt", str(receipt)]
        with patch.object(lib, "BASELINE", baseline), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            if fail:
                with self.assertRaises(lib.CheckpointError):
                    replay.main()
            else:
                replay.main()
        row = lib.parse_json(receipt.read_bytes())
        self.assertEqual(row["checks_passed"], not fail)
        self.assertEqual(row["exit_status"], 1 if fail else 0)
        self.assertEqual(row["spec_identity"], original)
        return row

    def test_synthetic_actual_command_success(self):
        row = self.replay_case("success", False)
        self.assertTrue(row["command_executed"])
        self.assertEqual(row["source_before"], row["source_after"])

    def test_unused_spec_drift_keeps_initial_identity_and_fails(self):
        row = self.replay_case("spec_drift", True)
        self.assertEqual(row["returncode"], 0)
        self.assertNotEqual(row["spec_identity"], lib.identity(self.outer / "spec.json"))

    def test_unused_approval_drift_fails(self):
        row = self.replay_case("approval_drift", True)
        self.assertIn("identity changed", row["failure"])

    def test_runtime_changed_during_command_fails(self):
        row = self.replay_case("runtime_drift", True)
        self.assertTrue(row["command_executed"])
        self.assertIn("clean-source", row["failure"])

    def test_dirty_source_fails_before_launch(self):
        row = self.replay_case("dirty_before", True)
        self.assertFalse(row["command_executed"])
        self.assertFalse((self.outer / "result.json").exists())

    def test_existing_output_is_not_overwritten(self):
        row = self.replay_case("existing_output", True)
        self.assertFalse(row["command_executed"])
        self.assertEqual((self.outer / "result.json").read_text(), "Preserved prior result.\n")

    def test_output_escape_is_rejected(self):
        row = self.replay_case("output_escape", True)
        self.assertFalse(row["command_executed"])
        self.assertFalse((self.root / "forbidden-result.json").exists())

    def test_command_exit_status_is_retained(self):
        row = self.replay_case("command_failure", True)
        self.assertEqual(row["returncode"], 7)

    def test_wrong_result_provenance_fails(self):
        row = self.replay_case("wrong_result", True)
        self.assertEqual(row["returncode"], 0)
        self.assertEqual(row["failure_stage"], "result_guards")

    def test_comparison_detects_input_drift_after_comparing(self):
        baseline, _, _, candidate = self.fixture()
        path = self.outer / "result.json"
        dump(path, candidate)
        initial = lib.identity(path)
        real = compare.finite_comparison
        def mutate(first, second, spec):
            result = real(first, second, spec)
            second["groups"]["Q1_synthetic"]["changed"] = True
            dump(path, second)
            return result
        receipt = self.outer / "comparison.json"
        argv = ["compare_replays.py", "--spec", str(self.outer / "spec.json"), "--receipt", str(receipt)]
        with patch.object(lib, "BASELINE", baseline), patch.object(compare, "finite_comparison", mutate), \
                patch.object(sys, "argv", argv), self.assertRaisesRegex(lib.CheckpointError, "identity changed"):
            compare.main()
        row = lib.parse_json(receipt.read_bytes())
        self.assertFalse(row["checks_passed"])
        self.assertEqual(row["candidate"], initial)

    def test_tex_graph_rejects_cycles_and_repeated_inputs(self):
        graphs = [{"book/main.tex": b"\\input{main}"},
                  {"book/main.tex": b"\\input{x}\\input{x}", "book/x.tex": b"text"}]
        for graph in graphs:
            with self.subTest(graph=graph), self.assertRaises(lib.CheckpointError):
                verify.expand_tex(graph.__getitem__)

    def graph_rejection_case(self, mode):
        baseline, spec, _, _ = self.fixture(graph_mode=mode)
        if mode == "omitted_active_with_filler":
            declared = dict(spec["tex_input_sha256"])
            del declared["book/input34.tex"]
            declared["book/figures/inactive0.tex"] = spec["tex_observation_sha256"]["book/figures/inactive0.tex"]
            spec["tex_input_sha256"] = declared
            dump(self.outer / "spec.json", spec)
        if mode == "live_missing_entry":
            (self.root / "book/main.tex").unlink()
        if mode == "live_changed_graph":
            (self.root / "book/main.tex").write_text("\\input{input1.tex}\n")
        receipt = self.outer / "graph-rejection.json"
        argv = [replay.__file__, "--spec", str(self.outer / "spec.json"), "--receipt", str(receipt)]
        with patch.object(lib, "BASELINE", baseline), patch.object(sys, "argv", argv), self.assertRaises(lib.CheckpointError):
            replay.main()
        row = lib.parse_json(receipt.read_bytes())
        self.assertFalse(row["command_executed"])
        self.assertFalse(row["checks_passed"])
        self.assertEqual(row["failure_stage"], "approval_guards")
        self.assertIsNone(row["argv"])
        self.assertFalse((self.outer / "result.json").exists())
        return row

    def test_CR02_unconnected_36_files_without_entry_rejected_before_launch(self):
        self.graph_rejection_case("no_entry_point")

    def test_CR02_disconnected_files_with_entry_rejected_before_launch(self):
        self.graph_rejection_case("disconnected")

    def test_CR02_omitted_active_input_replaced_by_filler_rejected_before_launch(self):
        self.graph_rejection_case("omitted_active_with_filler")

    def test_CR02_committed_cycle_rejected_before_launch(self):
        self.graph_rejection_case("cycle")

    def test_CR02_committed_repeated_input_rejected_before_launch(self):
        self.graph_rejection_case("repeated")

    def test_CR02_committed_outside_input_rejected_before_launch(self):
        self.graph_rejection_case("outside")

    def test_CR02_committed_absolute_input_rejected_before_launch(self):
        self.graph_rejection_case("absolute")

    def test_CR02_unsupported_input_syntax_rejected_before_launch(self):
        self.graph_rejection_case("unsupported")

    def test_CR02_live_missing_entry_rejected_before_launch(self):
        self.graph_rejection_case("live_missing_entry")

    def test_CR02_live_changed_graph_rejected_before_launch(self):
        self.graph_rejection_case("live_changed_graph")

    def test_CR02_shared_graph_walker_ignores_commented_inputs(self):
        self.assertIs(verify.expand_tex, lib.expand_tex)
        files = {"book/main.tex": b"% \\input{absent}\n\\input{child}\n",
                 "book/child.tex": b"text\\%still text % \\input{also-absent}\n"}
        expanded, graph = lib.expand_tex(files.__getitem__)
        self.assertEqual(set(graph), set(files))
        self.assertIn(b"text\\%still text", expanded)
        self.assertNotIn(b"absent", expanded)

    def test_full_schema_preserves_all_46_tex_rows_and_inactive_hashes(self):
        baseline, spec, reference, candidate = self.fixture()
        for phase in ("source_before", "source_after"):
            row = next(r for r in candidate[phase]["live_tex_source_observations"] if "inactive0" in r["path"])
            row["sha256"] = "a" * 64
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "observation path/order/hash"):
            lib.finite_comparison(reference, candidate, spec)
        spec["allowed_tex_observation_changes"] = ["book/figures/inactive0.tex"]
        with patch.object(lib, "BASELINE", baseline), self.assertRaisesRegex(lib.CheckpointError, "approved active source"):
            lib.ready_spec(spec)

    def test_candidate_manifest_cannot_hash_itself(self):
        manifest = {"baseline_commit": lib.BASELINE, "source_commit": "s", "files": {verify.MANIFEST: {}}}
        copies = {"baseline_commit": lib.BASELINE, "source_commit": "s"}
        with self.assertRaisesRegex(lib.CheckpointError, "hash itself"):
            verify.candidate_state(self.root, self.outer, "s", {}, manifest, copies, True)

    def candidate_case(self, mode):
        """Real temporary Git/command gates; science/PDF/original-audit gates mocked."""
        baseline, spec, _, _ = self.fixture()
        dump(self.outer / "control.json", {"mode": "success"})
        source = spec["source_commit"]
        with patch.object(lib, "BASELINE", baseline), contextlib.redirect_stdout(io.StringIO()):
            for module, name in ((replay, "run.json"), (compare, "comparison.json")):
                with patch.object(sys, "argv", [module.__file__, "--spec", str(self.outer / "spec.json"),
                                               "--receipt", str(self.outer / name)]):
                    module.main()
        base = self.root / lib.REL
        base.mkdir(parents=True)
        payloads = {}
        def put(name, data):
            p = self.root / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            payloads[name] = data
        def put_json(name, data):
            put(name, (json.dumps(data, indent=2) + "\n").encode())
        def copied(name, original):
            put(lib.REL + "/" + name, (self.outer / original).read_bytes())
        def pin(name, required):
            return {"path": name, "identity": lib.identity(base / name), "required_values": required}
        for name in ("integration", "computation", "run", "comparison"):
            copied(name + ".json", name + ".json")
        copied("spec.json", "spec.json")
        put(lib.RESULT, (self.outer / "result.json").read_bytes())
        # Deliberately not a PDF document; only a byte-identity gate fixture.
        put(lib.PDF, b"Synthetic PDF identity fixture; not a PDF artifact.\n")
        (self.outer / "synthetic-pdf-bytes").write_bytes((self.root / lib.PDF).read_bytes())
        pdf_identity = lib.identity(self.root / lib.PDF)
        put_json(lib.REL + "/source.json", {"passed": True, "source_commit": source, "baseline_commit": baseline,
                                            "parent_commit": baseline, "git_status_porcelain": "", "index_clean": True})
        put_json(lib.REL + "/other-approval.json", {"decision": "synthetic_approve"})
        put_json(lib.REL + "/tex.json", {"files": spec["tex_input_sha256"], "count": 36})
        for name in ("pdf-build.json", "pdf-visual.json"):
            put_json(lib.REL + "/" + name, {"decision": "synthetic_approve", "pdf_sha256": pdf_identity["sha256"]})
        put(lib.REL + "/note.txt", b"Synthetic initial candidate note.\n")
        approvals = [{"role": role, **pin("other-approval.json", {"/decision": "synthetic_approve"})}
                     for role in ("structure", "quantum", "geodesic", "conventions")]
        approvals += [{"role": role, **pin(name + ".json", {"/decision": "synthetic_approve"})}
                      for role, name in (("integration", "integration"), ("computation", "computation"))]
        config = {"schema_version": 1, "ready": True, "unresolved": [], "baseline_commit": baseline,
                  "source_commit": source, "replay_spec": {"path": "spec.json", "outer_source": "spec.json",
                                                            "identity": lib.identity(base / "spec.json")},
                  "source_receipt": pin("source.json", {"/passed": True}), "approval_pins": approvals,
                  "replay_receipt": pin("run.json", {"/checks_passed": True}),
                  "comparison_receipt": pin("comparison.json", {"/checks_passed": True}),
                  "unused_note": "initial",
                  "pdf": {"identity": pdf_identity, "reviewed_outer_pdf": "synthetic-pdf-bytes",
                          "build_timing_claim": "actual independently reviewed precommit build copied byte-for-byte",
                          "input_freeze": {**pin("tex.json", {"/count": 36}), "input_sha256_pointer": "/files"},
                          "build_receipt": {**pin("pdf-build.json", {"/decision": "synthetic_approve"}), "pdf_sha256_pointer": "/pdf_sha256"},
                          "visual_receipt": {**pin("pdf-visual.json", {"/decision": "synthetic_approve"}), "pdf_sha256_pointer": "/pdf_sha256"}}}
        put_json(verify.CONTRACT, config)
        def remake_manifests():
            rows = []
            for index, name in enumerate(sorted(payloads)):
                target = self.outer / "copies" / str(index)
                target.parent.mkdir(exist_ok=True)
                target.write_bytes((self.root / name).read_bytes())
                rows.append({"path": name, "outer_source": str(target.relative_to(self.outer)), **lib.identity(target)})
            dump(self.root / verify.COPIES, {"baseline_commit": baseline, "source_commit": source,
                                           "omissions": ["Synthetic gate fixture only."], "files": rows})
            dump(self.root / verify.MANIFEST, {"baseline_commit": baseline, "source_commit": source,
                                             "files": {p: lib.identity(self.root / p) for p in [*payloads, verify.COPIES]}})
        remake_manifests()
        initial = {str(self.root / p): lib.identity(self.root / p)
                   for p in (verify.CONTRACT, verify.MANIFEST, verify.COPIES)}
        def manuscript_hook(*_args):
            if mode == "payload_and_manifests":
                (base / "note.txt").write_text("Replaced payload and all corresponding identities.\n")
                remake_manifests()
            elif mode == "contract_and_manifests":
                config["unused_note"] = "changed during verification"
                put_json(verify.CONTRACT, config)
                remake_manifests()
            elif mode == "new_path_and_manifests":
                put(lib.REL + "/later.txt", b"Path added after initial candidate freeze.\n")
                remake_manifests()
            return {"synthetic_gate_only": True}
        actual_run = subprocess.run
        def fake_fsck(argv, *args, **kwargs):
            if argv == ["git", "fsck", "--full"]:
                return subprocess.CompletedProcess(argv, 0, "", "")
            return actual_run(argv, *args, **kwargs)
        receipt = self.outer / "verification.json"
        argv = [verify.__file__, "--root", str(self.root), "--outer", str(self.outer), "--candidate", "--receipt", str(receipt)]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(lib, "BASELINE", baseline))
            stack.enter_context(patch.object(verify, "BASELINE", baseline))
            stack.enter_context(patch.object(verify, "preservation", lambda *_: {"synthetic_gate_only": True}))
            stack.enter_context(patch.object(verify, "manuscript", manuscript_hook))
            stack.enter_context(patch.object(verify.subprocess, "run", fake_fsck))
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if mode == "success":
                verify.main()
            else:
                with self.assertRaises(lib.CheckpointError):
                    verify.main()
        row = lib.parse_json(receipt.read_bytes())
        self.assertEqual(row["checks_passed"], mode == "success")
        self.assertEqual(row["frozen_control_identities"], initial)
        return row

    def test_synthetic_candidate_success_control(self):
        self.candidate_case("success")

    def test_consistently_replaced_payload_and_manifests_rejected(self):
        self.candidate_case("payload_and_manifests")

    def test_consistently_replaced_contract_and_manifests_rejected(self):
        self.candidate_case("contract_and_manifests")

    def test_consistently_added_candidate_path_rejected(self):
        self.candidate_case("new_path_and_manifests")


if __name__ == "__main__":
    unittest.main()
