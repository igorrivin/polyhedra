# Polyhedra

Research software and a computational companion to *Polyhedra, Moduli, and Quantum Geometry*.

This repository integrates the volume toolkit, the historical `ipoly` study, and the supplied monograph while preserving the original Git histories and source provenance. The integration is in progress; numerical examples and mathematical claims retain the evidence limits recorded in the audit and plan.

## Contents

- [Volume toolkit](packages/volume-toolkit/README.md): existing Python package and API, tests, examples, and historical results.
- [Monograph source](book/README.md): canonical LaTeX source snapshot and figures.
- [Historical ipoly study](research/ipoly/README.md): original manuscript and verification scripts, retained unchanged.
- [Integration plan](INTEGRATION_PLAN.md): correction priorities, computational coverage and publication phases.
- [Provenance](provenance/README.md): source identities, restoration checks and path mapping.
- [Audit](audit/2026-10-31/): the evidence used to plan this integration.

## Development

Use Python 3.10 through 3.14, matching the toolkit's declared support. From the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -e 'packages/volume-toolkit[dev]'
cd packages/volume-toolkit
../../.venv/bin/python -m pytest -q
```

The minimal numerical installation is `pip install -e packages/volume-toolkit`. See the package README for optional dependencies. The installed `ideal-poly-optimize` command retains its name.

The original HF deployment and maintenance workflows remain as historical files inside the imported package. GitHub does not run workflows in that nested directory. Root workflows are deliberately configured for checks only; this repository does not currently publish a package, update HF, or deploy a Site automatically.

The text and the `ipoly` companion do not yet specify a distribution license. Preserve their attribution and resolve publication licensing before a public release. The toolkit retains its existing MIT license; see [licensing scope](LICENSES/README.md).
