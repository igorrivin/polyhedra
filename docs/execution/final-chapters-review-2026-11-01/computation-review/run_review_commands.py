from pathlib import Path
import json
import os
import subprocess
import time
from hashlib import sha256
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

ROOT=Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE=ROOT.parent/'execution/final-chapters-review-2026-11-01/computation-review'
PY='/tmp/polyhedra-baseline-20261031/bin/python'
jobs=[('tests-normal',[PY,'-B','-m','unittest','discover','-s','experiments/quantum_geodesics/tests','-v'],ROOT),
      ('tests-optimized',[PY,'-B','-O','-m','unittest','discover','-s','experiments/quantum_geodesics/tests','-v'],ROOT),
      ('ruff',['/opt/anaconda3/bin/ruff','check','experiments/quantum_geodesics'],ROOT),
      ('independent-replay',[PY,'-B',str(ROOT/'experiments/quantum_geodesics/run.py'),'--output',str(HERE/'independent-replay-result.json')],Path('/private/tmp'))]
def execute(job):
    name,argv,cwd=job
    start=time.perf_counter()
    result=subprocess.run(argv,cwd=cwd,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','GIT_OPTIONAL_LOCKS':'0'},capture_output=True,text=True,check=False)
    files={}
    for stream in ('stdout','stderr'):
        path=HERE/(name+'.'+stream+'.txt')
        with path.open('x') as file:file.write(getattr(result,stream))
        files[stream]={'path':path.name,'sha256':sha256(path.read_bytes()).hexdigest()}
    return {'name':name,'argv':argv,'cwd':str(cwd),'returncode':result.returncode,'elapsed_seconds':time.perf_counter()-start,'logs':files}
with ThreadPoolExecutor(max_workers=4) as pool:
    rows=list(pool.map(execute,jobs))
with (HERE/'command-receipts.json').open('x') as file:
    json.dump({'recorded_at_utc':datetime.now(timezone.utc).isoformat(),'commands':rows,'scope':'Actual independent reviewer replay and focused regressions; not clean-source replay or independent numerical-oracle approval.'},file,indent=2)
    file.write('\n')
print(json.dumps([{k:row[k] for k in ('name','returncode','elapsed_seconds')} for row in rows]))
if any(row['returncode'] for row in rows):raise SystemExit(1)
