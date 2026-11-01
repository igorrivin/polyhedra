# Section 15 analytic and numerical review

Section 15 now has an independently reviewed additive Airy expansion for the
specified pole-cleared equal-label regular-family Barnes integral, with fixed
bounded real transition parameter. The proof controls the whole contour,
global tail, Gaussian localization, and integrated remainder. Its
[14-claim ledger](../../../book/claims/section15.json) distinguishes the
analytic theorem, its external inputs, finite numerical evidence, and open
extensions. General tetrahedral shapes, unbounded transition parameters,
fixed positive volume, and a global state-integral interpretation remain
outside the approved theorem.

Source commit: `9f5b17aa34dd3ede7ae0b26d80b3b14d52111042`. The [closeout](closeout.md) records the exact source
and artifact boundaries. The [fresh full result](../../../artifacts/section15_quantum/result.json)
was generated after this source commit, outside the clean checkout. Its two
recorded source states have the same commit, empty Git status, and seven
hashes matching committed bytes. It contains 21 whole-integral quadratures,
seven precision/contour comparisons, and 28 direct special-function checks
at each of 40 and 60 decimal digits.

The [strict comparison](clean-source/scientific-comparison.json) preserves
all 21 scientific row objects and seven comparison objects from the original
[exploratory full run](computation/full-v1.json), excluding only the two
actual timing-field locations. Every one of the 27 shared component records
at each precision agrees exactly; the added tanh-sinh/direct-tail record is
validated separately. Both runs retain their distinct code/source identities.
The new result is an actual replay of the final committed code.

The first freshly evaluated quantum value is `0.459086488736078952...`, which
rounds to `0.459086`. Its difference from the historical `0.459087` is
approximately `-5.11263921048e-7`; the historical rounding convention and
original evaluator remain unknown. The other five historical quantum values
agree at six decimal places. An independently written whole-Barnes reference
agrees at all seven tested parameter points within `1.80e-12` observed difference.
Quadrature estimates and finite agreement do not give interval enclosures or
a guaranteed count of correct digits. Exact rational bounds control stated
correction-series/tail components under their strip hypotheses.

The [187-page working PDF](../../../artifacts/section15-analytic-review-2026-11-01/monograph-working-draft.pdf)
is the exact precommit PDF reviewed by the integration reviewer. Its 18 active
input hashes match the source commit. The reviewer actually inspected
[23 selected pages](integration-review/visual-review.json): every Section 15
page, adjoining pages, contents, List of Figures, and the shifted bibliography.
The other 164 pages were not visually reviewed in this pass. The preserved
PDF is not described as a postcommit rebuild.

The principal evidence is:

- [Analytic review](math-review/analytic-review.md),
  [approved analytic hashes](math-review/approved-hashes.json), and
  [primary-source pins](math-author/primary-source-pins.json).
- [Numerical integration delta](integration-review/numeric-delta-review.json),
  which preserves the earlier analytic proof and scopes the new finite claims.
- [Evaluator review](computation-review/computational-review.md),
  [final source approval](computation-review/approved-hashes.json),
  [independent reference](computation-review/independent-whole-q-matrix.json),
  and [final targeted acceptance](computation-review/final-source-acceptance.json).
- [Integrated source/PDF review](integration-review/review.md),
  [12-path approval](integration-review/approved-source-manifest.json),
  [source checkpoint](checkpoint/source-checkpoint.json), and
  [fresh-run command receipt](clean-source/run-command.json).

The failed [direct-D development attempt](computation/direct-D-development-failure.json)
and [method/refinement diagnostics](computation/direct-D-refinement.json)
remain explicit evidence that internal quadrature errors can be misleading.
The evaluator review records the historical odd-cutoff bookkeeping defect
and the author's observed pre-fix residual; a standalone raw before-run
artifact was not retained. The final acceptance file records the executed
after-fix quadrature and independently computed shorter integral.

The [copy manifest](evidence-copy-manifest.json) binds 52 compact
evidence copies to their exact outer-source bytes and lists omissions.
Duplicate chapter archives, build caches, rendered PNGs, and superseded
successful development runs remain outside canonical. Archived scripts and
bare filenames can refer to omitted outer working files. The maintained
[evaluator guide](../../../experiments/section15_quantum/README.md) is the
reproduction entry point.

Run `python -B docs/execution/section15-analytic-review-2026-11-01/verify_checkpoint.py`
after the local artifact commit, or add `--candidate` before that commit.
The verifier checks identity, ancestry, clean-run provenance, finite result
equality, preservation, and local links. It does not replay quadrature,
rebuild the PDF, or repeat visual inspection. Gates remain active under
`python -O`. Receipts are exclusive writes outside the checkout; `--receipt`
accepts a new path under this checkpoint's outer execution directory.
This verifier targets this checkpoint's exact candidate/final checkout state.
Later chapter revisions are expected to change HEAD or source bytes; checking
a later checkout will then reject that state without invalidating the retained
historical checkpoint evidence. Verify the recorded checkpoint checkout when
revisiting these gates. Independent candidate and postcommit review receipts
stay outside the artifact commit so they can bind its manifest and HEAD.

The original historical evaluator/raw campaign and the length-8192 torus run
remain unrecovered/unreplayed. Further chapter review, optional-dependency
coverage, HTML/browser verification, and publication preparation are separate
work. Upload remains the final publication step.
