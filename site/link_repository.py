"""Add public repository navigation to an accepted edition without recomputation.

Copyright 2026 Igor Rivin. SPDX-License-Identifier: MIT.
See LICENSES/new-companions-MIT.txt for the full license text.
"""
import argparse
import json
import re
import shutil
import subprocess
from collections import Counter
from hashlib import sha256
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = ('experiments/', 'artifacts/', 'packages/', 'book/claims/', 'docs/execution/')


def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True).strip()


def digest(data):
    return sha256(data).hexdigest()


def files(root):
    result = {}
    for p in root.rglob('*'):
        name = p.relative_to(root).as_posix()
        if any(part.startswith('._') for part in p.relative_to(root).parts):
            continue
        if p.is_symlink():
            raise ValueError('Symlink in edition: ' + name)
        if p.is_file():
            result[name] = p
    return result


class Paths(HTMLParser):
    def __init__(self):
        super().__init__()
        self.code = None
        self.paths = []

    def handle_starttag(self, tag, attrs):
        if tag == 'code':
            self.code = ''

    def handle_data(self, data):
        if self.code is not None:
            self.code += data

    def handle_endtag(self, tag):
        if tag == 'code' and self.code is not None:
            if self.code.startswith(PREFIXES):
                self.paths.append(self.code)
            self.code = None


def target(config, commit, path):
    if path.startswith('/') or '..' in Path(path).parts:
        raise ValueError('Unsafe repository path: ' + path)
    name = path.rstrip('/')
    kind = git('cat-file', '-t', commit + ':' + name)
    if kind not in ('tree', 'blob'):
        raise ValueError('Unsupported Git object: ' + path)
    return config['repository_url'] + '/' + ('tree' if kind == 'tree' else 'blob') + '/' + commit + '/' + quote(name, safe='/')


def companion_guide(config, commit):
    body = '<section id="reproduce"><h2>Find and run a computation</h2>'
    body += '<p>Use the <a href="' + config['repository_url'] + '">public companion repository</a> for the complete source, inputs and recorded results. '
    body += 'The links below are pinned to this edition\'s repository commit. Install the core toolkit in a Python 3.10-3.14 environment, then run commands from the repository root.</p>'
    body += '<p><a href="' + target(config, commit, 'README.md') + '">Clone and installation instructions</a> · '
    body += '<a href="' + target(config, commit, 'experiments/README.md') + '">Complete reproduction guide</a> · '
    body += '<a href="' + config['repository_url'] + '/releases/download/' + config['release_tag'] + '/polyhedra-source.zip">Download source and data ZIP</a></p>'
    body += '<p>Choose new output names outside the checkout. These example commands do not replace the committed results. The quantum smoke run and cutoff-64 torus run are smaller than their published campaigns.</p><pre><code>mkdir -p /tmp/polyhedra-run</code></pre>'
    for row in config['companions']:
        body += '<section class="evidence-group" id="run-' + row['id'] + '"><h3>' + escape(row['title']) + '</h3><p>'
        body += ' · '.join('<a href="' + name + '">Read Section ' + str(int(name[:2])) + '</a>' for name in row['chapters'])
        body += '</p><p>'
        entries = [('Recipe', row['recipe']), ('Source', row['entrypoint']), ('Recorded result', row['result'])]
        entries += [('Input ' + str(i + 1), name) for i, name in enumerate(row['inputs'])]
        body += ' · '.join('<a href="' + target(config, commit, name) + '">' + label + '</a>' for label, name in entries)
        body += '</p><pre><code>' + escape(row['command']) + '</code></pre>'
        body += '<p class="evidence-limit">' + escape(row['limit']) + '</p></section>'
    return body + '</section>'


def pdf_path_locations(doc, targets):
    """Find body paths across lines and pages, retaining every glyph location.

    The canonical book has two running headings and a numeric page footer.
    Remove only those recognized margin lines, never intervening body prose.
    """
    headings = {'Polyhedra,Moduli,andQuantumGeometry', 'Researchmonograph',
                'Polyhedra,Moduli,andQuantumGeometryResearchmonograph'}
    chars = []
    for page in doc:
        for bi, block in enumerate(page.get_text('rawdict')['blocks']):
            for li, line in enumerate(block.get('lines', [])):
                glyphs = [char for span in line['spans'] for char in span['chars']]
                text = ''.join(char['c'] for char in glyphs if not char['c'].isspace())
                if text in headings and line['bbox'][3] < 60:
                    continue
                if text == str(page.number + 1) and line['bbox'][1] > page.rect.height - 60:
                    continue
                chars.extend((char['c'], char['bbox'], (page.number, bi, li))
                             for char in glyphs if not char['c'].isspace())
    text = ''.join(char[0] for char in chars)
    occupied, found = set(), []
    for name in sorted(targets, key=len, reverse=True):
        for match in re.finditer(re.escape(name), text):
            positions = set(range(match.start(), match.end()))
            if occupied & positions:
                continue
            occupied.update(positions)
            found.append((name, chars[match.start():match.end()]))
    return found


def link_pdf(source, output, targets, repository_url):
    import pymupdf

    doc = pymupdf.open(source)
    original_toc = doc.get_toc(simple=False)
    original_links = [page.get_links() for page in doc]
    records = []
    counts = Counter()
    for name, chars in pdf_path_locations(doc, targets):
        rectangles = {}
        for _, bbox, line in chars:
            rect = pymupdf.Rect(bbox)
            rectangles[line] = rectangles[line] | rect if line in rectangles else rect
        segments = []
        for (page_number, _, _), rect in rectangles.items():
            doc[page_number].insert_link({'kind': pymupdf.LINK_URI, 'from': rect, 'uri': targets[name]})
            segments.append({'page': page_number + 1, 'rectangle': list(rect)})
        counts[name] += 1
        records.append({'page': segments[0]['page'], 'path': name, 'uri': targets[name],
                        'rectangles': [s['rectangle'] for s in segments], 'segments': segments})
    missing = set(targets) - set(counts)
    if missing:
        raise ValueError('Computational paths not located in PDF: ' + repr(sorted(missing)))
    footer = pymupdf.Rect(103, 733, 493, 767)
    page = doc[0]
    if any(pymupdf.Rect(b[:4]).intersects(footer) for b in page.get_text('blocks')):
        raise ValueError('Repository footer overlaps original title-page content')
    line = 'Code, inputs and results: github.com/igorrivin/polyhedra'
    page.insert_text((104, 746), line, fontsize=9, fontname='helv', color=(0.1, 0.23, 0.32))
    page.insert_text((104, 761), 'Computational paths in this PDF link to the published source edition.', fontsize=8, fontname='helv', color=(0.3, 0.3, 0.3))
    page.insert_link({'kind': pymupdf.LINK_URI, 'from': footer, 'uri': repository_url})
    doc.save(output, deflate=True)
    doc.close()
    original, linked = pymupdf.open(source), pymupdf.open(output)
    if len(original) != len(linked) or original_toc != linked.get_toc(simple=False):
        raise ValueError('PDF pagination or outline changed')
    def signature(link):
        return {k: v for k, v in link.items() if k not in ('xref', 'id')}
    for i, (before, after) in enumerate(zip(original, linked)):
        current = [signature(link) for link in after.get_links()]
        if any(signature(link) not in current for link in original_links[i]):
            raise ValueError('Existing PDF link changed on page ' + str(i + 1))
        if i:
            if before.get_text() != after.get_text() or before.get_pixmap().samples != after.get_pixmap().samples:
                raise ValueError('Original PDF content changed on page ' + str(i + 1))
        else:
            if not after.get_text().startswith(before.get_text()):
                raise ValueError('Original title-page text changed')
            for clip in (pymupdf.Rect(0, 0, before.rect.width, 732), pymupdf.Rect(0, 768, before.rect.width, before.rect.height)):
                if before.get_pixmap(clip=clip).samples != after.get_pixmap(clip=clip).samples:
                    raise ValueError('Title-page pixels changed outside repository footer')
    return {'pages': len(linked), 'path_occurrences': sum(counts.values()), 'unique_paths': len(counts),
            'existing_links_preserved': sum(map(len, original_links)), 'path_links': records,
            'source_sha256': digest(Path(source).read_bytes()), 'linked_sha256': digest(Path(output).read_bytes()),
            'render_comparison': f'All {len(linked)} pages compared: unchanged pixels outside the added title-page footer; existing text, links and outline preserved.'}


def build(source, output, ref, allow_dirty=False):
    source, output = source.resolve(), output.resolve()
    if output.exists() or output.is_relative_to(ROOT) or output.is_relative_to(source):
        raise ValueError('Output must be a new directory outside the research checkout and source')
    dirty = bool(git('status', '--porcelain'))
    if dirty and not allow_dirty:
        raise ValueError('Commit the publication source before building the final edition')
    commit = git('rev-parse', '--verify', ref + '^{commit}')
    config = json.loads((ROOT / 'site/book/repository.json').read_text())
    inputs = files(source)
    local_manifest = json.loads((source / 'downloads/edition-manifest.json').read_text())
    expected = local_manifest['output_sha256']
    if set(inputs) != set(expected) | {'downloads/edition-manifest.json'}:
        raise ValueError('Source edition inventory differs from its original manifest')
    for name, sha in expected.items():
        if digest(inputs[name].read_bytes()) != sha:
            raise ValueError('Source edition hash differs: ' + name)
    occurrences = []
    for name, path in inputs.items():
        if '/' not in name and name.endswith('.html'):
            scan = Paths(); scan.feed(path.read_text())
            occurrences.extend((name, value) for value in scan.paths)
    targets = {name: target(config, commit, name) for _, name in occurrences}
    replacements = {
        'Local working edition': 'Web working edition',
        'local working edition': 'web working edition',
        'This local edition': 'This web edition',
        'This is local preparation; no upload or deployment is performed.': 'This web edition is paired with its public computational repository.',
        '<a href="downloads/edition-manifest.json">Edition manifest</a>': '<a href="downloads/edition-manifest.json">Original edition manifest</a> · <a href="downloads/repository-link-manifest.json">Repository-link manifest</a>',
    }
    output.mkdir(parents=True)
    linked_count = 0
    changed = {}
    for name, path in inputs.items():
        data = path.read_bytes()
        before = data
        if '/' not in name and name.endswith('.html'):
            text = data.decode()
            for old, new in replacements.items():
                text = text.replace(old, new)
            def replace(match):
                nonlocal linked_count
                name = unescape(match[1])
                if name not in targets:
                    return match[0]
                linked_count += 1
                return '<a class="repository-path" href="' + targets[name] + '">' + match[0] + '</a>'
            text = re.sub(r'<code>([^<>]+)</code>', replace, text)
            text = text.replace('<a href="downloads/monograph.pdf">PDF</a>', '<a href="downloads/monograph.pdf">PDF</a><a href="' + config['repository_url'] + '">Repository</a>')
            if name == 'index.html':
                text = text.replace('<a href="downloads/monograph.pdf">Download the complete PDF</a>', '<a href="downloads/monograph.pdf">Download the complete PDF</a><a href="' + config['repository_url'] + '">Code and data on GitHub</a>')
            if name == 'computations.html':
                text = text.replace('<section class="evidence-group"', companion_guide(config, commit) + '<section class="evidence-group"', 1)
            text = text.replace('</footer>', '<p><a href="downloads/monograph-original.pdf">Original accepted PDF</a> · <a href="' + config['repository_url'] + '/releases/download/' + config['release_tag'] + '/polyhedra-source.zip">Complete source and data ZIP</a></p></footer>')
            data = text.encode()
        dest = output / name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
        if before != data:
            changed[name] = {'before': digest(before), 'after': digest(data)}
    if linked_count != len(occurrences):
        raise ValueError('Not all repository path occurrences were linked')
    css = output / 'assets/edition.css'
    css.write_text(css.read_text() + '\n#reproduce pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:1rem;background:#f5f5f2}\n')
    shutil.copyfile(source / 'downloads/monograph.pdf', output / 'downloads/monograph-original.pdf')
    pdf = link_pdf(source / 'downloads/monograph.pdf', output / 'downloads/monograph.pdf', targets, config['repository_url'])
    if Counter(row['path'] for row in pdf['path_links']) != Counter(name for _, name in occurrences):
        raise ValueError('PDF and HTML computational path occurrence counts differ')
    (output / 'downloads/repository-pdf-links.json').write_text(json.dumps(pdf, indent=2) + '\n')
    manifest = {'schema_version': 1, 'operation': 'polyhedra-repository-links-v1', 'repository_url': config['repository_url'],
                'repository_commit': commit, 'release_tag': config['release_tag'], 'source_dirty': dirty,
                'scientific_base_commit': config['scientific_base_commit'], 'scientific_replay': 'not performed',
                'scope': 'Public navigation, portable recipes and exact-commit source links; original mathematical text, fixtures and scientific results preserved. PDF annotations and title-page repository footer are publication additions.',
                'original_manifest_sha256': digest((source / 'downloads/edition-manifest.json').read_bytes()),
                'path_occurrences': linked_count, 'path_targets': targets, 'changed_html': changed,
                'pdf': {k: v for k, v in pdf.items() if k != 'path_links'},
                'output_sha256': {name: digest(path.read_bytes()) for name, path in sorted(files(output).items())}}
    (output / 'downloads/repository-link-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('repository_commit', 'path_occurrences', 'source_dirty', 'pdf')}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ref', default='HEAD')
    parser.add_argument('--allow-dirty', action='store_true', help='Author preview only; recorded in the manifest')
    args = parser.parse_args()
    build(args.source, args.output, args.ref, args.allow_dirty)
