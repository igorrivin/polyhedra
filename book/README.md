# Monograph source

The canonical text is [Polyhedra, Moduli, and Quantum Geometry](polyhedral_volumes_and_geodesic_identities.tex). It was imported byte-for-byte from the supplied 30 October 2026 archive; the current edition revises [Section 9](chapters/09-volume-hessians.tex) following two independent mathematical audits. Its original labels and numbered formulas are preserved, with expanded coordinate and positivity proofs, explicit finite-centering guarantees, and precise geometric hypotheses. The rest of the monograph has not received this bounded review.

The [Section 9 claim ledger](claims/section9.json) connects each statement to hypotheses, review evidence, code, computations and remaining gaps. The [companion reconciliation](companion-reconciliation.md) records corrections to the preserved [historical companion](../research/ipoly/README.md). Historical source bytes and the supplied reference PDF remain unchanged.

Build with TeX Live and latexmk from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The wrapper `main.tex` delegates to the canonical source, which now inputs the separate Section 9 chapter. The [reference PDF](reference/polyhedral_volumes_and_geodesic_identities.pdf) is the supplied PDF, not a newly reviewed release. New full-book build outputs go to the ignored `build/` directory.

The TikZ figures remain inline in the canonical TeX files, with editable copies in `figures/`. Editing only a separate figure copy does not change the PDF. Their captions and labels are retained.

The [chapter publishing build](../site/README.md) produces a complete Section 9 HTML chapter and PDF alongside the existing [worked computational example](../experiments/section9/README.md). It keeps the claim ledger and source archive with the generated chapter. Build and render verification are recorded separately from the proof audits in the [chapter execution evidence](../docs/execution/section9-chapter-2026-10-31/README.md); a successful conversion is not a full-monograph proof review or public deployment.

Original source hashes and duplicate mappings are in [provenance](../provenance/README.md). The [original package README](../provenance/monograph/README.source.md) records mathematical qualifications and the unavailable numerical replays. The Section 9 revision does not supply the missing torus diagnostic archive or executable Airy evidence. Their status remains recorded in the [computational-status ledger](computational-status.md).

Authorship metadata and text licensing require an explicit publication decision. No public book or Site has been published by this revision.
