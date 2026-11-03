# Exposition revision: Sections 10.1 and 17.1

Reader feedback identified two gaps: Section 10.1 used representation-theoretic notation before explaining its purpose, and Section 17.1 gave the unfolding formula without a concrete model of the operation. This revision adds the missing motivation, definitions, and calculations while preserving existing labels and numbered statements.

## Section 10.1

The revised text starts with the problem of making local algebra compatible with cutting, gluing, and changes of triangulation. It defines the complex Lie algebra, its representations and irreducibles, the tensor-product action, and the Clebsch-Gordan decomposition. The antisymmetric and symmetric pieces of two copies of C² provide a first example.

The text then defines the intertwiner space, the inclusions used to build its two bases, the basis maps B, the coefficients F, and the admissible summation indices. Three spin-one-half factors give an explicit two-dimensional multiplicity space. Four displayed vectors determine the complete recoupling matrix; inner products compute its entries. Phase choices, orthonormality, tetrahedral label placement, and the distinction between exact algebra and geometric asymptotics are explicit. The state-sum paragraph explains each index and weight and how the pentagon identity enters.

## Section 17.1

The opening example integrates a periodic sum on [0,1] by assembling its translated intervals into the real line. The exponential example has an elementary mean but is visibly nonconstant. The tent-function example supplies a contrasting pointwise partition of unity.

The surface discussion identifies moduli space, the space of surfaces with a distinguished curve, the orbit and stabilizer, and the change of integration domain. Cutting and regluing explain the length factor x dx. The punctured torus is worked through from pants with lengths (0,x,x) and twist period x to the elementary integral, the single stack factor one-half, McShane's cusp-gap mechanism, and V(1,1)=π²/12. A final paragraph explains how positive-boundary gap identities lead to lower-complexity volume recursion.

## Evidence and limits

[source-review.json](source-review.json) records exact source hashes, primary sources consulted, and author preview checks. [example-verification.json](example-verification.json) records exact finite algebra for the recoupling example using rational arithmetic and Q(sqrt(3)). The elementary unfolding examples have written derivations in the text. The cusp-gap classification, its exceptional null set, and the full volume recursion remain attributed to their cited sources; the new text explains their roles without claiming to reproduce all their proofs.

This is an author revision and self-review, not a new independent mathematical acceptance. The historical claim ledgers and their accepted snapshots are unchanged. No scientific campaign was rerun. All later parts of Chapters 10 and 17 remain byte-identical to the previous edition, and the other chapter sources are unchanged.

The author preview compiled 206 pages, retained all 613 label numbers and 129 bibliography numbers, and passed all 46 existing site tests. All eight pages spanning the revised passages were rendered and visually inspected. The final clean build and publication receive separate receipts in the outer `execution/exposition-revision-2026-11-03/` directory. Generated artifacts retain their own source commit in the edition manifest.

The local patch workflow preserved untouched source blocks and kept its intermediate Markdown markers outside the canonical TeX. Final short copyedits clarify the lowering operator, essential/simple curves, and ineffective isotropy. A separate unified diff records the complete final source change. The PDF-linker's comparison receipt now reports the actual page count instead of the previous fixed value of 200.
