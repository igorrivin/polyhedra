# Calibration examples

These examples identify editorial decisions, not a required template or a set of claims to copy into unrelated subjects.

## Operators are not their labels

Insufficient: “On V_j, J² has value ℏ²j(j+1), and J_z has values ℏm.” A reader can still mistake j for an angular momentum or confuse m with a component operator.

Explain that J_x, J_y and J_z are operators; j is the dimensionless spin quantum number, ranging over nonnegative integers and half-integers; V_j is the associated (2j+1)-dimensional state space; m labels a component eigenstate, with m=-j,-j+1,...,j. The eigenvalues are ℏ²j(j+1) for the squared magnitude and ℏm for the component. Work out j=1/2: squared magnitude 3ℏ²/4 and component ±ℏ/2. State that the magnitude is ℏ√(j(j+1)), not ℏj. If a box uses additional basis symbols from the main text, either reintroduce them briefly or describe the physical state directly.

The lesson generalizes to an eigenvector and its eigenvalue, an index and a coordinate, a random variable and its realization, or an operator and its matrix in a chosen basis.

## A formula for a sum is not motivation for summing

Insufficient: define every product and summation index in a state sum but never say what data are fixed and what question the sum answers.

Explain gluing first: multiply local amplitudes and sum over shared internal states, as in matrix composition. Identify the boundary data that remain visible. A two-versus-three-tetrahedra example explains which extra label is internal and why it is summed. Only then give the whole-manifold formula. Explain separately why the sum is finite and why the local identities imply independence from the triangulation; these are different properties.

## Unfolding needs a visible change of domain

Insufficient: “Integrate the orbit sum and unfold to the stabilizer quotient.” Defining the group and subgroup does not show the operation.

Start with a nonnegative integrable function f on the real line and a periodic sum Σ_k f(x+k). Integrate on [0,1], substitute u=x+k, and identify the translated intervals as a partition of the real line (endpoints have measure zero). Work out an integrable f. Then explain the analogous pieces in the actual quotient, including stabilizers and measure factors. Do not infer that the periodic sum is pointwise constant merely because its integral is simple.

## A useful picture exposes the constraint

For a triangle-angle domain, draw the positive simplex α+β+γ=π and identify its boundary as a degeneration. For a curvature deficit, show the transverse sectors around an edge and the missing wedge; label the interior dihedral angles. For a saddle merger, draw the phase derivative and its roots on both sides of the parameter transition. Each picture should explain an operation or hypothesis used immediately in the argument.

## A whole-document pass needs more than opening paragraphs

A new introductory paragraph can fix motivation while leaving the proof unreadable. Record internal gaps separately: an unnamed measure in a displayed integral, a transform whose convention is implicit, an unbound index in a proof, or an example that violates the theorem's hypotheses. Check the amended passage in context and record precisely which issues were resolved. Unresolved specialist prerequisites should have a working definition and a reading route; unresolved substantive explanations remain open work.
