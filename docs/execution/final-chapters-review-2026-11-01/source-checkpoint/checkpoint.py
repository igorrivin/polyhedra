"""Execute the specifically approved forty-path source checkpoint; no artifacts."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent
ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
TOOL_DIR = OUTER / 'checkpoint-work/revision-v3'
sys.path.insert(0, str(TOOL_DIR))
import checkpoint_lib as lib
import verify_checkpoint as verify

BASELINE = lib.BASELINE
APPROVAL = 'integration-review/final-acceptance.json'
APPROVAL_ID = {'sha256': '84b9eb77d45339fad20af6df2439f710a9fc2a47af35c823f4b3f8e3029cd708', 'bytes': 18644}
CODE = 'computation-review/revision-v2/final-acceptance.json'
CODE_ID = {'sha256': '70070fe32c42961d68b035ccb7fae5b012c50ac5814ca42bd05689bfc64b6592', 'bytes': 25941}
PREP = OUTER / 'checkpoint-curation-preparation'


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    lib.require(len(sys.argv) in (3, 4) and sys.argv[1] in ('commit', 'verify'), 'mode and new attempt name required')
    mode, attempt = sys.argv[1:3]
    lib.require(re.fullmatch('[a-z0-9-]+', attempt), 'unsafe attempt name')
    source = None if mode == 'commit' else sys.argv[3]
    lib.require(mode == 'commit' or re.fullmatch('[0-9a-f]{40}', source), 'actual source commit required')
    work = HERE / attempt
    work.mkdir(exist_ok=False)
    receipt = work / 'receipt.json'
    commands = work / 'commands.jsonl'
    report = {'schema_version': 1, 'passed': False, 'source_commit': source, 'baseline_commit': BASELINE,
              'parent_commit': None, 'git_status_porcelain': None, 'index_clean': False,
              'mode': mode, 'stage': 'approval_guards', 'commands': str(commands.relative_to(OUTER)),
              'scope': 'Actual source-only checkpoint and read-only preservation/integrity checks. No artifact copy, PDF build, science replay or publication.'}
    sequence = 0
    def command(argv, cwd=ROOT, allowed=(0,)):
        nonlocal sequence
        sequence += 1
        started = now()
        tick = time.perf_counter()
        process = subprocess.run(argv, cwd=cwd, env=lib.ENV, capture_output=True, check=False)
        output = {}
        for name, data in [('stdout', process.stdout), ('stderr', process.stderr)]:
            path = work / f'{sequence:03d}.{name}.bin'
            with path.open('xb') as handle:
                handle.write(data)
            output[name] = {'path': str(path.relative_to(OUTER)), **lib.identity(path)}
        row = {'sequence': sequence, 'argv': argv, 'cwd': str(cwd), 'started_at_utc': started,
               'finished_at_utc': now(), 'elapsed_seconds': time.perf_counter() - tick,
               'returncode': process.returncode, **output}
        with commands.open('a') as handle:
            handle.write(json.dumps(row) + '\n')
        lib.require(process.returncode in allowed,
                    f'Command {sequence} failed with exit {process.returncode}: {argv!r}')
        return process
    def git(*args):
        return command(['git', *args]).stdout
    def frozen_pin(name, expected):
        value, actual = lib.json_snapshot(OUTER / name)
        lib.require(actual == expected, 'approval identity differs: ' + name)
        frozen[str(OUTER / name)] = actual
        return value
    def current_hashes(mapping):
        actual = {p: lib.identity(lib.relative_path(ROOT, p))['sha256'] for p in mapping}
        lib.require(actual == mapping, 'current source/runtime/TeX hash differs')
        return actual
    def integrity():
        process = command(['git', 'fsck', '--full'], allowed=(0, 8))
        record = {'returncode': process.returncode, 'stdout': process.stdout.decode(),
                  'stderr': process.stderr.decode(), 'command_sequence': sequence,
                  'cleanup_performed': False}
        report.setdefault('integrity_attempts', []).append(record)
        lib.require(process.returncode == 0 and not process.stderr
                    and set(process.stdout.decode().splitlines()) <= verify.KNOWN_DANGLING,
                    'Git integrity failed; exact error preserved; this program performs no cleanup')
        return record
    with lib.receipt_record(OUTER, receipt, report):
        frozen = {str(Path(__file__).resolve()): lib.identity(Path(__file__).resolve())}
        approval = frozen_pin(APPROVAL, APPROVAL_ID)
        code = frozen_pin(CODE, CODE_ID)
        for key in ('source_integration_approved', 'precommit_pdf_build_and_visual_approved'):
            lib.require(approval[key] is True, 'integration approval predicate: ' + key)
        lib.require(approval['decision'] == 'approved_exact_source_integration_and_precommit_PDF_for_later_checkpoint'
                    and approval['required_open_findings'] == [] and approval['baseline_HEAD'] == BASELINE,
                    'integration decision/baseline differs')
        lib.require(code['implementation_approved'] is True and code['required_open_findings'] == [], 'code not accepted')
        accepted_tools, accepted_id = lib.json_snapshot(OUTER / 'checkpoint-review/revision-v3/final-acceptance.json')
        lib.require(accepted_id['sha256'] == '2c342b199506e589dbed3048e610c51846b739ecc3b9905540aff9624d8cac64', 'tool acceptance changed')
        frozen[str(OUTER / 'checkpoint-review/revision-v3/final-acceptance.json')] = accepted_id
        for name, expected in accepted_tools['accepted_preparation_files'].items():
            lib.require(lib.identity(TOOL_DIR / name) == expected, 'accepted helper changed: ' + name)
            frozen[str(TOOL_DIR / name)] = expected
        approved = lib.hash_map(approval['approved_source_sha256'], 'approved source')
        tex = lib.hash_map(approval['approved_active_tex_sha256'], 'active TeX')
        runtime = lib.hash_map(code['accepted_runtime_sha256'], 'runtime')
        lib.require(len(approved) == 40 and len(tex) == 36 and len(runtime) == 24
                    and runtime == approval['approved_runtime_sha256'], 'approved coverage/runtime differs')
        reference = code['accepted_author_result']
        lib.require(reference == approval['immutable_reviewed_author_result'], 'reference approvals differ')
        frozen[str(OUTER / reference['path'])] = {'sha256': reference['sha256'], 'bytes': reference['bytes']}
        pdf = approval['precommit_pdf']
        frozen[str(OUTER / pdf['path'])] = {'sha256': pdf['sha256'], 'bytes': pdf['bytes']}
        _, inventory_id = lib.json_snapshot(OUTER / 'structure/baseline-tracked-inventory.json')
        config = lib.parse_json((TOOL_DIR / 'checkpoint-contract.unready.json').read_bytes())
        lib.require(inventory_id == config['baseline_inventory']['identity'], 'baseline inventory differs')
        frozen[str(OUTER / 'structure/baseline-tracked-inventory.json')] = inventory_id
        provisional = lib.parse_json((PREP / 'source-checkpoint-plan.unready.json').read_bytes())
        lib.require(provisional['exact_source_sha256_provisional'] == approved, 'reviewed source plan map differs')
        observed_tex = {**code['author_tex_sha256'], **tex}
        lib.require(len(observed_tex) == 46, 'broader TeX observation coverage differs')
        guards = lib.merge_hashes(approved, tex, runtime, observed_tex)
        lib.require(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT), 'wrong Git root')
        lib.require(not git('remote'), 'unexpected remote')
        lib.require(git('config', '--get', 'core.filemode').strip() == b'false', 'exFAT Git filemode setting differs')
        base_tree = verify.tree(ROOT, BASELINE)
        modified = sorted(set(approved) & set(base_tree))
        added = sorted(set(approved) - set(base_tree))
        lib.require(len(base_tree) == 2273 and len(modified) == 6 and len(added) == 34, 'source inventory counts differ')
        report.update({'approval': {'path': APPROVAL, **APPROVAL_ID}, 'computation_approval': {'path': CODE, **CODE_ID},
                       'approved_source_sha256': approved, 'runtime_sha256': runtime,
                       'author_reference': reference, 'precommit_pdf': pdf, 'tex_input_sha256': tex,
                       'guard_sha256': guards, 'modified': modified, 'added': added,
                       'frozen_input_identities': frozen})
        current_hashes(guards)
        lib.require(lib.expand_tex(lambda p: (ROOT / p).read_bytes())[1] == tex, 'actual active TeX graph differs')
        lib.recheck(frozen)
        if mode == 'commit':
            report['stage'] = 'precommit_source_guards'
            lib.require(git('rev-parse', 'HEAD').decode().strip() == BASELINE, 'HEAD is not approved baseline')
            lib.require(not git('diff', '--cached', '--name-only'), 'index was not empty')
            status = git('status', '--porcelain=v1', '--untracked-files=all').decode()
            lib.require(set(status.splitlines()) == {' M ' + p for p in modified} | {'?? ' + p for p in added}, 'unexpected initial status')
            report['before'] = {'head': BASELINE, 'status_porcelain': status, 'index_clean': True, 'sha256': current_hashes(guards)}
            git('diff', '--check')
            for path in added:
                check = command(['git', 'diff', '--no-index', '--check', '--', '/dev/null', str(ROOT / path)], allowed=(0, 1, 2, 3))
                lib.require(check.returncode in (0, 1) and not check.stdout and not check.stderr, 'new source whitespace diagnostic: ' + path)
            report['precommit_integrity'] = integrity()
            path_list = work / 'approved-source-paths.nul'
            path_list.write_bytes(b'\0'.join(p.encode() for p in sorted(approved)) + b'\0')
            report['path_list'] = {'path': str(path_list.relative_to(OUTER)), **lib.identity(path_list)}
            lib.recheck(frozen)
            report['stage'] = 'stage_exact_source'
            git('--literal-pathspecs', 'add', '--pathspec-from-file=' + str(path_list), '--pathspec-file-nul')
            staged = git('diff', '--cached', '--no-renames', '--name-status').decode().splitlines()
            lib.require(set(staged) == {'M\t' + p for p in modified} | {'A\t' + p for p in added}, 'staged path/status set differs')
            git('diff', '--cached', '--check')
            lib.require(not git('diff', '--name-only'), 'unstaged source remains')
            index = {}
            for row in git('ls-files', '--stage', '-z').split(b'\0'):
                if row:
                    fields, name = row.split(b'\t', 1)
                    index[name.decode()] = fields.decode().split()
            for name, expected in approved.items():
                lib.require(index[name][0] == '100644' and index[name][2] == '0', 'staged Git mode/stage differs: ' + name)
                lib.require(sha256(git('show', ':' + name)).hexdigest() == expected, 'staged blob differs: ' + name)
            lib.require(set(git('status', '--porcelain=v1', '--untracked-files=all').decode().splitlines())
                        == {'M  ' + p for p in modified} | {'A  ' + p for p in added}, 'unexpected staged status')
            current_hashes(guards)
            lib.recheck(frozen)
            report['stage'] = 'commit_source'
            git('commit', '--file', str(PREP / 'source-commit-message.draft.txt'))
            source = git('rev-parse', 'HEAD').decode().strip()
            report['source_commit'] = source
        report['stage'] = 'postcommit_source_guards'
        lib.require(git('rev-list', '--parents', '-n', '1', source).decode().split() == [source, BASELINE], 'source is not direct child')
        report['parent_commit'] = BASELINE
        report['after'] = lib.source_state(ROOT, source, guards)
        report['git_status_porcelain'] = git('status', '--porcelain=v1', '--untracked-files=all').decode()
        lib.require(report['git_status_porcelain'] == '' and not git('diff', '--cached', '--name-only'), 'postcommit state not clean')
        report['index_clean'] = True
        report['preservation'] = verify.preservation(ROOT, OUTER, source, approved, config)
        report['manuscript'] = verify.manuscript(ROOT, source, {'tex_input_sha256': tex, 'approved_source_sha256': approved}, config)
        report['postcommit_integrity'] = integrity()
        lib.recheck(frozen)
        lib.require(lib.source_state(ROOT, source, guards) == report['after'], 'source drift at completion')
        report.update({'stage': 'complete', 'passed': True, 'checks_passed': True})
    final = HERE / 'source-checkpoint.json'
    with final.open('xb') as handle:
        handle.write(receipt.read_bytes())
    print(json.dumps({'passed': True, 'source_commit': source, 'receipt': str(final), 'identity': lib.identity(final)}))


if __name__ == '__main__':
    main()
