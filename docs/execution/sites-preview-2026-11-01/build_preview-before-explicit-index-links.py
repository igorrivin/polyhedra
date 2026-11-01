#!/usr/bin/env python3
"""Export the reviewed Section 9 artifacts as a buildless reading preview.

This is a presentation build. It never runs scientific computations, converts
LaTeX, changes the reviewed PDF, or publishes a Site.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import quote, unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
CHECKPOINT = Path("docs/execution/section9-barrier-2026-10-31/final-artifact-manifest.json")
HTML_PAGES = {
    "chapter.html": "Chapter 9",
    "index.html": "Grid companion",
    "barrier.html": "Barrier examples",
}
STYLE = '<!-- preview-style:start --><link rel="stylesheet" href="../assets/preview.css"><!-- preview-style:end -->'
NAV = '''<!-- preview-navigation:start -->
<nav class="edition-nav" aria-label="Monograph edition">
  <a class="edition-brand" href="../">Polyhedra, Moduli, and Quantum Geometry</a>
  <div><a href="../#contents">Contents</a><a href="chapter.html">Chapter</a><a href="index.html">Grid</a><a href="barrier.html">Barrier</a><a href="../#search">Search</a></div>
</nav>
<!-- preview-navigation:end -->'''
OWNER = "polyhedra-section9-reading-preview"


class PreviewError(ValueError):
    """An input or export does not satisfy the frozen publishing contract."""


def digest(data: bytes) -> str:
    return sha256(data).hexdigest()


def read_json(data: bytes):
    def reject(value):
        raise PreviewError(f"nonfinite JSON value: {value}")
    return json.loads(data, parse_constant=reject)


def embedded_json(value):
    """Keep JSON data inert even when a passage contains an HTML end tag."""
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False).replace(
        "&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace(
        "\u2028", "\\u2028").replace("\u2029", "\\u2029")


def safe_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (not path.is_absolute() and bool(path.parts) and
            all(part not in ("..", ".git", ".openai", ".DS_Store", "__MACOSX")
                and not part.startswith("._") for part in path.parts))


def ordinary_files(directory: Path):
    """Ignore only platform-created metadata, never arbitrary unlisted assets."""
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise PreviewError(f"symlink is not an export asset: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(directory)
        if any(part.startswith("._") or part == ".DS_Store" for part in relative.parts):
            header = path.read_bytes()[:8]
            if ((path.name.startswith("._") and header == bytes.fromhex("0005160700020000")) or
                    (path.name == ".DS_Store" and header == bytes.fromhex("0000000142756431"))):
                continue
            raise PreviewError(f"unrecognized platform-metadata path: {path}")
        result[relative.as_posix()] = path
    return result


def load_inputs(root: Path):
    root = root.resolve()
    manifest_bytes = (root / CHECKPOINT).read_bytes()
    manifest = read_json(manifest_bytes)
    expected = manifest["sha256"]
    site_paths = {name for name in expected if name.startswith("site/section9/")}
    reports = {"artifacts/section9/result.json", "artifacts/section9/barrier-result.json"}
    if len(expected) != 46 or len(site_paths) != 44 or set(expected) != site_paths | reports:
        raise PreviewError("the selected checkpoint must identify the reviewed 44 assets and two reports")
    actual = {"site/section9/" + name for name in ordinary_files(root / "site/section9")}
    if actual != site_paths:
        raise PreviewError("canonical site inventory differs from the frozen checkpoint")
    payload = {}
    for name, expected_digest in expected.items():
        path = root / name
        if not safe_name(name) or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise PreviewError(f"unsafe source path: {name}")
        data = path.read_bytes()
        if digest(data) != expected_digest:
            raise PreviewError(f"source hash differs from reviewed checkpoint: {name}")
        payload[name] = data
    for name in ("result.json", "barrier-result.json"):
        if payload[f"artifacts/section9/{name}"] != payload[f"site/section9/downloads/{name}"]:
            raise PreviewError(f"canonical and inspection report differ: {name}")
        provenance = read_json(payload[f"artifacts/section9/{name}"])["provenance"]
        if (provenance["source_commit"] != manifest["source_commit"] or
                provenance["repository_dirty_at_start"] is not False):
            raise PreviewError(f"report does not have the recorded clean numerical origin: {name}")
    return manifest, manifest_bytes, payload


def add_navigation(source: str) -> str:
    if "preview-navigation:start" in source or "preview-style:start" in source:
        raise PreviewError("source already contains preview navigation")
    if source.count("</head>") != 1 or len(re.findall(r"<body(?:\s[^>]*)?>", source)) != 1:
        raise PreviewError("expected exactly one head and body in reviewed HTML")
    result = source.replace("</head>", STYLE + "</head>", 1)
    result = re.sub(r"(<body(?:\s[^>]*)?>)", lambda m: m.group(1) + NAV, result, count=1)
    if result.replace(STYLE, "", 1).replace(NAV, "", 1) != source:
        raise PreviewError("presentation transformation did not preserve source HTML")
    return result


class SearchParser(HTMLParser):
    """Index visible passages; omit scripts, SVG data and duplicate TeX annotations."""
    omitted = {"script", "style", "annotation", "svg", "nav", "template"}
    blocks = {"p", "li", "tr", "pre", "figcaption", "h1", "h2", "h3", "h4"}

    def __init__(self, page: str, title: str):
        super().__init__(convert_charrefs=True)
        self.page, self.page_title = page, title
        self.records, self.headings, self.containers = [], [], []
        self.omit_depth, self.omit_tag = 0, None
        self.block, self.text, self.block_id = None, [], ""
        self.heading, self.heading_id = title, ""

    def handle_starttag(self, tag, attrs):
        if self.omit_depth:
            if tag == self.omit_tag:
                self.omit_depth += 1
            return
        if tag in self.omitted:
            self.omit_depth, self.omit_tag = 1, tag
            return
        attr = dict(attrs)
        if tag in ("section", "div", "article"):
            self.containers.append((tag, attr.get("id", "")))
        if tag in self.blocks and self.block is None:
            self.block, self.text = tag, []
            container_id = next((value for _, value in reversed(self.containers) if value), "")
            self.block_id = attr.get("id", "") or container_id or self.heading_id

    def handle_startendtag(self, tag, attrs):
        pass

    def handle_data(self, data):
        if self.block and not self.omit_depth:
            self.text.append(data)

    def handle_endtag(self, tag):
        if self.omit_depth:
            if tag == self.omit_tag:
                self.omit_depth -= 1
            return
        if tag == self.block:
            text = re.sub(r"\s+", " ", " ".join(self.text)).strip()
            if tag.startswith("h"):
                self.heading = text
                self.heading_id = self.block_id
                self.headings.append({"level": tag, "title": text, "anchor": self.block_id})
            if text:
                url = "section9/" + self.page
                if self.block_id:
                    url += "#" + quote(self.block_id, safe=":._-")
                self.records.append({"source": self.page_title, "title": self.heading,
                                     "url": url, "text": text[:6000]})
            self.block = None
        if tag in ("section", "div", "article") and self.containers:
            if self.containers[-1][0] == tag:
                self.containers.pop()


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.links = set(), []
        self.math_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                raise PreviewError(f"duplicate HTML id: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "math":
            self.math_count += 1
        for key in ("href", "src"):
            if key in attrs:
                self.links.append(attrs[key])


def validate_export(directory: Path, records):
    directory = directory.resolve()
    files = ordinary_files(directory)
    parsed = {}
    for name, path in files.items():
        if not safe_name(name) or path.is_symlink():
            raise PreviewError(f"unsafe output path: {name}")
        if name.endswith(".html"):
            parser = LinkParser()
            parser.feed(path.read_text())
            parsed[name] = parser
    count = 0
    links = [(name, link) for name, parser in parsed.items() for link in parser.links]
    links += [("index.html", item["url"]) for item in records]
    for name, link in links:
        target = urlsplit(link)
        if target.scheme or target.netloc:
            if target.scheme not in ("http", "https", "mailto"):
                raise PreviewError(f"unsupported link scheme: {link}")
            continue
        base = directory if target.path.startswith("/") else (directory / name).parent
        path = (base / unquote(target.path).lstrip("/")).resolve() if target.path else directory / name
        if path.is_dir():
            path /= "index.html"
        if not path.is_relative_to(directory) or not path.is_file():
            raise PreviewError(f"missing or escaping local link: {name}: {link}")
        relative = path.relative_to(directory).as_posix()
        if target.fragment and relative in parsed and unquote(target.fragment) not in parsed[relative].ids:
            raise PreviewError(f"unresolved fragment: {name}: {link}")
        count += 1
    if parsed["section9/chapter.html"].math_count != 209:
        raise PreviewError("chapter MathML inventory changed")
    return {"local_links_and_search_targets_checked": count, "html_pages": len(parsed),
            "chapter_mathml_count": 209, "search_passages": len(records),
            "browser_verification": "not performed; static checks do not establish browser rendering or interaction"}


def git_state(root):
    commit = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(root), "status", "--porcelain"], text=True).splitlines()
    return {"commit": commit, "dirty": bool(status), "status_porcelain": status}


def check_existing_output(directory):
    if directory.is_symlink() or any(path.is_symlink() for path in directory.rglob("*")):
        raise PreviewError("output directory contains a symlink")
    if not directory.exists() or not ordinary_files(directory):
        return
    path = directory / "preview-manifest.json"
    if not path.is_file():
        raise PreviewError("nonempty output directory has no preview ownership manifest")
    prior = read_json(path.read_bytes())
    if prior.get("operation") != OWNER:
        raise PreviewError("output directory belongs to another operation")
    expected = prior["output_sha256"]
    if set(ordinary_files(directory)) != set(expected) | {"preview-manifest.json"}:
        raise PreviewError("output directory contains unowned files")
    for name, value in expected.items():
        if not safe_name(name) or digest((directory / name).read_bytes()) != value:
            raise PreviewError(f"previous output was modified: {name}")


def build(root: Path, output: Path, *, require_clean=False):
    check_existing_output(output)
    root, output = root.resolve(), output.resolve()
    if output == root or output.is_relative_to(root):
        raise PreviewError("preview output must be outside the canonical research checkout")
    if (root / "site/build_preview.py").resolve() != Path(__file__).resolve():
        raise PreviewError("run the preview exporter belonging to the selected research checkout")
    check_existing_output(output)
    state = git_state(root)
    if require_clean and state["dirty"]:
        raise PreviewError("final preview export requires a clean research checkout")
    checkpoint, checkpoint_bytes, inputs = load_inputs(root)
    owner_paths = ["site/build_preview.py", "site/preview/index.html", "site/preview/preview.css", "site/preview/search.js"]
    owners = {name: (root / name).read_bytes() for name in owner_paths}
    template = owners["site/preview/index.html"].decode()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".polyhedra-preview-", dir=output.parent) as temp:
        stage = Path(temp).resolve()
        transformations, records, headings = {}, [], []
        for name, data in inputs.items():
            if not name.startswith("site/section9/"):
                continue
            relative = name.removeprefix("site/")
            if Path(relative).name in HTML_PAGES and relative.count("/") == 1:
                parser = SearchParser(Path(relative).name, HTML_PAGES[Path(relative).name])
                parser.feed(data.decode())
                records.extend(parser.records)
                if relative == "section9/chapter.html":
                    headings = [row for row in parser.headings if row["level"] == "h2" and row["anchor"].startswith("subsec:")]
                original = data
                data = add_navigation(data.decode()).encode()
                transformations[relative] = {"source_sha256": digest(original), "output_sha256": digest(data),
                                             "operation": "insert only marked navigation and stylesheet link",
                                             "original_recovered_byte_for_byte": True}
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        if len(headings) != 6:
            raise PreviewError("expected six canonical Section 9 subsection headings")
        toc = "\n".join('<li><a href="section9/chapter.html#' + quote(row["anchor"], safe=":._-") + '"><span>' +
                        escape(row["title"].split(" ", 1)[0]) + '</span>' + escape(row["title"].split(" ", 1)[1]) + '</a></li>'
                        for row in headings)
        if template.count("{{CONTENTS}}") != 1:
            raise PreviewError("landing template must have one contents insertion")
        index = {"schema_version": 1, "scope": "Section 9 and its two companions", "records": records}
        index_json = json.dumps(index, ensure_ascii=False, indent=2)
        embedded = embedded_json(index)
        if template.count("{{SEARCH_INDEX}}") != 1:
            raise PreviewError("landing template must have one search index insertion")
        (stage / "index.html").write_text(template.replace("{{CONTENTS}}", toc).replace("{{SEARCH_INDEX}}", embedded))
        (stage / "assets").mkdir()
        (stage / "assets/preview.css").write_bytes(owners["site/preview/preview.css"])
        (stage / "assets/search.js").write_bytes(owners["site/preview/search.js"])
        (stage / "search-index.json").write_text(index_json + "\n")
        # The manifest link is validated before its final hashes are available.
        (stage / "preview-manifest.json").write_text("{}\n")
        validation = validate_export(stage, records)
        output_hashes = {name: digest(path.read_bytes()) for name, path in sorted(ordinary_files(stage).items()) if name != "preview-manifest.json"}
        if (root / CHECKPOINT).read_bytes() != checkpoint_bytes:
            raise PreviewError("checkpoint manifest changed during build")
        for name, data in {**inputs, **owners}.items():
            if (root / name).read_bytes() != data:
                raise PreviewError(f"source changed during build: {name}")
        if git_state(root) != state:
            raise PreviewError("research checkout changed during presentation build")
        manifest = {"schema_version": 1, "operation": OWNER,
                    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                    "research_source": state,
                    "numerical_source_commit": checkpoint["source_commit"],
                    "checkpoint_manifest": {"path": str(CHECKPOINT), "sha256": digest(checkpoint_bytes)},
                    "input_sha256": {name: digest(data) for name, data in inputs.items()},
                    "builder_source_sha256": {name: digest(data) for name, data in owners.items()},
                    "html_transformations": transformations, "output_sha256": output_hashes,
                    "validation": validation,
                    "evidence_scope": "Presentation export of previously verified artifacts; no numerical execution or new mathematical review",
                    "publication": "not performed by this builder; a Site registration or local export is not a live deployment",
                    "pdf": {"unchanged": True, "sha256": digest(inputs["site/section9/downloads/section9.pdf"])}}
        (stage / "preview-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        check_existing_output(output)
        output.mkdir(parents=True, exist_ok=True)
        old_files = ordinary_files(output)
        for name, path in ordinary_files(stage).items():
            target = output / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(path.read_bytes())
        for name, path in old_files.items():
            if name not in output_hashes and name != "preview-manifest.json":
                path.unlink()
        for name, expected in output_hashes.items():
            if digest((output / name).read_bytes()) != expected:
                raise PreviewError(f"output copy differs: {name}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    manifest = build(args.root, args.output_dir, require_clean=args.require_clean)
    print(json.dumps({"output": str(args.output_dir.resolve()), "research_commit": manifest["research_source"]["commit"],
                      "dirty": manifest["research_source"]["dirty"], "exported_files": len(manifest["output_sha256"]) + 1,
                      **manifest["validation"]}, indent=2))


if __name__ == "__main__":
    main()
