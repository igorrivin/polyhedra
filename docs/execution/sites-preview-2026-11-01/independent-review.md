# Independent review of the Section 9 Sites preview

**Verdict: approved for the local canonical source checkpoint and subsequent clean offline export, on the exact source hashes in `independent-review-manifest.json`.** No unresolved defect remains in this bounded review. This is a software and artifact-integrity review, not formal certification, browser QA, deployment approval, or a mathematical audit of the whole monograph.

The reviewed baseline is `800219f78bdacaf77639cf4d38ff27d4b7342faa`. The author freeze is `author-final-manifest.json`, SHA-256 `b82c018dee070dffc79c63c918725547804e804933bc3a1063c3167447ea22e8`. The exporter is SHA-256 `d68aca41430476139464c2b4cd636024d5a0462e66161dfc372f3202049557c9`. All nine source hashes were independently checked against the current files before finalizing this review.

## Scope and reader claims

The landing page describes a Section 9 working edition, with six subsection links, the grid and barrier companions, numerical-result downloads, reproduction archives, and local text search. The full LaTeX source is explicitly labeled as a broader draft. No new author attribution or license is invented. Numerical evidence retains its numerical status; the presentation does not promote it to certification, whole-book verification, or proof of global results.

The code review covered the complete exporter, landing template, CSS, search JavaScript, ignore template, focused tests, and the corresponding publication-guide changes. Existing numerical code and scientific inputs were not edited or freshly replayed in this review.

## Independently executed checks

Exact commands, working directories, environment overrides, exit codes, and log hashes are in `review-command-manifest.json`. They used `/tmp/polyhedra-baseline-20261031/bin/python`, with `PYTHONDONTWRITEBYTECODE=1`, and Node `v26.12.1`.

- `python -m unittest discover -s site/tests -v`: 25 tests passed, including the previous publisher tests and the new preview tests.
- `python site/build_preview.py --output-dir <fresh outside-checkout temporary directory>/dist`: passed. The build records the dirty preview state rather than presenting it as a clean committed export.
- `node site/tests/test_preview_search.cjs <dist>/search-index.json`: 11 pure search assertions and six actual edition queries passed, with absent-query behavior checked.
- `node --check site/preview/search.js`: passed.

The separate `review-independent-checks.py` checker completed successfully; its results and exact command record are retained separately. It independently inspects files, parses HTML, resolves targets, compares bytes, and exercises the JavaScript search rather than relying only on the builder's validation report.

- All 46 frozen scientific checkpoint inputs match their recorded hashes.
- The fresh physical output has exactly 49 ordinary files, with no symlinks, metadata sidecars, `.git`, or environment-secret files. Its 48 payload hashes match the author's derived preview; the remaining file is the build manifest.
- Removing exactly the two declared stylesheet/navigation insertions recovers all three original scientific HTML files byte-for-byte. All 41 other scientific site files are unchanged.
- The PDF remains SHA-256 `9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0`.
- All 473 local links and search targets resolve to actual files and existing fragments. The checker does not silently translate directory URLs into index files.
- The chapter preserves 209 MathML nodes, 43 IDs, two figures, and all six subsection headings. Exact HTML restoration additionally preserves equations, anchors, tables, and mathematical content.
- The index contains 204 passages. Embedded JSON equals the downloadable index. Actual queries for Schur, asymmetric, flat triangle, Casson, lambda, and rooted forest return the expected chapter or companion sources; empty and absent queries behave correctly.
- The three unchanged downloadable ZIPs have 8, 10, and 11 entries respectively. Their inventories have no duplicate names, traversal, metadata sidecars, credentials, or holdout paths. The frozen input allowlist prevents unrelated research files from entering the ordinary export.
- Four output-symlink variants are rejected: a matching-content file, a dangling file, a directory, and the output root. External bytes remain unchanged.

The machine-readable result is `review-independent-checks.json`, SHA-256 `65079ea5eb93c243ac0dc99ab333262e4f6fbc2d4b528da40644740050ace32f`.

## Defects found and corrected

**Output symlink escape.** An earlier draft accepted an output file symlink when its target bytes matched the prior manifest, allowing a later write to follow the link outside the output. The scratch-only reproduction is preserved in `review-symlink-initial.json`; no maintained file was modified by that reproduction. The final implementation checks root, directory, file, and dangling symlinks before the empty-output shortcut, checks again before copying, and rejects symlinks while enumerating ordinary files. Independent regressions verify rejection and unchanged external bytes.

**Directory URLs in local navigation.** The parent found that the newly authored `./`, `../`, `../#contents`, and `../#search` links could resolve to directories when opened locally. They now use explicit `index.html` paths. `navigation-correction.json` records the change. Previous sources and author manifests remain under the `before-explicit-index-links` names, and the prior independent checks remain in `review-before-explicit-links/`. Final URL-resolution regressions and the independent actual-file target check pass. These are static URL checks, not browser navigation.

## Code quality and accessibility source review

The exporter has a bounded frozen-input allowlist, validates source/output ownership and existing output hashes, rejects unknown output files and unexpected metadata, and rechecks source snapshots before recording success. It does not silently overwrite unrelated output. Recognized metadata is ignored only after checking the AppleDouble or Finder header; unknown metadata-like paths are rejected. Clean-source publication remains a separate final-build gate.

Search is local vanilla JavaScript, with inert embedded JSON and a deferred classic script. It has no external dependency or fetch requirement. Search results use `textContent`; embedded JSON escapes HTML-significant characters and Unicode line separators. The search parser excludes navigation, scripts, styles, SVG, templates, and TeX annotations; malformed-link and escape-focused tests cover relevant boundary behavior.

The source includes a labeled search control, status announcement, ordinary links, focus styling, and responsive CSS scoped to the new landing/navigation classes. No measured contrast, rendered mobile layout, assistive-technology behavior, or interactive browser outcome is claimed from this source review.

## Asset, archive, and publication boundaries

This approval covers the reviewed source and ordinary exported payload. The author mirror at freeze also contained 68 recognized filesystem metadata entries excluded from its ordinary-file inventory. An ordinary-asset manifest therefore does not prove that a later deployment tar is free of metadata.

The installed official prepare helper copies directories recursively and the packaging helper invokes tar without metadata exclusions. Before any archive is accepted, the parent must check the actual staged physical tree, remove only header-verified generated metadata with retained evidence if needed, use `COPYFILE_DISABLE=1`, and inspect the actual tar inventory and extracted payload hashes. This review does not approve an archive that has not yet been built and inspected.

After the canonical source commit, the parent must make the required clean-source export and compare its 48 payload hashes with this reviewed build. Source commit, dirty-state, timestamp, and resulting manifest bytes can legitimately change; scientific and presentation payload bytes should remain identical. A source-content change invalidates the corresponding frozen approval until reviewed.

No browser, local server, file-URL navigation, headless fallback, network retry, source push, or Sites publication was attempted by this reviewer. The parent reports a registered private Site and a DNS-blocked source-open workflow; registration is not a live deployment. Browser rendering, hosted behavior, final archive inspection, and successful deployment remain separate outstanding checks. No fresh numerical replay, new proof certification, dependency installation, or whole-monograph audit is implied.
