# Independent review of the barrier examples and publication addendum

Disposition: approve the scoped experiment/reference logic, computational prose,
claim-ledger coverage changes, strict exporter integration, and inspected dirty
preview. This is source approval, not a claim that final clean-source generation,
publication or browser review has occurred. The final strict combined export
must contain both independent reports, no pending-evidence allowance, and the
fixed core hash below. Its later final artifact manifest must describe bytes
after the optional render-only backlinks.

The review was performed independently of the experiment and exporter authors.
The numerical solver itself, its full-suite baseline and wheel installation are
reviewed separately in `barrier-review.md`.

## Source and mathematical scope

The three fixed domains and independent maxima are correctly specified. The
full triangle maximum follows symmetry and strict concavity. The geometric disk
has one leading-trailing coordinate, zero volume derivative at its geometric
point, and nonzero barrier derivative `-28/15`. The two-triangle affine slice
has a negative right derivative at its flat endpoint, approximately
`-0.745354208180284059`, and strict concavity identifies its closed maximum.
No geometric realization is claimed for that slice.

An additional review calculation, independent of the driver and all toolkit
imports, constructs complex ideal shapes directly and uses 90-digit
Bloch-Wigner evaluation. It matches the three reported exact-space maximum
volumes with differences below `4e-65`. Exact rational dot/cross cotangents give
the disk's `-28/15` barrier derivative. These are independent numerical reference
comparisons and a rational derivative identity, not interval enclosures.

The driver's high-precision derivatives and scalar bisection references do not
call the production gradient or Hessian. It distinguishes exact decimal or
geometric angle spaces from the literal lifted binary64 Clausen model. That
distinction is necessary at the flat boundary: tiny triangle-sum defects move
the lifted stationary point and change the endpoint singularity. The page and
JSON preserve this qualification. The endpoint Bloch-Wigner comparison on
lifted angles is a numerical cross-check, not an assertion that their rounded
sums equal real pi.

All 54 recorded checks pass in the fresh corrected-source run and detached
replay. This count includes status and noncertificate flags as well as numerical
comparisons and trace checks; it does not mean 54 independent mathematical
proofs. The boundary observed gap is approximately `3.52701e-5`, below the
numerical sharper estimate `7.05981e-5` and the requested `1e-4`. Starting
centering and subsequent path work are reported separately. The limited
examples do not imply a scaling law, nearly-linear complexity, certified energy
error, or geometric realization.

The computational chapter changes retain all 204 inline formulas, 15 display
blocks, 15 numbered mathematical environments, two proofs, two propositions,
two TikZ sources and 26 ordered labels. All 26 claim IDs, proof statuses,
hypotheses, labels, original review evidence and source evidence are unchanged.
The prior proof review remains tied to its frozen chapter bytes; the new
computational revision has separate evidence. The historical-companion
reconciliation update accurately distinguishes the earlier grid from this
later barrier implementation.

## Reproduction, exporter and code review

The downloadable archive contains ten manifested payloads plus its manifest,
with unchanged maintained numerical modules, a clearly labeled subset
initializer, MIT license, captured requirements and origin provenance. The
post-fix ZIP was extracted outside the repository and run with the existing
minimal Python environment from an unrelated working directory, using an
absolute driver path and no PYTHONPATH. All actual toolkit imports resolved
inside the extracted bundle and matched the fixed reviewed module hashes.
Every case record exactly matched the fresh source-tree run. Detached Git
fields are unavailable/null, optional monograph sources are absent, and the
original checkout provenance is retained separately. This is a fresh numerical
replay using already-installed dependencies, not a dependency-resolution test.

The renderer validates source and fixture identity, refuses changed fixed
fixtures, preserves computation versions and timestamps during render-only
work, and labels inspection copies separately from the complete runnable ZIP.
The publisher requires an explicit matching barrier result when linked by the
chapter or ledger; it checks current source hashes, same-export report/input
bytes, embedded data and ZIP origin/payloads, rejecting missing, stale,
duplicate, extra or mutated payloads. Build inputs are frozen and rechecked.
Publication identity validation is not presented as a mathematical accuracy
check. The optional backlink changes only presentation, and the manifest labels
its build-time asset hash scope accordingly.

Source review found no circular reference oracle, hidden projection/clipping,
substitution of old canonical barrier results, or mistaken promotion of a
numerical gap estimate to a certificate. The root README's current-output link
initially pointed to the preceding export's closeout. The integration author
corrected it to the current barrier checkpoint while retaining the old closeout
as historical provenance; this correction was verified.

Focused validation passed: 27 experiment/exporter tests and 29 subtests. Those
tests ran before the narrow zero-dimensional core status correction; fresh
source-tree and detached three-fixture runs then used the corrected core and
matched every prior case record exactly. The numerical reviewer owns the
new zero-dimensional regressions and installed-package verification. Ruff
passes all four changed experiment/publisher Python files, and their authored
lines have no trailing whitespace.

## Preview and release boundary

All ten rendered chapter PDF pages were independently opened and visually
inspected. Text, formulas, equation numbers and both figures are legible with no
observed clipping, collisions or missing glyphs. The computational addendum fits
page 9. The approved preview PDF hash is
`05fa1d1c52b68df1ea3c46f04ca8452d30148340e26ac963f840f9ca86bbcb4d`.
Its chapter source is unchanged by the later core-only status correction.

Independent static HTML checks passed all local targets and fragments in the
three preview pages, with 209 chapter MathML nodes, both figures, every chapter
label and 12 bibliography anchors. This is not browser layout or interaction
verification. Browser/server work, external publication, network installation,
full-monograph proof review and rigorous floating-point certification were not
performed.

The combined preview was deliberately generated while the two new independent
reports were pending. The post-fix standalone barrier replay is fully checked,
but final strict combined generation still belongs to the release gate. A
clean-origin final run must regenerate the reports and ZIPs from the reviewed
source commit, check the final inspection copies/links, verify PDF rendered
pages against this approved layout, and record all final hashes after backlinks.
No canonical generated outputs or commits were made by this reviewer.

## Evidence and reviewer-harness corrections

`publication-review-manifest.json` identifies every reviewed source, commands
and evidence hashes. `publication-independent-checks.json` contains the
independent maxima, source-preservation checks, static links and all ten page
hashes. `publication-detached-replay.json` records the fresh corrected-core
execution, imports, payloads and result comparison. Initial pre-core-fix replay
evidence is retained separately under `publication-pre-core-fix-*`.

Two reviewer-harness corrections were needed and are preserved. The first
successful detached computation was followed by a false path assertion because
macOS returned `/var` while resolved imports used `/private/var`; resolving the
expected bundle root fixed that check without a numerical rerun. A draft inline
math matcher treated every preceding backslash as escaping a dollar sign,
including even-length TeX linebreak sequences. Counting escape parity fixed
that checker and established the 204 unchanged formulas. Neither was a product
failure; the unsuccessful checker/log drafts remain available.

## Exact reviewed source identities

| Source | SHA-256 |
| --- | --- |
| `experiments/section9/barrier_run.py` | `e9f1f772f9cfa5bb74637926b868d5f6cc1049c3cc4372faf8bbe750afc83c60` |
| `experiments/section9/barrier-fixtures.json` | `fdd1cd88cec4398199e46c8a38cfec2955f0118672972bfceb5ab732b86aec1a` |
| `experiments/section9/barrier-page.html` | `e4de74a735bf9d7bbdabae7f59fa368cef972297639a4cb2719d97d92ce3fb90` |
| `site/build_section9.py` | `b01681557e5acde91dac749065b9ef787edd03cb3a5b4fa21f77aff9e0cc63a5` |
| `book/chapters/09-volume-hessians.tex` | `5f61c653a5cd26bfa5e1a5b436c621b7d72436af46abd3d0b63c5cb401483b00` |
| `book/claims/section9.json` | `255ed6ebb0c3eb1c7714d238f2829f6115487817408545e40461ef87b47b5c73` |
| `packages/volume-toolkit/ideal_poly_volume_toolkit/angle_barrier.py` | `d782aff2a23c9073c6f7cf02666cc0ec3f4446f28185c7474116fcf42edbbd07` |
