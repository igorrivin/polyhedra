# Independent normalization companion review

The computational source, fixtures and tests pass this bounded independent
review. The README needs one source-pointer correction before its final
approval: its last paragraph links the Koziarz–Nguyen and McMullen compactified
volume formulas to Section 7, but those formulas are in Section 8. Replace
that link/text with `08-wp-flat-limit.tex`. No numerical or execution defect
was found. No canonical source was edited by this reviewer.

The approved computation uses exact rational arithmetic throughout its
scientific calculations. Floating elapsed time is metadata. Formal class
values at total weight two are distinguished from hyperbolic geometry;
`wp_from_weights` rejects the zero-area boundary. Strict light subsets,
unordered complementary divisors and final-chamber endpoints are handled
consistently. The no-light four-point case retains the valid cusp endpoint
at epsilon one. A polynomial may agree continuously on a wall while the
strict chamber predicate excludes that wall; the tests retain this distinction.

The independent probes in `verify_companion.py` passed:

- 121 four-point and 376 five-point flat-weight vectors: the positive
  denominator-six grid and every distinct relabeling of the fixed fixtures.
- 1,491 direct class evaluations, at two interior points and the continuous
  wall value for each vector. A five-coordinate intersection calculation
  with diagonal form `(1,-1,-1,-1,-1)` replaces the author's redundant ten
  boundary generators. It uses the standard blowup representation as a
  mathematical input, and does not call the author's psi or pairing helpers.
- An independent restricted-growth partition enumeration, with Bell counts
  15, 52 and 203 for n=4,5,6, agrees with the author's insertion recursion.
  The McMullen and intersection volumes agree at every tested n=4/5 vector.
- 512 SL2 triples, including 340 degenerate trace charts. The twist derivative
  was independently extracted as the odd part of an exactly quadratic
  conjugation expression, with zero algebraic residual.
- All 65 four-block partitions for each of three six-point weight vectors:
  195 F-curve probes. A reduction to four block weights independently checks
  the B and linear-term pairings.
- Gaussian-elimination determinant checks for the tetrahedral constraint
  minor and skew matrix; the uniform Gram eigenvalues `(-5,3,3,3)` and the
  triple-angle density ratio verify the fixed Gram/Pfaffian fixture.

All 11 supplied regression tests passed and Ruff was clean. The fixed driver
ran from `/private/tmp` under both normal Python and `python -O`, producing
the same scientific fields as the author run. The comparison omits precisely
the top-level timestamp, elapsed time and development source record. The
four companion source hashes were checked separately and stayed fixed.
Parallel manuscript authorship means the development manuscript hashes are
not an approval target in this code review; the final clean-source replay
must bind the subsequently frozen manuscript inputs.

The actual dirty Git state is retained in the replay. Import-only execution
from another directory produced no files or stdout/stderr and did not invoke
a subprocess. An injected failed check under optimized Python exited with
an error before creating an output file. Existing-output refusal is also
covered by the supplied CLI regression. Source inspection confirms that
scientific checks use explicit exceptions rather than removable assertions,
the sole subprocess operation is read-only Git metadata without a shell,
and no network, dynamic source execution, tolerance-based certification or
global numeric-context mutation is present.

The result remains finite arithmetic conditional on the stated intersection
and geometric formulas. Neither the original fixtures nor these larger
bounded probes prove a general divisor identity, analytic convergence,
global hyperbolic realization, or a full hyperideal cell integral. This
review does not designate the whole manuscript or toolkit as verified.

The exact approved computation hashes and evidence hashes are in
`review-manifest.json`. README approval is provisional pending the single
link correction. No package install, full-suite rerun, PDF build, Site action,
commit or remote operation was performed.
