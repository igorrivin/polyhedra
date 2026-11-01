"""Independent probe of render-only reproduction environment attribution.

Writes only temporary files plus this evidence directory. The version sentinels
simulate rendering an existing report under a different installed environment;
they are not a claim that those package versions exist.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import zipfile

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
spec = importlib.util.spec_from_file_location('review_section9_runner', ROOT / 'experiments/section9/run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
fixture = ROOT / 'experiments/section9/fixture.json'
report = {'schema_version': 2, 'experiment_id': json.loads(fixture.read_text())['id'],
          'provenance': runner.source_provenance(fixture)}
with tempfile.TemporaryDirectory(prefix='section9-review-render-') as name:
    destination = Path(name) / 'reproduction.zip'
    with patch.object(runner.platform, 'python_version', return_value='99.98.97'), \
            patch.object(runner.np, '__version__', '98.97.96'):
        runner.validate_render_sources(report, fixture)
        runner.create_reproduction_bundle(report, fixture, destination)
    with zipfile.ZipFile(destination) as bundle:
        requirements = bundle.read('section9-reproduction/requirements.txt').decode()
        readme = bundle.read('section9-reproduction/README.md').decode()
        manifest = json.loads(bundle.read('section9-reproduction/section9-bundle.json'))
    output = {
        'operation': 'independent render-only environment attribution probe',
        'driver_sha256': sha256((ROOT / 'experiments/section9/run.py').read_bytes()).hexdigest(),
        'recorded_numerical_python': report['provenance']['python'],
        'recorded_numerical_numpy': report['provenance']['numpy'],
        'origin_provenance_unchanged': manifest['origin_provenance'] == report['provenance'],
        'requirements': requirements,
        'readme_claims_render_environment_as_captured_run': 'captured reproduction used CPython 99.98.97' in readme,
        'requirements_use_render_environment': 'numpy==98.97.96' in requirements,
        'expected': 'Capturing a report from another environment must retain that report environment for reproduction requirements and captured-run prose, or explicitly label any changed render environment.',
    }
Path(__file__).with_suffix('.json').write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(output, indent=2))
