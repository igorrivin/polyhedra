# Independent Section 9 publishing implementation review

Reviewer: `/root/section9_build_review`. Review date: 31 October 2026, America/New_York. Baseline HEAD: `26b3c134d9308d345cb76f1240db9de982b2e5a6`.

## Final disposition

The reviewed publishing implementation and strict v3 preview pass this bounded code, anti-pattern and artifact review. No unresolved implementation blocker remains. This approves the source bytes below and the identified preliminary artifacts; it does not claim that clean-source release generation or a subsequent commit has already happened. Those are the parent's next gates.

| Reviewed source | SHA-256 |
| --- | --- |
| `site/build_section9.py` | `b02995dab6d0c1b7b9c5f700a12be0878481a8d372057339daeea40b41afff94` |
| `site/section9.css` | `aae27cd011f0d53aeb109ccaafbbe26e5a4c26eb2d9cb28c3aea78ec951f8b01` |
| `site/README.md` | `3bb8a1d3b9c5d16f0d3c967253918b2d5ad53a85c6871c6f2242f5e09a8a8caa` |
| `site/tests/test_build_section9.py` | `524d9b2d1a9811eab78c7904027649ef902acb66d202c1bc053fbbda5663d6ea` |
| `experiments/section9/run.py` | `91525e17669887d7863834a3322207088c7ff4dbf4b4f8348a67b529a6142a19` |
| `experiments/section9/README.md` | `e961e12152e3cd024f31a15c39338989c98a7a9539938ffa4b0ee565c932cb5b` |
| `experiments/section9/tests/test_rendering.py` | `a6726c477ae419d2a86b1d9c64fd1b12a27bc98395ea53f55dd1a1bc7e497a7f` |

The current mathematical chapter and claim ledger were separately proof-reviewed. This report checks preservation, conversion and provenance rather than re-auditing their mathematics. The complete monograph compiles, but this is not a proof review of its other chapters.

## Reproduced finding and correction

The first source review reproduced a render-only provenance defect in driver `50df302d6408deb250b5a4b6deb1869bc98325ca6e9a04c6f00e42438f3ce9b2`. An existing report could be rendered under a different Python/NumPy environment without changing source or fixture bytes. The numerical ZIP retained the old `origin_provenance`, but its requirements and captured-run README prose used the rendering environment. The independent sentinel probe changed version strings only; it did not install or claim the existence of sentinel package versions.

The original probe and result are preserved as `build-review-render-environment-probe.py` and `.json`. The author independently identified the same issue and corrected the bundle to take Python, NumPy, SciPy and mpmath versions from the numerical report. The separate `build-review-render-environment-rereview.py` and `.json` record the corrected behavior: original provenance remains unchanged and both environment-attribution flags are false. A maintained regression exercises the same meaningful failure case.

Two additional integrity improvements were checked during review. The ledger's `site/section9/downloads/section9-reproduction.zip` reference now links to the current exported numerical bundle, rather than remaining plain text or copying the older canonical ZIP. The chapter builder now verifies its existing numerical companion against its explicit result before linking it: result bytes, fixture hash, embedded HTML data, ZIP originating provenance, ZIP payload hashes and all five required numerical source-role hashes. My independent mutation of the ZIP's `geometry.py` was rejected by the payload-hash gate. This makes the documented later render-only link refresh unnecessary for repairing an unnoticed stale numerical input.

The first artifact-check run stopped at my own incorrect expected link suffix, “inspection copy”; the product correctly labels this complete ZIP “complete numerical bundle”. `build-review-checker-history.json` records that harness-only correction. It was not a product failure and is not hidden as an initial pass.

## Verification checklist

The independently executed focused runs passed: 8 builder integrity tests, 6 rendering/provenance tests and 11 existing variational tests. Their separate command logs are retained. Ruff's syntax, undefined-name, unused-import and unused-local selections (`E9,F63,F7,F82,F401,F841`) passed on the two changed Python tools and their two test modules. The new code, tests, CSS and build/experiment documentation contain no trailing whitespace or blank EOF diagnostics. Exact mathematical/archival snapshots fall under the parent's separately enumerated preservation exceptions; this review does not claim blanket repository whitespace success.

The strict preview is `/tmp/polyhedra-section9-build-v3/site/section9`, after the author's render-only refresh. Its source and output hashes were checked independently. There are no pending evidence files. A direct canonical-TeX delimiter count, excluding the rendered TikZ source, gives 206 chapter formulas. The two explicitly unaudited cross-reference equations and one bibliography formula bring the HTML to 209 MathML nodes, with no `merror`, script or MathML fallback. Both figures have local images, descriptive alternative text and explicit dimensions. All 26 chapter labels, two reference-only labels and 17 equation numbers resolve. Local HTML links remain within the relocated export tree; external links are citations, not rendering dependencies.

The exported ten-page PDF has 20 internal named actions, all resolving, eight relative download actions, all resolving within the exported tree, and 13 external links. The exported PDF hash is `c486049b6a92dfb4d780972d6e2e33625bd4574196e73eb5c3697cdaa237d4d3`. The entire set of ten rendered v3 page PNGs is byte-identical to the v2 pages visually reviewed by the parent. This independently verifies that the parent's recorded visual inspection applies to the v3 layout; I did not claim a separate browser or visual review.

I extracted `monograph-source.zip` outside the checkout and verified all seven payload hashes. With normal TeX Live packages and no source-checkout input dependency, both advertised entry points built successfully:

- `book/main.tex`: 177 pages and 607 distinct labels, including all expected chapter/cross-reference labels.
- `book/section9.tex`: 10 pages and 28 distinct labels.

Both builds converged with no unresolved-reference/citation warnings, duplicate labels or overfull boxes. The `.fls` input records contain no dependency on the original checkout. The source ZIP hash is `21aa370d9b9d4766e1a5a8c5aff80cc143f7fa77689ddb54e04c3c8c0c5593ac`. Canonical repository-relative hyperlinks inside the source archive retain their documented ownership context; the separately exported chapter PDF has the verified adjacent-download targets. A successful full-book build is not mathematical approval of all 177 pages.

## Anti-pattern and code-quality review

The implementation has one canonical mathematical source and derives its preamble, selected bibliography and numbering from the full compiled monograph. It does not maintain a second edited theorem/proof text. MathML presentation normalization is narrow and explicit; raw/unhandled TeX, missing anchors, lost figures and warnings fail the build. The local TeX include graph rejects missing, external, nonliteral and cyclic includes and unsupported asset commands. The complete actual source graph is archived and was compiled after extraction. Snapshot bytes and copied evidence are rechecked before successful completion.

External tools are invoked as argument lists without a shell; TeX builds use `-norc` and `-no-shell-escape`. There is no network rendering dependency, remote font/script import, dynamic `eval`, blanket exception swallowing or hard-coded user/workspace path in the new maintained publisher. The existing explicitly manifested numerical-subset import path is retained and not broadened to arbitrary imports. Requested missing publication assets fail rather than creating plausible dead links. The numeric driver preserves the stored computation's timestamp, numbers and provenance during render-only refresh.

The converter is intentionally a strict handler for this chapter, not a complete TeX parser. Its linear build orchestration is substantial, but its stages and ownership are clear and failure checks are local. Extending it to new TeX syntax or other chapters requires the regression tests and independent rendering check documented in `site/README.md`; this review does not infer general conversion completeness from one chapter.

## Evidence and remaining limits

The machine check records are `build-review-artifact-checks.json`, `build-review-extracted-builds.json`, and the original/corrected render-environment JSON pair. The independent artifact probe is retained as `build-review-artifact-checks.py`. Exact commands and logs for the two extracted TeX builds and three focused suites accompany this report. The mathematical/proof reviews, dependency preflight and the builder's own preview/detached-replay records remain separate evidence.

No browser, localhost server, dependency installation, public upload, Git mutation or original-repository mutation was performed by this reviewer. Browser layout and interaction remain unverified under the session's access restriction. The unavailable optional test dependencies were not resolved and the full suite was not rerun. After the approved source commit, regenerate in temporary directories from a clean checkout, verify final hashes and page renders, and then make the artifact checkpoint; the present dirty-preview record must not be relabeled as that future clean run.
