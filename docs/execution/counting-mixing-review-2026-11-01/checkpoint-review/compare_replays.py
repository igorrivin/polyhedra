#!/usr/bin/env python3
"""Compare two preserved reports strictly, retaining both actual identities.

This checks scientific equality and, for the torus campaign, native reports
and raw stream bytes. Clean-source provenance is a separate verifier gate.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
import json
from pathlib import Path

from checkpoint_lib import (
    counting_comparison, identity, load_json, outer_path, require,
    torus_raw_comparison, torus_report_comparison,
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
    a, b, receipt = (outer_path(outer, name) for name in (args.reference, args.candidate, args.receipt))
    require(a.resolve() != b.resolve(), "comparison requires two distinct run artifacts")
    require(not receipt.exists() and not receipt.is_symlink() and receipt.parent.is_dir(), "receipt must be a new outer path")
    before, after = load_json(a), load_json(b)
    if args.kind == "counting":
        comparison = counting_comparison(before, after)
    else:
        comparison = torus_report_comparison(before, after)
        comparison.update(torus_raw_comparison(before, after, outer))
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(), "checks_passed": True,
              "kind": args.kind, "reference": {"path": str(a), **identity(a)},
              "candidate": {"path": str(b), **identity(b)}, **comparison,
              "scope": "Strict finite scientific equality, including native/raw identity for torus; not a new replay, independent mathematical approval, interval proof or historical provenance recovery."}
    with receipt.open("x") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"checks_passed": True, "kind": args.kind, "receipt": str(receipt)}))


if __name__ == "__main__":
    main()
