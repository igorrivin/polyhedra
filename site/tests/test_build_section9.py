"""Strict publication failure modes; no external rendering tools required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('chapter_builder', ROOT / 'site/build_section9.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ChapterIntegrityTests(unittest.TestCase):
    def test_source_graph_complete_and_rejects_missing_external_cycle(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            book = root / 'book'
            (book / 'chapters').mkdir(parents=True)
            (book / 'main.tex').write_text('\\input{chapters/a.tex}\n')
            (book / 'chapters/a.tex').write_text('A source body\n')
            self.assertEqual(set(builder.source_graph(root)), {'book/main.tex', 'book/chapters/a.tex'})
            for bad, pattern in [('\\input{missing}', 'missing'), ('\\input{../outside}', 'external'),
                                 ('\\input{main.tex}', 'cyclic'), ('\\input foo', 'balanced')]:
                (book / 'chapters/a.tex').write_text(bad)
                with self.subTest(bad=bad), self.assertRaisesRegex(builder.BuildError, pattern):
                    builder.source_graph(root)

    def test_aux_nested_titles_and_duplicate_rejection(self):
        source = r'\newlabel{eq:a}{{9.8}{28}{A {nested} title}{equation.9.8}{}}' + '\n' + r'\bibcite{Rivin}{118}'
        labels, citations = builder.aux_maps(source)
        self.assertEqual(labels['eq:a']['number'], '9.8')
        self.assertEqual(citations['Rivin'], '118')
        tagged, _ = builder.aux_maps(r'\newlabel{eq:external}{{{16.7}}{9}{Reference only}{AMS.4}{}}')
        self.assertEqual(tagged['eq:external']['number'], '16.7')
        with self.assertRaisesRegex(builder.BuildError, 'duplicate compiled'):
            builder.aux_maps(source + '\n' + source)

    def test_equation_translation_preserves_authoritative_number_and_rejects_raw(self):
        labels = {'eq:a': {'number': '9.8'}}
        converter = builder.Converter(labels, {}, {})
        original = r'\begin{align}K_{\rm eff}&=x\notag\\y&=z\label{eq:a}\end{align}'
        result = converter.transform({'t': 'Math', 'c': [{'t': 'DisplayMath'}, original]})
        self.assertEqual(result['c'][0][0], 'eq:a')
        math = list(builder.ast_nodes(result, 'Math'))[0]['c'][1]
        self.assertEqual(math, r'\begin{aligned}K_{\mathrm{eff}}&=x\\y&=z\end{aligned}')
        self.assertIn('(9.8)', json.dumps(result))
        with self.assertRaisesRegex(builder.BuildError, 'unhandled raw'):
            converter.transform({'t': 'RawInline', 'c': ['latex', r'\unsupported{lost prose}']})
        with self.assertRaisesRegex(builder.BuildError, 'unresolved canonical'):
            converter.transform({'t': 'Math', 'c': [{'t': 'DisplayMath'}, r'x\label{missing}']})

    def test_citation_suffix_and_missing_citation(self):
        cite = {'t': 'Cite', 'c': [[{'citationId': 'A', 'citationPrefix': [],
                 'citationSuffix': [{'t': 'Str', 'c': 'Theorem 1'}]}], [{'t': 'RawInline', 'c': ['latex', r'\cite{A}']}]]}
        converter = builder.Converter({}, {'A': '118'}, {})
        result = converter.transform(cite)
        self.assertIn('#ref-A', json.dumps(result))
        self.assertIn('Theorem 1', json.dumps(result))
        with self.assertRaisesRegex(builder.BuildError, 'bibliography key'):
            builder.Converter({}, {}, {}).transform(cite)

    def test_html_gates_labels_math_images_local_downloads(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / 'image.svg').write_text('<svg/>')
            page = '<p id="eq:a"><math></math><a href="#eq:a">9.1</a></p><img src="image.svg" alt="Diagram">'
            self.assertEqual(builder.validate_html(page, root, ['eq:a'], 1, 1)['mathml_count'], 1)
            for broken, pattern in [(page.replace('id="eq:a"', 'id="wrong"'), 'labels absent'),
                                    (page + '<a href="missing.zip">download</a>', 'missing or external'),
                                    (page + '<script src="https://example.com/math.js"></script>', 'remote'),
                                    (page.replace('<math></math>', ''), 'count differs'),
                                    (page + '<span id="eq:a"></span>', 'duplicate')]:
                with self.subTest(pattern=pattern), self.assertRaisesRegex(builder.BuildError, pattern):
                    builder.validate_html(broken, root, ['eq:a'], 1, 1)

    def test_claim_requires_resolvable_label_evidence_and_coverage(self):
        claim = {'label': 'eq:a', 'status': 'conditional', 'hypotheses': ['positive angles'],
                 'review_evidence': ['audit.md'], 'coverage_gap': 'No solver.'}
        self.assertIn('No solver.', builder.claims_html({'claims': [claim]}, ['eq:a']))
        for field in ('label', 'review_evidence', 'coverage_gap'):
            bad = {key: value for key, value in claim.items() if key != field}
            with self.subTest(field=field), self.assertRaises(builder.BuildError):
                builder.claims_html({'claims': [bad]}, ['eq:a'])

    def test_ledger_discovers_site_bundle_without_using_old_canonical_copy(self):
        path = 'site/section9/downloads/section9-reproduction.zip'
        self.assertEqual(list(builder.ledger_paths({'evidence_paths': [path]})), [path])

    def test_companion_mismatched_result_and_embedded_report_are_rejected(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            downloads = root / 'downloads'
            downloads.mkdir()
            result = b'{"schema_version": 2}'
            report = json.loads(result)
            report['provenance'] = {'input_sha256': builder.digest(b'{}')}
            for filename, data in [('result.json', b'{}'), ('fixture.json', b'{}'), ('section9-reproduction.zip', b'')]:
                (downloads / filename).write_bytes(data)
            (root / 'index.html').write_text('\nconst data = {};')
            with self.assertRaisesRegex(builder.BuildError, 'result differs'):
                builder.validate_companion(root, result, report)
            (downloads / 'result.json').write_bytes(result)
            with self.assertRaisesRegex(builder.BuildError, 'HTML differs'):
                builder.validate_companion(root, result, report)

    def test_barrier_evidence_requires_explicit_result(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.assertIsNone(builder.validate_barrier_companion(root, root, None, required=False))
            with self.assertRaisesRegex(builder.BuildError, 'supply --barrier-result'):
                builder.validate_barrier_companion(root, root, None, required=True)
            with self.assertRaisesRegex(builder.BuildError, 'missing explicit barrier'):
                builder.validate_barrier_companion(root, root, root / 'missing.json', required=True)

    def test_barrier_nonreport_or_wrong_experiment_is_rejected(self):
        for invalid in ([], {'schema_version': True},
                        {'schema_version': 1, 'all_checks_passed': True,
                         'cases': [{}], 'experiment_id': 'unrelated-experiment'}):
            with self.subTest(invalid=invalid), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                result = root / 'invalid.json'
                result.write_text(json.dumps(invalid))
                with self.assertRaisesRegex(builder.BuildError, 'passing schema-1 report'):
                    builder.validate_barrier_companion(root, root, result, required=True)

    def barrier_export(self, root):
        """Synthetic identity fixtures; these deliberately claim no solver accuracy."""
        site = root / 'export'
        (site / 'downloads').mkdir(parents=True)
        fixture = {'id': 'section9-barrier-fixtures-v1', 'cases': [{'id': 'test-identity-only'}]}
        payload = {}
        for role, name in builder.BARRIER_SOURCES.items():
            data = (json.dumps(fixture).encode() if role == 'experiment.fixture'
                    else ('source role ' + role + '\n').encode())
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            payload[name] = data
        chapter = root / builder.CHAPTER
        chapter.parent.mkdir(parents=True, exist_ok=True)
        chapter.write_text('Canonical test chapter\n')
        provenance = {'input_sha256': builder.digest(payload[builder.BARRIER_SOURCES['experiment.fixture']]),
                      'source_sha256': {role: builder.digest(payload[name]) for role, name in builder.BARRIER_SOURCES.items()}}
        provenance['source_sha256']['book.chapter'] = builder.digest(chapter.read_bytes())
        provenance['source_files'] = [{'role': role, 'available': True, 'sha256': value}
                                      for role, value in provenance['source_sha256'].items()]
        report = {'schema_version': 1, 'all_checks_passed': True,
                  'experiment_id': fixture['id'], 'cases': fixture['cases'], 'provenance': provenance}
        result = root / 'explicit-barrier.json'
        result.write_text(json.dumps(report))
        (site / 'downloads/barrier-result.json').write_bytes(result.read_bytes())
        (site / 'downloads/barrier-fixtures.json').write_bytes(payload[builder.BARRIER_SOURCES['experiment.fixture']])
        (site / 'barrier.html').write_text('\nconst barrierData = ' + json.dumps({'report': report, 'fixture': fixture}) + ';\n')
        manifest = {'origin_provenance': provenance,
                    'payload_sha256': {name: builder.digest(data) for name, data in payload.items()}}
        with zipfile.ZipFile(site / 'downloads/barrier-reproduction.zip', 'w') as archive:
            for name, data in payload.items():
                archive.writestr('barrier-reproduction/' + name, data)
            archive.writestr('barrier-reproduction/barrier-bundle.json', json.dumps(manifest))
        return site, result

    def test_barrier_export_matches_explicit_current_inputs(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            site, result = self.barrier_export(root)
            snapshot = builder.validate_barrier_companion(root, site, result, required=True)
            self.assertEqual(snapshot['result_bytes'], result.read_bytes())
            self.assertEqual(set(snapshot['assets']), set(builder.BARRIER_ASSETS))
            self.assertEqual(len(snapshot['source_bytes']), 7)
            (root / builder.BARRIER_SOURCES['toolkit.angle_barrier']).write_text('changed solver\n')
            with self.assertRaisesRegex(builder.BuildError, 'source differs from current toolkit.angle_barrier'):
                builder.validate_barrier_companion(root, site, result, required=True)

    def test_barrier_missing_stale_or_mutated_export_is_rejected(self):
        for mutation, pattern in [('missing', 'missing barrier companion'),
                                  ('report', 'downloaded result differs'),
                                  ('fixture', 'fixture differs'),
                                  ('page', 'HTML differs'),
                                  ('zip-payload', 'payload hash mismatch'),
                                  ('zip-extra', 'unmanifested payloads')]:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as name:
                root = Path(name)
                site, result = self.barrier_export(root)
                if mutation == 'missing':
                    (site / 'barrier.html').unlink()
                elif mutation == 'report':
                    (site / 'downloads/barrier-result.json').write_text('{}')
                elif mutation == 'fixture':
                    (site / 'downloads/barrier-fixtures.json').write_text('{}')
                elif mutation == 'page':
                    (site / 'barrier.html').write_text('\nconst barrierData = {};\n')
                else:
                    path = site / 'downloads/barrier-reproduction.zip'
                    with zipfile.ZipFile(path) as archive:
                        payload = {name: archive.read(name) for name in archive.namelist()}
                    if mutation == 'zip-payload':
                        payload['barrier-reproduction/' + builder.BARRIER_SOURCES['toolkit.angle_barrier']] = b'changed'
                    else:
                        payload['barrier-reproduction/unrecorded.py'] = b'not in manifest'
                    with zipfile.ZipFile(path, 'w') as archive:
                        for name, data in payload.items():
                            archive.writestr(name, data)
                with self.assertRaisesRegex(builder.BuildError, pattern):
                    builder.validate_barrier_companion(root, site, result, required=True)


if __name__ == '__main__':
    unittest.main()
