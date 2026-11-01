"""Independent checks of a completed Section 9 preview, without a browser.

The PDF parser is a review dependency only. This is an evidence probe, not the
maintained publishing pipeline, and it does not claim a mathematical proof.
"""
import argparse
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import re
import shutil
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

from pypdf import PdfReader


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


class HTMLInventory(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.math = [], [], [], 0
        self.unexpected = []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'math':
            self.math += 1
        if tag in ('a', 'link', 'img', 'script'):
            target = attrs.get('href') or attrs.get('src')
            if target:
                self.links.append((tag, target))
        if tag == 'img':
            assert attrs.get('alt') and int(attrs['width']) > 0 and int(attrs['height']) > 0
            self.images.append(attrs)
        if tag in ('merror', 'script'):
            self.unexpected.append(tag)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--site', type=Path, required=True)
    parser.add_argument('--previous-rendered', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root, site = args.root.resolve(), args.site.resolve()
    manifest = json.loads((site / 'downloads/chapter-build.json').read_bytes())
    assert not manifest['pending_evidence']
    for name, expected in manifest['output_sha256'].items():
        assert digest(site / name) == expected, name
    for name, expected in manifest['inputs'].items():
        assert digest(root / name) == expected, name
    result_bytes = (site / 'downloads/result.json').read_bytes()
    assert sha256(result_bytes).hexdigest() == manifest['computation_result']['sha256']
    report = json.loads(result_bytes)
    assert report['all_checks_passed']

    html = (site / 'chapter.html').read_text()
    inventory = HTMLInventory()
    inventory.feed(html)
    assert not inventory.unexpected
    assert all(count == 1 for count in Counter(inventory.ids).values())
    expected_labels = set(manifest['chapter_label_map']) | set(manifest['external_reference_only_labels'])
    assert expected_labels <= set(inventory.ids)
    assert len(manifest['chapter_label_map']) == 26
    for tag, target in inventory.links:
        url = urlsplit(target)
        if url.scheme:
            assert tag == 'a', (tag, target)
        elif url.path:
            path = (site / unquote(url.path)).resolve()
            assert path.is_relative_to(site) and path.is_file(), target
        else:
            assert unquote(url.fragment) in inventory.ids, target
    assert len(inventory.images) == 2
    chapter = (root / 'book/chapters/09-volume-hessians.tex').read_text()
    chapter = re.sub(r'(?<!\\)%[^\n]*', '', chapter)
    chapter = re.sub(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', '', chapter, flags=re.S)
    dollar_count = len(re.findall(r'(?<!\\)\$', chapter))
    assert dollar_count % 2 == 0
    chapter_math = dollar_count // 2 + len(re.findall(r'\\\[', chapter)) + len(re.findall(r'\\begin\{(?:equation|align)\*?\}', chapter))
    assert chapter_math == 206
    assert inventory.math == chapter_math + 2 + 1 == 209
    for equation in manifest['numbered_equations']:
        pattern = 'id="' + re.escape(equation['label']) + r'".*?<span class="equation-number">\(' + re.escape(equation['number']) + r'\)</span>'
        assert re.search(pattern, html, re.S), equation
    assert 'Their hypotheses and proofs are outside the Section 9 review' in html
    assert '<a href="downloads/section9-reproduction.zip">site/section9/downloads/section9-reproduction.zip ' in html

    source_archive = site / 'downloads/monograph-source.zip'
    with zipfile.ZipFile(source_archive) as archive:
        assert len(archive.namelist()) == len(set(archive.namelist()))
        source_manifest = json.loads(archive.read('monograph-source/source-manifest.json'))
        for name, expected in source_manifest['payload_sha256'].items():
            assert sha256(archive.read('monograph-source/' + name)).hexdigest() == expected
        for name, expected in source_manifest['input_sha256'].items():
            assert digest(root / name) == expected

    pdf_path = site / 'downloads/section9.pdf'
    pdf = PdfReader(pdf_path)
    assert len(pdf.pages) == manifest['validation']['pdf_pages'] == 10
    local_links, external_links, internal_links = [], [], []
    named = pdf.named_destinations
    for page_number, page in enumerate(pdf.pages, 1):
        for reference in page.get('/Annots', []):
            action = reference.get_object().get('/A')
            if not action:
                continue
            kind = str(action.get('/S'))
            if kind == '/GoTo':
                dest = action.get('/D')
                if isinstance(dest, str):
                    assert dest in named, dest
                internal_links.append({'page': page_number, 'target': str(dest)})
            elif kind in ('/URI', '/GoToR'):
                target = str(action.get('/URI') or action.get('/F'))
                if urlsplit(target).scheme:
                    external_links.append(target)
                else:
                    path = (pdf_path.parent / unquote(target)).resolve()
                    assert path.is_relative_to(site) and path.is_file(), target
                    local_links.append({'page': page_number, 'target': target})
            else:
                raise AssertionError(('unexpected PDF action', kind))

    spec = importlib.util.spec_from_file_location('review_builder', root / 'site/build_section9.py')
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.validate_companion(site, result_bytes, report)
    with tempfile.TemporaryDirectory(prefix='section9-review-tamper-') as name:
        target = Path(name)
        (target / 'downloads').mkdir()
        for relative in ('index.html', 'downloads/result.json', 'downloads/fixture.json'):
            shutil.copyfile(site / relative, target / relative)
        with zipfile.ZipFile(site / 'downloads/section9-reproduction.zip') as original, \
                zipfile.ZipFile(target / 'downloads/section9-reproduction.zip', 'w') as changed:
            for item in original.infolist():
                data = original.read(item.filename)
                if item.filename.endswith('/geometry.py'):
                    data += b'\n# review-only tamper\n'
                changed.writestr(item, data)
        try:
            builder.validate_companion(target, result_bytes, report)
        except builder.BuildError as error:
            assert 'payload hash mismatch' in str(error), error
            tamper_message = str(error)
        else:
            raise AssertionError('changed numerical ZIP was accepted')

    rendered = Path(manifest['rendered_pages'])
    page_hashes = {path.name: digest(path) for path in sorted(rendered.glob('page-*.png'))}
    assert len(page_hashes) == 10
    previous_equal = None
    if args.previous_rendered:
        previous_equal = page_hashes == {path.name: digest(path) for path in sorted(args.previous_rendered.glob('page-*.png'))}
        assert previous_equal
    output = {
        'status': 'independent_static_artifact_checks_passed',
        'site': str(site), 'chapter_builder_sha256': digest(root / 'site/build_section9.py'),
        'chapter_html_sha256': digest(site / 'chapter.html'), 'chapter_pdf_sha256': digest(pdf_path),
        'source_archive_sha256': digest(source_archive),
        'numerical_result_sha256': sha256(result_bytes).hexdigest(),
        'chapter_labels': 26, 'external_reference_only_labels': 2,
        'math_count_from_canonical_delimiters_without_tikz': chapter_math,
        'mathml_total_with_reference_excerpts_and_bibliography': inventory.math,
        'images': inventory.images, 'source_archive_payloads_verified': len(source_manifest['payload_sha256']),
        'all_local_html_targets_exist': True, 'pdf_pages': len(pdf.pages),
        'local_pdf_links': local_links, 'external_pdf_link_count': len(external_links),
        'internal_pdf_link_count': len(internal_links), 'all_internal_pdf_named_targets_exist': True,
        'modified_numerical_zip_rejected': tamper_message,
        'rendered_page_sha256': page_hashes, 'matches_previous_rendered_pages': previous_equal,
        'browser_review': 'Not performed; static checks do not verify browser layout or interactions.',
        'proof_scope': 'This is software/artifact verification, not a mathematical proof audit.',
    }
    args.output.write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps({key: output[key] for key in ('status', 'chapter_pdf_sha256', 'pdf_pages', 'matches_previous_rendered_pages')}, indent=2))


if __name__ == '__main__':
    main()
