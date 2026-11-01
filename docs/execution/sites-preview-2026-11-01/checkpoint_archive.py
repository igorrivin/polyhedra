"""Inspect the actual official offline archive without publishing it."""
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path, PurePosixPath
import argparse
import json
import tarfile
import tempfile

OUTER = Path('/Volumes/Lexar/lambda/devel/polyhedra')
RAW = OUTER / 'execution/sites-preview-2026-11-01'
MIRROR = OUTER / 'publishing/polyhedra-reading-preview-20261101'


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument('--archive', type=Path, required=True)
parser.add_argument('--sha256', required=True)
args = parser.parse_args()
archive_path = args.archive.resolve()
assert digest(archive_path) == args.sha256
export = json.loads((RAW / 'final-export-verification.json').read_text())
payload = export['payload_sha256']
allowed_files = {'dist/' + name for name in payload} | {'dist/.openai/hosting.json'}
allowed_dirs = set()
for name in allowed_files:
    allowed_dirs.update(str(p) for p in PurePosixPath(name).parents if str(p) != '.')
output = Path(tempfile.mkdtemp(prefix='polyhedra-sites-archive-verified-')).resolve()
inventory = []
format_metadata = []
allowed_pax = {'mtime', 'LIBARCHIVE.xattr.com.apple.provenance',
               'SCHILY.xattr.com.apple.provenance'}
with tarfile.open(archive_path, 'r:gz') as archive:
    members = archive.getmembers()
    names = [member.name.rstrip('/') for member in members]
    assert len(names) == len(set(names)), 'duplicate archive names'
    files = set()
    for member, name in zip(members, names):
        parts = PurePosixPath(name).parts
        assert not PurePosixPath(name).is_absolute() and '..' not in parts
        assert not any(part.startswith('._') or part in ('.DS_Store', '__MACOSX', '.git') for part in parts), name
        assert set(member.pax_headers) <= allowed_pax, name
        format_metadata.append({'path': name, 'pax_value_sha256': {
            key: sha256(value.encode('utf-8', 'surrogateescape')).hexdigest()
            for key, value in member.pax_headers.items()}})
        if member.isdir():
            assert name in allowed_dirs, name
            continue
        assert member.isfile() and not member.issym() and not member.islnk(), name
        assert name in allowed_files, name
        files.add(name)
        stream = archive.extractfile(member)
        assert stream is not None
        data = stream.read()
        h = sha256(data).hexdigest()
        if name == 'dist/.openai/hosting.json':
            hosting = json.loads(data)
            assert hosting == {'project_id': 'appgprj_6ae6b5b94abc8191aa00dfe244adcf37',
                               'static': {'directory': 'dist'}}
        else:
            relative = name.removeprefix('dist/')
            assert h == payload[relative] == digest(MIRROR / 'dist' / relative), name
        destination = output / name
        assert destination.resolve().is_relative_to(output)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        assert digest(destination) == h
        inventory.append({'path': name, 'sha256': h, 'bytes': len(data)})
    assert files == allowed_files
assert (output / 'dist/index.html').is_file()
assert len(inventory) == 50
assert digest(archive_path) == args.sha256
record = {'status': 'offline_archive_verified_not_published',
          'verified_at_utc': datetime.now(timezone.utc).isoformat(),
          'archive_path': str(archive_path), 'archive_sha256': args.sha256,
          'archive_bytes': archive_path.stat().st_size, 'extracted_directory': str(output),
          'research_source_commit': export['source_commit'], 'site_source_commit': None,
          'project_id': hosting['project_id'], 'hosting': hosting,
          'member_count': len(members), 'file_count': len(inventory),
          'payload_files_identical_to_clean_export': 49,
          'sidecar_files_symlinks_traversal_duplicates_and_extra_payloads_absent': True,
          'pax_scope': 'Official macOS archive format retains only mtime and the two com.apple.provenance PAX representations. These headers are recorded, not claimed absent. No sidecar payload files exist.',
          'format_metadata': format_metadata,
          'normalization': 'Official helper adds the minimal static hosting manifest under dist/.openai; all 49 preview files are unchanged.',
          'files': inventory,
          'publication': 'No pushed Sites source commit, saved version or deployment exists for this candidate.',
          'browser_verification': 'Not performed; archive extraction/hash verification is not browser QA.'}
(RAW / 'final-archive-verification.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: record[key] for key in ('status', 'archive_sha256', 'archive_bytes',
                                             'file_count', 'payload_files_identical_to_clean_export',
                                             'extracted_directory')}, indent=2))
