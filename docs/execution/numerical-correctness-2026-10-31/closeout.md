# Numerical checkpoint closeout

The reviewed H³ numerical increment and its regenerated Section 9 companion
are committed locally. The numerical checks below pass within their stated
scope; the complete optional-dependency and publication gates remain open.

| Record | Commit |
| --- | --- |
| Reviewed numerical source, tests, contracts and evidence | `bed2d7dbaf80df7bcc4fd75ecce0459627c58963` |
| Clean source after test-whitespace cleanup | `9188e0624cdf6d9949af1f620336eff67c8b59d7` |
| Outputs regenerated from that clean source | `29440cfbfcdaa23711cfdac4e09bf5f939404273` |

The initial staged whitespace check found an extra final blank line in each
of two new test files. The shell block continued to the source commit after
that assertion; this was not a passing whitespace gate. The following commit
removed only those two newline bytes, with equal parsed test ASTs before and
after. All 47 product Python hashes remain identical to the independently
reviewed and installed-wheel-verified bytes. The corrected authored whitespace
check passes. [Hygiene evidence](source-hygiene.json) and
[staging verification](source-staging.json) preserve that sequence; earlier
test logs, source hashes and review findings were not rewritten.

The canonical [result](../../../artifacts/section9/result.json) records the
clean source commit, `repository_dirty_at_start=false`, and an empty initial
Git status. All seven recorded source/input/book hashes match both the source
commit and current files. All twelve numerical checks and exact rational
fixture checks pass: determinant 60, grounded determinant and forest sum 15,
15 nonzero forests, and Schur entry 15/2.

The final [reproduction ZIP](../../../site/section9/downloads/section9-reproduction.zip)
was extracted into a new temporary directory outside every checkout and run
with the fresh minimal Python 3.12 environment and `PYTHONPATH` unset. Its
[detached result](final-detached-result.json) passes all numerical and exact
checks and verifies all nine payload hashes. It records the clean originating
commit, unavailable live Git state, and explicitly omitted book assets.
The [replay record](final-detached-replay.json) contains the exact invocation.

| Final artifact | SHA-256 |
| --- | --- |
| Canonical result JSON | `96a9a6a3542610d840331b87b1d89ab65932c3b5082598f7065000fd612ee269` |
| Runnable reproduction ZIP | `aa686dfd6eecb6cbaa13e3c64eeae1ec15513b03c105d953daeb37a60fa36f46` |
| Final detached result | `17f3dbe8954978823a0dde979fe1429929487b090eccd09edfab74a9d4031abd` |

The generated HTML has twelve valid local/anchor links, and its inline
JavaScript passes a syntax check. This is [static verification](final-static-site-verification.json);
browser layout and interaction remain unverified under the existing local
listener and browser URL restrictions.

[Machine closeout evidence](closeout.json) and the separate
[closeout inventory](closeout-evidence.json) record the final artifacts and
copied verification files. The 127-entry pre-commit evidence inventory remains
unchanged. All 953 original tracked-file hashes still match the source
inventory; both original worktrees remain clean at their original heads, and
those heads remain reachable in the integrated history. All 396 local LFS
objects and 412 materialized LFS paths match their SHA-256 identities. The
canonical monograph source/PDF, historical companion and scientific data
corpus retain their original bytes.

Git integrity is checked using both exit status and diagnostics. The
pre-closeout check returned exit zero but reported AppleDouble sidecars;
it was correctly treated as a failure. Removing 209 files with verified
AppleDouble headers inside this new checkout's `.git` directory produced a
diagnostic-free `git fsck --full`. The [cleanup receipt](checkpoint-git-metadata-cleanup.json)
records every removed path/hash/header and unchanged genuine sibling. No
original repository or genuine Git object was removed. The final documentation
commit can create more sidecars, so its final HEAD, clean status, any further
verified cleanup and diagnostic-free fsck are recorded outside the checkout at
`execution/numerical-correctness-2026-10-31/final-post-commit-verification.json`.
That external receipt avoids a self-referential commit/cleanup cycle.

The integrated suite recorded **393 passed, 18 skipped, four failures and nine
collection errors, with zero warnings**. The failing/error/skip node IDs match
the prior checkpoint: missing Gymnasium/Hypothesis block those tests, and
pynauty cases skip. Wheel/sdist inventories, the minimal installed core,
independent precision and angle references, schema-v2 service contracts, and
the preserved v1 fixture pass their checks. These are local dependency-copy
checks, not fresh online resolution or complete supported-platform coverage.

This checkpoint does not certify global geometric realization, exact numerical
volumes, every optimizer path, the entire research corpus, or monograph proofs.
The historical geometry refiner, H⁴/H⁵ and Torch algorithms retain their
separate audit scope. Whole-book claim review and modularization, missing Airy
and torus evidence, browser/GUI/platform checks, licensing and publication
remain future work. No remote is configured; no push, package release, tag or
Sites deployment was performed.
