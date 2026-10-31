# Polyhedra, Moduli, and Quantum Geometry

## Variational principles, spectral methods, and computation

This package contains the consolidated research monograph, its editable
mathematical figures, and the supplied companion study from igorrivin/ipoly.

## Build

Run from this directory with a standard TeX Live installation:

    latexmk -pdf -interaction=nonstopmode -halt-on-error polyhedral_volumes_and_geodesic_identities.tex

The main TeX file is self-contained. All nine TikZ figures are inlined in it,
between `BEGIN INLINE FIGURE` and `END INLINE FIGURE` comments. There are no
external image dependencies. The figures/ directory holds separate editable
copies of the diagram inputs and their common TikZ preamble. To change a
figure in the monograph, replace the corresponding inline block in the main
file; editing a separate copy alone does not change the compiled monograph.

The bibliography is included in the main TeX file and does not require BibTeX.
The included PDF was compiled with pdfLaTeX and latexmk. The filename is retained
from earlier revisions; the document title is Polyhedra, Moduli, and Quantum
Geometry.

## Structure

I. Polyhedra and moduli measures
II. Variational geometry and computation
III. Quantum geometry, degeneration, and surgery
IV. Curves, trace formulas, and quotients
V. Mapping-class dynamics and mixing
VI. Sharp counting and arithmetic
VII. Open problems and conjectural directions

The abstract, introduction, principal-result map, reading routes, and list of
figures explain the new organization. The torus–sphere normalization now
follows the boundary/cone discussion. Existing equation and theorem labels
were retained, so internal links follow the reordered sections.

## Integration of the companion study

Section 9 develops the exact volume-Hessian/FEM identity in the specified
disk coordinates, boundary response and Schur complements, a rooted-forest
Gaussian determinant, and the compatible-barrier path-following argument.
It also distinguishes geometric flips, mapping-class flip graphs, and the
scope of the three-manifold extension. Positive feasibility, interior angle
compatibility, convex boundary admissibility, and computational assumptions
are stated where they are needed.

The companion_ipoly/ directory contains the supplied manuscript, PDF,
README, and Python scripts unchanged. Its nested archive duplicates are not
included. The numerical scripts were not rerun for this editorial revision;
their dependencies and experimental scope are described in the companion
README. The main monograph gives the derivations used in its integration.

## Corrections of 30 October 2026

The abstract and two summaries now retain the factor 2^{-d}: the coefficient
of A^d in the small-area Weil--Petersson volume expansion is 2^{-d} times
the Thurston--Deligne--Mostow volume, where d = n - 3. Equation (8.11)
was already correct and is unchanged.

Section 13 now states the contour-continuation and locally uniform L^1
tail-control input needed for its infinite spectral derivation. That input
is identified as an additional analytic hypothesis, not proved in this
revision. The residue identity, curvature formula, finite fusion matrix,
and Hermitian pairing retain their independent first-moment and period
derivations. The nearby summaries have been qualified consistently.

## Mathematical status

The front matter separates established inputs, deductions proved in the text,
conditional implications, and numerical checks. Local quantum formulas retain
their family and normalization hypotheses. The counting-to-mixing converse
retains endpoint weights, and the explicit genus-two estimate retains its
nonsquare (2,2) stratum. The general gluing and sharp-error questions remain
open problems in the monograph.

SHA256SUMS records the bytes of the included source and reference files.
