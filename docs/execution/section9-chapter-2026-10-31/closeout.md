# Section 9 chapter and computational companion closeout

Date: 31 October 2026, America/New_York.

The reviewed Section 9 source and publishing tools were committed as
`1bafb83d2ec152f1f8eac75b2be0e3c4b796198e`. The final numerical computation,
chapter build and render-only link refresh all ran from that clean source
commit, with their outputs outside the checkout. The separately verified
artifact commit is `a69e47346209fff04c94062552af5400d3d5da05`, recorded in
[artifact-commit.json](artifact-commit.json). The final documentation commit is
identified by the separate final postcommit receipt; neither later commit is
the computation origin.

## Delivered artifacts

- [Complete Section 9 HTML](../../../site/section9/chapter.html), including
  proofs, figures, references, and the 26-claim coverage table.
- [Ten-page chapter PDF](../../../site/section9/downloads/section9.pdf).
- [Complete monograph LaTeX source ZIP](../../../site/section9/downloads/monograph-source.zip).
- [Worked numerical companion](../../../site/section9/index.html),
  [result record](../../../artifacts/section9/result.json), and
  [detached reproduction ZIP](../../../site/section9/downloads/section9-reproduction.zip).

The [artifact manifest](final-artifact-manifest.json) records all 34 exported
files, including the result record, after the final render-only refresh.
The [copy manifest](final-copy-manifest.json) verifies their canonical copies
and the accompanying evidence. Selected SHA-256 values are:

| Artifact | SHA-256 |
| --- | --- |
| Chapter PDF | `a5b684f086fad6d0249da7cfc2a1fcf98b5eb193927614dc98baa1ab2cfc6e61` |
| Chapter HTML | `b43ed517a4542442236edb16110a78730d53301df33104898dfd03b4e9df308a` |
| Numerical result | `66fdc288483c07a30930714c97eb59c70c0be92566eaba9437fc7f4d10707a61` |
| Monograph source ZIP | `5a1d5a306a0504ebf5a0e8b46ba0ea6c9d2a664ba5fedc702ae748cd114b993b` |
| Numerical reproduction ZIP | `c6071e1681af10c79655d7446f8cf3414cf253bb1003e04a18f21cb62fdd8bcf` |

## Verification and its scope

The [fresh-generation checks](final-generation-checks.json) verify clean
origin metadata, every reviewed source hash, the explicit computation result,
both HTML pages and all numerical/source ZIP payloads. All twelve numerical
checks and exact finite identities pass: determinant `60`, rooted-forest sum
`15`, and Schur entry `15/2`. The extracted numerical bundle was freshly run
outside the repository in the existing minimal NumPy/SciPy/mpmath environment.
Every mathematical report field matches the source run. Detached Git status
and optional book assets are honestly unavailable, and originating provenance
is retained. See the [detached run](final-detached-run.json) and
[detached result](final-detached-result.json).

The final build has 607 full-book labels, including all 601 original labels;
26 chapter labels; 209 MathML expressions; two figures; twelve selected
references; and ten PDF pages, with no overfull boxes or unresolved references.
Equations 16.7 and 16.8 are explicitly reference-only and outside this chapter's
mathematical review. The [static artifact checks](final-artifact-static-checks.json)
verify local HTML/PDF links and internal PDF targets. All ten final page PNGs
are byte-identical to the pages visually inspected by the parent and to the
independently verified strict preview. The [visual comparison](final-visual-comparison.json)
records this layout identity; PDF metadata bytes naturally differ by build.

The publisher freshly compiled the full manuscript and standalone chapter.
All seven payloads of the final source ZIP are byte-identical to the strict
preview ZIP payloads that the independent reviewer extracted and compiled
outside the checkout: 177-page full book and ten-page chapter. Only the ZIP's
origin manifest changes for the clean source commit. This is payload identity
verification against an earlier extracted build, not a claim of another fresh
extracted-source build. A full-book compilation is not a full-book proof audit.

The independently reviewed source passed 25 focused tests before the source
commit. No package implementation changed during this increment, so the full
suite and wheel build were not repeated. The missing optional dependency/DNS
limits remain as recorded in the checkpoint README. No browser/server retry,
public upload or remote push was performed. Browser layout and interaction,
broader chapter review, missing Airy/torus evidence, text licensing/credit and
Sites publication remain separate work.

## Preserved execution history

The initial audits, revised-source reviews, failed conversion probes and dirty
previews remain unchanged. Source staging matched the reviewed hashes and only
the exact enumerated archival/reviewed-source whitespace exceptions; this is
not an unqualified `git diff --check` pass. The final generated inspection
copies preserve those bytes as well.
The generated HTML also retains Pandoc's single-space blank line 42, identical
to the independently reviewed preview. This exact additional preservation
exception was explicitly accepted and is recorded in
[artifact-staging-verification.json](artifact-staging-verification.json).

The local release/check scripts saved here use deliberately pinned checkpoint
paths. They are inspection evidence, not portable entry points; the maintained
[build guide](../../../site/README.md) supplies the reusable commands. A first
ad hoc final checker assumed the wrong exact-fixture field name and stopped
before copying any artifact. Its original script and corrected disposition are
preserved in [checker history](final-generation-checker-history.json). The
product source and numerical report did not change to satisfy that correction.

Git metadata cleanup and the final exact-HEAD verification receipt are retained
outside the checkout under `execution/section9-chapter-2026-10-31/`, avoiding a
self-referential commit cycle. Only verified AppleDouble metadata created under
the new consolidated `.git` is eligible for that cleanup; the original source
repositories and their genuine files remain untouched.
