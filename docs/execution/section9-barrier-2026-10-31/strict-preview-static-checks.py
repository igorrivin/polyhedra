"""Identity and static-link checks after both render-only refreshes; no numerical replay."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

root = Path(sys.argv[1] if len(sys.argv) > 1 else Path.cwd()).resolve()
outer = Path(__file__).resolve().parent
location = json.loads((outer / 'strict-preview-location.json').read_text())
run, site = Path(location['preview_root']), Path(location['site_dir'])
spec = importlib.util.spec_from_file_location('chapter_builder', root / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
hashfile = lambda p: sha256(p.read_bytes()).hexdigest()
manifest = json.loads((site / 'downloads/chapter-build.json').read_text())
reports = {name: json.loads((run / name).read_text()) for name in ('result.json', 'barrier-result.json')}
assert all(report['all_checks_passed'] is True for report in reports.values())
builder.validate_companion(site, (run / 'result.json').read_bytes(), reports['result.json'])
builder.validate_barrier_companion(root, site, run / 'barrier-result.json', required=True)
for name, expected in manifest['inputs'].items():
    assert hashfile(root / name) == expected, name
for name, expected in manifest['output_sha256'].items():
    assert hashfile(site / name) == expected, name
for key, name in [('computation_result', 'result.json'), ('barrier_computation_result', 'barrier-result.json')]:
    assert manifest[key]['sha256'] == hashfile(run / name)
    assert (site / 'downloads' / name).read_bytes() == (run / name).read_bytes()
assert manifest['preliminary'] and manifest['repository_dirty_at_start']
assert manifest['pending_evidence'] == []
assert manifest['validation']['chapter_overfull_hbox_count'] == 0
assert manifest['validation']['full_monograph_overfull_hbox_count'] == 0
html_checks = {}
for name, labels, math, figures in [
    ('chapter.html', list(manifest['chapter_label_map']) + list(manifest['external_reference_only_labels']), 209, 2),
    ('index.html', [], 0, 0), ('barrier.html', [], 0, 0)]:
    html_checks[name] = builder.validate_html((site / name).read_text(), site, labels, math, figures)
    if name != 'chapter.html':
        assert 'href="chapter.html"' in (site / name).read_text()
zip_checks = {}
for filename, prefix, manifest_name in [
    ('section9-reproduction.zip', 'section9-reproduction/', 'section9-bundle.json'),
    ('barrier-reproduction.zip', 'barrier-reproduction/', 'barrier-bundle.json'),
    ('monograph-source.zip', 'monograph-source/', 'source-manifest.json')]:
    with zipfile.ZipFile(site / 'downloads' / filename) as archive:
        bundle = json.loads(archive.read(prefix + manifest_name))
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert set(names) == {prefix + name for name in bundle['payload_sha256']} | {prefix + manifest_name}
        for name, expected in bundle['payload_sha256'].items():
            assert sha256(archive.read(prefix + name)).hexdigest() == expected, name
        if filename == 'monograph-source.zip':
            for name, expected in bundle['input_sha256'].items():
                assert expected == hashfile(root / name), name
        zip_checks[filename] = {'payload_count': len(bundle['payload_sha256']), 'all_payload_hashes_match': True}
changed = [name for name, expected in manifest['barrier_computation_result']['asset_sha256'].items()
           if hashfile(site / name) != expected]
assert changed == ['barrier.html'], changed
result = {'scope': 'Strict evidence-complete dirty-source preview after render-only backlinks; final clean-source generation pending',
          'preview_root': str(run), 'source_commit': manifest['source_commit'],
          'all_checks_passed': True, 'chapter_inputs_match_live_source': True,
          'chapter_output_hashes_match': True, 'both_explicit_reports_match_exports': True,
          'barrier_build_input_hash_scope': manifest['barrier_computation_result']['asset_hash_scope'],
          'barrier_assets_changed_by_backlink_refresh': changed,
          'html_checks': html_checks, 'zip_checks': zip_checks,
          'report_sha256': {name: hashfile(run / name) for name in reports},
          'final_preview_asset_sha256': {str(p.relative_to(site)): hashfile(p)
              for p in sorted(site.rglob('*')) if p.is_file() and not p.name.startswith('._')}}
(outer / 'strict-preview-static-checks.json').write_text(json.dumps(result, indent=2) + '\n')
(outer / 'strict-preview-build-manifest.json').write_bytes((site / 'downloads/chapter-build.json').read_bytes())
print(json.dumps({k: v for k, v in result.items() if k not in ('html_checks', 'final_preview_asset_sha256')}, indent=2))
