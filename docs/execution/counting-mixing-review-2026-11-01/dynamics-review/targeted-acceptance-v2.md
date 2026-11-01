# Targeted acceptance of dynamics metadata revision v2

Date: 2026-11-01. Decision: **accept R1–R3 and approve the revised ledger**. The analytic approval of all four unchanged chapters is preserved. This closes every required correction from the original mathematical review.

I read `revision-v2/handoff.md`, `delta-manifest.json`, `ledger-only.diff`, and the bibliography delta. I independently compared the before/after JSON trees and checked their byte hashes against the reviewed original ledger and current canonical ledger. Exactly three leaf strings changed:

- R1: `s27.tensor_first_corner` now attributes `eq:globaldiagonal` to Section 25.
- R2: the discrepancy theorem is pinned to printed p. 147, with proof p. 148 onward.
- R3: the stabilizer weight is pinned to the unnumbered display in the sketch of Theorem 1.1, printed/PDF p. 5, immediately after Theorem 1.8.

These match the independently verified source locations in the original review. The corrected outer source-pin file differs in exactly its two required pin strings and agrees with the revised embedded ledger sources. All four chapter hashes are unchanged, all 21 original author evidence files listed in the delta manifest still match their hashes, and the original reviewer artifacts remain byte-identical. Since the other ledger leaves are unchanged, all 59 claims, their hypotheses and statuses, and the 125-label coverage retain the prior approval.

The dynamics-related bibliography addition correctly cites Benirschke–Servan's 2026 erratum and says that the classical genus-two isometry used here is unchanged. This agrees with the primary erratum inspected during the original review and does not change any approved proof dependency. The McShane–Rivin v1 pin also matches the source previously inspected. I did not conduct a full audit of the other four bibliography changes or approve the whole main file by implication.

Approved revised ledger SHA256:

`8e462191ee8571f262d2c7ee9a90365a41eb526e9b1aaf4369fdb601897d506f`

`targeted-acceptance-v2.json` records the exact four chapter hashes, revised ledger hash, corrected source-pin hash, inspected delta hashes, and closed repairs. The earlier review report and manifest remain historical evidence and were not overwritten. No canonical edit, build, companion execution, commit, or upload was performed. The original external-source and conditional/open-claim limits remain in force.
