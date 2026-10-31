# Geometric realization from triangle angles

The toolkit separates angle feasibility, compatible volume optimization, and
coordinate realization. A feasible LP assigns positive angles with the required
linear sums; an arbitrary feasible assignment need not close when its triangles
are developed into the plane. Flatness applies at interior vertices, whose
angles sum to 2π. Boundary conditions are different and depend on the intended
convexity constraints.

## Maintained polyhedral workflow

Use the residual-bearing Rivin workflow when constructing a Delaunay realization:

```python
from ideal_poly_volume_toolkit.rivin_delaunay import (
    check_delaunay_realizability,
    optimize_hyperbolic_volume,
    realize_angles_as_points,
)

feasibility = check_delaunay_realizability(triangles)
if feasibility["realizable"]:
    optimum = optimize_hyperbolic_volume(
        triangles, initial_angles=feasibility["angles_radians"]
    )
    if optimum["success"]:
        realization = realize_angles_as_points(triangles, optimum["angles"])
        # Inspect success and the angle, closure, orientation and triangulation
        # diagnostics before using realization["points"].
```

The LP's `angles` field uses scaled units with π = 1. Its
`angles_radians` field is already in radians. Do not multiply the latter by π
again. Optimization and realization consume radians.

Neither LP feasibility nor optimizer termination alone establishes an embedded
convex polyhedron. The closed-sphere pipeline has a separate strict numerical
audit in `rivin_zero_shear`; exact existence would additionally require validated
root enclosures and geometric inequalities. See [architecture](architecture.md).

## Rigid development compatibility entry point

`geometric_realization.realize_from_angles_rigid` remains a small numerical
angle-development helper. It accepts arbitrary integer vertex labels and
coherently oriented faces. The angle in column k belongs to the vertex in
column k of that face. Cyclically rotating a face and its angle row preserves
the result.

The helper anchors an actual edge, then uses one oriented law-of-sines formula
to develop adjacent faces. It checks all triangle angles, local orientations,
vertex distinctness, and developing-map closure. Disconnected complexes and
incompatible cycles return `success=False`; malformed angle or face data raise
`ValueError`. The returned `vertex_list` maps the coordinate rows back to the
input labels. The retained `boundary_vertices` argument does not change the
angle development.

`success=True` means those local floating-point checks passed at the reported
`residual_tolerance`. The result is marked `evidence_status="numerical_development"`
and `embedding_checked=False`: global overlap, Delaunayness, convexity, and exact
existence are not certified by this helper. Use the maintained workflow and
independent geometric audit for those additional questions.

## Regression coverage

`tests/test_core_defect_regressions.py` checks cyclic rotations, arbitrary
relabeling (including when the two smallest labels are not adjacent), malformed
inputs, disconnected faces, and an incompatible cycle whose vertices can all be
placed. The legacy `examples/test_rigid_construction.py` remains an exploratory
plantri-based example; its LP output must still pass the development checks.
