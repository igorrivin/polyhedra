"""Strict v1/v2 evidence comparison; no source or scientific artifact mutation."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "consolidated"


def digest(path):
    h = sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


old_path = HERE / "full8192-author-v1/result.json"
new_path = HERE / "full8192-author-v2/result.json"
old, new = (json.loads(p.read_text()) for p in (old_path, new_path))
assert old["checks_passed"] and new["checks_passed"]
assert old["source_input_immutability_gate_passed"] and new["source_input_immutability_gate_passed"]
for rel, expected in new["provenance"]["source_sha256"].items():
    assert digest(ROOT / rel) == expected, rel
expected_printed = {
    "modular": {32: ("2.1686", "0.6015"), 128: ("1.1130", "0.3501"),
                512: ("0.7415", "0.1697"), 2048: ("0.4342", "0.0950")},
    "asymmetric": {32: ("0.8134", "0.2734"), 128: ("0.5285", "0.1494"),
                   512: ("0.3756", "0.0950"), 2048: ("0.2492", "0.0612")},
}
report = {"evidence_status": "author_replays_pending_independent_code_review_and_clean_source_replay",
          "old_report": {"path": str(old_path), "sha256": digest(old_path)},
          "new_report": {"path": str(new_path), "sha256": digest(new_path)},
          "source_freeze_sha256": new["provenance"]["source_sha256"],
          "current_sources_match_v2_freeze": True,
          "source_commit": new["provenance"]["source_commit"],
          "surfaces": []}
for before, after in zip(old["surfaces"], new["surfaces"]):
    assert before["surface"] == after["surface"]
    identical = ["counts", "blocks", "conditional_M_bounds", "cutoff_margins",
                 "count_through_cutoff", "count_through_guard", "root_count", "sector_counts",
                 "visited_outward_nodes", "pruned_frontier_nodes", "maximum_depth",
                 "maximum_visited_slope_coordinate", "maximum_subtraction_ratio",
                 "minimum_outward_log_growth", "slope_identity_fnv1a64_decimal"]
    for key in identical:
        assert before[key] == after[key], (after["surface"], key)
    streams = []
    for previous, current in zip(before["raw_streams"], after["raw_streams"]):
        assert Path(previous["path"]).name == Path(current["path"]).name
        assert previous["bytes"] == current["bytes"]
        assert previous["sha256"] == current["sha256"]
        assert digest(Path(previous["path"])) == previous["sha256"]
        assert digest(Path(current["path"])) == current["sha256"]
        streams.append({"name": Path(current["path"]).name, "bytes": current["bytes"],
                        "sha256": current["sha256"], "v1_v2_bytes_have_same_sha256": True})
    printed = []
    for block in after["blocks"]:
        if block["T"] in expected_printed[after["surface"]]:
            observed = (f'{block["M"]["value"]:.4f}', f'{block["Q"]:.4f}')
            expected = expected_printed[after["surface"]][block["T"]]
            assert observed == expected
            printed.append({"T": block["T"], "new_M": block["M"]["value"],
                            "new_Q": block["Q"], "retained_historical_printed_M_Q": expected,
                            "agrees_at_printed_precision": True})
    near = [s for s in after["precision_samples"]["samples"]
            if "declared_twelve_nearest_below_final_cutoff_per_sector" in s["selection_reasons"]]
    assert len({tuple(s["slope"]) for s in near}) == 36
    assert [sum(s["sector"] == i for s in near) for i in range(3)] == [12, 12, 12]
    all_width = max(after["conditional_M_bounds"], key=lambda b: b["width_approx"])
    printed_width = max((b for b in after["conditional_M_bounds"] if b["T"] in expected_printed[after["surface"]]),
                        key=lambda b: b["width_approx"])
    report["surfaces"].append({"surface": after["surface"], "count": after["count_through_cutoff"],
        "strictly_identical_scientific_fields": identical, "streams": streams,
        "printed_row_comparison": printed, "native_peak_rss_bytes": after["peak_rss_bytes"],
        "native_seconds": after["timing_seconds"]["native_total"],
        "maximum_selected_native_residual": after["precision_samples"]["maximum_native_absolute_residual"],
        "maximum_selected_100_vs140_residual": after["precision_samples"]["maximum_precision_absolute_residual"],
        "precision_selection_summary": {key: value for key, value in after["precision_samples"].items() if key != "samples"},
        "maximum_all_row_sensitivity_width": all_width,
        "maximum_printed_subset_sensitivity_width": printed_width,
        "minimum_dyadic_cutoff_distance": min(min(r["below_distance"], r["above_distance"])
                                              for r in after["cutoff_margins"] if r["cutoff"] <= 8192)})
report["new_driver_elapsed_seconds"] = new["elapsed_seconds"]
report["all_strict_comparisons_passed"] = True
with (HERE / "v1-v2-comparison-and-author-freeze.json").open("x") as stream:
    json.dump(report, stream, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({"all_strict_comparisons_passed": True,
                  "surfaces": [{"surface": s["surface"], "count": s["count"],
                                "near_final_minimum_length": s["precision_selection_summary"]["near_final_minimum_length"],
                                "near_final_maximum_length": s["precision_selection_summary"]["near_final_maximum_length"]}
                               for s in report["surfaces"]]}))
