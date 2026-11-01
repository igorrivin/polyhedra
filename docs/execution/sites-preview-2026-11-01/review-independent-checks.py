"""Independent inspection of the fixed reading-preview export; no browser work."""
from hashlib import sha256
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import unquote, urljoin, urlsplit
import zipfile

ROOT = Path("/Volumes/Lexar/lambda/devel/polyhedra/consolidated")
EVIDENCE = ROOT.parent / "execution/sites-preview-2026-11-01"
OUTPUT = Path(json.loads((EVIDENCE / "review-location.json").read_text())["output"]).resolve()
AUTHOR = json.loads((EVIDENCE / "author-final-manifest.json").read_text())
CHECKPOINT = json.loads((ROOT / "docs/execution/section9-barrier-2026-10-31/final-artifact-manifest.json").read_text())
MANIFEST = json.loads((OUTPUT / "preview-manifest.json").read_text())


def digest(data):
    return sha256(data).hexdigest()


class Document(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.math, self.figures = [], [], 0, []
        self.active_json = False
        self.inline_json = []
        self.new_navigation = []
        self.nav_depth = 0
        self.heading = None
        self.headings = []

    def handle_starttag(self, tag, attributes):
        a = dict(attributes)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "math":
            self.math += 1
        if tag == "img":
            self.figures.append(a.get("src"))
            assert a.get("alt"), "missing image alternative"
        for key in ("href", "src"):
            if key in a:
                self.links.append(a[key])
        if tag == "nav":
            self.nav_depth += 1
        if tag == "a" and ("edition-brand" in a.get("class", "").split() or self.nav_depth):
            self.new_navigation.append(a["href"])
        if tag in ("h1", "h2", "h3"):
            self.heading = [tag, a.get("id"), []]
        if tag == "script" and a.get("id") == "edition-search-data":
            self.active_json = True

    def handle_data(self, data):
        if self.active_json:
            self.inline_json.append(data)
        if self.heading is not None:
            self.heading[2].append(data)

    def handle_endtag(self, tag):
        if tag == "nav":
            self.nav_depth -= 1
        if tag == "script":
            self.active_json = False
        if self.heading is not None and tag == self.heading[0]:
            self.headings.append([self.heading[0], self.heading[1], "".join(self.heading[2])])
            self.heading = None


for name, expected in AUTHOR["source_sha256"].items():
    assert digest((ROOT / name).read_bytes()) == expected, name
for name, expected in CHECKPOINT["sha256"].items():
    assert digest((ROOT / name).read_bytes()) == expected, name

physical = list(OUTPUT.rglob("*"))
assert not any(p.is_symlink() for p in physical)
files = {p.relative_to(OUTPUT).as_posix(): p for p in physical if p.is_file()}
assert set(files) == set(MANIFEST["output_sha256"]) | {"preview-manifest.json"}
assert len(files) == 49
for name in files:
    assert not any(p.startswith("._") or p in {".git", ".openai", ".DS_Store", "__MACOSX", ".env"} for p in PurePosixPath(name).parts), name
for name, expected in MANIFEST["output_sha256"].items():
    assert digest(files[name].read_bytes()) == expected, name

html_documents = {}
restored_html, untouched = [], 0
for name, expected in CHECKPOINT["sha256"].items():
    if not name.startswith("site/"):
        continue
    relative = name.removeprefix("site/")
    data = files[relative].read_bytes()
    if name.endswith(".html"):
        text = data.decode()
        for label in ("style", "navigation"):
            text, count = re.subn(r"<!-- preview-" + label + r":start -->.*?<!-- preview-" + label + r":end -->", "", text, flags=re.S)
            assert count == 1, (name, label)
        assert text.encode() == (ROOT / name).read_bytes(), name
        restored_html.append(relative)
    else:
        assert digest(data) == expected, name
        untouched += 1
for name, path in files.items():
    if name.endswith(".html"):
        parsed = Document()
        parsed.feed(path.read_text())
        assert len(parsed.ids) == len(set(parsed.ids)), name
        html_documents[name] = parsed
assert len(html_documents) == 4
chapter = html_documents["section9/chapter.html"]
assert chapter.math == 209
assert len(chapter.figures) == 2
subsections = [h for h in chapter.headings if h[0] == "h2" and (h[1] or "").startswith("subsec:")]
assert len(subsections) == 6

index = json.loads(files["search-index.json"].read_text())
assert len(index["records"]) == 204
assert json.loads("".join(html_documents["index.html"].inline_json)) == index
assert {r["source"] for r in index["records"]} == {"Chapter 9", "Grid companion", "Barrier examples"}
assert max(len(r["text"]) for r in index["records"]) < 6000
assert all("secretFixture" not in r["text"] for r in index["records"])
landing = files["index.html"].read_text()
assert "broader draft" in landing and "limited to Section 9" in landing
assert 'for="edition-query"' in landing and 'role="status"' in landing
assert "fetch(" not in files["assets/search.js"].read_text()
assert "innerHTML" not in files["assets/search.js"].read_text()
assert not any("{{" in files[name].read_text() for name in html_documents)

links = [(name, link) for name, doc in html_documents.items() for link in doc.links]
links.extend(("index.html", row["url"]) for row in index["records"])
checked = 0
for name, href in links:
    url = urlsplit(href)
    if url.scheme or url.netloc:
        assert url.scheme in {"https", "http", "mailto"}
        continue
    resolved = urlsplit(urljoin((OUTPUT / name).as_uri(), href))
    target = Path(unquote(resolved.path)).resolve()
    assert target.is_relative_to(OUTPUT) and target.is_file(), (name, href)
    relative = target.relative_to(OUTPUT).as_posix()
    if resolved.fragment and relative in html_documents:
        assert unquote(resolved.fragment) in html_documents[relative].ids, (name, href)
    checked += 1
assert checked == 473

archives = {}
for name in ("monograph-source.zip", "section9-reproduction.zip", "barrier-reproduction.zip"):
    with zipfile.ZipFile(OUTPUT / "section9/downloads" / name) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        assert all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in names)
        assert not any(any(p.startswith("._") or p in {".git", ".env", ".DS_Store", "__MACOSX"} for p in PurePosixPath(n).parts) for n in names)
        assert not any("holdout" in n.lower() or "credential" in n.lower() for n in names)
        archives[name] = {"entries": len(names), "sha256": digest((OUTPUT / "section9/downloads" / name).read_bytes())}

spec = importlib.util.spec_from_file_location("reviewed_preview", ROOT / "site/build_preview.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
symlink_checks = {}
for kind in ("matching-file", "dangling-file", "directory", "output-root"):
    with tempfile.TemporaryDirectory(prefix="preview-fixed-link-review-") as temporary:
        base = Path(temporary)
        outside = base / "outside"
        outside.mkdir()
        victim = outside / "asset.txt"
        victim.write_bytes(b"unmodified")
        target = base / "dist"
        if kind == "output-root":
            target.symlink_to(outside)
        else:
            target.mkdir()
            if kind == "directory":
                (target / "subdirectory").symlink_to(outside)
            else:
                (target / "asset.txt").symlink_to(victim if kind == "matching-file" else outside / "missing.txt")
            if kind == "matching-file":
                (target / "preview-manifest.json").write_text(json.dumps({"operation": builder.OWNER, "output_sha256": {"asset.txt": digest(b"unmodified")}}))
        try:
            builder.build(ROOT, target)
        except builder.PreviewError as error:
            assert "symlink" in str(error), str(error)
        else:
            raise AssertionError(kind)
        assert victim.read_bytes() == b"unmodified" and not (outside / "missing.txt").exists()
        symlink_checks[kind] = "rejected; outside bytes unchanged"

node = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {searchRecords, excerpt} = require(process.argv[1]);
const data = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const required = {'Schur':['Chapter 9','Grid companion'],'asymmetric':['Barrier examples'],'flat triangle':['Barrier examples'],'Casson':['Chapter 9'],'λ':['Chapter 9'],'rooted forest':['Chapter 9','Grid companion']};
const results = {};
for (const [query, sources] of Object.entries(required)) {
  const found=searchRecords(data.records,query,1000);
  for(const source of sources) assert.ok(found.items.some(x=>x.source===source),query+': '+source);
  assert.ok(found.total===found.items.length);
  results[query]={count:found.total,sources:[...new Set(found.items.map(x=>x.source))]};
}
assert.deepEqual(searchRecords(data.records,'   '),{total:0,items:[]});
assert.equal(searchRecords(data.records,'no-such-phrase-qxz').total,0);
assert.ok(excerpt('Proof about a boundary maximum','boundary').includes('boundary'));
console.log(JSON.stringify(results));
"""
run = subprocess.run(["node", "-e", node, str(ROOT / "site/preview/search.js"), str(OUTPUT / "search-index.json")], capture_output=True, text=True, check=True)
queries = json.loads(run.stdout)
mirror = Path(AUTHOR["mirror"]) / "dist"
assert all((mirror / name).read_bytes() == files[name].read_bytes() for name in MANIFEST["output_sha256"])
assert MANIFEST["research_source"]["dirty"] is True
assert MANIFEST["numerical_source_commit"] == "c1f100b957166b93eca0d214586322d5af71b9cf"
assert MANIFEST["pdf"]["sha256"] == "9db08eec8405c637c8ac79ad0afcaaa4b4bf810435463dbb3361fee7616975f0"
assert "not performed" in MANIFEST["publication"]
for name, expected in AUTHOR["source_sha256"].items():
    assert digest((ROOT / name).read_bytes()) == expected, name
result = {"status": "passed", "source_sha256": AUTHOR["source_sha256"], "review_output": str(OUTPUT),
          "source_checkpoint_inputs_verified": 46, "output_files": len(files),
          "scientific_html_exactly_recovered": restored_html, "unchanged_nonhtml_assets": untouched,
          "local_links_and_search_targets": checked, "chapter_mathml_nodes": chapter.math,
          "chapter_ids": len(chapter.ids), "chapter_figures": len(chapter.figures), "subsections": subsections,
          "search_passages": len(index["records"]), "actual_search_queries": queries, "archives": archives,
          "symlink_regressions": symlink_checks, "author_and_reviewer_assets_identical": True,
          "source_preview_dirty": True, "browser_qa": "not performed",
          "deployment": "not performed; registered Site is not a live deployment",
          "packaging_boundary": "Site tar still needs physical archive inventory verification; ordinary assets may omit recognized metadata"}
(EVIDENCE / "review-independent-checks.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: result[key] for key in ("status", "output_files", "local_links_and_search_targets", "chapter_mathml_nodes", "search_passages", "author_and_reviewer_assets_identical")}, indent=2))
