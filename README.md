# Polyhedra

Research software and a computational companion to *Polyhedra, Moduli, and Quantum Geometry*.

This repository integrates the volume toolkit, the historical `ipoly` study, and the supplied monograph while preserving the original Git histories and source provenance. The integration is in progress; numerical examples and mathematical claims retain the evidence limits recorded in the audit and plan.

## Contents

- [Volume toolkit](packages/volume-toolkit/README.md): existing Python package and API, tests, examples, and historical results.
- [Monograph source](book/README.md): canonical LaTeX source snapshot and figures.
- [Historical ipoly study](research/ipoly/README.md): original manuscript and verification scripts, retained unchanged.
- [Section 9 companion](site/section9/index.html): the first worked text, computation and result example; [runnable reproduction archive](site/section9/downloads/section9-reproduction.zip) and [instructions](experiments/section9/README.md).
- [Computational status](book/computational-status.md): checked examples, reported results awaiting evidence, and the next mathematical review tasks.
- [Numerical errata](book/numerical-errata.md): corrected software contracts, changed bounded examples, and the limits of those corrections.
- [Numerical-correctness checkpoint](docs/execution/numerical-correctness-2026-10-31/README.md): precision, angle-solver and optimizer-result evidence, review stages and remaining checks.
- [First integration checkpoint](docs/execution/2026-10-31/README.md): preserved baseline, initial independent reviews and recovery inventory.
- [Integration plan](INTEGRATION_PLAN.md): correction priorities, computational coverage and publication phases.
- [Provenance](provenance/README.md): source identities, restoration checks and path mapping.
- [Audit](audit/2026-10-31/): the evidence used to plan this integration.

## Development

Use Python 3.10 through 3.14, matching the toolkit's declared support. The system `python3` is currently 3.15 and is unsuitable. With an installed supported interpreter (3.12 shown), from the repository root:

```sh
python3.12 -m venv .venv
.venv/bin/python -m pip install -e 'packages/volume-toolkit[dev]'
cd packages/volume-toolkit
../../.venv/bin/python -m pytest -q
```

The commands above describe the installation procedure. [Baseline environment validation](docs/execution/2026-10-31/baseline.md) used an isolated copy of existing dependencies after PyPI DNS resolution failed; complete optional-dependency validation remains outstanding. The minimal numerical installation is `pip install -e packages/volume-toolkit`. See the package README for optional dependencies. The installed `ideal-poly-optimize` command retains its name.

For numerical work, choose an explicit [volume precision mode](packages/volume-toolkit/docs/numerical-precision.md). Legacy `fast` defaults remain finite Fourier approximations; `exact` and `eval_only` are compatibility names for numerical mpmath evaluation. Current optimizer output uses [schema v2](packages/volume-toolkit/docs/optimizer-result-contract.md), separating freshly checked candidates from the solver's convergence flag. The [Rivin angle contract](packages/volume-toolkit/docs/rivin-numerics.md) records feasibility and KKT residuals for the finite angle program. None of these numerical statuses supplies an interval proof or a general embedding certificate.

The original HF deployment and maintenance workflows remain as historical files inside the imported package. GitHub does not run workflows in that nested directory. Root workflows are deliberately configured for checks only; this repository does not currently publish a package, update HF, or deploy a Site automatically.

The text and the `ipoly` companion do not yet specify a distribution license. Preserve their attribution and resolve publication licensing before a public release. The toolkit retains its existing MIT license; see [licensing scope](LICENSES/README.md).
