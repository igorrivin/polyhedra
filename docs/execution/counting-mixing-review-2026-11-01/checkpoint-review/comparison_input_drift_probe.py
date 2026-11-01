"""Inject a file change after real comparison, before its receipt is assembled."""
import contextlib
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import checkpoint_lib as lib
import compare_replays as comparison

HERE = Path(__file__).resolve().parent


def main():
    with tempfile.TemporaryDirectory(prefix="comparison-drift-", dir=HERE) as directory:
        outer = Path(directory)
        data = lib.load_json(HERE.parent / "computation/revision-v2/author-result-60-90-v2.json")
        for name in ("reference.json", "candidate.json"):
            (outer / name).write_text(json.dumps(data) + "\n")
        candidate = outer / "candidate.json"
        before = lib.identity(candidate)

        def compare_then_inject_drift(left, right):
            result = lib.counting_comparison(left, right)
            changed = lib.load_json(candidate)
            changed["check_counts"]["exact"] += 1
            candidate.write_text(json.dumps(changed) + "\n")
            return result

        argv = ["compare_replays.py", "--kind", "counting", "--outer", str(outer),
                "--reference", "reference.json", "--candidate", "candidate.json", "--receipt", "receipt.json"]
        failure = None
        with patch.object(comparison, "counting_comparison", compare_then_inject_drift), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
            try:
                comparison.main()
            except Exception as exc:
                failure = type(exc).__name__ + ": " + str(exc)
        receipt = lib.load_json(outer / "receipt.json") if (outer / "receipt.json").exists() else None
        result = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
                  "scope": "Synthetic post-comparison mutation injection; actual comparison and receipt assembly, not a scientific replay",
                  "python_optimized": sys.flags.optimize, "failure": failure,
                  "candidate_before": before, "candidate_after": lib.identity(candidate),
                  "receipt_written": receipt is not None, "receipt_checks_passed": receipt["checks_passed"] if receipt else None,
                  "receipt_candidate": receipt["candidate"] if receipt else None,
                  "receipt_exact_count": receipt["check_counts"]["exact"] if receipt else None,
                  "actual_candidate_exact_count": lib.load_json(candidate)["check_counts"]["exact"]}
        path = HERE / ("comparison-input-drift-optimized-v1.json" if sys.flags.optimize else "comparison-input-drift-normal-v1.json")
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
