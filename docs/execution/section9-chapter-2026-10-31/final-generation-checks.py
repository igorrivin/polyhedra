"""Checkpoint evidence, with deliberately pinned local paths; not a portable entry point."""
from pathlib import Path
from hashlib import sha256
import importlib.util
import json
import subprocess
import zipfile

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUTER = ROOT.parent / 'execution/section9-chapter-2026-10-31'
BUILD = Path('/tmp/polyhedra-section9-final-20261031')
SITE = BUILD / 'site/section9'
DETACHED = Path('/tmp/polyhedra-section9-final-detached-20261031/section9-reproduction')
SOURCE = '1bafb83d2ec152f1f8eac75b2be0e3c4b796198e'

def digest(path):
    return sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (OUTER / name).write_text(json.dumps(value, indent=2) + '\n')

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == SOURCE
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
source_review = json.loads((OUTER / 'source-preflight.json').read_text())
for name, expected in source_review['sha256'].items():
    assert digest(ROOT / name) == expected, name
spec = importlib.util.spec_from_file_location('section9_builder_final_checks', ROOT / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
report_bytes = (BUILD / 'result.json').read_bytes()
report = json.loads(report_bytes)
replay = json.loads((DETACHED / 'artifacts/section9/result.json').read_bytes())
build = json.loads((SITE / 'downloads/chapter-build.json').read_bytes())
assert report['all_checks_passed'] and len(report['checks']) == 12
assert replay['all_checks_passed'] and len(replay['checks']) == 12
assert report['exact_fixture']['checks_passed']
assert report['exact_fixture']['det_negative_volume_hessian'] == '60'
assert report['exact_fixture']['rooted_forest_weight_sum'] == '15'
assert report['exact_fixture']['effective_K_entry'] == '15/2'
assert {k: v for k, v in report.items() if k != 'provenance'} == {k: v for k, v in replay.items() if k != 'provenance'}
for provenance in (report['provenance'], build):
    assert provenance['source_commit'] == SOURCE
    assert provenance['repository_dirty_at_start'] is False
assert not build['pending_evidence'] and not build['preliminary']
assert build['full_monograph_label_count'] == 607
assert len(build['chapter_label_map']) == 26
assert len(build['external_reference_only_labels']) == 2
assert len(build['numbered_equations']) == 17
assert len(build['citation_map']) == 12
for key, expected in [('mathml_count', 209), ('figure_count', 2), ('pdf_pages', 10), ('pdf_pages_rendered', 10),
                      ('full_monograph_overfull_hbox_count', 0), ('chapter_overfull_hbox_count', 0)]:
    assert build['validation'][key] == expected, key
for path, expected in build['inputs'].items():
    assert digest(ROOT / path) == expected, path
for path, expected in build['output_sha256'].items():
    assert digest(SITE / path) == expected, path
assert build['computation_result']['sha256'] == digest(BUILD / 'result.json')
assert build['computation_result']['provenance'] == report['provenance']
assert (SITE / 'downloads/result.json').read_bytes() == report_bytes
builder.validate_companion(SITE, report_bytes, report)
chapter_html = builder.validate_html((SITE / 'chapter.html').read_text(), SITE,
    list(build['chapter_label_map']) + list(build['external_reference_only_labels']), 209, 2)
companion_html = builder.validate_html((SITE / 'index.html').read_text(), SITE, [], 0, 0)
assert replay['provenance']['execution_context'] == 'detached-bundle'
assert replay['provenance']['source_commit'] is None
assert replay['provenance']['repository_dirty_at_start'] is None
assert replay['provenance']['bundle_origin'] == report['provenance']
assert replay['provenance']['bundle_payload_hashes_match']
assert not replay['provenance']['bundle_payload_mismatches']
assert all(not row['available'] for row in replay['provenance']['source_files'] if row['role'].startswith('book.'))
archive_checks = {}
for filename, prefix, manifest_name, hash_key in [
    ('section9-reproduction.zip', 'section9-reproduction/', 'section9-bundle.json', 'payload_sha256'),
    ('monograph-source.zip', 'monograph-source/', 'source-manifest.json', 'payload_sha256')]:
    with zipfile.ZipFile(SITE / 'downloads' / filename) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        manifest = json.loads(archive.read(prefix + manifest_name))
        assert set(archive.namelist()) == {prefix + name for name in manifest[hash_key]} | {prefix + manifest_name}
        for name, expected in manifest[hash_key].items():
            assert sha256(archive.read(prefix + name)).hexdigest() == expected, name
        origin = manifest.get('origin_provenance', manifest)
        assert origin['source_commit'] == SOURCE and origin['repository_dirty_at_start'] is False
        archive_checks[filename] = {'sha256': digest(SITE / 'downloads' / filename), 'verified_payloads': len(manifest[hash_key]), 'clean_source_origin': True}
        if filename == 'monograph-source.zip':
            for name, expected in manifest['input_sha256'].items():
                assert digest(ROOT / name) == expected, name
            with zipfile.ZipFile('/tmp/polyhedra-section9-build-v3/site/section9/downloads/monograph-source.zip') as previous:
                previous_manifest = json.loads(previous.read(prefix + manifest_name))
                assert manifest['payload_sha256'] == previous_manifest['payload_sha256']
                for name in manifest['payload_sha256']:
                    assert archive.read(prefix + name) == previous.read(prefix + name), name
            archive_checks[filename]['all_seven_source_payloads_identical_to_independently_built_v3'] = True
            archive_checks[filename]['fresh_extracted_source_build_claimed'] = False
pages = {p.name: digest(p) for p in sorted((BUILD / 'chapter-build/rendered-pages').glob('page-*.png'))}
assert len(pages) == 10
comparisons = {}
for version in ('v2', 'v3'):
    previous = Path('/tmp/polyhedra-section9-build-' + version) / 'chapter-build/rendered-pages'
    same = pages == {p.name: digest(p) for p in sorted(previous.glob('page-*.png'))}
    assert same
    comparisons[version] = same
visual = {'scope': 'Final generated PDF page pixels compared with the complete v2 visual review and independently verified v3 renders.',
          'chapter_pdf_sha256': digest(SITE / 'downloads/section9.pdf'), 'pages': 10,
          'rendered_page_sha256': pages, 'matches_prior_page_hashes': comparisons,
          'basis': 'Root visually inspected every v2 page; identical keyed final page PNG bytes preserve that approved layout.',
          'not_claimed': 'This is rendered-page identity verification, not a new browser review or identical PDF metadata.'}
write('final-visual-comparison.json', visual)
artifacts = {'artifacts/section9/result.json': digest(BUILD / 'result.json')}
for path in sorted(SITE.rglob('*')):
    if path.is_file():
        assert not any(part.startswith('._') for part in path.relative_to(SITE).parts)
        artifacts['site/section9/' + str(path.relative_to(SITE))] = digest(path)
write('final-artifact-manifest.json', {'source_commit': SOURCE, 'source_clean_at_generation': True,
      'scope': 'Final complete export after render-only refresh, before canonical copy.', 'sha256': artifacts})
result = {'status': 'final_clean_source_generation_and_replay_passed', 'source_commit': SOURCE,
          'source_clean_before_and_after_generation': True, 'all_83_reviewed_source_hashes_match': True,
          'numerical_checks_passed': 12, 'exact_fixture_checks_passed': True, 'fresh_detached_replay_passed': True,
          'detached_mathematical_fields_identical': True, 'detached_source_and_git_availability_honest': True,
          'detached_bundle_origin_preserved': True, 'source_report_sha256': digest(BUILD / 'result.json'),
          'detached_report_sha256': digest(DETACHED / 'artifacts/section9/result.json'),
          'render_only_preserved_original_result_bytes': True, 'chapter_inputs_match_current_sources': True,
          'chapter_outputs_match_after_render_only': True, 'full_monograph_labels': 607, 'chapter_labels': 26,
          'external_reference_only_labels': 2, 'numbered_displays': 17, 'selected_citations': 12,
          'mathml_nodes': 209, 'figures': 2, 'pdf_pages': 10, 'overfull_boxes': 0,
          'chapter_static_html': chapter_html, 'companion_static_html': companion_html,
          'archives': archive_checks, 'all_page_renders_match_visually_reviewed_preview': True,
          'verification_script_sha256': digest(Path(__file__)),
          'static_pdf_html_probe_sha256': digest(OUTER / 'build-review-artifact-checks.py'),
          'static_artifact_checks_sha256': digest(OUTER / 'final-artifact-static-checks.json'),
          'browser_review': 'Not performed; no browser/server policy workaround attempted.',
          'full_test_suite': 'Not rerun; 25 focused tests were independently passed before the source commit.',
          'source_archive_build_scope': 'Fresh full and standalone builds performed by publisher; final ZIP payloads equal v3 payloads independently extracted and compiled earlier.'}
write('final-generation-checks.json', result)
(OUTER / 'final-build-manifest.json').write_bytes((SITE / 'downloads/chapter-build.json').read_bytes())
(OUTER / 'final-detached-result.json').write_bytes((DETACHED / 'artifacts/section9/result.json').read_bytes())
assert not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT)
print(json.dumps({key: result[key] for key in ('status', 'source_commit', 'numerical_checks_passed', 'fresh_detached_replay_passed', 'mathml_nodes', 'pdf_pages')}, indent=2))
