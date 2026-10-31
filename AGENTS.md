# Repository working instructions

Follow the accepted [integration plan](INTEGRATION_PLAN.md). This is a monorepo with one Git root; do not initialize nested repositories or alter the preserved original repositories outside this checkout.

## Ownership

- `packages/volume-toolkit/`: supported Python toolkit. Follow its `CLAUDE.md`, architecture, module index, and release checks; keep existing import and command names compatible.
- `research/ipoly/`: historical imported manuscript and scripts. Preserve source bytes; current implementations and corrections belong in maintained modules, experiment drivers, and errata.
- `book/`: canonical mathematical source. Preserve theorem/equation labels and distinguish proved, conditional, numerical, and open statements.
- `provenance/`: source identities, history/path maps, restoration and migration evidence.
- `site/`: generated publishing frontend and its build tooling. Do not expose private holdout answers or unclassified results.

Each scientific computation must name its coordinates, conventions, precision, residuals and evidence status. A tolerance check is not exact arithmetic or an interval proof. Existing historical outputs must retain their status and provenance.

Only root `.github/workflows/` is active CI. Do not transplant the nested historical HF force-push or maintenance jobs into the root.

## Documentation lookup

Use Context7 for current library, framework, SDK, API, CLI and cloud-service documentation. Begin with `resolve-library-id` unless an exact library ID is supplied; then use `query-docs` for one scoped concept. This is unnecessary for ordinary refactoring, business logic, or scripts written from scratch. Prefer documented signatures and repository patterns.

## Verification

Run meaningful focused regression tests for corrected failures, then the existing relevant suite. Use an isolated supported Python environment. Keep source installation, test results, numerical replay, proof verification and deployment as separate claims. Update the nearest ownership documentation when responsibilities or entry points change.
