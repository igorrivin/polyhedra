"""Reproduce the monograph's first small variational worked example.

Requires an installed volume toolkit (or PYTHONPATH=packages/volume-toolkit).
Exact rational FEM assembly is an independent fixture oracle; the reusable
numerical operators are owned by ideal_poly_volume_toolkit.variational.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

import mpmath as mp
import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUNDLE_MANIFEST = ROOT / 'section9-bundle.json'
# A detached reproduction archive exports only the maintained numerical subset.
# Normal repository runs still use the installed toolkit (or explicit PYTHONPATH).
if BUNDLE_MANIFEST.is_file():
    sys.path.insert(0, str(ROOT / 'packages/volume-toolkit'))

# This import must follow the explicit detached-bundle path selection above.
from ideal_poly_volume_toolkit import variational as var  # noqa: E402


def rational_fem(points, triangles):
    """Assemble exact barycentric-gradient energies from integer coordinates."""
    if any(type(value) is not int for point in points for value in point):
        raise ValueError("the exact fixture oracle requires integer coordinates")
    points = [[Fraction(value) for value in point] for point in points]
    n = len(points)
    matrix = [[Fraction(0) for _ in range(n)] for _ in range(n)]
    for face in triangles:
        p = [points[i] for i in face]
        area2 = ((p[1][0] - p[0][0]) * (p[2][1] - p[0][1])
                 - (p[1][1] - p[0][1]) * (p[2][0] - p[0][0]))
        if area2 <= 0:
            raise ValueError("exact fixture faces must be counterclockwise")
        gradients = [[(p[(k+1) % 3][1] - p[(k+2) % 3][1]) / area2,
                      (p[(k+2) % 3][0] - p[(k+1) % 3][0]) / area2]
                     for k in range(3)]
        for i, a in enumerate(face):
            for j, b in enumerate(face):
                matrix[a][b] += area2 / 2 * sum(x*y for x, y in zip(gradients[i], gradients[j]))
    return matrix


def rooted_forest_sum(matrix, boundary):
    """Enumerate nonzero-weight B-rooted spanning forests for this small graph."""
    n = len(matrix)
    roots = set(boundary)
    edges = [(i, j, -matrix[i][j]) for i in range(n) for j in range(i+1, n)
             if matrix[i][j] != 0]
    total, count = Fraction(0), 0
    for chosen in combinations(edges, n - len(roots)):
        parent = list(range(n))

        def find(v):
            while parent[v] != v:
                v = parent[v]
            return v

        weight = Fraction(1)
        for a, b, w in chosen:
            a, b = find(a), find(b)
            if a == b:
                break
            parent[a] = b
            weight *= w
        else:
            components = {}
            for v in range(n):
                components.setdefault(find(v), []).append(v)
            if all(len(roots.intersection(vertices)) == 1 for vertices in components.values()):
                total += weight
                count += 1
    return total, count


def high_precision_hessian(points, faces, incidence, u, dps=50):
    """Independent numerical derivative of the Clausen volume, not an enclosure."""
    # Precision contexts and multivariable diff are documented at:
    # https://mpmath.org/doc/current/calculus/differentiation.html
    with mp.workdps(dps):
        base = []
        for face in faces:
            for k in range(3):
                p, q, r = (points[face[j % 3]] for j in (k, k+1, k+2))
                a = [mp.mpf(int(q[j])) - int(p[j]) for j in range(2)]
                b = [mp.mpf(int(r[j])) - int(p[j]) for j in range(2)]
                base.append(mp.atan2(a[0]*b[1] - a[1]*b[0], a[0]*b[0] + a[1]*b[1]))
        coefficients = [[int(x) for x in row] for row in incidence]

        def volume(*parameters):
            return mp.fsum(mp.clsin(2, 2*(a + mp.fsum(c*x for c, x in zip(row, parameters)))) / 2
                           for a, row in zip(base, coefficients))

        point = tuple(mp.mpf(str(x)) for x in u)
        result = []
        for i in range(len(u)):
            row = []
            for j in range(len(u)):
                orders = tuple(int(k == i) + int(k == j) for k in range(len(u)))
                row.append(float(mp.diff(volume, point, orders)))
            result.append(row)
        return np.array(result)


def source_provenance(fixture_path):
    def record(role, path, required=True):
        path = Path(path).resolve()
        try:
            location, kind = str(path.relative_to(ROOT)), 'project-relative'
        except ValueError:
            location, kind = str(path), 'external'
        row = {'role': role, 'path': location, 'location_kind': kind, 'required': required}
        if not path.is_file():
            if required:
                raise FileNotFoundError(f'required reproduction source is missing: {role}: {path}')
            return {**row, 'available': False, 'reason': 'optional monograph asset not included in this execution context'}
        return {**row, 'available': True, 'sha256': sha256(path.read_bytes()).hexdigest()}

    records = [record('experiment.driver', __file__),
               record('toolkit.variational', var.__file__),
               record('toolkit.geometry', Path(var.__file__).with_name('geometry.py')),
               record('experiment.fixture', fixture_path),
               record('experiment.template', HERE / 'page.html'),
               record('book.tex', ROOT / 'book/polyhedral_volumes_and_geodesic_identities.tex', False),
               record('book.chapter', ROOT / 'book/chapters/09-volume-hessians.tex', False),
               record('book.reference_pdf', ROOT / 'book/reference/polyhedral_volumes_and_geodesic_identities.pdf', False)]
    commit, status, dirty = None, [], None
    if (ROOT / '.git').exists():
        commit = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
        status = subprocess.check_output(['git', '-C', str(ROOT), 'status', '--porcelain'], text=True).splitlines()
        dirty = bool(status)
    bundle = json.loads(BUNDLE_MANIFEST.read_text()) if BUNDLE_MANIFEST.is_file() else None
    bundle_mismatches = []
    if bundle:
        for name, digest in bundle['payload_sha256'].items():
            path = ROOT / name
            if not path.is_file() or sha256(path.read_bytes()).hexdigest() != digest:
                bundle_mismatches.append(name)
    return {
        'source_commit': commit,
        'execution_context': 'git-checkout' if commit else ('detached-bundle' if bundle else 'source-without-git'),
        'repository_dirty_at_start': dirty,
        'git_status_porcelain_at_start': status,
        'input_sha256': sha256(fixture_path.read_bytes()).hexdigest(),
        'source_files': records,
        'source_sha256': {row['role']: row['sha256'] for row in records if row['available']},
        'bundle_origin': bundle['origin_provenance'] if bundle else None,
        'bundle_payload_hashes_match': not bundle_mismatches if bundle else None,
        'bundle_payload_mismatches': bundle_mismatches,
        'python': platform.python_version(), 'numpy': np.__version__,
        'scipy': scipy.__version__, 'mpmath': mp.__version__,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    }


def build_report(fixture_path=HERE / 'fixture.json'):
    fixture_path = Path(fixture_path).resolve()
    provenance = source_provenance(fixture_path)
    fixture = json.loads(fixture_path.read_text())
    canonical_fixture = json.loads((HERE / 'fixture.json').read_text())
    if fixture != canonical_fixture:
        raise ValueError('--fixture must be a copy of the supplied section9-rectangle-grid-v1 fixture; this renderer is not a general mesh experiment')
    points, faces = np.array(fixture['points']), np.array(fixture['triangles'])
    interior, boundary = fixture['interior_vertices'], fixture['boundary_vertices']
    incidence = var.leading_trailing_matrix(faces, interior)
    base = var.corner_angles(points, faces)
    zero = np.zeros(len(interior))
    gradient, hessian = var.angle_volume_derivatives(base, incidence, zero)
    laplacian = var.cotangent_stiffness(len(points), faces, base)
    fem = var.fem_stiffness(points, faces)
    grounded = laplacian[np.ix_(interior, interior)]
    response = var.schur_complement(laplacian, interior)
    boundary_voltage = points[boundary, 0] / 3
    harmonic = -np.linalg.solve(grounded, laplacian[np.ix_(interior, boundary)] @ boundary_voltage)
    currents = response @ boundary_voltage
    volume = var.angle_volume(base, incidence, zero)
    with mp.workdps(50):
        volume_reference = float(12 * mp.catalan)
        volume_reference_decimal = str(12 * mp.catalan)
    off_u = np.array(fixture['off_origin_parameters'])
    off_angles = var.deformed_angles(base, incidence, off_u)
    _, off_hessian = var.angle_volume_derivatives(base, incidence, off_u)
    off_laplacian = var.cotangent_stiffness(len(points), faces, off_angles)
    reference_hessian = high_precision_hessian(points, faces, incidence, off_u)
    rational = rational_fem(fixture['points'], fixture['triangles'])
    exact_grounded = [[rational[i][j] for j in interior] for i in interior]
    forest_sum, forest_count = rooted_forest_sum(rational, boundary)
    a, b, c, d = (exact_grounded[i][j] for i, j in ((0,0),(0,1),(1,0),(1,1)))
    determinant_l = a*d - b*c
    determinant_k = 4 * determinant_l
    effective_k = 2*d - (2*c)*(2*b)/(2*a)
    checks = {}

    def check(name, value, tolerance):
        checks[name] = {'max_abs_error': float(value), 'tolerance': tolerance,
                        'passed': bool(value <= tolerance)}

    check('cotangent_vs_independent_fem', np.max(abs(laplacian-fem)), 1e-12)
    check('fem_vs_exact_rational_fixture', np.max(abs(fem-np.array(rational, dtype=float))), 1e-12)
    check('negative_hessian_equals_twice_grounded_laplacian', np.max(abs(hessian+2*grounded)), 1e-12)
    check('geometric_gradient', np.max(abs(gradient)), 1e-12)
    check('volume_vs_12_catalan', abs(volume-volume_reference), 1e-12)
    check('off_origin_negative_hessian_identity',
          np.max(abs(off_hessian + 2*off_laplacian[np.ix_(interior, interior)])), 1e-12)
    check('off_origin_hessian_vs_50_digit_derivative', np.max(abs(off_hessian-reference_hessian)), 1e-11)
    check('dirichlet_response_constant_kernel', np.max(abs(response.sum(axis=1))), 1e-12)
    check('dirichlet_response_symmetry', np.max(abs(response-response.T)), 1e-12)
    check('harmonic_linear_voltage', np.max(abs(harmonic-np.array([1/3,2/3]))), 1e-12)
    check('linear_voltage_energy', abs(float(boundary_voltage @ currents)-2/3), 1e-12)
    check('schur_determinant_factor', abs(float(np.linalg.det(-hessian))-float(2*a*effective_k)), 1e-11)
    exact_passed = (exact_grounded == [[Fraction(4),Fraction(-1)],[Fraction(-1),Fraction(4)]]
                    and forest_sum == determinant_l == 15 and forest_count == 15
                    and determinant_k == 2*a*effective_k == 60)
    return {
        'schema_version': 2, 'experiment_id': fixture['id'], 'provenance': provenance,
        'statement_labels': ['eq:ipolyAngleCoordinates', 'eq:ipolyHessian', 'eq:ipolyDtN',
                             'eq:ipolySchur', 'eq:ipolyForestDeterminant'],
        'conventions': fixture['conventions'],
        'methods': {'volume': 'canonical geometry.bloch_wigner, binary64',
                    'derivatives': 'analytic leading-trailing derivatives, binary64',
                    'independent_derivative_oracle': 'mpmath.diff of Clausen volume at 50 decimal digits',
                    'exact_fixture': 'Fraction FEM gradients from integer geometry; exhaustive nonzero rooted forests'},
        'exact_fixture': {'grounded_laplacian': [[str(x) for x in row] for row in exact_grounded],
                          'det_L_II': str(determinant_l), 'det_negative_volume_hessian': str(determinant_k),
                          'rooted_forest_weight_sum': str(forest_sum), 'nonzero_rooted_forest_count': forest_count,
                          'eliminated_K_entry': str(2*a), 'effective_K_entry': str(effective_k),
                          'checks_passed': exact_passed},
        'numerical': {'volume': volume, 'reference_12_catalan_50_digits': volume_reference_decimal,
                      'gradient': gradient.tolist(), 'negative_hessian': (-hessian).tolist(),
                      'grounded_laplacian': grounded.tolist(), 'dirichlet_response': response.tolist(),
                      'boundary_vertices': boundary, 'boundary_voltage': boundary_voltage.tolist(),
                      'harmonic_interior_voltage': harmonic.tolist(), 'boundary_current': currents.tolist(),
                      'energy': float(boundary_voltage @ currents),
                      'off_origin_parameters': off_u.tolist(), 'off_origin_minimum_angle': float(off_angles.min()),
                      'off_origin_hessian': off_hessian.tolist()},
        'checks': checks,
        'all_checks_passed': exact_passed and all(row['passed'] for row in checks.values()),
        'scope': {'exact': 'finite rational matrix and forest calculations on the integer-coordinate fixture',
                  'numerical': 'binary64 operators and 50-digit derivative comparison, without rigorous enclosures',
                  'off_origin': 'abstract angle structure; no assertion that its triangles close geometrically',
                  'not_claimed': ['strict simplicial convex realization', 'global optimality', 'nearly-linear solver',
                                  'full Section 9 proof verification', 'complete chapter-to-HTML conversion']},
    }


def create_reproduction_bundle(report, fixture_path, destination):
    """Export complete experiment sources and a labeled numerical package subset."""
    license_path = ROOT / 'packages/volume-toolkit/LICENSE'
    if not license_path.is_file():
        license_path = ROOT / 'LICENSES/volume-toolkit-MIT.txt'
    if not license_path.is_file():
        raise FileNotFoundError('the toolkit MIT license is required in the reproduction bundle')
    payload = {}
    for name in ('run.py', 'page.html'):
        payload[f'experiments/section9/{name}'] = (HERE / name).read_bytes()
    payload['experiments/section9/fixture.json'] = Path(fixture_path).read_bytes()
    for name in ('variational.py', 'geometry.py'):
        payload[f'packages/volume-toolkit/ideal_poly_volume_toolkit/{name}'] = Path(var.__file__).with_name(name).read_bytes()
    payload['packages/volume-toolkit/ideal_poly_volume_toolkit/__init__.py'] = (
        b'"""Generated Section 9 numerical subset; not the complete toolkit API.\n'
        b'Original maintained modules are copied unchanged. See LICENSES and section9-bundle.json.\n"""\n'
    )
    payload['LICENSES/volume-toolkit-MIT.txt'] = license_path.read_bytes()
    origin = report['provenance']
    payload['requirements.txt'] = ''.join(f'{name}=={origin[name]}\n' for name in ('numpy', 'scipy', 'mpmath')).encode()
    payload['README.md'] = (
        '# Section 9 reproduction bundle\n\n'
        'This is a generated numerical subset of the Ideal Polyhedra Volume Toolkit, '
        'with its maintained variational.py and geometry.py copied unchanged. '
        'It is not a full toolkit distribution: Torch, rendering, RL and unrelated APIs are excluded. '
        'The original MIT license is in LICENSES/volume-toolkit-MIT.txt. '
        'The numerical reproduction needs only NumPy, SciPy and mpmath.\n\n'
        'The captured reproduction used CPython '
        f'{origin["python"]}; other Python/platform combinations were not validated for this bundle. '
        'From this extracted directory, install dependencies with '
        '`python -m pip install -r requirements.txt`, then run '
        '`python experiments/section9/run.py`. '
        'An absolute runner path also works from another working directory; the runner finds '
        'this explicitly labeled bundled subset. No development checkout is needed.\n\n'
        'Outputs default to artifacts/section9/result.json and site/section9/index.html. '
        'The optional --fixture argument accepts only an unchanged copy of the supplied fixture. '
        'The monograph source/PDF are not included and are explicitly reported unavailable; '
        'their absence does not prevent this finite computation or its companion rendering. '
        'This bundle does not verify the full monograph.\n\n'
        'section9-bundle.json records originating source provenance and every payload hash. '
        'A detached run has no Git clean/dirty state and records that as unavailable. '
        'The original source snapshot may itself have been dirty; that status remains in origin_provenance.\n'
    ).encode()
    manifest = {'schema_version': 1, 'scope': 'Section 9 numerical reproduction subset',
                'origin_provenance': report['provenance'],
                'payload_sha256': {name: sha256(data).hexdigest() for name, data in payload.items()}}
    payload['section9-bundle.json'] = (json.dumps(manifest, indent=2, allow_nan=False) + '\n').encode()
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            archive.writestr('section9-reproduction/' + name, data)


def validate_render_sources(report, fixture_path):
    """Prevent an old report from acquiring a bundle of changed current sources.

    Relocated, byte-identical inputs are allowed. Rendering retains the report's
    original timestamp, numerical results and execution provenance.
    """
    if report.get('schema_version') != 2:
        raise ValueError('unsupported stored report schema')
    fixture_path = Path(fixture_path)
    fixture = json.loads(fixture_path.read_text())
    if report.get('experiment_id') != fixture.get('id'):
        raise ValueError('stored report experiment does not match fixture')
    old = report['provenance']
    current = source_provenance(fixture_path)
    if old.get('input_sha256') != current['input_sha256']:
        raise ValueError('stored report input hash does not match current fixture')
    recorded = {row['role']: row for row in old.get('source_files', [])}
    if len(recorded) != len(old.get('source_files', [])):
        raise ValueError('stored report has duplicate source roles')
    for row in current['source_files']:
        previous = recorded.get(row['role'])
        if previous is None or previous.get('available') != row['available']:
            raise ValueError(f"stored report source availability differs: {row['role']}")
        if row['available'] and (previous.get('sha256') != row['sha256']
                                or old.get('source_sha256', {}).get(row['role']) != row['sha256']):
            raise ValueError(f"stored report source hash differs: {row['role']}")
    if current['bundle_payload_mismatches']:
        raise ValueError('detached bundle payload integrity check failed')


def render_site(report, fixture_path, result_path, site_dir, *, chapter_page=None,
                book_source_archive=None):
    """Render an identity-checked report; this operation performs no computation."""
    fixture_path, result_path, site_dir = map(Path, (fixture_path, result_path, site_dir))
    validate_render_sources(report, fixture_path)
    if json.loads(result_path.read_text()) != report:
        raise ValueError('result file does not contain the supplied report')
    requested = [(chapter_page, 'chapter page'), (book_source_archive, 'complete source archive')]
    for path, title in requested:
        if path is not None and not Path(path).is_file():
            raise FileNotFoundError(f'requested {title} is missing: {path}')

    def copy(source, destination):
        if Path(source).resolve() != destination.resolve():
            shutil.copyfile(source, destination)

    site_dir.mkdir(parents=True, exist_ok=True)
    downloads = site_dir / 'downloads'
    downloads.mkdir(exist_ok=True)
    for source, name in [(fixture_path, 'fixture.json'), (result_path, 'result.json'),
                         (Path(__file__), 'run.py'), (Path(var.__file__), 'variational.py')]:
        copy(source, downloads / name)
    book_files = [ROOT / 'book/polyhedral_volumes_and_geodesic_identities.tex',
                  ROOT / 'book/reference/polyhedral_volumes_and_geodesic_identities.pdf']
    book_links = []
    for source in book_files:
        if source.is_file():
            copy(source, downloads / source.name)
            title = 'Full monograph PDF (supplied reference)' if source.suffix == '.pdf' else 'Main LaTeX inspection copy (requires chapter inputs)'
            book_links.append(f'<li><a href="downloads/{source.name}">{title}</a></li>')
    if not book_links:
        book_links.append('<li>Monograph source and PDF are not included in this detached computation bundle.</li>')
    if chapter_page is not None:
        if Path(chapter_page).resolve() != (site_dir / 'chapter.html').resolve():
            raise ValueError('chapter page must be built in this site directory with its local assets')
        book_links.append('<li><a href="chapter.html">Read the complete Section 9 chapter and claim ledger</a></li>')
    if book_source_archive is not None:
        copy(book_source_archive, downloads / 'monograph-source.zip')
        book_links.append('<li><a href="downloads/monograph-source.zip">Complete monograph LaTeX source (ZIP)</a></li>')
    create_reproduction_bundle(report, fixture_path, downloads / 'section9-reproduction.zip')
    template = (HERE / 'page.html').read_text()
    data = json.dumps({'report': report, 'fixture': json.loads(fixture_path.read_text())}, allow_nan=False)
    page = template.replace('__EXPERIMENT_DATA__', data.replace('</', '<\\/')).replace('__BOOK_DOWNLOAD_LINKS__', '\n'.join(book_links))
    (site_dir / 'index.html').write_text(page)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixture', type=Path, default=HERE / 'fixture.json',
                        help='path to an unchanged copy of the supplied rectangle fixture')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/section9/result.json')
    parser.add_argument('--site-dir', type=Path, default=ROOT / 'site/section9')
    parser.add_argument('--render-result', type=Path,
                        help='render an existing identity-checked result without recomputing it')
    parser.add_argument('--chapter-page', type=Path, help='existing chapter.html in --site-dir')
    parser.add_argument('--book-source-archive', type=Path, help='existing complete LaTeX source ZIP')
    args = parser.parse_args()
    if args.render_result:
        report = json.loads(args.render_result.read_text(),
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f'nonfinite JSON: {value}')))
        result_path = args.render_result
    else:
        report = build_report(args.fixture)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
        result_path = args.output
    render_site(report, args.fixture, result_path, args.site_dir,
                chapter_page=args.chapter_page, book_source_archive=args.book_source_archive)
    print(json.dumps({'operation': 'render_existing_report' if args.render_result else 'compute_and_render',
                      'all_checks_passed': report['all_checks_passed'],
                      'source_commit': report['provenance']['source_commit'],
                      'dirty_at_start': report['provenance']['repository_dirty_at_start'],
                      'result': str(result_path), 'html': str(args.site_dir / 'index.html')}, indent=2))
    return 0 if report['all_checks_passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
