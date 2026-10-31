# Airy and torus evidence recovery

Date: 31 October 2026. This is a local recovery inventory, not a numerical replay. Original repositories and archive contents were read without modification. The canonical monograph remains unchanged.

**Outcome:** no executable Airy exact-integral evidence or Markoff/Farey diagnostic archive was recovered from the provided material or reachable local code histories. The [machine inventory](evidence-recovery.json) records identities, counts, archive hashes and keyword/name matches. Absence from this scoped search does not imply absence from other machines, remote branches, unpublished notebooks or external archives.

## Material searched

| Material | Search performed | Result |
| --- | --- | --- |
| Toolkit at `cc6b689652ce735f2098bb0a3235089210d764df` | Current Python, Julia, Sage, notebook, JSON, CSV, TSV and Markdown content; names of all locally reachable objects; 359 distinct named code blobs across 89 reachable commits (4,101,144 bytes). | No target-topic content match. A historical Euclidean-fit diagnostics plot is unrelated. |
| ipoly at `30ef40e23005509bd94d26f27dc48ea778832a50` | Same current-file search; all locally reachable object names; 22 code blobs in its one reachable commit (73,782 bytes). | No target-topic content match. The torus-bundle script was read and concerns angle structures and bundle-volume optimization. |
| Original monograph ZIP and 43 ZIP files in the two supplied worktrees | All member names; members ending in `.py`, `.jl`, `.sage`, `.ipynb`, `.json`, `.csv`, `.tsv`, `.txt` or `.md`, with a 2 MB member limit. No selected member exceeded that limit. | No target-topic content match in the selected executable/data/documentation members. Name matches are the known bundle script and an Airy illustration source. |
| Canonical monograph TeX | Read the exact-integral table and trace-experiment passages identified below. | Printed numerical rows and methodological claims exist; they do not supply the missing runnable evidence. |

Content search terms were case-insensitive `markoff`, `airy`, `double[ _-]?sine`, `diagnostic archive`, `sensitivity table`, `18191508`, and `18486116`. Name searches additionally included `torus` and `diagnostic`. Current-file searches used `rg`; historical inventory used local `git rev-list --objects --all` and `git cat-file blob`; ZIP contents were inspected without extraction or execution. The search did not fetch remote refs, download historical LFS payloads absent locally, inspect unrelated home directories, execute historical scripts, or interpret arbitrary binary model files. Historical code counts refer to blob paths bearing the selected code extensions.

The original ZIP SHA-256 remains `8f28b07686ea579a7dfb7b88ccef5c12bdd50b6e328737d5a8a79f6e06ba92dc`. Its 39 members are already fully mapped in [the import member map](../../../provenance/monograph/member-map.json); 25 companion members duplicate the preserved ipoly files.

## Recovery requirements

The [book status ledger](../../../book/computational-status.md) gives source labels, line locations, mathematical scope and the next verification tasks. Two evidence packages are required:

1. **Section 15:** exact log-double-sine/cleared-integrand implementation; normalization and branch choices; contour and cutoff parameters; precision and convergence/tail studies; raw six-row output and scaled residual calculation. Review the exact evaluator independently before comparing it with the first Airy correction.
2. **Section 30:** enumeration source; both trace triples and multiplicity conventions; full block table; direct-trace and long-path precision reports; event-order sensitivity tables; dependency and run metadata. Validate a small independent replay before the length-8192 campaign.

If recovery fails, the numerical availability statements need explicit correction in the publication edition. New computations must be recorded as new runs with their own provenance. The printed rounded rows cannot stand in for the missing raw archive.
