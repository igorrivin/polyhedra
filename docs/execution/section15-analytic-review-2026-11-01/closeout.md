# Section 15 revision closeout

The revised Section 15 gives a scoped proof of the additive Airy expansion
and first correction for the specified pole-cleared regular-family Barnes
integral with upward measure `dw/i`, fixed bounded real transition parameter,
and `b` tending to zero. It separates fixed-b contour relocation from
uniform estimates on a centered scaled strip; corrects the linear subtraction
in the cited Gamma integral; fixes the phase constant through the real
Murakami-Yano formula and the shrinking-volume limit; and supplies explicit
whole-contour, tail, localization, and integrated-remainder estimates.
The resonance conclusion is limited to sufficiently small `b` in fixed
bounded physical windows. The independent review checked the cited primary
source statements; it did not reprove those external theorems.

The first analytic approval covers the chapter/13-claim ledger before the
numerical supplement. A separate delta review binds the final chapter and
14-claim ledger and confirms that the analytic prefix, interpretation suffix,
old proof fields, statuses, and source pins are preserved. All 607 manuscript
labels, 21 Section 15 labels, and 129 bibliography keys remain in their
original order. No other canonical chapter changed.

Baseline: `3ddf610dbe4578c7828e55f4e9cd92aacaba6df6`.
Source commit: `9f5b17aa34dd3ede7ae0b26d80b3b14d52111042`. It is the baseline's direct child and changes
exactly 12 approved paths: eight existing source/document files and four
new evaluator files. Staged byte hashes matched the final approvals and
`git diff --cached --check` passed without whitespace exceptions. The source
checkpoint has 1,855 tracked paths and a clean index/worktree with no remotes.
The artifact commit must be the source commit's direct child. Its actual
HEAD is recorded only in an outer verification receipt, avoiding a committed
assertion of its own identity.

The new evaluator computes the exact cleared Barnes integrand through
combined centered double-sine logarithms. The leading dilogarithm primitive,
finite cotangent correction series, rational series bounds, outer quadrature,
tail diagnostics, and comparison-only Airy column have distinct roles.
The independent code review checked normalization, centered shifts,
branches, finite coefficients, direct-integral origin limits, and algebraic
tail subtraction. Its separately written reference combines the original
whole Barnes log integrals and uses SciPy QUADPACK, with no author evaluator,
dilogarithm D expansion, or Airy input. Some parameter arithmetic still shares
mpmath, and both implementations use uncertified floating-point quadrature.

Review found and repaired odd-cutoff panel bookkeeping, a polynomial guard
that disappeared under optimization, package-import behavior, and incomplete
source/HEAD drift checks. The 26 focused tests and Ruff passed. Independent
targeted acceptance passed 13 contract checks and 28 direct special-function
checks at both 40 and 60 dps; a separate final-source smoke run succeeded.
The historical odd-cutoff before observation is preserved in the reviewer
report, with the stated `-0.0026948522550` residual. No standalone raw before
record survives in the outer evidence. The after record is an actual
executed quadrature, not a reconstructed or relabeled earlier result; its
shorter integral is also compared to an independent reference.

Actual failed diagnostics are retained. The initial full direct-D check
failed at 60 dps before panel refinement. Later alternate Gauss-Legendre
quadrature still differed from the bounded series by roughly `2.3e-46` while
reporting an internal error near `1e-66`. Tanh-sinh and higher-precision
comparisons give separate successful observations. The added rational
direct-D tail bound concerns a tail included in an integral over
`[0,infinity)`; it is not presented as an omitted-tail quadrature error.

The fresh full run was executed after the clean source commit and wrote
exclusively to the outer execution directory. Both internal source snapshots
and surrounding command snapshots record the same clean HEAD and seven
scientific source hashes, all matching committed bytes. It completed 21
whole-integral settings across seven parameter points, seven comparisons,
and 28 direct checks at each of 40 and 60 dps. The strict comparison requires
exact equality of all 21 row objects after removing only
`rows[*].elapsed_seconds`, exact equality of seven comparison objects, and
exact named equality of all 27 shared direct-check records per precision.
The extra tanh-sinh record is checked separately. The other excluded
component-container field is
`independent_double_sine_checks[*].elapsed_seconds`; run timestamps, source
states, and the added quadrature convention are explicitly recorded.

The final displayed quantum values are finite numerical evidence for this
integral, with no claim to an interval enclosure or a guaranteed number of
correct digits. The first quantum value is `0.459086488736078952...` and
rounds to `0.459086`; the new-minus-historical difference from `0.459087` is
approximately `-5.11263921048e-7`. The other five historical values agree after rounding,
and the negative-continuation input gives `0.517966671856531011...`.
All seven independently computed whole-integral reference values agree
within `1.80e-12` observed difference. The fresh result and exploratory
full-v1 record remain separate artifacts with their actual source identities.

| Canonical artifact | SHA-256 |
| --- | --- |
| `artifacts/section15_quantum/result.json` | `b8d600a6ca3797f45e616bc324d0d1620066e9c203c085229d4c544f6e245009` |
| `artifacts/section15-analytic-review-2026-11-01/monograph-working-draft.pdf` | `d299e1883c2aaae5e4b4cfabae42368c1e6fd645a04563e85a53d94f5d31d7ed` |

The 187-page PDF is the exact reviewed precommit output, copied unchanged.
Its 18 frozen active inputs were checked against the actual recorded TeX
input graph and later against the source commit. The full build converged
on 607 labels and 129 citations, with no unresolved/duplicate references or
overfull boxes. One inherited Section 9 underfull-box notice and the
expected shell-escape-disabled package warning remain recorded. The reviewer
actually inspected 23 pages, including all Section 15 pages 73-79, adjoining
pages 72/80/81, contents 2-6, List of Figures 7, and bibliography 181-187.
The other 164 pages were not visually inspected in this pass.

The [copy manifest](evidence-copy-manifest.json) records 52 exact
evidence copies, two canonical artifact copies, and explicit omissions.
The earlier Section 15 table/check artifact, all prior artifacts and site
exports, 1,843 protected baseline files, 412 materialized LFS files, and
953 files in the two original repositories retain their bytes. The original
ZIP and supplied reference PDF remain unchanged. Git integrity checks leave
the two pre-existing harmless dangling blobs untouched. Any actual metadata
sidecar cleanup, if required, has its own narrowly scoped receipt and outer
byte backup; no genuine Git object or original-repository metadata is removed.

Candidate and final verification are separate from the fresh computation,
PDF build, analytic review, and visual inspection. The maintained verifier
checks both phases with explicit exceptions that remain active under `-O`,
and writes exclusive receipts outside canonical. Independent checkpoint
approval precedes the artifact commit. The local source/artifact checkpoint
used no network, browser, remote creation, upload, deployment, or publication.
Earlier primary-source access is described in the retained review records.

Broader-shape and unbounded-parameter quantum extensions remain open research
directions. The original evaluator/raw run remains unrecovered; the new
exact-integrand evaluator and fresh full replay provide the replacement
reproduction route. These research extensions and original-run recovery are
not publication prerequisites. Remaining revision work includes further
chapter review, optional-dependency coverage, resolution of the documented
length-8192 torus campaign status, HTML/browser checks, and final publication
metadata/licensing. Upload remains the final publication step.
