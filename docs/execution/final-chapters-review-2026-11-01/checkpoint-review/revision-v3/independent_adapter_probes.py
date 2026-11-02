"""Independent adapter controls and read-only actual-receipt compatibility."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys
import tempfile

HERE = Path(__file__).resolve().parent
SUBJECT = HERE / "subject-v3"
OUTER = HERE.parents[1]
sys.path.insert(0, str(SUBJECT))
import checkpoint_lib as lib  # noqa: E402


def main():
    rows = []
    with tempfile.TemporaryDirectory(prefix="adapter-review-", dir=HERE) as temporary:
        base = Path(temporary)
        outer = base / "outer"
        outside = base / "outside"
        outer.mkdir()
        outside.mkdir()
        for name in ("reference.json", "identical-bytes.json"):
            (outer / name).write_text('{"synthetic":true}\n')
        (outer / "alias.json").symlink_to(outer / "reference.json")
        (outer / "escape").symlink_to(outside, target_is_directory=True)
        identity = lib.identity(outer / "reference.json")
        value = {"path": "reference.json", **identity}
        pin = {"reference_identity_pointer": "/result", "reference_identity_shape": "path-record"}

        def probe(name, record, selected_pin, declared, expected):
            original = repr(record)
            try:
                result = lib.approved_reference_identity(record, selected_pin, outer, declared)
                outcome = {"accepted": True, "projected_identity": result}
            except Exception as exc:
                outcome = {"accepted": False, "exception": type(exc).__name__, "reason": str(exc)}
            if repr(record) != original:
                raise RuntimeError("Adapter mutated approval: " + name)
            rows.append({"id": name, "expected_acceptance": expected, "approval_unchanged": True, **outcome})

        probe("explicit_path_relative", {"result": value}, pin, "reference.json", True)
        probe("explicit_path_absolute_declaration", {"result": value}, pin, str(outer / "reference.json"), True)
        probe("default_two_key_identity", {"result": identity}, {"reference_identity_pointer": "/result"}, "reference.json", True)
        probe("explicit_two_key_identity", {"result": identity}, {"reference_identity_pointer": "/result", "reference_identity_shape": "identity"}, "reference.json", True)
        probe("unrelated_approval_fields_preserved", {"result": value, "other_scientific_fields": {"unchanged": [1, "1", True]}}, pin, "reference.json", True)
        for field in value:
            bad = {k: v for k, v in value.items() if k != field}
            probe("missing_" + field, {"result": bad}, pin, "reference.json", False)
        for field in ("extra", "size", "approved"):
            probe("extra_" + field, {"result": {**value, field: True}}, pin, "reference.json", False)
        for index, shape in enumerate((None, False, 0, [], {}, "guess", "identity")):
            probe("bad_shape_" + str(index), {"result": value}, {**pin, "reference_identity_shape": shape}, "reference.json", False)
        probe("path_record_not_inferred", {"result": value}, {"reference_identity_pointer": "/result"}, "reference.json", False)
        for index, bad in enumerate((True, 1.0, "1", -1, None, [], {})):
            probe("bad_bytes_" + str(index), {"result": {**value, "bytes": bad}}, pin, "reference.json", False)
        for index, bad in enumerate((None, False, 1, "", "f" * 63, "f" * 65, "F" * 64, "g" * 64)):
            probe("bad_digest_" + str(index), {"result": {**value, "sha256": bad}}, pin, "reference.json", False)
        for index, name in enumerate((None, False, 1, [], {}, "", ".", "./reference.json", "sub//reference.json",
                                      "../reference.json", "sub/../reference.json", "._reference.json",
                                      str(outer / "reference.json"), "identical-bytes.json", "alias.json", "escape/reference.json")):
            probe("bad_approved_path_" + str(index), {"result": {**value, "path": name}}, pin, "reference.json", False)
        for index, declared in enumerate(("identical-bytes.json", "alias.json", "escape/reference.json", "../reference.json", str(outside / "reference.json"))):
            probe("bad_declared_path_" + str(index), {"result": value}, pin, declared, False)
        probe("matching_escape_paths_rejected", {"result": {**value, "path": "escape/reference.json"}}, pin, "escape/reference.json", False)
        probe("missing_selected_pointer", {"unrelated": value}, pin, "reference.json", False)

    # Read only the frozen computational approval/result. Do not bind or audit
    # the live manuscript currently undergoing integration.
    approval_path = OUTER / "computation-review/revision-v2/final-acceptance.json"
    approval, approval_identity = lib.json_snapshot(approval_path)
    if approval_identity["sha256"] != "70070fe32c42961d68b035ccb7fae5b012c50ac5814ca42bd05689bfc64b6592":
        raise RuntimeError("Real computational approval identity changed")
    approved = approval["accepted_author_result"]
    real_pin = {"reference_identity_pointer": "/accepted_author_result", "reference_identity_shape": "path-record"}
    projection = lib.approved_reference_identity(approval, real_pin, OUTER, approved["path"])
    result_path = OUTER / approved["path"]
    result, result_identity = lib.json_snapshot(result_path)
    if projection != result_identity or result_identity["sha256"] != "5f73fce03e43103dc457570bcd90f4722599b5ac0d67a9b9b88d9e00679f0429":
        raise RuntimeError("Real approved reference projection differs")
    # Only the fragment needed to validate the already approved author report;
    # this is explicitly not a ready replay specification.
    author_stage_fragment = {
        "expected_groups": approval["accepted_group_names"],
        "expected_check_counts": approval["derived_check_counts"],
        "runtime_sha256": approval["accepted_runtime_sha256"],
        "reference_manuscript_sha256": approval["author_current_manuscript_sha256"],
        "reference_tex_observation_sha256": approval["author_tex_sha256"],
    }
    lib.validate_report(result, author_stage_fragment, clean=False)
    lib.require_unchanged(approval_path, approval_identity, "actual approval")
    lib.require_unchanged(result_path, result_identity, "actual approved author report")
    mismatches = [row["id"] for row in rows if row["accepted"] != row["expected_acceptance"]]
    record = {
        "scope": "Independent adapter probes and read-only accepted author-stage schema compatibility; no final binding, live manuscript approval or replay.",
        "probe_count": len(rows), "unexpected_outcomes": mismatches, "probes": rows,
        "real_compatibility": {"approval": {"path": str(approval_path.relative_to(OUTER)), **approval_identity},
                               "reference": {"path": approved["path"], **result_identity},
                               "projected_identity_matches": True, "author_stage_schema_passes": True,
                               "input_identities_unchanged": True, "live_manuscript_read": False},
        "subject_lib_sha256": sha256((SUBJECT / "checkpoint_lib.py").read_bytes()).hexdigest(),
    }
    name = "independent-probes-optimized.json" if sys.flags.optimize else "independent-probes-normal.json"
    with (HERE / name).open("x") as handle:
        json.dump(record, handle, indent=2, allow_nan=False)
        handle.write("\n")
    if mismatches:
        raise RuntimeError("Unexpected adapter outcomes: " + str(mismatches))
    print(json.dumps({"probe_count": len(rows), "unexpected_outcomes": [], "real_compatibility": True}))


if __name__ == "__main__":
    main()
