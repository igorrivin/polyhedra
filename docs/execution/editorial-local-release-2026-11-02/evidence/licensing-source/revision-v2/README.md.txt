# Licensing source revision v2

Only the final review-status sentence in `book/README.md` changes from the original licensing freeze. It now records source/full-edition/license-notice review outcomes while leaving browser QA and remaining release-environment checks explicitly open. All other wording, license scopes, notices, metadata and legal-text bytes remain unchanged.

`review-repair.patch` is the single-file delta from v1; `licensing-source.patch` is the complete 11-file author delta against `edef1dda04cac2f50a7c22e4240556714fac4d91`. The original freeze remains untouched. `after/` and `freeze-manifest.json` pin all 11 revised source files; `preservation-checks.json` verifies that only the one sentence differs and all 36 TeX inputs retain their licensing-v1 hashes. The original official-text verification remains applicable without modification.

No build, marker rerun, science replay, staging, commit or remote action occurred.
