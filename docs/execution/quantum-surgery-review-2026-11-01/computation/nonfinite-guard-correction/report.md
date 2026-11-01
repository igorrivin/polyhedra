# Nonfinite numerical guard correction

The independent reviewer reproduced a false pass: at 50 digits, comparing actual matrix [1, NaN] with expected [1, 0] recorded residual 0.0 because Python max ignored the later NaN magnitude. The author independently reproduced that exact failure before the edit.

Only periods.py and tests/test_quantum_surgery.py changed. norm now rejects every nonfinite scalar or matrix entry before taking magnitudes or a maximum. NumericChecks.close validates actual and expected separately, and validates the difference before scaling. The existing guard test now covers scalar inputs and first/middle/last matrix positions on both sides, real NaN and positive/negative infinity, complex nonfinite values, and nonfinite subtraction of finite native scalars. A failed guard never records a successful residual.

All 15 focused tests and Ruff pass. A new author replay from /private/tmp records the actual dirty tree and passes the same 192 exact identities, 300 numerical checks at 60/90 digits and 72 precision comparisons. All scientific result sections, including observables and residual strings, are identical to the original author result. No numerical formula, precision, fixture, tolerance or declared scope changed.

The initial computation/source-manifest.json and shared-docs/source-20-path-manifest.json remain untouched. The correction receipt in final-source-manifest.json records both changed files' before/after hashes, the new replay identity and checks. The new source-20-path-manifest.json records every original hash and current hash; only the two authorized files differ. No README or shared-document count changed, because the test method count remains 15.

No manuscript edits, PDF builds, commits, historical artifact changes or remote actions were performed. Independent targeted recheck is a separate reviewer step.
