"""Apply only the root-authorized integration files after all frozen gates."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import shutil

work = Path(__file__).resolve().parent
root = work.parents[2] / "consolidated"
review = work.parent / "computation-review/revision-v2/approved-manifest-v2.json"
expected_review_sha = "c059cf9591f534bb6517486389b111c79fdff77531b192cbfab846021bd6536e"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(review) == expected_review_sha
approval = json.loads(review.read_text())
assert approval["approved"] and not approval["open_findings"]
assert approval["approved_source_set_sha256"] == "4b1f8f22f155c464f0ecda6ab95c581926db157bae4ee7583e67fbc6448ded63"
for item in approval["approved_sources"]:
    assert sha(root / item["path"]) == item["sha256"], item["path"]

baseline = json.loads((work / "baseline-manifest.json").read_text())["files"]
proposal = json.loads((work / "proposal-manifest.json").read_text())
assert set(baseline) == set(proposal["files"])
assert len(baseline) == 18
assert not (work / "applied-source-manifest.json").exists()
for rel, item in proposal["files"].items():
    assert sha(root / rel) == baseline[rel]["sha256"] == item["before_sha256"], rel
    assert sha(work / "proposals" / rel) == item["proposal_sha256"], rel

protected_paths = {"book/main.tex", "book/polyhedral_volumes_and_geodesic_identities.tex", "artifacts/section30/result.json"}
for folder in ["experiments/counting_mixing", "experiments/torus_campaign", "experiments/section30"]:
    protected_paths.update(str(p.relative_to(root)) for p in (root / folder).rglob("*")
                           if p.is_file() and not p.name.startswith("._")
                           and p.suffix in {".py", ".cpp", ".json", ".md"})
protected_before = {p: sha(root / p) for p in sorted(protected_paths)}


def expand(path, snapshot=False, graph=None):
    graph = set() if graph is None else graph
    rel = str(path.relative_to(root))
    graph.add(rel)
    snapshot_path = work / "snapshots/before" / rel
    text = (snapshot_path if snapshot and snapshot_path.exists() else path).read_text()

    def included(match):
        target = root / "book" / match[1]
        if target.suffix != ".tex":
            target = target.with_suffix(".tex")
        return expand(target, snapshot, graph)[0]

    return re.sub(r"\\input\{([^}]+)\}", included, text), graph


expanded_before, graph_before = expand(root / "book/main.tex")
changed = [rel for rel, item in proposal["files"].items() if item["changed"]]
assert len(changed) == 13
for rel in changed:
    shutil.copyfile(work / "proposals" / rel, root / rel)

expanded_after, graph_after = expand(root / "book/main.tex")
labels = lambda s: re.findall(r"\\label\{([^}]+)\}", s)
bibs = lambda s: re.findall(r"\\bibitem(?:\[[^]]*\])?\{([^}]+)\}", s)
assert labels(expanded_before) == labels(expanded_after)
assert len(labels(expanded_after)) == 607
assert bibs(expanded_before) == bibs(expanded_after)
assert len(bibs(expanded_after)) == 129
assert graph_before == graph_after and len(graph_after) == 26
protected_after = {p: sha(root / p) for p in sorted(protected_paths)}
assert protected_before == protected_after

claim_counts = {}
proof_blocks_preserved = {}
for rel in baseline:
    assert sha(root / rel) == proposal["files"][rel]["proposal_sha256"], rel
    old = (work / "snapshots/before" / rel).read_text()
    new = (root / rel).read_text()
    if rel.startswith("book/claims/"):
        left, right = json.loads(old), json.loads(new)
        invariants = lambda d: [(c["id"], c.get("labels", []), c["status"]) for c in d["claims"]]
        assert invariants(left) == invariants(right), rel
        claim_counts[rel] = len(right["claims"])
    if rel.endswith(".tex"):
        blocks = lambda s: re.findall(r"\\begin\{(proof|theorem|lemma|proposition|corollary)\}.*?\\end\{\1\}", s, re.S)
        # Capture the complete blocks, not only their environment names.
        full_blocks = lambda s: [m.group(0) for m in re.finditer(r"\\begin\{(proof|theorem|lemma|proposition|corollary)\}.*?\\end\{\1\}", s, re.S)]
        assert full_blocks(old) == full_blocks(new), rel
        proof_blocks_preserved[rel] = len(full_blocks(new))
assert sum(claim_counts.values()) == 168

preservation = {
    "canonical_labels": 607,
    "labels_order_identical": True,
    "canonical_bibkeys": 129,
    "bibkey_order_identical": True,
    "active_tex_source_files": 26,
    "active_tex_source_graph_identical": True,
    "claim_counts": claim_counts,
    "total_claims": 168,
    "claim_ids_labels_statuses_preserved": True,
    "unchanged_proof_and_formal_statement_blocks": proof_blocks_preserved,
    "protected_source_and_old_artifact_hashes_identical": protected_before == protected_after,
    "protected_files": protected_after,
    "scope": "Source and metadata preservation only. No build, numerical replay, final artifact generation, commit or upload was performed.",
}
(work / "applied-preservation-check.json").write_text(json.dumps(preservation, indent=2) + "\n")
shutil.copyfile(work / "proposal.diff", work / "applied-source.diff")
manifest = {
    "applied_at_utc": datetime.now(timezone.utc).isoformat(),
    "authorization": "Root GO after independent finite-companion v2 acceptance; eighteen assigned paths only.",
    "status": "applied_for_independent_integration_review",
    "finite_companion_approval_manifest_sha256": expected_review_sha,
    "files": {rel: {**item, "canonical_sha256": sha(root / rel)} for rel, item in proposal["files"].items()},
    "changed_files": changed,
    "changed_file_count": len(changed),
    "unchanged_assigned_file_count": len(baseline) - len(changed),
    "applied_diff_sha256": sha(work / "applied-source.diff"),
    "preservation_check_sha256": sha(work / "applied-preservation-check.json"),
    "future_artifact_paths": ["artifacts/counting_mixing/result.json", "artifacts/torus_campaign/result.json", "artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf"],
    "future_checkpoint_path": "docs/execution/counting-mixing-review-2026-11-01/",
}
(work / "applied-source-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps({"status": manifest["status"], "changed_files": changed, "labels": 607, "bibliography_keys": 129, "claims": 168, "active_tex_files": 26}, indent=2))
