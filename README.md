# ipoly

Manuscript and numerical verification scripts for *Duffin's resistor networks,
the volume of ideal polyhedra, and nearly-linear-time Laplacian solvers*.

## Contents

- [Manuscript PDF](duffin_rivin_volume_laplacian_solvers.pdf) and
  [LaTeX source](duffin_rivin_volume_laplacian_solvers.tex).
- `v1_volume_hessian.py` through `v21_snappea_vs_ours.py`, including
  `v10_diag.py`: 22 research scripts covering cotangent Laplacians, volume
  Hessians, Newton and barrier methods, and ideal triangulations.
- `verification_scripts.zip`: the original script archive.
- `files (5).zip`: the original bundle containing the manuscript and script
  archive.

## Running the scripts

The scripts use Python 3 with NumPy, SciPy, and mpmath. The three-manifold
experiments also require SnapPy; the random-link comparison uses Spherogram.

Run scripts from the repository root because some load neighboring scripts by
relative path. For example:

```sh
python3 v1_volume_hessian.py
```

Some experiments take command-line arguments; see each script's source for
its modes and parameters. These are standalone research experiments, with
diagnostics printed to the terminal.
