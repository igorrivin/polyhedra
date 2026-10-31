# Corrected package and minimal-core verification

Date: 31 October 2026. Result: **the corrected local wheel and both Section 9 reproduction modes pass the checks below**. No consolidated implementation files, original repositories, shared baseline environment, Git staging, or commits were changed by this verifier.

The code snapshot was taken after the Section 9 author reported its corrections stable, with base Git HEAD `c53387221dc6d000ac46c0b1ce44232c50f02a3c` and uncommitted corrected sources. [The source-copy manifest](package-verification-source-copy.json) records every copied file hash and Git status. This is verification of those exact source bytes, not a clean-commit release build. Final canonical generated artifacts still need the parent’s clean-code-commit regeneration.

After the final driver import-order cleanup, both Section 9 modes were rerun successfully against driver SHA-256 `efd0f829cb8e8663b23ab23eb0dd19e3988afd1db3710d2fccaf65c3a38f28f5` and preliminary input ZIP SHA-256 `f13c1437f6ac093e85de80b7fc1a5a020c8fc1624fc9fd0c7038eae132f81f66`. All 47 package Python file hashes remained unchanged, so the wheel was not rebuilt. The linked replay commands, results, logs and summary now describe this final-driver replay; earlier records remain outside the canonical checkout under `execution/2026-10-31/package-verification-before-import-cleanup/`.

## Isolated core environment

`/tmp/polyhedra-core-verification-20261031` was created with the existing CPython 3.12.11 interpreter using `python -m venv`. System site-packages and user site-packages are disabled. Only NumPy 2.5.4, SciPy 1.18.1, and mpmath 1.3.0 were copied from the earlier isolated baseline, alongside venv’s pip 25.0.1. No editable links or `.pth` files were copied. This is a **local dependency snapshot**, not a fresh network resolver installation or cross-platform lock validation.

Before installing the wheel, the toolkit was absent. Torch, Gymnasium, Gradio, pytest, Hypothesis, pynauty, matplotlib, and networkx remain absent after installation and were not imported by the exercised core paths. `pip check` reports no broken requirements. Evidence: [environment](package-verification-environment.json), [copy manifest](package-verification-local-copies.json), and [installed-module checks](package-verification-installed.json).

## Distribution and installed behavior

The finalized toolkit was copied to `/tmp/polyhedra-corrected-build-20261031`, excluding Git metadata, AppleDouble files, caches, build output and egg-info. The existing baseline build tools ran:

```sh
/tmp/polyhedra-baseline-20261031/bin/python -m build --no-isolation \
  --outdir /tmp/polyhedra-corrected-package-artifacts-20261031
```

The wheel was installed into the separate core environment, from `/tmp`:

```sh
PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
  /tmp/polyhedra-core-verification-20261031/bin/python -m pip install \
  --no-index --no-deps \
  /tmp/polyhedra-corrected-package-artifacts-20261031/ideal_poly_volume_toolkit-0.3.0-py3-none-any.whl
```

Both distributions contain `variational.py`. All **47 package Python files** have identical SHA-256 hashes across the current source, temporary source copy, wheel, sdist and installed wheel. No Git metadata, result corpus, bytecode/cache sidecars, PEM or key files appear in the distributions. The wheel and sdist were built successfully; only the wheel was installed, so this is not a separate fresh sdist-install test. [Distribution inventories and hashes](package-verification-distributions.json) and [build log](package-verification-build.log) preserve the evidence.

| Artifact | SHA-256 |
| --- | --- |
| `ideal_poly_volume_toolkit-0.3.0-py3-none-any.whl` | `ea5345e92c96e58359df230a9da03c70afbef5ae642253fdcab53ef8181653cd` |
| `ideal_poly_volume_toolkit-0.3.0.tar.gz` | `2ef3eb1543aa01d8cf9a25e4fdc766b5c2822dc57d19e9b247e6ccff56e75c43` |

Outside-checkout imports of the package, geometry, variational, holonomy, Rivin and generic development modules resolve to the new environment’s installed files. Direct installed-wheel probes confirm that rational shear underflow does not certify, exact rational zero still certifies, cyclically rotated faces develop with the expected orientation, the near-pi scalar Hessian has positive sign, and oversized unsigned face labels raise `ValueError`.

The installed `ideal-poly-optimize` command ran the baseline tetrahedron fixture from `/tmp` with `--vertices 4 --trials 1 --maxiter 30 --popsize 8 --workers 1 --seed 42`. Its JSON validates against the optimization-result-v1 schema; volume `1.0149416063705312` and the V=4, F=4, E=6, Euler=2 structure exactly match the baseline. Schema validation used jsonschema in the separate baseline environment; jsonschema was not added to the core runtime. [CLI result](package-verification-tetrahedron.json).

## Section 9 reproduction modes

Both commands ran from `/tmp` with `PYTHONPATH` unset and outputs redirected to `/tmp/polyhedra-package-replay-final-20261031`. [Exact commands and exit codes](package-verification-replay-commands.json).

| Mode | Verified behavior |
| --- | --- |
| Repository driver with installed wheel and external fixture copy | Exit 0; installed `variational.py` and `geometry.py` are recorded as external source paths, and fixture provenance records the external path without error. |
| Extracted `section9-reproduction.zip` | Exit 0; imports use the archive’s explicit numerical subset. Module hashes equal the maintained source. Git commit and dirty state are `null`, omitted book assets are explicitly unavailable, and every bundle payload hash matches. |

Each mode passes all **12 numerical checks** plus the exact rational fixture checks: determinant 60, rooted-forest weight sum 15 with 15 nonzero forests, and Schur effective entry 15/2. The detached renderer also regenerates its HTML and another reproduction archive successfully. Numerical/exact status and bundle-integrity status were checked separately; the runner’s `all_checks_passed` field covers the mathematical checks, while provenance carries payload-integrity status. [Combined machine summary](package-verification-summary.json), [wheel-run result](package-verification-wheel-result.json), [detached-run result](package-verification-detached-result.json).

## Limits and documentation

This verification establishes the selected minimal-core installed paths and finite worked example, not optional GUI/RL/graph functionality, the supported-Python CI matrix, general realization, full mathematical proof audit, browser rendering, deployment, or an online dependency resolution. The full-suite optional-dependency failures remain documented elsewhere.

Context7 documentation used: [Python venv](https://github.com/python/cpython/blob/main/Doc/library/venv.rst) for isolation and pip bootstrapping, and [pip repeatable installs](https://pip.pypa.io/en/stable/topics/repeatable-installs/) for installing local wheels with `--no-index --no-deps`. Build commands follow the already-verified baseline workflow. Local distribution artifacts remain under `execution/2026-10-31/package-verification-artifacts/`; temporary environments and replay outputs are disposable verification material, not the canonical release artifacts.
