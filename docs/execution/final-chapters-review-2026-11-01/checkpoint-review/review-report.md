# Independent checkpoint preparation review

Decision: **targeted revision required**. The prepared tools are not approved for a real replay yet. The complete required set is CR01 and CR02 in `review-findings.json`.

CR01 concerns strict scientific equality. JSON floating-number tokens are converted to binary64 before comparison. The independent probes show that `1e-999` and `0.0`, `1.0000000000000001` and `1.0`, and two values straddling the binary64 integer boundary collapse. Full report comparisons also falsely accept two of those changes in an unknown scientific field. These are changes in the numerical value, not acceptable metadata differences. Boolean/integer, string/number, integer/float and tiny-positive string controls remain correctly distinguished.

CR02 concerns the prelaunch manuscript freeze. A set of 36 declared files is counted and hash checked, but the active input graph is not traversed until the later candidate verifier. A synthetic replay with 36 unconnected TeX files and no `book/main.tex` was launched successfully. Its command receipt is retained in each mode. The actual graph rooted at the wrapper must be verified before launch; a connected synthetic graph should replace the current count-only positive fixture.

All four production scripts were read in full, including identity, path, receipt, comparison, source, preservation and candidate lifecycle gates. The exact 15-file author preparation was verified and copied to `subject-v1/` before testing, then matched again after review. No author files were modified. The existing 29 tests passed normally and under `-O`, and Ruff passed. Fifteen independent probes ran in each mode: six observed false acceptances correspond to the two defects above; the remaining controls rejected as intended. The reviewer probe script also passes Ruff.

The synthetic fixtures create temporary Git repositories and launch a synthetic driver. They are not monograph computations, PDF files, real source/artifact commits, or an audit of the final candidate. The current unready templates remain unchanged. No canonical source/artifact, original repository, PDF, stage, commit or remote operation was performed by this review.

After repair, recheck the two affected gates and unchanged controls. Actual final receipt schemas, source and computation approvals, complete fourteen-group report, source commit, PDF/rendering receipts, candidate curation and final lifecycle verification still require separate binding and review.
