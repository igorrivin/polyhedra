"""Accept only the declared two-pin repair; retain the initial evidence."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


OUTER = Path(__file__).resolve().parent
ROOT = OUTER.parents[2] / "consolidated"
AUTHOR = OUTER.parent / "quantum-author"
V2 = AUTHOR / "revision-v2"
INITIAL = OUTER / "initial-author-freeze"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


expected_subjects = {
    "book/chapters/10-quantum-introduction.tex":
        "010a50a8f5205255bef2417f76515fff8962a443ea835c30bfcee02846c5ebfb",
    "book/chapters/11-quantum-degeneration.tex":
        "5a62080dbc2320f57efec073aa803cdff20dd06c05529dc7e064346cf0f47db9",
    "book/claims/sections10-11.json":
        "34dbb6255dc468cb796bb3a129eeaf37ac0c5f4dc358abfd73030e64331b3539",
}
added = {
    "book/chapters/03-ideal-tetrahedron.tex":
        "81c51ade3378fbfd4baff1cebeb2dcdd8b0fd43a032ac45fb3b30c4908060797",
    "book/claims/sections7-8.json":
        "7438f1b5c8fde23fa81b0b1c3250d2965debf79678026d649bd7ff7cd368439d",
}
assert sha(V2 / "freeze-manifest.json") == (
    "f043f6943bd124638802bfdb5d5e7505269143f54046eea93d298345191c0620"
)
assert sha(AUTHOR / "freeze-manifest.json") == (
    "107eda60080662c39b747bfa98fbbca765c2e3fa18b6d161960057128dfe1456"
)
assert sha(AUTHOR / "handoff-evidence-hashes.json") == (
    "ac70f770daa0912a229c77c3a66491cb4170b27d77f8dfcf264d6d2e356cd270"
)
for path, expected in expected_subjects.items():
    assert sha(ROOT / path) == expected, path
    if path.endswith(".tex"):
        assert (ROOT / path).read_bytes() == (INITIAL / path).read_bytes()

ledger_path = "book/claims/sections10-11.json"
before_bytes = (INITIAL / ledger_path).read_bytes()
after_bytes = (ROOT / ledger_path).read_bytes()
assert before_bytes == (V2 / "ledger-before.json").read_bytes()
assert after_bytes == (V2 / "ledger-after.json").read_bytes()
stripped = after_bytes
for path, digest in added.items():
    line = f'    "{path}": "{digest}",\n'.encode()
    assert stripped.count(line) == 1
    stripped = stripped.replace(line, b"", 1)
assert stripped == before_bytes, "Delta is not exactly the two declared lines"
before = json.loads(before_bytes)
after = json.loads(after_bytes)
assert len(after["claims"]) == 61
assert after["claims"] == before["claims"]
before_other = {k: v for k, v in before.items() if k != "reviewed_dependency_sha256"}
after_other = {k: v for k, v in after.items() if k != "reviewed_dependency_sha256"}
assert before_other == after_other
expected_dependencies = before["reviewed_dependency_sha256"] | added
assert after["reviewed_dependency_sha256"] == expected_dependencies
assert len(expected_dependencies) == 11
dependency_checks = {}
for path, expected in expected_dependencies.items():
    actual = sha(ROOT / path)
    assert actual == expected, path
    dependency_checks[path] = actual
manifest = read_json(V2 / "freeze-manifest.json")
assert {row["path"]: row["sha256"] for row in manifest["canonical_files"]} == expected_subjects
assert manifest["reviewed_dependency_sha256"] == expected_dependencies

final_copy = OUTER / "final-author-freeze"
assert not final_copy.exists(), "Do not overwrite a prior final acceptance freeze"
final_copy.mkdir()
for name in ("freeze-manifest.json", "handoff.md", "ledger.patch", "validation.json"):
    shutil.copy2(V2 / name, final_copy / name)
for path in expected_subjects:
    target = final_copy / path
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / path, target)
    assert sha(target) == expected_subjects[path]

sources = read_json(OUTER / "independent-source-review.json")
source_counts = dict(Counter(row["access_status"] for row in sources["source_records"]))
record = {
    "status": "independent_exact_byte_acceptance",
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "reviewer": "quantum_background_reviewer",
    "accepted_canonical_sha256": expected_subjects,
    "accepted_author_freeze_sha256": sha(V2 / "freeze-manifest.json"),
    "accepted_author_handoff_sha256": sha(V2 / "handoff.md"),
    "initial_ledger_sha256": hashlib.sha256(before_bytes).hexdigest(),
    "initial_freeze_preserved": True,
    "repair_delta": "Exactly two inserted dependency-hash lines; no other ledger-byte changes.",
    "mathematical_claims_and_chapter_bytes_unchanged": True,
    "all_live_dependency_sha256": dependency_checks,
    "claim_count": 61,
    "preserved_label_count": 48,
    "source_review_counts": source_counts,
    "findings": [{"id": "QR01", "status": "resolved_by_independently_verified_metadata_repair"}],
    "required_open_findings": [],
    "independent_probes_reused_without_rerun": {
        "reason": "Only dependency metadata changed; mathematical statements and both source hashes are identical.",
        "script_sha256": sha(OUTER / "independent_probes.py"),
        "result_sha256": sha(OUTER / "independent-probe-results.json"),
    },
    "companion_status": "Mathematical specification accepted; maintained implementation and execution not yet reviewed.",
    "source_review_limit": "Selected external statements inspected; no full external proof or external PDF byte hash claimed; one source unavailable and two checked only at metadata/abstract level.",
    "scope": "Source/claim-ledger approval only; no canonical edit by reviewer, commit, build, installation, upload or global computational certification.",
}
(OUTER / "final-acceptance.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({
    "status": record["status"],
    "ledger_sha256": expected_subjects[ledger_path],
    "dependencies": len(dependency_checks),
    "claims": 61,
    "labels": 48,
    "open_findings": [],
}, indent=2))
