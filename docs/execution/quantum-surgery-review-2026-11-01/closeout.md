# Quantum and surgery revision closeout

Sections 12–14 and 16 now have modular canonical sources, 56 claim groups,
independent mathematical and implementation reviews, and a finite exact and
multiprecision companion. The review retains the principal numerical factors
while making the hypotheses and limits explicit.

In the quantum chapters, the revision rescales Goldman, peripheral and
torsion forms together; supplies the second Hermitian period-pairing
coefficient argument; preserves both Plancherel square roots and the reflected
infinity label; and separates the finite sine operator and local classical
fold from the unproved spectral residue/contour interchange and from
Section 15's separate global quantum Airy argument, which remains outside
this review. The continued Gram signature alone does not establish geometric
realization; the required cofactor condition remains visible.

In Section 16, multiplier logarithms are distinguished from SL2 eigenvalue
logs, with the factor-two filling equation and nonlinear coefficient
conversion explicit. The full positive angle tangent and peripheral rank
hypotheses support the Hessian response. A uniform local inverse controls
bounded angles and long slopes; geometric cone completion is a separate
claim. The local volume/action identity, sixth-order series and canonical
covariance are retained. Torsion signs, square-root phases and regularity are
specified. The global quantum transfer stays conditional, while the actual
figure-eight RT/TV result is cited as an external special-case theorem.

Baseline: `bf260eaab047d9047602ece652e5a7e43625d3f6`.
Source commit: `514bc30b0d86a0a38b2ede1cb9dfb261a6b2995a`.
Exactly 20 approved source/document paths changed: six existing paths and
fourteen additions. Its parent is the baseline. The subsequent artifact
commit must be its direct child; the outer postcommit receipt records its
actual HEAD. No committed file asserts its own final commit hash.

The initial extraction reconstructs the baseline manuscript byte for byte.
All 607 existing labels remain unique and in their original order. The new
ledgers cover 30 quantum and 26 surgery claim groups. Main-source changes
beyond extraction are explicitly recorded bibliography changes. Staging found
exactly four inherited blank-at-EOF notices in the new chapters. Their exact
line locations, approved hashes and unchanged terminal bytes are in the
[exception record](checkpoint/source-whitespace-exceptions.json). No blanket
whitespace exclusion or alteration of approved source bytes was used.

Independent review exposed a finite-matrix guard defect: `max` could ignore
a later NaN and record residual zero. Only `periods.py` and its regression
test changed. Every actual, expected and difference entry is now checked for
finiteness before scaling. Independent before/after evidence shows six of
24 invalid matrix cases formerly passed and all 24 now reject. The focused
regression also covers scalar/vector positions, complex nonfinite values and
overflow in finite native-scalar subtraction. All 15 focused tests and Ruff
pass; the finite mathematical outputs and recorded residuals are unchanged.

The corrected companion passes 192 exact identity checks, 300 numerical
checks at 60/90 decimal digits and 72 cross-precision comparisons. The
independent code review adds 96 exact/guard checks, 34 numerical checks and
26 checks at two additional cut-plane points. Independent quantum
mathematical probes add 36 exact checks and 40 numerical comparisons;
independent surgery probes add 36 exact checks. These finite observations
do not certify infinite tails, geometric realizations or interval bounds.
Numerical formulas share the mpmath backend where documented.

The final result was freshly generated with Python 3.12.11 from the clean
source commit, writing to a new outer path before any evidence was copied
into the checkout. Both `source` and `source_at_completion` record
`git_dirty: false`, empty status and the correct source commit. Their exact
13-file hash/size lists agree with the approved source and committed blobs.
The [comparison](clean-source/scientific-comparison.json) matches every other
JSON field against the corrected independent `replay-result-final.json`.
The only exclusions are `/generated_at_utc`, `/elapsed_seconds`, `/source`
and `/source_at_completion`; provenance is checked separately. Initial dirty
author and reviewer results remain historical, not relabeled as clean runs.

| Artifact | SHA-256 |
| --- | --- |
| `artifacts/quantum_surgery/result.json` | `accdcaae347f363f20761cc2ffc7a2a252c2199787a277e519cef9978c5578cf` |
| `artifacts/quantum-surgery-review-2026-11-01/monograph-working-draft.pdf` | `f62a96cc99b6ccfd173b5667d97f6baa7d921f040058b6b7c2a5345b609e9846` |

The PDF has 186 pages, 607 resolved labels and 129 bibliography items, with
no undefined/duplicate references or citations, missing characters or
overfull boxes. One inherited underfull warning in unchanged Section 9 is
retained; its page 31 was visually checked and is readable. The expected
no-shell-escape epstopdf warning required no conversion. All 25 existing
site/build tests pass. The reviewer actually opened all 56 selected page
images: 1–7, 9, 31, 52–74, 77–93 and 180–186. This is selected-page layout
review, not a visual or mathematical review of the entire monograph.

The saved PDF is the exact inspected precommit build. All 18 active TeX
input hashes match the committed source. No clean-source PDF rebuild,
postcommit visual inspection, browser review or publication is asserted.
The 48 curated evidence files are byte-only copies. AppleDouble
sidecars, PNGs, caches and redundant snapshots remain outside the canonical
evidence allowlist. Historical author freezes are retained together with
the path-only ledger correction, NZ Section 6 citation correction and
nonfinite-guard correction records.

The verifier accounts for all 1,782 baseline tracked paths. The 1,776
protected paths, including 412 materialized LFS files, preserve their bytes.
Both original repository heads remain ancestors; their 953 original tracked
files, received ZIP and supplied reference PDF preserve their identities.
Earlier Section 9/site downloads and Section 15/30/normalization results and
PDFs remain unchanged. The candidate/final verifier checks source-to-artifact
direct-parent ancestry, the exact artifact allowlist, links and Git integrity.
Its receipts remain outer; harmless dangling objects are not deleted.

Before the candidate freeze, Git integrity checking identified 30 generated
AppleDouble sidecars inside the canonical `.git` directory: 29 object
sidecars and one branch-ref sidecar. Each fsck-named file was backed up byte
for byte and its AppleDouble header, entry table and bounds were verified
before removal. All genuine counterparts and both dangling blobs were
preserved; Git status was unchanged and the subsequent `git fsck --full`
passed. The outer `execution/quantum-surgery-review-2026-11-01/` directory
retains `git-metadata-cleanup/receipt.json`, the byte backups and pre/post
output. The receipt SHA-256 is
`fc2ad874ca271c7f2db1aa8b1e3b029eb131fb6f3e3c4676994fee69a46f71dc`.
The checkpoint verifier itself performs no metadata cleanup.

The next substantive work is Section 15's global contour, tail and uniform
remainder analysis. The original exact quantum-integral evidence and
length-8192 torus campaign remain unrecovered/unreplayed. Remaining chapters,
optional dependencies, HTML/browser review, metadata, authorship and licensing
are still separate work. This local checkpoint performs no upload, push,
remote retry or Site publication.
