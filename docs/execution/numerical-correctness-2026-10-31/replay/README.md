# Portable numerical review replays

These adapters retain the numerical computations from the original review
drivers but select an explicit repository and a new output file. They do not
contain a replacement product kernel. Original scripts and original failing
and passing outputs remain one directory above; their source hashes and the
adapter hashes are mapped in [the evidence inventory](../evidence-files.json).

Use the supported environment described in the [checkpoint](../README.md).
From the consolidated root, with dependencies installed in `.venv`:

```sh
POLY_REPO="$PWD"
POLY_PY="$POLY_REPO/.venv/bin/python"
POLY_REPLAY="$POLY_REPO/docs/execution/numerical-correctness-2026-10-31"
POLY_OUTPUT="$(mktemp -d)"
PYTHONDONTWRITEBYTECODE=1 "$POLY_PY" "$POLY_REPLAY/replay/angle-before-after.py" \
  --repo "$POLY_REPO" --output "$POLY_OUTPUT/angle-before-after.json"
PYTHONDONTWRITEBYTECODE=1 "$POLY_PY" "$POLY_REPLAY/replay/angle-independent.py" \
  --repo "$POLY_REPO" --output "$POLY_OUTPUT/angle-independent.json"
PYTHONDONTWRITEBYTECODE=1 "$POLY_PY" "$POLY_REPLAY/replay/precision-independent.py" \
  --repo "$POLY_REPO" --output "$POLY_OUTPUT/precision-independent.json"
```

- `angle-before-after.py` reads the baseline Rivin module from commit
  `285a6cb71473ba1f238983e062662cf890cbba05` without modifying it, then compares
  it with the selected current source on five cases and the 90-input LP scan.
  The Git history must contain that commit. It also checks the rational
  positive-angle witness; exact primal/dual optimality is in the independent
  driver.
- `angle-independent.py` assembles its own angle constraints, compares seven
  SLSQP solves with mpmath objectives, and verifies exact rational primal and
  dual certificates for the `1/7` fixture. It also records the current public
  reporting and actual/reported volume-call counts.
- `precision-independent.py` retains the 74-case raw-formula comparisons at
  450/1100 digits, conversion checks and precision-restoration checks. It
  returns failure when its stated finite comparison criteria fail; those
  criteria are not a uniform API error guarantee.

All three reject an existing output path. Their JSON names the actually
imported sources and hashes. The scripts' CLI help can be inspected without
running the numerical experiments.

All three adapters have completed real executions after portability review:
five before/after cases plus the 90-input scan, seven independent angle
comparisons with exact `1/7`, and 74 independent precision cases.
[Verification record](verification.json) gives the actual driver/output
hashes and preserves the two adapter-only issues caught and corrected before
these successful runs. Help and syntax checks alone were not the basis for
this execution claim.

Two original precision author drivers already accept a repository path and
explicit output and can also be run portably:

```sh
PYTHONDONTWRITEBYTECODE=1 "$POLY_PY" "$POLY_REPLAY/precision-probe.py" \
  "$POLY_REPO" --output "$POLY_OUTPUT/precision-before-after.json"
PYTHONDONTWRITEBYTECODE=1 "$POLY_PY" "$POLY_REPLAY/precision-negative-axis-probe.py" \
  "$POLY_REPO" --output "$POLY_OUTPUT/precision-negative-axis.json"
```

The second also writes `precision-negative-axis-before.json` into the chosen
output directory and verifies the preserved intermediate source snapshot's
hash. Always choose a new directory. Its comparison is a fresh replay of
that snapshot when executed; merely copying its recorded JSON is not one.

The service's executable current regression references are
`tests/test_optimizer_result_contract.py`, `tests/test_optimization.py`,
`tests/test_correctness_regressions.py` and `tests/test_data_integrity.py`.
Use the checkpoint's focused command. Its original reviewer scripts retain
machine paths and output redirection from the historical review; they are
preserved for provenance and are not used as portable launchers here.
