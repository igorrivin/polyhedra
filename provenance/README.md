# Source provenance and restoration

`source-map.json` records the original source heads, exact subtree identities, unsquashed import commits, destination paths, and original archive hash. The archived source heads are ancestors of `main`; the original files at those import commits can be recovered without reconstructing their history from a squashed snapshot.

The imports were made with the documented [Git merge-subtree workflow](https://github.com/git/htmldocs/blob/gh-pages/howto/using-merge-subtree.html): merge the original head with the `ours` strategy without committing, populate a prefix with `read-tree`, verify the staged subtree identity and every materialized file hash, then commit. No source history was rewritten. Local source refs are retained under `refs/archive/toolkit/` and `refs/archive/ipoly/`; no external repository was created or pushed.

## Backups

The separate local backup directory is `../integration-backups/2026-10-31/`, relative to this repository root. It contains complete-ref Git bundles, all 396 available toolkit LFS payloads, the original monograph ZIP, hash manifests, and command records. `backup-manifest.json` in this directory is a tracked copy of its manifest. Git bundles do not contain LFS payloads.

Both bundles were verified and restored into fresh temporary checkouts with their LFS payloads. All 925 toolkit and 28 ipoly tracked files matched the original SHA-256 inventory, and `git fsck --full --no-reflogs` passed in both restored checkouts. Source branch heads remained unchanged and worktrees were clean. The temporary restoration checkouts were removed after verification; the backups and original repositories remain.

To restore, clone the relevant bundle with `--no-checkout`, copy its backed-up `lfs/objects` content into the restored `.git/lfs/objects`, then check out `main`. Compare file hashes to `audit/2026-10-31/source-inventory.json`. Use an ordinary local filesystem for restoration; the Lexar filesystem can generate AppleDouble `._*` sidecars which Git mistakes for indexes, refs or loose objects. Only verified AppleDouble sidecars created in the new checkout were removed during import; no original repository was modified.

## Monograph and audit

The received ZIP is retained in `archives/`. `monograph/member-map.json` records the destination and hash of all 39 members. Twenty-five companion files are represented by the identical `research/ipoly` files. The main TeX, editable figure copies and supplied PDF were copied without mathematical edits. The original package README and checksum list retain their original meaning as archive records, not as a checksum list for the reorganized directory.

The planning audit is retained under `audit/2026-10-31/`. Its inventory and observed numerical results describe the original sources, not later corrected code. `audit-adaptations.json` records the explicit-path update that makes the probe script runnable from this monorepo.

## Scope

This is local preservation and integration evidence. It is not remote-visibility verification, remote CI, complete numerical replay, a proof audit, or publication. The existing source contains trailing whitespace; source-import commits deliberately preserved those bytes. Subsequent authored changes are checked separately.
