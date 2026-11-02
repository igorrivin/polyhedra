"""Supplemental reviewer probes of declared local acceptance/source identities."""
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from experiments.quantum_geodesics import run

baseline = run.load_fixture()
cases = [
    ('wrong_quantum_acceptance_hash', ['formula_contracts', 'quantum', 'review_acceptance_sha256'], '0'*64),
    ('wrong_quantum_source_freeze_hash', ['formula_contracts', 'quantum', 'accepted_source_freeze_sha256'], '0'*64),
    ('wrong_geodesic_contract_acceptance_hash', ['formula_contracts', 'geodesic', 'review_acceptance_sha256'], '0'*64),
    ('wrong_geodesic_source_acceptance_hash', ['formula_contracts', 'geodesic', 'final_source_review_sha256'], '0'*64),
    ('wrong_geodesic_accepted_source_set_hash', ['formula_contracts', 'geodesic', 'accepted_source_set_sha256'], '0'*64),
    ('wrong_accepted_manuscript_pin', ['accepted_manuscript_sha256', 'book/chapters/10-quantum-introduction.tex'], '0'*64),
]
records = []
for name, keys, value in cases:
    data = deepcopy(baseline)
    target = data
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    try:
        run.validate_fixture(data)
    except (ArithmeticError, ValueError, TypeError, KeyError) as error:
        records.append({'name': name, 'path': keys, 'replacement': value,
                        'rejected': True, 'exception': type(error).__name__, 'message': str(error)})
    else:
        records.append({'name': name, 'path': keys, 'replacement': value, 'rejected': False})
output = HERE/('provenance-controls-optimized-v1.json' if sys.flags.optimize else 'provenance-controls-normal-v1.json')
with output.open('x') as handle:
    json.dump({'schema_version': 1, 'optimized': bool(sys.flags.optimize), 'records': records,
               'scope': 'Only in-memory fixture changes; valid original acceptance copies and canonical files untouched.'}, handle, indent=2)
    handle.write('\n')
print(json.dumps({'checks': len(records), 'accepted_corruptions': [r['name'] for r in records if not r['rejected']]}))
