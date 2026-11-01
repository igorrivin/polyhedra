"""Strict publication failure modes; no external rendering tools required."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

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


if __name__ == '__main__':
    unittest.main()
