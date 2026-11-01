"""Read-only preservation checks for the manuscript integration overlay."""
from pathlib import Path
import hashlib
import json
import re

work = Path(__file__).resolve().parent
root = work.parents[2] / "consolidated"
before = json.loads((work / "baseline-manifest.json").read_text())
drift = [p for p, v in before["files"].items()
         if hashlib.sha256((root / p).read_bytes()).hexdigest() != v["sha256"]]


def expand(path, overlay=False, graph=None):
    graph = set() if graph is None else graph
    graph.add(str(path.relative_to(root)))
    rel = path.relative_to(root)
    candidate = work / "proposals" / rel
    text = (candidate if overlay and candidate.exists() else path).read_text()

    def included(match):
        target = root / "book" / match[1]
        if target.suffix != ".tex":
            target = target.with_suffix(".tex")
        return expand(target, overlay, graph)[0]

    return re.sub(r"\\input\{([^}]+)\}", included, text), graph


a, graph_a = expand(root / "book/main.tex")
b, graph_b = expand(root / "book/main.tex", True)
labels = lambda s: re.findall(r"\\label\{([^}]+)\}", s)
bibs = lambda s: re.findall(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", s)
report = {
    "canonical_snapshot_drift": drift,
    "canonical_labels": len(labels(a)),
    "proposal_labels": len(labels(b)),
    "labels_order_identical": labels(a) == labels(b),
    "canonical_bibkeys": len(bibs(a)),
    "proposal_bibkeys": len(bibs(b)),
    "bibkey_order_identical": bibs(a) == bibs(b),
    "active_tex_source_files": len(graph_b),
    "active_tex_source_graph_identical": graph_a == graph_b,
    "main_source_and_bibliography_edited_by_proposal": False,
}
assert not drift
assert report["canonical_labels"] == report["proposal_labels"] == 607
assert report["canonical_bibkeys"] == report["proposal_bibkeys"] == 129
assert report["labels_order_identical"] and report["bibkey_order_identical"]
assert report["active_tex_source_files"] == 26
assert report["active_tex_source_graph_identical"]
(work / "proposal-preservation-check.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
