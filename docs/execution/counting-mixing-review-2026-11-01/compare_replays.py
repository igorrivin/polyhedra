#!/usr/bin/env python3
"""Compare preserved reports with frozen input identities and failure receipts.

This is scientific equality plus native/raw identity for torus. Clean-source
provenance is a separate verifier gate; this command performs no replay.
"""
from argparse import ArgumentParser
import json
from pathlib import Path

from checkpoint_lib import (
    counting_comparison, external_inputs_unchanged, json_snapshot, outer_path, receipt_record, require,
    require_unchanged, torus_raw_comparison, torus_report_comparison,
)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--kind", choices=("counting", "torus"), required=True)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--reference", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--receipt", required=True)
    args = parser.parse_args()
    outer = args.outer.resolve()
    report = {"kind": args.kind, "reference": {"path": args.reference},
              "candidate": {"path": args.candidate}, "stage": "input_snapshot_guards",
              "scope": "Strict finite scientific equality, including native/raw identity for torus; not a replay, independent mathematical approval, interval proof or historical provenance recovery."}
    with receipt_record(outer, args.receipt, report):
        a, b = (outer_path(outer, name) for name in (args.reference, args.candidate))
        require(a.resolve() != b.resolve(), "comparison requires two distinct run artifacts")
        before, before_identity = json_snapshot(a)
        report["reference"] = {"path": str(a), **before_identity}
        after, after_identity = json_snapshot(b)
        report["candidate"] = {"path": str(b), **after_identity}
        require_unchanged(a, before_identity, "comparison reference")
        require_unchanged(b, after_identity, "comparison candidate")
        report["stage"] = "scientific_comparison"
        if args.kind == "counting":
            comparison = counting_comparison(before, after)
        else:
            comparison = torus_report_comparison(before, after)
            report["stage"] = "native_and_raw_comparison"
            comparison.update(torus_raw_comparison(before, after, outer))
        report.update(comparison)
        report["stage"] = "final_input_identity_guards"
        require_unchanged(a, before_identity, "comparison reference")
        require_unchanged(b, after_identity, "comparison candidate")
        if args.kind == "torus":
            external_inputs_unchanged(comparison["external_input_identities"])
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "kind": args.kind, "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
