# Targeted CV01 acceptance

Decision: **CV01 resolved; approve the exact revision-v3 Section 32, Appendix B and claim ledger.** No required findings remain in this conventions review.

The new Q1 paragraph correctly points to Section 4's positive-boundary Zonneveld extension and Theorem 3. It retains the selected pair `L1<L2`, full-measure tree/double-tree cells, and equal-length volume values by continuity. It does not assert a cell bijection at equality or identify these cells with hyperideal angle cells. The direct hyperideal integration question remains open.

The `s32.q01` dependency still points to the earlier bundled `s4.tree_density` claim, but its new usage field explicitly selects that claim's Zonneveld evidence and review limit rather than its BMZ origin-cusp hypotheses. The new source pointer resolves to the existing `sources/Zonneveld` record and its Theorem 3 locator. The added citation uses an existing bibliography key.

`recheck_cv01.py` independently verifies exactly one source-paragraph replacement and exactly the seven declared JSON paths. Appendix B is byte-identical; the other 65 claims, all statuses, computational support, quantum acceptance, geodesic pending snapshot and historical metadata are unchanged. All 98 earlier pin occurrences were rechecked, with only the authorized current subject hashes substituted. The 32-file preservation inventory and the original independent review manifest remain intact. The graph still contains 36 files, 613 unique labels and 129 bibliography keys; both owned labels and all 15 question titles/order are preserved.

Accepted author freeze: `839ad986f3162e849c362c3c43c666913fd601fbfea55d9264c41a3b5d1affe4`.

| File | Accepted SHA-256 |
| --- | --- |
| `book/chapters/32-open-questions.tex` | `50fc264bbfc55fc19cb79dc09aa7a828b2cba479f6b3afb1c62459e0d31c9b5d` |
| `book/chapters/appendix-b-conventions.tex` | `b57a96b3f141e0d372b26dbb710d1ec0fa8e8a4a8ac8f0dd04b4ce0432f99a74` |
| `book/claims/section32-appendixb.json` | `488298ff34c229222010d03452f18e4f3855b9c7026589c74a28fbece04f3a9e` |

The unchanged 65-claim review and its source-access limits are inherited from `../review-report.md` and `../claim-coverage.json`, bound by the preserved `../review-manifest.json`. This accepts all 66 claims within the conventions review's scope, not the pending geodesic mathematical review or any companion implementation/result. The frozen handoff's 14 planned groups and later review/result upgrades remain integration work. No numerical replay, complete external-proof audit, canonical edit, build/PDF marker, installation, stage, commit or upload occurred.
