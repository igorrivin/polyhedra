"""Exact small illustrations for the independent Section 9 proof audit.

This is audit evidence, not an alternative production numerical library.
Only integer/Fraction arithmetic is used. No maintained toolkit module is
imported and no canonical result is overwritten.
"""

from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path


def rank(matrix):
    rows = [[Q(x) for x in row] for row in matrix]
    if not rows:
        return 0
    pivot = 0
    for column in range(len(rows[0])):
        found = next((i for i in range(pivot, len(rows)) if rows[i][column]), None)
        if found is None:
            continue
        rows[pivot], rows[found] = rows[found], rows[pivot]
        denominator = rows[pivot][column]
        rows[pivot] = [x / denominator for x in rows[pivot]]
        for i in range(len(rows)):
            if i != pivot and rows[i][column]:
                coefficient = rows[i][column]
                rows[i] = [a - coefficient * b for a, b in zip(rows[i], rows[pivot])]
        pivot += 1
        if pivot == len(rows):
            break
    return pivot


def constraint_inventory(faces):
    edges = {}
    n = 3 * len(faces)
    equations = []
    for t, face in enumerate(faces):
        equations.append([int(k // 3 == t) for k in range(n)])
        for k in range(3):
            edge = tuple(sorted((face[(k + 1) % 3], face[(k + 2) % 3])))
            edges.setdefault(edge, []).append(3 * t + k)
    for corners in edges.values():
        equations.append([int(k in corners) for k in range(n)])
    boundary = {v for edge, corners in edges.items() if len(corners) == 1 for v in edge}
    vertices = set(v for face in faces for v in face)
    interior = sorted(vertices - boundary)
    coordinate_columns = []
    for v in interior:
        coordinate_columns.append([
            int(face[(k + 1) % 3] == v) - int(face[(k + 2) % 3] == v)
            for face in faces for k in range(3)
        ])
    assert all(sum(a * b for a, b in zip(row, col)) == 0
               for row in equations for col in coordinate_columns)
    constraint_rank = rank(equations)
    return {
        "vertices": len(vertices), "edges": len(edges), "faces": len(faces),
        "boundary_vertices": sorted(boundary), "interior_vertices": interior,
        "constraint_rank": constraint_rank, "angle_tangent_dimension": n - constraint_rank,
        "coordinate_rank": rank(coordinate_columns),
        "all_coordinate_columns_satisfy_original_constraints": True,
    }


def matvec(matrix, vector):
    return [sum(a * b for a, b in zip(row, vector)) for row in matrix]


def forests(weighted_edges):
    roots = {2, 3}
    count, nonzero, value = 0, 0, Q(0)
    for chosen in combinations(weighted_edges, 2):
        parent = list(range(4))

        def find(i):
            while parent[i] != i:
                i = parent[i]
            return i

        product = Q(1)
        cycle = False
        for a, b, weight in chosen:
            a, b = find(a), find(b)
            if a == b:
                cycle = True
                break
            parent[a] = b
            product *= weight
        if cycle:
            continue
        components = {}
        for i in range(4):
            components.setdefault(find(i), []).append(i)
        if all(len(set(vertices) & roots) == 1 for vertices in components.values()):
            count += 1
            nonzero += product != 0
            value += product
    return {"forests": count, "nonzero_forests": nonzero, "weight_sum": str(value)}


disk = constraint_inventory([(0, 1, 2), (0, 2, 3), (0, 3, 1)])
annulus = constraint_inventory([
    (0, 1, 4), (0, 4, 3), (1, 2, 5), (1, 5, 4), (2, 0, 3), (2, 3, 5),
])
assert disk["angle_tangent_dimension"] == disk["coordinate_rank"] == 1
assert annulus["angle_tangent_dimension"] == 1 and annulus["coordinate_rank"] == 0

# This is 2*sqrt(3) times the stiffness matrix for (120,30,30) degrees.
obtuse = [[6, -3, -3], [-3, 2, 1], [-3, 1, 2]]
for vector, eigenvalue in [([1, 1, 1], 0), ([0, 1, -1], 1), ([-2, 1, 1], 9)]:
    assert matvec(obtuse, vector) == [eigenvalue * x for x in vector]
assert obtuse[1][2] > 0

# sqrt(3) times the regular-tetrahedron edge-variable quadratic matrix.
# Opposite pairs are (0,3), (1,4), (2,5); K=(R*S)^T(R*S).
rows = [[0, -1, 1, 0, -1, 1], [1, 0, -1, 1, 0, -1], [-1, 1, 0, -1, 1, 0]]
tetra = [[sum(row[i] * row[j] for row in rows) for j in range(6)] for i in range(6)]
assert rank(tetra) == 2 and tetra[0][3] == 2
assert all(tetra[i][i] < sum(abs(tetra[i][j]) for j in range(6) if i != j) for i in range(6))

forest_cases = []
for internal_weight in [Q(2), Q(0)]:
    edges = [(0, 1, internal_weight), (0, 2, Q(3)), (0, 3, Q(5)),
             (1, 2, Q(7)), (1, 3, Q(11)), (2, 3, Q(-13))]
    grounded = [[internal_weight + 8, -internal_weight],
                [-internal_weight, internal_weight + 18]]
    determinant = grounded[0][0] * grounded[1][1] - grounded[0][1] ** 2
    record = forests(edges)
    assert Q(record["weight_sum"]) == determinant
    assert determinant == (196 if internal_weight else 144)
    record.update(internal_weight=str(internal_weight), determinant=str(determinant))
    forest_cases.append(record)

output = Path(__file__).with_name("math-audit-checks.json")
evidence = {
    "scope": "exact finite illustrations accompanying an independent general proof audit",
    "script_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "baseline_commit": "26b3c134d9308d345cb76f1240db9de982b2e5a6",
    "baseline_tex_sha256": "63102e64405a58b8f5d51bfdffe6be43fc5cfe9a232dc0f396f1709733d750dc",
    "disk": disk, "annulus_scope_counterexample": annulus,
    "obtuse_boundary_matrix_scaled_2sqrt3": obtuse,
    "obtuse_matrix_eigenvalues_exact": [0, 1, 9],
    "regular_tetra_edge_matrix_scaled_sqrt3": tetra,
    "tetra_rank": 2, "tetra_psd_gram_factorization": rows,
    "tetra_has_positive_off_diagonal": True, "tetra_not_diagonally_dominant": True,
    "rooted_forest_cases": forest_cases,
    "all_checks_passed": True,
}
output.write_text(json.dumps(evidence, indent=2, allow_nan=False) + "\n")
print(json.dumps({"all_checks_passed": True, "output": str(output)}))
