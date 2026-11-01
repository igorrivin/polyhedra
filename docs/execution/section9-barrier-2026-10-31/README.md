# Section 9 dense barrier checkpoint

Date: 31 October 2026. Baseline source commit:
`014d1c4e70dfdfc852fa542f3a9c469f08dbd618`.

This increment implements the chapter's specified short-step schedule in a
small dense binary64 solver, starting from a supplied positive affine angle
slice. Initial centering has its own budget. Endpoint status, fresh Newton
decrement, angle margins, linear-solve residuals, numerical conditioning and
theorem-derived gap estimates are reported separately. Every result retains
`certified: false`. The implementation supplies no feasibility construction,
nearly-linear backend, formal rounding certificate or geometric realization.

The [solver](../../../packages/volume-toolkit/ideal_poly_volume_toolkit/angle_barrier.py),
[fixed-fixture experiment](../../../experiments/section9/barrier_run.py),
[chapter addendum](../../../book/chapters/09-volume-hessians.tex), and
[26-claim ledger](../../../book/claims/section9.json) are the maintained sources.
The [publishing guide](../../../site/README.md) specifies the two-report export:
the grid and barrier examples have separate result files, HTML companions and
reproduction bundles. The chapter builder requires the explicit barrier
report and rejects mismatched source, fixture, HTML and ZIP identities.

The mathematical approval in the
[previous checkpoint](../section9-chapter-2026-10-31/README.md) applies to its
frozen chapter and ledger hashes. This increment preserves that proof
mathematics and its labels; changes to the ending computational subsection,
status prose and [companion reconciliation](../../../book/companion-reconciliation.md)
have a separate review scope. Neither a successful floating-point run nor a
publisher integrity check promotes a theorem's proof status.

The independent [solver review](barrier-review.md) and
[experiment, export and addendum review](barrier-publication-review.md) approve
their explicitly scoped source snapshots. Their
[core manifest](review-final-manifest.json) and
[publication manifest](publication-review-manifest.json) identify exact source
and evidence bytes. The corrected solver hash is
`d782aff2a23c9073c6f7cf02666cc0ec3f4446f28185c7474116fcf42edbbd07`.
The review found and corrected a zero-dimensional status inconsistency at tiny
positive parameters; the initial reproduction and earlier author manifests
remain preserved.

Final focused core checks passed 43 tests. The separate experiment/publisher
suite passed 27 tests with 29 subtests; the publication reviewer subsequently
replayed the three cases using the corrected core. All 54 recorded example
checks pass, including status flags, numerical comparisons and trace checks.
Independent reference probes,
fresh detached reproduction, and an offline wheel installed into a new target
also passed within the recorded environments. The broader package run before
the narrow fix had 423 passed, 18 skipped, four failures and nine collection
errors; their identities and messages match the preceding checkpoint's
missing optional dependencies. No final-source full-suite pass is claimed.

The [initial preview](preview-static-checks.json) used dirty sources and allowed
the two then-pending reviews. Its ten PDF pages were inspected independently;
the [parent's visual approval](parent-preview-visual-review.json) pins the PDF
and every rendered-page hash. These records precede the narrow core correction
and remain historical. The [evidence copy manifest](evidence-copy-manifest.json)
verifies byte-preserving copies, including failed checker drafts and the
original failed approximate-centering test.

The corrected-core [strict combined preview](strict-preview-static-checks.json)
has now passed with both approved reports and no pending-evidence allowance.
Its separate [independent approval](barrier-strict-preview-review.md) verifies
current sources, explicit results, embedded data, local links, all three ZIP
payload inventories and the actual report inspection copies. Both fresh
numerical reports survive the backlink refreshes byte for byte. The
[page comparison](strict-preview-visual-comparison.json) shows all ten rendered
pages identical to the previously inspected layout; the parent independently
confirmed that comparison. The strict PDF hash is
`71a422affa9a76b0b3872977d70e9e97409ac8c1086633066c3836330a4afbc8`.
Its source checkout is explicitly dirty; this is an approved precommit preview.
The [strict evidence copy manifest](strict-preview-evidence-copy-manifest.json)
keeps the later approval separate from the frozen primary review inputs.

The [final closeout](closeout.md) records clean-source generation from
`c1f100b957166b93eca0d214586322d5af71b9cf` and canonical artifacts in
`4823348bbd1593d8cade4d0a038531f80a97a676`. Fresh grid and barrier runs, the strict chapter build,
both render-only backlinks, both detached numerical replays, all final output
hashes and the ten-page comparison passed. The
[artifact manifest](final-artifact-manifest.json) covers 46 canonical files after
backlinks. The final PDF hash is
`9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0`.
No public Site or book edition is published. The postcommit receipt is retained
outside the repository as explained in the closeout; package-environment,
browser and numerical-certification limits remain explicit above.
