# Targeted dependency reconciliation, revision v2

Status: author reconciliation complete; ready for independent conventions review. The initial author freeze and every evidence file named by it remain unchanged. This revision edits only `book/claims/section32-appendixb.json`. Both chapter files are byte-identical to the initial conventions freeze.

## Comparison with the finalized author tracks

The two quantum chapters are unchanged. The quantum ledger changed only through QR01: two missing dependency hashes were inserted. The author revision-v2 freeze has SHA-256 `f043f6943bd124638802bfdb5d5e7505269143f54046eea93d298345191c0620`; the ledger is `34dbb6255dc468cb796bb3a129eeaf37ac0c5f4dc358abfd73030e64331b3539`. The independent `quantum-review/final-acceptance.json` is pinned at SHA-256 `c631f5ed63513246adf7bbec958c3298ab577861ee02f1d359ff6ca25b7c4dd9` and accepts exactly these three source hashes with no required open findings. Its selected-statement/source-access and computational limits remain explicit.

Every finalized geodesic chapter equals the previously observed chapter after removing exactly one EOF blank line. This was checked by reconstructing the old SHA-256 from the final bytes plus one newline. There is no semantic chapter change to reconcile. The final author freeze is `38994ff43e952ff42ccafb4d56c44e51c385a0092d156e3d35cdbcf1041d7eec`, and the newly available 59-claim ledger is `aca716a9b08128e7c6feefb79693ff9313139dbc52c0b33ce7e395d6fce80d54`.

The finalized geodesic convention dictionary agrees with Appendix B: positive geometric traces remain distinct from signed character traces; the punctured torus retains two N labels and one H label; twist is signed displacement; common cuff orientation and tangential momentum are preserved; signed cusp truncation uses lambda=exp(d/2) without sqrt(2); the cusp gap scope excludes geodesic boundary; and Basmajian uses the full boundary orthospectrum with the stated orientation factor. The source hypotheses remain attached to the referenced formulas. No chapter prose change is necessary.

Independent geodesic mathematical review remains **pending**. Neither the author freeze, the 59-claim ledger, nor its finite author scratch checks are relabeled as an independent approval.

## Exact metadata delta

The ledger now binds the accepted quantum source/ledger snapshot and the final geodesic author source/ledger snapshot. It adds 23 precise dependency pointers, including unlabelled claims for the leading Chen–Murakami theorem, punctured-torus multiplicity, cuff generating functions, cusp exceptional directions and decoration invariance. Existing claim statements and statuses are retained. Per-claim review-state fields distinguish accepted quantum dependencies from geodesic author dependencies awaiting review.

Both planned companion contract pins are refreshed. The geodesic contract includes the explicit signed cusp fixture H=20,t=3, stable tiny-positive tail evaluations, and guard precision at a=1e-12. All four quantum groups and ten geodesic groups remain `planned_contract_only`; no maintained implementation or execution is asserted. The seven earlier result pins and their finite-evidence boundaries are unchanged.

The JSON delta changes only dependency/review/provenance metadata: `author_review`, dependency fields within `claims`, planned contract metadata in `computational_support_map`, `current_author_dependencies`, `external_source_policy`, `pending_dependencies`, and the new `dependency_reconciliation` record. `metadata-delta.json` lists every changed JSON path. `ledger-only.patch` is the zero-context text delta. The three owned files are saved in both `before/` and `after/`.

## Validation and remaining work

The source graph is expanded from **book/main.tex**, including the wrapper and canonical manuscript. It has **36 files**, **129 bibliography keys**, and **613 unique labels**: the original **607** in their original order plus the six separately recorded geodesic additions. This author still adds no labels. The fifteen question titles/order, 43 convention rows, 66 claims, both chapter hashes, all prior review/result pins, and all fourteen planned groups are preserved.

The static source/reference/hash checks pass with no current dependency drift. Actual owned-file whitespace and one final newline are checked; the separate revision validation checks the new evidence files as well. Initial evidence preservation is rechecked against the original freeze, rather than inferred from a directory name.

Independent conventions review, independent geodesic review and any resulting reconciliation, maintained companion implementation/review, final evidence curation and rendered layout checks remain separate. No build, numerical replay, installation, staging, commit or remote action occurred in this revision.
