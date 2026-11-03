"""Regressions for full-book constructs absent from the frozen Section 9 edition."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("book_builder", ROOT / "site/build_book.py")
book = importlib.util.module_from_spec(spec)
spec.loader.exec_module(book)


def converter(number="28", labels=None, routes=None):
    return book.BookConverter(labels or {}, {"A": "129"}, routes or {},
                              {"number": number, "file": "28-model.html"}, {})


class CompleteBookTests(unittest.TestCase):
    def test_explicit_unnumbered_illustration_preserves_caption_and_alt(self):
        caption = [{"t": "Str", "c": "Angle"}, {"t": "Space"},
                   {"t": "Math", "c": [{"t": "InlineMath"}, "A+B<\\pi"]}]
        figure = {"t": "Figure", "c": [["", [], []], [None, [{"t": "Plain", "c": caption}]],
                   [{"t": "Plain", "c": [{"t": "Image", "c": [["", [], []], [], ["assets/figure.png", ""]]}]}]]}
        document = {"blocks": [figure]}
        book.mark_unnumbered_figures(document, r"\begin{figure}\caption*{Angle $A+B<\pi$}\end{figure}")
        transformed = converter().transform(document)
        result = transformed["blocks"][0]
        self.assertIn("unnumbered", result["c"][0][1])
        self.assertEqual(result["c"][1][1][0]["c"], caption)
        image = next(book.chapter.ast_nodes(result, "Image"))
        self.assertIn("Angle", book.chapter.inline_text(image["c"][1]))
        self.assertNotIn("Figure", book.chapter.inline_text(result["c"][1]))
        figure["c"][0][1] = []
        book.mark_unnumbered_figures(document, r"\begin{figure}\caption{Angle}\end{figure}")
        with self.assertRaisesRegex(book.BuildError, "source label"):
            converter().transform(document)
        with self.assertRaisesRegex(book.BuildError, "inventories differ"):
            book.mark_unnumbered_figures(document, "")
        with self.assertRaisesRegex(book.BuildError, "numbered source label"):
            book.mark_unnumbered_figures(document, r"\begin{figure}\caption*{Angle}\label{bad}\end{figure}")

    def test_source_bundle_and_selected_code_carry_exact_scoped_license_files(self):
        _, payload = book.curated_inputs(ROOT)
        expected = {"LICENSES/README.md", "LICENSES/CC-BY-4.0.txt", "LICENSES/MONOGRAPH-NOTICE.md",
                    "LICENSES/new-companions-MIT.txt", "LICENSES/new-companion-files.txt", "LICENSES/volume-toolkit-MIT.txt",
                    "packages/volume-toolkit/LICENSE"}
        self.assertEqual(set(book.LICENSE_FILES), expected)
        for name in expected:
            self.assertEqual(payload[name], (ROOT / name).read_bytes())
        covered = set(payload["LICENSES/new-companion-files.txt"].decode().splitlines())
        for name in payload:
            if name.startswith("experiments/") and name.endswith(".py"):
                self.assertIn(name, covered)
        self.assertNotIn("experiments/section15/historical-table.json", covered)
        sources = book.chapter.source_graph(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "monograph-source.zip"
            book.source_archive(path, sources, payload)
            with zipfile.ZipFile(path) as archive:
                self.assertEqual(set(archive.namelist()), set(sources) | expected | {"source-manifest.json"})
                for name, data in {**sources, **{name: payload[name] for name in expected}}.items():
                    self.assertEqual(archive.read(name), data)
                manifest = json.loads(archive.read("source-manifest.json"))
                self.assertEqual(manifest["source_sha256"], {name: book.digest(data) for name, data in sources.items()})
                self.assertEqual(manifest["license_sha256"], {name: book.digest(payload[name]) for name in expected})
                self.assertIn("CC BY 4.0", manifest["rights"])
                self.assertIn("LICENSES/new-companion-files.txt", manifest["rights"])
                self.assertNotIn("artifacts/", "\n".join(archive.namelist()))
            missing_terms = dict(payload)
            del missing_terms["LICENSES/CC-BY-4.0.txt"]
            with self.assertRaisesRegex(book.BuildError, "missing required license"):
                book.source_archive(Path(tmp) / "incomplete.zip", sources, missing_terms)

    def test_source_routes_include_every_chapter_label_and_bibliography_entry(self):
        sources = book.chapter.source_graph(ROOT)
        _, pages, parts, routes, bib = book.source_pages(sources)
        self.assertEqual(len(sources), 36)
        self.assertEqual(len(pages), 35)
        self.assertEqual(len(parts), 7)
        self.assertEqual(len(routes), 613)
        self.assertEqual(len(bib), 136)
        self.assertEqual(routes["sec:monographintro"], "introduction.html")
        self.assertEqual(routes["sec:ipolybridge"], "09-volume-hessians.html")
        self.assertEqual(routes["app:conventions"], "appendix-b-conventions.html")

    def test_source_router_rejects_unconsumed_prose_and_active_inputs(self):
        sources = book.chapter.source_graph(ROOT)
        main = str(book.chapter.MAIN)
        needle = b"\\input{chapters/01-volume-normalization.tex}"
        changed = dict(sources)
        changed[main] = sources[main].replace(needle, needle + b"\nSentinel prose $123=456$. \\textbf{Keep this proof}.\n", 1)
        with self.assertRaisesRegex(book.BuildError, "unconsumed body"):
            book.source_pages(changed)
        changed[main] = sources[main].replace(needle, needle + b"\n\\include{review-extra}\n", 1)
        changed["book/review-extra.tex"] = b"Additional active content.\n"
        with self.assertRaisesRegex(book.BuildError, "unrecognized chapter include"):
            book.source_pages(changed)
        changed[main] = sources[main]
        with self.assertRaisesRegex(book.BuildError, "inputs were not consumed"):
            book.source_pages(changed)

    def test_supported_include_is_consumed_and_wrapper_bibliography_remainders_rejected(self):
        sources = book.chapter.source_graph(ROOT)
        main = str(book.chapter.MAIN)
        changed = dict(sources)
        changed[main] = sources[main].replace(b"\\input{chapters/01-volume-normalization.tex}", b"\\include{chapters/01-volume-normalization}", 1)
        self.assertEqual(book.source_pages(changed), book.source_pages(sources))
        for filename, original, replacement, message in (
            ("book/main.tex", b"\\input", b"Retain wrapper prose.\n\\input", "entry wrapper"),
            (main, b"\\begin{thebibliography}{999}", b"\\begin{thebibliography}{999}\nRetain bibliography prose.\n", "before bibliography"),
            (main, b"\\end{thebibliography}", b"\\end{thebibliography}\nRetain final prose.\n", "after the bibliography"),
        ):
            changed = dict(sources)
            changed[filename] = sources[filename].replace(original, replacement, 1)
            with self.subTest(region=message), self.assertRaisesRegex(book.BuildError, message):
                book.source_pages(changed)

    def test_nested_input_to_already_routed_chapter_is_not_silently_expanded(self):
        sources = book.chapter.source_graph(ROOT)
        changed = dict(sources)
        name = "book/chapters/01-volume-normalization.tex"
        changed[name] += b"\n\\input{chapters/02-ideal-angle-cells.tex}\n"
        with self.assertRaisesRegex(book.BuildError, "nested source include"):
            book.source_pages(changed)
        main = str(book.chapter.MAIN)
        for needle in (b"\\begin{document}", b"\\bibitem{WentworthGardiner}"):
            changed = dict(sources)
            changed[main] = sources[main].replace(needle, b"\\input{chapters/02-ideal-angle-cells.tex}\n" + needle, 1)
            with self.subTest(region=needle), self.assertRaisesRegex(book.BuildError, "outside the routed chapter region"):
                book.source_pages(changed)

    def test_align_split_respects_nested_substack_and_matrix_breaks(self):
        tex = r"A&=\substack{x\\y},\notag\\B&=\begin{pmatrix}1&2\\3&4\end{pmatrix},\label{b}\\C&=4\label{c}"
        rows = book.split_align_rows(tex)
        self.assertEqual(len(rows), 3)
        self.assertIn(r"x\\y", rows[0])
        self.assertIn(r"3&4", rows[1])
        labels = {"b": {"number": "28.4"}, "c": {"number": "28.5"}}
        numbered = book.equation_rows(r"\begin{align}" + tex + r"\end{align}", labels)
        self.assertEqual([x["number"] for x in numbered], [None, "28.4", "28.5"])

    def test_align_unlabeled_rows_are_numbered_from_compiled_witnesses(self):
        labels = {"b": {"number": "28.8"}}
        tex = r"\begin{align}A&=B,\\C&=D.\label{b}\end{align}"
        self.assertEqual([row["number"] for row in book.equation_rows(tex, labels)], ["28.7", "28.8"])
        with self.assertRaisesRegex(book.BuildError, "uniquely fixed"):
            book.equation_rows(r"\begin{align}A&=B\\C&=D\end{align}", {})
        bad = {"a": {"number": "28.2"}, "b": {"number": "28.8"}}
        with self.assertRaisesRegex(book.BuildError, "uniquely fixed"):
            book.equation_rows(r"\begin{align}A&=B\label{a}\\C&=D\label{b}\end{align}", bad)

    def test_mathml_row_numbers_and_anchors_attach_to_corresponding_rows(self):
        rows = [{"labels": ["a"], "ordinal": 0, "number": "2.1"},
                {"labels": ["b"], "ordinal": 1, "number": "2.2"}]
        from html import escape
        html = '<span class="aligned-equations" data-equation-rows="' + escape(json.dumps(rows), quote=True) + '"><math xmlns="' + book.MATH_NS + '"><semantics><mtable><mtr><mtd><mi>a</mi></mtd></mtr><mtr><mtd><mi>b</mi></mtd></mtr></mtable></semantics></math></span>'
        rendered = book.insert_align_numbers(html)
        root = ET.fromstring(rendered)
        actual = root.findall(".//{" + book.MATH_NS + "}mtr")
        self.assertEqual([node.attrib["id"] for node in actual], ["a", "b"])
        self.assertEqual([node.attrib["data-number"] for node in actual], ["2.1", "2.2"])
        self.assertIn("(2.2)", rendered)
        with self.assertRaisesRegex(book.BuildError, "rows differ"):
            book.insert_align_numbers(html.replace("<mtr><mtd><mi>b</mi></mtd></mtr>", ""))

    def test_spacing_workaround_preserves_the_airy_inequality(self):
        source = r"\begin{split}&G(v+iy)-G(v)\\&\hspace{25mm}\le -c_1\lambda y^2-c_2y^4\end{split}"
        normalized, labels = book.normalize_math(source)
        self.assertEqual(normalized, source.replace(r"\hspace{25mm}", r"\quad "))
        self.assertEqual(labels, [])

    def test_unlabeled_numbered_equation_is_rejected_but_starred_display_is_kept(self):
        with self.assertRaisesRegex(book.BuildError, "requires an explicit canonical label"):
            converter("1").transform({"t": "Math", "c": [{"t": "DisplayMath"}, r"\begin{equation}x=123\end{equation}"]})
        result = converter("1").transform({"t": "Math", "c": [{"t": "DisplayMath"}, r"\begin{equation*}x=123\end{equation*}"]})
        self.assertEqual(result["t"], "Math")
        self.assertEqual(result["c"][1], "x=123")
        with self.assertRaisesRegex(book.BuildError, "starred equation"):
            converter("1").transform({"t": "Math", "c": [{"t": "DisplayMath"}, r"\begin{equation*}x=123\label{x}\end{equation*}"]})

    def test_unlabeled_remark_and_question_keep_the_shared_theorem_counter(self):
        c = converter("3", {"prop:a": {"number": "3.2"}}, {"prop:a": "28-model.html"})
        def statement(kind, label="", style="Strong"):
            return {"t": "Div", "c": [[label, [kind], []], [{"t": "Para", "c": [
                {"t": style, "c": [{"t": "Str", "c": kind.title()}, {"t": "Space"}, {"t": "Str", "c": "1"}]},
                {"t": "Str", "c": " Body."}]}]]}
        remark = c.transform(statement("remark", style="Emph"))
        proposition = c.transform(statement("proposition", "prop:a"))
        self.assertEqual(remark["c"][0][0], "statement-3.1")
        self.assertIn("3.2", json.dumps(proposition))
        questions = converter("32")
        for i in range(1, 16):
            result = questions.transform(statement("question"))
            self.assertEqual(result["c"][0][0], f"statement-32.{i}")

    def test_cross_page_reference_and_citation_suffix(self):
        c = converter(labels={"eq:a": {"number": "9.8"}}, routes={"eq:a": "09-volume-hessians.html"})
        result = c.transform({"t": "RawInline", "c": ["latex", r"\eqref{eq:a}"]})
        self.assertEqual(result["c"][2][0], "09-volume-hessians.html#eq:a")
        self.assertEqual(result["c"][1][0]["c"], "(9.8)")
        citation = {"t": "Cite", "c": [[{"citationId": "A", "citationPrefix": [], "citationSuffix": [book.literal("Theorem 2")]}], []]}
        rendered = json.dumps(c.transform(citation))
        self.assertIn("references.html#ref-A", rendered)
        self.assertIn("129", rendered)
        self.assertIn("Theorem 2", rendered)

    def test_unhandled_raw_tex_is_never_silently_dropped(self):
        with self.assertRaisesRegex(book.BuildError, "unhandled raw"):
            converter().transform({"t": "RawBlock", "c": ["latex", r"\unsupported{Proof text}"]})
        path = converter().transform({"t": "RawInline", "c": ["latex", r"\path{artifacts/quantum_geodesics/result.json}"]})
        self.assertEqual(path["c"][1], "artifacts/quantum_geodesics/result.json")

    def test_physics_note_keeps_math_citations_and_other_quotations(self):
        c = converter()
        math = {"t": "Math", "c": [{"t": "InlineMath"}, r"J_x=\hbar\sigma_x/2"]}
        citation = {"t": "Cite", "c": [[{"citationId": "A", "citationPrefix": [], "citationSuffix": []}], []]}
        note = {"t": "BlockQuote", "c": [
            {"t": "Para", "c": [{"t": "Strong", "c": [book.literal("Physics: angular momentum.")]}]},
            {"t": "Para", "c": [math, citation]}]}
        result = c.transform(note)
        self.assertEqual(result["t"], "Div")
        self.assertIn("physics-box", result["c"][0][1])
        self.assertIn(["role", "note"], result["c"][0][2])
        self.assertIn(r"J_x=\hbar\sigma_x/2", [x["c"][1] for x in book.chapter.ast_nodes(result, "Math")])
        self.assertIn("references.html#ref-A", json.dumps(result))
        for quote in ({"t": "BlockQuote", "c": []},
                      {"t": "BlockQuote", "c": [{"t": "Para", "c": []}]},
                      {"t": "BlockQuote", "c": [{"t": "Para", "c": [book.literal("A quotation.")]}]}):
            self.assertEqual(c.transform(quote), quote)

    def test_appendix_longtable_spacing_keeps_the_following_note_and_rejects_other_setters(self):
        blocks = [{"t": "RawBlock", "c": ["latex", r"\setlength{\LTpost}{4pt}"]},
                  {"t": "Para", "c": [book.literal("Source conventions. Retain the complete note.")]}]
        result = converter("B").transform(blocks)
        self.assertEqual(result[0], {"t": "Plain", "c": []})
        self.assertEqual(result[1], blocks[1])
        for raw in (r"\setlength{\LTpost}{8pt}", r"\setlength{\parskip}{4pt}"):
            with self.subTest(raw=raw), self.assertRaisesRegex(book.BuildError, "unhandled raw"):
                converter("B").transform({"t": "RawBlock", "c": ["latex", raw]})

    def test_frontmatter_navigation_removal_preserves_authored_headings(self):
        source = r"\section*{Introduction}\addcontentsline{toc}{section}{Introduction}" + "\n" + r"\subsection*{Results}\addcontentsline{toc}{subsection}{Results}Retained prose."
        result = book.trim_frontmatter(source)
        self.assertNotIn("addcontentsline", result)
        self.assertIn(r"\subsection*{Results}", result)
        self.assertIn("Retained prose.", result)
        grouped = r"\begingroup\small Important retained prose.\endgroup"
        self.assertEqual(book.trim_frontmatter(grouped), grouped)

    def test_externally_supplied_compilation_receipt_option_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()
            result = subprocess.run([sys.executable, str(ROOT / "site/build_book.py"), "--output-dir", str(directory / "out"),
                                     "--work-dir", str(directory / "work"), "--reuse-compilation", str(directory / "self-authored.json")],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unrecognized arguments", result.stderr)
            self.assertFalse((directory / "work").exists())
            self.assertFalse(hasattr(book, "load_compilation"))

    def test_normalized_paths_reject_checkout_overlap_and_symlink_aliases_before_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()
            checkout, hop = directory / "checkout", directory / "hop"
            checkout.mkdir()
            hop.mkdir()
            link = directory / "alias"
            link.symlink_to(hop, target_is_directory=True)
            paths = [
                (directory / "out", hop / ".." / "checkout" / "scratch", "outside"),
                (hop / ".." / "checkout" / "out", directory / "scratch", "outside"),
                (hop / ".." / "out", directory / "out" / "scratch", "disjoint"),
                (directory / "out", hop / ".." / "out", "disjoint"),
                (link / ".." / "out", directory / "scratch", "symlink"),
            ]
            with patch.object(book, "ROOT", checkout), patch.object(book.preview, "git_state", side_effect=AssertionError("path guard was bypassed")):
                for output, work, message in paths:
                    with self.subTest(output=output, work=work), self.assertRaisesRegex(book.BuildError, message):
                        book.build(checkout, output, work)
            self.assertFalse((checkout / "scratch").exists())
            self.assertFalse((directory / "out").exists())

    def test_existing_compilation_scratch_is_rejected_before_any_compiler_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve()
            work = directory / "previous-build"
            work.mkdir()
            (work / "build-owner.json").write_text(json.dumps({"operation": book.OWNER}))
            with patch.object(book, "tools_available", return_value={}), patch.object(book, "compile_book", side_effect=AssertionError("compiler called")):
                with self.assertRaisesRegex(book.BuildError, "new empty scratch"):
                    book.build(ROOT, directory / "output", work)
            self.assertFalse((directory / "output").exists())

    def test_canonical_byline_affiliation_and_acknowledgment_are_preserved(self):
        sources = book.chapter.source_graph(ROOT)
        preamble, pages, parts, _, _ = book.source_pages(sources)
        metadata = book.canonical_metadata(preamble)
        self.assertEqual(metadata["author"], "Igor Rivin")
        self.assertEqual(metadata["affiliation_lines"], ["Department of Mathematics, Temple University"])
        self.assertIn("substantial help from Codex", pages[0]["tex"])
        for page in pages:
            page["title"] = page["number"] or "Introduction"
        content = book.landing(pages, parts, {"schema_version": 1, "records": []}, "test", metadata)
        html = book.page_shell("Contents", content, metadata=metadata)
        self.assertIn('<meta name="author" content="Igor Rivin">', html)
        self.assertIn('<meta name="affiliation" content="Department of Mathematics, Temple University">', html)
        self.assertIn('<span class="author">Igor Rivin</span>', html)
        self.assertIn('<span class="affiliation">Department of Mathematics, Temple University</span>', html)
        self.assertEqual(book.canonical_metadata(r"\author{}\date{30 October 2026}")["author"], "")
        with self.assertRaisesRegex(book.BuildError, "unsupported markup"):
            book.canonical_metadata(r"\author{A\and B}\date{30 October 2026}")

    def test_output_ownership_rejects_foreign_modified_and_symlink_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            file = root / "keep.txt"
            file.write_text("preserve")
            with self.assertRaisesRegex(book.BuildError, "foreign"):
                book.check_output(root)
            (root / "downloads").mkdir()
            manifest = {"operation": book.OWNER, "output_sha256": {"keep.txt": book.digest(b"before")}}
            (root / "downloads/edition-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(book.BuildError, "modified"):
                book.check_output(root)
            (root / "link.txt").symlink_to(file)
            with self.assertRaises((book.BuildError, book.preview.PreviewError)):
                book.check_output(root)
            self.assertEqual(file.read_text(), "preserve")

    def test_passage_search_routes_outside_section9_and_omits_annotations(self):
        parser = book.PassageParser("32-open-questions.html", "Questions")
        parser.feed('<section id="questions"><h1>Questions</h1><p>Quantum <math><mi>q</mi><annotation>duplicate TeX</annotation></math></p></section>')
        self.assertEqual(parser.records[-1]["url"], "32-open-questions.html#questions")
        self.assertNotIn("duplicate", parser.records[-1]["text"])


if __name__ == "__main__":
    unittest.main()
