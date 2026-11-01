#!/usr/bin/env python3
"""Verify the local Section 15 checkpoint without replay, build, or mutation.

Candidate mode checks the exact new artifact set above the clean source commit.
Final mode checks its direct-child commit and a clean index/worktree. Receipts
are exclusive writes under the outer execution directory, avoiding a commit
that contains an assertion of its own hash. All gates remain active with -O.
"""
from argparse import ArgumentParser
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import copy
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

CANDIDATE_ROOT = Path(__file__).resolve().parents[3]
ROOT = CANDIDATE_ROOT if (CANDIDATE_ROOT/'book').is_dir() else CANDIDATE_ROOT/'consolidated'
REL = 'docs/execution/section15-analytic-review-2026-11-01'
CHECKPOINT = ROOT/REL
OUT = ROOT.parent/'execution/section15-analytic-review-2026-11-01'
BASELINE = '3ddf610dbe4578c7828e55f4e9cd92aacaba6df6'
MANIFEST = REL+'/candidate-artifact-manifest.json'
RESULT = 'artifacts/section15_quantum/result.json'
PDF = 'artifacts/section15-analytic-review-2026-11-01/monograph-working-draft.pdf'
ENV = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
MAIN = 'book/polyhedral_volumes_and_geodesic_identities.tex'
CHAPTER = 'book/chapters/15-quantum-airy.tex'
LEDGER = 'book/claims/section15.json'
FULL_V1 = 'bfb7bf75aa4522e794f2c6000863df786988a67bf92354d41d7075dfcee37a83'


def require(condition, message='Checkpoint invariant failed'):
    if not condition:
        raise RuntimeError(message)


def digest(data):
    return sha256(data).hexdigest()


def git(*args, cwd=ROOT):
    return subprocess.check_output(['git', *args], cwd=cwd, env=ENV)


def read_json(path):
    return json.loads(path.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def identity(path):
    data = path.read_bytes()
    return {'sha256': digest(data), 'bytes': len(data)}


def expand(data, getter):
    return re.sub(rb'^\\input\{chapters/([^{}\n]+\.tex)\}\n',
                  lambda m: expand(getter('book/chapters/'+m[1].decode()), getter), data, flags=re.M)


def protected_files(approved, source=None):
    """Compare every protected baseline blob, including materialized LFS bytes."""
    entries = []
    for row in git('ls-tree', '-r', '-z', BASELINE).split(b'\0'):
        if row:
            fields, raw_path = row.split(b'\t', 1)
            mode, kind, oid = fields.split()
            require(kind == b'blob', 'baseline contains a non-blob entry')
            entries.append((mode, oid, raw_path.decode()))
    require(len(entries) == 1851, 'baseline tracked count must be 1851')
    modified = {p for _, _, p in entries if p in approved}
    require(len(modified) == 8 and len(set(approved)-modified) == 4, 'source must modify 8 and add 4 paths')
    rows = [row for row in entries if row[2] not in modified]
    proc = subprocess.run(['git', 'cat-file', '--batch'], cwd=ROOT, env=ENV,
                          input=b'\n'.join(row[1] for row in rows)+b'\n', capture_output=True, check=True)
    require(not proc.stderr, 'cat-file reported stderr')
    offset, lfs_count = 0, 0
    for mode, oid, path in rows:
        end = proc.stdout.index(b'\n', offset)
        found, kind, length = proc.stdout[offset:end].split()
        require(found == oid and kind == b'blob', 'cat-file response identity')
        start, size = end+1, int(length)
        blob = proc.stdout[start:start+size]
        require(proc.stdout[start+size:start+size+1] == b'\n', 'cat-file framing')
        offset = start+size+1
        current = os.readlink(ROOT/path).encode() if mode == b'120000' else (ROOT/path).read_bytes()
        if blob.startswith(b'version https://git-lfs.github.com/spec/v1\n'):
            match = re.fullmatch(rb'version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n', blob)
            require(match is not None, 'unrecognized LFS pointer: '+path)
            require(digest(current) == match[1].decode() and len(current) == int(match[2]), 'materialized LFS mismatch: '+path)
            lfs_count += 1
        else:
            require(current == blob, 'protected baseline bytes changed: '+path)
    require(offset == len(proc.stdout), 'unexpected trailing cat-file bytes')
    require(len(rows) == 1843 and lfs_count == 412, 'protected/LFS counts must be 1843/412')
    # Commit-level paths/modes are checked as well as materialized bytes.
    if source:
        changes = git('diff', '--name-status', BASELINE, source).decode().splitlines()
        actual = {row.split('\t')[1]: row.split('\t')[0] for row in changes}
        expected = {name: 'M' for name in modified} | {name: 'A' for name in set(approved)-modified}
        require(actual == expected, 'source commit changes or modes differ from declared paths')
        baseline_modes = {path: mode for mode, _, path in entries}
        source_modes = {}
        for row in git('ls-tree', '-r', '-z', source).split(b'\0'):
            if row:
                fields, path = row.split(b'\t', 1)
                source_modes[path.decode()] = fields.split()[0]
        require(len(source_modes) == 1855, 'source tracked-tree count')
        require(all(source_modes[name] == baseline_modes[name] for name in baseline_modes),
                'source commit changed a baseline file mode')
        require(all(source_modes[name] == b'100644' for name in set(approved)-modified),
                'new source files must be regular non-executable blobs')
    return {'baseline_tracked_files': len(entries), 'protected_baseline_files': len(rows),
            'materialized_lfs_files': lfs_count}


def original_files(source):
    inventory = read_json(ROOT.parent/'audit/2026-10-31/source-inventory.json')
    count = 0
    for repository in inventory['repositories']:
        directory = ROOT.parent/repository['path']
        require(git('rev-parse', 'HEAD', cwd=directory).decode().strip() == repository['head'], 'original HEAD changed')
        require(not git('status', '--porcelain', '--untracked-files=all', cwd=directory), 'original repository is dirty')
        subprocess.run(['git', 'merge-base', '--is-ancestor', repository['head'], source], cwd=ROOT, env=ENV, check=True)
        for item in repository['files']:
            data = (directory/item['path']).read_bytes()
            require(digest(data) == item['sha256'] and len(data) == item['bytes'], 'original file changed: '+item['path'])
            count += 1
    require(count == 953, 'original source count must be 953')
    archive = inventory['monograph_archive']
    data = (ROOT.parent/archive['path']).read_bytes()
    require(digest(data) == archive['sha256'] and len(data) == archive['bytes'], 'original ZIP changed')
    reference = ROOT/'book/reference/polyhedral_volumes_and_geodesic_identities.pdf'
    require(digest(reference.read_bytes()) == '40dd069bd2653f9a78666a31f53910d74b7f8de2a4a75d5a5dd62466032a6cd5', 'supplied reference PDF changed')
    return count


def approved_sources():
    author = read_json(CHECKPOINT/'math-author/integrated-author-manifest.json')
    code = read_json(CHECKPOINT/'computation-review/approved-hashes.json')
    integration = read_json(CHECKPOINT/'integration-review/approved-source-manifest.json')
    approved = author['owned_final_sha256'] | code['approved_code_sha256']
    require(len(author['owned_final_sha256']) == 8 and len(code['approved_code_sha256']) == 4 and len(approved) == 12,
            'approval source counts must be 8 + 4')
    require(integration['approved_source_sha256'] == approved, 'integration source approval mismatch')
    require(integration['baseline_commit'] == code['baseline_commit'] == BASELINE, 'approval baseline mismatch')
    require(integration['decision'] == 'approved_with_explicit_scope_limits', 'integration decision')
    require(code['decision'] == 'approved_for_corrected_source_and_bounded_finite_numerical_evidence', 'code decision')
    require(integration['source_commit_approval'] is True and integration['approved_source_count'] == 12
            and integration['modified_baseline_paths'] == 8 and integration['new_source_paths'] == 4,
            'integration approval count/scope')
    for row in integration['independent_approvals'].values():
        for key in ('manifest', 'report'):
            require(digest((CHECKPOINT/'integration-review'/row[key]).read_bytes()) == row[key+'_sha256'],
                    'integration predecessor evidence identity')
    for name, expected in integration['review_records_sha256'].items():
        require(digest((CHECKPOINT/'integration-review'/name).read_bytes()) == expected, 'integration evidence identity: '+name)
    for name, expected in code['review_and_evidence_sha256'].items():
        require(digest((CHECKPOINT/'computation-review'/name).read_bytes()) == expected, 'code evidence identity: '+name)
    math = read_json(CHECKPOINT/'math-review/approved-hashes.json')
    require(math['decision'] == 'approved_with_stated_scope' and math['baseline_commit'] == BASELINE, 'analytic approval')
    for name, expected in math['evidence_sha256'].items():
        require(digest((CHECKPOINT/'math-review'/name).read_bytes()) == expected, 'analytic evidence identity: '+name)
    delta = read_json(CHECKPOINT/'integration-review/numeric-delta-review.json')
    require(delta['analytic_approval_manifest_sha256'] == digest((CHECKPOINT/'math-review/approved-hashes.json').read_bytes()), 'analytic delta predecessor')
    require(delta['approved_analytic_sha256'] == math['approved_sha256'], 'analytic approved hash chain')
    require(delta['reviewed_final_sha256'] == {p: approved[p] for p in (CHAPTER, LEDGER)}, 'numeric delta final hashes')
    require(delta['chapter_delta_confined_to_numerical_subsection'] is True
            and delta['analytic_prefix_and_interpretation_suffix_byte_identical'] is True
            and delta['ledger_old_analytic_proofs_statuses_and_source_pins_preserved'] is True,
            'numerical integration changed approved analytic material')
    require(delta['ledger_claim_count'] == 14 and delta['full_v1_sha256'] == FULL_V1, 'delta input/count')
    return approved, code, integration


def scientific_result(source, approved, code):
    result = read_json(ROOT/RESULT)
    prior_path = CHECKPOINT/'computation/full-v1.json'
    require(digest(prior_path.read_bytes()) == FULL_V1, 'exploratory full-v1 identity')
    prior = read_json(prior_path)
    require(prior['source_at_start'] == prior['source_at_finish'], 'historical full-v1 source drift')
    require(prior['source_at_start']['commit'] == BASELINE, 'full-v1 historical commit')
    require(result['status'] == prior['status'] == 'all_declared_checks_passed'
            and result['profile'] == prior['profile'] == 'full', 'full-run status')
    require(len(result['rows']) == len(prior['rows']) == 21, '21 quantum quadratures required')
    old_rows, new_rows = copy.deepcopy(prior['rows']), copy.deepcopy(result['rows'])
    for rows in (old_rows, new_rows):
        for row in rows:
            del row['elapsed_seconds']
    require(old_rows == new_rows, 'scientific row mismatch excluding only actual timing')
    require(len(result['comparisons']) == 7 and result['comparisons'] == prior['comparisons'], 'seven exact comparison objects')
    old_sets = {x['working_dps']: x for x in prior['independent_double_sine_checks']}
    new_sets = {x['working_dps']: x for x in result['independent_double_sine_checks']}
    require(len(old_sets) == len(new_sets) == 2 and set(old_sets) == set(new_sets) == {40, 60}, 'component-check precision sets')
    added_name = 'D_alternate_method_and_panels_argument_3'
    for dps in (40, 60):
        old, new = old_sets[dps], new_sets[dps]
        require(old['evidence_status'] == new['evidence_status'], 'component evidence status')
        old_named = {r['name']: r for r in old['records']}
        new_named = {r['name']: r for r in new['records']}
        require(len(old_named) == len(old['records']) == 27 and len(new_named) == len(new['records']) == 28,
                'component counts or names')
        require(set(new_named) == set(old_named) | {added_name}, 'unexpected added/removed component check')
        require(all(new_named[name] == row for name, row in old_named.items()), 'shared component record differs')
        extra = new_named[added_name]
        detail = extra['details']
        with localcontext() as context:
            context.prec = 110
            threshold, residual, error = (Decimal(extra['threshold']), Decimal(extra['absolute_residual']),
                                          Decimal(detail['quadrature_error_estimate']))
            require(all(x.is_finite() for x in (threshold, residual, error)) and
                    0 <= residual < threshold and 0 <= error < threshold, 'new direct-D check does not pass')
            real_z = Decimal(detail['z']['real'])
            require(min(real_z, 1-real_z) > Decimal(1)/50, 'new check numerical strip margin')
        require(detail['method'] == 'tanh-sinh' and detail['integration_domain'] == ['0', 'infinity'], 'new method/domain')
        require(detail['panels'] == [0, '1/2']+[2**k for k in range(15)]+['infinity'], 'new direct-D panel layout')
        require(detail['tail_cutoff'] == 8192 and detail['tail_strip_epsilon_exact'] == '1/50', 'new tail parameters')
        require('not an omitted-tail error' in detail['tail_bound_role'], 'tail role must describe included tail')
        require(Fraction(detail['direct_D_tail_bound_exact']) == Fraction(1, 80)**2/(6*Fraction(1, 50)*2**327), 'exact rational direct-D tail bound')
    old_conventions, new_conventions = dict(prior['conventions']), dict(result['conventions'])
    new_direct_convention = new_conventions.pop('direct_D_quadrature')
    require(old_conventions == new_conventions, 'previous conventions changed')
    for key in ('schema_version', 'runtime', 'sources', 'limitations'):
        require(prior[key] == result[key], 'unexpected result metadata change: '+key)
    runtime = dict(code['approved_code_sha256'])
    for path in ('experiments/section15/historical-table.json',
                 'book/chapters/14-normalized-quantum-comparison.tex', CHAPTER):
        runtime[path] = code['review_context_sha256'][path]
    require(len(runtime) == 7, 'seven scientific sources required')
    require(result['source_at_start'] == result['source_at_finish'], 'clean replay source/HEAD drift')
    for key in ('source_at_start', 'source_at_finish'):
        state = result[key]
        require(state['commit'] == source and state['dirty_status'] == '', 'replay must start/finish at clean source commit')
        require(state['sha256'] == runtime, 'run source hash set differs from final approval')
        for path, expected in state['sha256'].items():
            require(digest(git('show', source+':'+path)) == expected == digest((ROOT/path).read_bytes()), 'runtime source identity: '+path)
    comparison = read_json(CHECKPOINT/'clean-source/scientific-comparison.json')
    require(comparison['status'] == 'clean_full_run_scientific_comparison_passed'
            and comparison['candidate_commit'] == source and comparison['candidate_sources_clean_and_stable'] is True,
            'strict comparison receipt status')
    require(comparison['input_sha256'] == {
        'baseline': FULL_V1, 'candidate': digest((ROOT/RESULT).read_bytes()),
        'approval': digest((CHECKPOINT/'computation-review/approved-hashes.json').read_bytes())}, 'comparison input identities')
    require(comparison['comparison_script_sha256'] == digest((CHECKPOINT/'computation-review/compare_full_runs.py').read_bytes()), 'comparison script identity')
    require(comparison['excluded_scientific_JSON_paths'] == ['rows[*].elapsed_seconds', 'independent_double_sine_checks[*].elapsed_seconds'], 'comparison exclusion scope')
    require(comparison['identical_scientific_rows'] == 21 and comparison['identical_comparisons'] == 7,
            'comparison record counts')
    require(comparison['shared_component_checks'] == [{'dps': 40, 'identical_named_records': 27}, {'dps': 60, 'identical_named_records': 27}], 'shared check counts')
    require(comparison['added_component_checks_validated_separately'] == [
        next(r for r in new_sets[dps]['records'] if r['name'] == added_name) for dps in (40, 60)], 'new component records')
    require(comparison['expected_metadata_changes']['conventions.direct_D_quadrature'] == new_direct_convention, 'direct-D convention receipt')
    command = read_json(CHECKPOINT/'clean-source/run-command.json')
    require(command['returncode'] == 0 and command['clean_before'] is True and command['clean_after'] is True,
            'clean full run command did not complete successfully')
    require(command['source_commit'] == source and command['source_before'] == result['source_at_start']
            and command['source_after'] == result['source_at_finish'], 'run command/source state mismatch')
    require(command['result'] == identity(ROOT/RESULT), 'run command result identity')
    return {'quantum_quadratures': 21, 'precision_contour_comparisons': 7,
            'shared_component_checks_per_precision': 27, 'new_component_checks_per_precision': 1,
            'component_precisions': [40, 60], 'runtime_source_hashes_verified': len(runtime),
            'clean_source_states_verified': 2, 'fresh_clean_source_result': True}


def manuscript():
    old = expand(git('show', BASELINE+':'+MAIN), lambda p: git('show', BASELINE+':'+p))
    current = expand((ROOT/MAIN).read_bytes(), lambda p: (ROOT/p).read_bytes())
    labels = re.findall(rb'\\label\{([^{}]+)\}', current)
    require(labels == re.findall(rb'\\label\{([^{}]+)\}', old), 'all book labels/order must be preserved')
    require(len(labels) == len(set(labels)) == 607, '607 unique manuscript labels required')
    chapter_labels = re.findall(rb'\\label\{([^{}]+)\}', (ROOT/CHAPTER).read_bytes())
    require(chapter_labels == re.findall(rb'\\label\{([^{}]+)\}', git('show', BASELINE+':'+CHAPTER))
            and len(chapter_labels) == 21, '21 Section 15 labels/order required')
    bib = re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', current)
    require(bib == re.findall(rb'\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}', old)
            and len(bib) == len(set(bib)) == 129, '129 bibliography keys/order required')
    claims = read_json(ROOT/LEDGER)['claims']
    require(len(claims) == len({c['id'] for c in claims}) == 14, '14 unique claim groups required')
    require({label for c in claims for label in c['labels']} == {x.decode() for x in chapter_labels}, 'ledger must cover all and only Section 15 labels')
    return {'labels_preserved': len(labels), 'section15_labels': len(chapter_labels),
            'bibliography_keys_preserved': len(bib), 'section15_claims': len(claims)}


def local_links(approved):
    docs = {ROOT/p for p in approved if p.endswith('.md')}
    docs.update(CHECKPOINT.rglob('*.md'))
    count = 0
    for path in docs:
        if path.name.startswith('._'):
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
            parsed = urlsplit(target.strip('<>'))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            require((path.parent/unquote(parsed.path)).resolve().exists(), 'missing local link: '+str(path)+' -> '+target)
            count += 1
    return count


def ledger_local_paths():
    paths = set()

    def visit(value):
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and re.fullmatch(r'(?:book|docs|experiments|artifacts)/[^\s]+', value):
            paths.add(value)

    visit(read_json(ROOT/LEDGER))
    for name in paths:
        require((ROOT/name).exists(), 'ledger path is missing: '+name)
    return len(paths)


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', action='store_true')
    parser.add_argument('--receipt', type=Path, help='new receipt under the outer execution directory')
    args = parser.parse_args()
    require(git('rev-parse', '--show-toplevel').decode().strip() == str(ROOT), 'unexpected Git root')
    require(not git('remote'), 'this local checkpoint must have no remotes')
    manifest = read_json(ROOT/MANIFEST)
    approved, code, integration = approved_sources()
    checkpoint = read_json(CHECKPOINT/'checkpoint/source-checkpoint.json')
    source = checkpoint['source_commit']
    require(checkpoint['baseline_commit'] == manifest['baseline_commit'] == BASELINE, 'checkpoint baseline')
    require(manifest['source_commit'] == source and checkpoint['approved_source_sha256'] == approved, 'source checkpoint identity')
    require(checkpoint['index_clean'] is True and checkpoint['worktree_clean'] is True
            and checkpoint['no_remotes'] is True and checkpoint['tracked_files'] == 1855, 'source checkpoint clean counts')
    require(git('rev-list', '--parents', '-n', '1', source).decode().split() == [source, BASELINE], 'source must have baseline as sole parent')
    stage = read_json(CHECKPOINT/'checkpoint/source-stage.json')
    require(set(stage['staged_paths']) == set(approved) and stage['staged_source_sha256'] == approved,
            'staged source allowlist/bytes')
    require(stage['diff_check_passed'] is True and stage['whitespace_exceptions'] == [], 'source whitespace gate')
    for name, row in checkpoint['source_approvals'].items():
        require(identity(CHECKPOINT/name) == row == stage['source_approvals'][name], 'source approval receipt identity: '+name)
    source_integrity = read_json(CHECKPOINT/'checkpoint/source-integrity.json')
    require(source_integrity['source_commit'] == source and source_integrity['returncode'] == 0
            and source_integrity['stderr'] == '' and source_integrity['source_status_porcelain'] == ''
            and source_integrity['tracked_files'] == 1855 and source_integrity['no_remotes'] is True,
            'source Git integrity receipt')
    require(set(source_integrity['stdout'].splitlines()) == {
        'dangling blob dba78d2f1770521c3cfaef91091f1c296ec57abd',
        'dangling blob 4c37b26b85df0662fbc6ab71661713083ac3a7c1'}, 'source fsck must contain only known harmless dangling blobs')
    head = git('rev-parse', 'HEAD').decode().strip()
    for name, expected in approved.items():
        require(digest((ROOT/name).read_bytes()) == digest(git('show', source+':'+name))
                == digest(git('show', head+':'+name)) == expected, 'approved source bytes: '+name)
    artifact_paths = set(manifest['files']) | {MANIFEST}
    require(MANIFEST not in manifest['files'], 'artifact manifest cannot contain its own hash')
    require(all(not any(part.startswith('._') for part in Path(p).parts) for p in artifact_paths), 'sidecar in artifact manifest')
    actual = {str(p.relative_to(ROOT)) for p in CHECKPOINT.rglob('*') if p.is_file() and not p.name.startswith('._')}
    actual.update({RESULT, PDF})
    require(actual == artifact_paths, 'artifact inventory differs from declared paths')
    require(not git('diff', '--cached', '--name-only'), 'index must be empty')
    if args.candidate:
        require(head == source and not git('diff', '--name-only'), 'candidate must be over clean source commit')
        require(set(git('ls-files', '--others', '--exclude-standard').decode().splitlines()) == artifact_paths,
                'candidate untracked paths differ from artifact allowlist')
    else:
        require(git('rev-list', '--parents', '-n', '1', head).decode().split() == [head, source],
                'artifact commit must have source as its sole parent')
        require(not git('status', '--porcelain=v1', '--untracked-files=all'), 'final index/worktree must be clean')
        require(set(git('diff-tree', '--no-commit-id', '--name-only', '-r', head).decode().splitlines()) == artifact_paths,
                'artifact commit paths differ from allowlist')
        require(all(row.startswith('A\t') for row in git('diff', '--name-status', source, head).decode().splitlines()),
                'artifact commit may only add declared files')
        for name in artifact_paths:
            require(git('ls-tree', head, '--', name).split()[0] == b'100644', 'artifact must be a regular non-executable blob: '+name)
    for name, row in manifest['files'].items():
        require(identity(ROOT/name) == row, 'candidate artifact identity: '+name)
        if not args.candidate:
            require(git('show', head+':'+name) == (ROOT/name).read_bytes(), 'committed artifact bytes: '+name)
    if not args.candidate:
        require(git('show', head+':'+MANIFEST) == (ROOT/MANIFEST).read_bytes(), 'committed manifest bytes')
    copies = read_json(CHECKPOINT/'evidence-copy-manifest.json')
    require(copies['source_commit'] == source, 'copy manifest source commit')
    require(len({row['path'] for row in copies['files']}) == len(copies['files']), 'duplicate copied evidence path')
    for row in copies['files']:
        current, original = CHECKPOINT/row['path'], OUT/row['outer_source']
        require(identity(current) == {'sha256': row['sha256'], 'bytes': row['bytes']}, 'copied evidence identity')
        require(current.read_bytes() == original.read_bytes(), 'copied evidence differs from outer original')
    require(set(copies['artifacts']) == {RESULT, PDF}, 'exactly two artifact copies required')
    for name, row in copies['artifacts'].items():
        require(identity(ROOT/name) == {'sha256': row['sha256'], 'bytes': row['bytes']}, 'artifact copy identity')
        require((ROOT/name).read_bytes() == (OUT/row['outer_source']).read_bytes(), 'artifact bytes differ from reviewed outer source')
    science = scientific_result(source, approved, code)
    pdf_inputs = read_json(CHECKPOINT/'integration-review/pdf-inputs.json')['sha256']
    require(len(pdf_inputs) == 18, '18 active TeX inputs required')
    for path, expected in pdf_inputs.items():
        require(digest((ROOT/path).read_bytes()) == digest(git('show', source+':'+path)) == expected, 'PDF input/source identity: '+path)
    at_source = read_json(CHECKPOINT/'clean-source/pdf-inputs-at-source.json')
    require(at_source['source_commit'] == source and at_source['sha256'] == pdf_inputs
            and at_source['all_match_committed_source'] is True, 'post-source-commit PDF input check')
    visual = read_json(CHECKPOINT/'integration-review/visual-review.json')
    pdf_identity = identity(ROOT/PDF)
    require(visual['pdf_sha256'] == pdf_identity['sha256'] and visual['new_visual_defects'] == []
            and visual['decision'] == 'passed_for_stated_visual_scope', 'reviewed PDF identity or findings')
    require(visual['inspected_page_count'] == len(visual['inspected_pages'])
            and len(set(visual['inspected_pages'])) == len(visual['inspected_pages']), 'visual page scope count')
    require(integration['pdf']['sha256'] == pdf_identity['sha256'] and integration['pdf']['input_sha256'] == pdf_inputs,
            'integrated PDF approval identity/inputs')
    require(integration['pdf']['pages'] == visual['pdf_pages'] == 187
            and integration['pdf']['active_input_files'] == 18
            and integration['pdf']['compiled_labels'] == 607 and integration['pdf']['compiled_citations'] == 129,
            'integrated PDF counts')
    require(integration['pdf']['visually_inspected_pages'] == visual['inspected_pages']
            and visual['inspected_page_count'] == 23, 'integrated visual scope')
    build = read_json(CHECKPOINT/'integration-review/pdf-build-review.json')
    require(build['pdf_sha256'] == pdf_identity['sha256'] and build['input_sha256'] == pdf_inputs
            and build['actual_recorded_manuscript_inputs_match_frozen_graph'] is True
            and build['actual_recorded_manuscript_input_count'] == 18,
            'actual PDF build input identity')
    require(build['undefined_or_duplicate_labels'] == [] and build['overfull_boxes'] == []
            and build['compiled_labels'] == 607 and build['compiled_citations'] == 129,
            'PDF reference convergence')
    require(build['selected_pages'] == visual['inspected_pages'], 'built/rendered/reviewed page scope')
    for row in visual['images']:
        require(row['finding'] == 'pass' and build['rendered_sha256'][row['path']] == row['sha256'],
                'reviewed image identity/scope')
    require([row['page'] for row in visual['images']] == visual['inspected_pages'], 'actual inspected-image set')
    for key in ('build_command_receipt', 'marker_receipt'):
        require(digest((CHECKPOINT/'integration-review'/build[key]).read_bytes()) == build[key+'_sha256'],
                'build command/marker receipt identity')
    preservation = protected_files(approved, source)
    originals = original_files(source)
    labels = manuscript()
    links = local_links(approved)
    ledger_paths = ledger_local_paths()
    fsck = subprocess.run(['git', 'fsck', '--full'], cwd=ROOT, env=ENV, capture_output=True, text=True)
    require(fsck.returncode == 0 and not fsck.stderr, 'Git fsck failed: '+fsck.stdout+fsck.stderr)
    report = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'mode': 'candidate' if args.candidate else 'postcommit', 'checks_passed': True,
        'baseline_commit': BASELINE, 'source_commit': source, 'head': head,
        'source_paths_verified': len(approved), 'artifact_paths_verified': len(artifact_paths),
        'copied_evidence_files_verified': len(copies['files']),
        'candidate_manifest_sha256': digest((ROOT/MANIFEST).read_bytes()),
        'result_sha256': digest((ROOT/RESULT).read_bytes()), 'pdf_sha256': pdf_identity['sha256'],
        'pdf_input_hashes_verified': len(pdf_inputs), 'pdf_pages': integration['pdf']['pages'],
        'visually_reviewed_pages': visual['inspected_page_count'],
        **science, **preservation, **labels, 'original_files': originals,
        'local_links_checked': links, 'ledger_local_paths_checked': ledger_paths,
        'index_clean': True, 'worktree_clean': not args.candidate,
        'no_remotes': True, 'git_fsck_returncode': fsck.returncode,
        'git_fsck_stdout': fsck.stdout, 'git_fsck_stderr': fsck.stderr,
        'git_metadata_cleanup_by_this_verifier': False,
        'scope': 'Identity, clean-run provenance, finite result equality, preservation and local links. No new numerical replay, PDF build, visual inspection, browser check or publication.'
    }
    receipt = args.receipt or OUT/('candidate-verification.json' if args.candidate else 'final-postcommit-verification.json')
    require(receipt.resolve().is_relative_to(OUT.resolve()), 'receipt must be under outer execution directory')
    if args.receipt is None and receipt.exists():
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = receipt.with_name(receipt.stem+'-'+stamp+receipt.suffix)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    with receipt.open('x') as handle:
        handle.write(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({key: report[key] for key in ('mode', 'checks_passed', 'head',
        'source_paths_verified', 'artifact_paths_verified', 'local_links_checked')}, indent=2))
    print('Receipt: '+str(receipt))


if __name__ == '__main__':
    main()
