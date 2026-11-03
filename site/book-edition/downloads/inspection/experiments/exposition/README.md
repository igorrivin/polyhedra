# Small calculations for the exposition pass

Run `python experiments/exposition/check_examples.py` from the repository root in a supported Python environment with SymPy. The program prints JSON and fails on a nonzero symbolic residual. All nonintegral algebraic inputs are exact rational numbers or symbolic constants; no floating-point tolerance is used.

The examples follow the manuscript from angle-domain areas and a three-vertex resistor network through spin measurement probabilities, Gaussian integrals, fusion matrices, unfolding, cuff matching, lattice filters and arithmetic error exponents. Each JSON record names its section and calculation. They are deliberately small enough to follow by hand. Change an example's inputs to explore it, while retaining its geometric hypotheses.

The saved [result](../../artifacts/exposition/result.json) records the actual source state, source hashes and runtime. The [editorial ledger](../../docs/exposition/README.md) explains why the examples were added. These checks verify the displayed finite calculations, not the specialist theorems surrounding them. They do not rerun any earlier scientific campaign, prove an asymptotic estimate, or certify that arbitrary algebraic data realize a surface or polyhedron.

This code and guide are covered by the repository's new-companion MIT grant.
