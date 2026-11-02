"""Q2: exact Klein moments and first dihedral curvature from rational vertices."""

from itertools import combinations, product
from math import comb, factorial

import sympy as sp

from .common import ExactChecks, integer, positive, rational, require


def simplex_monomial(a, b, c):
    for exponent in (a, b, c):
        integer(exponent, 0, 20)
    return sp.Rational(factorial(a)*factorial(b)*factorial(c), factorial(a+b+c+3))


def _beta_by_polynomial(a, b):
    # Integral_0^1 x^(a-1)*(1-x)^(b-1) dx, evaluated without the factorial identity.
    return sum(sp.Rational((-1)**j*comb(b-1, j), a+j) for j in range(b))


def simplex_duffy_monomial(a, b, c):
    for exponent in (a, b, c):
        integer(exponent, 0, 20)
    return (_beta_by_polynomial(a+1, b+c+3)*_beta_by_polynomial(b+1, c+2)
            * _beta_by_polynomial(c+1, 1))


def box_monomial(bounds, exponents, *, shifted=False):
    if len(bounds) != 3 or len(exponents) != 3:
        raise ValueError("three box intervals and exponents required")
    result = sp.Integer(1)
    for pair, exponent in zip(bounds, exponents):
        integer(exponent, 0, 20)
        if len(pair) != 2:
            raise ValueError("box interval needs two endpoints")
        lo, hi = map(rational, pair)
        if lo >= hi:
            raise ValueError("box intervals must be nondegenerate and increasing")
        if shifted:
            center, half_width = (lo+hi)/2, (hi-lo)/2
            result *= half_width*sum(
                sp.Rational(2*comb(exponent, j), j+1)*center**(exponent-j)*half_width**j
                for j in range(0, exponent+1, 2))
        else:
            result *= (hi**(exponent+1)-lo**(exponent+1))/(exponent+1)
    return sp.expand(result)


def radial_moment(k, monomial):
    integer(k, 0, 8)
    return sp.expand(sum(
        sp.Integer(factorial(k)//(factorial(a)*factorial(b)*factorial(k-a-b)))
        * monomial(2*a, 2*b, 2*(k-a-b))
        for a in range(k+1) for b in range(k-a+1)))


def box_vertices(bounds):
    if len(bounds) != 3:
        raise ValueError("three box intervals required")
    parsed = []
    for interval in bounds:
        if not isinstance(interval, list) or len(interval) != 2:
            raise ValueError("box interval needs two exact endpoints")
        lo, hi = map(rational, interval)
        if lo >= hi:
            raise ValueError("box intervals must increase")
        parsed.append((lo, hi))
    vertices = list(product(*parsed))
    faces = []
    for axis in range(3):
        for side in range(2):
            members = [i for i, point in enumerate(vertices) if point[axis] == parsed[axis][side]]
            # The product order's first three are noncollinear; winding is repaired below.
            faces.append(members)
    return vertices, faces


def polyhedron_geometry(vertices, faces):
    """Derive oriented unit normals and true edges from the declared convex faces."""
    vertices = [sp.Matrix(point) for point in vertices]
    if len(vertices) < 4 or any(point.rows != 3 or not all(x.is_Rational for x in point) for point in vertices):
        raise ValueError("at least four exact rational three-dimensional vertices required")
    if len(set(map(tuple, vertices))) != len(vertices):
        raise ValueError("vertices must be distinct")
    center = sum(vertices, sp.zeros(3, 1))/len(vertices)
    normals, supports = [], []
    for face in faces:
        if len(face) < 3 or len(set(face)) != len(face):
            raise ValueError("face needs at least three distinct vertices")
        for index in face:
            integer(index, 0, len(vertices)-1)
        origin = vertices[face[0]]
        raw = (vertices[face[1]]-origin).cross(vertices[face[2]]-origin)
        if raw.dot(raw) == 0:
            raise ValueError("first three face vertices must be noncollinear")
        orientation = sp.simplify(raw.dot(center-origin))
        if orientation == 0:
            raise ValueError("nondegenerate convex polyhedron required")
        if orientation > 0:
            raw = -raw
        normal = raw/sp.sqrt(raw.dot(raw))
        support = sp.simplify(normal.dot(origin))
        if any(sp.simplify(normal.dot(vertices[i])-support) != 0 for i in face):
            raise ValueError("face vertices are not coplanar")
        if any(sp.simplify(normal.dot(point)-support) > 0 for point in vertices):
            raise ValueError("face is not a supporting plane")
        normals.append(normal)
        supports.append(support)
    edges = []
    for f, g in combinations(range(len(faces)), 2):
        common = sorted(set(faces[f]) & set(faces[g]))
        if not common:
            continue
        if len(common) != 2:
            raise ValueError("adjacent true faces must share exactly two edge vertices")
        difference = vertices[common[0]]-vertices[common[1]]
        length = sp.sqrt(difference.dot(difference))
        cosine = sp.simplify(-normals[f].dot(normals[g]))
        sine_squared = sp.simplify(1-cosine**2)
        if sine_squared <= 0:
            raise ValueError("adjacent faces must have an interior angle strictly between 0 and pi")
        sine = sp.sqrt(sine_squared)
        hf, hg = supports[f], supports[g]
        coefficient = sp.simplify(-(hf*hg+cosine*(hf**2+hg**2)/2)/sine)
        edges.append({"faces": [f, g], "vertices": common, "L": length, "cos_alpha_E": cosine,
                      "sin_alpha_E": sine, "h_f": hf, "h_g": hg, "b": coefficient})
    return {"vertices": [list(point) for point in vertices], "faces": faces,
            "outward_unit_normals": [list(normal) for normal in normals],
            "supports": supports, "edges": edges,
            "exact_maximum_vertex_norm_squared": max(point.dot(point) for point in vertices)}


def tail_bound(radius, volume, radius_squared_bound, m):
    integer(m, 0, 20)
    r, v, bound = positive(radius), positive(volume), positive(radius_squared_bound)
    t = r*r*bound
    if not t < 1:
        raise ValueError("Klein series requires r^2 R^2 < 1")
    return sp.factor(r**3*v*t**(m+1)*(m+2-(m+1)*t)/(1-t)**2)


def exact_checks(fixture):
    checks, rows = ExactChecks(), []
    t = sp.Symbol("t", real=True)
    for m in fixture["truncation_orders"]:
        integer(m, 0, 4)
        finite = sum((k+1)*t**k for k in range(m+1))
        remainder = t**(m+1)*(m+2-(m+1)*t)/(1-t)**2
        checks.equal(f"scalar tail m={m}", 1/(1-t)**2-finite, remainder)
    for item in fixture["polyhedra"]:
        name = item["id"]
        if item["kind"] == "standard_simplex":
            vertices = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1)]
            faces = [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]
            direct = simplex_monomial
            independent = simplex_duffy_monomial
        elif item["kind"] == "box":
            vertices, faces = box_vertices(item["bounds"])

            def direct(a, b, c):
                return box_monomial(item["bounds"], (a, b, c))

            def independent(a, b, c):
                return box_monomial(item["bounds"], (a, b, c), shifted=True)
        else:
            raise ValueError("only standard simplex and rectangular boxes are implemented")
        moments = [radial_moment(k, direct) for k in range(5)]
        for k, moment in enumerate(moments):
            checks.equal(f"{name}: independent radial moment M_{2*k}", moment, radial_moment(k, independent))
        for k, expected in enumerate(item["expected_initial_moments"]):
            checks.equal(f"{name}: declared M_{2*k}", moments[k], rational(expected))
        geometry = polyhedron_geometry(vertices, faces)
        bound = positive(item["radius_squared_bound"])
        checks.truth(f"{name}: exact rational radius bound", bound >= geometry["exact_maximum_vertex_norm_squared"])
        curvature = sp.Integer(0)
        for index, edge in enumerate(geometry["edges"]):
            f, g = edge["faces"]
            nf, ng = map(sp.Matrix, (geometry["outward_unit_normals"][f], geometry["outward_unit_normals"][g]))
            hf, hg = edge["h_f"], edge["h_g"]
            # Direct Lorentz product of (sqrt(t)*h,n)/sqrt(1-t*h^2), with signature -+++.
            lorentz_cosine = (t*hf*hg-nf.dot(ng))/sp.sqrt((1-t*hf**2)*(1-t*hg**2))
            chapter_cosine = (edge["cos_alpha_E"]+t*hf*hg)/sp.sqrt((1-t*hf**2)*(1-t*hg**2))
            checks.equal(f"{name}: edge {index} Lorentz cosine", lorentz_cosine, chapter_cosine)
            derived_b = sp.simplify(-sp.diff(lorentz_cosine, t).subs(t, 0)/edge["sin_alpha_E"])
            checks.equal(f"{name}: edge {index} curvature coefficient", derived_b, edge["b"])
            curvature += edge["L"]*edge["b"]
            edge["lorentz_cosine_in_t"] = lorentz_cosine
        curvature = sp.simplify(curvature)
        checks.equal(f"{name}: first curvature-volume sum", curvature, -3*moments[0])
        if item["kind"] == "standard_simplex":
            checks.truth("simplex: three zero and three nonzero curvature coefficients",
                         sum(edge["b"] == 0 for edge in geometry["edges"]) == 3)
            for index, edge in enumerate(geometry["edges"]):
                if edge["b"] != 0:
                    checks.equal(f"simplex: nonzero edge {index} length", edge["L"], sp.sqrt(2))
                    checks.equal(f"simplex: nonzero edge {index} coefficient", edge["b"], -1/(6*sp.sqrt(2)))
        truncations = []
        for r_text in fixture["radii"]:
            r = positive(r_text)
            for m in fixture["truncation_orders"]:
                tail = tail_bound(r_text, str(moments[0]), str(bound), m)
                checks.truth(f"{name}: r={r_text}, m={m} nonnegative tail", tail >= 0)
                truncations.append({"r": r, "m": m, "t": r*r*bound,
                                    "series_partial_volume": sum((k+1)*r**(3+2*k)*moments[k] for k in range(m+1)),
                                    "analytic_geometric_series_tail_bound": tail})
        rows.append({"id": name, "radial_moments_k0_through_4": moments,
                     "volume_coefficients_r3_through_r11": [(k+1)*value for k, value in enumerate(moments)],
                     "geometry": geometry, "curvature_sum": curvature, "radius_squared_bound": bound,
                     "truncations": truncations})
    require(rows, "Klein fixture is empty")
    return checks.result(rows=rows, coordinate="curvature -1 Klein ball; exactly P_r=r*Q; interior dihedral angles",
                         formulas={"density": "r^3/(1-r^2*|y|^2)^2", "moments": "M_2k=integral_Q |y|^(2k) d^3y",
                                   "curvature": "b=-(h_f*h_g+cos(alpha_E)*(h_f^2+h_g^2)/2)/sin(alpha_E)"},
                         tail_status="exact rational evaluation of an analytic series-truncation bound; no quadrature performed")
