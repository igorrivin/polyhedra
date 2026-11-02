# Revision v3: explicit approved reference identity shape

Preparation only. Independent targeted review of this revision is pending; neither template is ready for real execution. The previous v2 handoff below is retained as historical preparation context, not an assertion that its pending mathematics/code reviews remain pending today.

The real independently accepted computational receipt at `computation-review/revision-v2/final-acceptance.json` has an `/accepted_author_result` record with exactly `path`, `sha256`, and `bytes`. Revision v3 adds one explicit `reference_identity_shape: path-record` adapter. It verifies that the approved path is a canonical safe relative path under OUTER and is the same declared reference path; only then does it project the two identity fields. The original default `identity` shape still requires exactly `sha256` and `bytes`. Missing/extra keys, unsafe/mismatched paths, invalid hashes, noninteger or negative byte counts, and undeclared shapes fail. The approval itself is never rewritten.

See `ADAPTER.md`, `revision.patch`, `revision-delta.json`, and `freeze-manifest.json` for the actual v2-to-v3 delta, verification, and immutable identities. Earlier v2 files and its independent acceptance remain untouched. Final integration/PDF approval, source commit, concrete schema binding, clean-source replay, curation/candidate review and artifact commit remain separate future stages.

---

# Prepared final-chapter checkpoint tools, revision v2

This directory is **preparatory author work**, awaiting independent review. Both JSON templates have `ready: false` and explicit unresolved dependencies. They cannot authorize a clean-source replay or claim a completed checkpoint. No canonical source, artifact, index, commit, remote, or actual PDF was changed by this preparation. No monograph computation was run.

Revision v2 repairs independent findings **CR01** and **CR02**. The initial preparation and independent review remain unchanged in their original directories. `revision.patch` records the exact file deltas; the revision freeze binds those originals and the new evidence. This is an author repair, pending targeted independent recheck.

The implementation adapts the frozen-input and failure-receipt patterns from `consolidated/docs/execution/counting-mixing-review-2026-11-01/`. Torus execution, native binaries, raw streams, historical whitespace exceptions, and fixed earlier receipt identities are omitted. The new tools support only the finite `quantum_geodesics` companion.

| Tool | Purpose and boundary |
| --- | --- |
| `checkpoint_lib.py` | Strict JSON with rejection of lossy decimal tokens, safe paths, exclusive receipts, the shared active TeX graph walker, approval/input snapshots, and individually checked report metadata. |
| `run_clean_replay.py` | Execute the approved companion once into a new outer file. Require the final source commit, empty Git status, and unchanged reviewed/runtime/manuscript inputs before and after. |
| `compare_replays.py` | Compare the accepted author report with the new clean-source report. This performs no numerical computation. |
| `verify_checkpoint.py` | Read-only candidate or artifact-commit verification: ancestry, source/approval/run identities, original preservation, exact PDF copy, manuscript labels, and candidate/copy inventories. |
| `test_checkpoint.py` | Explicitly synthetic gate tests, including temporary repositories and subprocesses. They do not test the monograph mathematics. |

The scripts are specific to baseline `151673b1817e66aae493eb7da1be5ddf49adfe0f`, its original research workspace, and a separate later artifact commit. They are not a portable replacement for the companion's own reproduction command. Complete checkpoint verification additionally uses retained outer evidence and the unchanged original repositories and source ZIP.

## Binding the real evidence

After final independent computation and integration approval, copy `replay-spec.unready.json` to a new real specification and fill its fields from the retained receipts. The proposed paths and JSON pointers are interfaces to be reconciled with the actual original records; do not rewrite those records to fit a template. Preserve the unready templates and this initial preparation.

The integration approval must bind the exact final source hash map. The computation approval must bind the exact runtime hash map, accepted author-result identity, author-stage manuscript observation hashes, broader 46-file TeX observation hashes, and **all fourteen exact group names**. Mapping, path-record-list, and path-record-mapping hash representations are supported where declared. The four-group quantum author result is deliberately insufficient.

Bind the source commit only after it actually exists as the baseline's direct child. Fill the 36 active TeX hashes, complete runtime map, observed manuscript hashes, all 46 broader TeX observation hashes, and their conflict-free union. The accepted author report must record the same complete source state before and after its run; its actual precommit dirty state is retained. Keep that final author-run window free of concurrent canonical changes. The clean replay must record the source commit with empty status in both observations. If an actual final report or review uses a different schema, make a small reviewed adaptation rather than weakening these predicates.

Before launch, one shared graph walker recursively expands `book/main.tex` from both the source commit and current files and requires both exact path/hash maps to equal the declared 36-entry map. Counting files is insufficient. Missing entry points, omitted active inputs, unrelated filler paths, repeated/cyclic inputs, absolute/traversing paths, and unsupported input syntax fail before the command. The walker supports this book's literal braced `\input{...}` syntax, ignores TeX comments, and rejects unsupported input/include forms; it is not a general TeX interpreter. The later manuscript verifier imports this same function.

`allowed_manuscript_changes` is exactly the set whose observed hashes differ between the approved author snapshot and the final integration snapshot. Each must be an independently approved source path. The accepted mathematical source pins remain fixed in the fixture and both report observations. No runtime file, dependency, fixture, precision, software version, formula, group, count, or unknown scientific field is discarded during comparison.

The full companion also records `live_tex_source_observations`: 46 sorted path/hash rows. These comprise the 36 active inputs and ten preserved inactive figure fragments/preamble files; the active graph still has 36 inputs. `reference_tex_observation_sha256` and `tex_observation_sha256` bind the two stages. `allowed_tex_observation_changes` must equal the actually changed paths and contain only independently approved active source paths. All ten inactive hashes remain fixed. Every observed file is guarded against current and committed bytes, and the only additional comparison exceptions are the individual changed `/live_tex_source_observations/i/sha256` fields. No whole array is excluded.

The comparison can exclude only **actually differing** UTC generation time, elapsed time, Git commit/dirty/status fields, the current-hash/match fields for enumerated manuscript observations, and the individual broader-TeX hash fields just described. Each excluded value is retained in the receipt and checked against its stage. Missing locations, duplicate exclusions, overlapping exclusions, stale inputs, unknown scientific changes, and altered runtime identities fail.

CR01 is addressed with a narrow decimal round-trip policy. A JSON fractional/exponent token is accepted only if it is finite and `Decimal(original_token) == Decimal(str(parsed_float))`. Arbitrary decimal tokens outside this lossless serialization subset are **rejected**; this is not arbitrary-precision numeric parsing or a claim that binary64 represents every accepted decimal exactly. Ordinary Python-generated timing values survive unchanged. Tokens such as `1e-999`, `1.0000000000000001`, and `9007199254740993.0` fail explicitly instead of collapsing to another number. Integer/float, boolean/integer, string/number, large integer, and tiny-positive-string distinctions remain intact. Success and failure receipts remain ordinary strict JSON, including valid tiny timing values.

Set `ready: true` and `unresolved: []` only once all real bindings are complete and independently reviewed. Reserve new receipt paths. Typical commands from this directory are:

```sh
/tmp/polyhedra-baseline-20261031/bin/python -B run_clean_replay.py --spec /absolute/outer/clean-source/replay-spec.json --receipt /absolute/outer/clean-source/run-command.json
/tmp/polyhedra-baseline-20261031/bin/python -B compare_replays.py --spec /absolute/outer/clean-source/replay-spec.json --receipt /absolute/outer/clean-source/scientific-comparison.json
```

These tools do not stage or commit source, copy the result into canonical artifacts, or run existing historical campaigns. Once a safe exclusive receipt is opened, a failed guard or command leaves a failed receipt with the original input identities and actual command status. Existing results and receipts are never overwritten.

## Candidate curation and later verification

Only after the clean replay and comparison pass should the separate candidate be curated. Bind `checkpoint-contract.unready.json` to the six original independent approval roles, actual source-commit receipt, original replay specification, actual command/comparison receipts, and reviewed PDF evidence. Keep the actual replay specification outside canonical and copy its exact bytes; `replay_spec.outer_source` identifies that original.

The PDF is the exact independently reviewed **precommit** build, copied byte-for-byte. Its input freeze must equal all 36 committed TeX inputs. Its build and visual receipts must name that same PDF. The proposed receipt predicates require the real successful build, converged references/labels, and actual visual approval; hashes alone are not a visual review. Marker execution, rendering, page inspection, and any subsequent typesetting corrections belong to the PDF/integration phase and were not performed here.

The candidate manifest excludes its own hash. The evidence-copy manifest maps every other payload, except itself, to exact retained outer bytes and records omissions. Approval of the candidate and postcommit receipts stay outside that candidate, avoiding circular identities. Candidate verification requires source HEAD, unchanged tracked files, an empty index, and exactly the declared untracked artifact paths. Postcommit verification instead requires a clean direct child that adds exactly those paths, with mode `100644`.

The preservation gate checks 2,273 baseline Git entries, unchanged protected materialized bytes, all 412 LFS payloads, the two original repository HEADs and 953 files, and the original ZIP. The manuscript gate requires all original 607 labels in order plus exactly the six declared anchors, 613 unique labels, 129 unchanged bibliography keys, and the three final ledgers with 186 claims. The source commit must pass default whitespace checks; no earlier whitespace exception is imported. Git integrity is read-only: any new failure stops verification, and no sidecar is removed by these tools.

Independent integration/link checks, full rendered-page coverage, historical-suite status, editorial consistency, publication metadata/licensing, and final upload are separate tasks. This verifier does not claim to perform them.

## Verification of this preparation

`verification-v2-final/` retains the final normal/optimized unit-test and Ruff commands, outputs, and exit statuses. The earlier successful 49-test repair stage remains in `verification-v2/`; the final stage adds a scalar-type regression for source-state metadata. The new regressions exercise all three lossy-number pairs through the full comparison CLI and failure-receipt serialization in both directions, ordinary decimal/timing success, the shared connected-input positive fixture, rejected prelaunch graph defects, and immutable inactive TeX observations. Source-state equality uses the same type-preserving canonical encoding, so bool/int or int/float changes cannot hide inside metadata exclusions. The retained fixtures test scientific-field retention, exact group binding, stage-specific manuscript changes, strict JSON, protected outputs, dirty source, command failures, input drift, and consistent replacement of candidate payloads/control manifests. Temporary Git repositories, approval records, report values, and non-PDF byte fixtures are explicitly synthetic. The candidate tests mock the original-source, mathematical/PDF, and Git-integrity audits; passing them is not an audit of the real final candidate. The initial 29-test preparation evidence remains in the parent directory's `verification-v1/`.

The next gate is independent review of these prepared tools and their tests. Final schema binding, final numerical replay, curation, source/artifact commits, and postcommit verification remain unresolved.
