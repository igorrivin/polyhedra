"""Validate actual final source/PDF receipt schemas without rewriting evidence.

This adapter reads the retained original receipts, including the failed default
whitespace check. It performs no build, inspection, cleanup, replay or mutation.
"""
from pathlib import Path
import struct
import subprocess

from checkpoint_lib import (
    BASELINE, ENV, KNOWN_DANGLING, REL, digest, encode, git, identity,
    load_json, outer_path, parse_json, require,
)
from source_approval_adapter import approved_source_map

SOURCE_SHA = "06513002e97910d2a2f4d267fb2ce79db5ee792c5d1602ed8ff480d0c0fc4f2e"
INTEGRATION_SHA = "0fe9b4a314efdd5d1d8c33f448b49d36d998200bcad2d09a0dd12ede5cbf7a2d"
EXCEPTION_SHA = "9e35561bf07b707f298b559aab86d4f642209e13a58663b33fd2835ed0ef04fa"
EOF_DIAGNOSTICS = [
    "book/chapters/25-global-coefficient-filters.tex:361: new blank line at EOF.",
    "book/chapters/27-weighted-mixing-converse.tex:850: new blank line at EOF.",
    "book/chapters/28-genus-two-model.tex:769: new blank line at EOF.",
    "book/chapters/29-controlled-observables.tex:772: new blank line at EOF.",
    "book/chapters/31-arithmetic-remainder.tex:415: new blank line at EOF.",
]


def whitespace_record(row, exception, expected_command):
    require(exception["authority"] == "/root" and exception["approved"] is True
            and exception["source_edits_authorized"] is False, "wrong whitespace exception authority/scope")
    require(exception["approved_source_manifest_sha256"] == INTEGRATION_SHA
            and exception["diagnostics"] == EOF_DIAGNOSTICS
            and exception["original_command_returncode"] == 2, "original failed default check must remain explicit")
    require(row["original_command"] == expected_command and row["original_diagnostics"] == EOF_DIAGNOSTICS,
            "whitespace exception changed the exact command/diagnostic scope")
    require(row["adjusted_core_whitespace"] == "-blank-at-eof" and row["prior_core_whitespace"] is None
            and row["only_blank_at_eof_disabled"] is True, "whitespace waiver disabled an extra rule")
    require(row["adjusted_check_returncode"] == 0 and row["adjusted_check_output"] == "",
            "effective whitespace check must pass without diagnostics")
    require(row["exception_sha256"] == EXCEPTION_SHA and row["root_decision"] == exception["decision"]
            and row["root_reason"] == exception["reason"], "whitespace exception binding")


def verify_source_receipts(root, outer, source, approved, config):
    base = root / REL
    path = base / "source-checkpoint/source-checkpoint.json"
    require(digest(path) == SOURCE_SHA == config["source_checkpoint_identity"]["sha256"], "actual source receipt identity")
    record = load_json(path)
    require(record["passed"] is True and record["source_commit"] == source
            and record["baseline_commit"] == record["parent_commit"] == BASELINE,
            "actual source checkpoint ancestry/status")
    require(record["git_status_porcelain"] == "" and record["index_clean"] is True
            and record["tracked_path_count"] == 1939 and record["changed_path_count"] == 33
            and record["modified_existing_count"] == 8 and record["new_count"] == 25,
            "actual source checkpoint clean counts")
    require(all(record[k] is False for k in ("artifact_generation_performed", "canonical_docs_generated",
                                            "numerical_replay_performed", "remote_operation_performed")),
            "source and artifact/replay boundaries were conflated")
    for item in record["receipt_files"]:
        require(digest(base / item["path"]) == item["sha256"], "retained source receipt dependency: " + item["path"])
    stage = load_json(base / "source-checkpoint/stage.json")
    require(stage["passed"] is True and stage["phase"] == "stage" and stage["baseline_commit"] == BASELINE,
            "actual staging receipt status")
    for rows in (stage["staged_files"], record["committed_files"]):
        require(len(rows) == len({r["path"] for r in rows}) == 33
                and {r["path"]: r["sha256"] for r in rows} == approved
                and all(r["materialized_identical"] is True for r in rows), "reviewed/staged/committed source maps differ")
        for row in rows:
            require(identity(root / row["path"]) == {"sha256": row["sha256"], "bytes": row["bytes"]}, "actual source receipt byte count")
    require(stage["staged_tree"] == record["source_tree"] == git(root, "rev-parse", source + "^{tree}").decode().strip(),
            "staged/source tree identity")
    pin = next(p for p in config["approval_pins"] if p["role"] == "integration")
    final_approval = load_json(base / pin["path"])
    require(pin["identity"]["sha256"] == INTEGRATION_SHA == record["approval"]["manifest_sha256"]
            and approved_source_map(final_approval, pin) == approved, "source receipt independent approval identity")
    require(stage["approval"] == record["approval"], "staged and final approval context differs")
    review_directory = (base / pin["path"]).parent
    for item in record["approval"]["independent_receipts"]:
        p = Path(item["path"])
        require(item["passed"] is True and digest(review_directory / p.name) == item["sha256"],
                "final integration dependency identity")
    parent = base / "parent-source-approval.json"
    require(digest(parent) == record["approval"]["parent_approval_sha256"] and load_json(parent)["all_passed"] is True,
            "parent source approval binding")
    exception_path = base / "source-checkpoint/root-whitespace-exception.json"
    require(digest(exception_path) == EXCEPTION_SHA, "exact EOF exception identity")
    exception = load_json(exception_path)
    require(len(stage["whitespace_checks"]) == len(record["whitespace_checks"]) == 1, "exactly one bounded whitespace rule exception")
    whitespace_record(stage["whitespace_checks"][0], exception, ["git", "diff", "--cached", "--check"])
    whitespace_record(record["whitespace_checks"][0], exception, ["git", "diff-tree", "--check", source + "^", source])
    commands = [parse_json(line) for line in (base / "source-checkpoint/commands.jsonl").read_bytes().splitlines()]
    by_sequence = {r["sequence"]: r for r in commands}
    require(len(by_sequence) == len(commands), "duplicate source command sequence")
    for sequence in (40, 47, 49, 90, 92, 180, 182):
        command = by_sequence[sequence]
        adjusted = sequence in (49, 92, 182)
        suffix = ["diff-tree", "--check", source + "^", source] if sequence in (180, 182) else ["diff", "--cached", "--check"]
        expected = ["git"] + (["-c", "core.whitespace=-blank-at-eof"] if adjusted else []) + suffix
        require(command["argv"] == expected and command["returncode"] == (0 if adjusted else 2), "actual whitespace command/exit status")
        for stream in ("stdout", "stderr"):
            row = command[stream]
            p = base / "source-checkpoint" / row["path"]
            require(identity(p) == {"sha256": row["sha256"], "bytes": row["bytes"]}, "whitespace command output bytes")
            require(p.read_text().splitlines() == ([] if adjusted or stream == "stderr" else EOF_DIAGNOSTICS), "whitespace command diagnostics")
    current = []
    for options in ([], ["-c", "core.whitespace=-blank-at-eof"]):
        process = subprocess.run(["git", *options, "diff-tree", "--check", source + "^", source], cwd=root,
                                 env=ENV, capture_output=True, text=True, check=False)
        require(process.returncode == (0 if options else 2) and process.stderr == ""
                and process.stdout.splitlines() == ([] if options else EOF_DIAGNOSTICS), "current committed-source whitespace scope differs")
        current.append({"returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr})
    integrity = record["fsck"]
    require(integrity["returncode"] == 0 and set(integrity["output"]) == KNOWN_DANGLING
            and integrity["unexpected_findings"] == [] and integrity["cleanup_performed"] is True, "actual source integrity receipt")
    recovery = integrity["sidecar_recovery"]
    removal_path = base / "source-checkpoint/git-sidecar-recovery/removal.json"
    require(digest(removal_path) == recovery["sha256"], "sidecar removal receipt identity")
    removal = load_json(removal_path)
    require(removal == recovery["details"] and removal["source_commit"] == source
            and removal["removed_count"] == 45 and removal["all_genuine_counterparts_unchanged"] is True
            and removal["only_exact_fsck_reported_confirmed_appledouble_sidecars_removed"] is True, "sidecar cleanup scope")
    inspection_path = base / "source-checkpoint" / removal["inspection_path"]
    require(digest(inspection_path) == removal["inspection_sha256"], "sidecar inspection binding")
    inspection = load_json(inspection_path)
    require(inspection["all_headers_backups_counterparts_validated"] is True and inspection["deletion_performed"] is False
            and inspection["reported_count"] == len(inspection["files"]) == 45, "sidecar inspection count/scope")
    require({r["reported_path"] for r in inspection["files"]} == {r["path"] for r in removal["removed"]}
            and all(r["genuine_counterpart_unchanged"] is True for r in removal["removed"]), "exact inspected/removal path set")
    for row in inspection["files"]:
        backup = outer_path(outer, "source-checkpoint/" + row["backup_path"])
        require(identity(backup) == {"sha256": row["sidecar_sha256"], "bytes": row["sidecar_bytes"]}
                and row["backup_sha256"] == row["sidecar_sha256"] and row["backup_byte_for_byte_verified"] is True
                and row["genuine_counterpart"]["git_validated"] is True, "sidecar exact backup/counterpart evidence")
        data = backup.read_bytes()
        require(len(data) >= 26, "short AppleDouble backup")
        magic, version = struct.unpack(">II", data[:8])
        count = struct.unpack(">H", data[24:26])[0]
        require(magic == 0x00051607 and version == 0x00020000 and 26 + 12 * count <= len(data), "AppleDouble header/entry-table bounds")
        for i in range(count):
            _, offset, size = struct.unpack(">III", data[26 + 12*i:38 + 12*i])
            require(offset >= 26 + 12*count and offset + size <= len(data), "AppleDouble entry bounds")
    return {"source_receipt_sha256": SOURCE_SHA, "source_tracked_files": 1939, "default_whitespace_check_passed": False,
            "accepted_blank_at_eof_paths": [s.split(":", 1)[0] for s in EOF_DIAGNOSTICS],
            "effective_whitespace_check_passed": True, "current_source_whitespace_recheck": current,
            "recorded_validated_sidecar_removals": 45, "sidecar_backups_verified": 45,
            "metadata_cleanup_by_this_verifier": False}


def verify_pdf_receipts(root, outer, source, config, inputs, pdf_identity):
    base = root / REL / "integration-review/revision-v2"
    approval = load_json(base / "approved-source-manifest.json")
    freeze = load_json(base / "tex-input-freeze.json")
    build = load_json(base / "pdf-build-receipt.json")
    visual = load_json(base / "pdf-visual-approval.json")
    render = load_json(base / "pdf-render-manifest.json")
    for row in approval["receipts"]:
        require(digest(base / row["path"]) == row["sha256"], "independent PDF/integration receipt binding")
    require(freeze["count"] == 26 and {p: r["sha256"] for p, r in freeze["files"].items()} == inputs,
            "actual reviewed PDF input freeze differs")
    require(approval["reviewed_pdf"]["precommit"] is True
            and approval["reviewed_pdf"]["sha256"] == build["pdf_sha256"] == visual["source_pdf_sha256"]
            == render["source_pdf_sha256"] == pdf_identity["sha256"], "precommit PDF approval identity")
    require(build["build_status"] == "approved_precommit_frozen_source_build" and build["returncode"] == 0
            and build["actual_tex_input_count"] == 26 and set(build["actual_tex_input_paths"]) == set(inputs)
            and build["source_freeze_unchanged_after_build"] is True and build["freeze_matches_live_source_at_final_review"] is True,
            "actual precommit build input/command status")
    require(build["compiled_unique_labels"] == 607 and build["compiled_unique_bibliography_keys"] == 129
            and build["overfull_count"] == 0 and build["undefined_references_or_citations"] is False,
            "actual PDF convergence counts")
    require(build["pages"] == visual["source_pdf_pages"] == render["pdf_page_count"] == config["pdf"]["pages"] == 191,
            "reviewed PDF page count")
    require(visual["decision"] == "approve" and visual["open_findings"] == [], "actual visual approval")
    pages = visual["inspected_pages"]
    require(len(pages) == len(set(pages)) == visual["inspected_page_count"] == 94
            and all(1 <= p <= 191 for p in pages) and render["rendered_page_coverage"] == pages,
            "actual 94-page inspection scope")
    require(visual["images"] == render["images"] and visual["contact_sheets"] == render["contact_sheets"]
            and [r["page"] for r in visual["images"]] == pages, "render/inspection image identities")
    require(len(visual["full_page_legibility_checks"]) == 10 and set(visual["full_page_legibility_checks"]) <= set(pages),
            "full-page legibility scope")
    for row in visual["images"] + visual["contact_sheets"]:
        path = outer_path(outer, "integration-review/revision-v2/" + row["path"])
        require(digest(path) == row["sha256"], "retained reviewed image changed")
    marker = load_json(root / REL / "parent-preliminary-build/build-command.json")
    require(marker["pdf_operation_marker_run_before_this_build"] is True and build["artifact_marker"].startswith("Not rerun."),
            "once-only marker provenance")
    require(encode(config["pdf"]["input_sha256"]) == encode(inputs), "PDF contract input identity")
    return {"PDF_pages": 191, "actually_visually_reviewed_pages": 94, "full_page_legibility_checks": 10,
            "PDF_build_timing": "reviewed precommit build copied byte-for-byte", "marker_reexecuted": False}
