# Sites reading preview closeout

The Section 9 reading preview is complete as a local, reviewed presentation
increment. It has a contents page, local passage search and navigation between
the chapter and its two computational companions. The [candidate archive](../../../artifacts/sites-preview/polyhedra-sites-preview.tar.gz)
is ready for the supported Sites workflow when source synchronization becomes
available. It has not been saved or deployed to Sites.

The clean research source commit is
`e79d4cee5b9fd7f999054617406ecebb1b9677cd`, directly after baseline
`800219f78bdacaf77639cf4d38ff27d4b7342faa`. The separate artifact/closeout commit
follows it; its final HEAD and postcommit checks are recorded outside the
checkout in `../execution/sites-preview-2026-11-01/final-postcommit-verification.json`.
The [verifier](final-postcommit-verification.py) avoids recursive final-HEAD
records in committed documents. The original source review is retained unchanged.

The [independent source review](independent-review.md) approved the final nine
source hashes with no unresolved finding after the path, symlink and explicit
index-link corrections. It ran 25 site tests, pure search assertions and six
real-edition queries, and checked all 473 local/search targets, 204 passages,
209 MathML nodes, two figures and the six subsections. The two new presentation
inserts can be removed from each derived chapter/companion HTML file to recover
its frozen input byte for byte. Initial failures and correction evidence remain
in the [source evidence inventory](evidence-copy-manifest.json).

The [final clean export](final-export-verification.json) records the source
commit above with `dirty: false`, separately from numerical source commit
`c1f100b957166b93eca0d214586322d5af71b9cf`. Its 48 payload files match the approved
draft; the 49th file is the clean-source preview manifest with SHA-256
`457f11d89ca415095ab80906abd501e014afc187744f6b70a3effcb42585f1dd`.
The final link/target and search checks passed while the research checkout
remained clean. All 46 scientific inputs retain their frozen bytes, including
PDF SHA-256 `9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0`.
No numerical replay, scientific export, PDF build or PDF inspection was repeated.

The [generated metadata record](final-dist-metadata-cleanup.json) preserves the
paths, headers, hashes and sibling identities for 68 AppleDouble sidecars removed
only from the generated mirror `dist`. Genuine payload hashes were unchanged.
The actual directory contained exactly 49 ordinary files before packaging; no
symlink, extra payload, Git directory or metadata sidecar remained there.

The root agent ran the [official offline packager](offline-package-command.json)
with `COPYFILE_DISABLE=1`. Its unchanged 2,778,427-byte archive has SHA-256
`9425c791ecb0f7d88f91aae8b19dfb7d30c6526446b103cf6415e79734007cd1`.
Both the [parent check](parent-offline-package-verification.json) and the
[independent archive inspection](final-archive-verification.json) verified the
actual 71 tar members and 50 regular files: all 49 clean-export files plus the
official minimal `dist/.openai/hosting.json`. Validated files were safely
extracted outside the checkout and rehashed. There are no duplicate, traversal,
symlink, hardlink, extra-payload or sidecar-file members. The normalized hosting
manifest identifies the existing project and `static.directory: dist`.

The official macOS archive retains `mtime`,
`LIBARCHIVE.xattr.com.apple.provenance` and
`SCHILY.xattr.com.apple.provenance` PAX headers. Their value hashes are recorded;
these format headers are not claimed absent. The parent's first checker rejected
all xattr headers too broadly; its [correction history](parent-package-check-history.json)
is preserved. The corrected checks permit only these exact three keys. The
official archive was not rewritten or stripped.

The existing Site is `appgprj_6ae6b5b94abc8191aa00dfe244adcf37`, titled
*Polyhedra, Moduli, and Quantum Geometry*. The [fresh native observation](native-sites-state.json)
after packaging confirms owner role, custom access, one allowed owner, zero
groups, version zero, and null live/preview URLs. Registry status `active`
means registered. The official source-open helper failed with exit 128 because
`git.chatgpt-team.site` could not be resolved. It initialized an unborn mirror
Git checkout but performed no source push. There is no Sites source commit,
saved version or deployment; the research source SHA is not a substitute.
No token, credential, bypass secret or authentication header is retained here.

After actual network recovery, reuse the same project ID. Re-read Site access,
obtain a fresh source write credential, and run the supported source workflow
in the existing derived mirror. Verify the resulting source push and package,
then save/deploy the exact candidate privately while access remains owner-private.
Do not recreate the Site or present its expected registration URL as live.
Browser rendering, interaction and accessibility checks remain unperformed;
static checks and safe archive extraction do not establish those outcomes.

The final verifier checks the nine reviewed source hashes, 46 scientific files,
953 original tracked files, original repository heads and ancestry, original
archive and supplied reference PDF. All scientific, history, original-source
and earlier-checkpoint trees remain unchanged. Only the root README gains a
navigation link to this checkpoint. No canonical Git remote or push was added.
If new canonical `.git` sidecars exist, the verifier removes only header- and
table-verified AppleDouble files and records cumulative batches with unchanged
genuine siblings. It requires ordinary `git fsck --full` to exit zero with
empty stderr, preserves informational dangling objects, and then requires
`git fsck --full --no-dangling` to have empty diagnostics. No genuine objects or
refs are deleted to suppress notices. The final receipt records the results.
