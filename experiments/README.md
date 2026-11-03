# Computational companion guide

Run from the repository root after the [core installation](../README.md#quick-start). Python 3.10-3.14 is supported by the toolkit; the published calculations record their own actual versions and working precisions. Use a Git clone for provenance-aware replay.

Create a directory outside the repository and use a fresh filename for each run:

```sh
mkdir -p /tmp/polyhedra-run
```

| Monograph | Recipe and code | Recorded result |
| --- | --- | --- |
| Sections 1-8 and Appendix A | [Recipe](normalizations/README.md) · [Entry point](normalizations/run.py) | [JSON](../artifacts/normalizations/result.json) |
| Section 9: Hessians and barriers | [Recipe](section9/README.md) · [Entry point](section9/run.py) | [JSON](../artifacts/section9/result.json) |
| Sections 10-11, 17-22, 32 and Appendix B | [Recipe](quantum_geodesics/README.md) · [Entry point](quantum_geodesics/run.py) | [JSON](../artifacts/quantum_geodesics/result.json) |
| Sections 12-14 and 16 | [Recipe](quantum_surgery/README.md) · [Entry point](quantum_surgery/run.py) | [JSON](../artifacts/quantum_surgery/result.json) |
| Section 15: finite Airy checks | [Recipe](section15/README.md) · [Entry point](section15/check.py) | [JSON](../artifacts/section15/checks.json) |
| Section 15: exact-integrand quadrature | [Recipe](section15_quantum/README.md) · [Entry point](section15_quantum/check.py) | [JSON](../artifacts/section15_quantum/result.json) |
| Sections 23-31: finite formulas | [Recipe](counting_mixing/README.md) · [Entry point](counting_mixing/run.py) | [JSON](../artifacts/counting_mixing/result.json) |
| Section 30: bounded diagnostic | [Recipe](section30/README.md) · [Entry point](section30/run.py) | [JSON](../artifacts/section30/result.json) |
| Sections 30-31: full torus campaign | [Recipe](torus_campaign/README.md) · [Entry point](torus_campaign/run.py) | [JSON](../artifacts/torus_campaign/result.json) |

## Example invocations

These commands write new observations. They do not replace the committed historical results. The Section 15 smoke run and cutoff-64 torus run are bounded examples; their READMEs describe the larger published settings and preflights.

### Sections 1-8 and Appendix A

```sh
python experiments/normalizations/run.py --output /tmp/polyhedra-run/normalizations.json
```

### Section 9: Hessians and barriers

```sh
python experiments/section9/run.py --output /tmp/polyhedra-run/section9.json --site-dir /tmp/polyhedra-run/section9-site
```

### Sections 10-11, 17-22, 32 and Appendix B

```sh
python experiments/quantum_geodesics/run.py --output /tmp/polyhedra-run/quantum-geodesics.json
```

### Sections 12-14 and 16

```sh
python experiments/quantum_surgery/run.py --output /tmp/polyhedra-run/quantum-surgery.json
```

### Section 15: finite Airy checks

```sh
python experiments/section15/check.py --output /tmp/polyhedra-run/airy-finite.json
```

### Section 15: exact-integrand quadrature

```sh
python experiments/section15_quantum/check.py --profile smoke --output /tmp/polyhedra-run/quantum-smoke.json
```

### Sections 23-31: finite formulas

```sh
python experiments/counting_mixing/run.py --output /tmp/polyhedra-run/counting-mixing.json
```

### Section 30: bounded diagnostic

```sh
python experiments/section30/run.py --output /tmp/polyhedra-run/torus-bounded.json
```

### Sections 30-31: full torus campaign

```sh
python experiments/torus_campaign/run.py --cutoff 64 --output-dir /tmp/polyhedra-run/torus64
```

The Section 9 guide also gives the separate barrier solver command. Existing result files retain their original source hashes, precision, coordinates and evidence status. The [status ledger](../book/computational-status.md) states what each computation establishes and what remains conditional, historical or open.

## Licenses

The chapter companions live in `counting_mixing`, `normalizations`, `quantum_geodesics`, `quantum_surgery`, `section15`, `section15_quantum`, `section30`, `section9` and `torus_campaign`. Each directory's README records its scientific scope, invocation and evidence limits.

The newly authored code, tests, current fixtures and associated documentation in the exact [covered-file list](../LICENSES/new-companion-files.txt) are licensed under [MIT, Copyright 2026 Igor Rivin](../LICENSES/new-companions-MIT.txt). Existing toolkit and third-party notices remain applicable. Historical inputs, contract/acceptance snapshots, archived sources and generated results are outside this new-code grant; see the [license map](../LICENSES/README.md). The monograph has its separate CC BY 4.0 license.

This notice changes no runtime source, fixture, recorded result or approval pin and implies no numerical replay.
