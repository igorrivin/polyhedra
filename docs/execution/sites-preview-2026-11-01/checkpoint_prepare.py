"""Copy frozen review evidence and prepare the explicit source checkpoint."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import argparse
import json
import subprocess

OUTER = Path('/Volumes/Lexar/lambda/devel/polyhedra')
ROOT = OUTER / 'consolidated'
RAW = OUTER / 'execution/sites-preview-2026-11-01'
DEST = ROOT / 'docs/execution/sites-preview-2026-11-01'
MIRROR = OUTER / 'publishing/polyhedra-reading-preview-20261101'
BASELINE = '800219f78bdacaf77639cf4d38ff27d4b7342faa'
PROJECT = 'appgprj_6ae6b5b94abc8191aa00dfe244adcf37'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


parser = argparse.ArgumentParser()
parser.add_argument('--review-report', required=True)
parser.add_argument('--review-manifest', required=True)
args = parser.parse_args()
for name in (args.review_report, args.review_manifest):
    if Path(name).name != name or not (RAW / name).is_file():
        raise SystemExit('Expected an existing frozen top-level review file')
assert subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], cwd=ROOT, text=True).strip() == str(ROOT)
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == BASELINE
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=ROOT, text=True).strip()
author = json.loads((RAW / 'author-final-manifest.json').read_text())
for name, expected in author['source_sha256'].items():
    assert digest(ROOT / name) == expected, name

DEST.mkdir(parents=True, exist_ok=True)
patterns = ('author-*', 'build_preview-before-*', 'test_build_preview-before-*',
            'index-before-*', 'navigation-correction.json', 'review-*')
selected = {p for pattern in patterns for p in RAW.glob(pattern)
            if p.is_file() and not p.name.startswith('._')}
selected.update((RAW / args.review_report, RAW / args.review_manifest))
selected.update(p for p in (RAW / 'review-before-explicit-links').glob('*')
                if p.is_file() and not p.name.startswith('._'))
copies = []
for source in sorted(selected):
    relative = source.relative_to(RAW)
    destination = DEST / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    assert digest(source) == digest(destination)
    copies.append({'source': str(source), 'destination': str(destination),
                   'sha256': digest(source), 'bytes': source.stat().st_size})
write_json(DEST / 'evidence-copy-manifest.json', {'scope': 'Frozen author and independent-review evidence, including retained failed drafts',
           'copied_at_utc': datetime.now(timezone.utc).isoformat(), 'files': copies})

registration = {
    'status': 'registered_owner_private_not_deployed',
    'source': 'Native Sites observations and the failed source-helper call recorded by the parent agent',
    'project_id': PROJECT,
    'title': 'Polyhedra, Moduli, and Quantum Geometry',
    'slug': 'polyhedra-moduli-quantum-geometry',
    'created_at': '2026-11-01T03:44:57.582143+00:00',
    'expected_url': 'https://polyhedra-moduli-quantum-geometry.ig-riv.chatgpt.site',
    'expected_url_is_verified_live': False,
    'current_user_role': 'owner', 'access_mode': 'custom',
    'allowed_user_roles': ['owner'], 'allowed_group_count': 0,
    'latest_version_number': 0, 'current_live_url': None,
    'source_commit': None, 'saved_version_id': None, 'deployment_id': None,
    'source_open_attempt': {
        'argv': ['node', '/Users/igorrivin/.codex/plugins/cache/openai-curated-remote/sites/1.1.2/scripts/site-workflow.mjs',
                 '--project-id', PROJECT],
        'cwd': str(MIRROR), 'mode': 'open; no archive or build commands supplied',
        'credential_transport': 'hidden stdin; credential not retained in this record',
        'returncode': 128,
        'error': "fatal: unable to access 'https://git.chatgpt-team.site/7ae148ba-74b8-450e-b2a4-951aca23fb81/appgprj_6ae6b5b94abc8191aa00dfe244adcf37.git/': Could not resolve host: git.chatgpt-team.site",
        'effect': 'Helper initialized the derived checkout, then failed before source synchronization; no push or publication occurred.'},
    'continuation': 'Reuse this project ID after actual network recovery. Read current Site access, obtain a fresh source write credential, and use the supported source helper to commit/push/package before saving or deploying the exact resulting source/archive. Do not substitute the canonical research commit for the Sites source commit.',
    'secrets': 'No token, credential, bypass secret or authentication header is stored.'}
write_json(DEST / 'site-registration.json', registration)

readme = f'''# Section 9 Sites reading preview

This checkpoint adds a reading frontend to the already reviewed Section 9
chapter and its two computational companions. The [exporter](../../../site/build_preview.py)
adds a six-subsection contents list, local passage search and shared navigation.
The PDF, numerical reports, figures, code and reproduction ZIPs retain the
frozen scientific bytes from the [barrier checkpoint](../section9-barrier-2026-10-31/README.md).
The three derived HTML pages differ only by two reversible presentation inserts.
This is a presentation increment, not a new computation or mathematical review.

The [independent review]({args.review_report}) and [review manifest]({args.review_manifest})
approve exact source hashes. Their checks include 25 site tests, pure search
assertions, real-edition queries, 473 local/search targets, 204 indexed passages,
the 209 original MathML nodes and exact HTML restoration. Initial path,
symlink and directory-link findings remain preserved in the
[evidence inventory](evidence-copy-manifest.json). Browser rendering and
interaction were not tested; no browser or local server was launched.

The [registered Site](site-registration.json) is owner-private and has no saved
version or live deployment. The source helper failed because the environment
could not resolve `git.chatgpt-team.site`. Its expected URL is not evidence of
publication. No credentials are stored in this checkpoint. The derived checkout
is outside the research repository at `{MIRROR}`.

Clean-source generation and a separately inspected offline deployment candidate
follow the reviewed source commit. Platform sidecars must be removed from the
generated export only after their headers and genuine payload hashes are checked;
an ordinary asset manifest alone does not prove archive curation. Publication
remains dependent on source synchronization through the supported Sites workflow.
The complete LaTeX download is the broader draft; Section 9's review does not
extend to the rest of the monograph.
'''
(DEST / 'README.md').write_text(readme)

source_paths = sorted(author['source_sha256'])
evidence_paths = sorted(str(p.relative_to(ROOT)) for p in DEST.rglob('*')
                        if p.is_file() and not any(part.startswith('._') for part in p.relative_to(DEST).parts))
paths = source_paths + evidence_paths
ignored, normal = [], []
for name in paths:
    result = subprocess.run(['git', 'check-ignore', '-q', '--', name], cwd=ROOT)
    assert result.returncode in (0, 1), name
    (ignored if result.returncode == 0 else normal).append(name)
manifest = {'baseline': BASELINE, 'scope': 'Reviewed presentation sources and frozen checkpoint evidence only',
            'source_paths': source_paths, 'normal_paths': normal, 'explicit_ignored_evidence': ignored,
            'sha256': {name: digest(ROOT / name) for name in paths},
            'review_report_sha256': digest(RAW / args.review_report),
            'review_manifest_sha256': digest(RAW / args.review_manifest)}
write_json(RAW / 'source-staging-manifest.json', manifest)
print(json.dumps({'copied_evidence': len(copies), 'staging_paths': len(paths),
                  'explicit_ignored_evidence': len(ignored), 'manifest': str(RAW / 'source-staging-manifest.json')}, indent=2))
