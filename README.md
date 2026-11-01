# Polyhedra

Research software and a computational companion to *Polyhedra, Moduli, and Quantum Geometry*.

This repository integrates the volume toolkit, the historical `ipoly` study, and the supplied monograph while preserving the original Git histories and source provenance. The integration is in progress; numerical examples and mathematical claims retain the evidence limits recorded in the audit and plan.

## Contents

- [Volume toolkit](packages/volume-toolkit/README.md): existing Python package and API, tests, examples, and historical results.
- [Monograph source](book/README.md): canonical LaTeX with normalization and hypothesis reviews of Sections 1–8 and Appendix A, a separately reviewed Section 9, the current finite-period and local-surgery revision of Sections 12–14 and 16, and bounded computational-evidence revisions to Sections 15 and 30. Each increment retains its own review status and evidence limits.
- [Historical ipoly study](research/ipoly/README.md): original manuscript and verification scripts, retained unchanged.
- [Complete Section 9 chapter](site/section9/chapter.html): reviewed text with proofs and computational coverage; [chapter PDF](site/section9/downloads/section9.pdf) and [monograph LaTeX source snapshot](site/section9/downloads/monograph-source.zip). The [generation checkpoint](docs/execution/section9-barrier-2026-10-31/README.md) records artifact provenance; these frozen downloads do not include the later Sections 15/30 or normalization revisions.
- [Section 9 companion](site/section9/index.html): the first worked text, computation and result example; [runnable reproduction archive](site/section9/downloads/section9-reproduction.zip) and [instructions](experiments/section9/README.md).
- [Section 9 chapter checkpoint](docs/execution/section9-chapter-2026-10-31/README.md): mathematical corrections, independent proof review, publishing-build evidence and remaining validation; [claim ledger](book/claims/section9.json), [historical companion reconciliation](book/companion-reconciliation.md) and [chapter build guide](site/README.md).
- [Section 9 dense barrier checkpoint](docs/execution/section9-barrier-2026-10-31/README.md): executable centering and short-step schedule, independent numerical references, and the separate computational-addendum and export review. Floating-point gap estimates are not formal certificates.
- [Sites reading preview](docs/execution/sites-preview-2026-11-01/README.md): frozen Section 9 presentation checkpoint with reviewed navigation, passage search and an inspected offline candidate. Its source upload failed; further upload is deferred until manuscript revision and local release verification are complete.
- [Current quantum and surgery increment](docs/execution/quantum-surgery-review-2026-11-01/README.md): Sections 12–14 and 16, with two claim ledgers and a [bounded computational companion](experiments/quantum_surgery/README.md). Its initial author run passes 192 exact finite identities, period and Euler-arc comparisons at 60/90 digits, and 15 focused tests. Independent review, final artifact generation and integrated PDF verification have separate records; finite computations do not establish spectral tails or global quantum-invariant asymptotics.
- [Prior normalization review](docs/execution/normalization-review-2026-11-01/README.md): Sections 1–8 and Appendix A, with 41 recorded claims and an [exact finite companion](experiments/normalizations/README.md). Independent computational review passed; the checkpoint records mathematical review and integrated PDF verification separately. This is a bounded increment, not a full-book proof review.
- [Prior Airy and torus checkpoint](docs/execution/monograph-revision-2026-11-01/README.md): corrected evidence descriptions, finite Airy checks and a bounded replacement torus computation, with inherited theorem claims and unreplayed original results kept distinct. Its artifacts remain frozen.
- [Computational status](book/computational-status.md): checked examples, reported results awaiting evidence, and the next mathematical review tasks.
- [Numerical errata](book/numerical-errata.md): corrected software contracts, changed bounded examples, and the limits of those corrections.
- [Numerical-correctness checkpoint](docs/execution/numerical-correctness-2026-10-31/README.md): precision, angle-solver and optimizer-result evidence, review stages and remaining checks.
- [First integration checkpoint](docs/execution/2026-10-31/README.md): preserved baseline, initial independent reviews and recovery inventory.
- [Integration plan](INTEGRATION_PLAN.md): correction priorities, computational coverage and publication phases.
- [Provenance](provenance/README.md): source identities, restoration checks and path mapping.
- [Audit](audit/2026-10-31/): the evidence used to plan this integration.

The current increment's output paths are `artifacts/quantum_surgery/result.json` and `artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf`; its checkpoint records generation, source identities and verification. The earlier normalization result and PDF, Site downloads, and Section 15/30 results retain their own source identities. Section 15's global contour, tail and uniform-remainder review remains outstanding, followed by the counting/mixing chapters and the other unrevised sections specified in the plan. The whole book is not yet publication-ready. Upload and deployment remain the final publication step.

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
