"""Targeted audit probes against the selected checkout.

The observed-probe-results.json file records the original 31 October audit.
Running this script after corrections produces current observations and does
not rewrite that historical record. Pass --toolkit-root to select an original
or installed source checkout explicitly.
"""
from pathlib import Path
import importlib.util
import sys
import json
from fractions import Fraction
import argparse
import numpy as np
from scipy.spatial import Delaunay

workspace = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--toolkit-root", type=Path,
    default=workspace / "packages" / "volume-toolkit",
)
ROOT = parser.parse_args().toolkit_root.resolve()

def load(name):
    p = ROOT / 'ideal_poly_volume_toolkit' / (name + '.py')
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m

rd = load('rivin_delaunay')
gr = load('geometric_realization')
rh = load('rivin_holonomy')
points = np.random.default_rng(10).random((10, 2))
triangles = [tuple(map(int, t)) for t in Delaunay(points).simplices]
lp = rd.check_delaunay_realizability(triangles)
opt = rd.optimize_hyperbolic_volume(triangles, initial_angles=lp['angles_radians'])
real = rd.realize_angles_as_points(triangles, opt['angles'])
print('existing-realization-regression', json.dumps({
    'lp': bool(lp['realizable']), 'optimization': bool(opt['success']),
    'realization': bool(real['success']),
    'angle_error_degrees': float(real['angle_error_degrees']),
    'closure_error': float(real['closure_error']),
    'triangulation_preserved': bool(real['triangulation_preserved']),
}))
faces = [(0, 2, 1), (0, 1, 3), (1, 2, 3), (2, 0, 3)]
cert = rh.certify_exact_zero_shear_structure(faces)
print('exact-zero-shear-tetrahedron', json.dumps(cert.as_dict()))
_, zero_shears = rh.triangulation_from_faces(faces)
tiny_shears = {key: Fraction(1, 10**400) for key in zero_shears}
tiny_result = rh.check_arithmeticity(faces, shears=tiny_shears)
print('exact-zero-shear-underflow-probe', json.dumps({
    'all_inputs_nonzero': all(value != 0 for value in tiny_shears.values()),
    'is_arithmetic': tiny_result['is_arithmetic'],
    'has_exact_zero_shears': tiny_result['has_exact_zero_shears'],
    'normalized_shears': tiny_result['shears'],
    'status': tiny_result['arithmeticity_status'],
}))
xy = np.array([[0., 0.], [1., 0.], [-.3, 1.2], [1., .8]])
for tris in [[(0, 1, 3), (0, 3, 2)], [(0, 1, 3), (3, 2, 0)]]:
    ang = np.array([
        [rd.compute_triangle_angle(xy[t[i]], xy[t[(i+1)%3]], xy[t[(i+2)%3]])
         for i in range(3)] for t in tris
    ])
    r = gr.realize_from_angles_rigid(tris, ang)
    p = r['points']
    areas = [float(np.linalg.det(np.array([p[t[1]]-p[t[0]], p[t[2]]-p[t[0]]]))) for t in tris]
    print('rigid-orientation-probe', json.dumps({
        'triangles': tris, 'success': r['success'],
        'signed_double_areas': areas, 'points': p.tolist(),
    }))
