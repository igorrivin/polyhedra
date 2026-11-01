import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
EVIDENCE = ROOT.parent / 'execution/section9-barrier-2026-10-31'
PREVIEW = Path('/var/folders/07/k5d5zt815j92q33gdb61j1280000gn/T/polyhedra-barrier-integration-preview-20261031-baylv1cs')
work = Path(tempfile.mkdtemp(prefix='section9-barrier-publication-review-'))
archive_path = PREVIEW / 'site/section9/downloads/barrier-reproduction.zip'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
with zipfile.ZipFile(archive_path) as archive:
    names = archive.namelist()
    assert len(names) == len(set(names))
    assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in names)
    archive.extractall(work)
bundle = work / 'barrier-reproduction'
manifest = json.loads((bundle / 'barrier-bundle.json').read_text())
assert all(sha(bundle / p) == h for p, h in manifest['payload_sha256'].items())
assert not (bundle / '.git').exists()
execution = work / 'unrelated-working-directory'
execution.mkdir()
driver = bundle / 'experiments/section9/barrier_run.py'
result = work / 'detached-result.json'
site = work / 'detached-site'
imports = work / 'actual-imports.json'
program = '''import hashlib,json,runpy,sys
from pathlib import Path
source,output,site,imports = sys.argv[1:]
ns=runpy.run_path(source,run_name='detached_review')
rows={name:{'path':str(Path(ns[name].__file__).resolve()),'sha256':hashlib.sha256(Path(ns[name].__file__).read_bytes()).hexdigest()} for name in ('solver','var','geometry')}
Path(imports).write_text(json.dumps(rows,indent=2)+'\\n')
sys.argv=[source,'--output',output,'--site-dir',site]
raise SystemExit(ns['main']())
'''
env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
env.pop('PYTHONPATH', None)
command = ['/tmp/polyhedra-numerical-core-20261031/bin/python', '-c', program, str(driver), str(result), str(site), str(imports)]
proc = subprocess.run(command, cwd=execution, env=env, text=True, capture_output=True)
(EVIDENCE / 'publication-detached-replay.log').write_text(proc.stdout + proc.stderr)
record = {'archive':str(archive_path), 'archive_sha256':sha(archive_path), 'temporary_work':str(work), 'command':command,'cwd':str(execution),'exit_code':proc.returncode,'stdout':proc.stdout,'stderr':proc.stderr}
(EVIDENCE / 'publication-detached-replay.json').write_text(json.dumps(record,indent=2)+'\n')
assert proc.returncode == 0, proc.stderr
actual = json.loads(imports.read_text())
assert all(Path(row['path']).is_relative_to(bundle) for row in actual.values())
origin_result = json.loads((PREVIEW / 'site/section9/downloads/barrier-result.json').read_text())
replayed = json.loads(result.read_text())
assert replayed['all_checks_passed'] is True
assert replayed['cases'] == origin_result['cases']
assert replayed['provenance']['bundle_payload_hashes_match'] is True
assert replayed['provenance']['execution_context'] == 'detached-bundle'
assert replayed['provenance']['repository_dirty_at_start'] is None
assert replayed['provenance']['source_commit'] is None
assert replayed['provenance']['bundle_origin'] == origin_result['provenance']
assert not next(row for row in replayed['provenance']['source_files'] if row['role']=='book.chapter')['available']
record.update({'payloads_verified':len(manifest['payload_sha256']),'actual_imports':actual,'cases_exactly_equal':True,'recorded_checks_passed':sum(check['passed'] for case in replayed['cases'] for check in case['checks'].values()),'result_sha256':sha(result),'detached_provenance':replayed['provenance']})
(EVIDENCE / 'publication-detached-replay.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'temporary_work':str(work),'cases_exactly_equal':True,'recorded_checks_passed':record['recorded_checks_passed'],'payloads_verified':len(manifest['payload_sha256']),'imports':actual},indent=2))
