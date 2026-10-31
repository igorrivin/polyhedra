# Independent callback correction follow-up

Date: 2026-10-31. Decision: **approved for the reviewed H3 service, threshold,
and result-contract scope**. The sole blocking finding in `service-review.md`
is resolved at the source hashes recorded below. The original report and
failure evidence are preserved. This approval does not cover the independent
kernel/angle reviews or establish a clean full-suite result.

## Correction reviewed

`optimize_ideal_polyhedron` now passes `deepcopy(trial)` to its callback. This
detaches the NumPy parameter array and the validation mapping recursively,
while internal history and winner selection continue to use the checked
trial. Callback signature, trial type, raw solver convergence, candidate
validity, and evaluation accounting are unchanged. Documentation accurately
limits the guarantee to the callback boundary; it does not claim that completed
result objects are immutable.

The two new regression cases exercise immediate callback mutation and mutation
through a retained earlier callback reference during a later trial. They check
parameters, vertices, fresh volumes, trial history, status, diagnostics, strict
JSON and v2 validation. The ordinary callback test now checks equal values with
distinct objects, which is the intended compatibility change rather than a
weakened numerical assertion.

## Independent replay and additional checks

I executed the original independent `service-review-probe.py` with only its two
output-filename occurrences redirected to
`service-review-callback-original-replay.json`. Its ordinary service, schema,
threshold, polish, and real-SciPy checks pass again. The original failing
callback case now gives:

| Check | Result |
|---|---|
| Reported best volume | 1.0149416064096535 |
| Recomputed volume from best parameters | 1.0149416064096535 |
| Recomputed volume from returned vertices | 1.0149416064096535 |
| Parameters reconstruct returned vertices | true |
| Callback edit changes stored cached objective | false |
| Serialized original diagnostics and verified status | retained |
| v2 schema and strict JSON | pass |

Additional independent cases overwrite callback arrays with NaN and clear the
callback validation mappings, replacing them with nested diagnostics containing
NaN/Infinity. Both immediate mutation and retained-reference mutation on a
later trial leave the real result consistent and strictly serializable. All
returned trial volumes agree with fresh evaluations of their own parameters;
the earlier better winner remains selected. The callback arrays share no memory
with internal trial arrays, and validation mappings are distinct objects.

Current production diagnostics have scalar values. To check actual recursive
isolation independently of that fact, a separate controlled constructor probe
temporarily supplied an existing nested diagnostic dictionary containing a list
and NumPy array. Editing both from the callback left the internal values at
`[3.0]` and `[4.0]`; the callback values became `[-99.0]` and `[-98.0]`. Mapping
and list identities differed and array memory was not shared. This synthetic
diagnostic is explicitly not a production v2 fixture and was not passed off as
schema-valid production data.

## Verification and provenance

- Focused suite, same four files as the original review: **64 passed in 2.29s**.
  Evidence: `service-review-callback-tests.log` and
  `service-review-callback-tests.xml`.
- Ruff on all six changed Python files: **all checks passed**.
  Evidence: `service-review-callback-ruff.log`.
- Independent original replay plus immediate, delayed, and recursively nested
  mutation checks: **passed**. Evidence:
  `service-review-callback-recheck.py`, `service-review-callback-recheck.json`,
  `service-review-callback-recheck.log`, and
  `service-review-callback-original-replay.json`.

Tests ran from `consolidated/packages/volume-toolkit` under
`/tmp/polyhedra-baseline-20261031/bin/python`, with bytecode disabled,
third-party pytest auto-loading disabled, and the isolated matplotlib cache.
The probe records resolved source import paths, dependency versions, and all
ten owned source hashes. They match the updated author manifest and remained
unchanged throughout the independent replay and follow-up.

Reviewed `optimization.py` SHA-256:
`1e9cedb1bd48e8a79356c51c336199b9134012eedf59487b6819fb491918098e`.

The following original evidence hashes were checked before and after and did
not change:

- Original reviewer script: `bb1b306f95de8bca0992f3fb30918b9d2528285ee9e4796c7564f407751df66a`.
- Original failure JSON: `e6e7e2a5a1a3ded606c7b19fc21563433ebc9944703b72f95955337fa5bdc2da`.

No implementation files, original repositories, or remote state were changed
by this reviewer. No full suite was run, as requested while the kernel and
angle follow-ups remain pending. No further blocker was found in this bounded
service follow-up.
