# Barrier examples author handoff

The five owned sources are frozen at the SHA256 values in
`examples-final-manifest.json`. No commits or canonical generated outputs were
created. The dirty preview is `/tmp/polyhedra-barrier-preview-reviewed/` and is
for review, not publication. `examples-bundle-manifest.json` is the actual
download manifest. Its ten payloads were checked byte-for-byte against their
recorded hashes; the three maintained numerical modules are copied unchanged.

The three fixture definitions were derived independently of the production
solver. The triangle maximum follows symmetry and strict concavity; the disk
maximum is its geometric angle assignment and the scalar log-sine derivative
telescopes along radial edges; the boundary-slice maximum follows strict
concavity and its negative limiting derivative. References use exact decimal
coordinates/parameters and 80-digit Clausen formulas. Separate lifts of actual
binary64 inputs have their own stationary references, and the endpoint is also
checked with an independent high-precision Bloch–Wigner formula. These are
numerical reference comparisons, not interval certificates.

The disk's nonzero barrier gradient at u=0 is -28/15. Its pure barrier center
is about 0.0363414688893 and its exact Phi_1 center about 0.0284464026744.
The initial centering phase only requires decrement at most 1/4, so its accepted
point is not asserted to equal that center. The recorded path reaches u>0.02
before approaching its geometric maximum at zero. Every accepted disk point
preserves the four interior-edge opposite sums to the recorded tolerance.

The boundary case's exact maximum volume is
0.3160358446012942861798335805775719456118860120729091191292577588.
Its endpoint observed gap is about 3.52701e-5, below its numerical finite-iterate
estimate of 7.05981e-5. A tiny rounded triangle-sum defect changes the limiting
derivative of the lifted Clausen model: its stationary point is about
2.25e-16 inside the exact-space boundary, and its reference maximum differs by
about 7.14e-15. Both references are retained and this is described in the page.

All 54 recorded numerical checks passed. Centering/path/evaluation counts were
4/375/756 for the triangle, 3/841/1687 for the disk, and 2/562/1128 for the
boundary slice; all starts have independent initial decrement above 1/4.
There were no line-search backtracks in these examples. The fresh author
preview took about 2.59 seconds including references and rendering; that is one
small run, not a scaling benchmark. The exact final values are in the manifest.

Focused author validation: 15 experiment tests passed, with 8 subtests, in
4.06 seconds. This includes nine new barrier tests and the six existing grid
rendering tests. Changed Python files pass Ruff. The tests challenge independent
reference values, initial centering, nontrivial disk motion, constraints, the
boundary perturbation, strict JSON, source/input identities, all archive
payloads, local download links, stored computation versions, and corrupt
detached payload rejection. They do not substitute for a fresh detached replay.

The publisher contract is `barrier.html`, downloads `barrier-result.json`,
`barrier-fixtures.json`, `barrier-reproduction.zip`, `barrier_run.py`, and
`angle_barrier.py`. The ZIP prefix is `barrier-reproduction/`; its manifest is
`barrier-bundle.json`. The page embeds JSON after the exact newline marker
`const barrierData = ` as `{report, fixture}`. Source roles are
`experiment.driver/fixture/template`, `toolkit.angle_barrier/variational/geometry`,
and optional `book.chapter`. Render-only operations validate source identity and
preserve stored computation provenance. An optional real adjacent `chapter.html`
can be linked after the publisher creates it.

Root owns independent review, the fresh minimal-environment detached run,
installed-package verification, and final clean-source generation. No browser,
server, dependency installation, or external publication was attempted here.
