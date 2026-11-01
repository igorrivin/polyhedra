"""Verify exact identities after rendering, independently of numerical execution."""
import importlib.util
import json
from hashlib import sha256
from pathlib import Path
import zipfile

root = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
outer = root.parent / 'execution/section9-chapter-2026-10-31'
run = Path('/tmp/polyhedra-section9-build-v3')
site = run / 'site/section9'
detached = Path('/tmp/polyhedra-section9-detached-v3/section9-reproduction')
spec = importlib.util.spec_from_file_location('section9_builder', root / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
hashfile = lambda path: sha256(path.read_bytes()).hexdigest()
report_bytes = (run / 'result.json').read_bytes()
report = json.loads(report_bytes)
build = json.loads((site / 'downloads/chapter-build.json').read_text())
replay = json.loads((detached / 'artifacts/section9/result.json').read_text())
assert report['all_checks_passed'] and replay['all_checks_passed']
assert {k:v for k,v in report.items() if k != 'provenance'} == {k:v for k,v in replay.items() if k != 'provenance'}
assert replay['provenance']['execution_context'] == 'detached-bundle'
assert replay['provenance']['source_commit'] is None
assert replay['provenance']['repository_dirty_at_start'] is None
assert replay['provenance']['bundle_origin'] == report['provenance']
assert replay['provenance']['bundle_payload_hashes_match']
assert all(not row['available'] for row in replay['provenance']['source_files'] if row['role'].startswith('book.'))
builder.validate_companion(site, report_bytes, report)
for path, expected in build['inputs'].items():
    assert hashfile(root / path) == expected, path
for path, expected in build['output_sha256'].items():
    assert hashfile(site / path) == expected, path
assert build['computation_result']['sha256'] == hashfile(run / 'result.json')
assert (site / 'downloads/result.json').read_bytes() == report_bytes
assert not build['pending_evidence']
assert build['repository_dirty_at_start'] is True
assert build['validation']['chapter_overfull_hbox_count'] == 0
chapter_validation = builder.validate_html((site/'chapter.html').read_text(), site,
    list(build['chapter_label_map']) + list(build['external_reference_only_labels']),
    build['validation']['mathml_count'], 2)
companion_validation = builder.validate_html((site/'index.html').read_text(),site,[],0,0)
with zipfile.ZipFile(site / 'downloads/monograph-source.zip') as z:
    prefix='monograph-source/'
    manifest=json.loads(z.read(prefix+'source-manifest.json'))
    for path, expected in manifest['payload_sha256'].items():
        assert sha256(z.read(prefix+path)).hexdigest() == expected
    for path, expected in manifest['input_sha256'].items():
        assert expected == hashfile(root/path)
result = {'scope':'strict preliminary preview after render-only refresh; sources are dirty, not final release',
    'numerical_run_all_checks_passed':True,'detached_replay_all_checks_passed':True,
    'detached_report_except_provenance_identical':True,'detached_optional_book_assets_absent':True,
    'rendered_companion_matches_explicit_result':True,'result_bytes_preserved_by_render_only':True,
    'chapter_input_hashes_match_current_sources':True,'chapter_output_hashes_match_after_render_only':True,
    'source_archive_payload_and_current_input_hashes_match':True,
    'chapter_html':chapter_validation,'companion_html':companion_validation,
    'source_commit':build['source_commit'],'source_dirty':True,
    'implementation_sha256':{str(p.relative_to(root)):hashfile(p) for p in [
        root/'site/build_section9.py',root/'site/section9.css',root/'site/README.md',
        root/'site/tests/test_build_section9.py',root/'experiments/section9/run.py',
        root/'experiments/section9/README.md',root/'experiments/section9/tests/test_rendering.py']},
    'artifact_sha256':{str(p.relative_to(run)):hashfile(p) for p in sorted(run.glob('site/section9/**/*')) if p.is_file()},
    'result_sha256':hashfile(run/'result.json'),
    'detached_result_sha256':hashfile(detached/'artifacts/section9/result.json')}
(outer/'strict-preview-checks.json').write_text(json.dumps(result,indent=2)+'\n')
(outer/'strict-preview-artifact-manifest.json').write_text(json.dumps({'scope':result['scope'],
    'result_sha256':result['result_sha256'],'artifact_sha256':result['artifact_sha256']},indent=2)+'\n')
(outer/'strict-preview-build-manifest.json').write_bytes((site/'downloads/chapter-build.json').read_bytes())
print(json.dumps({k:v for k,v in result.items() if k not in ('artifact_sha256','chapter_html','companion_html')},indent=2))
