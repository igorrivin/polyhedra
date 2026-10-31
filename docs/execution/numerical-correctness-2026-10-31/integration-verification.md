# Numerical correctness: integrated verification

The current H³ corrections pass the available numerical, packaging, and reproduction checks below. The full test suite remains blocked by the same missing optional dependencies as the preceding checkpoint. No implementation, original repository, canonical Section 9 artifact, staging area, or commit was changed by this verifier.

## Combined tests and research-data integrity

The full suite ran once from the maintained package under the existing isolated CPython 3.12.11 baseline environment. Resolved imports point at the current checkout, not that environment's older installed wheel. The result is **393 passed, 18 skipped, 4 failed, 9 collection errors, zero warnings**, in 35.44 seconds. The previous checkpoint recorded 279 passed, the same 18 skips, 4 failures and 9 collection errors, and two quadrature warnings.

The JUnit comparison confirms identical failure, collection-error, and skip node IDs. The failures/errors still concern missing Gymnasium or Hypothesis; the skips concern unavailable pynauty. There are 114 additional passing cases, and the earlier quadrature warnings are absent. This is not a clean full-suite pass. See [comparison](integration-full-suite-comparison.json), [current JUnit](integration-full-tests.xml), [test log](integration-full-tests.log), and [source import verification](integration-source-imports.json).

Ruff passes on every changed/new maintained Python file; `git diff --check` passes. The materialized data-integrity command verifies **412 LFS paths**, parses 354 LFS JSON payloads, checks both canonical input hashes and both result-manifest artifacts, and verifies ordinary-Git exceptions, including both optimizer schemas and the historical v1 fixture. These are data/schema checks, not fresh numerical replays of the research corpus. See [Ruff command](integration-ruff.json), [Ruff log](integration-ruff.log), and [data-integrity log](integration-data-integrity.log).

## New distribution and isolated installed core

The package was copied to `/tmp/polyhedra-numerical-build-20261031`, excluding Git metadata, AppleDouble files, bytecode, caches, old build outputs and egg-info. The copy contains 936 files and 76,722,683 bytes. The existing baseline build tool produced a wheel and sdist with `python -m build --no-isolation`; the build did not write package metadata into the checkout. [Source-copy manifest](integration-source-copy.json).

The fresh `/tmp/polyhedra-numerical-core-20261031` environment has system and user site-packages disabled. Only NumPy 2.5.4, SciPy 1.18.1, and mpmath 1.3.0 were copied from the existing local dependency snapshot; venv supplied pip 25.0.1. Before installation, the toolkit and optional libraries were absent. The new local wheel was installed with `--no-index --no-deps` from `/tmp`; `pip check` passes. This is a locally copied dependency environment, not a fresh online resolution or portable lockfile validation. [Environment before install](integration-core-environment-before.json), [dependency-copy hashes](integration-dependency-copies.json), [install log](integration-install.log), and [pip check](integration-pip-check.log).

All **47 package Python files** have matching SHA-256 hashes in the live source, temporary copy, wheel, sdist and installed wheel. They remained unchanged through the end of verification. Distribution inventories contain no AppleDouble, Git, bytecode/cache, result/research payload, or PEM/key files. The sdist was built and inspected; it was not separately installed. The package retains its existing version 0.3.0; this is a checked local build, not a published versioned release. [Distribution inventory](integration-distributions.json), [build log](integration-build.log), and [final source hashes](integration-source-hashes-final.json).

| Distribution | SHA-256 |
| --- | --- |
| `ideal_poly_volume_toolkit-0.3.0-py3-none-any.whl` | `4c3d2531a3f345b893e467bc5c4af726be672f858e8a2a84894e93f23e559333` |
| `ideal_poly_volume_toolkit-0.3.0.tar.gz` | `9fab55fc7a84a684d43099717a720f85994b0445a87ae5ccd53afa63ac34eb95` |

Copies of both distributions remain outside the checkout at the original outer-workspace path `execution/numerical-correctness-2026-10-31/integration-artifacts/`. The binaries are omitted from this canonical evidence copy; their hashes are recorded above. They are not clean-source release artifacts.

## Installed numerical behavior

The [standalone installed probe](integration-installed-probes.py) never adds a checkout path. All exercised modules resolve to the new environment's site-packages, and Torch, Gymnasium, Gradio, pytest, Hypothesis, pynauty, matplotlib, and networkx remain absent.

- MP120 accepts a rational angle `1e-400` without underflow. The negative-axis value and local triangle at `-1+i*1e-300` agree with the unreduced 450-digit dilogarithm definition to better than `1e-115` relative discrepancy. The binary64 kernel returns a finite, positive value for `1e308+i*1e308`, consistent with that independent high-precision definition. Scoped precision restores on normal completion and error.
- The angle optimizer returns the accurate regular ideal-tetrahedron volume `1.0149416064096535`, with feasible residuals and passing numerical KKT audit. The eight-face strict LP returns common normalized margin `1/7`. A nonstationary zero-budget start remains unsuccessful.
- A controlled solver return with cached volume 100 and `success=False` is freshly evaluated to the regular-tetrahedron volume. The candidate remains valid while raw convergence stays false. A callback that overwrites its parameter array with NaNs and clears its diagnostics cannot corrupt the stored result. This deliberately synthetic cached-objective probe is not a claim about ordinary SciPy behavior.
- A real small SciPy run retains its valid candidate and unsuccessful raw convergence separately. The earlier rational-underflow arithmeticity, exact-zero certificate, cyclic face-development, and near-pi Hessian-sign corrections still pass through the installed wheel.

See [installed probe results](integration-installed-probes.json). The first verifier script mistakenly read an LP field named `residuals`; it was corrected to the existing `primal_residuals` contract. The initial KeyError is retained in [the harness log](integration-installed-probes-harness-before.log). No product correction was needed.

The installed CLI ran with `--vertices 4 --trials 1 --maxiter 30 --popsize 8 --workers 1 --seed 42`, producing volume `1.0149416063712777`, one valid trial, and one separately counted verification evaluation. Both its v2 payload and the controlled v2 payload validate with jsonschema in the separate baseline environment and serialize with strict JSON. The historical v1 fixture also validates and is byte-identical to the initial `tetrahedron-cli.json`; the v1 schema is unchanged from HEAD. See [CLI output](integration-installed-cli-v2.json), [CLI log](integration-installed-cli.log), and [schema evidence](integration-json-schemas.json).

## Section 9 reproduction

From `/tmp` with `PYTHONPATH` unset, the repository driver used the newly installed wheel and an external copy of the unchanged fixture. Its newly generated reproduction ZIP was then extracted and rerun with the same minimal environment. Both modes pass all **12 numerical checks** and the exact rational fixture: determinant 60, grounded determinant and rooted-forest sum 15, 15 nonzero forests, and Schur entry 15/2.

The installed mode records site-packages paths and the new geometry hash. The detached mode uses its explicit numerical subset; all nine payload hashes match, with the same current geometry bytes. It correctly records no live Git commit/dirty state, and marks omitted book assets unavailable. The preliminary ZIP has SHA-256 `237d23bfecf0537e58d371a9b335cb47d14925de3a49a985e4def33b469f970a`.

These are preliminary verification outputs: their origin truthfully records the working checkout as dirty at HEAD `285a6cb71473ba1f238983e062662cf890cbba05`. The tracked canonical Section 9 outputs remain historical until the commit worker regenerates them from the next clean source commit. [Replay summary](integration-section9-replays.json), [installed result](integration-section9-wheel-result.json), [detached result](integration-section9-detached-result.json), and [exact commands](integration-commands.json).

## Commit-worker handoff

After the verified source, tests and documentation are committed, confirm `git status --porcelain` is empty. From the consolidated root, regenerate the canonical outputs with:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=packages/volume-toolkit \
  /tmp/polyhedra-baseline-20261031/bin/python experiments/section9/run.py
```

Before the separate artifact commit, inspect `artifacts/section9/result.json`: `all_checks_passed` must be true, all 12 check entries and the exact fixture must pass, `provenance.source_commit` must equal the clean source commit, `repository_dirty_at_start` must be false, and its initial status list must be empty. Compare every available source/book hash against actual bytes. Check the generated ZIP's nine payload hashes, and ensure its geometry hash matches `integration-source-hashes-final.json`.

Extract that **final canonical ZIP** into a new temporary directory. From `/tmp`, run its absolute `experiments/section9/run.py` path with `env -u PYTHONPATH PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-numerical-core-20261031/bin/python`, directing `--output` and `--site-dir` to new temporary paths. Assert all mathematical checks, `bundle_payload_hashes_match=true`, null live Git state, and a `bundle_origin` that names the clean source commit with `repository_dirty_at_start=false`. Do not reuse the preliminary dirty-origin result as evidence for the final ZIP. Preserve that final result and hashes in the closeout evidence.

This verification does not establish a whole-book proof audit, general realization or global-optimality certificate, optional GUI/RL/accelerator behavior, the supported-Python matrix, browser rendering, publication, deployment, or a remote push. Current documentation used: [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/) and [Python venv](https://github.com/python/cpython/blob/main/Doc/library/venv.rst), fetched through Context7. The build command follows the already checked repository workflow.
