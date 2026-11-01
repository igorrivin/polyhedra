"""Integrity tests for a presentation export of the frozen Section 9 outputs."""
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urljoin, urlsplit


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("build_preview", ROOT / "site/build_preview.py")
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class EmbeddedIndex(HTMLParser):
    def __init__(self):
        super().__init__()
        self.active = False
        self.data = []

    def handle_starttag(self, tag, attrs):
        if tag == "script" and dict(attrs).get("id") == "edition-search-data":
            self.active = True

    def handle_data(self, data):
        if self.active:
            self.data.append(data)

    def handle_endtag(self, tag):
        if tag == "script":
            self.active = False


class PreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="polyhedra-preview-tests-")
        cls.output = Path(cls.temp.name) / "dist"
        cls.manifest = preview.build(ROOT, cls.output)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_reviewed_bytes_and_html_are_preserved(self):
        self.assertEqual(len(self.manifest["input_sha256"]), 46)
        self.assertEqual(len(self.manifest["html_transformations"]), 3)
        for name, expected in self.manifest["input_sha256"].items():
            if not name.startswith("site/"):
                continue
            actual = (self.output / name.removeprefix("site/")).read_bytes()
            if name.endswith(".html"):
                actual = actual.decode().replace(preview.STYLE, "", 1).replace(preview.NAV, "", 1).encode()
            with self.subTest(path=name):
                self.assertEqual(sha256(actual).hexdigest(), expected)
        self.assertEqual(self.manifest["numerical_source_commit"], "c1f100b957166b93eca0d214586322d5af71b9cf")
        self.assertIn("not performed", self.manifest["publication"])

    def test_offline_index_and_targets_match(self):
        page = (self.output / "index.html").read_text()
        parser = EmbeddedIndex()
        parser.feed(page)
        data = json.loads("".join(parser.data))
        self.assertEqual(data, json.loads((self.output / "search-index.json").read_text()))
        self.assertGreater(len(data["records"]), 100)
        sources = {row["source"] for row in data["records"]}
        self.assertEqual(sources, {"Chapter 9", "Grid companion", "Barrier examples"})
        self.assertNotIn('type="module"', page)
        self.assertNotIn("fetch(", (self.output / "assets/search.js").read_text())
        checked = preview.validate_export(self.output, data["records"])
        self.assertEqual(checked["chapter_mathml_count"], 209)
        self.assertEqual(checked["html_pages"], 4)

    def test_inline_json_cannot_close_script(self):
        data = {"text": '</script><script>alert("x")</script>&\u2028\u2029'}
        encoded = preview.embedded_json(data)
        self.assertNotIn("<", encoded)
        self.assertNotIn("&", encoded)
        self.assertEqual(json.loads(encoded), data)

    def test_authored_navigation_resolves_to_files_locally_and_when_hosted(self):
        landing = preview.LinkParser()
        landing.feed((ROOT / "site/preview/index.html").read_text())
        navigation = preview.LinkParser()
        navigation.feed(preview.NAV)
        for page, links in (("index.html", landing.links), ("section9/chapter.html", navigation.links)):
            for href in links:
                if urlsplit(href).scheme:
                    continue
                with self.subTest(page=page, href=href):
                    local = urlsplit(urljoin((self.output / page).resolve().as_uri(), href))
                    target = Path(unquote(local.path))
                    self.assertTrue(target.is_file(), str(target))
                    hosted = urlsplit(urljoin("https://edition.example/" + page, href))
                    self.assertEqual(hosted.scheme, "https")
                    self.assertEqual(hosted.netloc, "edition.example")
                    self.assertEqual(unquote(hosted.path).lstrip("/"), target.relative_to(self.output.resolve()).as_posix())
                    self.assertEqual(hosted.fragment, local.fragment)

    def test_search_omits_script_and_tex_duplicates(self):
        parser = preview.SearchParser("example.html", "Example")
        parser.feed('<nav><br><a>skip navigation</a></nav><section id="result"><h2>A result</h2>'
                    '<p>Volume <math><mi>V</mi><annotation>duplicate Tex</annotation></math></p>'
                    '<script>secretFixture = 42</script><p>Last passage</p></section>')
        all_text = " ".join(row["text"] for row in parser.records)
        self.assertIn("Volume V", all_text)
        self.assertIn("Last passage", all_text)
        for excluded in ("skip navigation", "duplicate Tex", "secretFixture"):
            self.assertNotIn(excluded, all_text)
        self.assertTrue(all(row["url"].endswith("#result") for row in parser.records))

    def test_duplicate_injection_is_rejected(self):
        source = "<html><head></head><body><p>Text</p></body></html>"
        with self.assertRaises(preview.PreviewError):
            preview.add_navigation(preview.add_navigation(source))

    def test_output_symlinks_do_not_touch_external_data(self):
        for kind in ("file", "directory", "root", "dangling"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp:
                base = Path(temp)
                external = base / "external"
                external.mkdir()
                victim = external / "data.txt"
                victim.write_text("unchanged external bytes")
                directory = base / "dist"
                if kind == "root":
                    directory.symlink_to(external, target_is_directory=True)
                else:
                    directory.mkdir()
                    if kind in ("file", "dangling"):
                        (directory / "data.txt").symlink_to(victim if kind == "file" else external / "missing.txt")
                        name = "data.txt"
                    else:
                        (directory / "nested").symlink_to(external, target_is_directory=True)
                        name = "nested/data.txt"
                    manifest = {"operation": preview.OWNER, "output_sha256": {name: sha256(victim.read_bytes()).hexdigest()}}
                    (directory / "preview-manifest.json").write_text(json.dumps(manifest))
                with self.assertRaisesRegex(preview.PreviewError, "symlink"):
                    preview.build(ROOT, directory)
                self.assertEqual(victim.read_text(), "unchanged external bytes")
                self.assertFalse((external / "missing.txt").exists())

    def test_foreign_or_changed_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            path = directory / "foreign.txt"
            path.write_text("keep")
            with self.assertRaises(preview.PreviewError):
                preview.check_existing_output(directory)
            manifest = {"operation": preview.OWNER, "output_sha256": {"foreign.txt": sha256(b"before").hexdigest()}}
            (directory / "preview-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(preview.PreviewError, "modified"):
                preview.check_existing_output(directory)
            self.assertEqual(path.read_text(), "keep")

    def test_final_build_rejects_dirty_checkout(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(preview, "git_state", return_value={"dirty": True}):
            with self.assertRaisesRegex(preview.PreviewError, "clean research"):
                preview.build(ROOT, Path(temp) / "dist", require_clean=True)

    def test_unknown_metadata_cannot_bypass_output_ownership(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            path = directory / "._not-platform-metadata"
            path.write_text("keep this data")
            with self.assertRaisesRegex(preview.PreviewError, "unrecognized platform"):
                preview.build(ROOT, directory)
            self.assertEqual(path.read_text(), "keep this data")

    def test_different_checkout_cannot_misattribute_builder(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(preview.PreviewError, "selected research checkout"):
                preview.build(root / "source", root / "output")

    def test_mutated_or_extra_input_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            manifest = json.loads((ROOT / preview.CHECKPOINT).read_text())
            for name in [str(preview.CHECKPOINT), *manifest["sha256"]]:
                destination = root / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / name, destination)
            target = root / "site/section9/barrier.html"
            original = target.read_bytes()
            target.write_bytes(original + b"mutated")
            with self.assertRaisesRegex(preview.PreviewError, "hash differs"):
                preview.load_inputs(root)
            target.write_bytes(original)
            (root / "site/section9/unreviewed.txt").write_text("not in the export")
            with self.assertRaisesRegex(preview.PreviewError, "inventory differs"):
                preview.load_inputs(root)

    def test_missing_fragment_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "dist"
            shutil.copytree(self.output, root)
            path = root / "index.html"
            path.write_text(path.read_text().replace("#subsec:ipolyCoordinates", "#missing-reviewed-anchor", 1))
            with self.assertRaisesRegex(preview.PreviewError, "unresolved fragment"):
                preview.validate_export(root, [])


if __name__ == "__main__":
    unittest.main()
