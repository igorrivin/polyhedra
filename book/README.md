# Monograph source

The canonical text is [Polyhedra, Moduli, and Quantum Geometry](polyhedral_volumes_and_geodesic_identities.tex). It was imported byte-for-byte from the supplied 30 October 2026 archive. [Section 9](chapters/09-volume-hessians.tex) was revised following two independent mathematical audits, with its original labels and numbered formulas preserved, expanded coordinate and positivity proofs, explicit finite-centering guarantees, and precise geometric hypotheses.

The [current revision checkpoint](../docs/execution/monograph-revision-2026-11-01/README.md) separates [Section 15](chapters/15-quantum-airy.tex) and [Section 30](chapters/30-sharp-diagnostics.tex) into chapter files and corrects their computational-evidence descriptions. New companions check the [finite Airy algebra and approximation column](../experiments/section15/README.md) and a [bounded replacement torus diagnostic](../experiments/section30/README.md). These are scoped additions: the exact quantum-integral table and the original length-8192 torus report remain unreplayed, and neither chapter is designated fully mathematically reviewed. The remaining chapters retain their earlier review status.

The [Section 9 claim ledger](claims/section9.json) connects each statement to hypotheses, review evidence, code, computations and remaining gaps. The [companion reconciliation](companion-reconciliation.md) records corrections to the preserved [historical companion](../research/ipoly/README.md). Historical source bytes and the supplied reference PDF remain unchanged.

Build with TeX Live and latexmk from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The wrapper `main.tex` delegates to the canonical source, which inputs the separate Sections 9, 15 and 30. The [reference PDF](reference/polyhedral_volumes_and_geodesic_identities.pdf) is the supplied PDF, not a newly reviewed release. New full-book build outputs go to the ignored `build/` directory.

The TikZ figures remain inline in the canonical TeX files, with editable copies in `figures/`. Editing only a separate figure copy does not change the PDF. Their captions and labels are retained.

The [chapter publishing build](../site/README.md) produces a complete Section 9 HTML chapter and PDF alongside the grid and dense barrier [computational examples](../experiments/section9/README.md). It keeps the claim ledger and source archive with the generated chapter. The barrier implementation extends computational coverage while preserving the reviewed proof mathematics; its numerical gap estimates are not interval certificates. The [barrier checkpoint](../docs/execution/section9-barrier-2026-10-31/README.md) records that implementation and export review separately from the earlier [chapter proof and build evidence](../docs/execution/section9-chapter-2026-10-31/README.md). These existing Section 9 exports, the [reading preview](../docs/execution/sites-preview-2026-11-01/README.md), and their broader monograph-source downloads remain frozen historical checkpoints. They have not been regenerated to include the current Sections 15 and 30 revisions. A successful conversion is not a full-monograph proof review or public deployment.

Original source hashes and duplicate mappings are in [provenance](../provenance/README.md). The [original package README](../provenance/monograph/README.source.md) records mathematical qualifications and the unavailable numerical replays. The [computational-status ledger](computational-status.md) distinguishes newly executable finite checks from missing original calculations, and records the remaining review work.

Authorship metadata and text licensing require an explicit publication decision. Manuscript revision, computational checks and local release verification precede the final upload and deployment step in the [plan](../INTEGRATION_PLAN.md). No public book or Site has been published by this revision.
