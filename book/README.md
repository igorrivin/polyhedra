# Monograph source

The current canonical text is [Polyhedra, Moduli, and Quantum Geometry](polyhedral_volumes_and_geodesic_identities.tex), imported byte-for-byte from the supplied 30 October 2026 source archive. Section 9 already incorporates the central `ipoly` arguments. The historical companion remains at [research/ipoly](../research/ipoly/README.md).

Build with TeX Live and latexmk from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

The wrapper `main.tex` delegates to the full imported source; it introduces no mathematical changes. The [reference PDF](reference/polyhedral_volumes_and_geodesic_identities.pdf) is the supplied PDF, not a newly reviewed release. New build outputs go to the ignored `build/` directory.

All nine TikZ figures are currently inline in the TeX, with editable copies in `figures/`. Editing only a separate figure copy does not change the current PDF. The integration plan will replace this duplication with one canonical input while retaining the captions and labels.

Source hashes and duplicate mappings are in [provenance](../provenance/README.md). The [original package README](../provenance/monograph/README.source.md) records mathematical qualifications and the unavailable numerical replays. This import does not supply the missing torus diagnostic archive or executable Airy evidence. Their availability claims remain correction work items, not newly reproduced results.

Authorship metadata and text licensing require an explicit publication decision. No public book or Site has been published by this import.
