# Independent actual-schema adapter review

Decision: **approve the revision-v3 preparation code**. No required findings remain in this narrow adapter review. Final source, PDF and replay bindings remain pending.

The new explicitly declared `path-record` shape requires exactly `path`, `sha256` and `bytes`. It validates the canonical relative approved path and its equality to the declared OUTER reference before projecting the two identity fields. The default `identity` shape retains its exact two-key contract. Missing or extra keys, Boolean/floating/negative byte counts, malformed hashes, unknown shapes, traversal, sidecar paths, symlink escape and mismatched paths reject. Same bytes at a different path do not substitute for the approved reference. The original approval object and file are not rewritten.

Nine selected tests passed normally and under `-O`, including all five added tests, the old default two-key command path, input drift, comparison failure receipts and disconnected-graph rejection. Fifty-seven independent controls per mode also passed, and Ruff passed. The exact delta adds one adapter and changes its single `approved_spec` callsite; 31 other library functions, all 50 earlier test bodies, the three entry-point files and checkpoint contract remain unchanged. Their accepted v2 numeric, graph, source and comparison review is reused by identity.

The actual computational acceptance `70070fe32c42961d68b035ccb7fae5b012c50ac5814ca42bd05689bfc64b6592` projects to the unchanged approved author result `5f73fce03e43103dc457570bcd90f4722599b5ac0d67a9b9b88d9e00679f0429`. Strict parsing and the already approved author-stage metadata schema pass. This was read-only compatibility checking; no live manuscript hashes were read or declared final.

All 22 revision-v3 payloads and 75 v2 author/reviewer payloads remain unchanged after review. The earlier failed findings and subsequent acceptances remain intact. Both templates remain explicitly unready; their illustrative pointers must still be bound to the real final receipts. No real numerical replay, PDF operation, canonical edit, source/artifact commit or upload occurred.
