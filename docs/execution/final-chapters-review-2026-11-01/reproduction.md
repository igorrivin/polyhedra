# Reproduction and evidence boundaries

The source commit is `8f722ae462307146818932cde4811e4bb4e8423e`. The [companion README](../../../experiments/quantum_geodesics/README.md) defines the finite groups, formulas, conventions, dependencies and limits. The [clean-source report](../../../artifacts/quantum_geodesics/result.json) records its actual software versions and requested/guarded precision. Numerical agreement is not an interval error certificate.

From a clean checkout of that source commit, the direct companion entry point is:

```text
python -B experiments/quantum_geodesics/run.py --output /absolute/path/to/a/new-result.json
```

Use the recorded environment and a new output path. A later reproduction is a new operation and must retain its own source state, result and receipts. Do not overwrite the original author or clean-source reports.

The historical guarded run used the approved v3 tools and the exact [replay specification](clean-source/replay-spec.json). Its actual command is in the [run receipt](clean-source/run-command.json). The subsequent [comparison](clean-source/scientific-comparison.json) kept every field except 68 precisely enumerated timing and verified stage-provenance pointers. Both operations checked frozen approvals, the complete runtime, active input graph and broader source observations. A partial four-group report or renamed group is rejected. Lossy fractional JSON tokens are rejected before comparison rather than silently rounded.

The reusable entry points are `run_clean_replay.py --spec SPEC --receipt NEW_RECEIPT`, `compare_replays.py --spec SPEC --receipt NEW_RECEIPT`, and `verify_checkpoint.py --root ROOT --outer OUTER --candidate --receipt NEW_RECEIPT`. The retained spec deliberately identifies the original absolute checkout/evidence locations and an already completed output. Any later guarded replay therefore needs a separate, explicitly rebound specification and independently reviewed stage bindings; keep the original spec unchanged. Failure receipts must be preserved, and no success may be inferred from an attempted command.

The [source checkpoint receipt](source-checkpoint/source-checkpoint.json) records the exact 40-path commit. Its historical commit script is evidence, not a command to rerun against this artifact tree. The final PDF was built and reviewed **before** that commit; all 36 active TeX hashes were then matched to committed bytes. The [input freeze](integration-review/tex-input-freeze.json), [build record](integration-review/pdf-build-receipt.json), raw recorder/aux/log evidence and [visual review](integration-review/visual-review.json) retain that provenance. No PDF rebuild was performed during replay or curation.

The [independent oracle script](computation-review/independent_oracles.py) reads `computation-review/subject-v1/author-result-70-110.json`. Exactly one v1 report is retained for that purpose. To rerun the oracle, copy the script and its input into a fresh scratch layout preserving their relative paths, use the recorded dependency versions, and keep its new output separate. The retained oracle covers 400 exact and 1,322 numerical alternate checks. The final computational review reused those results because the mathematical modules, fixture and scientific strings were unchanged; it did not freshly rerun the oracle.

The structural extraction is recoverable from the baseline commit plus the retained manuscript-body and ten new chapter snapshots. The other 25 active inputs, including `book/main.tex`, were unchanged baseline files. Historical author/reviewer scripts may hardcode their stage layout or require a prior source snapshot; run them only in an isolated restoration. Accepted mathematical snapshots and correction diffs are retained separately from later integration prose/layout/ledger changes.

For the synthetic checkpoint gate suite, copy the matching tool directory and unready templates to a scratch directory and run `python -B -m unittest -v test_checkpoint`, then `python -B -O -m unittest -v test_checkpoint`. These temporary Git/report fixtures are not scientific results. The [retention policy](evidence-retention.md) explains omitted duplicates and renamed raw evidence. Candidate/copy manifests have no self-hash cycle; independent candidate and postcommit receipts stay outside the payload.
