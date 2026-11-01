"""Independent fixture references and the publication boundary of barrier runs."""

import copy
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import mpmath as mp

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('section9_barrier_runner', ROOT / 'experiments/section9/barrier_run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.extend(value for key, value in attrs if key == 'href')


class BarrierExampleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = ROOT / 'experiments/section9/barrier-fixtures.json'
        with mp.workdps(37):
            cls.report = runner.build_report(cls.fixture)
            if mp.mp.dps != 37:
                raise AssertionError('reference computation leaked its mpmath precision')
        cls.cases = {case['id']: case for case in cls.report['cases']}

    def test_three_independent_reference_volumes_and_gap_comparisons(self):
        # Values derived before the implementation, using Clausen functions.
        expected = {
            'regular-triangle': '1.014941606409653625021202554274520285941689307530299792017489106776',
            'asymmetric-disk': '3.0062866417470506525050027983572778475653682538807032900869601879',
            'boundary-maximum': '0.3160358446012942861798335805775719456118860120729091191292577588',
        }
        self.assertTrue(self.report['all_checks_passed'])
        self.assertTrue(self.report['exercises_initial_centering'])
        with mp.workdps(80):
            for name, value in expected.items():
                case = self.cases[name]
                reference, result = case['reference'], case['solver']
                with self.subTest(name=name):
                    self.assertLess(abs(mp.mpf(reference['exact_space_maximum_volume_decimal'])-mp.mpf(value)), mp.mpf('1e-58'))
                    self.assertGreater(mp.mpf(reference['independent_initial_decrement_decimal']), mp.mpf('.25'))
                    self.assertGreater(result['centering_steps'], 0)
                    self.assertGreater(result['path_steps'], 100)
                    self.assertFalse(result['certified'])
                    for key in ('exact_space_observed_gap_decimal', 'lifted_input_observed_gap_decimal'):
                        self.assertGreaterEqual(mp.mpf(reference[key]), -mp.mpf('1e-11'))
                        self.assertLess(mp.mpf(reference[key]), mp.mpf(result['gap_bound_estimate'])+mp.mpf('1e-11'))

    def test_asymmetric_disk_moves_and_preserves_opposite_sums(self):
        case = self.cases['asymmetric-disk']
        reference, result, invariants = case['reference'], case['solver'], case['invariance_diagnostics']
        self.assertGreater(max(row['parameters'][0] for row in result['history']), .02)
        self.assertLess(abs(result['parameters'][0]), 1e-5)
        self.assertEqual(len(invariants['interior_edge_opposite_corner_pairs']), 4)
        self.assertEqual(invariants['maximum_opposite_sum_tangent_residual'], 0)
        self.assertLess(invariants['maximum_interior_edge_opposite_sum_change'], 1e-14)
        with mp.workdps(80):
            self.assertLess(abs(mp.mpf(reference['exact_space_barrier_gradient_at_volume_maximum_decimal'])+mp.mpf(28)/15), mp.mpf('1e-60'))
            self.assertLess(abs(mp.mpf(reference['exact_space_volume_gradient_at_geometric_maximum_decimal'])), mp.mpf('1e-70'))
            self.assertLess(abs(mp.mpf(reference['exact_space_phi1_center_decimal'])-mp.mpf('0.0284464026743893140179952955125951747504707475048301513965223')), mp.mpf('1e-58'))

    def test_boundary_reference_distinguishes_rounding_and_closed_maximum(self):
        case = self.cases['boundary-maximum']
        reference, result = case['reference'], case['solver']
        with mp.workdps(80):
            derivative = mp.mpf(reference['exact_space_boundary_right_derivative_decimal'])
            self.assertLess(abs(derivative-mp.mpf('-0.74535420818028405918242345507887943784194992689642428123093113514')), mp.mpf('1e-60'))
            exact = mp.mpf(reference['exact_space_maximizer_parameters_decimal'][0])
            lifted = mp.mpf(reference['lifted_input_stationary_parameters_decimal'][0])
            self.assertEqual(exact, -mp.mpf('.05'))
            self.assertGreater(abs(lifted-exact), mp.mpf('1e-17'))
            self.assertLess(abs(lifted-exact), mp.mpf('1e-14'))
            self.assertLess(mp.mpf(reference['lifted_input_stationarity_residual_decimal']), mp.mpf('1e-29'))
            self.assertGreater(mp.mpf(reference['reference_maximum_representation_difference_decimal']), mp.mpf('1e-16'))
        self.assertGreater(result['parameters'][0], -.05)
        self.assertLess(result['parameters'][0], -.0499)
        self.assertGreater(float(reference['exact_space_observed_gap_decimal']), 3e-5)

    def test_fixed_fixture_rejects_changed_definitions(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'fixtures.json'
            fixture = runner.read_json(self.fixture)
            fixture['cases'][0]['initial_parameters'][0] += .01
            path.write_text(json.dumps(fixture))
            with self.assertRaisesRegex(ValueError, 'unchanged copy'):
                runner.build_report(path)
            path.write_bytes(self.fixture.read_bytes())
            runner.validate_render_sources(self.report, path)

    def test_source_input_and_optional_chapter_identity_are_required(self):
        changed = copy.deepcopy(self.report)
        changed['provenance']['source_sha256']['toolkit.angle_barrier'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'source hash differs: toolkit.angle_barrier'):
            runner.validate_render_sources(changed, self.fixture)
        changed = copy.deepcopy(self.report)
        changed['provenance']['input_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'input hash'):
            runner.validate_render_sources(changed, self.fixture)
        changed = copy.deepcopy(self.report)
        changed['provenance']['source_files'] = [row for row in changed['provenance']['source_files'] if row['role'] != 'book.chapter']
        with self.assertRaisesRegex(ValueError, 'availability differs: book.chapter'):
            runner.validate_render_sources(changed, self.fixture)

    def test_rendering_preserves_report_environment_and_all_downloads(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result, site = root / 'result.json', root / 'site'
            result.write_text(json.dumps(self.report, allow_nan=False)+'\n')
            original = result.read_bytes()
            with patch.object(runner.np, '__version__', '999-render-only'), \
                    patch.object(runner.platform, 'python_version', return_value='999-render-only'):
                runner.render_site(self.report, self.fixture, result, site)
            self.assertEqual(result.read_bytes(), original)
            self.assertEqual((site / 'downloads/barrier-result.json').read_bytes(), original)
            html = (site / 'barrier.html').read_text()
            embedded = html.split('\nconst barrierData = ', 1)[1].split(';\n</script>', 1)[0]
            self.assertEqual(json.loads(embedded)['report'], self.report)
            self.assertNotIn('href="chapter.html"', html)
            links = LinkParser()
            links.feed(html)
            for href in links.links:
                if not href.startswith('#'):
                    self.assertTrue((site / href).is_file(), href)
            with zipfile.ZipFile(site / 'downloads/barrier-reproduction.zip') as archive:
                requirements = archive.read('barrier-reproduction/requirements.txt').decode()
                readme = archive.read('barrier-reproduction/README.md').decode()
                manifest = json.loads(archive.read('barrier-reproduction/barrier-bundle.json'))
                self.assertEqual(manifest['origin_provenance'], self.report['provenance'])
                self.assertEqual(set(archive.namelist()), {'barrier-reproduction/'+key for key in manifest['payload_sha256']} | {'barrier-reproduction/barrier-bundle.json'})
                for path, expected in manifest['payload_sha256'].items():
                    self.assertEqual(sha256(archive.read('barrier-reproduction/'+path)).hexdigest(), expected)
                for module in (runner.solver, runner.var, runner.geometry):
                    path = Path(module.__file__)
                    self.assertEqual(archive.read('barrier-reproduction/packages/volume-toolkit/ideal_poly_volume_toolkit/'+path.name), path.read_bytes())
            self.assertIn('numpy=='+self.report['provenance']['numpy'], requirements)
            self.assertIn('CPython '+self.report['provenance']['python'], readme)
            self.assertNotIn('999-render-only', requirements+readme)

    def test_missing_chapter_or_wrong_report_fails_before_output(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result, site = root / 'result.json', root / 'site'
            result.write_text(json.dumps(self.report))
            with self.assertRaisesRegex(FileNotFoundError, 'requested chapter page is missing'):
                runner.render_site(self.report, self.fixture, result, site, chapter_page=site / 'chapter.html')
            self.assertFalse(site.exists())
            result.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'does not contain'):
                runner.render_site(self.report, self.fixture, result, site)
            self.assertFalse(site.exists())

    def test_detached_payload_corruption_is_reported_and_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'payload.txt').write_text('changed')
            manifest = root / 'barrier-bundle.json'
            manifest.write_text(json.dumps({'origin_provenance': self.report['provenance'], 'payload_sha256': {'payload.txt': '0'*64}}))
            with patch.object(runner, 'ROOT', root), patch.object(runner, 'BUNDLE_MANIFEST', manifest):
                provenance = runner.source_provenance(self.fixture)
                self.assertIsNone(provenance['source_commit'])
                self.assertIsNone(provenance['repository_dirty_at_start'])
                self.assertEqual(provenance['bundle_origin'], self.report['provenance'])
                self.assertEqual(provenance['bundle_payload_mismatches'], ['payload.txt'])
                with self.assertRaisesRegex(ValueError, 'payload integrity check failed'):
                    runner.build_report(self.fixture)

    def test_nonfinite_json_is_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'nonfinite.json'
            for value in ('NaN', 'Infinity', '-Infinity'):
                path.write_text('{"value": '+value+'}')
                with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'nonfinite JSON value'):
                    runner.read_json(path)


if __name__ == '__main__':
    unittest.main()
