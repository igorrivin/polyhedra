#!/usr/bin/env python3
"""Build the complete Section 9 excerpt from canonical LaTeX, offline.

Python standard library only; external tools: latexmk, pdflatex, pandoc,
and Ghostscript. See site/README.md for the reviewed build sequence.
This is a deliberately strict chapter converter, not a general TeX interpreter.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from urllib.parse import unquote, urlsplit
import zipfile

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path('book/polyhedral_volumes_and_geodesic_identities.tex')
CHAPTER = Path('book/chapters/09-volume-hessians.tex')
LEDGER = Path('book/claims/section9.json')
EXTERNAL_LABELS = ('eq:cuspHessian', 'eq:cuspmatrixHessian')
BARRIER_SOURCES = {
    'experiment.driver': 'experiments/section9/barrier_run.py',
    'experiment.template': 'experiments/section9/barrier-page.html',
    'experiment.fixture': 'experiments/section9/barrier-fixtures.json',
    'toolkit.angle_barrier': 'packages/volume-toolkit/ideal_poly_volume_toolkit/angle_barrier.py',
    'toolkit.variational': 'packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py',
    'toolkit.geometry': 'packages/volume-toolkit/ideal_poly_volume_toolkit/geometry.py',
}
BARRIER_ASSETS = ('barrier.html', 'downloads/barrier-result.json',
                  'downloads/barrier-fixtures.json', 'downloads/barrier-reproduction.zip')
LABEL_RE = re.compile(r'\\label\{([^{}]+)\}')
ENVIRONMENTS = {'equation', 'equation*', 'align', 'align*', 'aligned',
                'proposition', 'proof', 'figure', 'pmatrix', 'bmatrix',
                'matrix', 'cases', 'itemize', 'enumerate'}


class BuildError(ValueError):
    """A source, conversion or publication integrity gate failed."""


def digest(data):
    return sha256(data).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def uncomment(text):
    return re.sub(r'(?<!\\)%[^\n]*', '', text)


def group(text, pos):
    """Read a balanced TeX group, preserving nested braces and escaped braces."""
    while pos < len(text) and text[pos].isspace():
        pos += 1
    if pos >= len(text) or text[pos] != '{':
        raise BuildError(f'expected balanced TeX group near {text[pos:pos+60]!r}')
    start, depth = pos + 1, 1
    pos += 1
    while pos < len(text):
        if text[pos] == '\\':
            pos += 2
            continue
        depth += (text[pos] == '{') - (text[pos] == '}')
        if not depth:
            return text[start:pos], pos + 1
        pos += 1
    raise BuildError('unclosed TeX group')


def source_graph(root, entry=Path('book/main.tex')):
    """Snapshot literal local TeX includes; never follow paths outside book/."""
    root = root.resolve()
    book = (root / 'book').resolve()
    payload, active = {}, []

    def visit(path):
        path = path.resolve()
        if not path.is_relative_to(book):
            raise BuildError(f'external source path is forbidden: {path}')
        if path in active:
            raise BuildError(f'cyclic TeX include: {path}')
        if path in payload:
            return
        if not path.is_file():
            raise BuildError(f'missing TeX input: {path}')
        active.append(path)
        data = path.read_bytes()
        payload[path] = data
        text = uncomment(data.decode('utf-8'))
        if re.search(r'\\(?:includegraphics|bibliography|addbibresource|lstinputlisting|verbatiminput)\b', text):
            raise BuildError(f'unsupported external asset command in {path}; add explicit graph support first')
        for match in re.finditer(r'\\(?:input|include)\b', text):
            name, _ = group(text, match.end())
            if not name or re.search(r'[\\#$~]', name) or Path(name).is_absolute():
                raise BuildError(f'nonliteral/external TeX input in {path}: {name}')
            child = Path(name)
            if child.suffix != '.tex':
                child = child.with_suffix('.tex')
            # All builds run from book/. Match TeX's input resolution explicitly.
            visit(book / child)
        active.pop()

    visit(root / entry)
    return {str(path.relative_to(root)): data for path, data in payload.items()}


def aux_maps(text):
    labels, citations = {}, {}
    for line in text.splitlines():
        if line.startswith(r'\newlabel{'):
            label, pos = group(line, len(r'\newlabel'))
            content, _ = group(line, pos)
            number, pos = group(content, 0)
            # amsmath stores an explicit \tag inside one harmless brace group.
            if number.startswith('{'):
                unwrapped, end = group(number, 0)
                if end == len(number):
                    number = unwrapped
            page, pos = group(content, pos)
            title, pos = group(content, pos)
            anchor, _ = group(content, pos)
            row = {'number': number, 'page': page, 'title': title, 'anchor': anchor}
            if label in labels:
                raise BuildError(f'duplicate compiled label: {label}')
            labels[label] = row
        elif line.startswith(r'\bibcite{'):
            key, pos = group(line, len(r'\bibcite'))
            value, _ = group(line, pos)
            if key in citations:
                raise BuildError(f'duplicate bibliography key: {key}')
            citations[key] = value
    if not labels:
        raise BuildError('compiled auxiliary file has no labels')
    return labels, citations


def bibliography(text):
    match = re.search(r'\\begin\{thebibliography\}\{[^{}]*\}(.*?)\\end\{thebibliography\}', text, re.S)
    if not match:
        raise BuildError('expected the canonical manual bibliography')
    body = match.group(1)
    items = list(re.finditer(r'\\bibitem\{([^{}]+)\}', body))
    result = {}
    for i, item in enumerate(items):
        key = item.group(1)
        if key in result:
            raise BuildError(f'duplicate bibliography item: {key}')
        result[key] = body[item.end():items[i+1].start() if i+1 < len(items) else len(body)].strip()
    return result


def external_equations(text, labels):
    result = []
    for label in EXTERNAL_LABELS:
        matches = [m for m in re.finditer(r'\\begin\{equation\}.*?\\end\{equation\}', text, re.S)
                   if label in LABEL_RE.findall(m.group())]
        if len(matches) != 1 or label not in labels:
            raise BuildError(f'cannot extract external equation {label}')
        equation = matches[0].group().replace(r'\begin{equation}', r'\begin{equation*}').replace(
            r'\end{equation}', r'\end{equation*}')
        equation = equation.replace(r'\label{' + label + '}', r'\tag{' + labels[label]['number'] + r'}\label{' + label + '}')
        result.append(equation)
    return '\n'.join(result)


def run(command, *, cwd, log, stdin=None):
    result = subprocess.run(list(map(str, command)), cwd=cwd, input=stdin,
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text('$ ' + ' '.join(map(str, command)) + '\n' + result.stdout + result.stderr)
    if result.returncode:
        raise BuildError(f'command failed ({result.returncode}); see {log}')
    return result


def tool(name, choices=()):
    value = shutil.which(name)
    if value:
        return value
    for candidate in choices:
        if Path(candidate).is_file():
            return candidate
    raise BuildError(f'required build tool is unavailable: {name}')


def compile_tex(source, outdir, tools, logs, name):
    outdir.mkdir(parents=True, exist_ok=True)
    run([tools['latexmk'], '-norc', '-pdf', '-interaction=nonstopmode', '-halt-on-error',
         '-file-line-error', '-no-shell-escape', f'-outdir={outdir}', source],
        cwd=source.parent, log=logs / f'{name}.log')
    aux = (outdir / (source.stem + '.aux')).read_text()
    latex_log = (outdir / (source.stem + '.log')).read_text(errors='replace')
    fatal = ('There were undefined references', 'There were undefined citations',
             'Label(s) may have changed', 'multiply-defined labels', 'Rerun to get cross-references right')
    if any(value in latex_log for value in fatal):
        raise BuildError(f'LaTeX references did not converge: {name}')
    return outdir / (source.stem + '.pdf'), aux, latex_log


def ast_nodes(value, kind):
    if isinstance(value, dict):
        if value.get('t') == kind:
            yield value
        for child in value.values():
            yield from ast_nodes(child, kind)
    elif isinstance(value, list):
        for child in value:
            yield from ast_nodes(child, kind)


def literal(text):
    return {'t': 'Str', 'c': text}


def inline_text(nodes):
    result = []
    def visit(value):
        if isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, dict):
            if value.get('t') == 'Str':
                result.append(value['c'])
            elif value.get('t') in ('Space', 'SoftBreak', 'LineBreak'):
                result.append(' ')
            elif value.get('t') == 'Math':
                result.append(value['c'][1])
            else:
                visit(value.get('c', []))
    visit(nodes)
    return ''.join(result).strip()


def normalize_math(text):
    """Only presentation syntax changes; canonical proof bytes are untouched."""
    labels = LABEL_RE.findall(text)
    text = LABEL_RE.sub('', text)
    text = re.sub(r'\\tag\{[^{}]+\}', '', text)
    text = re.sub(r'\\(?:begin|end)\{equation\*?\}', '', text)
    text = re.sub(r'\\(begin|end)\{align\*?\}', r'\\\1{aligned}', text)
    text = text.replace(r'\notag', '')
    text = re.sub(r'\{\\rm\s+([A-Za-z]+)\}', r'{\\mathrm{\1}}', text)
    text = text.replace(r'\hbox{', r'\text{')
    return text.strip(), labels


class Converter:
    def __init__(self, labels, citations, link_map):
        self.labels, self.citations, self.link_map = labels, citations, link_map
        self.equations, self.used_citations, self.references = [], set(), set()
        self.section = int(labels.get('sec:ipolybridge', {'number': '9'})['number']) - 1
        self.subsection = 0

    def number(self, label):
        if label not in self.labels:
            raise BuildError(f'unresolved canonical label: {label}')
        return self.labels[label]['number']

    def transform(self, value):
        if isinstance(value, list):
            return [self.transform(x) for x in value]
        if not isinstance(value, dict):
            return value
        kind, content = value.get('t'), value.get('c')
        if kind in ('RawInline', 'RawBlock'):
            raw = content[1].strip()
            if content[0] == 'latex' and kind == 'RawInline':
                match = re.fullmatch(r'\\(eqref|ref|label)\{([^{}]+)\}', raw)
                if match:
                    command, label = match.groups()
                    number = self.number(label)
                    if command == 'label':
                        return {'t': 'Span', 'c': [[label, [], []], []]}
                    self.references.add(label)
                    return {'t': 'Link', 'c': [['', [], []],
                            [literal(f'({number})' if command == 'eqref' else number)], ['#' + label, '']]}
            if content[0] == 'latex' and kind == 'RawBlock' and raw == r'\centering':
                # Figure alignment is supplied by CSS; this command has no prose.
                return {'t': 'Plain', 'c': []}
            raise BuildError(f'unhandled raw {content[0]}: {content[1][:160]}')
        if kind == 'Math':
            normalized, equation_labels = normalize_math(content[1])
            node = {'t': 'Math', 'c': [content[0], normalized]}
            if not equation_labels:
                return node
            if len(equation_labels) != 1:
                raise BuildError('multiple labels in one math node need explicit numbering support')
            label = equation_labels[0]
            number = self.number(label)
            self.equations.append({'label': label, 'number': number})
            return {'t': 'Span', 'c': [[label, ['numbered-equation'], []], [node,
                    {'t': 'Span', 'c': [['', ['equation-number'], []], [literal(f'({number})')]]}]]}
        if kind == 'Cite':
            inlines = [literal('[')]
            for i, citation in enumerate(content[0]):
                key = citation['citationId']
                if key not in self.citations:
                    raise BuildError(f'unresolved bibliography key: {key}')
                self.used_citations.add(key)
                if i:
                    inlines.append(literal('; '))
                inlines += self.transform(citation['citationPrefix'])
                inlines.append({'t': 'Link', 'c': [['', [], []], [literal(self.citations[key])], ['#ref-' + key, '']]})
                if citation['citationSuffix']:
                    inlines.append(literal(', '))
                    inlines += self.transform(citation['citationSuffix'])
            inlines.append(literal(']'))
            return {'t': 'Span', 'c': [['', ['citation'], []], inlines]}
        if kind == 'Link':
            attrs, text, target = content
            properties = dict(attrs[2])
            if 'reference' in properties:
                label = properties['reference']
                self.references.add(label)
                number = self.number(label)
                text = [literal(f'({number})' if properties.get('reference-type') == 'eqref' else number)]
                target = ['#' + label, '']
            elif target[0] in self.link_map:
                target = [self.link_map[target[0]], target[1]]
            elif not target[0].startswith(('#', 'https://', 'http://', 'mailto:')):
                raise BuildError(f'unmapped local chapter link: {target[0]}')
            return {'t': 'Link', 'c': [attrs, self.transform(text), target]}
        if kind == 'Header':
            level, attrs, title = content
            if 'unnumbered' not in attrs[1]:
                if level == 1:
                    self.section += 1
                    self.subsection = 0
                    number = str(self.section)
                elif level == 2:
                    self.subsection += 1
                    number = f'{self.section}.{self.subsection}'
                else:
                    raise BuildError(f'unsupported numbered heading level: {level}')
                if attrs[0] in self.labels and self.number(attrs[0]) != number:
                    raise BuildError(f'heading number disagrees with TeX: {attrs[0]}')
                title = [literal(number + ' ')] + title
            return {'t': kind, 'c': [level, attrs, self.transform(title)]}
        if kind == 'Div' and any(x in content[0][1] for x in ('proposition', 'theorem', 'lemma', 'corollary')):
            label = content[0][0]
            if not label:
                explicit = [node for node in ast_nodes(content[1], 'RawInline')
                            if node['c'][0] == 'latex' and re.fullmatch(r'\\label\{[^{}]+\}', node['c'][1])]
                if len(explicit) != 1:
                    raise BuildError('numbered theorem needs one explicit label')
                label = LABEL_RE.fullmatch(explicit[0]['c'][1]).group(1)
                content[0][0] = label
                explicit[0].clear()
                explicit[0].update({'t': 'Str', 'c': ''})
            number = self.number(label)
            strong = next(ast_nodes(content[1], 'Strong'), None)
            if strong is None or strong['c'][-1].get('t') != 'Str':
                raise BuildError(f'unrecognized theorem heading: {label}')
            strong['c'][-1]['c'] = number
        if kind == 'Figure':
            attrs, caption, body = content
            images = list(ast_nodes(body, 'Image'))
            if len(images) != 1:
                raise BuildError(f'figure does not contain exactly one rendered image: {attrs[0]}')
            alt = inline_text(caption[0] or caption[1])
            if not alt:
                raise BuildError(f'figure alt text is empty: {attrs[0]}')
            images[0]['c'][1] = [literal(alt)]
            number = self.number(attrs[0])
            caption[1][0]['c'] = [literal(f'Figure {number}. ')] + caption[1][0]['c']
        return {key: self.transform(child) for key, child in value.items()}


class HTMLAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links, self.images, self.math = [], [], [], 0
        self.remote_dependencies = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'math':
            self.math += 1
        if tag in ('a', 'img', 'script', 'link'):
            target = attrs.get('href', attrs.get('src', ''))
            if target:
                self.links.append(target)
                if tag != 'a' and urlsplit(target).scheme:
                    self.remote_dependencies.append(target)
        if tag == 'img':
            if not attrs.get('alt'):
                raise BuildError('image without descriptive alt text')
            self.images.append(attrs.get('src'))


def validate_html(html, output_dir, expected_labels, expected_math, expected_figures):
    audit = HTMLAudit()
    audit.feed(html)
    duplicates = [key for key, count in Counter(audit.ids).items() if count != 1]
    if duplicates:
        raise BuildError(f'duplicate HTML anchors: {duplicates}')
    missing = set(expected_labels) - set(audit.ids)
    if missing:
        raise BuildError(f'chapter labels absent from HTML: {sorted(missing)}')
    if audit.math != expected_math or len(audit.images) != expected_figures:
        raise BuildError(f'conversion count differs: {audit.math}/{expected_math} math; {len(audit.images)}/{expected_figures} figures')
    if audit.remote_dependencies:
        raise BuildError(f'offline build has remote dependencies: {audit.remote_dependencies}')
    if 'class="math' in html and '<math' not in html:
        raise BuildError('MathML conversion produced a fallback')
    for target in audit.links:
        url = urlsplit(target)
        if url.scheme:
            continue
        if not url.path:
            if unquote(url.fragment) not in audit.ids:
                raise BuildError(f'broken HTML anchor: {target}')
        else:
            path = (output_dir / unquote(url.path)).resolve()
            if not path.is_relative_to(output_dir.resolve()) or not path.is_file():
                raise BuildError(f'missing or external local HTML asset: {target}')
    return {'mathml_count': audit.math, 'figure_count': len(audit.images),
            'anchors': audit.ids, 'local_links_checked': len(audit.links),
            'browser_review': 'not performed; static checks are not browser verification'}


def ledger_paths(value):
    if isinstance(value, str) and value.startswith(('docs/', 'book/', 'packages/', 'experiments/', 'artifacts/', 'site/')):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from ledger_paths(child)
    elif isinstance(value, list):
        for child in value:
            yield from ledger_paths(child)


def claims_html(ledger, labels, evidence_links=None, pending=()):
    claims = ledger.get('claims')
    if not isinstance(claims, list) or not claims:
        raise BuildError('claim ledger must have a nonempty claims array')
    rows = []
    evidence_links = evidence_links or {}
    def display(value):
        if isinstance(value, list):
            return '<ul>' + ''.join('<li>' + display(child) + '</li>' for child in value) + '</ul>'
        if isinstance(value, dict):
            return '<dl>' + ''.join('<dt>' + escape(key.replace('_', ' ')) + '</dt><dd>' + display(child) + '</dd>'
                                   for key, child in value.items()) + '</dl>'
        value = str(value)
        if value in evidence_links:
            role = ('complete numerical bundle' if value.endswith(('section9-reproduction.zip', 'barrier-reproduction.zip')) else
                    'computation record' if value in ('artifacts/section9/result.json', 'artifacts/section9/barrier-result.json')
                    else 'inspection copy')
            return '<a href="' + escape(evidence_links[value]) + '">' + escape(value) + ' (' + role + ')</a>'
        if value in pending:
            return escape(value) + ' <strong>(pending review evidence; preliminary build)</strong>'
        if value.startswith(('https://', 'http://')):
            return '<a href="' + escape(value, quote=True) + '">' + escape(value) + '</a>'
        return escape(value)
    for claim in claims:
        claim_labels = claim.get('labels', [claim.get('label')])
        if not claim_labels or any(label not in labels for label in claim_labels):
            raise BuildError(f'claim has missing/nonchapter label: {claim.get("id")}')
        for field in ('status', 'hypotheses'):
            if not claim.get(field):
                raise BuildError(f'claim lacks {field}: {claim.get("id")}')
        evidence = claim.get('review_evidence') or claim.get('source_evidence')
        coverage = claim.get('computation') or claim.get('coverage_gap')
        if not evidence or not coverage:
            raise BuildError(f'claim lacks review/source evidence or computation/gap: {claim.get("id")}')
        links = '<br>'.join(f'<a href="#{escape(label)}">{escape(label)}</a>' for label in claim_labels)
        details = {key: claim[key] for key in ('review_evidence', 'source_evidence') if key in claim}
        computation = {key: claim[key] for key in ('computation', 'coverage_gap') if key in claim}
        rows.append(f'<tr><th scope="row">{links}</th><td>{display(claim["status"])}</td>'
                    f'<td>{display(claim["hypotheses"])}</td><td>{display(details)}</td><td>{display(computation)}</td></tr>')
    return ('<section id="claim-ledger"><h2>Claim status and computational coverage</h2>'
            '<p>The ledger distinguishes proof review, conditional results, numerical checks, and remaining gaps. '
            '<a href="downloads/section9-claims.json">Download the complete structured ledger</a>.</p>'
            '<div class="table-scroll"><table><thead><tr><th>Canonical label</th><th>Status</th><th>Hypotheses</th>'
            '<th>Review and sources</th><th>Computation or coverage gap</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></div></section>')


def validate_companion(output_dir, result_bytes, report):
    """The chapter must link the same computation it records, even before refresh."""
    downloads = output_dir / 'downloads'
    for required in (output_dir / 'index.html', downloads / 'result.json',
                     downloads / 'fixture.json', downloads / 'section9-reproduction.zip'):
        if not required.is_file():
            raise BuildError(f'build the numerical companion in the same output directory first: {required}')
    if (downloads / 'result.json').read_bytes() != result_bytes:
        raise BuildError('existing companion result differs from explicit computation result')
    fixture_bytes = (downloads / 'fixture.json').read_bytes()
    if digest(fixture_bytes) != report['provenance']['input_sha256']:
        raise BuildError('existing companion fixture differs from explicit computation input')
    page = (output_dir / 'index.html').read_text()
    prefix = '\nconst data = '
    if page.count(prefix) != 1:
        raise BuildError('cannot identify the companion embedded computation')
    embedded, _ = json.JSONDecoder().raw_decode(page.split(prefix, 1)[1])
    if embedded.get('report') != report or embedded.get('fixture') != json.loads(fixture_bytes):
        raise BuildError('existing companion HTML differs from explicit computation result/input')
    with zipfile.ZipFile(downloads / 'section9-reproduction.zip') as archive:
        prefix = 'section9-reproduction/'
        manifest = json.loads(archive.read(prefix + 'section9-bundle.json'))
        if manifest.get('origin_provenance') != report['provenance']:
            raise BuildError('existing numerical ZIP origin differs from explicit computation')
        for name, expected in manifest['payload_sha256'].items():
            if digest(archive.read(prefix + name)) != expected:
                raise BuildError(f'existing numerical ZIP payload hash mismatch: {name}')
        roles = {'experiment.driver': 'experiments/section9/run.py',
                 'experiment.template': 'experiments/section9/page.html',
                 'experiment.fixture': 'experiments/section9/fixture.json',
                 'toolkit.variational': 'packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py',
                 'toolkit.geometry': 'packages/volume-toolkit/ideal_poly_volume_toolkit/geometry.py'}
        for role, name in roles.items():
            if digest(archive.read(prefix + name)) != report['provenance']['source_sha256'][role]:
                raise BuildError(f'existing numerical ZIP source differs: {role}')


def validate_barrier_companion(root, output_dir, result_path, *, required):
    """Freeze a matching barrier report/export and its actual maintained sources.

    This validates identity and the driver's reported disposition, not the
    mathematical accuracy of a floating-point result. No numerical package is
    imported by the publishing tool.
    """
    if result_path is None:
        if required:
            raise BuildError('the chapter/ledger references the barrier example; supply --barrier-result')
        return None
    root, output_dir, result_path = map(lambda p: Path(p).resolve(), (root, output_dir, result_path))
    if not result_path.is_file():
        raise BuildError(f'missing explicit barrier result: {result_path}')
    result_bytes = result_path.read_bytes()
    try:
        report = json.loads(result_bytes, parse_constant=lambda x: (_ for _ in ()).throw(
            BuildError(f'nonfinite barrier JSON: {x}')))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise BuildError(f'invalid explicit barrier result: {error}') from error
    if (not isinstance(report, dict) or type(report.get('schema_version')) is not int
            or report.get('schema_version') != 1
            or report.get('experiment_id') != 'section9-barrier-fixtures-v1'
            or report.get('all_checks_passed') is not True
            or not isinstance(report.get('cases'), list) or not report['cases']):
        raise BuildError('barrier result must be a passing schema-1 report with cases')
    assets = {}
    for name in BARRIER_ASSETS:
        path = output_dir / name
        if not path.is_file():
            raise BuildError(f'missing barrier companion asset: {name}; run barrier_run.py first')
        assets[name] = path.read_bytes()
    if assets['downloads/barrier-result.json'] != result_bytes:
        raise BuildError('barrier downloaded result differs from explicit report')
    try:
        provenance = report['provenance']
        source_records = {row['role']: row for row in provenance['source_files']}
        if len(source_records) != len(provenance['source_files']):
            raise BuildError('barrier report has duplicate source roles')
        fixture_bytes = assets['downloads/barrier-fixtures.json']
        fixture = json.loads(fixture_bytes)
        if (digest(fixture_bytes) != provenance['input_sha256']
                or fixture.get('id') != report.get('experiment_id')):
            raise BuildError('barrier fixture differs from explicit report/input')
        marker = '\nconst barrierData = '
        page = assets['barrier.html'].decode('utf-8')
        if page.count(marker) != 1:
            raise BuildError('cannot identify the embedded barrier report')
        embedded, _ = json.JSONDecoder().raw_decode(page.split(marker, 1)[1])
        if embedded.get('report') != report or embedded.get('fixture') != fixture:
            raise BuildError('barrier HTML differs from explicit report/input')
        source_bytes = {}
        for role, name in {**BARRIER_SOURCES, 'book.chapter': str(CHAPTER)}.items():
            path = root / name
            if not path.is_file():
                raise BuildError(f'missing maintained barrier input: {name}')
            data = path.read_bytes()
            if provenance['source_sha256'].get(role) != digest(data):
                raise BuildError(f'barrier report source differs from current {role}')
            record = source_records.get(role, {})
            if record.get('available') is not True or record.get('sha256') != digest(data):
                raise BuildError(f'barrier report source record differs: {role}')
            source_bytes[name] = data
        if provenance['source_sha256']['experiment.fixture'] != digest(fixture_bytes):
            raise BuildError('barrier downloaded fixture differs from recorded source')
        with zipfile.ZipFile(BytesIO(assets['downloads/barrier-reproduction.zip'])) as archive:
            prefix, manifest_name = 'barrier-reproduction/', 'barrier-bundle.json'
            manifest = json.loads(archive.read(prefix + manifest_name))
            if manifest.get('origin_provenance') != provenance:
                raise BuildError('barrier ZIP origin differs from explicit report')
            payload = manifest['payload_sha256']
            if not isinstance(payload, dict) or any(Path(name).is_absolute() or '..' in Path(name).parts for name in payload):
                raise BuildError('barrier ZIP has invalid payload paths')
            names = archive.namelist()
            expected = {prefix + name for name in payload} | {prefix + manifest_name}
            if len(names) != len(set(names)) or set(names) != expected:
                raise BuildError('barrier ZIP has duplicate or unmanifested payloads')
            for name, expected_hash in payload.items():
                if digest(archive.read(prefix + name)) != expected_hash:
                    raise BuildError(f'barrier ZIP payload hash mismatch: {name}')
            for role, name in BARRIER_SOURCES.items():
                if digest(archive.read(prefix + name)) != provenance['source_sha256'][role]:
                    raise BuildError(f'barrier ZIP source differs: {role}')
    except (AttributeError, KeyError, TypeError, UnicodeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
        raise BuildError(f'malformed barrier report/export: {error}') from error
    return {'path': result_path, 'result_bytes': result_bytes, 'report': report,
            'assets': assets, 'source_bytes': source_bytes}


def build(root, output_dir, result_path, workdir, *, allow_pending_evidence=False,
          barrier_result_path=None):
    root, output_dir, result_path, workdir = [Path(p).resolve() for p in (root, output_dir, result_path, workdir)]
    if workdir == root or workdir.is_relative_to(root / 'book/chapters'):
        raise BuildError('unsafe build directory')
    workdir.mkdir(parents=True, exist_ok=True)
    logs = workdir / 'logs'
    tools = {name: tool(name, [f'/Library/TeX/texbin/{name}', f'/opt/homebrew/bin/{name}', f'/usr/local/bin/{name}'])
             for name in ('latexmk', 'pandoc', 'gs')}
    versions = {}
    for name, executable in tools.items():
        version = run([executable, '-version' if name == 'latexmk' else '--version'],
                      cwd=root, log=logs / f'{name}-version.log').stdout.strip()
        versions[name] = version if name == 'latexmk' else version.splitlines()[0]
    commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    status = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True).splitlines()
    sources = source_graph(root)
    for path in (str(MAIN), str(CHAPTER)):
        if path not in sources:
            raise BuildError(f'canonical source is absent from graph: {path}')
    extra_inputs = {str(LEDGER): (root / LEDGER).read_bytes(),
                    'site/build_section9.py': Path(__file__).read_bytes(),
                    'site/section9.css': (root / 'site/section9.css').read_bytes()}
    result_bytes = result_path.read_bytes()
    report = json.loads(result_bytes)
    if report.get('schema_version') != 2 or not report.get('all_checks_passed'):
        raise BuildError('computation result must be a passing Section 9 schema-2 report')
    report_sources = report['provenance']['source_sha256']
    for role, path in (('book.tex', MAIN), ('book.chapter', CHAPTER)):
        if report_sources.get(role) != digest(sources[str(path)]):
            raise BuildError(f'computation report does not identify the current {role}')
    canonical = sources[str(MAIN)].decode()
    chapter = sources[str(CHAPTER)].decode()
    ledger = json.loads(extra_inputs[str(LEDGER)])
    evidence_paths = set(ledger_paths(ledger))
    barrier_evidence = {
        BARRIER_SOURCES[role] for role in
        ('experiment.driver', 'experiment.template', 'experiment.fixture', 'toolkit.angle_barrier')
    } | {'artifacts/section9/barrier-result.json', 'site/section9/barrier.html',
         'site/section9/downloads/barrier-reproduction.zip'}
    barrier_required = ('barrier.html' in chapter or 'barrier_run.py' in chapter
                        or bool(evidence_paths & barrier_evidence))
    barrier = validate_barrier_companion(root, output_dir, barrier_result_path, required=barrier_required)
    if barrier is not None and barrier['source_bytes'][str(CHAPTER)] != sources[str(CHAPTER)]:
        raise BuildError('chapter changed between grid and barrier input snapshots')
    chapter_labels = LABEL_RE.findall(uncomment(chapter))
    if len(chapter_labels) != len(set(chapter_labels)):
        raise BuildError('duplicate chapter label')
    # Freeze every input before invoking tools. Recheck the live files at the end.
    snapshot = workdir / 'snapshot'
    for path, data in {**sources, **extra_inputs}.items():
        destination = snapshot / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    output_dir.mkdir(parents=True, exist_ok=True)
    downloads, assets = output_dir / 'downloads', output_dir / 'assets'
    downloads.mkdir(exist_ok=True)
    assets.mkdir(exist_ok=True)
    validate_companion(output_dir, result_bytes, report)
    full_pdf, full_aux, full_log = compile_tex(snapshot / 'book/main.tex', workdir / 'full', tools, logs, 'full-monograph')
    labels, citations = aux_maps(full_aux)
    all_source_labels = [label for data in sources.values() for label in LABEL_RE.findall(uncomment(data.decode()))]
    if len(set(all_source_labels)) != len(all_source_labels) or set(all_source_labels) - labels.keys():
        raise BuildError('full-monograph labels are duplicated or not present in compiled aux')
    preamble = canonical.split(r'\begin{document}', 1)[0]
    bib = bibliography(canonical)
    external = external_equations(canonical, labels)
    external_header = (r'\section*{Cross-references outside this chapter}' + '\n'
                       'The following equations are copied from Section 16 of the full monograph solely '
                       'to resolve references. Their hypotheses and proofs are outside the Section 9 review. '
                       'These excerpts are not audited claims of this chapter.\n')
    link_map = {'../site/section9/index.html': 'index.html',
                '../artifacts/section9/result.json': 'downloads/result.json',
                '../site/section9/downloads/section9-reproduction.zip': 'downloads/section9-reproduction.zip',
                'claims/section9.json': 'downloads/section9-claims.json'}
    copied = {}
    if barrier is not None:
        copied.update(barrier['source_bytes'])
        link_map.update({
            '../site/section9/barrier.html': 'barrier.html',
            '../artifacts/section9/barrier-result.json': 'downloads/barrier-result.json',
            '../site/section9/downloads/barrier-reproduction.zip': 'downloads/barrier-reproduction.zip',
        })
        for name in (BARRIER_SOURCES['experiment.driver'], BARRIER_SOURCES['toolkit.angle_barrier']):
            target = 'downloads/' + Path(name).name
            (output_dir / target).write_bytes(barrier['source_bytes'][name])
            link_map['../' + name] = target
    source_roles = {'experiments/section9/run.py': 'experiment.driver',
                    'experiments/section9/fixture.json': 'experiment.fixture',
                    'packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py': 'toolkit.variational'}
    for path in ('experiments/section9/run.py', 'experiments/section9/fixture.json', 'experiments/section9/README.md',
                 'book/companion-reconciliation.md',
                 'packages/volume-toolkit/ideal_poly_volume_toolkit/variational.py'):
        target = 'reproduction-guide.md' if path.endswith('README.md') else Path(path).name
        data = (root / path).read_bytes()
        if path in source_roles and report_sources.get(source_roles[path]) != digest(data):
            raise BuildError(f'computation report source differs from requested inspection copy: {path}')
        (downloads / target).write_bytes(data)
        copied[path] = data
        link_map['../' + path] = 'downloads/' + target
        if path.startswith('book/'):
            link_map[path[len('book/'):]] = 'downloads/' + target
    (downloads / 'result.json').write_bytes(result_bytes)
    (downloads / 'section9-claims.json').write_bytes(extra_inputs[str(LEDGER)])
    (assets / 'section9.css').write_bytes(extra_inputs['site/section9.css'])

    # Render each original TikZ picture separately, without altering its source.
    figures = list(re.finditer(r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}', chapter, re.S))
    if len(figures) != chapter.count(r'\begin{figure}'):
        raise BuildError('every chapter figure must have exactly one supported TikZ drawing')
    html_chapter = chapter
    figure_manifest = []
    for i, match in reversed(list(enumerate(figures, 1))):
        figure_dir = workdir / f'figure-{i}'
        figure_dir.mkdir(exist_ok=True)
        tex = figure_dir / 'figure.tex'
        tex.write_text(preamble + '\n' + r'\usepackage[active,tightpage]{preview}' + '\n'
                       + r'\PreviewEnvironment{tikzpicture}\setlength\PreviewBorder{5pt}' + '\n'
                       + r'\begin{document}' + '\n' + match.group() + '\n' + r'\end{document}' + '\n')
        pdf, _, _ = compile_tex(tex, figure_dir / 'build', tools, logs, f'figure-{i}')
        png = assets / f'section9-figure-{i}.png'
        run([tools['gs'], '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m', '-r240',
             '-dFirstPage=1', '-dLastPage=1', f'-sOutputFile={png}', pdf],
            cwd=figure_dir, log=logs / f'figure-{i}-png.log')
        html_chapter = html_chapter[:match.start()] + r'\includegraphics{assets/' + png.name + '}' + html_chapter[match.end():]
        png_header = png.read_bytes()[:24]
        if png_header[:8] != b'\x89PNG\r\n\x1a\n':
            raise BuildError('figure renderer did not produce a PNG')
        width, height = int.from_bytes(png_header[16:20], 'big'), int.from_bytes(png_header[20:24], 'big')
        figure_manifest.append({'index': i, 'tikz_sha256': digest(match.group().encode()),
                                'png_sha256': digest(png.read_bytes()), 'dpi': 240,
                                'width': width, 'height': height})
    unknown_envs = set(re.findall(r'\\begin\{([^{}]+)\}', html_chapter)) - ENVIRONMENTS
    if unknown_envs:
        raise BuildError(f'unsupported chapter environments: {sorted(unknown_envs)}')

    def read_latex(text, name):
        raw = run([tools['pandoc'], '--from=latex+raw_tex', '--to=json'], cwd=snapshot / 'book',
                  log=logs / f'{name}-read.log', stdin=preamble + '\n' + r'\begin{document}' + '\n' + text + '\n' + r'\end{document}')
        if raw.stderr.strip():
            raise BuildError(f'Pandoc reader warning; see {logs / (name + "-read.log")}')
        parsed = json.loads(raw.stdout)
        # The full-book title/author/date in the shared preamble are not chapter
        # content. The chapter page supplies its own explicit document title.
        parsed['meta'] = {}
        return parsed

    document = read_latex(html_chapter + '\n' + external_header + external, 'chapter')
    converter = Converter(labels, citations, link_map)
    document = converter.transform(document)
    chapter_math_count = len(list(ast_nodes(document, 'Math')))
    used = sorted(converter.used_citations, key=lambda key: int(citations[key]))
    document['blocks'].append({'t': 'Header', 'c': [1, ['references', ['unnumbered'], []], [literal('References')]]})
    for key in used:
        if key not in bib:
            raise BuildError(f'cited entry missing from bibliography: {key}')
        blocks = converter.transform(read_latex(bib[key], 'bib-' + key))['blocks']
        blocks[0]['c'] = [literal(f'[{citations[key]}] ')] + blocks[0]['c']
        document['blocks'].append({'t': 'Div', 'c': [['ref-' + key, ['bibliography-entry'], []], blocks]})
    write_json(workdir / 'chapter-ast.json', document)
    html_result = run([tools['pandoc'], '--from=json', '--to=html5', '--math-method=mathml', '--wrap=none'],
                      cwd=output_dir, log=logs / 'chapter-html.log', stdin=json.dumps(document))
    if html_result.stderr.strip():
        raise BuildError(f'Pandoc MathML warning/fallback; see {logs / "chapter-html.log"}')
    html_body = html_result.stdout
    for figure in figure_manifest:
        old = f'<img src="assets/section9-figure-{figure["index"]}.png"'
        if html_body.count(old) != 1:
            raise BuildError('rendered figure image is missing or duplicated')
        html_body = html_body.replace(old, old + f' width="{figure["width"]}" height="{figure["height"]}"')

    selected_bib = '\n'.join(r'\bibitem[' + citations[key] + ']{' + key + '}\n' + bib[key] for key in used)
    figure_labels = [key for key in chapter_labels if labels[key]['anchor'].startswith('figure.')]
    first_figure = int(labels[figure_labels[0]]['number']) if figure_labels else 1
    section_number = int(labels['sec:ipolybridge']['number'])
    wrapper = (preamble + '\n' + r'\begin{document}' + '\n'
               + r'\hypersetup{pdftitle={Section 9: Volume Hessians, finite elements, and computational complexity}}' + '\n'
               + r'\setcounter{section}{' + str(section_number - 1) + '}\n'
               + r'\setcounter{figure}{' + str(first_figure - 1) + '}\n'
               + r'\input{chapters/09-volume-hessians.tex}' + '\n'
               + external_header + external + '\n' + r'\begin{thebibliography}{999}' + '\n'
               + selected_bib + '\n' + r'\end{thebibliography}' + '\n' + r'\end{document}' + '\n')
    # Only href targets change in PDF-only copies; mathematical source is identical.
    pdf_chapter, pdf_wrapper = chapter, wrapper
    for source, target in link_map.items():
        pdf_target = target[len('downloads/'):] if target.startswith('downloads/') else '../' + target
        pdf_chapter = pdf_chapter.replace(r'\href{' + source + '}', r'\href{' + pdf_target + '}')
        pdf_wrapper = pdf_wrapper.replace(r'\href{' + source + '}', r'\href{' + pdf_target + '}')
    pdf_book = workdir / 'standalone'
    (pdf_book / 'chapters').mkdir(parents=True, exist_ok=True)
    (pdf_book / 'chapters/09-volume-hessians.tex').write_text(pdf_chapter)
    (pdf_book / 'section9.tex').write_text(pdf_wrapper)
    pdf, chapter_aux, chapter_log = compile_tex(pdf_book / 'section9.tex', workdir / 'chapter-pdf', tools, logs, 'standalone-chapter')
    chapter_map, chapter_citations = aux_maps(chapter_aux)
    for label in chapter_labels + list(EXTERNAL_LABELS):
        if label not in chapter_map or chapter_map[label]['number'] != labels[label]['number']:
            raise BuildError(f'standalone PDF changed label number: {label}')
    if any(chapter_citations.get(key) != citations[key] for key in used):
        raise BuildError('standalone bibliography numbers differ from monograph')
    shutil.copyfile(pdf, downloads / 'section9.pdf')
    renders = workdir / 'rendered-pages'
    renders.mkdir(exist_ok=True)
    run([tools['gs'], '-dSAFER', '-dBATCH', '-dNOPAUSE', '-sDEVICE=png16m', '-r110',
         f'-sOutputFile={renders}/page-%03d.png', pdf], cwd=workdir, log=logs / 'render-pages.log')
    pages = int(re.search(r'\\gdef\s*\\@abspage@last\{(\d+)\}', chapter_aux).group(1))
    if len(list(renders.glob('page-*.png'))) != pages:
        raise BuildError('not every standalone PDF page rendered')
    archive_payload = dict(sources)
    archive_payload['book/companion-reconciliation.md'] = copied['book/companion-reconciliation.md']
    archive_payload['book/section9.tex'] = wrapper.encode()
    archive_payload[str(LEDGER)] = extra_inputs[str(LEDGER)]
    archive_payload['README.md'] = (
        '# Complete canonical monograph LaTeX source\n\n'
        'From book/, run `latexmk -norc -pdf main.tex` for the full monograph or '
        '`latexmk -norc -pdf section9.tex` for the generated Section 9 excerpt. '
        'The preamble and selected bibliography in section9.tex are generated from the canonical full source. '
        'External Section 16 equations are reference-only, outside this chapter review. '
        'Canonical chapter source is unchanged; repository-relative hyperlinks need the repository/companion. '
        'The separately distributed chapter PDF rewrites only those link targets for its downloads directory.\n'
    ).encode()
    archive_payload['source-manifest.json'] = (json.dumps({'source_commit': commit, 'repository_dirty_at_start': bool(status),
        'input_sha256': {name: digest(data) for name, data in sources.items()},
        'payload_sha256': {name: digest(data) for name, data in archive_payload.items()}}, indent=2) + '\n').encode()
    with zipfile.ZipFile(downloads / 'monograph-source.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(archive_payload.items()):
            info = zipfile.ZipInfo('monograph-source/' + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    evidence_links, pending_evidence = {}, []
    barrier_targets = {'artifacts/section9/barrier-result.json': 'downloads/barrier-result.json',
                       'site/section9/downloads/barrier-reproduction.zip': 'downloads/barrier-reproduction.zip',
                       'site/section9/barrier.html': 'barrier.html'}
    for name in sorted(evidence_paths):
        if name == 'artifacts/section9/result.json':
            evidence_links[name] = 'downloads/result.json'
            continue
        if name == 'site/section9/downloads/section9-reproduction.zip':
            evidence_links[name] = 'downloads/section9-reproduction.zip'
            continue
        if name in barrier_targets:
            if barrier is None:
                raise BuildError(f'barrier evidence requires --barrier-result: {name}')
            evidence_links[name] = barrier_targets[name]
            continue
        path = (root / name).resolve()
        if not path.is_relative_to(root):
            raise BuildError(f'external ledger evidence path: {name}')
        if not path.is_file():
            if allow_pending_evidence and name.startswith(('docs/execution/section9-chapter-2026-10-31/',
                                                         'docs/execution/section9-barrier-2026-10-31/')):
                pending_evidence.append(name)
                continue
            raise BuildError(f'missing ledger evidence: {name}')
        data = path.read_bytes()
        frozen = copied.get(name, sources.get(name, extra_inputs.get(name)))
        if frozen is not None and data != frozen:
            raise BuildError(f'input changed before ledger inspection copy: {name}')
        copied[name] = data
        destination = downloads / 'inspection' / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        evidence_links[name] = str(destination.relative_to(output_dir))
    claims = claims_html(ledger, chapter_labels, evidence_links, pending_evidence)
    html = ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<title>Section 9 — Volume Hessians</title><link rel="stylesheet" href="assets/section9.css"></head><body>'
            '<header class="masthead"><p>Polyhedra, Moduli, and Quantum Geometry</p><nav aria-label="Chapter resources">'
            '<a href="index.html">Grid companion</a>'
            + ('<a href="barrier.html">Barrier solver examples</a>' if barrier is not None else '')
            + '<a href="downloads/section9.pdf">Chapter PDF</a>'
            '<a href="downloads/monograph-source.zip">Complete LaTeX source</a><a href="#claim-ledger">Claim ledger</a></nav></header>'
            '<main>' + html_body + claims + '</main><footer><p>Built from source commit <code>' + escape(commit)
            + '</code>; source checkout ' + ('dirty (preliminary)' if status else 'clean at build start') + '. '
            'Offline MathML and source-rendered figures. The linked computation is a separate finite check, not a proof audit.</p>'
            '<p><a href="downloads/chapter-build.json">Build provenance and validation</a></p></footer></body></html>')
    # Create provenance target before checking every local link; finalize below.
    write_json(downloads / 'chapter-build.json', {'status': 'building'})
    validation = validate_html(html, output_dir, chapter_labels + list(EXTERNAL_LABELS),
                               len(list(ast_nodes(document, 'Math'))), len(figures))
    manifest = {'schema_version': 1, 'operation': 'build_complete_section9_excerpt',
                'generated_at_utc': datetime.now(timezone.utc).isoformat(), 'source_commit': commit,
                'repository_dirty_at_start': bool(status), 'git_status_porcelain_at_start': status,
                'inputs': {name: digest(data) for name, data in {**sources, **extra_inputs, **copied}.items()},
                'computation_result': {'actual_path': str(result_path), 'sha256': digest(result_bytes),
                                       'provenance': report['provenance']},
                'barrier_computation_result': ({'actual_path': str(barrier['path']),
                                               'sha256': digest(barrier['result_bytes']),
                                               'provenance': barrier['report']['provenance'],
                                               'asset_hash_scope': 'inputs at chapter-build time, before any optional render-only backlink refresh',
                                               'asset_sha256': {name: digest(data) for name, data in barrier['assets'].items()}}
                                              if barrier is not None else None),
                'tools': tools, 'tool_versions': versions, 'full_monograph_label_count': len(labels),
                'pending_evidence': pending_evidence,
                'preliminary': bool(status) or bool(pending_evidence),
                'chapter_label_map': {key: labels[key] for key in chapter_labels},
                'external_reference_only_labels': {key: labels[key] for key in EXTERNAL_LABELS},
                'citation_map': {key: citations[key] for key in used},
                'numbered_equations': converter.equations, 'figures': sorted(figure_manifest, key=lambda x: x['index']),
                'validation': {**validation, 'pdf_pages': pages, 'pdf_pages_rendered': pages,
                               'visual_review': 'pending human/agent inspection of rendered pages',
                               'chapter_math_nodes_before_bibliography': chapter_math_count,
                               'full_monograph_overfull_hbox_count': full_log.count('Overfull \\hbox'),
                               'chapter_overfull_hbox_count': chapter_log.count('Overfull \\hbox')},
                'work_directory': str(workdir), 'rendered_pages': str(renders)}
    # Fail if any canonical/report/copied source changed during the snapshot build.
    for path, data in {**sources, **extra_inputs, **copied}.items():
        if (root / path).read_bytes() != data:
            raise BuildError(f'input changed during build; rerun from stable sources: {path}')
    if result_path.read_bytes() != result_bytes:
        raise BuildError('computation result changed during build')
    if barrier is not None:
        if barrier['path'].read_bytes() != barrier['result_bytes']:
            raise BuildError('barrier computation result changed during build')
        for name, data in barrier['assets'].items():
            if (output_dir / name).read_bytes() != data:
                raise BuildError(f'barrier companion asset changed during build: {name}')
    (output_dir / 'chapter.html').write_text(html)
    manifest['output_sha256'] = {str(path.relative_to(output_dir)): digest(path.read_bytes())
        for path in [output_dir / 'chapter.html', downloads / 'section9.pdf', downloads / 'monograph-source.zip',
                     downloads / 'section9-claims.json', *sorted(assets.glob('section9-*')), assets / 'section9.css']}
    write_json(downloads / 'chapter-build.json', manifest)
    write_json(workdir / 'build-manifest.json', manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path, required=True,
                        help='existing numerical companion output directory; use a temporary path for release builds')
    parser.add_argument('--computation-result', type=Path, required=True)
    parser.add_argument('--barrier-result', type=Path,
                        help='explicit matching barrier report; required when chapter/ledger links that example')
    parser.add_argument('--work-dir', type=Path,
                        help='retained snapshot/log/render directory (default: new temporary directory)')
    parser.add_argument('--allow-pending-evidence', action='store_true',
                        help='preliminary preview only: mark missing current audit files as pending; final builds reject them')
    args = parser.parse_args()
    workdir = args.work_dir or Path(tempfile.mkdtemp(prefix='section9-chapter-'))
    manifest = build(args.root, args.output_dir, args.computation_result, workdir,
                     allow_pending_evidence=args.allow_pending_evidence,
                     barrier_result_path=args.barrier_result)
    print(json.dumps({'source_commit': manifest['source_commit'], 'dirty_at_start': manifest['repository_dirty_at_start'],
                      'pdf_pages': manifest['validation']['pdf_pages'],
                      'chapter': str(args.output_dir / 'chapter.html'), 'work_dir': str(workdir)}, indent=2))


if __name__ == '__main__':
    main()
