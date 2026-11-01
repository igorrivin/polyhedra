"""Fresh execution of both final numerical archives outside the checkout."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = Path(__file__).resolve().parent
location = json.loads((OUTER / 'final-generation-location.json').read_text())
generated = Path(location['preview_root'])
source_commit = location['source_commit']
work = Path(tempfile.mkdtemp(prefix='polyhedra-barrier-final-replays-')).resolve()
records = {}

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

program = '''import hashlib,json,runpy,sys
from pathlib import Path
driver,output,site,imports=sys.argv[1:]
namespace=runpy.run_path(driver,run_name="detached_checkpoint")
sys.argv=[driver,"--output",output,"--site-dir",site]
code=namespace["main"]()
rows={name:{"path":str(Path(module.__file__).resolve()),"sha256":hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()} for name,module in sys.modules.items() if (name=="ideal_poly_volume_toolkit" or name.startswith("ideal_poly_volume_toolkit.")) and getattr(module,"__file__",None)}
Path(imports).write_text(json.dumps(rows,indent=2)+"\\n")
raise SystemExit(code)
'''
env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}
env.pop('PYTHONPATH', None)
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
for label, archive_name, prefix, bundle_manifest, driver_name, report_name in [
    ('grid', 'section9-reproduction.zip', 'section9-reproduction', 'section9-bundle.json', 'run.py', 'result.json'),
    ('barrier', 'barrier-reproduction.zip', 'barrier-reproduction', 'barrier-bundle.json', 'barrier_run.py', 'barrier-result.json')]:
    archive_path = generated / 'site/section9/downloads' / archive_name
    destination = work / label
    destination.mkdir()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        assert all(not Path(name).is_absolute() and '..' not in Path(name).parts and name.startswith(prefix + '/') for name in names)
        manifest = json.loads(archive.read(prefix + '/' + bundle_manifest))
        assert set(names) == {prefix + '/' + name for name in manifest['payload_sha256']} | {prefix + '/' + bundle_manifest}
        for name, expected in manifest['payload_sha256'].items():
            assert sha256(archive.read(prefix + '/' + name)).hexdigest() == expected
        archive.extractall(destination)
    bundle = (destination / prefix).resolve()
    assert not (bundle / '.git').exists()
    original = json.loads((generated / report_name).read_text())
    assert manifest['origin_provenance'] == original['provenance']
    assert original['provenance']['source_commit'] == source_commit
    assert original['provenance']['repository_dirty_at_start'] is False
    cwd = destination / 'unrelated-working-directory'
    cwd.mkdir()
    output, site, imports = destination / 'replayed.json', destination / 'site', destination / 'imports.json'
    command = ['/tmp/polyhedra-numerical-core-20261031/bin/python', '-c', program,
               str(bundle / 'experiments/section9' / driver_name), str(output), str(site), str(imports)]
    proc = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True)
    log = OUTER / ('final-detached-' + label + '.log')
    log.write_text(proc.stdout + proc.stderr)
    row = {'archive': str(archive_path), 'archive_sha256': digest(archive_path),
           'command': command, 'working_directory': str(cwd), 'returncode': proc.returncode,
           'log_sha256': digest(log), 'bundle_root': str(bundle)}
    records[label] = row
    (OUTER / 'final-detached-replay.json').write_text(json.dumps({'status': 'running', 'records': records}, indent=2) + '\n')
    assert proc.returncode == 0, proc.stderr
    actual = json.loads(imports.read_text())
    assert actual
    for name, module in actual.items():
        path = Path(module['path']).resolve()
        assert path.is_relative_to(bundle), (name, path)
        relative = str(path.relative_to(bundle))
        assert module['sha256'] == manifest['payload_sha256'][relative] == digest(path), name
    replayed = json.loads(output.read_text())
    assert replayed['all_checks_passed'] is True
    assert {k: v for k, v in replayed.items() if k != 'provenance'} == {k: v for k, v in original.items() if k != 'provenance'}
    provenance = replayed['provenance']
    assert provenance['execution_context'] == 'detached-bundle'
    assert provenance['source_commit'] is None and provenance['repository_dirty_at_start'] is None
    assert provenance['bundle_origin'] == original['provenance']
    assert provenance['bundle_payload_hashes_match'] is True and not provenance['bundle_payload_mismatches']
    for item in provenance['source_files']:
        if item['role'] == 'book.chapter':
            assert item['available'] is False
    row.update({'payload_count': len(manifest['payload_sha256']), 'actual_imports': actual,
                'all_result_fields_except_provenance_identical': True, 'all_checks_passed': True,
                'result_path': str(output), 'result_sha256': digest(output), 'detached_provenance': provenance})
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
record = {'status': 'both_fresh_detached_replays_passed', 'finished_at_utc': datetime.now(timezone.utc).isoformat(),
          'source_commit': source_commit, 'repository_clean_throughout': True, 'records': records,
          'scope': 'Fresh numerical execution with existing minimal dependencies; no dependency installation, network resolution or browser use.'}
(OUTER / 'final-detached-replay.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'status': record['status'], 'source_commit': source_commit,
                  'records': {name: {key: value for key, value in row.items() if key in ('payload_count', 'all_result_fields_except_provenance_identical', 'all_checks_passed', 'archive_sha256', 'result_sha256')} for name, row in records.items()}}, indent=2))
