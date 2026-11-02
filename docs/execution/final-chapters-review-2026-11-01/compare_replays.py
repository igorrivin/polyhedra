#!/usr/bin/env python3
"""Compare the approved author report and actual clean-source report, read-only."""
from argparse import ArgumentParser
import json
from pathlib import Path

from checkpoint_lib import (
    approved_spec, finite_comparison, json_snapshot, outer_path, receipt_record, recheck, require,
)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    spec, spec_identity = json_snapshot(args.spec)
    root, outer = Path(spec["root"]).resolve(), Path(spec["outer"]).resolve()
    require(not outer.is_relative_to(root) and not root.is_relative_to(outer),
            "canonical and outer evidence directories must be disjoint")
    report = {"schema_version": 1, "spec_identity": spec_identity, "source_commit": spec.get("source_commit"),
              "frozen_input_identities": {}, "candidate": None, "stage": "approval_guards",
              "scope": "Strict report comparison and frozen-input checks; no numerical replay or independent scientific approval."}
    with receipt_record(outer, args.receipt, report):
        _, _, reference, frozen = approved_spec(spec)
        frozen[str(args.spec.resolve())] = spec_identity
        path = outer_path(outer, spec["output"])
        require(path.resolve() != outer_path(outer, spec["reference"]["path"]).resolve(),
                "comparison requires two distinct run artifacts")
        candidate, candidate_identity = json_snapshot(path)
        frozen[str(path)] = candidate_identity
        report.update({"frozen_input_identities": frozen, "candidate": candidate_identity,
                       "stage": "scientific_comparison"})
        recheck(frozen)
        report.update(finite_comparison(reference, candidate, spec))
        report["stage"] = "final_input_identity_guards"
        recheck(frozen)
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "receipt": str(args.receipt)}))


if __name__ == "__main__":
    main()
