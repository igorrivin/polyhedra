# Monograph revision closeout

Sections 15 and 30 now have separate canonical sources, explicit computational
status, claim ledgers and runnable finite companions. The revised plan places
upload/deployment after the remaining manuscript work and local release gates.

Source commit: `cf34fcbcd0ee867a2dee974d9c952238bc5c6ce6`.
Baseline: `df952174e55f08a52596d912d9713a9d1e116313`.
The final artifact/closeout commit is recorded by the postcommit receipt at
`../execution/monograph-revision-2026-11-01/final-postcommit-verification.json`
relative to the repository root. The committed verifier checks that it is
the direct child of the source commit and that all sixteen approved source
hashes remain unchanged.

The original numerical rows are retained with corrected provenance. The Airy
integral values and the length-8192 torus campaign are explicitly unreplayed;
the claim that the missing torus diagnostic archive accompanies the book has
been removed. The new computations have their own inputs and run identities.
No original result was reconstructed from rounded table values.

Independent review approved 31 exact Airy checks, six approximation values at
80/120 digits, 16 torus regression tests, and the bounded replacement spectrum
of 1,104/1,127 curves through length 64. Additional reviewer probes covered
independent differentiation and cubic-contour integration, 816 matrix words,
1,485 exact-rational event cases and 4,437 conditional-bound perturbations.
The torus bounds assume both a per-length error radius and fixed curve
membership; neither assumption is certified. These finite checks do not
audit the full analytic proofs or establish asymptotic counting claims.

The two final records were generated from the clean source commit using
Python 3.12.11; the Airy run used mpmath 1.3.0. Both outputs were written
outside the checkout before either was copied into `artifacts/`, so both
truthfully record `repository_dirty_at_start: false`. Every scientific field
matches the corresponding independent replay after excluding only the
explicit provenance and timing paths listed in the comparison record.

| Artifact | SHA-256 |
| --- | --- |
| `artifacts/section15/checks.json` | `1b275fb776a7a203cfada670bf37d4a5c428a463e24edafb38ed0e8c258f8404` |
| `artifacts/section30/result.json` | `762b07184f76893c810f3e9832fd44dc7e4b292c1a64aae61aa26832e02884a1` |
| `artifacts/monograph-revision-2026-11-01/monograph-working-draft.pdf` | `44e428ddbc625231f483748a9bfce914b4d4fc987a0c34b6201003e6dc87cacd` |

The PDF is the exact precommit working draft already reviewed, copied without
alteration. All five TeX input hashes match the committed source. No new build
or visual inspection after the source commit is claimed. Its full build has
179 pages, 607 resolved labels and 126 bibliography entries, with no undefined
or duplicate references/citations and no overfull boxes. The single underfull
warning remains in the log. Pages 68–75 and 155–166 were visually inspected;
the other 159 pages were not inspected in this pass. The existing 25 site/build
tests also passed. Build success is not a full-monograph proof audit or browser
verification.

The two new chapter files retain their original extraction tails. Staging
therefore reported exactly two blank-EOF notices, at chapter 15 line 512 and
chapter 30 line 672. The approved bytes were preserved and those exact notices
were recorded separately from the earlier unstaged and trailing-space checks.
No general whitespace exclusion was applied. Any additional byte-preserved
evidence whitespace is separately inventoried before the artifact commit.

The source import, original histories and 953 original tracked files remain
protected. Earlier scientific outputs, Section 9 site files, source-download
snapshots and the supplied ZIP/reference PDF are unchanged. The final verifier
checks these identities, all new artifact hashes, source ancestry, local
links, clean worktree/index and Git integrity. Only verified AppleDouble
sidecars under the canonical `.git` may be removed, with genuine sibling
identities retained. Informational dangling objects are preserved.

The next substantive review covers Sections 1–8 measure normalizations and
their hypotheses. Broader proof review, an exact-integrand Airy evaluator,
recovery or separate full replacement of the long torus run, optional-dependency
test coverage, full HTML/browser checks, authorship and licensing remain open.
The prior optional-dependency-limited suite is not relabelled a pass. Upload is
the final publication phase; this checkpoint performs no remote operation,
HTML regeneration or Site action.
