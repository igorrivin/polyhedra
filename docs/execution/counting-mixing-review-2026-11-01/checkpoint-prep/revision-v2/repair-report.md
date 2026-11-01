# Checkpoint preparation R1–R4 repair

This is a revised preparation freeze for targeted independent review. It is
not a source-commit authorization, a scientific replay, a PDF build/review,
or a completed canonical candidate. All edits and synthetic fixtures are
confined to `checkpoint-prep/`. No canonical file, original source repository,
Git metadata or previous evidence was changed by this task.

`before/` contains exact copies of all 13 original preparation files, including
both templates, the original handoff and original validation receipts.
`before-manifest.json` binds those copied bytes. The root-level original
templates and evidence files also retain their original identities; only the
maintained implementation files and README were updated. A separate
`replay-spec-v2.template.json` adds the mandatory unresolved list without
overwriting its predecessor. Both preparation templates remain unready.

R1 is repaired in the replay wrapper, comparison driver and native/raw
comparison path. `json_snapshot()` parses the exact bytes whose initial
SHA-256 and length it returns. The replay wrapper captures specification and
approval identities before launching its subprocess, uses only those parsed
objects, and checks the original identities before launch, after completion,
and before successful receipt completion. Result and accepted preflight
identities receive the same treatment. An unused-field mutation is rejected;
the failure receipt retains the identity actually used before execution.

The comparator captures both report identities before comparison, uses the
matching parsed snapshots and checks both identities before success. Native
reports also use one-read snapshots. Native and raw stream input identities
are retained explicitly and rechecked after their comparisons and at final
comparison/verifier receipt completion. A post-comparison change cannot be
paired with a success record or silently replace the recorded identity.
All scientific comparison exclusions remain unchanged and exact.

R2 is repaired by freezing the initial contract, candidate manifest, copy
manifest and candidate path set. Both artifact checks use those frozen parsed
objects. Their original identities are checked before artifact work and again
after all source/scientific/PDF/integrity/artifact work. The receipt records
those initial identities and paths. Replacing payloads and both manifests
with a newly consistent set is rejected, as are replaced contracts,
copy manifests and path sets.

R3 is repaired by requiring an explicit empty JSON list at `unresolved` in
both finalized contracts and replay specifications. Missing, null or nonempty
values fail even when `ready` is true. `ready: false` remains an independent
rejection. This preparation does not change either flag to authorize work.

R4 is repaired with an exclusively opened outer receipt reserved before the
audited guards. Dirty-source rejection, command failure, malformed inputs,
scientific mismatch and verification failure are retained with
`checks_passed: false`, failure stage/text, wrapper exit status and available
initial input/command details. A command that was not run has
`command_executed: false` and no fabricated subprocess return code. A command
that returned 7 retains that subprocess code while the wrapper records its
own nonzero exit status. Existing or unsafe receipt paths are refused and
never overwritten. Malformed routing data cannot establish a safe outer
destination and is rejected before reservation.

The final validation contains 45 tests in normal Python and under `python -O`,
with Ruff passing. The added regressions exercise real synthetic subprocesses,
successful controls, unused specification/approval mutation, report mutation
after the real comparison, native/raw mutation after comparison, coherent
replacement of verifier control files and payloads, source refusal before
launch, nonempty/missing unresolved lists, scientific mismatches, exact
subprocess exit codes, and no-overwrite/path-safety boundaries. The verifier
control-flow probes substitute unrelated mathematical, preservation, PDF and
approval functions because a complete real candidate is not yet being tested;
the actual Git, artifact, copy-manifest and final identity gates remain active.
`validation-final.json` contains the complete actual commands and outputs.
The first development lint failure (an unused import) and 42-test run remain
separately recorded in `validation-attempt1.json`.

Source commit `5e34f23d981631605783cbe0f74247659f12a10a` was made by another
agent during this repair, as reported by the root orchestrator. This repair
does not independently certify its in-progress integrity/sidecar closeout.
Its actual source receipts use a different schema than the original prepared
Section 15-style adapter and include an explicitly accepted five-path
`blank-at-eof` exception. Concrete curation must retain the original failed
default check, exact root exception, successful check with only that rule
disabled, staged reviewed-byte identities, and any validated sidecar backup/
recovery receipts. Do not claim the default staged whitespace check passed.
The candidate adapter must be finalized against those real receipts and
reviewed; the existing no-exception placeholder must not be filled falsely.

Final integration/PDF approval and source-commit information arriving from
other agents are not substituted into the preserved original templates.
After targeted machinery approval, the orchestrator will supply the concrete
execution specification and authorize actual clean-source replays separately.
