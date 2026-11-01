"""A render-only operation must not reattribute changed code to an old run."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('section9_runner', ROOT / 'experiments/section9/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class RenderingIdentityTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ROOT / 'experiments/section9/fixture.json'
        self.report = {'schema_version': 2, 'experiment_id': json.loads(self.fixture.read_text())['id'],
                       'provenance': runner.source_provenance(self.fixture)}

    def test_identical_relocated_fixture_is_allowed(self):
        with tempfile.TemporaryDirectory() as name:
            fixture = Path(name) / 'fixture.json'
            fixture.write_bytes(self.fixture.read_bytes())
            runner.validate_render_sources(self.report, fixture)

    def test_changed_code_or_input_is_rejected(self):
        changed = copy.deepcopy(self.report)
        changed['provenance']['source_sha256']['experiment.driver'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'source hash differs: experiment.driver'):
            runner.validate_render_sources(changed, self.fixture)
        changed = copy.deepcopy(self.report)
        changed['provenance']['input_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'input hash'):
            runner.validate_render_sources(changed, self.fixture)

    def test_new_chapter_role_cannot_be_silently_attached_to_older_report(self):
        changed = copy.deepcopy(self.report)
        changed['provenance']['source_files'] = [row for row in changed['provenance']['source_files'] if row['role'] != 'book.chapter']
        with self.assertRaisesRegex(ValueError, 'availability differs: book.chapter'):
            runner.validate_render_sources(changed, self.fixture)

    def test_missing_requested_assets_fail_before_output(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result = root / 'result.json'
            result.write_text(json.dumps(self.report))
            for keyword in ('chapter_page', 'book_source_archive'):
                with self.subTest(keyword=keyword), self.assertRaisesRegex(FileNotFoundError, 'requested'):
                    runner.render_site(self.report, self.fixture, result, root / 'site', **{keyword: root / 'missing'})
                self.assertFalse((root / 'site').exists())

    def test_result_bytes_cannot_be_replaced_by_different_report(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            result = root / 'result.json'
            result.write_text('{}')
            with self.assertRaisesRegex(ValueError, 'does not contain'):
                runner.render_site(self.report, self.fixture, result, root / 'site')

    def test_rendering_environment_does_not_rewrite_captured_dependency_versions(self):
        with tempfile.TemporaryDirectory() as name:
            destination = Path(name) / 'reproduction.zip'
            with patch.object(runner.np, '__version__', '999-render-only'), \
                    patch.object(runner.platform, 'python_version', return_value='999-render-only'):
                runner.validate_render_sources(self.report, self.fixture)
                runner.create_reproduction_bundle(self.report, self.fixture, destination)
            with zipfile.ZipFile(destination) as archive:
                requirements = archive.read('section9-reproduction/requirements.txt').decode()
                readme = archive.read('section9-reproduction/README.md').decode()
            self.assertIn('numpy==' + self.report['provenance']['numpy'], requirements)
            self.assertIn('CPython ' + self.report['provenance']['python'], readme)
            self.assertNotIn('999-render-only', requirements + readme)


if __name__ == '__main__':
    unittest.main()
