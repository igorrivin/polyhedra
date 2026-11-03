# Public edition and computational sources

The monograph is published at https://polyhedra.dimensionreducers.ai and its canonical research repository at https://github.com/igorrivin/polyhedra.

The `edition-2026-11-03-r4` release expands Section 10.1 with a physics box connecting Pauli matrices and Wigner recoupling to quantum geometry, Euclidean Regge calculus before the hyperbolic discussion, a checked regular-tetrahedron example, and a motivated account of the Ponzano–Regge and Turaev–Viro state sums. The rebuilt monograph has 209 pages. All 613 existing label numbers and the original 129 bibliography numbers are preserved; seven references are appended. The [revision record](execution/regge-turaev-viro-2026-11-03/README.md) separates the new author checks from historical approvals. The earlier [r3 exposition revision](execution/exposition-revision-2026-11-03/README.md), including its unfolding examples in Section 17.1, is retained. The new finite example has its own driver and result; existing scientific implementations, fixtures, historical claim ledgers and recorded results retain their earlier bytes and evidence scope.

Release r2 remains the linked 200-page edition based on scientific artifact commit `13f15cb12a0bfe694cf161c3dda1acebe59fb211`. The `scientific_base_commit` in the repository-link configuration retains that historical baseline; the new edition's build manifest identifies the revised mathematical source exactly.

## Reader entry points

- `experiments/README.md` maps the nine companions to recipes, entry points and recorded results.
- The website's computational index links back to the relevant chapters and to source, inputs, outputs and recipes at the exact published repository commit.
- All 54 repository-path occurrences in the current HTML edition become links to their 24 existing file/directory targets.
- The linked PDF retains all pages and mathematical content of the newly compiled edition. It adds a small repository address to the title page and URI annotations over located computational paths. That edition's unannotated PDF is downloadable as `monograph-original.pdf`; older published PDFs remain in their versioned GitHub releases.
- The release's `polyhedra-source.zip` contains tracked source and materialized LFS data, with a per-file SHA-256 manifest. It contains no Git database or local environments. Git-based provenance-aware drivers should be run from a clone.

## Build and verification

The existing `site/build_book.py` produces the accepted local edition. `site/link_repository.py` adds the public presentation and repository links to a separate output directory. It reads `site/book/repository.json` and an exact commit; every target must exist at that commit. It preserves the original local-edition manifest and adds a repository-link manifest that records all changed outputs. No mathematical conversion or scientific campaign is run by the linking step.

```sh
python -m pip install pymupdf
python site/link_repository.py --source site/book-edition --output /tmp/polyhedra-linked --ref HEAD
```

The linking step requires a clean source commit and a new output directory. The generated PDF is an annotated publication derivative; the canonical TeX and the original accepted PDF remain unchanged. Rendering and link verification have separate receipts under the outer publication execution directory, and the final repository publication summary records their results.

## Historical records and licensing

The original toolkit and `ipoly` histories are retained. Old execution receipts describe their own frozen states, including unsuccessful network or dependency checks; they are not statements about the current public website. Historical or superseded results remain labelled as such and are not newly promoted to verified mathematical evidence.

The [license map](../LICENSES/README.md) preserves CC BY 4.0 for the monograph, scoped MIT notices for maintained code, and inherited/third-party exclusions. Publication does not impose a blanket license on the archive.

## Publication checks

The [preflight receipt](publication/preflight.json) records 713 passing toolkit tests, 46 site tests with 109 passing subtests, successful materialized-data checks, and a compatible 95-package isolated environment. The [resolved dependency list](publication/requirements-py312.txt) describes that environment. The [history audit](publication/history-audit.json) checked reachable Git content, embedded archives and all historical LFS payloads before public upload. These are bounded verification records, not a general proof or a fresh replay of every scientific result.

## Python 3.10 compatibility check

The first hosted matrix passed on Python 3.11-3.14 and in the data-integrity job. Python 3.10 with SciPy 1.15.3 exposed an incorrect test expectation: it expected accepted-iterate callbacks, which SciPy added in 1.16. The existing solver correctly returns the separately labelled residual-evaluation fallback. The regression test now checks the appropriate documented trajectory kind and its individual records. No solver, mathematical source, fixture or scientific result was changed for this correction. The earlier public tags and releases remain historical snapshots.
