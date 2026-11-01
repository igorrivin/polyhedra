"""Read-only adapter and replay-evidence audit; never executes either experiment.

RootView routes the prospective canonical evidence prefix to retained outer
receipts. All source-file and Git access still uses the actual canonical root.
This permits frozen-adapter review before the moving candidate is complete.
"""
import ast
import copy
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent.parent
CANONICAL = OUTER.parent.parent / "consolidated"
SOURCE = "5e34f23d981631605783cbe0f74247659f12a10a"
sys.path.insert(0, str(HERE / "subject"))
lib = importlib.import_module("checkpoint_lib")
adapter = importlib.import_module("candidate_receipt_adapter")
approval_adapter = importlib.import_module("source_approval_adapter")


class RootView(type(Path())):
    def __truediv__(self, key):
        if str(key) == lib.REL:
            return OUTER
        return super().__truediv__(key)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def rejection(operation, expected):
    try:
        operation()
    except Exception as exc:
        require(expected in str(exc), "probe rejected for unrelated reason: " + str(exc))
        return {"rejected": True, "exception": type(exc).__name__, "message": str(exc)}
    raise RuntimeError("mutation was accepted: " + expected)


def main():
    watched = {}

    def read(name):
        path = OUTER / name
        data, initial = lib.json_snapshot(path)
        watched[str(path)] = initial
        return data

    approval = read("integration-review/revision-v2/approved-source-manifest.json")
    pin = {"role": "integration", "path": "integration-review/revision-v2/approved-source-manifest.json",
           "identity": watched[str(OUTER / "integration-review/revision-v2/approved-source-manifest.json")],
           "source_sha256_pointer": "/approved_sources", "source_sha256_shape": "path-record-list"}
    approved = approval_adapter.approved_source_map(approval, pin)
    source_receipt = read("source-checkpoint/source-checkpoint.json")
    freeze = read("integration-review/revision-v2/tex-input-freeze.json")
    inputs = {p: row["sha256"] for p, row in freeze["files"].items()}
    pdf_path = Path(approval["reviewed_pdf"]["path"])
    pdf_identity = lib.identity(pdf_path)
    watched[str(pdf_path)] = pdf_identity
    config = {"source_checkpoint_identity": watched[str(OUTER / "source-checkpoint/source-checkpoint.json")],
              "approval_pins": [pin], "pdf": {"pages": 191, "input_sha256": inputs}}
    view = RootView(CANONICAL)
    source_validation = adapter.verify_source_receipts(view, OUTER, SOURCE, approved, config)
    pdf_validation = adapter.verify_pdf_receipts(view, OUTER, SOURCE, config, inputs, pdf_identity)

    mutations = {}
    reduced = dict(approved)
    reduced.pop(next(iter(reduced)))
    mutations["source_path_omission"] = rejection(
        lambda: adapter.verify_source_receipts(view, OUTER, SOURCE, reduced, config),
        "reviewed/staged/committed source maps differ")
    mutations["wrong_source_commit"] = rejection(
        lambda: adapter.verify_source_receipts(view, OUTER, lib.BASELINE, approved, config),
        "actual source checkpoint ancestry/status")
    changed = copy.deepcopy(config)
    changed["source_checkpoint_identity"]["sha256"] = "0" * 64
    mutations["wrong_source_receipt_identity"] = rejection(
        lambda: adapter.verify_source_receipts(view, OUTER, SOURCE, approved, changed),
        "actual source receipt identity")
    changed = copy.deepcopy(config)
    changed["pdf"]["pages"] = 190
    mutations["wrong_pdf_page_count"] = rejection(
        lambda: adapter.verify_pdf_receipts(view, OUTER, SOURCE, changed, inputs, pdf_identity),
        "reviewed PDF page count")
    reduced_inputs = dict(inputs)
    reduced_inputs.pop(next(iter(reduced_inputs)))
    mutations["omitted_pdf_input"] = rejection(
        lambda: adapter.verify_pdf_receipts(view, OUTER, SOURCE, config, reduced_inputs, pdf_identity),
        "actual reviewed PDF input freeze differs")
    mutations["different_pdf_hash"] = rejection(
        lambda: adapter.verify_pdf_receipts(view, OUTER, SOURCE, config, inputs, {**pdf_identity, "sha256": "0" * 64}),
        "precommit PDF approval identity")

    spec = read("clean-source/replay-spec.json")
    require(spec["ready"] is True and spec["unresolved"] == [] and spec["source_commit"] == SOURCE,
            "final replay specification is not resolved at expected source")
    require(spec["approved_source_sha256"] == approved and spec["pdf_input_sha256"] == inputs,
            "actual replay specification differs from independent source/PDF approval")
    require(spec["replay_guard_sha256"] == lib.merge_hashes(approved, inputs,
            spec["replays"]["counting"]["runtime_sha256"], spec["replays"]["torus"]["runtime_sha256"]),
            "actual complete replay guard differs")
    live = lib.source_state(CANONICAL, SOURCE, spec["replay_guard_sha256"], clean=False)
    expected_state = {"head": SOURCE, "status_porcelain": "", "sha256": spec["replay_guard_sha256"]}
    results = {}
    for kind in ("counting", "torus"):
        command = read(f"clean-source/{kind}/run-command.json")
        comparison = read(f"clean-source/{kind}/scientific-comparison.json")
        require(command["source_before"] == command["source_after"] == expected_state,
                "recorded clean start/end source state differs")
        require(command["checks_passed"] is True and command["command_executed"] is True
                and command["exit_status"] == command["returncode"] == 0 and command["stderr"] == "",
                "actual replay command did not complete successfully")
        require(command["spec_identity"] == watched[str(OUTER / "clean-source/replay-spec.json")]
                and command["source_approval_identity"] == pin["identity"], "replay receipt input identity mismatch")
        require(comparison["checks_passed"] is True and comparison["exit_status"] == 0, "comparison receipt failed")
        reference_path, result_path = Path(comparison["reference"]["path"]), Path(comparison["candidate"]["path"])
        before, before_identity = lib.json_snapshot(reference_path)
        after, after_identity = lib.json_snapshot(result_path)
        watched[str(reference_path)], watched[str(result_path)] = before_identity, after_identity
        require({k: comparison["reference"][k] for k in before_identity} == before_identity
                and {k: comparison["candidate"][k] for k in after_identity} == after_identity
                and command["result"] == after_identity and Path(command["output_path"]) == result_path,
                "recorded replay/comparison output identity mismatch")
        runtime = spec["replays"][kind]["runtime_sha256"]
        if kind == "counting":
            state = after["source"]
            require(state == after["source_at_completion"] and state["git_commit"] == SOURCE
                    and state["git_dirty"] is False and state["git_status_porcelain"] == [], "finite internal source provenance")
            require({r["path"]: r["sha256"] for r in state["sources"]} == runtime, "finite runtime source map")
            fresh = lib.counting_comparison(before, after)
        else:
            provenance = after["provenance"]
            require(after["phase"] == "clean_replay" and provenance["source_commit"] == SOURCE
                    and provenance["source_sha256"] == runtime and provenance["repository_dirty_at_start"] is False
                    and provenance["git_status_porcelain_at_start"] == [], "full v3 internal source provenance")
            fresh = lib.torus_report_comparison(before, after)
            fresh.update(lib.torus_raw_comparison(before, after, OUTER))
            watched.update(fresh["external_input_identities"])
        for key, value in fresh.items():
            require(lib.encode(comparison[key]) == lib.encode(value), "fresh comparison differs from retained receipt: " + key)
        results[kind] = {"result_identity": after_identity, "reference_identity": before_identity,
                         "comparison_receipt_identity": watched[str(OUTER / f"clean-source/{kind}/scientific-comparison.json")],
                         "fresh_comparison_matches_retained_receipt": True,
                         "counts": fresh.get("check_counts", fresh.get("surface_counts")),
                         "blocks": fresh.get("blocks"), "external_native_raw_files_freshly_rehashed": len(fresh.get("external_input_identities", {}))}

    require(source_receipt["source_commit"] == SOURCE and len(approved) == 33 and len(inputs) == 26,
            "source/PDF scope changed")
    for path in (HERE / "subject").glob("*.py"):
        require(not any(isinstance(node, ast.Assert) for node in ast.walk(ast.parse(path.read_text()))),
                "removable assertion gate in production adapter")
    for name, frozen_identity in watched.items():
        lib.require_unchanged(Path(name), frozen_identity, "independent reviewed receipt/input")
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "python_optimized": sys.flags.optimize,
              "checks_passed": True, "scope": "Frozen adapter and retained actual evidence audit through read-only path routing; no real replay, candidate verification, build, visual reinspection or cleanup",
              "source_commit": SOURCE, "approved_source_paths": len(approved), "replay_guard_paths": len(spec["replay_guard_sha256"]),
              "source_receipt_adapter": source_validation, "PDF_receipt_adapter": pdf_validation,
              "argument_mutation_probes": mutations, "actual_replay_evidence": results,
              "current_canonical_status_at_source_identity_read": live["status_porcelain"],
              "current_status_is_not_used_as_a_historical_clean_replay_claim": True,
              "watched_input_identities": watched, "canonical_mutations": []}
    path = HERE / ("actual-receipt-audit-optimized.json" if sys.flags.optimize else "actual-receipt-audit-normal.json")
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"checks_passed": True, "scope": report["scope"], "evidence": str(path),
                      "argument_mutations_rejected": len(mutations), "source_paths": len(approved), "PDF_inputs": len(inputs),
                      "source_receipt_adapter": source_validation, "PDF_receipt_adapter": pdf_validation,
                      "actual_replay_evidence": results}, indent=2))


if __name__ == "__main__":
    main()
