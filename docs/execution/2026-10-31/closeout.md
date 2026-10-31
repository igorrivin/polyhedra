# First checkpoint closeout

The reviewed source and its generated Section 9 companion are committed locally. The first bounded integration increment is complete; the remaining phase gates in the [checkpoint](README.md) still apply.

| Record | Commit |
| --- | --- |
| Reviewed source, tests and evidence | `c02b358de5a6f724faf3368a641ba64f5841d859` |
| Outputs regenerated from that clean source | `74e2abc67e434e0d7eadf70d7becaa6de2f77785` |

The canonical [result](../../../artifacts/section9/result.json) records `repository_dirty_at_start=false` and an empty initial Git status. All seven recorded source/input/book hashes match both the working files and the source commit. Exact rational fixture checks and all twelve numerical checks pass. The [HTML companion](../../../site/section9/index.html) has twelve valid local/anchor links, and its JavaScript passes a syntax check. This is static verification; browser interaction and layout remain unverified.

The final [reproduction ZIP](../../../site/section9/downloads/section9-reproduction.zip) was extracted outside every checkout and run with the minimal Python 3.12 environment, with `PYTHONPATH` unset. It imports the bundled numerical subset, passes all exact and twelve numerical checks, and verifies all nine payload hashes. Its [detached result](final-detached-result.json) retains the clean originating commit while recording detached Git state as unavailable. Omitted book assets are explicitly unavailable.

| Final artifact | SHA-256 |
| --- | --- |
| Canonical result JSON | `75403f2c513ec1d962ba3742409f5b08ba1de7a87a17b7f7265ede2890a978bf` |
| Runnable reproduction ZIP | `b95eea258e8f6ad8928a583be68b221acb1dbec825c5118bdeabfbfd39291f04` |

[Machine closeout evidence](closeout.json) records the commands, all nine artifact hashes and the independent verification scope. All 953 original tracked-file hashes still match the inventory; both original worktrees are clean at their original heads, and both heads remain reachable in the integrated history. No remote is configured; this is a local checkpoint with no push or Site deployment.

Git object integrity passed after removing 143 verified AppleDouble sidecars generated inside this new checkout's `.git` directory. The [cleanup receipt](git-metadata-cleanup.json) records their headers, hashes and unchanged real Git siblings. Original repositories and actual Git objects/refs were not removed. The final documentation commit can itself generate more filesystem sidecars, so final HEAD/status/fsck and any subsequent verified cleanup are recorded in the outer workspace at `execution/2026-10-31/final-post-commit-verification.json`; that external receipt avoids an endless self-referential commit/cleanup cycle.

The available suite previously recorded 279 passed, 18 skipped, four failures and nine collection errors; all failures/errors require unavailable Gymnasium or Hypothesis. Eleven focused tests pass after the final driver import-order cleanup, and Ruff passes for all seven changed/new Python files. Corrected wheel installation and minimal-runtime checks passed. These are copied-local-dependency checks, not a fresh resolver install or the full supported-platform matrix. Captured logs and JUnit files retain their original whitespace to preserve their recorded hashes; authored code and documentation pass whitespace checks.

Next work is the remaining solver contracts, companion integration and monograph review/modularization, followed by missing computational evidence and a full conversion/publication pass. Browser QA, complete dependencies/GUI/matrix checks, authorship/licensing, canonical remote choice and Sites publication remain outstanding.
