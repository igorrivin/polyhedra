#!/usr/bin/env python3
"""Back up and remove only independently validated sidecars named by failed fsck."""
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import subprocess
import sys
import zlib
from datetime import datetime, timezone

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
CHECKPOINT = Path(__file__).resolve().parent
OUT = CHECKPOINT / 'git-sidecar-recovery'
EXPECTED_HEAD = '5e34f23d981631605783cbe0f74247659f12a10a'
FSCK_SEQUENCE = 174
PHASE = sys.argv[1]
COMMANDS = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def ensure(condition, message):
    if not condition:
        raise RuntimeError(message)


def git(*args):
    proc = subprocess.run(['git', *args], cwd=ROOT, capture_output=True)
    COMMANDS.append({'argv': ['git', *args], 'cwd': str(ROOT), 'returncode': proc.returncode,
                     'stdout_bytes': len(proc.stdout), 'stdout_sha256': sha(proc.stdout),
                     'stdout': proc.stdout.decode(errors='replace') if len(proc.stdout) < 300 else None,
                     'stderr': proc.stderr.decode(errors='replace')})
    ensure(proc.returncode == 0, f'Git counterpart validation failed: {args!r}')
    return proc.stdout


def regular(path):
    ensure(stat.S_ISREG(path.lstat().st_mode) and not path.is_symlink(), f'Not a regular file: {path}')


def apple_double(data):
    ensure(len(data) >= 26, 'AppleDouble header truncated')
    magic, version, filler, count = struct.unpack('>II16sH', data[:26])
    ensure(magic == 0x00051607 and version == 0x00020000, 'Not a version-2 AppleDouble sidecar')
    table_end = 26 + 12 * count
    ensure(0 < count <= 64 and table_end <= len(data), 'Invalid AppleDouble entry count/table')
    entries = []
    for i in range(count):
        entry_id, offset, length = struct.unpack('>III', data[26 + 12 * i:38 + 12 * i])
        ensure(offset >= table_end and offset + length <= len(data), 'AppleDouble entry outside file')
        entries.append({'id': entry_id, 'offset': offset, 'length': length})
    ensure(len({e['id'] for e in entries}) == count, 'Duplicate AppleDouble entry IDs')
    ordered = sorted(entries, key=lambda e: e['offset'])
    ensure(all(a['offset'] + a['length'] <= b['offset'] for a, b in zip(ordered, ordered[1:])), 'Overlapping AppleDouble entries')
    return {'magic_hex': f'{magic:08x}', 'version_hex': f'{version:08x}',
            'filler_hex': filler.hex(), 'entry_count': count, 'entries': entries,
            'header_and_entry_bounds_valid': True}


def counterpart(path):
    genuine = path.with_name(path.name[2:])
    regular(genuine)
    data = genuine.read_bytes()
    info = {'path': str(genuine.relative_to(ROOT)), 'bytes': len(data), 'sha256': sha(data)}
    if path.parent == ROOT / '.git/refs/heads':
        ensure(genuine.name == 'main' and data == (EXPECTED_HEAD + '\n').encode(), 'Genuine branch ref differs')
        ensure(git('rev-parse', 'refs/heads/main').decode().strip() == EXPECTED_HEAD, 'Main ref resolution differs')
        ensure(git('cat-file', '-t', EXPECTED_HEAD) == b'commit\n', 'Main ref does not identify a commit')
        info.update({'kind': 'branch_ref', 'resolved_commit': EXPECTED_HEAD, 'git_validated': True})
    else:
        object_id = path.parent.name + genuine.name
        ensure(re.fullmatch('[0-9a-f]{40}', object_id) is not None, 'Invalid counterpart object name')
        decompressor = zlib.decompressobj()
        raw = decompressor.decompress(data) + decompressor.flush()
        ensure(decompressor.eof and not decompressor.unused_data and not decompressor.unconsumed_tail, 'Malformed loose-object zlib stream')
        header, payload = raw.split(b'\0', 1)
        kind, size_bytes = header.split(b' ', 1)
        ensure(kind in (b'blob', b'tree', b'commit', b'tag') and int(size_bytes) == len(payload), 'Invalid loose-object header/size')
        ensure(hashlib.sha1(raw).hexdigest() == object_id, 'Loose-object SHA1 differs from genuine filename')
        ensure(git('cat-file', '-t', object_id).strip() == kind, 'Git reports another object type')
        ensure(int(git('cat-file', '-s', object_id)) == len(payload), 'Git reports another object size')
        ensure(git('cat-file', kind.decode(), object_id) == payload, 'Git object payload differs from decoded genuine file')
        info.update({'kind': 'loose_object', 'object_id': object_id, 'object_type': kind.decode(),
                     'payload_bytes': len(payload), 'payload_sha256': sha(payload),
                     'zlib_header_size_sha1_valid': True, 'git_validated': True})
    return info


def inspect():
    OUT.mkdir(exist_ok=False)
    backup_dir = OUT / 'backups'
    backup_dir.mkdir()
    records = [json.loads(line) for line in (CHECKPOINT / 'commands.jsonl').read_text().splitlines()]
    report = next(row for row in records if row['sequence'] == FSCK_SEQUENCE)
    ensure(report['argv'] == ['git', 'fsck', '--full'] and report['returncode'] == 8, 'Wrong failed fsck report')
    stderr_path = CHECKPOINT / report['stderr']['path']
    stderr = stderr_path.read_bytes()
    ensure(sha(stderr) == report['stderr']['sha256'], 'Failed fsck report changed')
    reported = []
    for line in stderr.decode().splitlines():
        if line.startswith('error: refs/heads/._main: badRefName:') or line.startswith('error: refs/heads/._main: badRefContent:'):
            path = '.git/refs/heads/._main'
        else:
            match = re.fullmatch(r'bad sha1 file: (\.git/objects/[0-9a-f]{2}/\._[0-9a-f]{38})', line)
            ensure(match is not None, f'Unexpected fsck error cannot be cleaned: {line}')
            path = match.group(1)
        if path not in reported:
            reported.append(path)
    ensure(len(reported) == 45, 'Expected the observed 45 exact reported sidecars')
    ensure(git('rev-parse', 'HEAD').decode().strip() == EXPECTED_HEAD, 'HEAD changed before sidecar recovery')
    checks = []
    for index, relative in enumerate(reported, 1):
        path = ROOT / relative
        regular(path)
        data = path.read_bytes()
        header = apple_double(data)
        original = counterpart(path)
        backup = backup_dir / f'{index:02d}-{path.parent.name}-{path.name[2:]}.appledouble.bin'
        ensure(not backup.exists(), 'Refusing to overwrite a sidecar backup')
        backup.write_bytes(data)
        ensure(backup.read_bytes() == data, 'Backup bytes differ')
        checks.append({'reported_path': relative, 'sidecar_bytes': len(data), 'sidecar_sha256': sha(data),
                       'apple_double': header, 'genuine_counterpart': original,
                       'backup_path': str(backup.relative_to(CHECKPOINT)), 'backup_sha256': sha(backup.read_bytes()),
                       'backup_byte_for_byte_verified': True})
    receipt = {'recorded_utc': datetime.now(timezone.utc).isoformat(), 'phase': 'inspect_and_backup',
               'source_commit': EXPECTED_HEAD, 'failed_fsck_sequence': FSCK_SEQUENCE,
               'failed_fsck_stderr_path': str(stderr_path.relative_to(CHECKPOINT)),
               'failed_fsck_stderr_sha256': sha(stderr), 'reported_count': len(reported),
               'all_headers_backups_counterparts_validated': True, 'files': checks, 'commands': COMMANDS,
               'deletion_performed': False}
    (OUT / 'inspection.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'phase': 'inspect_and_backup', 'passed': True, 'files': len(checks), 'receipt': str(OUT / 'inspection.json')}))


def remove():
    inspection_path = OUT / 'inspection.json'
    inspection = json.loads(inspection_path.read_text())
    ensure(inspection['all_headers_backups_counterparts_validated'] is True, 'Inspection has not passed')
    ensure(not (OUT / 'removal.json').exists(), 'Removal already recorded')
    ensure(git('rev-parse', 'HEAD').decode().strip() == EXPECTED_HEAD, 'HEAD changed before sidecar removal')
    for row in inspection['files']:
        path = ROOT / row['reported_path']
        regular(path)
        data = path.read_bytes()
        ensure(len(data) == row['sidecar_bytes'] and sha(data) == row['sidecar_sha256'], 'Sidecar changed after backup')
        ensure(apple_double(data) == row['apple_double'], 'Sidecar header changed after backup')
        ensure((CHECKPOINT / row['backup_path']).read_bytes() == data, 'Sidecar backup no longer identical')
        ensure(counterpart(path) == row['genuine_counterpart'], 'Genuine counterpart changed before deletion')
    removed = []
    for row in inspection['files']:
        path = ROOT / row['reported_path']
        ensure(sha(path.read_bytes()) == row['sidecar_sha256'], 'Sidecar changed immediately before unlink')
        path.unlink()
        ensure(not path.exists(), 'Sidecar unlink did not take effect')
        original = ROOT / row['genuine_counterpart']['path']
        ensure(sha(original.read_bytes()) == row['genuine_counterpart']['sha256'], 'Genuine counterpart changed during sidecar unlink')
        removed.append({'path': row['reported_path'], 'operation': 'Path.unlink',
                        'sidecar_sha256': row['sidecar_sha256'], 'backup_path': row['backup_path'],
                        'genuine_counterpart_unchanged': True})
    ensure(git('rev-parse', 'HEAD').decode().strip() == EXPECTED_HEAD, 'HEAD changed after sidecar removal')
    receipt = {'recorded_utc': datetime.now(timezone.utc).isoformat(), 'phase': 'remove_confirmed_sidecars',
               'source_commit': EXPECTED_HEAD, 'inspection_path': str(inspection_path.relative_to(CHECKPOINT)),
               'inspection_sha256': sha(inspection_path.read_bytes()), 'removed_count': len(removed),
               'removed': removed, 'commands': COMMANDS, 'all_genuine_counterparts_unchanged': True,
               'only_exact_fsck_reported_confirmed_appledouble_sidecars_removed': True}
    (OUT / 'removal.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'phase': 'remove_confirmed_sidecars', 'passed': True, 'files': len(removed), 'receipt': str(OUT / 'removal.json')}))


if PHASE == 'inspect':
    inspect()
elif PHASE == 'remove':
    remove()
else:
    raise RuntimeError('Expected inspect or remove')
