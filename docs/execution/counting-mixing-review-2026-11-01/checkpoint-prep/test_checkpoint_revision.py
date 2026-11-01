"""R1-R4 regressions using synthetic commands and disposable Git fixtures.

Adapted from checkpoint-review/independent_probes_v1.py's demonstrated cases.
No synthetic driver output is mathematical evidence or a scientific replay.
The verifier probes retain real main/Git/manifest/copy gates and substitute
only unrelated mathematical, preservation, PDF and approval work.
"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import checkpoint_lib as lib
import compare_replays as compare
import run_clean_replay as replay
import verify_checkpoint as verifier

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent
FIXTURE_ENV = {
    **os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_AUTHOR_NAME": "Checkpoint regression fixture", "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "Checkpoint regression fixture", "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
}
DRIVER = '''from pathlib import Path
from hashlib import sha256
import json, subprocess, sys
root=Path.cwd()
output=Path(sys.argv[sys.argv.index("--output")+1])
outer=output.parent
mode=json.loads((outer/"control.json").read_text())["mode"]
if mode == "command_failure":
    sys.exit(7)
head=subprocess.check_output(["git","rev-parse","HEAD"],text=True).strip()
status=subprocess.check_output(["git","status","--porcelain=v1","--untracked-files=all"],text=True).splitlines()
name="experiments/counting_mixing/run.py"
source={"git_commit":head,"git_dirty":bool(status),"git_status_porcelain":status,
        "sources":[{"path":name,"sha256":sha256((root/name).read_bytes()).hexdigest()}]}
if mode in ("spec_drift", "approval_drift"):
    path=outer/("replay-spec.json" if mode=="spec_drift" else "approval.json")
    data=json.loads(path.read_text());data["unused_note"]="changed after launch"
    path.write_text(json.dumps(data,indent=2)+"\\n")
output.write_text(json.dumps({"checks_passed":True,"source":source,"source_at_completion":source})+"\\n")
'''


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def fixture_git(root, *args):
    return subprocess.check_output(["git", *args], cwd=root, env=FIXTURE_ENV, text=True).strip()


class RevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="revision-gate-test-", dir=HERE)
        self.base = Path(self.temp.name)
        self.root, self.outer = self.base / "repo", self.base / "evidence"
        self.root.mkdir()
        self.outer.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def source_fixture(self):
        root, outer = self.root, self.outer
        fixture_git(root, "init", "-q")
        (root / "README.md").write_text("Synthetic fixture only.\n")
        fixture_git(root, "add", "README.md")
        fixture_git(root, "commit", "-qm", "fixture baseline")
        baseline = fixture_git(root, "rev-parse", "HEAD")
        driver = root / "experiments/counting_mixing/run.py"
        driver.parent.mkdir(parents=True)
        driver.write_text(DRIVER)
        inputs = {}
        for i in range(26):
            name = f"book/input{i}.tex"
            path = root / name
            path.parent.mkdir(exist_ok=True)
            path.write_text(f"synthetic manuscript input {i}\n")
            inputs[name] = lib.digest(path)
        runtime = {str(driver.relative_to(root)): lib.digest(driver)}
        approved = inputs | runtime
        fixture_git(root, "add", ".")
        fixture_git(root, "commit", "-qm", "fixture source")
        source = fixture_git(root, "rev-parse", "HEAD")
        approval_path = outer / "approval.json"
        dump(approval_path, {"decision": "approve", "approved_source_sha256": approved, "unused_note": "original"})
        spec = {"schema_version": 1, "ready": True, "unresolved": [], "root": str(root), "outer": str(outer),
                "python": sys.executable, "baseline_commit": baseline, "source_commit": source,
                "source_approval": {"path": "approval.json", "identity": lib.identity(approval_path),
                                    "source_sha256_pointer": "/approved_source_sha256", "required_values": {"/decision": "approve"}},
                "approved_source_sha256": approved, "pdf_input_sha256": inputs, "replay_guard_sha256": approved,
                "replays": {"counting": {"output": "result.json", "runtime_sha256": runtime}, "torus": {"runtime_sha256": {}}},
                "unused_note": "original"}
        dump(outer / "replay-spec.json", spec)
        return baseline, source, approved, spec

    def replay_case(self, mode, should_fail, *, unresolved="empty"):
        baseline, _, _, spec = self.source_fixture()
        if unresolved == "nonempty":
            spec["unresolved"] = ["Independent review pending"]
        elif unresolved == "missing":
            del spec["unresolved"]
        dump(self.outer / "replay-spec.json", spec)
        dump(self.outer / "control.json", {"mode": mode})
        if mode == "dirty_before":
            (self.root / "unexpected.json").write_text("{}\n")
        spec_path, approval_path = self.outer / "replay-spec.json", self.outer / "approval.json"
        initial_spec, initial_approval = lib.identity(spec_path), lib.identity(approval_path)
        receipt = self.outer / "receipt.json"
        argv = ["run_clean_replay.py", "--spec", str(spec_path), "--kind", "counting", "--receipt", str(receipt)]
        with patch.object(replay, "BASELINE", baseline), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            if should_fail:
                with self.assertRaises(lib.CheckpointError):
                    replay.main()
            else:
                replay.main()
        report = lib.load_json(receipt)
        self.assertEqual(report["checks_passed"], not should_fail)
        self.assertEqual(report["exit_status"], 1 if should_fail else 0)
        self.assertEqual(report["spec_identity"], initial_spec)
        if report["source_approval_identity"] is not None:
            self.assertEqual(report["source_approval_identity"], initial_approval)
        if should_fail:
            self.assertTrue(report["failure"])
            self.assertTrue(report["failure_stage"])
        return report, initial_spec, initial_approval

    def test_R1_real_wrapper_success_control(self):
        report, _, _ = self.replay_case("success", False)
        self.assertTrue(report["command_executed"])
        self.assertEqual(report["source_before"], report["source_after"])

    def test_R1_changed_unused_spec_rejected_with_original_identity(self):
        report, original, _ = self.replay_case("spec_drift", True)
        self.assertNotEqual(lib.identity(self.outer / "replay-spec.json"), original)
        self.assertEqual(report["returncode"], 0)
        self.assertIn("replay specification identity changed", report["failure"])

    def test_R1_changed_unused_approval_rejected_with_original_identity(self):
        report, _, original = self.replay_case("approval_drift", True)
        self.assertNotEqual(lib.identity(self.outer / "approval.json"), original)
        self.assertEqual(report["returncode"], 0)
        self.assertIn("source approval identity changed", report["failure"])

    def test_R4_dirty_prelaunch_guard_leaves_failure_receipt(self):
        report, _, _ = self.replay_case("dirty_before", True)
        self.assertFalse(report["command_executed"])
        self.assertIsNone(report["returncode"])
        self.assertEqual(report["failure_stage"], "prelaunch_source_guards")
        self.assertFalse((self.outer / "result.json").exists())

    def test_R4_command_failure_retains_actual_exit_code(self):
        report, _, _ = self.replay_case("command_failure", True)
        self.assertEqual(report["returncode"], 7)
        self.assertEqual(report["exit_status"], 1)

    def test_R3_nonempty_unresolved_spec_leaves_failure_before_launch(self):
        report, _, _ = self.replay_case("success", True, unresolved="nonempty")
        self.assertFalse(report["command_executed"])
        self.assertFalse((self.outer / "result.json").exists())

    def test_R3_missing_unresolved_spec_leaves_failure_before_launch(self):
        report, _, _ = self.replay_case("success", True, unresolved="missing")
        self.assertFalse(report["command_executed"])

    def test_R3_ready_contract_requires_explicit_empty_unresolved(self):
        for fields in ({}, {"unresolved": ["pending"]}, {"unresolved": None}):
            with self.subTest(fields=fields), self.assertRaisesRegex(lib.CheckpointError, "explicit empty unresolved"):
                verifier.approved_contract(self.root, {"schema_version": 1, "ready": True, **fields})

    def comparison_case(self, mode):
        before = lib.load_json(OUTER / "computation/revision-v2/author-result-60-90-v2.json")
        after = copy.deepcopy(before)
        if mode == "mismatch":
            after["check_counts"]["exact"] += 1
        a, b, receipt = (self.outer / name for name in ("reference.json", "candidate.json", "comparison.json"))
        dump(a, before)
        dump(b, after)
        initial = {"reference": lib.identity(a), "candidate": lib.identity(b)}
        real_compare = compare.counting_comparison

        def mutate_after_comparison(first, second):
            result = real_compare(first, second)
            target = a if mode == "reference_drift" else b
            changed = lib.load_json(target)
            changed["check_counts"]["exact"] += 1
            dump(target, changed)
            return result

        argv = ["compare_replays.py", "--kind", "counting", "--outer", str(self.outer), "--reference", str(a),
                "--candidate", str(b), "--receipt", str(receipt)]
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if mode in ("reference_drift", "candidate_drift"):
                stack.enter_context(patch.object(compare, "counting_comparison", mutate_after_comparison))
            if mode == "success":
                compare.main()
            else:
                with self.assertRaises(lib.CheckpointError):
                    compare.main()
        report = lib.load_json(receipt)
        self.assertEqual(report["checks_passed"], mode == "success")
        self.assertEqual(report["exit_status"], 0 if mode == "success" else 1)
        for name in initial:
            self.assertEqual({k: report[name][k] for k in ("sha256", "bytes")}, initial[name])
        return report

    def test_R1_comparison_success_control(self):
        self.comparison_case("success")

    def test_R1_candidate_changed_after_comparison_leaves_failure(self):
        report = self.comparison_case("candidate_drift")
        self.assertIn("comparison candidate identity changed", report["failure"])

    def test_R1_reference_changed_after_comparison_leaves_failure(self):
        report = self.comparison_case("reference_drift")
        self.assertIn("comparison reference identity changed", report["failure"])

    def test_R4_scientific_mismatch_leaves_false_receipt(self):
        report = self.comparison_case("mismatch")
        self.assertEqual(report["failure_stage"], "scientific_comparison")

    def test_R4_existing_receipt_is_never_overwritten(self):
        receipt = self.outer / "existing.json"
        receipt.write_text("preserved receipt bytes\n")
        before = lib.identity(receipt)
        with self.assertRaises(lib.CheckpointError), lib.receipt_record(self.outer, receipt, {}):
            self.fail("existing receipt should not enter audited work")
        self.assertEqual(lib.identity(receipt), before)

    def test_R4_receipt_escape_writes_nothing(self):
        path = self.root / "forbidden.json"
        with self.assertRaises(lib.CheckpointError), lib.receipt_record(self.outer, path, {}):
            self.fail("unsafe receipt should not enter audited work")
        self.assertFalse(path.exists())

    def external_comparison_case(self, changed_kind):
        reference = lib.load_json(OUTER / "torus-campaign/full8192-author-v2/result.json")
        candidate = copy.deepcopy(reference)
        target = None
        for label, report in (("reference", reference), ("candidate", candidate)):
            directory = self.outer / label
            directory.mkdir()
            for surface in report["surfaces"]:
                rows = []
                for suffix in ("lengths.f64le", "slopes.i32le"):
                    path = directory / (surface["surface"] + "." + suffix)
                    path.write_bytes(b"12345678")
                    rows.append({"path": str(path), **lib.identity(path)})
                    if label == "candidate" and changed_kind == "raw":
                        target = path
                surface["raw_streams"] = rows
                path = directory / (surface["surface"] + ".native.json")
                dump(path, {"surface": surface["surface"], "raw_peak_rss": 1,
                            "timing_seconds": {key: 0.0 for key in lib.TIMING_KEYS}, "count": 1})
                surface["raw_native_report"] = {"path": str(path), "sha256": lib.digest(path)}
                if label == "candidate" and changed_kind == "native":
                    target = path
        a, b = self.outer / "reference.json", self.outer / "candidate.json"
        dump(a, reference)
        dump(b, candidate)
        initial = lib.identity(target)
        actual_raw_comparison = compare.torus_raw_comparison

        def mutate_after_raw_comparison(*args):
            result = actual_raw_comparison(*args)
            if changed_kind == "raw":
                target.write_bytes(b"12345679")
            else:
                record = lib.load_json(target)
                record["count"] = 2
                dump(target, record)
            return result

        receipt = self.outer / "external-drift-receipt.json"
        argv = ["compare_replays.py", "--kind", "torus", "--outer", str(self.outer),
                "--reference", str(a), "--candidate", str(b), "--receipt", str(receipt)]
        with patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()), \
                patch.object(compare, "torus_raw_comparison", mutate_after_raw_comparison), self.assertRaises(lib.CheckpointError):
            compare.main()
        report = lib.load_json(receipt)
        self.assertFalse(report["checks_passed"])
        self.assertEqual(report["exit_status"], 1)
        self.assertEqual(report["external_input_identities"][str(target)], initial)
        self.assertNotEqual(lib.identity(target), initial)
        self.assertIn("external native/raw comparison input", report["failure"])

    def test_R1_raw_stream_changed_after_comparison_is_rejected(self):
        self.external_comparison_case("raw")

    def test_R1_native_report_changed_after_comparison_is_rejected(self):
        self.external_comparison_case("native")

    def verifier_case(self, mode):
        baseline, source, approved, _ = self.source_fixture()
        config = {"pdf": {"input_sha256": {}}, "replays": {"counting": {"runtime_sha256": {}},
                  "torus": {"runtime_sha256": {}}}, "replay_guard_sha256": approved, "unused_note": "original"}
        payloads = {verifier.CONTRACT: json.dumps(config).encode(), lib.PDF: b"synthetic PDF fixture only\n",
                    **{path: b"{}\n" for path in lib.RESULTS.values()}, lib.REL + "/note.txt": b"version one\n"}
        for name, value in payloads.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)

        def remake_manifests():
            copies = []
            for i, name in enumerate(payloads):
                destination = self.outer / "copies" / str(i)
                destination.parent.mkdir(exist_ok=True)
                destination.write_bytes((self.root / name).read_bytes())
                copies.append({"path": name, "outer_source": str(destination.relative_to(self.outer)), **lib.identity(destination)})
            dump(self.root / verifier.COPY_MANIFEST, {"baseline_commit": baseline, "source_commit": source,
                                                     "omissions": ["Synthetic fixture only"], "files": copies})
            files = {name: lib.identity(self.root / name) for name in [*payloads, verifier.COPY_MANIFEST]}
            dump(self.root / verifier.MANIFEST, {"baseline_commit": baseline, "source_commit": source, "files": files})

        remake_manifests()
        original = {p: lib.identity(self.root / p) for p in (verifier.CONTRACT, verifier.MANIFEST, verifier.COPY_MANIFEST)}

        def scientific_hook(*_args):
            if mode == "payload_and_manifests":
                (self.root / lib.REL / "note.txt").write_text("replaced payload and consistent new manifests\n")
                remake_manifests()
            elif mode == "contract_and_manifests":
                changed = lib.load_json(self.root / verifier.CONTRACT)
                changed["unused_note"] = "replaced during verification"
                dump(self.root / verifier.CONTRACT, changed)
                remake_manifests()
            elif mode == "copy_and_manifest":
                changed = lib.load_json(self.root / verifier.COPY_MANIFEST)
                changed["omissions"].append("new content during verification")
                dump(self.root / verifier.COPY_MANIFEST, changed)
                candidate = lib.load_json(self.root / verifier.MANIFEST)
                candidate["files"][verifier.COPY_MANIFEST] = lib.identity(self.root / verifier.COPY_MANIFEST)
                dump(self.root / verifier.MANIFEST, candidate)
            elif mode == "new_path_and_manifests":
                name = lib.REL + "/added-during-verification.txt"
                payloads[name] = b"new path\n"
                (self.root / name).write_bytes(payloads[name])
                remake_manifests()
            external = {}
            if mode == "external_drift":
                path = self.outer / "external.raw"
                path.write_bytes(b"12345678")
                external[str(path)] = lib.identity(path)
            return {"synthetic_gate_only": True, "torus": {"external_input_identities": external}}

        def PDF_hook(*_args):
            if mode == "external_drift":
                (self.outer / "external.raw").write_bytes(b"12345679")
            return {"synthetic_gate_only": True}

        receipt = self.outer / "verification.json"
        argv = ["verify_checkpoint.py", "--root", str(self.root), "--outer", str(self.outer), "--candidate", "--receipt", str(receipt)]
        with contextlib.ExitStack() as stack:
            for name, value in {
                "BASELINE": baseline, "approved_contract": lambda *_: (source, approved),
                "source_checkpoint_receipts": lambda *_: None, "preservation": lambda *_: {"synthetic_gate_only": True},
                "scientific_results": scientific_hook, "manuscript_pdf_links": PDF_hook,
                "fsck": lambda *_: {"synthetic_gate_only": True},
            }.items():
                stack.enter_context(patch.object(verifier, name, value))
            stack.enter_context(patch.object(sys, "argv", argv))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            if mode == "success":
                verifier.main()
            else:
                with self.assertRaises(lib.CheckpointError):
                    verifier.main()
        report = lib.load_json(receipt)
        self.assertEqual(report["checks_passed"], mode == "success")
        self.assertEqual(report["exit_status"], 0 if mode == "success" else 1)
        self.assertEqual(report["frozen_control_identities"], original)
        self.assertEqual(report["candidate_manifest_sha256"], original[verifier.MANIFEST]["sha256"])
        return report

    def test_R2_verifier_unchanged_candidate_control(self):
        self.verifier_case("success")

    def test_R2_consistent_replaced_payload_and_manifests_rejected(self):
        self.verifier_case("payload_and_manifests")

    def test_R2_consistent_replaced_contract_and_manifests_rejected(self):
        self.verifier_case("contract_and_manifests")

    def test_R2_consistent_replaced_copy_and_candidate_manifests_rejected(self):
        self.verifier_case("copy_and_manifest")

    def test_R2_replaced_path_set_rejected(self):
        report = self.verifier_case("new_path_and_manifests")
        self.assertNotIn(lib.REL + "/added-during-verification.txt", report["frozen_artifact_paths"])

    def test_R1_verifier_rechecks_external_native_raw_inputs_before_success(self):
        report = self.verifier_case("external_drift")
        self.assertIn("external native/raw comparison input", report["failure"])


if __name__ == "__main__":
    unittest.main()
