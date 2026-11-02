#!/usr/bin/env python3
"""Build the complete local working edition from the canonical TeX graph.

This is the manuscript's strict converter, not a general LaTeX interpreter.
The frozen Section 9 exporter and scientific artifacts are read-only inputs.
See site/README.md for the local-only workflow and evidence boundaries.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html import escape, unescape
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OWNER = "polyhedra-complete-local-working-edition-v1"
THEOREMS = {"theorem", "proposition", "lemma", "corollary", "definition", "remark", "question"}
MATH_NS = "http://www.w3.org/1998/Math/MathML"


def sibling(name):
    spec = importlib.util.spec_from_file_location("book_" + name, Path(__file__).with_name(name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


chapter = sibling("build_section9")
preview = sibling("build_preview")
BuildError = chapter.BuildError
digest = chapter.digest
write_json = chapter.write_json


def literal(value):
    return {"t": "Str", "c": value}


def raw_html(value):
    return {"t": "RawBlock", "c": ["html", value]}


def mask_comments(text):
    """Hide comments without moving source offsets used by the routing parser."""
    return re.sub(r"(?<!\\)%[^\n]*", lambda match: " " * len(match.group()), text)


def source_pages(sources):
    """Consume every supported body region and input; reject unexplained content."""
    main = sources[str(chapter.MAIN)].decode()
    wrapper = chapter.uncomment(sources["book/main.tex"].decode()).strip()
    if wrapper != r"\input{polyhedral_volumes_and_geodesic_identities.tex}":
        raise BuildError("entry wrapper has unsupported or unconsumed content")
    masked_main = mask_comments(main)
    if masked_main.count(r"\begin{document}") != 1 or masked_main.count(r"\end{document}") != 1:
        raise BuildError("expected exactly one document boundary pair")
    start, end = masked_main.index(r"\begin{document}"), masked_main.index(r"\end{document}")
    if start >= end:
        raise BuildError("document boundaries are out of order")
    preamble, body = main[:start], main[start + len(r"\begin{document}"):end]
    tail = main[end + len(r"\end{document}"):]
    if chapter.uncomment(tail).strip():
        raise BuildError("unconsumed content after the document boundary")
    masked = mask_comments(body)
    first_part_match = re.search(r"\\monographpart\b", masked)
    if not first_part_match:
        raise BuildError("missing authored monograph parts")
    first_part = first_part_match.start()
    intro = body[:first_part]
    pages = [{"file": "introduction.html", "source": str(chapter.MAIN), "number": "",
              "tex": intro, "part": None}]
    bib_starts = list(re.finditer(r"\\begin\{thebibliography\}", masked))
    bib_ends = list(re.finditer(r"\\end\{thebibliography\}", masked))
    if len(bib_starts) != 1 or len(bib_ends) != 1 or bib_starts[0].start() <= first_part:
        raise BuildError("expected one complete final bibliography")
    _, bib_content_start = chapter.group(masked, bib_starts[0].end())
    if bib_content_start > bib_ends[0].start() or masked[bib_ends[0].end():].strip():
        raise BuildError("unconsumed content after the bibliography")
    bib_content = masked[bib_content_start:bib_ends[0].start()]
    if re.search(r"\\(?:input|include)\b", mask_comments(preamble) + bib_content):
        raise BuildError("source include outside the routed chapter region needs explicit handling")
    first_bibitem = re.search(r"\\bibitem\{", bib_content)
    if not first_bibitem:
        raise BuildError("empty manual bibliography")
    bib_prefix = bib_content[:first_bibitem.start()]
    bib_prefix = re.sub(r"\\setlength\{\\(?:itemsep|parskip)\}\{0pt\}", "", bib_prefix)
    bib_prefix = bib_prefix.replace(r"\addcontentsline{toc}{section}{References}", "")
    if bib_prefix.strip():
        raise BuildError("unconsumed content before bibliography entries")
    region = masked[first_part:bib_starts[0].start()]
    parts, current_part = [], None
    used = {"book/main.tex", str(chapter.MAIN)}
    pos, appendix = 0, False
    while pos < len(region):
        if region[pos].isspace():
            pos += 1
            continue
        layout = re.match(r"\\(clearpage|appendix)\b", region[pos:])
        if layout:
            if layout.group(1) == "appendix":
                if appendix:
                    raise BuildError("repeated appendix boundary")
                appendix = True
            pos += layout.end()
            continue
        token = re.match(r"\\(monographpart|input|include)\b", region[pos:])
        if not token:
            raise BuildError(f"unconsumed body content between chapter inputs: {region[pos:pos + 100]!r}")
        value, pos = chapter.group(region, pos + token.end())
        if token.group(1) == "monographpart":
            if appendix:
                raise BuildError("unexpected part after the appendix boundary")
            summary, pos = chapter.group(region, pos)
            if re.search(r"[\\$]", value + summary):
                raise BuildError("part title/summary needs explicit markup conversion")
            current_part = {"title": value, "summary": summary, "chapters": []}
            parts.append(current_part)
        else:
            relative = Path(value)
            if relative.suffix != ".tex":
                relative = relative.with_suffix(".tex")
            source = "book/" + relative.as_posix()
            if source not in sources or not value.startswith("chapters/") or not preview.safe_name(source):
                raise BuildError(f"unrecognized chapter include: {source}")
            if source in used:
                raise BuildError(f"repeated chapter include: {source}")
            used.add(source)
            stem = relative.stem
            number = stem.split("-", 1)[0]
            number = str(int(number)) if number.isdigit() else stem.split("-")[1].upper()
            if appendix == number.isdigit():
                raise BuildError("chapter and appendix boundary disagree")
            page = {"file": stem + ".html", "source": source, "number": number,
                    "tex": sources[source].decode(), "part": current_part if number.isdigit() else None}
            pages.append(page)
            if number.isdigit():
                current_part["chapters"].append(page["file"])
    if used != set(sources):
        raise BuildError(f"active source inputs were not consumed: {sorted(set(sources) - used)}")
    for page in pages:
        if re.search(r"\\(?:input|include)\b", mask_comments(page["tex"])):
            raise BuildError(f"nested source include needs explicit routing: {page['source']}")
    if len(parts) != 7 or len(pages) != 35 or [x["number"] for x in pages[1:]] != [*map(str, range(1, 33)), "A", "B"]:
        raise BuildError("expected seven parts, introduction, 32 chapters and Appendices A/B in source order")
    labels = {}
    for page in pages:
        for label in chapter.LABEL_RE.findall(chapter.uncomment(page["tex"])):
            if label in labels:
                raise BuildError(f"duplicate source label: {label}")
            labels[label] = page["file"]
    return preamble, pages, parts, labels, chapter.bibliography(chapter.uncomment(main))


def canonical_metadata(preamble):
    """Read the supported literal byline/date directly from canonical TeX."""
    values = {}
    masked = mask_comments(preamble)
    for name in ("author", "date"):
        matches = list(re.finditer(r"\\" + name + r"\b", masked))
        if len(matches) != 1:
            raise BuildError(f"expected one canonical {name} declaration")
        value, _ = chapter.group(masked, matches[0].end())
        values[name] = value
    lines = re.split(r"\\\\(?:\[[^\]]+\])?", values["author"])
    lines = [re.sub(r"^\s*\\normalsize\b", "", line).strip() for line in lines]
    lines = [re.sub(r"\s+", " ", line) for line in lines]
    if any(re.search(r"[\\{}$]", line) for line in [*lines, values["date"]]):
        raise BuildError("canonical byline/date needs explicit unsupported markup conversion")
    return {"author": lines[0], "affiliation_lines": [line for line in lines[1:] if line], "date": values["date"].strip()}


def split_align_rows(body):
    """Split only outer align rows, never a matrix, substack, or grouped break."""
    rows, start, pos, braces, environments = [], 0, 0, 0, 0
    while pos < len(body):
        if body[pos] == "\\":
            environment = re.match(r"\\(begin|end)\{[^{}]+\}", body[pos:])
            if environment:
                environments += 1 if environment.group(1) == "begin" else -1
                if environments < 0:
                    raise BuildError("unbalanced math environment")
                pos += len(environment.group())
                continue
            if body.startswith("\\\\", pos) and not braces and not environments:
                rows.append(body[start:pos])
                pos += 2
                spacing = re.match(r"\[[^\]]*\]", body[pos:])
                if spacing:
                    pos += len(spacing.group())
                start = pos
                continue
            pos += 2
            continue
        braces += (body[pos] == "{") - (body[pos] == "}")
        if braces < 0:
            raise BuildError("unbalanced math braces")
        pos += 1
    if braces or environments:
        raise BuildError("unclosed math grouping")
    if body[start:].strip():
        rows.append(body[start:])
    return rows


def equation_rows(tex, labels):
    """Recover every align-row number from TeX's labels, including unlabeled rows."""
    match = re.fullmatch(r"\s*\\begin\{align(\*?)\}(.*?)\\end\{align\1\}\s*", tex, re.S)
    if not match:
        return None
    rows, counted, witnesses = [], 0, []
    for text in split_align_rows(match.group(2)):
        names = chapter.LABEL_RE.findall(text)
        numbered = not match.group(1) and not re.search(r"\\(?:notag|nonumber)\b", text)
        if names and not numbered:
            raise BuildError("a labeled align row cannot suppress numbering")
        row = {"labels": names, "ordinal": counted if numbered else None, "number": None}
        if numbered:
            for name in names:
                if name not in labels:
                    raise BuildError(f"unresolved align label: {name}")
                number = labels[name]["number"]
                prefix, tail = number.rsplit(".", 1)
                witnesses.append((prefix, int(tail) - counted))
            counted += 1
        rows.append(row)
    if counted and (not witnesses or len(set(witnesses)) != 1):
        raise BuildError("align numbering is not uniquely fixed by the compiled labels")
    if counted:
        prefix, first = witnesses[0]
        for row in rows:
            if row["ordinal"] is not None:
                row["number"] = f"{prefix}.{first + row['ordinal']}"
    return rows


def normalize_math(tex):
    normalized, labels = chapter.normalize_math(tex)
    # texmath does not parse this dimensional hspace inside split. Spacing has
    # no mathematical content; all operators and terms are preserved.
    normalized = re.sub(r"\\hspace\{[0-9.]+(?:mm|cm|em|pt)\}", r"\\quad ", normalized)
    normalized = normalized.replace(r"\nonumber", "")
    return normalized, labels


class BookConverter:
    def __init__(self, labels, citations, label_pages, page, link_map):
        self.labels, self.citations, self.label_pages = labels, citations, label_pages
        self.page, self.link_map = page, link_map
        self.number = page["number"]
        self.heading_counts = [0, 0, 0]
        self.theorem_count = 0
        self.equations, self.references, self.used_citations = [], set(), set()

    def label_number(self, label):
        if label not in self.labels or label not in self.label_pages:
            raise BuildError(f"unresolved canonical label: {label}")
        return self.labels[label]["number"]

    def reference(self, label, equation=False):
        number = self.label_number(label)
        self.references.add(label)
        target = ("" if self.label_pages[label] == self.page["file"] else self.label_pages[label]) + "#" + label
        return {"t": "Link", "c": [["", [], []], [literal(f"({number})" if equation else number)], [target, ""]]}

    def transform(self, value):
        if isinstance(value, list):
            return [self.transform(x) for x in value]
        if not isinstance(value, dict):
            return value
        kind, content = value.get("t"), value.get("c")
        if kind in ("RawInline", "RawBlock"):
            raw = content[1].strip()
            if content[0] != "latex":
                raise BuildError(f"unexpected raw format: {content[0]}")
            reference = re.fullmatch(r"\\(eqref|ref|label)\{([^{}]+)\}", raw)
            if reference:
                command, label = reference.groups()
                self.label_number(label)
                if command == "label":
                    return {"t": "Span", "c": [[label, [], []], []]}
                return self.reference(label, command == "eqref")
            path = re.fullmatch(r"\\path\{([^{}]+)\}", raw)
            if path:
                return {"t": "Code", "c": [["", [], []], path.group(1)]}
            # The appendix's LTpost setting controls only printed whitespace
            # after its longtable; HTML table spacing is supplied by edition.css.
            if raw in {r"\centering", r"\noindent", r"\arraybackslash", r"\small", r"\medskip", r"\clearpage",
                       r"\begingroup", r"\endgroup", r"\setlength{\LTpost}{4pt}"}:
                return {"t": "Str", "c": ""} if kind == "RawInline" else {"t": "Plain", "c": []}
            raise BuildError(f"unhandled raw TeX: {raw[:180]}")
        if kind == "Math":
            normalized, names = normalize_math(content[1])
            if re.search(r"\\begin\{equation\}", content[1]) and not names:
                raise BuildError("numbered equation requires an explicit canonical label")
            if re.search(r"\\begin\{equation\*\}", content[1]) and names:
                raise BuildError("starred equation cannot carry a numbered label")
            math = {"t": "Math", "c": [content[0], normalized]}
            rows = equation_rows(content[1], self.labels)
            if rows is not None and any(row["number"] for row in rows):
                for row in rows:
                    for label in row["labels"]:
                        self.label_number(label)
                        self.equations.append({"label": label, "number": row["number"]})
                return {"t": "Span", "c": [["", ["aligned-equations"],
                        [["data-equation-rows", json.dumps(rows, separators=(",", ":"))]]], [math]]}
            if not names:
                return math
            if len(names) != 1:
                raise BuildError("multiple equation labels outside a supported align environment")
            name = names[0]
            number = self.label_number(name)
            self.equations.append({"label": name, "number": number})
            return {"t": "Span", "c": [[name, ["numbered-equation"], [["data-number", number]]],
                    [math, {"t": "Span", "c": [["", ["equation-number"], []], [literal(f"({number})")]]}]]}
        if kind == "Cite":
            inlines = [literal("[")]
            for index, citation in enumerate(content[0]):
                key = citation["citationId"]
                if key not in self.citations:
                    raise BuildError(f"unresolved bibliography key: {key}")
                self.used_citations.add(key)
                if index:
                    inlines.append(literal("; "))
                inlines.extend(self.transform(citation["citationPrefix"]))
                inlines.append({"t": "Link", "c": [["", [], []], [literal(self.citations[key])],
                                                        ["references.html#ref-" + key, ""]]})
                if citation["citationSuffix"]:
                    inlines.append(literal(", "))
                    inlines.extend(self.transform(citation["citationSuffix"]))
            return {"t": "Span", "c": [["", ["citation"], []], inlines + [literal("]")]]}
        if kind == "Link":
            attrs, text, target = content
            props = dict(attrs[2])
            if "reference" in props:
                return self.reference(props["reference"], props.get("reference-type") == "eqref")
            if target[0] in self.link_map:
                target = [self.link_map[target[0]], target[1]]
            elif not target[0].startswith(("https://", "http://", "mailto:")):
                raise BuildError(f"unmapped local source link: {target[0]}")
            return {"t": "Link", "c": [attrs, self.transform(text), target]}
        if kind == "Header":
            level, attrs, title = content
            # The article preamble retains the default secnumdepth=3;
            # paragraph headings (Pandoc level 4) therefore have no number.
            if "unnumbered" not in attrs[1] and level <= 3:
                if not self.number or not 1 <= level <= 3:
                    raise BuildError("unsupported numbered heading")
                if level == 1:
                    number = self.number
                else:
                    self.heading_counts[level - 2] += 1
                    self.heading_counts[level - 1:] = [0] * (4 - level)
                    number = self.number + "." + ".".join(map(str, self.heading_counts[:level - 1]))
                if attrs[0] in self.labels and self.label_number(attrs[0]) != number:
                    raise BuildError(f"heading disagrees with compiled number: {attrs[0]}")
                title = [literal(number + " ")] + title
            return {"t": "Header", "c": [min(level, 4), attrs, self.transform(title)]}
        if kind == "Div" and THEOREMS.intersection(content[0][1]):
            self.theorem_count += 1
            number = self.number + "." + str(self.theorem_count)
            explicit = [n for n in chapter.ast_nodes(content[1], "RawInline")
                        if n["c"][0] == "latex" and re.fullmatch(r"\\label\{[^{}]+\}", n["c"][1])]
            name = content[0][0]
            if explicit:
                if name or len(explicit) != 1:
                    raise BuildError("ambiguous theorem label")
                name = chapter.LABEL_RE.fullmatch(explicit[0]["c"][1]).group(1)
                content[0][0] = name
                explicit[0].clear()
                explicit[0].update(literal(""))
            if name and self.label_number(name) != number:
                raise BuildError(f"theorem number disagrees with TeX: {name}: {number}")
            if not name:
                content[0][0] = "statement-" + number
            strong = content[1][0].get("c", [None])[0]
            if not strong or strong.get("t") not in {"Strong", "Emph"} or strong["c"][-1].get("t") != "Str":
                raise BuildError("unrecognized theorem heading")
            strong["c"][-1]["c"] = number
        if kind == "Figure":
            attrs, caption, body = content
            images = list(chapter.ast_nodes(body, "Image"))
            if len(images) != 1 or not attrs[0]:
                raise BuildError("figure must have one image and a source label")
            alt = chapter.inline_text(caption[0] or caption[1])
            if not alt:
                raise BuildError("figure has no caption")
            images[0]["c"][1] = [literal(alt)]
            number = self.label_number(attrs[0])
            caption[1][0]["c"] = [literal(f"Figure {number}. ")] + caption[1][0]["c"]
        return {key: self.transform(child) for key, child in value.items()}


def insert_align_numbers(html):
    """Attach the compiled row numbers to the actual outer MathML rows."""
    pattern = re.compile(r'<span class="aligned-equations" data-equation-rows="([^"]+)">\s*(<math\b.*?</math>)\s*</span>', re.S)
    def replace(match):
        rows = json.loads(unescape(match.group(1)))
        math = ET.fromstring(match.group(2))
        table = math.find(".//{" + MATH_NS + "}mtable")
        actual = list(table) if table is not None else []
        if len(actual) != len(rows) or any(node.tag != "{" + MATH_NS + "}mtr" for node in actual):
            raise BuildError("MathML alignment rows differ from the TeX row inventory")
        table.set("columnspacing", "0.8em")
        for node, row in zip(actual, rows):
            if len(row["labels"]) > 1:
                raise BuildError("more than one label on a math row is unsupported")
            if row["labels"]:
                node.set("id", row["labels"][0])
            cell = ET.SubElement(node, "{" + MATH_NS + "}mtd", {"class": "align-number", "columnalign": "right"})
            if row["number"]:
                node.set("data-number", row["number"])
                ET.SubElement(cell, "{" + MATH_NS + "}mtext").text = "(" + row["number"] + ")"
        ET.register_namespace("", MATH_NS)
        return '<span class="aligned-equations">' + ET.tostring(math, encoding="unicode") + "</span>"
    html = pattern.sub(replace, html)
    if "data-equation-rows=" in html:
        raise BuildError("unprocessed MathML equation numbering")
    return html


def trim_frontmatter(tex):
    """Remove only print navigation and layout; HTML supplies equivalent contents."""
    tex = re.sub(r"\\begingroup\\small\s*(?:\\linespread\{[0-9.]+\}\\selectfont\s*)?"
                 r"\\setlength\{\\parskip\}\{0pt\}\s*\\(?:tableofcontents|listoffigures)\s*\\endgroup", "", tex)
    tex = re.sub(r"\\addcontentsline\{toc\}\{(?:section|subsection)\}\{[^{}]*\}", "", tex)
    tex = re.sub(r"\\(?:maketitle|clearpage)\b", "", tex)
    tex = tex.replace(r"\thispagestyle{plain}", "").replace(r"\setcounter{tocdepth}{2}", "")
    return tex


def read_latex(preamble, tex, tools, work, name):
    # Pandoc's documented latex_macros expansion and JSON AST are used before
    # strict transforms: https://pandoc.org/MANUAL.html#extension-latex_macros
    result = chapter.run([tools["pandoc"], "--from=latex+raw_tex", "--to=json"], cwd=work,
                         log=work / "logs" / (name + "-read.log"),
                         stdin=preamble + "\n" + r"\begin{document}" + "\n" + tex + "\n" + r"\end{document}")
    if result.stderr.strip():
        raise BuildError(f"Pandoc reader warning: {name}")
    document = json.loads(result.stdout)
    abstract = document["meta"].get("abstract")
    if abstract:
        if abstract["t"] != "MetaBlocks":
            raise BuildError("unrecognized abstract representation")
        document["blocks"].insert(0, {"t": "Div", "c": [["abstract", ["abstract"], []],
            [{"t": "Header", "c": [2, ["abstract-title", ["unnumbered"], []], [literal("Abstract")]]}, *abstract["c"]]]})
    document["meta"] = {}
    return document


def write_html(document, tools, work, name):
    # MathML is local and needs no runtime CDN. A fallback warning is fatal.
    result = chapter.run([tools["pandoc"], "--from=json", "--to=html5", "--math-method=mathml",
                          "--section-divs", "--wrap=none"], cwd=work,
                         log=work / "logs" / (name + "-html.log"), stdin=json.dumps(document))
    if result.stderr.strip():
        raise BuildError(f"Pandoc MathML warning/fallback: {name}; see {work / 'logs' / (name + '-html.log')}")
    return insert_align_numbers(result.stdout)


def tools_available():
    return {name: chapter.tool(name, [f"/Library/TeX/texbin/{name}", f"/opt/homebrew/bin/{name}", f"/usr/local/bin/{name}"])
            for name in ("latexmk", "pandoc", "gs")}


def compile_book(sources, preamble, pages, tools, work, versions):
    """Only the explicit build path calls TeX; importing/testing never does."""
    snapshot = work / "snapshot"
    for name, data in sources.items():
        path = snapshot / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    pdf, aux, _ = chapter.compile_tex(snapshot / "book/main.tex", work / "pdf", tools, work / "logs", "full-book")
    figure_manifest = []
    for page in pages:
        for ordinal, match in enumerate(re.finditer(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", page["tex"], re.S), 1):
            number = len(figure_manifest) + 1
            folder = work / f"figure-{number:02d}"
            folder.mkdir(parents=True, exist_ok=True)
            tex = folder / "figure.tex"
            tex.write_text(preamble + "\n" + r"\usepackage[active,tightpage]{preview}" + "\n" +
                           r"\PreviewEnvironment{tikzpicture}\setlength\PreviewBorder{5pt}" + "\n" +
                           r"\begin{document}" + "\n" + match.group() + "\n" + r"\end{document}" + "\n")
            figure_pdf, _, _ = chapter.compile_tex(tex, folder / "pdf", tools, work / "logs", f"figure-{number:02d}")
            png = folder / "figure.png"
            chapter.run([tools["gs"], "-dSAFER", "-dBATCH", "-dNOPAUSE", "-sDEVICE=png16m", "-r240",
                         "-dFirstPage=1", "-dLastPage=1", f"-sOutputFile={png}", figure_pdf],
                        cwd=folder, log=work / "logs" / f"figure-{number:02d}-png.log")
            header = png.read_bytes()[:24]
            if header[:8] != b"\x89PNG\r\n\x1a\n":
                raise BuildError("figure renderer did not produce PNG")
            figure_manifest.append({"source": page["source"], "ordinal": ordinal,
                "tikz_sha256": digest(match.group().encode()), "file": f"assets/figure-{number:02d}.png",
                "path": str(png), "sha256": digest(png.read_bytes()), "width": int.from_bytes(header[16:20], "big"),
                "height": int.from_bytes(header[20:24], "big"), "dpi": 240})
    receipt = {"operation": OWNER, "stage": "fresh full-book and diagram compilation",
        "source_sha256": {name: digest(data) for name, data in sources.items()}, "pdf": str(pdf),
        "pdf_sha256": digest(pdf.read_bytes()), "aux": str(work / "pdf/main.aux"), "aux_sha256": digest(aux.encode()),
        "figures": figure_manifest, "tool_versions": versions}
    write_json(work / "compilation-manifest.json", receipt)
    return receipt


def verify_fresh_compilation_bytes(receipt):
    """Recheck outputs produced by this invocation, never load an input receipt."""
    files = [(receipt[role], receipt[role + "_sha256"]) for role in ("pdf", "aux")]
    files.extend((row["path"], row["sha256"]) for row in receipt["figures"])
    for name, expected in files:
        path = Path(name)
        if (any(parent.is_symlink() for parent in (path, *path.parents))
                or not path.is_file() or digest(path.read_bytes()) != expected):
            raise BuildError(f"freshly compiled artifact changed during export: {name}")


def replace_figures(page, figures):
    rows = [row for row in figures if row["source"] == page["source"]]
    matches = list(re.finditer(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", page["tex"], re.S))
    if len(rows) != len(matches):
        raise BuildError("figure receipt and chapter differ")
    tex = page["tex"]
    for row, match in reversed(list(zip(rows, matches))):
        if row["tikz_sha256"] != digest(match.group().encode()):
            raise BuildError("figure receipt does not bind the current drawing")
        tex = tex[:match.start()] + r"\includegraphics{" + row["file"] + "}" + tex[match.end():]
    return tex


def render_book(sources, receipt, tools, work, link_map):
    preamble, pages, parts, label_pages, bib = source_pages(sources)
    labels, citations = chapter.aux_maps(Path(receipt["aux"]).read_text())
    if set(labels) != set(label_pages) or set(citations) != set(bib):
        raise BuildError("compiled labels/bibliography do not match the complete source inventory")
    results, all_equations = {}, []
    for page in pages:
        tex = replace_figures(page, receipt["figures"])
        if not page["number"]:
            tex = trim_frontmatter(tex)
        document = read_latex(preamble, tex, tools, work, Path(page["file"]).stem)
        converter = BookConverter(labels, citations, label_pages, page, link_map)
        document = converter.transform(document)
        headers = list(chapter.ast_nodes(document, "Header"))
        first = next((node for node in headers if node["c"][0] == 1), None)
        if first is None:
            raise BuildError(f"chapter has no top-level heading: {page['file']}")
        page["title"] = chapter.inline_text(first["c"][2])
        page["headings"] = [{"level": node["c"][0], "id": node["c"][1][0], "title": chapter.inline_text(node["c"][2])}
                            for node in headers if node["c"][0] <= 3]
        page["math_count"] = len(list(chapter.ast_nodes(document, "Math")))
        page["table_count"] = len(list(chapter.ast_nodes(document, "Table")))
        page["figure_count"] = len(list(chapter.ast_nodes(document, "Figure")))
        source_tables = len(re.findall(r"\\begin\{(?:tabular|longtable)\}", chapter.uncomment(page["tex"])))
        source_figures = len(re.findall(r"\\begin\{figure\}", chapter.uncomment(page["tex"])))
        if page["table_count"] != source_tables or page["figure_count"] != source_figures:
            raise BuildError(f"source table/figure inventory differs: {page['file']}")
        html = write_html(document, tools, work, Path(page["file"]).stem)
        for row in receipt["figures"]:
            image = f'<img src="{row["file"]}"'
            if image in html:
                html = html.replace(image, image + f' width="{row["width"]}" height="{row["height"]}"')
        html = re.sub(r"(<table\b.*?</table>)", r'<div class="table-scroll" tabindex="0" role="region" aria-label="Scrollable table">\1</div>', html, flags=re.S)
        results[page["file"]] = html
        all_equations.extend(converter.equations)
    bib_page = {"file": "references.html", "number": "", "title": "References", "headings": []}
    converter = BookConverter(labels, citations, label_pages, bib_page, link_map)
    blocks = [{"t": "Header", "c": [1, ["references", ["unnumbered"], []], [literal("References")]]}]
    for key in sorted(bib, key=lambda k: int(citations[k])):
        document = read_latex(preamble, bib[key], tools, work, "bib-" + key)
        entry = converter.transform(document)["blocks"]
        entry[0]["c"] = [literal("[" + citations[key] + "] ")] + entry[0]["c"]
        blocks.append({"t": "Div", "c": [["ref-" + key, ["bibliography-entry"], []], entry]})
    document["blocks"] = blocks
    bib_page.update(math_count=len(list(chapter.ast_nodes(document, "Math"))), table_count=0, figure_count=0)
    results["references.html"] = write_html(document, tools, work, "references")
    pages.append(bib_page)
    return pages, parts, label_pages, labels, citations, results, all_equations


class PassageParser(preview.SearchParser):
    def __init__(self, page, title):
        super().__init__(page, title)

    def handle_endtag(self, tag):
        before = len(self.records)
        super().handle_endtag(tag)
        for row in self.records[before:]:
            row["url"] = row["url"].removeprefix("section9/")


def page_shell(title, content, *, current="", previous=None, following=None, headings=(), metadata=None):
    links = '<a href="index.html">Contents</a><a href="index.html#search">Search</a><a href="computations.html">Computational evidence</a><a href="downloads/monograph.pdf">PDF</a>'
    chapter_nav = ""
    if previous or following:
        chapter_nav = '<nav class="chapter-nav" aria-label="Chapter navigation">'
        chapter_nav += f'<a href="{previous["file"]}"><span>Previous</span>{escape(previous["title"])}</a>' if previous else "<span></span>"
        chapter_nav += f'<a href="{following["file"]}"><span>Next</span>{escape(following["title"])}</a>' if following else "<span></span>"
        chapter_nav += "</nav>"
    contents = ""
    if len(headings) > 1:
        items = "".join(f'<li class="depth-{h["level"]}"><a href="#{escape(h["id"], quote=True)}">{escape(h["title"])}</a></li>' for h in headings if h["level"] > 1)
        contents = '<details class="page-contents"><summary>On this page</summary><ol>' + items + "</ol></details>"
    credits = ""
    if metadata and metadata["author"]:
        credits = '<meta name="author" content="' + escape(metadata["author"], quote=True) + '">'
        if metadata["affiliation_lines"]:
            credits += '<meta name="affiliation" content="' + escape(" ".join(metadata["affiliation_lines"]), quote=True) + '">'
    return ('<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            + credits +
            f'<title>{escape(title)} · Polyhedra, Moduli, and Quantum Geometry</title><meta name="description" content="Complete local working edition with linked mathematics, references and bounded computational evidence.">'
            '<link rel="stylesheet" href="assets/edition.css"></head><body><a class="skip-link" href="#main">Skip to content</a>'
            '<header class="masthead"><a class="brand" href="index.html">Polyhedra, Moduli,<br>and Quantum Geometry</a><p class="edition-label">Local working edition</p>'
            f'<nav aria-label="Edition navigation">{links}</nav></header><div class="reading-layout">{contents}<main id="main">{content}{chapter_nav}</main></div>'
            '<footer><p>This local edition distinguishes proved results, conditional statements, finite checks and open questions. '
            'The computational records retain their original provenance; this edition performs no new scientific replay.</p>'
            '<p><a href="downloads/edition-manifest.json">Edition manifest</a> · <a href="downloads/monograph-source.zip">Complete TeX source</a> · '
            '<a href="downloads/inspection/LICENSES/README.md">Rights and licensing status</a></p></footer></body></html>\n')


def source_archive(path, sources):
    entries = dict(sources)
    entries["source-manifest.json"] = (json.dumps({"operation": OWNER, "source_sha256": {k: digest(v) for k, v in sources.items()},
        "scope": "Exact active TeX graph for this local working edition. No publication license is assigned."}, indent=2) + "\n").encode()
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data)


def curated_inputs(root):
    selection = json.loads((root / "site/book/downloads.json").read_text())
    paths = set(selection["inspection_files"])
    for group in selection["groups"]:
        paths.update(group["files"])
    payload = {}
    for name in sorted(paths):
        if not preview.safe_name(name) or not name.startswith(("book/", "experiments/", "artifacts/", "packages/volume-toolkit/", "LICENSES/")):
            raise BuildError(f"unapproved inspection download path: {name}")
        path = root / name
        if path.is_symlink() or not path.is_file() or any(p.is_symlink() for p in path.parents if p != root.parent):
            raise BuildError(f"missing or symlinked inspection file: {name}")
        payload[name] = path.read_bytes()
    return selection, payload


def computation_page(selection, payload):
    body = '<h1>Computational evidence</h1><p class="lede">Finite calculations, their source records, and their limits.</p>'
    body += ('<p>These downloads are unchanged recorded results and explicitly selected inspection files. '
             'No campaign is rerun by the web build. The result files retain their original source commits, dirty-state records, '
             'inputs, precision and residuals; current source downloads are identified separately by the edition manifest.</p>'
             '<p>The local selection excludes private holdouts and unclassified research outputs. No publication license is assigned '
             'to the manuscript or companion scripts. See the <a href="downloads/inspection/LICENSES/README.md">licensing scope</a>.</p>'
             '<p><a href="historical-section9/index.html">Frozen Section 9 worked example</a> · '
             '<a href="historical-section9/barrier.html">Frozen barrier examples</a> · '
             '<a href="downloads/inspection/book/computational-status.md">Complete computational status ledger</a></p>')
    for group in selection["groups"]:
        body += f'<section class="evidence-group" id="{escape(group["id"])}"><h2>{escape(group["title"])}</h2><p>{escape(group["scope"])}</p><p class="evidence-limit">{escape(group["limit"])}</p><ul>'
        for name in group["files"]:
            body += f'<li><a href="downloads/inspection/{escape(name)}">{escape(name)}</a> <span class="file-size">{len(payload[name]):,} bytes</span></li>'
        body += "</ul></section>"
    return body


def landing(pages, parts, search, source_commit, metadata, dirty=False):
    by_file = {page["file"]: page for page in pages}
    body = '<section class="edition-intro"><p class="eyebrow">A complete local working edition</p><h1>Polyhedra, Moduli,<br>and Quantum Geometry</h1><p class="subtitle">Variational principles, spectral methods, and computation</p>'
    if metadata["author"]:
        body += '<p class="byline"><span class="author">' + escape(metadata["author"]) + '</span>'
        body += "".join('<span class="affiliation">' + escape(line) + '</span>' for line in metadata["affiliation_lines"])
        body += '</p>'
    body += '<p class="lede">Read the monograph from polyhedral volume and moduli measures through quantum geometry, trace formulas, mixing and sharp counting.</p>'
    body += '<p class="edition-actions"><a class="primary-link" href="introduction.html">Start with the introduction</a><a href="downloads/monograph.pdf">Download the complete PDF</a></p></section>'
    body += '<section id="search" class="edition-search"><h2>Search the monograph</h2><form id="edition-search-form"><label for="edition-query">Find a topic, formula name, or reference</label><div class="search-controls"><input id="edition-query" type="search" autocomplete="off" placeholder="Try: Airy, Schur complement, marked torus" disabled><button type="submit" disabled>Search</button><button type="reset">Clear</button></div></form><p id="edition-search-status" role="status" aria-live="polite">Search requires JavaScript; the complete contents remain available below.</p><ol id="edition-search-results" hidden></ol></section>'
    body += '<section id="contents"><h2>Contents</h2><p><a href="introduction.html">Introduction: the connections and the results</a></p>'
    for roman, part in zip(("I", "II", "III", "IV", "V", "VI", "VII"), parts):
        body += f'<section class="contents-part"><p class="part-number">Part {roman}</p><h3>{escape(part["title"])}</h3><p>{escape(part["summary"])}</p><ol>'
        for name in part["chapters"]:
            page = by_file[name]
            body += f'<li><a href="{name}">{escape(page["title"])}</a></li>'
        body += "</ol></section>"
    body += '<div class="contents-end"><h3>Appendices and references</h3><ul>'
    for page in pages:
        if page.get("number") in ("A", "B") or page["file"] == "references.html":
            body += f'<li><a href="{page["file"]}">{escape(page["title"])}</a></li>'
    body += '</ul></div></section><section class="edition-note"><h2>About this edition</h2><p>All chapters, proofs, appendices, bibliography, tables and diagrams are converted from the canonical TeX source. '
    body += 'The <a href="computations.html">computational evidence index</a> records the distinct scope of each maintained companion. '
    body += 'The <a href="historical-section9/chapter.html">earlier Section 9 edition</a> remains a separate frozen checkpoint, including its older source archive.</p>'
    dirty_note = " with uncommitted local changes (author preview)" if dirty else ""
    body += f'<p>Manuscript date: {escape(metadata["date"])}. Research checkout commit <code>{escape(source_commit)}</code>{dirty_note}. This is local preparation; no upload or deployment is performed.</p></section>'
    body += '<script id="edition-search-data" type="application/json">' + preview.embedded_json(search) + '</script><script src="assets/search.js" defer></script>'
    return body


def check_output(output):
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise BuildError("output must be an ordinary directory")
    files = preview.ordinary_files(output)
    if not files:
        return
    manifest_path = output / "downloads/edition-manifest.json"
    if not manifest_path.is_file():
        raise BuildError("refusing to overwrite foreign output")
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("operation") != OWNER:
        raise BuildError("output is not owned by the complete-edition builder")
    expected = manifest.get("output_sha256", {})
    if set(files) != set(expected) | {"downloads/edition-manifest.json"}:
        raise BuildError("existing output inventory differs from its manifest")
    for name, sha in expected.items():
        if digest(files[name].read_bytes()) != sha:
            raise BuildError(f"refusing to overwrite modified output: {name}")


def validate_output(output, pages, label_pages, labels, citations, equations, search):
    parsed = {}
    for name, path in preview.ordinary_files(output).items():
        if name.endswith(".html"):
            audit = chapter.HTMLAudit()
            audit.feed(path.read_text())
            if len(audit.ids) != len(set(audit.ids)):
                raise BuildError(f"duplicate HTML anchors: {name}")
            if audit.remote_dependencies:
                raise BuildError(f"external runtime dependency: {name}")
            parsed[name] = audit
    for label, page in label_pages.items():
        if label not in parsed[page].ids:
            raise BuildError(f"source label lost: {label}")
    for key in citations:
        if "ref-" + key not in parsed["references.html"].ids:
            raise BuildError(f"bibliography entry lost: {key}")
    for page in pages:
        audit = parsed[page["file"]]
        if audit.math != page["math_count"] or len(audit.images) != page["figure_count"]:
            raise BuildError(f"math/figure inventory differs: {page['file']}")
        if (output / page["file"]).read_text().count("<table") != page["table_count"]:
            raise BuildError(f"table inventory differs: {page['file']}")
    for row in equations:
        if row["number"] != labels[row["label"]]["number"]:
            raise BuildError("equation numbering differs from the compiled book")
    links = [(name, href) for name, audit in parsed.items() for href in audit.links]
    links.extend(("index.html", row["url"]) for row in search["records"])
    for name, href in links:
        url = urlsplit(href)
        if url.scheme or url.netloc:
            if url.scheme not in ("http", "https", "mailto"):
                raise BuildError(f"unsupported URL: {href}")
            continue
        path = ((output / name).parent / unquote(url.path)).resolve() if url.path else output / name
        if not path.is_relative_to(output) or not path.is_file():
            raise BuildError(f"missing or escaping local link: {name}: {href}")
        relative = path.relative_to(output).as_posix()
        if url.fragment and relative in parsed and unquote(url.fragment) not in parsed[relative].ids:
            raise BuildError(f"unresolved local fragment: {name}: {href}")
    return {"html_pages": len(parsed), "book_pages": len(pages), "source_labels": len(label_pages),
            "bibliography_entries": len(citations), "mathml_nodes": sum(page["math_count"] for page in pages),
            "figures": sum(page["figure_count"] for page in pages), "tables": sum(page["table_count"] for page in pages),
            "local_links_and_search_targets": len(links), "search_passages": len(search["records"]),
            "browser_verification": "not performed by this builder; static checks are separate"}


def normalized_directory(path):
    """Reject symlink aliases before normalizing dot segments for path guards."""
    supplied = Path(path).absolute()
    if any(parent.is_symlink() for parent in (supplied, *supplied.parents)):
        raise BuildError("build/output path has a symlink ancestor")
    return supplied.resolve()


def build(root, output, work, *, require_clean=False):
    root = Path(root).resolve()
    output, work = normalized_directory(output), normalized_directory(work)
    if root != ROOT.resolve():
        raise BuildError("builder must belong to the selected research checkout")
    for path in (output, work):
        if path.is_relative_to(root):
            raise BuildError("build/output must be outside the research checkout without symlink ancestors")
    if output == work or output.is_relative_to(work) or work.is_relative_to(output):
        raise BuildError("output and build scratch directories must be disjoint")
    check_output(output)
    state = preview.git_state(root)
    if require_clean and state["dirty"]:
        raise BuildError("final export requires a clean research checkout")
    sources = chapter.source_graph(root)
    preamble, pages, _, _, _ = source_pages(sources)
    metadata = canonical_metadata(preamble)
    selection, payload = curated_inputs(root)
    historical = preview.load_inputs(root)
    inputs = {**sources, **payload,
        **{str(path.relative_to(root)): path.read_bytes() for path in (root / "site/book").iterdir() if path.is_file() and not path.name.startswith(".")},
        "site/build_book.py": Path(__file__).read_bytes(), "site/build_section9.py": (root / "site/build_section9.py").read_bytes(),
        "site/build_preview.py": (root / "site/build_preview.py").read_bytes()}
    tools = tools_available()
    if work.exists() and not work.is_dir():
        raise BuildError("build scratch must be an ordinary directory")
    existing_work = preview.ordinary_files(work)
    marker = work / "build-owner.json"
    if existing_work or (work.exists() and any(work.iterdir())):
        raise BuildError("every build requires a new empty scratch directory for fresh compilation")
    work.mkdir(parents=True, exist_ok=True)
    write_json(marker, {"operation": OWNER, "research_root": str(root)})
    versions = {}
    for name, executable in tools.items():
        version = chapter.run([executable, "-version" if name == "latexmk" else "--version"], cwd=work,
                              log=work / "logs" / (name + "-version.log")).stdout.strip()
        versions[name] = {"executable": executable, "version": version if name == "latexmk" else version.splitlines()[0]}
    receipt = compile_book(sources, preamble, pages, tools, work, versions)
    destination = output
    output = work / "export-staging"
    if output.exists():
        shutil.rmtree(output)
    (output / "downloads").mkdir(parents=True)
    (output / "assets").mkdir()
    for name, data in payload.items():
        path = output / "downloads/inspection" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for name, data in historical[2].items():
        if not name.startswith("site/section9/"):
            continue
        path = output / "historical-section9" / name.removeprefix("site/section9/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    for row in receipt["figures"]:
        data = Path(row["path"]).read_bytes()
        if digest(data) != row["sha256"]:
            raise BuildError("figure changed after compilation")
        (output / row["file"]).write_bytes(data)
    pdf_data = Path(receipt["pdf"]).read_bytes()
    if digest(pdf_data) != receipt["pdf_sha256"]:
        raise BuildError("PDF changed after compilation")
    (output / "downloads/monograph.pdf").write_bytes(pdf_data)
    source_archive(output / "downloads/monograph-source.zip", sources)
    for name in ("edition.css", "search.js"):
        (output / "assets" / name).write_bytes(inputs["site/book/" + name])
    link_map = {"../" + name: "downloads/inspection/" + name for name in payload}
    link_map.update({name.removeprefix("book/"): "downloads/inspection/" + name for name in payload if name.startswith("book/")})
    for name in historical[2]:
        if name.startswith("site/section9/"):
            link_map["../" + name] = "historical-section9/" + name.removeprefix("site/section9/")
    pages, parts, label_pages, labels, citations, rendered, equations = render_book(sources, receipt, tools, work, link_map)
    records = []
    for index, page in enumerate(pages):
        parser = PassageParser(page["file"], page["title"])
        parser.feed(rendered[page["file"]])
        records.extend(parser.records)
        html = page_shell(page["title"], rendered[page["file"]], current=page["file"],
            previous=pages[index - 1] if index else None, following=pages[index + 1] if index + 1 < len(pages) else None,
            headings=page["headings"], metadata=metadata)
        (output / page["file"]).write_text(html)
    search = {"schema_version": 1, "scope": "Complete monograph, appendices and bibliography", "records": records}
    write_json(output / "search-index.json", search)
    (output / "index.html").write_text(page_shell("Contents", landing(pages, parts, search, state["commit"], metadata, state["dirty"]), metadata=metadata))
    (output / "computations.html").write_text(page_shell("Computational evidence", computation_page(selection, payload), metadata=metadata))
    # Reserve the manifest target before link validation. The final manifest owns
    # all other output bytes; its self-hash is intentionally not recursive.
    write_json(output / "downloads/edition-manifest.json", {})
    checks = validate_output(output.resolve(), pages, label_pages, labels, citations, equations, search)
    for name, data in inputs.items():
        if (root / name).read_bytes() != data:
            raise BuildError(f"source changed during the build: {name}")
    preview.load_inputs(root)
    verify_fresh_compilation_bytes(receipt)
    if json.loads((work / "compilation-manifest.json").read_text()) != receipt:
        raise BuildError("compilation receipt changed during the export")
    if preview.git_state(root) != state:
        raise BuildError("research Git state changed during the build")
    manifest = {"schema_version": 1, "operation": OWNER, "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_source": state, "source_sha256": {name: digest(data) for name, data in sources.items()},
        "input_sha256": {name: digest(data) for name, data in inputs.items()},
        "historical_section9_sha256": {name: digest(data) for name, data in historical[2].items()},
        "historical_section9_checkpoint_sha256": digest(historical[1]),
        "compilation": receipt, "canonical_metadata": metadata, "tool_versions": versions, "verification": checks,
        "label_pages": label_pages, "label_numbers": {key: row["number"] for key, row in labels.items()},
        "bibliography_numbers": citations, "scientific_replay": "not performed; all reports copied unchanged",
        "rights": "Local working edition. Manuscript and new companion publication rights remain unresolved.",
        "publication": "not performed; no Site registration, source synchronization, upload or deployment",
        "output_sha256": {name: digest(path.read_bytes()) for name, path in preview.ordinary_files(output).items()
                          if name != "downloads/edition-manifest.json"}}
    write_json(output / "downloads/edition-manifest.json", manifest)
    # Only a completely checked staging tree replaces a verified prior export.
    check_output(destination)
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(output), str(destination))
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    try:
        result = build(ROOT, args.output_dir, args.work_dir, require_clean=args.require_clean)
    except (BuildError, preview.PreviewError) as error:
        parser.exit(1, f"complete edition build failed: {error}\n")
    print(json.dumps(result["verification"], indent=2))


if __name__ == "__main__":
    main()
