# Independent integration review — 31 October 2026

Reviewed migration baseline: `c53387221dc6d000ac46c0b1ce44232c50f02a3c` in `consolidated/`. This review excludes concurrent numerical corrections and new Section 9 implementation work. The review made no changes to either source repository or the consolidated implementation, and performed no staging, commits, remote operations, or publication. Only this report and sampled PDF renderings were created in the outer execution directory.

**Result: no blocking migration defect found.** The checks below establish preservation and local integration. They do not establish that the existing mathematical claims are correct, that all numerical results have been replayed, or that the project is ready for publication.

## Preservation and import checks

| Check | Independently observed result |
| --- | --- |
| Source history reachability | Both original heads are ancestors of `c533872` (`git merge-base --is-ancestor`). |
| Exact toolkit import | Source `cc6b689652ce735f2098bb0a3235089210d764df` and subtree `4662e5996862a7f438728c4561363597ee76493d:packages/volume-toolkit` have identical tree ID `77de37c814ca7c562f0f2dd05bb3f7c138fe8d5c`. |
| Exact ipoly import | Source `30ef40e23005509bd94d26f27dc48ea778832a50` and subtree `b0119244ee0e62b33e3fa871975091e5775868a9:research/ipoly` have identical tree ID `94231c471e8b362a3181cddd5ec3ef0e261b09e0`. |
| Original materialized files | All 925 toolkit and 28 ipoly tracked files match the SHA-256 inventory. Both original worktrees remain clean. |
| Git object integrity | `git fsck --full --no-reflogs` passes in the consolidated repository. No nested `.git` directories or `160000` gitlink entries were found. Original refs are retained under `refs/archive/`. |
| Git backups | Both bundle byte hashes match `provenance/backup-manifest.json`; `git bundle verify` succeeds for each bundle. |
| LFS backups | All 396 payloads in `integration-backups/2026-10-31/ideal_poly_volume_toolkit/lfs/objects/` have the recorded size and SHA-256 OID. These payloads are separate from the Git bundles, as documented. |
| Received archive | Preserved ZIP SHA-256 is `8f28b07686ea579a7dfb7b88ccef5c12bdd50b6e328737d5a8a79f6e06ba92dc`, matching the recorded original. |
| Archive member mapping | All 39 members are represented exactly once: 14 copied and 25 deduplicated. Every destination has the exact ZIP member bytes and recorded hash. All 25 deduplicated companion members point to identical files under `research/ipoly/`. |
| Remote scope | `git remote -v` is empty. No remote operation was performed by this review. |

Exact import tree identity includes all tracked names, modes and Git blobs, including LFS pointer blobs. The materialized-file and LFS-payload checks address the data behind those pointers. The implementation's provenance also records fresh restoration checks of both bundles; this review independently verified the bundles and payloads but did not repeat those complete restorations.

## Integration code, CI, documentation and entry points

The migration-specific product change in `packages/volume-toolkit/scripts/check_data_integrity.py:90–107` correctly handles Git LFS paths reported relative to the monorepo root. It obtains the package prefix, includes only paths with that prefix, and removes the prefix before package-relative checks. An empty prefix retains standalone-repository behavior. The change does not alter scientific data or numerical algorithms.

The accompanying test at `packages/volume-toolkit/tests/test_data_integrity.py:38–45` corrects a stale exact count, asserts unique paths, checks that every returned file exists, and verifies LFS attributes. The actual checkout has 412 LFS paths. The focused checks ran against these files, which had no concurrent diff from `c533872`.

Root `.github/workflows/ci.yml` is the only active workflow location. Its toolkit jobs use `packages/volume-toolkit` as their working directory, install from that directory, and cover declared Python 3.10–3.14. The separate integrity job requires materialized data. Checkout requests LFS data; workflow permissions are `contents: read`. There is no active HF deployment, force-push, maintenance, package publication, or Site deployment step. Historical nested workflows remain inactive by location. Remote CI and full dependency resolution were not run in this review.

Local Markdown links checked in the root README, AGENTS, integration plan, book README, licensing README and provenance README resolve. Root development commands address the new package path and retain the `ideal-poly-optimize` entry point. The baseline environment's installed command returns help successfully from `/private/tmp`, without relying on the caller's source directory. This is an entry-point smoke check of the existing installed baseline, not a fresh wheel build. The historical Dockerfile still expects `packages/volume-toolkit` as its build context; its referenced input paths exist. No Docker build was run.

The monograph wrapper and book build paths are internally consistent. The supplied PDF is explicitly a reference artifact. Licensing documentation correctly distinguishes the toolkit MIT license from the unresolved text and ipoly distribution licenses. The imported toolkit's old project URLs remain historical until a destination remote exists.

The audit probe's path adaptation is explicit in `provenance/audit-adaptations.json`, including original and adapted hashes. Historical numerical observations remain identified as observations of the original sources. The preserved import whitespace and historical files were not treated as new code defects.

## Focused execution

From `consolidated/packages/volume-toolkit`:

```sh
PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR=/tmp/polyhedra-mpl-review-20261031 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  /tmp/polyhedra-baseline-20261031/bin/python -m pytest \
  tests/test_data_integrity.py -q -p no:cacheprovider
```

Result: **11 passed in 13.99 seconds**.

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/polyhedra-baseline-20261031/bin/python \
  scripts/check_data_integrity.py --require-materialized
```

Result: **412 LFS paths verified, 354 JSON payloads parsed, two canonical input hashes and two manifest artifacts validated; all required payloads materialized.** The broad numerical suite was not repeated as part of this read-only migration review.

## Sampled PDF inspection

Source: `consolidated/book/reference/polyhedral_volumes_and_geodesic_identities.pdf` (174 physical pages). This is the unchanged supplied PDF, checked by the archive member comparison above. Poppler was unavailable; existing `/usr/local/bin/gs` (Ghostscript 10.04.0) rendered the samples without installations or network retries. Page selection used existing pypdf text extraction. Command options were checked against the upstream [Ghostscript usage documentation](https://github.com/artifexsoftware/ghostpdl/blob/master/doc/src/Use.rst).

For each physical page `P` in `1 28 29 168`:

```sh
/usr/local/bin/gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r120 \
  -dTextAlphaBits=4 -dGraphicsAlphaBits=4 -dFirstPage=P -dLastPage=P \
  -sOutputFile=/Volumes/Lexar/lambda/devel/polyhedra/execution/2026-10-31/pdf-review/page-P.png \
  /Volumes/Lexar/lambda/devel/polyhedra/consolidated/book/reference/polyhedral_volumes_and_geodesic_identities.pdf
```

`P` denotes substitution of the selected page number. All four commands exited successfully. Each resulting image was opened and visually inspected:

| Physical page | Content | Sampled visual finding |
| --- | --- | --- |
| [1](pdf-review/page-1.png) | Title, subtitle, date and abstract | Text legible, margins intact; no visible overlap or clipping. |
| [28](pdf-review/page-28.png) | Section 9 coordinates, Hessian proposition, proof and Schur complement | Equation alignment, symbols, numbering and proof ending visible; no obvious glyph loss or overflow. |
| [29](pdf-review/page-29.png) | Cotangent figure, response and Gaussian formulas, forest determinant | Diagram labels and caption readable; formulas and boxed result fit the page. |
| [168](pdf-review/page-168.png) | Appendix B conventions table | Both table columns, wrapped mathematical entries, bottom rule and following paragraph are visible and legible. |

**Publication follow-up:** Ghostscript reported `CMap unrecoverably broken` followed by “errors were repaired or ignored” for pages 28, 29 and 168. Page 1 did not report that warning. No corresponding visual defect was apparent in these samples. This warning belongs to the supplied reference PDF and was not introduced by migration. A release build should investigate its font/character-map integrity and check text extraction and accessibility. This review does not identify the underlying PDF object or claim that all 174 pages render correctly.

## Nonblocking improvement

Add small focused cases for `list_lfs_paths` that cover an empty repository prefix, a nested package prefix, and exclusion of a sibling package's LFS path. The existing test exercises the actual nested checkout but does not explicitly exercise those boundary cases. The `>=407` assertion is a historical floor; document its rationale or use a deliberate required-path set if long-term artifact preservation is intended. Neither point caused a failure in the present 412-path checkout.

The next numerical and editorial phases remain governed by their own gates. This review does not clear existing P0 mathematical/status findings, missing Airy or torus evidence, complete PDF review, licensing, remote CI, or publication.
