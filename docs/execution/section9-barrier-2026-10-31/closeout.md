# Section 9 barrier implementation closeout

The dense affine-angle solver, three reproducible examples, and the chapter's
computational addendum are now integrated locally. The solver separates initial
centering from short-step path work, checks feasibility and the freshly evaluated
Newton decrement, and reports explicit unsuccessful outcomes. Its finite-gap
values remain numerical estimates with `certified: false`.

The local source commit is `c1f100b957166b93eca0d214586322d5af71b9cf`; the generated-artifact commit is
`4823348bbd1593d8cade4d0a038531f80a97a676`. Both numerical reports and the strict chapter build record the
source commit with a clean checkout at execution. All five generation/render
steps preserved that clean state. [Exact commands](final-generation-location.json),
[checks](final-generation-checks.json), and the [46-file artifact manifest](final-artifact-manifest.json)
record the final bytes after both backlink refreshes. This document belongs to
the subsequent documentation commit; its exact SHA and final integrity checks
are in the external postcommit receipt described below.

The [barrier companion](../../../site/section9/barrier.html),
[chapter HTML](../../../site/section9/chapter.html),
[chapter PDF](../../../site/section9/downloads/section9.pdf), and
[barrier reproduction ZIP](../../../site/section9/downloads/barrier-reproduction.zip)
are current local outputs. The PDF hash is
`9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0`. All ten rendered pages are byte-identical to
the layout independently opened and approved during review. The chapter retains
209 MathML expressions, both figures, its 26 labels and the full monograph's
607 unique labels. Static local-link checks pass; these are not browser tests.

Both final numerical ZIPs were extracted outside the checkout and executed
from unrelated working directories with the existing minimal interpreter and
no PYTHONPATH. Actual toolkit imports resolved inside the respective extracted
bundles and matched their payload hashes. All result fields except execution
provenance exactly match the final source runs; detached Git fields remain
unavailable while the clean origin is retained. The
[fresh replay record](final-detached-replay.json) is separate from archive/hash
verification and from dependency installation, which was not attempted.

The boundary example has observed high-precision volume gap about `3.52701e-5`,
below its numerical finite-iterate estimate `7.05981e-5` and requested `1e-4`.
The triangle and asymmetric disk agree with independent reference maxima.
All 54 recorded checks pass; that count includes status and provenance-related
checks, not 54 independent mathematical proofs. Exact-space references and
literal binary64-input stationary references remain distinguished.

The [core review](barrier-review.md), [publication/addendum review](barrier-publication-review.md),
and [strict preview approval](barrier-strict-preview-review.md) retain exact
approved hashes. Final core tests passed 43 cases (32 barrier and 11 existing
variational tests), and five independent numerical probe groups passed. The
experiment/export suite passed 27 tests with 29 subtests before the narrow
zero-dimensional status fix; corrected-core source and detached executions
subsequently matched all three case records exactly. Offline wheel/sdist and a
new-target installed-wheel probe passed the final module bytes using existing
dependencies. Those were preliminary working-tree package checks, not a newly
resolved environment or a clean-source release-wheel build.

The one complete package run had 423 passed, 18 skipped, four failed and nine
collection errors on the preceding core hash `ea73137f...`. Its nonpass
identities and messages match the prior baseline: Gymnasium and Hypothesis are
unavailable, and pynauty-dependent cases are skipped. The later solver change
was one reporting assignment for a zero-dimensional domain; its two new
regressions and focused tests passed. A final-source full-suite pass is not
claimed. The [full-suite comparison](review-full-suite-comparison.json) retains
the exact evidence.

Canonical copying preserved every verified byte. One obsolete generated
inspection copy of the prior companion probe was removed because it no longer
belongs to the strict export; its original frozen checkpoint source remains
untouched. [Copy identities](final-copy-manifest.json) and
[artifact staging checks](artifact-staging-verification.json) record this.
Two checkpoint-helper mistakes were corrected without changing product code or
numerical results; the [history](checkpoint-harness-history.json) preserves them.
The actual final artifact staged-whitespace check passes with empty diagnostics.

Only this new checkpoint's README and closeout records change during the
final documentation step; all frozen numerical/publication source hashes remain
unchanged. The parent independently checked all 46 canonical outputs and all
953 original tracked files, original repository heads and ancestry, original
archive and supplied reference PDF. The
[postcommit verifier](final-postcommit-verification.py) checks the final commit
chain, current source/artifact hashes, originals and clean Git state. It may
remove only header-verified AppleDouble metadata under the new repository's
`.git`, recording the unchanged genuine siblings. Its receipt is kept outside
the repository at `../execution/section9-barrier-2026-10-31/final-postcommit-verification.json`
(relative to the repository root), so recording the final HEAD does not require
another recursive commit. The verifier records ordinary `git fsck --full` with normal reflog reachability:
exit zero and empty stderr are required, while informational dangling-object
notices are classified and their exact objects preserved outside the checkout.
It then requires `git fsck --full --no-dangling` to exit zero with empty stdout
and stderr. No genuine objects are deleted or archive refs created to suppress
notices. Metadata cleanup batches are accumulated, so the earlier 197 verified
sidecar removals remain recorded after the final check. The initial unpublished
closeout and checker are retained in the external amendment history.

No public Site, remote repository, push or external publication was created.
The implementation does not supply a nearly-linear backend, a scaling law,
rigorous floating-point error enclosure, peripheral-holonomy solver, or global
geometric realization certificate. The rest of the monograph has not thereby
received a full proof audit.
