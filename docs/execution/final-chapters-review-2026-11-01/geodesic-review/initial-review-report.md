# Independent initial review of Sections 17-22

Decision: mathematical arguments and the finite G1-G10 contract are accepted at their explicitly bounded scopes. Two minor source-pin repairs, R1 and R2, are required before final source approval. This initial review binds the author freeze manifest SHA-256 `38994ff43e952ff42ccafb4d56c44e51c385a0092d156e3d35cdbcf1041d7eec` and the seven-file source set SHA-256 `86ac29026811b5c7f6207e4568d01a01496326f3c8c1b0d8fb2b8fcfb541d8c6`.

## Findings requiring correction

1. R1, chapter 19 line 153 / claim 19.09: MirzSimple Theorem 3.4 and (3.6) support coordinates and the definition of combinatorial length. The actual two-sided comparison is Proposition 3.5, (3.7), p.107, for an L-bounded decomposition. Add those exact pins in the prose, source record and affected ledger descriptions. [Primary journal PDF](https://annals.math.princeton.edu/wp-content/uploads/annals-v168-n1-p03.pdf).
2. R2, chapter 22 lines 52-53 / claim 22.03: the explicit measure-zero paragraph after Corollary 5 is printed p.5, while the cited Theorem 3 is p.4. Extend the pp.3-4 pin to cover p.5, consistently in prose and records. [Primary author draft](https://macbuse.github.io/M2R_2019/shearsAgain.pdf).

No formula, local-proof, topological-indexing or finite-contract blocker was found. These pin corrections do not alter G1-G10. The initial source snapshots and review are preserved; targeted acceptance must bind the repaired final hashes.

## Coverage and independent evidence

All six chapters were read in full, the extracted-baseline changes were inspected, and all 59 claim rows were checked for formulas, hypotheses, dependencies, proof summaries, source pins and computation status. `initial-claim-review.json` gives a distinct note for every row. `initial-label-review.json` covers all 54 owned labels. The independent source check confirms 48 baseline labels in original order, six explicit additions, unchanged headings, exact agreement between the baseline extraction and author before snapshots, valid claim dependencies, and matching chapter/ledger hash bindings. It does not reissue approval of unrelated chapters or the global graph.

`independent_probes.py` imports neither author scratch nor author implementation. It passed 37 exact symbolic/rational checks and 112 representative floating checks across 70 and 110 decimal digits. It independently verifies Hessian numerators/determinant, finite symbolic kernel cancellation, signed matrix traces, cusp and triangle algebra, finite coarea integrals, analytic-tail comparisons, nonstationary position matching, and scaled positive shadows through length 1000. These probes are not a complete G1-G10 implementation, interval enclosures or global spectrum computations. The first run reached result serialization but hit a reviewer variable-name collision; that bookkeeping bug was repaired and the full probe rerun successfully.

## Proof-sensitive checks

The strongest potential objection is that minimizing a strictly convex function need not by itself establish strict convexity in an external parameter. The chapter avoids that gap: the full endpoint objective is strictly jointly convex, feasible configurations interpolate affinely, and at an intersected cuff the twist coefficient is plus or minus one. Different twists therefore cannot have identical full endpoint vectors. Applying the strict inequality to the interpolated competitor and then taking the minimum proves the asserted strict convexity.

The endpoint characterization can also be justified without merely assuming existence of a minimizing configuration. Write C=cosh(d)>1 and

`z = ((C-1)/2) cosh(u+v) + ((C+1)/2) cosh(u-v)`.

Since `max(|u+v|,|u-v|)=|u|+|v|`, this gives `D_d(u,v) >= |u|+|v| + log((C-1)/4)`. Thus the finite sum is coercive on the closed affine gluing space. It has a unique minimum. In independent coordinates for the feasible endpoints and the genuine twist, the endpoint map is injective; pulling the positive-definite block Hessian back preserves positive definiteness. The implicit-function theorem applies at the minimizer, and the Schur complement of its endpoint block gives positive second variation in the twist. This supplements, but is not needed to repair, the chapter's valid interpolation proof. Disjoint curves have no such twist constraint and remain constant.

The torus figure classification uses the topology of the incompressible pants complement, not numerical trace multiplicity. Its two annuli identify the unique disjoint simple class. Exactly three cuff-pair choices survive, with two distinct N cyclic words and one H word. The N words have primitive homology, so are not proper powers; the H cyclic word is not periodic. The positive F kernel then groups complete three-curve blocks through an exact functional relation. No finite list is promoted to a whole-surface enumeration.

The other vulnerable distinctions are handled explicitly: an unfolding average does not imply pointwise constancy; derivative/variance claims retain the required convergence and regularity; the cusp gap partition excludes geodesic-boundary exits; positions and tangential velocities are separate gluing data; signed cusp decoration is not an embedded-horocycle claim; and Basmajian's orientation factor is checked at both ends.

## Sources and access limits

`source-statement-review.json` records all fourteen cited primary-source roles. Independent direct or indexed checks recover the critical Mirzakhani, Hu-Tan, Luo-Tan, Rivin, ALPS, McShane-draft, Springborn and Parlier statement pins. Mirzakhani's volume PDF could only be checked through targeted primary-PDF indexing after a direct timeout. Lei-Zhang remains abstract-only: the preview click failed. Wolpert's scan text exposed its cover, so no newly recovered external formula is claimed; its mathematical role is independently supplied by the endpoint derivation.

An additional primary scan makes Kerckhoff Theorem 1, p.253, and the explicit nonsimple-curve remark on p.254 readable. This is an optional improvement to the source record, not a replacement for the local argument and not a complete external-proof audit. [Primary scan](https://poisson.phc.dm.unipi.it/~camponovo/Kerckhoff-NielsenRealizationProblem-1983.pdf).

The arXiv connector initially stalled for about 23 minutes and was interrupted by the root agent; it supplied no usable evidence. Subsequent bounded web reads completed normally. No private manuscript content was uploaded.

## Exposition and anti-pattern review

The revision states domains and conventions adjacent to formulas, retains the earlier anchors, and explains why each correction changes the mathematical scope. No unsupported novelty, global classification from sampling, source proof from theorem inspection, numerical enclosure from precision agreement, or publication approval from local checks is asserted. The pending maintained companion status is honest in all 59 rows. The two required edits improve pinpoint provenance only.

No canonical source was edited by this reviewer. No stage, commit, installation, PDF operation/marker, full scientific campaign, upload, or unrelated toolkit tests were performed.
