"""Strict author/reviewer scientific comparison, with explicit metadata exclusions."""
from pathlib import Path
import hashlib
import json

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "computation-review"
REPO = BASE.parent.parent / "consolidated"
author = json.loads((BASE / "computation/author-result-60-90.json").read_text())
reviewer = json.loads((OUT / "reviewer-result-60-90.json").read_text())
exclusions = {
    "/generated_at_utc", "/elapsed_seconds", "/source/git_dirty",
    "/source/git_status_porcelain", "/source_at_completion/git_dirty",
    "/source_at_completion/git_status_porcelain",
}
differences, excluded = [], []


def compare(a, b, path=""):
    if path in exclusions:
        if a != b:
            excluded.append({"path": path, "author": a, "reviewer": b})
        return
    if type(a) is not type(b):
        differences.append({"path": path, "author": a, "reviewer": b})
    elif isinstance(a, dict):
        if a.keys() != b.keys():
            differences.append({"path": path, "keys_author": list(a), "keys_reviewer": list(b)})
        for key in a.keys() & b.keys():
            compare(a[key], b[key], path + "/" + str(key))
    elif isinstance(a, list):
        if len(a) != len(b):
            differences.append({"path": path, "length_author": len(a), "length_reviewer": len(b)})
        for i, (x, y) in enumerate(zip(a, b)):
            compare(x, y, path + "/" + str(i))
    elif a != b:
        differences.append({"path": path, "author": a, "reviewer": b})


compare(author, reviewer)
chapter_text = "\n".join(
    path.read_text() for path in (REPO / "book/chapters").glob("*.tex")
    if not path.name.startswith(".")
)
labels = [
    {"label": label, "present": "\\label{" + label + "}" in chapter_text}
    for row in reviewer["fixture"]["formula_contracts"].values()
    if isinstance(row, dict) and "labels" in row for label in row["labels"]
]
contracts = [
    {"path": path, "expected": digest,
     "actual": hashlib.sha256((BASE / path).read_bytes()).hexdigest()}
    for path, digest in reviewer["fixture"]["formula_contracts"]["author_contract_sha256"].items()
]
result = {
    "status": "pass" if not differences and all(x["present"] for x in labels)
    and all(x["expected"] == x["actual"] for x in contracts) else "fail",
    "comparison": "Strict JSON equality at every nonexcluded path, including numerical strings, "
    "residuals, observations, formulas, precision data, counts, source hashes, HEAD, runtime versions, and limits.",
    "declared_exclusions": sorted(exclusions), "excluded_differences": excluded,
    "scientific_differences": differences, "label_checks": labels, "contract_hash_checks": contracts,
    "reviewer_result_sha256": hashlib.sha256((OUT / "reviewer-result-60-90.json").read_bytes()).hexdigest(),
}
(OUT / "strict-comparison.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": result["status"], "scientific_differences": len(differences),
                  "excluded_differences": len(excluded), "labels": len(labels), "contracts": len(contracts)}))
assert result["status"] == "pass"
