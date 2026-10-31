"""
Numerical Rivin angle feasibility and constrained volume optimization.

For the intended triangulated-disk setting, search for angles satisfying:
(a) All angles are positive
(b) Sum of angles in each triangle equals π (or 1 after scaling)
(c) Sum of angles around each interior vertex equals 2π (or 2 after scaling)
(d) Sum of angles at each boundary vertex is ≤ π (or ≤ 1 after scaling)
(e) Sum of opposite angles across each interior edge is ≤ π (or ≤ 1 after scaling)

The standard LP maximizes the minimum angle. The strict LP maximizes one
common margin for angles and the boundary/dihedral inequalities. Returned
candidates are checked against the original finite constraints. A positive
witness is numerical evidence for this angle system; no verified witness
does not establish exact infeasibility. These routines do not certify the
triangulated-disk hypothesis or a global geometric embedding.

References:
- Rivin, I. (1994). "Euclidean structures on simplicial surfaces and hyperbolic volume"
- Leibon, G. (2002). "Characterizing the Delaunay decompositions of compact hyperbolic surfaces"
"""

import numpy as np
from scipy.optimize import linprog, minimize
from collections import defaultdict
from typing import List, Tuple, Set, Dict, Optional
import random
import time


def extract_boundary_vertices(triangles: List[Tuple[int, int, int]]) -> Set[int]:
    """
    Extract boundary vertices from a triangulation.

    A vertex is on the boundary if it's incident to at least one edge that appears
    in exactly one triangle.

    Args:
        triangles: List of triangles, each given as (v0, v1, v2)

    Returns:
        Set of boundary vertex indices
    """
    edge_count = defaultdict(int)

    # Count how many times each edge appears
    for tri in triangles:
        v0, v1, v2 = tri
        # Store edges in canonical form (min vertex first)
        edges = [
            tuple(sorted([v0, v1])),
            tuple(sorted([v1, v2])),
            tuple(sorted([v2, v0]))
        ]
        for edge in edges:
            edge_count[edge] += 1

    # Boundary edges appear exactly once
    boundary_edges = {edge for edge, count in edge_count.items() if count == 1}

    # Collect all vertices on boundary edges
    boundary_vertices = set()
    for edge in boundary_edges:
        boundary_vertices.add(edge[0])
        boundary_vertices.add(edge[1])

    return boundary_vertices


def build_vertex_angle_incidence(triangles: List[Tuple[int, int, int]]) -> Dict[int, List[Tuple[int, int]]]:
    """
    Build mapping from vertex to all angles incident to it.

    Args:
        triangles: List of triangles, each given as (v0, v1, v2)

    Returns:
        Dict mapping vertex_id -> list of (triangle_id, corner_id) where corner_id in {0,1,2}
        indicates which corner of the triangle has this vertex
    """
    vertex_angles = defaultdict(list)

    for tri_id, tri in enumerate(triangles):
        for corner_id, vertex in enumerate(tri):
            vertex_angles[vertex].append((tri_id, corner_id))

    return vertex_angles


def build_edge_adjacency(triangles: List[Tuple[int, int, int]]) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """
    Build mapping from each edge to the angles opposite to it.

    For an interior edge shared by two triangles, we get the two opposite angles.
    For a boundary edge (in only one triangle), we get one opposite angle.

    Args:
        triangles: List of triangles, each given as (v0, v1, v2)

    Returns:
        Dict mapping edge (as sorted tuple) -> list of (triangle_id, corner_id) for opposite angles
        where corner_id is the corner opposite to this edge in the triangle
    """
    edge_opposite_angles = defaultdict(list)

    for tri_id, tri in enumerate(triangles):
        v0, v1, v2 = tri
        # For each edge, find the opposite corner
        edges_and_opposite = [
            (tuple(sorted([v0, v1])), 2),  # edge v0-v1, opposite corner is v2 (index 2)
            (tuple(sorted([v1, v2])), 0),  # edge v1-v2, opposite corner is v0 (index 0)
            (tuple(sorted([v2, v0])), 1),  # edge v2-v0, opposite corner is v1 (index 1)
        ]
        for edge, corner_id in edges_and_opposite:
            edge_opposite_angles[edge].append((tri_id, corner_id))

    return edge_opposite_angles


def find_interior_edges(triangles: List[Tuple[int, int, int]]) -> List[Tuple[int, int]]:
    """
    Find all interior edges (edges shared by exactly 2 triangles).

    Args:
        triangles: List of triangles, each given as (v0, v1, v2)

    Returns:
        List of interior edges as sorted tuples (v1, v2)
    """
    edge_opposite_angles = build_edge_adjacency(triangles)
    interior_edges = [edge for edge, angles in edge_opposite_angles.items() if len(angles) == 2]
    return interior_edges


def compute_rivin_angle_residuals(
    triangles: List[Tuple[int, int, int]],
    angles: np.ndarray,
    boundary_vertices: Optional[Set[int]] = None,
    *,
    tolerance: float = 1e-6,
) -> Dict:
    """Compute primal and inequality residuals for a Rivin angle structure.

    The returned margins use the convention that positive values are
    feasible and negative values are violations.  In particular,
    ``dihedral_margin`` is ``pi`` minus the two angles opposite an interior
    edge, and ``boundary_margin`` is ``pi`` minus the angle sum at a boundary
    vertex.

    This helper intentionally reports both ordinary feasibility (allowing
    equality up to ``tolerance``) and strict-interior status.  Callers that
    construct arithmetic witnesses should apply their own, usually larger,
    positive margin threshold rather than relying on floating-point equality.
    """
    if tolerance < 0 or not np.isfinite(tolerance):
        raise ValueError("tolerance must be a finite nonnegative number")
    if not triangles:
        raise ValueError("triangles must be nonempty")

    angle_array = np.asarray(angles, dtype=float)
    expected_shape = (len(triangles), 3)
    if angle_array.shape != expected_shape:
        raise ValueError(
            f"angles must have shape {expected_shape}; got {angle_array.shape}"
        )
    if not np.all(np.isfinite(angle_array)):
        raise ValueError("angles must all be finite")

    if boundary_vertices is None:
        boundary_vertices = extract_boundary_vertices(triangles)
    else:
        boundary_vertices = set(boundary_vertices)

    all_vertices = {vertex for tri in triangles for vertex in tri}
    unknown_boundary = boundary_vertices - all_vertices
    if unknown_boundary:
        raise ValueError(
            "boundary_vertices contains vertices absent from triangles: "
            f"{sorted(unknown_boundary)}"
        )
    interior_vertices = all_vertices - boundary_vertices
    vertex_angles = build_vertex_angle_incidence(triangles)
    edge_opposite_angles = build_edge_adjacency(triangles)

    triangle_residuals = np.sum(angle_array, axis=1) - np.pi
    interior_vertex_residuals = {}
    for vertex in sorted(interior_vertices):
        angle_sum = sum(
            angle_array[tri_id, corner_id]
            for tri_id, corner_id in vertex_angles[vertex]
        )
        interior_vertex_residuals[vertex] = float(angle_sum - 2.0 * np.pi)

    dihedral_margins = {}
    for edge in sorted(edge_opposite_angles):
        opposite_angles = edge_opposite_angles[edge]
        if len(opposite_angles) == 2:
            angle_sum = sum(
                angle_array[tri_id, corner_id]
                for tri_id, corner_id in opposite_angles
            )
            dihedral_margins[edge] = float(np.pi - angle_sum)

    boundary_margins = {}
    for vertex in sorted(boundary_vertices):
        angle_sum = sum(
            angle_array[tri_id, corner_id]
            for tri_id, corner_id in vertex_angles[vertex]
        )
        boundary_margins[vertex] = float(np.pi - angle_sum)

    max_triangle_residual = float(np.max(np.abs(triangle_residuals)))
    max_vertex_residual = max(
        (abs(value) for value in interior_vertex_residuals.values()),
        default=0.0,
    )
    max_equality_residual = max(max_triangle_residual, max_vertex_residual)

    worst_dihedral_edge = min(
        dihedral_margins,
        key=lambda edge: (dihedral_margins[edge], edge),
        default=None,
    )
    min_dihedral_margin = (
        dihedral_margins[worst_dihedral_edge]
        if worst_dihedral_edge is not None
        else None
    )
    worst_boundary_vertex = min(
        boundary_margins,
        key=lambda vertex: (boundary_margins[vertex], vertex),
        default=None,
    )
    min_boundary_margin = (
        boundary_margins[worst_boundary_vertex]
        if worst_boundary_vertex is not None
        else None
    )

    inequality_margins = [*dihedral_margins.values(), *boundary_margins.values()]
    min_inequality_margin = min(inequality_margins, default=None)
    min_angle = float(np.min(angle_array))
    max_angle = float(np.max(angle_array))
    feasible = (
        max_equality_residual <= tolerance
        and min_angle >= -tolerance
        and (
            min_inequality_margin is None
            or min_inequality_margin >= -tolerance
        )
    )
    strict_interior = (
        max_equality_residual <= tolerance
        and min_angle > tolerance
        and (
            min_inequality_margin is None
            or min_inequality_margin > tolerance
        )
    )

    return {
        "feasible": bool(feasible),
        "strict_interior": bool(strict_interior),
        "tolerance": float(tolerance),
        "min_angle": min_angle,
        "max_angle": max_angle,
        "max_triangle_sum_residual": max_triangle_residual,
        "max_interior_vertex_sum_residual": float(max_vertex_residual),
        "max_equality_residual": float(max_equality_residual),
        "min_dihedral_margin": min_dihedral_margin,
        "worst_dihedral_edge": worst_dihedral_edge,
        "max_dihedral_angle": (
            float(np.pi - min_dihedral_margin)
            if min_dihedral_margin is not None
            else None
        ),
        "min_boundary_margin": min_boundary_margin,
        "worst_boundary_vertex": worst_boundary_vertex,
        "max_boundary_angle_sum": (
            float(np.pi - min_boundary_margin)
            if min_boundary_margin is not None
            else None
        ),
        "min_inequality_margin": min_inequality_margin,
        "n_triangles": len(triangles),
        "n_vertices": len(all_vertices),
        "n_interior_vertices": len(interior_vertices),
        "n_boundary_vertices": len(boundary_vertices),
        "n_interior_edges": len(dihedral_margins),
    }


def flip_edge(triangles: List[Tuple[int, int, int]], edge: Tuple[int, int]) -> Optional[List[Tuple[int, int, int]]]:
    """
    Perform an edge flip in a triangulation.

    Given two triangles sharing an edge, flip the edge to the other diagonal
    of the quadrilateral formed by the two triangles.

    For example:
        Triangles: (a, b, c) and (b, d, c) sharing edge (b, c)
        After flip: (a, b, d) and (a, d, c) sharing edge (a, d)

    Args:
        triangles: List of triangles as (v0, v1, v2) tuples
        edge: Edge to flip as (v1, v2) tuple (order doesn't matter)

    Returns:
        New list of triangles with the edge flipped, or None if edge is not flippable
    """
    # Normalize edge to sorted form
    edge_sorted = tuple(sorted(edge))

    # Find triangles incident to this edge
    edge_triangles = []
    other_triangles = []

    for tri in triangles:
        v0, v1, v2 = tri
        tri_edges = [
            tuple(sorted([v0, v1])),
            tuple(sorted([v1, v2])),
            tuple(sorted([v2, v0]))
        ]
        if edge_sorted in tri_edges:
            edge_triangles.append(tri)
        else:
            other_triangles.append(tri)

    # Must be exactly 2 triangles (interior edge)
    if len(edge_triangles) != 2:
        return None

    # Extract the two triangles
    tri1, tri2 = edge_triangles

    # Preserve the cyclic orientation of tri1.  Rotate it to (u, v, a),
    # where u-v is the directed shared edge.  A consistently oriented tri2
    # must then have cyclic form (v, u, d).  Refuse to repair inconsistent
    # input locally: silently doing so can hide a non-orientable or otherwise
    # malformed triangulation from callers that use ``flip_edge`` directly.
    u = v = a = None
    for i in range(3):
        candidate_u = tri1[i]
        candidate_v = tri1[(i + 1) % 3]
        if tuple(sorted((candidate_u, candidate_v))) == edge_sorted:
            u = candidate_u
            v = candidate_v
            a = tri1[(i + 2) % 3]
            break
    if u is None or v is None or a is None:
        return None

    tri2_u = tri2_v = d = None
    for i in range(3):
        candidate_u = tri2[i]
        candidate_v = tri2[(i + 1) % 3]
        if tuple(sorted((candidate_u, candidate_v))) == edge_sorted:
            tri2_u = candidate_u
            tri2_v = candidate_v
            d = tri2[(i + 2) % 3]
            break
    if tri2_u != v or tri2_v != u or d is None:
        return None
    if a == d:
        return None

    # CRITICAL CHECK (from cubic-graph-optimizer):
    # Verify the new edge (a, d) doesn't already exist
    new_edge = tuple(sorted([a, d]))
    for tri in other_triangles:
        v0, v1, v2 = tri
        tri_edges = [
            tuple(sorted([v0, v1])),
            tuple(sorted([v1, v2])),
            tuple(sorted([v2, v0]))
        ]
        if new_edge in tri_edges:
            # Edge already exists - flip would create invalid triangulation
            return None

    # Create new triangles with flipped edge (a, d), preserving tri1's local
    # cyclic orientation.  For tri1=(u,v,a), tri2=(v,u,d), the consistently
    # oriented replacements are (a,u,d) and (a,d,v).
    new_tri1 = (a, u, d)
    new_tri2 = (a, d, v)

    # Return new triangulation
    return other_triangles + [new_tri1, new_tri2]


def random_edge_flips(triangles: List[Tuple[int, int, int]], n_flips: int, seed: Optional[int] = None) -> List[Tuple[int, int, int]]:
    """
    Perform n random edge flips on a triangulation.

    Uses the flip_edge() function which validates each flip to ensure validity.

    Args:
        triangles: Initial triangulation
        n_flips: Number of edge flips to perform
        seed: Random seed for reproducibility

    Returns:
        Triangulation after n_flips random edge flips
    """
    if seed is not None:
        random.seed(seed)

    current = triangles
    successful_flips = 0

    # Try many more attempts than requested, since many edges aren't flippable
    for attempt in range(n_flips * 10):
        if successful_flips >= n_flips:
            break

        # Find all interior edges (edges in exactly 2 triangles)
        interior_edges = find_interior_edges(current)

        if not interior_edges:
            break

        # Pick a random interior edge
        edge = random.choice(interior_edges)

        # Try to flip it (will return None if not flippable)
        flipped = flip_edge(current, edge)

        if flipped is not None:
            current = flipped
            successful_flips += 1

    return current


def check_delaunay_realizability(triangles: List[Tuple[int, int, int]],
                                 boundary_vertices: Optional[Set[int]] = None,
                                 verbose: bool = False,
                                 strict: bool = False,
                                 andreev: bool = False) -> Dict:
    """
    Search for a numerical positive witness for the Delaunay angle system.

    Searches for a numerically verified positive angle assignment. The
    constraints assume the intended triangulated-disk setting; this function
    does not itself certify a global embedding or exact infeasibility.
    In strict mode it maximizes one common margin for angles, boundary sums
    and dihedrals. Units are normalized by pi. It does not independently
    maximize dihedral slack or perform lexicographic optimization.

    Constraints:
    (a) All angles are positive
    (b) Sum of angles in each triangle equals π (scaled to 1)
    (c) Sum of angles around each interior vertex equals 2π (scaled to 2)
    (d) Sum of angles at each boundary vertex is ≤ π (scaled to ≤ 1)
        - If andreev=True: ≤ π/2 (scaled to ≤ 0.5)
    (e) For each interior edge, sum of two opposite angles (dihedral angle) ≤ π (scaled to ≤ 1)
        - If strict=True: < π (achieved by maximizing slack ε > 0 such that sum ≤ 1 - ε)
        - If andreev=True: ≤ π/2 (scaled to ≤ 0.5)

    Args:
        triangles: List of triangles, each given as (v0, v1, v2) tuple of vertex indices
        boundary_vertices: Set of boundary vertex indices (if None, auto-detect)
        verbose: If True, print detailed information
        strict: If True, require dihedral angles to be strictly < π (not = π)
        andreev: If True, require dihedral angles ≤ π/2 (Andreev's theorem)

    Returns:
        Dict with keys:
        - 'realizable': bool, True if a positive feasible witness is verified
        - 'min_angle': float, measured minimum normalized angle in the witness
        - 'slack': float, the guaranteed common normalized margin (strict=True)
        - 'angles': np.ndarray of shape (n_triangles, 3), angle assignment (if realizable)
        - 'status': int, optimization status from scipy
        - 'message': str, status message
    """
    triangles, boundary_vertices = _validate_rivin_inputs(triangles, boundary_vertices)
    n_triangles = len(triangles)
    n_angles = 3 * n_triangles  # 3 angles per triangle

    if boundary_vertices is None:
        boundary_vertices = extract_boundary_vertices(triangles)

    # Get all vertices
    all_vertices = set()
    for tri in triangles:
        all_vertices.update(tri)

    interior_vertices = all_vertices - boundary_vertices

    if verbose:
        print(f"Triangulation: {n_triangles} triangles, {len(all_vertices)} vertices")
        print(f"  Interior vertices: {len(interior_vertices)}")
        print(f"  Boundary vertices: {len(boundary_vertices)}")

    # Build vertex -> angles incidence
    vertex_angles = build_vertex_angle_incidence(triangles)

    # Build edge -> opposite angles mapping
    edge_opposite_angles = build_edge_adjacency(triangles)

    # Classify edges as interior (shared by 2 triangles) or boundary (only 1 triangle)
    interior_edges = {edge: angles for edge, angles in edge_opposite_angles.items() if len(angles) == 2}
    boundary_edges = {edge: angles for edge, angles in edge_opposite_angles.items() if len(angles) == 1}

    # Determine dihedral angle bound based on mode
    if andreev:
        dihedral_bound = 0.5  # π/2 in normalized units
        boundary_bound = 0.5  # π/2 for boundary vertices too
        mode_desc = "Andreev (dihedral ≤ π/2)"
    else:
        dihedral_bound = 1.0  # π in normalized units
        boundary_bound = 1.0  # π for boundary vertices
        mode_desc = "strict (dihedral < π)" if strict else "standard (dihedral ≤ π)"

    # LP formulation:
    # Standard mode: maximize t (minimum angle)
    # Strict mode: maximize a common positive margin, with t = ε.
    #
    # Variables:
    # - Standard: [angle[0,0], ..., angle[n-1,2], t]
    # - Strict: [angle[0,0], ..., angle[n-1,2], t, ε]
    #
    # Constraints:
    # - angle[i] >= t for all i (reformulated as -angle[i] + t <= 0)
    # - sum of angles in triangle = 1
    # - sum of angles around interior vertex = 2
    # - sum of angles around boundary vertex <= boundary_bound
    # - sum of two opposite angles across interior edge <= dihedral_bound - ε (if strict)
    #                                                     <= dihedral_bound (if not strict)

    if strict:
        n_vars = n_angles + 2  # angles + t + ε
        # A weighted epsilon/t tradeoff can set t=0 despite existence of a
        # strictly positive witness. Coupling t=epsilon below tests strict
        # feasibility through the common margin instead.
        c = np.zeros(n_vars)
        c[-1] = -1.0
        t_idx = -2
        eps_idx = -1
    else:
        n_vars = n_angles + 1  # angles + t
        # Objective: maximize t <=> minimize -t
        c = np.zeros(n_vars)
        c[-1] = -1.0  # coefficient for t
        t_idx = -1
        eps_idx = None

    # Inequality constraints: A_ub @ x <= b_ub
    # (a) angle[i] >= t  <=>  -angle[i] + t <= 0
    A_ub_list = []
    b_ub_list = []

    for i in range(n_angles):
        row = np.zeros(n_vars)
        row[i] = -1.0        # -angle[i]
        row[t_idx] = 1.0     # +t
        A_ub_list.append(row)
        b_ub_list.append(0.0)

    # (d) sum of angles at boundary vertex <= boundary_bound (< boundary_bound if strict)
    for vertex in boundary_vertices:
        row = np.zeros(n_vars)
        for tri_id, corner_id in vertex_angles[vertex]:
            angle_idx = 3 * tri_id + corner_id
            row[angle_idx] = 1.0
        if strict:
            row[eps_idx] = 1.0  # +ε (so constraint is: sum + ε <= boundary_bound)
        A_ub_list.append(row)
        b_ub_list.append(boundary_bound)

    # (e) sum of two opposite angles across interior edge <= dihedral_bound - ε (Delaunay condition)
    for edge, opposite_angles in interior_edges.items():
        assert len(opposite_angles) == 2, f"Interior edge {edge} should have exactly 2 opposite angles"
        row = np.zeros(n_vars)
        for tri_id, corner_id in opposite_angles:
            angle_idx = 3 * tri_id + corner_id
            row[angle_idx] = 1.0
        if strict:
            row[eps_idx] = 1.0  # +ε (so constraint is: sum + ε <= dihedral_bound)
        A_ub_list.append(row)
        b_ub_list.append(dihedral_bound)

    # Note: For strict mode, ε >= 0 is enforced via bounds below, not as a constraint

    A_ub = np.array(A_ub_list) if A_ub_list else np.zeros((0, n_vars))
    b_ub = np.array(b_ub_list) if b_ub_list else np.zeros(0)

    # Equality constraints: A_eq @ x == b_eq
    # (b) sum of angles in triangle = 1
    # (c) sum of angles around interior vertex = 2
    A_eq_list = []
    b_eq_list = []

    for tri_id in range(n_triangles):
        row = np.zeros(n_vars)
        for corner_id in range(3):
            angle_idx = 3 * tri_id + corner_id
            row[angle_idx] = 1.0
        A_eq_list.append(row)
        b_eq_list.append(1.0)  # scaled: sum = π becomes sum = 1

    for vertex in interior_vertices:
        row = np.zeros(n_vars)
        for tri_id, corner_id in vertex_angles[vertex]:
            angle_idx = 3 * tri_id + corner_id
            row[angle_idx] = 1.0
        A_eq_list.append(row)
        b_eq_list.append(2.0)  # scaled: sum = 2π becomes sum = 2

    if strict:
        row = np.zeros(n_vars)
        row[t_idx], row[eps_idx] = 1.0, -1.0
        A_eq_list.append(row)
        b_eq_list.append(0.0)

    A_eq = np.array(A_eq_list)
    b_eq = np.array(b_eq_list)

    if verbose:
        print(f"\nLP formulation ({mode_desc}):")
        if strict:
            print(f"  Variables: {n_vars} (angles: {n_angles}, t: 1, ε: 1)")
        else:
            print(f"  Variables: {n_vars} (angles: {n_angles}, t: 1)")
        print(f"  Inequality constraints: {A_ub.shape[0]}")
        print(f"    - Angle >= t: {n_angles}")
        print(f"    - Boundary vertex angle sum <= {boundary_bound}: {len(boundary_vertices)}")
        if strict:
            print(f"    - Interior edge opposite angles sum + ε <= {dihedral_bound}: {len(interior_edges)}")
        else:
            print(f"    - Interior edge opposite angles sum <= {dihedral_bound}: {len(interior_edges)}")
        print(f"  Equality constraints: {A_eq.shape[0]}")
        print(f"    - Triangle angle sum = 1: {n_triangles}")
        print(f"    - Interior vertex angle sum = 2: {len(interior_vertices)}")
        print("\n  Edge classification:")
        print(f"    - Interior edges: {len(interior_edges)}")
        print(f"    - Boundary edges: {len(boundary_edges)}")

    # Bounds: angles and t can be any real number (LP will constrain them)
    # Actually, we can bound t from below by 0 for numerical stability
    # For strict mode, ε >= 0 (must have positive slack)
    if strict:
        bounds = [(None, None)] * n_angles + [(0, None), (0, None)]  # t >= 0, ε >= 0
    else:
        bounds = [(None, None)] * n_angles + [(0, None)]  # t >= 0

    # Solve LP
    result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq,
                    bounds=bounds, method='highs')

    # Audit the original normalized equations, inequalities and bounds rather
    # than treating the optimizer's status flag as a feasibility certificate.
    # https://docs.scipy.org/doc/scipy/tutorial/optimize.html#linear-programming
    lp_tolerance = 1e-8
    candidate = None if result.x is None else np.asarray(result.x, dtype=float)
    finite_candidate = bool(candidate is not None and candidate.shape == (n_vars,)
                            and np.all(np.isfinite(candidate)))
    primal = {"finite_candidate": finite_candidate, "tolerance": lp_tolerance,
              "equality_residual": None, "inequality_violation": None,
              "bound_violation": None, "passed": False}
    if finite_candidate:
        equality_error = float(np.max(np.abs(A_eq @ candidate-b_eq), initial=0.0))
        inequality_error = float(np.max(A_ub @ candidate-b_ub, initial=0.0))
        bound_error = float(np.max(-candidate[n_angles:], initial=0.0))
        primal.update({"equality_residual": equality_error,
                       "inequality_violation": inequality_error,
                       "bound_violation": bound_error,
                       "passed": max(equality_error, inequality_error, bound_error) <= lp_tolerance})
    accepted = bool(result.success and result.status == 0 and primal["passed"])
    angles = None
    min_angle = 0.0
    slack = 0.0
    if accepted:
        angles = candidate[:n_angles].reshape(n_triangles, 3)
        min_angle = float(np.min(angles))
        if strict:
            slack = float(candidate[eps_idx])

    # Numerical positive-witness threshold, distinct from the residual audit.
    positive_witness_threshold = 1e-6
    if strict:
        realizable = (accepted and min_angle > positive_witness_threshold
                      and slack > positive_witness_threshold)
    else:
        realizable = accepted and min_angle > positive_witness_threshold

    message = str(result.message)
    if result.success and not accepted:
        message += "; rejected by original-constraint feasibility audit"
    if verbose:
        print(f"\nLP status: {result.status} - {message}")
        print(f"  Solver success: {result.success}; residual audit: {primal['passed']}")

    result_dict = {
        'realizable': realizable,
        'min_angle': min_angle,
        'min_angle_radians': min_angle * np.pi,
        'angles': angles,
        'angles_radians': angles * np.pi if angles is not None else None,
        'status': result.status,
        'solver_iterations': getattr(result, 'nit', None),
        'message': message,
        'success': accepted,
        'solver_success': bool(result.success),
        'primal_residuals': primal,
        'evidence_status': 'numerical_angle_feasibility' if accepted else 'not_verified',
        'feasibility_status': ('positive_witness_found' if realizable
                               else 'no_positive_witness_verified'),
        'positive_witness_threshold': positive_witness_threshold,
        'n_triangles': n_triangles,
        'n_vertices': len(all_vertices),
        'n_interior': len(interior_vertices),
        'n_boundary': len(boundary_vertices),
        'mode': mode_desc,
        'strict': strict,
        'andreev': andreev,
    }

    # Add slack information for strict mode
    if strict:
        result_dict['strict_objective'] = 'max_common_positive_margin'
        result_dict['slack'] = slack
        result_dict['slack_radians'] = slack * np.pi
        # Legacy max_dihedral fields are guaranteed upper bounds implied by
        # the common margin; actual measured margins are reported separately.
        result_dict['max_dihedral'] = dihedral_bound - slack
        result_dict['max_dihedral_radians'] = (dihedral_bound - slack) * np.pi
        actual_dihedrals = [sum(angles[t, k] for t, k in uses)
                            for uses in interior_edges.values()] if angles is not None else []
        actual_boundary = [sum(angles[t, k] for t, k in vertex_angles[v])
                           for v in boundary_vertices] if angles is not None else []
        result_dict['measured_min_dihedral_margin'] = (
            float(dihedral_bound-max(actual_dihedrals)) if actual_dihedrals else None)
        result_dict['measured_min_boundary_margin'] = (
            float(boundary_bound-max(actual_boundary)) if actual_boundary else None)

    return result_dict


def format_realizability_report(result: Dict) -> str:
    """
    Format the numerical angle-witness result without a geometric certificate.

    Args:
        result: Dictionary returned by check_delaunay_realizability

    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("NUMERICAL DELAUNAY ANGLE-FEASIBILITY CHECK")
    report.append("=" * 60)
    report.append(f"Triangulation: {result['n_triangles']} triangles, {result['n_vertices']} vertices")
    report.append(f"  Interior vertices: {result['n_interior']}")
    report.append(f"  Boundary vertices: {result['n_boundary']}")
    if result.get('strict', False):
        report.append("Objective: maximize the common angle/inequality margin")
    else:
        report.append("Objective: maximize the minimum angle")
    report.append("")

    if result['realizable']:
        report.append("✓ Positive angle witness verified numerically")
    else:
        report.append("✗ No positive angle witness verified by this run")
    if result['success']:
        report.append(f"  Measured min angle: {result['min_angle']:.9g} (normalized by pi)")
        report.append(f"  Measured min angle: {result['min_angle_radians']:.9g} radians")
        report.append(f"  Measured min angle: {np.degrees(result['min_angle_radians']):.9g}°")
        if result.get('strict', False):
            report.append(f"  Guaranteed common margin: {result['slack']:.9g} (normalized by pi)")
    threshold = result.get('positive_witness_threshold', 1e-6)
    report.append(f"  Required positive-witness margin: > {threshold:.9g} (normalized by pi)")
    report.append("Disk topology, a global embedding, and exact infeasibility are not certified.")

    report.append("")
    report.append(f"Solver status: {result['status']} - {result['message']}")
    report.append("=" * 60)

    return "\n".join(report)


def lobachevsky_function(theta: float) -> float:
    """Evaluate Lambda(theta) = D(exp(2i theta))/2 in binary64.

    The angle domain is the closed interval [0, pi], with removable endpoint
    values zero. This uses the canonical Bloch-Wigner kernel rather than a
    cutoff quadrature; it supplies neither exact arithmetic nor an enclosure.
    """
    from .geometry import bloch_wigner

    if not np.isfinite(theta) or not 0 <= theta <= np.pi:
        raise ValueError("theta must be finite and between zero and pi")
    if theta == 0 or theta == np.pi:
        return 0.0
    return 0.5*bloch_wigner(np.exp(2j*theta))


def lobachevsky_gradient(theta: float) -> float:
    """
    Compute the gradient of the Lobachevsky function: Λ'(θ) = -log(2sin(θ)).

    Args:
        theta: Finite angle strictly between zero and pi, in radians.

    Returns:
        Gradient value. The derivative diverges at both endpoints; no finite
        boundary sentinel is substituted.

    Raises:
        ValueError: If theta is outside the open angle domain.
    """
    if not np.isfinite(theta) or not 0 < theta < np.pi:
        raise ValueError("theta must be finite and strictly between zero and pi")
    return -np.log(2 * np.sin(theta))


def lobachevsky_hessian(theta: float) -> float:
    """
    Compute the Hessian (second derivative) of the Lobachevsky function: Λ''(θ) = -cot(θ).

    Args:
        theta: Finite angle strictly between zero and pi, in radians.

    Returns:
        Second derivative, negative below pi/2 and positive above pi/2.
        Concavity of tetrahedral volume holds on the constrained angle plane,
        not for each unconstrained scalar summand.

    Raises:
        ValueError: If theta is outside the open angle domain.
    """
    if not np.isfinite(theta) or not 0 < theta < np.pi:
        raise ValueError("theta must be finite and strictly between zero and pi")
    return -1.0 / np.tan(theta)


_RIVIN_RANK_RCOND = 1e-12


def _validate_rivin_inputs(triangles, boundary_vertices):
    """Validate the angle-complex data, without asserting disk topology."""
    from numbers import Integral

    faces = []
    for face in triangles:
        if len(face) != 3 or any(
            not isinstance(v, Integral) or isinstance(v, (bool, np.bool_))
            for v in face
        ):
            raise ValueError("each triangle must contain three integer labels")
        face = tuple(map(int, face))
        if len(set(face)) != 3:
            raise ValueError("triangle vertices must be distinct")
        faces.append(face)
    if not faces or len({tuple(sorted(face)) for face in faces}) != len(faces):
        raise ValueError("triangles must be nonempty and contain no duplicate faces")
    if any(len(uses) > 2 for uses in build_edge_adjacency(faces).values()):
        raise ValueError("an edge must have at most two incident triangles")
    actual_boundary = extract_boundary_vertices(faces)
    boundary = actual_boundary if boundary_vertices is None else set(boundary_vertices)
    if boundary != actual_boundary:
        raise ValueError("boundary_vertices must match the triangle-complex boundary")
    return faces, boundary


def _rivin_constraint_matrices(triangles, boundary_vertices):
    """Retain every original row; numerical rank is used only for solves."""
    n = 3 * len(triangles)
    incidence = build_vertex_angle_incidence(triangles)
    interior = sorted(set(incidence) - boundary_vertices)
    equalities = []
    for t in range(len(triangles)):
        row = np.zeros(n)
        row[3*t:3*t+3] = 1.0
        equalities.append(row)
    for vertex in interior:
        row = np.zeros(n)
        for t, k in incidence[vertex]:
            row[3*t+k] = 1.0
        equalities.append(row)
    inequalities, labels = [], []
    for edge, uses in sorted(build_edge_adjacency(triangles).items()):
        if len(uses) == 2:
            row = np.zeros(n)
            for t, k in uses:
                row[3*t+k] = 1.0
            inequalities.append(row)
            labels.append(f"dihedral {edge}")
    n_dihedrals = len(inequalities)
    for vertex in sorted(boundary_vertices):
        row = np.zeros(n)
        for t, k in incidence[vertex]:
            row[3*t+k] = 1.0
        inequalities.append(row)
        labels.append(f"boundary vertex {vertex}")
    return (
        np.asarray(equalities),
        np.array([np.pi] * len(triangles) + [2*np.pi] * len(interior)),
        np.asarray(inequalities).reshape(-1, n),
        np.full(len(inequalities), np.pi),
        labels,
        n_dihedrals,
    )


def _angle_structure_volume(x):
    """Accurate binary64 tetrahedral sum through the canonical BW kernel.

    Cyclically choose the largest sine as denominator, keeping each shape's
    modulus at most one. This is not an exact or interval evaluation.
    """
    from .geometry import bloch_wigner

    angles = np.asarray(x, dtype=float).reshape(-1, 3)
    if not np.all(np.isfinite(angles)) or np.any(angles <= 0) or np.any(angles >= np.pi):
        raise ValueError("volume evaluation requires positive nonflat angle triples")
    c = np.argmax(np.sin(angles), axis=1)
    order = (c[:, None] + np.array([1, 2, 0])) % 3
    a, b, c = np.take_along_axis(angles, order, axis=1).T
    shapes = (np.sin(b) / np.sin(c)) * np.exp(1j*a)
    return float(np.sum(bloch_wigner(shapes)))


def _angle_gradient(x):
    if not np.all(np.isfinite(x)) or np.any(x <= 0) or np.any(x >= np.pi):
        raise ValueError("volume derivatives require positive nonflat angles")
    return -np.log(2*np.sin(x))


def _newton_direction(x, null_basis):
    gradient = _angle_gradient(x)
    reduced = null_basis.T @ gradient
    # Near a flat angle the curvature can exceed binary64 range even while
    # the gradient remains finite. Use a genuine ascent direction in that
    # case; do not replace the angle or fabricate a finite curvature value.
    with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
        hessian = (null_basis * (-1/np.tan(x))[:, None]).T @ null_basis
    coordinates = reduced
    if np.all(np.isfinite(hessian)):
        try:
            coordinates = np.linalg.solve(hessian, -reduced)
        except np.linalg.LinAlgError:
            pass
    with np.errstate(over="ignore", invalid="ignore"):
        slope = float(reduced @ coordinates)
    if not np.all(np.isfinite(coordinates)) or not np.isfinite(slope) or slope <= 0:
        coordinates = reduced
    return null_basis @ coordinates, gradient, float(np.linalg.norm(reduced))


def _angle_armijo_step(x, direction, gradient, alpha, inequalities, rhs, tolerance):
    """Backtrack feasibly; count both initial and attempted candidate values."""
    evaluations = 1
    initial_value = _angle_structure_volume(x)
    slope = float(gradient @ direction)
    roundoff = 32*np.finfo(float).eps * max(1.0, abs(initial_value))
    for _ in range(80):
        candidate = x + alpha*direction
        feasible = (
            np.all(np.isfinite(candidate))
            and np.all(candidate > 0) and np.all(candidate < np.pi)
            and (not len(inequalities) or np.max(inequalities @ candidate - rhs) <= tolerance)
        )
        if feasible:
            evaluations += 1
            value = _angle_structure_volume(candidate)
            if value + roundoff >= initial_value + 1e-4*alpha*slope:
                return candidate, alpha, evaluations
        alpha *= 0.5
        if np.array_equal(x + alpha*direction, x):
            break
    return None, alpha, evaluations


def _angle_bound_step(x, direction):
    positive = direction > 0
    negative = direction < 0
    limits = [1.0]
    if np.any(positive):
        limits.append(0.995*float(np.min((np.pi-x[positive])/direction[positive])))
    if np.any(negative):
        limits.append(0.995*float(np.min(-x[negative]/direction[negative])))
    return min(limits)


def _newton_in_nullspace(x, N, verbose=False, tol=1e-12, max_iter=50, label=""):
    """Equality-preserving Newton ascent with an actual-volume line search.

    The caller supplies a valid positive triangle-angle structure and a basis
    preserving its equalities. No coordinate clipping is performed. Returns
    the historical (angles, iterations, converged, reduced-gradient norm).
    """
    x = np.asarray(x, dtype=float).copy()
    N = np.asarray(N, dtype=float)
    if x.ndim != 1 or x.size % 3 or N.ndim != 2 or N.shape[0] != len(x):
        raise ValueError("incompatible angle vector and null-space basis")
    if (isinstance(max_iter, (bool, np.bool_))
            or not isinstance(max_iter, (int, np.integer)) or max_iter < 0):
        raise ValueError("max_iter must be a nonnegative integer")
    if not np.isfinite(tol) or tol <= 0 or not np.all(np.isfinite(N)):
        raise ValueError("tol must be positive and finite, and the basis must be finite")
    _angle_gradient(x)
    iterations = 0
    for iteration in range(max_iter):
        direction, gradient, norm = _newton_direction(x, N)
        if verbose:
            print(f"  {label}iter {iteration}: reduced gradient {norm:.3e}")
        if norm <= tol:
            break
        candidate, _, _ = _angle_armijo_step(
            x, direction, gradient, _angle_bound_step(x, direction),
            np.zeros((0, len(x))), np.zeros(0), tol,
        )
        if candidate is None:
            break
        x = candidate
        iterations += 1
    final_norm = float(np.linalg.norm(N.T @ _angle_gradient(x)))
    return x, iterations, final_norm <= tol, final_norm


def _rivin_kkt_diagnostics(x, A, b, B, d, *, tolerance, null_basis=None):
    """Independent primal/dual check against every supplied constraint.

    For maximizing V under Bx <= d, grad(V) = A.T*lambda + B.T*mu,
    mu >= 0. Nonnegative least squares checks existence of multipliers even
    when binding rows are redundant; an unconstrained least-squares sign
    check alone is insufficient in that case.
    """
    from scipy.linalg import null_space
    from scipy.optimize import nnls

    gradient = _angle_gradient(x)
    N = null_space(A, rcond=_RIVIN_RANK_RCOND) if null_basis is None else null_basis
    slack = d - B @ x
    tight = np.flatnonzero(slack <= 10*tolerance)
    multipliers = np.zeros(len(B))
    dual_solver_success = True
    # scipy.optimize.nnls returns (nonnegative solution, residual norm).
    # https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.nnls.html
    if len(tight) and N.shape[1]:
        try:
            multipliers[tight], _ = nnls(
                N.T @ B[tight].T, N.T @ gradient,
                maxiter=max(100, 10*len(tight)),
            )
        except (RuntimeError, np.linalg.LinAlgError):
            dual_solver_success = False
    equality_multipliers = np.linalg.lstsq(
        A.T, gradient - B.T @ multipliers, rcond=_RIVIN_RANK_RCOND
    )[0]
    stationarity = gradient - A.T @ equality_multipliers - B.T @ multipliers
    equality_error = float(np.max(np.abs(A @ x - b), initial=0.0))
    inequality_error = float(np.max(-slack, initial=0.0))
    stationarity_error = float(np.linalg.norm(stationarity, ord=np.inf))
    complementarity_error = float(np.max(np.abs(multipliers*slack), initial=0.0))
    dual_error = float(np.max(-multipliers, initial=0.0))
    positive_angles = bool(np.all(x > 0) and np.all(x < np.pi))
    passed = (
        dual_solver_success and positive_angles and equality_error <= tolerance
        and inequality_error <= tolerance and stationarity_error <= tolerance
        and complementarity_error <= tolerance and dual_error <= tolerance
    )
    return {
        "passed": bool(passed), "tolerance": float(tolerance),
        "equality_residual": equality_error,
        "inequality_violation": inequality_error,
        "stationarity_residual": stationarity_error,
        "complementarity_residual": complementarity_error,
        "dual_sign_violation": dual_error,
        "positive_angles": positive_angles,
        "dual_solver_success": dual_solver_success,
        "equality_multipliers": equality_multipliers.tolist(),
        "inequality_multipliers": multipliers.tolist(),
        "binding_indices": tight.tolist(),
        "numerical_equality_rank": int(len(x)-N.shape[1]),
        "rank_rcond": _RIVIN_RANK_RCOND,
        "evidence_status": "numerical_kkt_check",
    }


def _solve_angle_polytope(x, A, b, B, d, *, max_iter, max_active_rounds,
                          tolerance, verbose=False):
    """Feasible active-set Newton, with blocker activation and dual release."""
    from scipy.linalg import null_space

    x = np.asarray(x, dtype=float).copy()
    base_null = null_space(A, rcond=_RIVIN_RANK_RCOND)
    active, history = [], []
    projected_rows = []
    # Select independent initially binding rows; retain all rows for auditing.
    for index in np.flatnonzero(d-B @ x <= tolerance):
        projected = B[index] @ base_null
        remainder = projected.copy()
        for q in projected_rows:
            remainder -= (remainder @ q)*q
        norm = np.linalg.norm(remainder)
        if norm > _RIVIN_RANK_RCOND*max(1.0, np.linalg.norm(projected)):
            projected_rows.append(remainder/norm)
            active.append(int(index))
    cached_active, N = None, base_null
    evaluations = changes = iterations = 0
    reason = "max_iterations"
    target = min(1e-12, tolerance*0.01)
    for iteration in range(max_iter):
        iterations = iteration+1
        if tuple(active) != cached_active:
            N = (base_null @ null_space(B[active] @ base_null, rcond=_RIVIN_RANK_RCOND)
                 if active else base_null)
            cached_active = tuple(active)
        direction, gradient, norm = _newton_direction(x, N)
        if verbose:
            print(f"  iter {iteration}: reduced gradient {norm:.3e}; active {len(active)}")
        if norm <= target:
            multipliers = np.linalg.lstsq(
                (B[active] @ base_null).T, base_null.T @ gradient,
                rcond=_RIVIN_RANK_RCOND,
            )[0] if active else np.zeros(0)
            if len(multipliers) and np.min(multipliers) < -tolerance:
                if changes >= max_active_rounds:
                    reason = "max_active_set_changes"
                    break
                position = int(np.argmin(multipliers))
                index = active.pop(position)
                history.append({"action": "release", "constraint_index": index,
                                "multiplier": float(multipliers[position]), "iteration": iteration})
                changes += 1
                continue
            reason = "stationary_working_set"
            break

        alpha = _angle_bound_step(x, direction)
        blocker = None
        slack = d-B @ x
        directional = B @ direction
        direction_floor = 64*np.finfo(float).eps*max(1.0, np.linalg.norm(direction))
        for index in range(len(B)):
            if index not in active and directional[index] > direction_floor:
                limit = max(0.0, float(slack[index]))/directional[index]
                if limit < alpha:
                    alpha, blocker = limit, index
        blocked_alpha = alpha
        if alpha == 0 and blocker is not None:
            candidate, accepted_alpha, count = x.copy(), alpha, 0
        else:
            candidate, accepted_alpha, count = _angle_armijo_step(
                x, direction, gradient, alpha, B, d, tolerance
            )
        evaluations += count
        if candidate is None:
            reason = "line_search_failed"
            break
        x = candidate
        if (blocker is not None and accepted_alpha == blocked_alpha
                and d[blocker]-B[blocker] @ x <= tolerance):
            if changes >= max_active_rounds:
                reason = "max_active_set_changes"
                break
            row_norm = np.linalg.norm(B[blocker] @ N)
            if row_norm <= _RIVIN_RANK_RCOND*max(1.0, np.linalg.norm(B[blocker])):
                reason = "numerically_dependent_blocker"
                break
            active.append(blocker)
            history.append({"action": "activate", "constraint_index": int(blocker),
                            "iteration": iteration})
            changes += 1
    # A zero budget can certify an already stationary feasible point, but
    # exhaustion never makes a nonstationary point successful.
    kkt = _rivin_kkt_diagnostics(x, A, b, B, d, tolerance=tolerance, null_basis=base_null)
    augmented = np.vstack([A, B[active]]) if active else A
    final_null = null_space(augmented, rcond=_RIVIN_RANK_RCOND)
    reduced_norm = float(np.linalg.norm(final_null.T @ _angle_gradient(x)))
    if kkt["passed"]:
        reason = "numerical_kkt_converged"
    return x, {
        "success": bool(kkt["passed"]), "termination_reason": reason,
        "n_iterations": iterations, "n_active_set_changes": changes,
        "n_volume_evaluations": evaluations, "active_set_history": history,
        "working_set_indices": active, "reduced_gradient_norm": reduced_norm,
        "kkt": kkt,
    }


def optimize_hyperbolic_volume(triangles: List[Tuple[int, int, int]],
                               initial_angles: Optional[np.ndarray] = None,
                               boundary_vertices: Optional[Set[int]] = None,
                               verbose: bool = False,
                               require_interior: bool = False,
                               *, max_iter: int = 300,
                               max_active_rounds: Optional[int] = None,
                               tolerance: float = 1e-10) -> Dict:
    """Numerically maximize volume on the specified positive angle polytope.

    Feasible projected Newton steps use an accurate-volume Armijo search.
    Inequalities can enter and leave the working set. Success requires an
    independent check of all original constraints, positive angles, and
    numerical KKT stationarity, dual signs and complementarity. This is not
    an exact/global-optimality or geometric-realization certificate.

    Exact flat triangles are outside this differentiable solver's domain.
    Nonpositive or infeasible starts are reported explicitly, never clipped.
    If no start is supplied, a residual-audited feasibility LP provides one.
    The final volume uses the canonical binary64 Bloch-Wigner kernel.

    require_interior rejects a final converged dihedral tie (within 1e-9 of
    pi), not a temporary working-set activation. Boundary-vertex equalities
    alone do not trigger it. Arithmeticity requires its separate downstream
    tests/certificates. max_iter and max_active_rounds bound iteration work
    and working-set changes, respectively; tolerance controls the residual
    acceptance tests. Existing return fields are retained with added method,
    termination and KKT diagnostics.

    n_volume_evaluations counts all objective calls, including each line
    search's initial value, rejected candidate values, and the final report
    value. n_iterations counts only angle-optimizer iterations; LP status,
    margins and solver_iterations are retained separately in feasibility_lp
    (None when the caller supplies initial_angles).
    """
    triangles, boundary_vertices = _validate_rivin_inputs(triangles, boundary_vertices)
    for name, value in (("max_iter", max_iter), ("max_active_rounds", max_active_rounds)):
        if value is not None and (isinstance(value, (bool, np.bool_))
                                  or not isinstance(value, (int, np.integer)) or value < 0):
            raise ValueError(f"{name} must be a nonnegative integer")
    if not np.isfinite(tolerance) or tolerance <= 0:
        raise ValueError("tolerance must be finite and positive")
    A, b, B, d, labels, n_dihedrals = _rivin_constraint_matrices(triangles, boundary_vertices)
    if max_active_rounds is None:
        max_active_rounds = max(20, 4*len(B))
    lp = None

    def failure(reason, message, angles=None, residuals=None):
        return {
            "success": False, "angles": angles, "volume": None,
            "message": message, "termination_reason": reason,
            "n_active_constraints": 0, "active_constraint_labels": [],
            "n_iterations": 0, "n_active_set_changes": 0,
            "n_volume_evaluations": 0, "feasibility_lp": lp,
            "reduced_gradient_norm": None, "residuals": residuals,
            "kkt": None, "volume_method": "bloch_wigner_binary64",
            "evidence_status": "not_verified", "active_set_history": [],
        }

    if initial_angles is None:
        lp = check_delaunay_realizability(triangles, boundary_vertices, verbose=False)
        if not lp["realizable"]:
            context = f"LP status {lp['status']}: {lp['message']}"
            if not lp["success"]:
                if not lp["solver_success"] or lp["status"] != 0:
                    return failure("feasibility_lp_failed", f"Feasibility LP solver failed. {context}")
                return failure("feasibility_lp_audit_failed",
                               f"Feasibility LP candidate failed the residual audit. {context}")
            return failure("no_positive_initial_witness",
                           "No positive initial angle witness verified: measured minimum "
                           f"{lp['min_angle']:.9g} (normalized by pi), required > "
                           f"{lp.get('positive_witness_threshold', 1e-6):.9g}. {context}")
        initial_angles = lp["angles_radians"]
    angles = np.asarray(initial_angles, dtype=float)
    if angles.shape != (len(triangles), 3) or not np.all(np.isfinite(angles)):
        raise ValueError("initial_angles must be finite with shape (n_triangles, 3)")
    residuals = compute_rivin_angle_residuals(
        triangles, angles, boundary_vertices, tolerance=tolerance
    )
    if np.any(angles <= 0) or np.any(angles >= np.pi):
        return failure("nonpositive_or_flat_initial_angles",
                       "Positive nonflat angles are required; no clipping was performed", angles.copy(), residuals)
    x = angles.ravel().copy()
    if (np.max(np.abs(A @ x-b), initial=0) > tolerance
            or np.max(B @ x-d, initial=0) > tolerance):
        return failure("infeasible_initial_angles", "Initial angles violate the original constraints",
                       angles.copy(), residuals)
    # Correct only roundoff-size affine residuals via a rank-revealing solve.
    # All original rows remain in both the final audit and residual output.
    correction = np.linalg.lstsq(A, b-A @ x, rcond=_RIVIN_RANK_RCOND)[0]
    candidate = x+correction
    if np.all(candidate > 0) and np.all(candidate < np.pi) and np.max(B @ candidate-d, initial=0) <= tolerance:
        x = candidate
    x, diagnostics = _solve_angle_polytope(
        x, A, b, B, d, max_iter=max_iter, max_active_rounds=max_active_rounds,
        tolerance=tolerance, verbose=verbose,
    )
    final_angles = x.reshape(-1, 3)
    residuals = compute_rivin_angle_residuals(
        triangles, final_angles, boundary_vertices, tolerance=tolerance
    )
    binding = diagnostics["kkt"]["binding_indices"]
    max_dihedral = float(np.max(B[:n_dihedrals] @ x, initial=0.0))
    rejected_tie = bool(require_interior and diagnostics["success"]
                        and n_dihedrals and max_dihedral >= np.pi-1e-9)
    success = bool(diagnostics["success"] and residuals["feasible"] and not rejected_tie)
    message = "Numerical primal and KKT checks passed" if success else diagnostics["termination_reason"]
    if rejected_tie:
        message = "Rejected: final cocircular tie within 1e-9 of pi (require_interior)"
    diagnostics["n_volume_evaluations"] += 1
    final_volume = _angle_structure_volume(x)
    return {
        **diagnostics, "success": success, "angles": final_angles,
        "volume": final_volume, "volume_method": "bloch_wigner_binary64",
        "feasibility_lp": lp,
        "n_active_constraints": len(binding),
        "active_constraint_labels": [labels[i] for i in binding],
        "constraint_labels": labels,
        "max_dihedral_angle": max_dihedral, "message": message,
        "rejected_tie": rejected_tie, "residuals": residuals,
        "evidence_status": "numerical_kkt_check" if diagnostics["success"] else "not_verified",
    }


def legalize_to_interior_maximum(
    triangles: List[Tuple[int, int, int]],
    boundary_vertices: Optional[Set[int]] = None,
    *,
    max_flips: int = 64,
    margin_tolerance: float = 1e-4,
    constraint_tolerance: float = 1e-6,
    verbose: bool = False,
) -> Dict:
    """Legalize a finite Delaunay disk toward a strict Rivin maximum.

    A rejected unconstrained maximum identifies an interior edge whose
    opposite-angle sum reaches or exceeds ``pi``.  Flipping the worst such
    edge and resolving is the angle-structure analogue of deterministic
    Delaunay legalization.  The process is bounded by ``max_flips`` and by
    orientation-independent cycle detection.

    Acceptance is deliberately stronger than
    ``optimize_hyperbolic_volume(..., require_interior=True)``: the optimizer
    must converge with no active constraints, equality residuals and angle
    positivity must satisfy ``constraint_tolerance``, and both interior-edge
    and boundary-vertex margins must be at least ``margin_tolerance``.  The
    boundary test certifies strictness after the disk is coned to its implicit
    vertex at infinity.

    Returns a structured dictionary.  ``finite_triangulation`` always holds
    the last valid oriented disk, including on failure.  ``termination_reason``
    is one of ``accepted``, ``max_flips``, ``cycle_detected``, ``lp_failure``,
    ``optimizer_failure``, ``residual_failure``, ``insufficient_margin``, or
    ``unflippable_edge``.
    """
    if isinstance(max_flips, bool) or int(max_flips) != max_flips or max_flips < 0:
        raise ValueError("max_flips must be a nonnegative integer")
    max_flips = int(max_flips)
    for name, value in (
        ("margin_tolerance", margin_tolerance),
        ("constraint_tolerance", constraint_tolerance),
    ):
        if not np.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite nonnegative number")

    current = []
    for face in triangles:
        if len(face) != 3:
            raise ValueError(f"each triangle must contain three vertices: {face}")
        normalized_face = []
        for vertex in face:
            if isinstance(vertex, bool) or int(vertex) != vertex or vertex < 0:
                raise ValueError(
                    f"triangle vertices must be nonnegative integers: {face}"
                )
            normalized_face.append(int(vertex))
        oriented_face = tuple(normalized_face)
        if len(set(oriented_face)) != 3:
            raise ValueError(f"triangle vertices must be distinct: {face}")
        current.append(oriented_face)
    if not current:
        raise ValueError("triangles must be nonempty")

    canonical_faces = [tuple(sorted(face)) for face in current]
    if len(set(canonical_faces)) != len(canonical_faces):
        raise ValueError("triangles contains a duplicate face")

    all_vertices = {vertex for face in current for vertex in face}
    n_finite_vertices = len(all_vertices)
    if all_vertices != set(range(n_finite_vertices)):
        raise ValueError(
            "triangle vertex labels must be contiguous from 0 through "
            f"{n_finite_vertices - 1}"
        )

    # The boundary-completion service owns the project's strict finite-disk
    # validation: one connected boundary cycle, Euler characteristic one,
    # manifold vertex links, face connectivity, and orientability.  Its
    # finite prefix is also a coherently wound copy of the input disk.
    # Import locally to keep this legacy numerical module independent at
    # import time.
    from .optimization import complete_boundary_triangulation

    completed = complete_boundary_triangulation(
        np.asarray(current, dtype=np.int64),
        n_finite_vertices,
    )
    current = [
        tuple(map(int, face)) for face in completed[:len(current)]
    ]
    actual_boundary = extract_boundary_vertices(current)

    if boundary_vertices is None:
        fixed_boundary = actual_boundary
    else:
        fixed_boundary = set()
        for vertex in boundary_vertices:
            if isinstance(vertex, bool) or int(vertex) != vertex or vertex < 0:
                raise ValueError(
                    "boundary_vertices must contain nonnegative integer labels"
                )
            fixed_boundary.add(int(vertex))
        if fixed_boundary != actual_boundary:
            raise ValueError(
                "boundary_vertices must exactly match the triangulated disk "
                f"boundary {sorted(actual_boundary)}"
            )

    start_time = time.perf_counter()
    lp_seconds = 0.0
    optimization_seconds = 0.0
    history = []
    seen_states = set()
    flips_completed = 0
    final_optimization = None
    final_residuals = None

    def finish(reason, message, *, optimization=None, residuals=None):
        result_angles = None if optimization is None else optimization.get("angles")
        result_volume = None if optimization is None else optimization.get("volume")
        return {
            "success": reason == "accepted",
            "termination_reason": reason,
            "message": message,
            "finite_triangulation": list(current),
            "angles": result_angles,
            "volume": result_volume,
            "n_flips": flips_completed,
            "n_states": len(history),
            "residuals": residuals,
            "optimization_result": optimization,
            "history": history,
            "timings": {
                "total_seconds": float(time.perf_counter() - start_time),
                "lp_seconds": float(lp_seconds),
                "optimization_seconds": float(optimization_seconds),
            },
        }

    while True:
        state_key = tuple(sorted(tuple(sorted(face)) for face in current))
        if state_key in seen_states:
            return finish(
                "cycle_detected",
                "Legalization revisited a previously evaluated triangulation",
            )
        seen_states.add(state_key)

        step = flips_completed
        lp_start = time.perf_counter()
        lp_result = check_delaunay_realizability(
            current,
            boundary_vertices=fixed_boundary,
            verbose=False,
        )
        lp_elapsed = time.perf_counter() - lp_start
        lp_seconds += lp_elapsed
        history_row = {
            "step": step,
            "lp_realizable": bool(lp_result["realizable"]),
            "lp_min_angle": float(lp_result.get("min_angle", 0.0)),
            "lp_slack": (
                float(lp_result["slack"])
                if lp_result.get("slack") is not None
                else None
            ),
            "lp_seconds": float(lp_elapsed),
            "optimizer_success": None,
            "optimizer_message": None,
            "optimizer_iterations": None,
            "optimizer_active_constraints": None,
            "optimizer_reduced_gradient_norm": None,
            "optimizer_rejected_tie": False,
            "optimization_seconds": 0.0,
            "residuals": None,
            "flipped_edge": None,
            "status": None,
        }
        if not lp_result["realizable"]:
            history_row["status"] = "lp_failure"
            history.append(history_row)
            return finish(
                "lp_failure",
                "Rivin LP did not verify a positive initial angle witness "
                f"(status {lp_result['status']}): {lp_result['message']}",
            )

        optimization_start = time.perf_counter()
        optimization_result = optimize_hyperbolic_volume(
            current,
            initial_angles=lp_result["angles_radians"],
            boundary_vertices=fixed_boundary,
            verbose=False,
            require_interior=True,
        )
        optimization_elapsed = time.perf_counter() - optimization_start
        optimization_seconds += optimization_elapsed
        optimized_angles = optimization_result.get("angles")
        if optimized_angles is not None:
            # Always recompute with the caller's tolerance.  Optimizer-owned
            # residuals use its default tolerance and must not decide this
            # higher-level acceptance contract when the caller overrides it.
            final_residuals = compute_rivin_angle_residuals(
                current,
                optimized_angles,
                fixed_boundary,
                tolerance=constraint_tolerance,
            )
            optimization_result = {
                **optimization_result,
                "residuals": final_residuals,
            }
        else:
            final_residuals = None
        final_optimization = optimization_result

        history_row.update({
            "optimizer_success": bool(optimization_result["success"]),
            "optimizer_message": optimization_result.get("message"),
            "optimizer_iterations": optimization_result.get("n_iterations"),
            "optimizer_active_constraints": optimization_result.get(
                "n_active_constraints"
            ),
            "optimizer_reduced_gradient_norm": optimization_result.get(
                "reduced_gradient_norm"
            ),
            "optimizer_rejected_tie": bool(
                optimization_result.get("rejected_tie", False)
            ),
            "optimization_seconds": float(optimization_elapsed),
            "residuals": final_residuals,
        })

        if optimization_result["success"]:
            equality_ok = (
                final_residuals is not None
                and final_residuals["max_equality_residual"]
                <= constraint_tolerance
                and final_residuals["min_angle"] > constraint_tolerance
            )
            if not equality_ok:
                history_row["status"] = "residual_failure"
                history.append(history_row)
                return finish(
                    "residual_failure",
                    "Optimizer converged but equality or angle residuals failed",
                    optimization=final_optimization,
                    residuals=final_residuals,
                )

            dihedral_margin = final_residuals["min_dihedral_margin"]
            boundary_margin = final_residuals["min_boundary_margin"]
            margins_ok = (
                (dihedral_margin is None or dihedral_margin >= margin_tolerance)
                and (boundary_margin is None or boundary_margin >= margin_tolerance)
                and optimization_result.get("n_active_constraints", 0) == 0
            )
            if not margins_ok:
                history_row["status"] = "insufficient_margin"
                history.append(history_row)
                return finish(
                    "insufficient_margin",
                    "Optimizer converged without the requested strict margins",
                    optimization=final_optimization,
                    residuals=final_residuals,
                )

            history_row["status"] = "accepted"
            history.append(history_row)
            if verbose:
                print(
                    f"Accepted strict interior maximum after "
                    f"{flips_completed} flip(s)"
                )
            return finish(
                "accepted",
                "Strict interior Rivin maximum found",
                optimization=final_optimization,
                residuals=final_residuals,
            )

        if not optimization_result.get("rejected_tie", False):
            history_row["status"] = "optimizer_failure"
            history.append(history_row)
            return finish(
                "optimizer_failure",
                f"Volume optimizer failed: {optimization_result.get('message')}",
                optimization=final_optimization,
                residuals=final_residuals,
            )

        worst_edge = (
            None
            if final_residuals is None
            else final_residuals.get("worst_dihedral_edge")
        )
        if worst_edge is None:
            history_row["status"] = "optimizer_failure"
            history.append(history_row)
            return finish(
                "optimizer_failure",
                "Tie rejection did not identify an interior edge",
                optimization=final_optimization,
                residuals=final_residuals,
            )
        if flips_completed >= max_flips:
            history_row["status"] = "max_flips"
            history.append(history_row)
            return finish(
                "max_flips",
                f"Reached the maximum of {max_flips} edge flips",
                optimization=final_optimization,
                residuals=final_residuals,
            )

        flipped = flip_edge(current, worst_edge)
        history_row["flipped_edge"] = worst_edge
        if flipped is None:
            history_row["status"] = "unflippable_edge"
            history.append(history_row)
            return finish(
                "unflippable_edge",
                f"Worst violating edge {worst_edge} is not flippable",
                optimization=final_optimization,
                residuals=final_residuals,
            )

        history_row["status"] = "flipped"
        history.append(history_row)
        current = flipped
        flips_completed += 1
        if verbose:
            margin = final_residuals.get("min_dihedral_margin")
            print(
                f"Flip {flips_completed}/{max_flips}: edge {worst_edge}, "
                f"dihedral margin {margin:.3e}"
            )


def compute_triangle_angle(p1: np.ndarray, p2: np.ndarray, p3: np.ndarray) -> float:
    """
    Compute the angle at vertex p1 in triangle (p1, p2, p3).

    Args:
        p1, p2, p3: 2D points as arrays

    Returns:
        Angle at p1 in radians
    """
    # Normalize each ray before taking dot and cross products.  ``hypot`` is
    # scale-stable for very small and very large coordinates, while arccos of
    # a rounded cosine loses near-collinear angles.  A zero-length ray is a
    # degenerate triangle; returning zero keeps optimization penalties finite
    # and makes that behavior explicit rather than relying on atan2(0, 0).
    v1 = np.asarray(p2, dtype=float) - np.asarray(p1, dtype=float)
    v2 = np.asarray(p3, dtype=float) - np.asarray(p1, dtype=float)
    if v1.shape != (2,) or v2.shape != (2,):
        raise ValueError("triangle points must be two-dimensional vectors")

    norm1 = float(np.hypot(v1[0], v1[1]))
    norm2 = float(np.hypot(v2[0], v2[1]))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    unit1 = v1 / norm1
    unit2 = v2 / norm2
    cross = float(unit1[0] * unit2[1] - unit1[1] * unit2[0])
    dot = float(np.dot(unit1, unit2))
    return float(np.arctan2(abs(cross), dot))


def realize_angles_as_points(triangles: List[Tuple[int, int, int]],
                            target_angles: np.ndarray,
                            boundary_vertices: Optional[Set[int]] = None,
                            verbose: bool = False) -> Dict:
    """
    Construct a geometric realization of a triangulation with given angles.

    Given target angles for each corner of each triangle, find 2D point positions
    that realize those angles (approximately).

    This is an inverse problem: angles → geometry. We solve it via optimization.

    Args:
        triangles: List of triangles as (v0, v1, v2) tuples
        target_angles: Array of shape (n_triangles, 3) with target angles in radians
        boundary_vertices: Set of boundary vertices (auto-detected if None)
        verbose: If True, print progress

    Returns:
        Dict with keys:
        - 'success': bool
        - 'points': np.ndarray of shape (n_vertices, 2) with 2D coordinates
        - 'angle_error': float, RMS error in angles
        - 'message': str
    """
    if boundary_vertices is None:
        boundary_vertices = extract_boundary_vertices(triangles)
    target_angle_residuals = compute_rivin_angle_residuals(
        triangles,
        target_angles,
        boundary_vertices,
    )

    # Get all vertices
    all_vertices = set()
    for tri in triangles:
        all_vertices.update(tri)
    n_vertices = len(all_vertices)

    # Create vertex index mapping
    vertex_list = sorted(all_vertices)
    vertex_to_idx = {v: i for i, v in enumerate(vertex_list)}

    if verbose:
        print("Reconstructing geometry from angles...")
        print(f"  Vertices: {n_vertices}")
        print(f"  Triangles: {len(triangles)}")

    # Fix translation, rotation, and scale by setting:
    # - First vertex at origin (0, 0) - fixes translation (2 DOF)
    # - Second vertex at (1, 0) - fixes rotation and scale (2 DOF)
    # This gives us exactly 4 constraints for 4 degrees of freedom

    v0 = vertex_list[0]
    v1 = vertex_list[1]

    fixed_points = {}
    fixed_points[v0] = np.array([0.0, 0.0])
    fixed_points[v1] = np.array([1.0, 0.0])

    # Identify free vertices (all except first two)
    free_vertices = [v for v in vertex_list if v not in fixed_points]
    n_free = len(free_vertices)

    if verbose:
        print(f"  Fixed vertices: {len(fixed_points)} (at 0 and 1)")
        print(f"  Free vertices: {n_free}")

    # Incremental graph-based construction
    # Place vertices one by one using angle constraints from already-placed neighbors
    if verbose:
        print("  Constructing geometry incrementally using angle constraints...")

    from scipy.spatial import Delaunay as scipy_Delaunay
    expected_triangulation_set = set(tuple(sorted(tri)) for tri in triangles)

    # Developing-map layout (exact similar-triangle construction).
    #
    # The previous implementation placed each new vertex at the apex of an
    # ISOSCELES triangle over the base edge (height = (L/2)/tan(theta/2)),
    # which satisfies the apex angle but generically violates the other two
    # prescribed angles by tens of degrees, and chose the side of the edge
    # arbitrarily (the pos1/pos2 "scores" were identical).  That produced
    # the 27-38 degree angle errors observed on 50/100-vertex Rivin-optimal
    # angle structures.
    #
    # The correct construction develops the triangulated disk across shared
    # edges: each triangle's shape is determined exactly by its three target
    # angles (law of sines), and the new vertex is placed on the OPPOSITE
    # side of the shared edge from the already-placed triangle, giving a
    # consistent orientation.  At Rivin's critical point the log-sin edge
    # conditions are precisely the closure conditions of this developing
    # map, so re-visited vertices reproduce their positions up to numerical
    # error (reported as closure_error).

    closure_error = [0.0]

    def construct_from_angles():
        """Develop the triangulation across shared edges with exact
        per-triangle shapes given by target_angles.  Returns the point
        array, or None if the dual graph is disconnected."""
        points = np.zeros((n_vertices, 2))

        # edge -> list of (tri_id, opposite_vertex)
        edge_tris = {}
        for tid, tri in enumerate(triangles):
            for k in range(3):
                e = tuple(sorted((tri[k], tri[(k + 1) % 3])))
                edge_tris.setdefault(e, []).append((tid, tri[(k + 2) % 3]))

        def angle_at(tid, v):
            tri = triangles[tid]
            return target_angles[tid][list(tri).index(v)]

        def third_position(tid, u, v, w, side_sign):
            """Position of w in triangle tid given placed u, v; side_sign
            = +1 places w to the left of the directed edge u->v."""
            pu = points[vertex_to_idx[u]]
            pv = points[vertex_to_idx[v]]
            au = angle_at(tid, u)
            aw = angle_at(tid, w)
            av = angle_at(tid, v)
            d = pv - pu
            L = np.hypot(d[0], d[1])
            if L < 1e-14 or np.sin(aw) < 1e-14:
                return None
            r = L * np.sin(av) / np.sin(aw)  # |uw| by the law of sines
            c, s = np.cos(au), np.sin(au) * side_sign
            rot = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]]) / L
            return pu + r * rot

        placed_vertices = set()
        placed_tris = set()

        # Seed: first triangle, first edge along (0,0)-(1,0), apex above.
        t0 = 0
        u0, v0_, w0 = triangles[t0]
        points[vertex_to_idx[u0]] = np.array([0.0, 0.0])
        points[vertex_to_idx[v0_]] = np.array([1.0, 0.0])
        pw = third_position(t0, u0, v0_, w0, +1.0)
        if pw is None:
            return None
        points[vertex_to_idx[w0]] = pw
        placed_vertices.update((u0, v0_, w0))
        placed_tris.add(t0)

        from collections import deque
        queue = deque([t0])
        while queue:
            t1 = queue.popleft()
            tri1 = triangles[t1]
            for k in range(3):
                a, b = tri1[k], tri1[(k + 1) % 3]
                e = tuple(sorted((a, b)))
                for (t2, w2) in edge_tris[e]:
                    if t2 in placed_tris:
                        continue
                    # third vertex of t1 across this edge
                    w1 = tri1[(k + 2) % 3]
                    pa = points[vertex_to_idx[a]]
                    pb = points[vertex_to_idx[b]]
                    pw1 = points[vertex_to_idx[w1]]
                    dx = pb - pa
                    cross1 = dx[0] * (pw1[1] - pa[1]) - dx[1] * (pw1[0] - pa[0])
                    side_sign = -1.0 if cross1 > 0 else +1.0
                    pos = third_position(t2, a, b, w2, side_sign)
                    if pos is None:
                        return None
                    idx = vertex_to_idx[w2]
                    if w2 in placed_vertices:
                        closure_error[0] = max(
                            closure_error[0],
                            float(np.hypot(*(points[idx] - pos))))
                    else:
                        points[idx] = pos
                        placed_vertices.add(w2)
                    placed_tris.add(t2)
                    queue.append(t2)

        if len(placed_tris) < len(triangles) or len(placed_vertices) < n_vertices:
            if verbose:
                print(f"    Developing map incomplete: "
                      f"{len(placed_tris)}/{len(triangles)} triangles, "
                      f"{len(placed_vertices)}/{n_vertices} vertices")
            return None

        if verbose:
            print(f"    Developing map complete; closure error = "
                  f"{closure_error[0]:.3e}")
        return points

    points_constructed = construct_from_angles()

    if points_constructed is None:
        # Construction failed
        if verbose:
            print("    ✗ Incremental construction failed")
        return {
            'success': False,
            'points': None,
            'vertex_list': vertex_list,
            'volume': None,
            'triangulation_preserved': False,
            'angle_error': None,
            'angle_error_degrees': None,
            'max_angle_error': None,
            'max_angle_error_degrees': None,
            'closure_error': None,
            'orientation_consistent': False,
            'min_abs_oriented_area': None,
            'residuals': {
                'rms_angle_error': None,
                'max_angle_error': None,
                'closure_error': None,
                'orientation_consistent': False,
                'min_abs_oriented_area': None,
                'target_angle_structure': target_angle_residuals,
                'realized_angle_structure': None,
            },
            'message': 'Incremental construction failed',
            'n_iterations': 0,
        }

    points = points_constructed

    def triangulation_is_delaunay(pts, tol=1e-7):
        """Is the TARGET triangulation a Delaunay triangulation of pts?

        Robust to ties: at Rivin's volume maximum some interior edges are
        exactly cocircular (active constraints), so scipy's Delaunay picks
        an arbitrary diagonal there and a strict set-equality test fails
        spuriously.  By Delaunay's lemma, an embedded triangulation with a
        convex boundary is (a) Delaunay iff every interior edge is locally
        Delaunay; with angles available, "locally Delaunay" is exactly
        opposite-angle sum <= pi (+ tol for ties).
        Checks: (1) all triangles consistently oriented (embedding),
        (2) every interior edge locally Delaunay within tol,
        (3) boundary convex (angle sums at boundary vertices <= pi + tol).
        """
        # (1) consistent orientation
        signs = []
        for (a, b, c) in triangles:
            pa, pb, pc = (pts[vertex_to_idx[a]], pts[vertex_to_idx[b]],
                          pts[vertex_to_idx[c]])
            cr = (pb[0]-pa[0])*(pc[1]-pa[1]) - (pb[1]-pa[1])*(pc[0]-pa[0])
            signs.append(np.sign(cr))
            if abs(cr) < 1e-14:
                return False
        if len(set(signs)) > 1:
            return False
        # actual corner angles from the layout
        def corner(pa, pb, pc):
            return compute_triangle_angle(pa, pb, pc)
        # (2) local Delaunay per interior edge
        edge_opp = {}
        for tid, (a, b, c) in enumerate(triangles):
            tri_pts = {a: pts[vertex_to_idx[a]], b: pts[vertex_to_idx[b]],
                       c: pts[vertex_to_idx[c]]}
            for (x, y, o) in ((a, b, c), (b, c, a), (c, a, b)):
                e = tuple(sorted((x, y)))
                ang = corner(tri_pts[o], tri_pts[x], tri_pts[y])
                edge_opp.setdefault(e, []).append(ang)
        vertex_sums = {}
        for tid, (a, b, c) in enumerate(triangles):
            pa, pb, pc = (pts[vertex_to_idx[a]], pts[vertex_to_idx[b]],
                          pts[vertex_to_idx[c]])
            vertex_sums[a] = vertex_sums.get(a, 0.0) + corner(pa, pb, pc)
            vertex_sums[b] = vertex_sums.get(b, 0.0) + corner(pb, pc, pa)
            vertex_sums[c] = vertex_sums.get(c, 0.0) + corner(pc, pa, pb)
        for e, angs in edge_opp.items():
            if len(angs) == 2 and angs[0] + angs[1] > np.pi + tol:
                return False
        # (3) convex boundary
        for v in boundary_vertices:
            if vertex_sums.get(v, 0.0) > np.pi + tol:
                return False
        return True

    # Check initial triangulation: exact scipy match, else the tie-robust
    # local-Delaunay certificate.
    try:
        tri = scipy_Delaunay(points)
        current_triangles = set()
        for simplex in tri.simplices:
            v0, v1, v2 = [vertex_list[i] for i in simplex]
            current_triangles.add(tuple(sorted([v0, v1, v2])))
        initial_tri_correct = (current_triangles == expected_triangulation_set)
        if not initial_tri_correct and triangulation_is_delaunay(points):
            initial_tri_correct = True
            if verbose:
                print("    ✓ Target triangulation is Delaunay for the layout "
                      "(scipy picked other diagonals on cocircular ties)")
        elif verbose and initial_tri_correct:
            print("    ✓ Initial geometry has correct triangulation!")
        elif verbose:
            print("    ⚠ Initial triangulation mismatch:")
            print(f"    Expected {len(expected_triangulation_set)} triangles, got {len(current_triangles)}")
            print("    Will refine using optimization...")
    except Exception as e:
        if verbose:
            print(f"    ⚠ Triangulation check failed: {e}")
        initial_tri_correct = False

    # Refine using optimization (if triangulation not perfect)
    if not initial_tri_correct:
        if verbose:
            print("  Refining geometry with optimization...")

        # Extract initial coordinates for free vertices
        initial_coords = np.zeros(n_free * 2)
        for i, v in enumerate(free_vertices):
            initial_coords[2*i:2*i+2] = points[vertex_to_idx[v]]

        def objective_with_penalty(x):
            """Minimize angle error with soft triangulation penalty."""
            # Reconstruct points
            pts = np.zeros((n_vertices, 2))
            for v, pos in fixed_points.items():
                pts[vertex_to_idx[v]] = pos
            for i, v in enumerate(free_vertices):
                pts[vertex_to_idx[v]] = x[2*i:2*i+2]

            # Angle error
            angle_err = 0.0
            for tri_id, (v0, v1, v2) in enumerate(triangles):
                p0 = pts[vertex_to_idx[v0]]
                p1 = pts[vertex_to_idx[v1]]
                p2 = pts[vertex_to_idx[v2]]

                angle0 = compute_triangle_angle(p0, p1, p2)
                angle1 = compute_triangle_angle(p1, p2, p0)
                angle2 = compute_triangle_angle(p2, p0, p1)

                target = target_angles[tri_id]
                angle_err += (angle0 - target[0])**2
                angle_err += (angle1 - target[1])**2
                angle_err += (angle2 - target[2])**2

            # Triangulation penalty
            try:
                tri = scipy_Delaunay(pts)
                curr_tris = set()
                for simplex in tri.simplices:
                    v0, v1, v2 = [vertex_list[i] for i in simplex]
                    curr_tris.add(tuple(sorted([v0, v1, v2])))

                if curr_tris != expected_triangulation_set:
                    n_missing = len(expected_triangulation_set - curr_tris)
                    n_extra = len(curr_tris - expected_triangulation_set)
                    penalty = 1000.0 * (n_missing + n_extra)  # Strong penalty
                else:
                    penalty = 0.0
            except Exception:
                penalty = 10000.0

            return angle_err + penalty

        from scipy.optimize import minimize
        opt_result = minimize(
            objective_with_penalty,
            initial_coords,
            method='L-BFGS-B',
            options={'maxiter': 2000, 'ftol': 1e-12}  # More iterations
        )

        # Update points with optimized coordinates
        for i, v in enumerate(free_vertices):
            points[vertex_to_idx[v]] = opt_result.x[2*i:2*i+2]

        if verbose:
            print(f"    Optimization completed ({opt_result.nit} iterations)")

    # Final triangulation check (exact match, else tie-robust certificate)
    try:
        tri = scipy_Delaunay(points)
        current_triangles = set()
        for simplex in tri.simplices:
            v0, v1, v2 = [vertex_list[i] for i in simplex]
            current_triangles.add(tuple(sorted([v0, v1, v2])))
        triangulation_correct = (current_triangles == expected_triangulation_set) \
            or triangulation_is_delaunay(points)
    except Exception:
        triangulation_correct = False

    # Compute angle error and volume
    angle_errors = []
    angle_differences = []
    realized_angles = np.zeros_like(np.asarray(target_angles, dtype=float))
    final_volume = 0.0

    for tri_id, (v0, v1, v2) in enumerate(triangles):
        p0 = points[vertex_to_idx[v0]]
        p1 = points[vertex_to_idx[v1]]
        p2 = points[vertex_to_idx[v2]]

        angle0 = compute_triangle_angle(p0, p1, p2)
        angle1 = compute_triangle_angle(p1, p2, p0)
        angle2 = compute_triangle_angle(p2, p0, p1)

        actual = np.array([angle0, angle1, angle2])
        target = target_angles[tri_id]
        difference = actual - target
        realized_angles[tri_id] = actual
        angle_differences.extend(difference)
        angle_errors.extend(difference**2)

        # Compute volume
        final_volume += lobachevsky_function(angle0)
        final_volume += lobachevsky_function(angle1)
        final_volume += lobachevsky_function(angle2)

    rms_error = np.sqrt(np.mean(angle_errors))
    max_angle_error = float(np.max(np.abs(angle_differences)))

    signed_double_areas = []
    for v0, v1, v2 in triangles:
        p0 = points[vertex_to_idx[v0]]
        p1 = points[vertex_to_idx[v1]]
        p2 = points[vertex_to_idx[v2]]
        signed_double_areas.append(
            float(
                (p1[0] - p0[0]) * (p2[1] - p0[1])
                - (p1[1] - p0[1]) * (p2[0] - p0[0])
            )
        )
    orientation_signs = {
        int(np.sign(area)) for area in signed_double_areas if abs(area) > 1e-14
    }
    orientation_consistent = (
        len(orientation_signs) == 1
        and all(abs(area) > 1e-14 for area in signed_double_areas)
    )
    min_abs_oriented_area = 0.5 * min(map(abs, signed_double_areas))
    realized_angle_residuals = compute_rivin_angle_residuals(
        triangles,
        realized_angles,
        boundary_vertices,
    )

    if verbose:
        print("  Construction: complete")
        print(f"  Achieved volume: {final_volume:.6f}")
        print(f"  Triangulation preserved: {'✓' if triangulation_correct else '✗'}")
        print(f"  RMS angle error: {rms_error:.6f} rad = {np.degrees(rms_error):.2f}°")

    # Success requires BOTH the target combinatorics and the target angles
    # to be attained (the old criterion ignored the angle error, so layouts
    # tens of degrees off the Rivin-optimal shape could report success).
    angles_attained = rms_error < 1e-6
    return {
        'success': triangulation_correct and angles_attained,
        'points': points,
        'vertex_list': vertex_list,  # Maps point index to original vertex ID
        'volume': final_volume,
        'triangulation_preserved': triangulation_correct,
        'angle_error': rms_error,
        'angle_error_degrees': np.degrees(rms_error),
        'max_angle_error': max_angle_error,
        'max_angle_error_degrees': float(np.degrees(max_angle_error)),
        'closure_error': closure_error[0],
        'orientation_consistent': orientation_consistent,
        'min_abs_oriented_area': float(min_abs_oriented_area),
        'residuals': {
            'rms_angle_error': float(rms_error),
            'max_angle_error': max_angle_error,
            'closure_error': float(closure_error[0]),
            'orientation_consistent': orientation_consistent,
            'min_abs_oriented_area': float(min_abs_oriented_area),
            'target_angle_structure': target_angle_residuals,
            'realized_angle_structure': realized_angle_residuals,
        },
        'message': 'Developing-map construction completed',
        'n_iterations': 0,
    }


def refine_geometry_for_volume(initial_points: np.ndarray,
                               vertex_list: List[int],
                               expected_triangulation: List[Tuple[int, int, int]],
                               verbose: bool = False) -> Dict:
    """
    Refine approximate geometry by direct volume optimization.

    Starting from approximate point positions, optimize coordinates to maximize
    hyperbolic volume while checking that the Delaunay triangulation remains correct.

    This is the final refinement step after angle-based reconstruction.

    Args:
        initial_points: Array of shape (n_vertices, 2) with initial positions
        vertex_list: List mapping point index to original vertex ID
        expected_triangulation: The expected triangulation (list of triangles)
        verbose: If True, print progress

    Returns:
        Dict with keys:
        - 'success': bool
        - 'points': Optimized point coordinates
        - 'volume': Final hyperbolic volume
        - 'triangulation_preserved': bool, whether Delaunay triangulation is correct
        - 'message': str
    """
    from scipy.spatial import Delaunay as scipy_Delaunay

    n_vertices = len(initial_points)
    vertex_to_idx = {v: i for i, v in enumerate(vertex_list)}

    # Fix first 2 vertices to eliminate translation/rotation/scale freedom
    # vertex 0 at its current position, vertex 1 at its current position
    # This fixes translation (2 DOF), rotation (1 DOF), and scale (1 DOF) = 4 DOF
    fixed_indices = [0, 1]
    free_indices = [i for i in range(n_vertices) if i not in fixed_indices]

    if verbose:
        print("Refining geometry via direct volume optimization...")
        print(f"  Vertices: {n_vertices} ({len(free_indices)} free)")

    # Check initial triangulation
    try:
        tri_initial = scipy_Delaunay(initial_points)
        initial_triangles = set()
        for simplex in tri_initial.simplices:
            v0, v1, v2 = [vertex_list[i] for i in simplex]
            initial_triangles.add(tuple(sorted([v0, v1, v2])))

        expected_set = set(tuple(sorted(tri)) for tri in expected_triangulation)

        if initial_triangles != expected_set:
            if verbose:
                print("  ⚠ Warning: Initial triangulation does not match expected!")
                print(f"    Expected {len(expected_set)} triangles, got {len(initial_triangles)}")
                print("    Refinement may not preserve triangulation")
    except Exception:
        pass

    # Initial coordinates for free vertices
    x0 = initial_points[free_indices].flatten()

    # Objective: maximize volume = sum of Lobachevsky functions
    # We minimize the negative
    def objective(x):
        # Reconstruct full points
        points = initial_points.copy()
        for i, idx in enumerate(free_indices):
            points[idx] = x[2*i:2*i+2]

        # Compute Delaunay triangulation
        try:
            tri = scipy_Delaunay(points)
            current_triangles = set()
            for simplex in tri.simplices:
                # Map back to original vertex IDs
                v0, v1, v2 = [vertex_list[i] for i in simplex]
                current_triangles.add(tuple(sorted([v0, v1, v2])))

            # Check if triangulation matches
            expected_set = set(tuple(sorted(tri)) for tri in expected_triangulation)

            if current_triangles != expected_set:
                # Triangulation changed - penalize heavily
                return 1e10

            # Compute volume
            volume = 0.0
            for tri in expected_triangulation:
                v0, v1, v2 = tri
                p0 = points[vertex_to_idx[v0]]
                p1 = points[vertex_to_idx[v1]]
                p2 = points[vertex_to_idx[v2]]

                # Compute angles
                angle0 = compute_triangle_angle(p0, p1, p2)
                angle1 = compute_triangle_angle(p1, p2, p0)
                angle2 = compute_triangle_angle(p2, p0, p1)

                # Add Lobachevsky contributions
                volume += lobachevsky_function(angle0)
                volume += lobachevsky_function(angle1)
                volume += lobachevsky_function(angle2)

            return -volume  # Minimize negative volume

        except Exception:
            # Degenerate configuration
            return 1e10

    # Optimize using L-BFGS-B

    result = minimize(
        objective,
        x0,
        method='L-BFGS-B',
        options={'maxiter': 1000, 'ftol': 1e-12}
    )

    # Reconstruct final points
    final_points = initial_points.copy()
    for i, idx in enumerate(free_indices):
        final_points[idx] = result.x[2*i:2*i+2]

    # Verify final triangulation
    tri_final = scipy_Delaunay(final_points)
    final_triangles = set()
    for simplex in tri_final.simplices:
        v0, v1, v2 = [vertex_list[i] for i in simplex]
        final_triangles.add(tuple(sorted([v0, v1, v2])))

    expected_set = set(tuple(sorted(tri)) for tri in expected_triangulation)
    triangulation_preserved = (final_triangles == expected_set)

    final_volume = -result.fun if result.success and result.fun < 1e9 else None

    if verbose:
        print(f"  Optimization: {'converged' if result.success else 'failed'}")
        print(f"  Iterations: {result.nit}")
        if final_volume is not None:
            print(f"  Final volume: {final_volume:.6f}")
        print(f"  Triangulation preserved: {'✓' if triangulation_preserved else '✗'}")

    return {
        'success': result.success and triangulation_preserved,
        'points': final_points,
        'volume': final_volume,
        'triangulation_preserved': triangulation_preserved,
        'message': result.message,
        'n_iterations': result.nit,
    }
