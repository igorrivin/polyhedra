#!/usr/bin/env python3
"""Verify the counting/mixing checkpoint; never compute, build, commit or clean.

This prepared template deliberately rejects an unfinalized contract. Finalize
the contract from exact independent approvals after integration and replay.
The contract and this program belong in the candidate artifact manifest; that
manifest excludes its own hash. Independent receipts remain outside canonical.
Patterns: docs/execution/section15-analytic-review-2026-11-01/verify_checkpoint.py.
"""
from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlsplit

from checkpoint_lib import (
    BASELINE, ENV, PDF, REL, RESULTS, commit_blob, counting_comparison, digest,
    encode, external_inputs_unchanged, fsck, get_pointer, git, identity, json_snapshot, load_json, merge_hashes,
    outer_path, receipt_record, relative_path, repository, require, require_unchanged,
    torus_raw_comparison, torus_report_comparison,
)
from source_approval_adapter import approved_source_map
from candidate_receipt_adapter import verify_source_receipts, verify_pdf_receipts

MANIFEST = REL + "/candidate-artifact-manifest.json"
COPY_MANIFEST = REL + "/evidence-copy-manifest.json"
CONTRACT = REL + "/checkpoint-contract.json"


def approved_contract(root, config):
    require(config["schema_version"] == 1 and config["ready"] is True,
            "checkpoint contract is unfinished; final approvals/replays are required")
    require(type(config.get("unresolved")) is list and config["unresolved"] == [],
            "checkpoint contract requires explicit empty unresolved list")
    require(config["baseline_commit"] == BASELINE, "wrong baseline")
    source = config["source_commit"]
    require(isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source), "missing source commit")
    approved = config["approved_source_sha256"]
    require(approved and all(re.fullmatch(r"[0-9a-f]{64}", v) for v in approved.values()), "missing approved sources")
    require(all(not p.startswith(("artifacts/", "site/", "research/", "packages/", "provenance/", "docs/execution/"))
                for p in approved), "source checkpoint may not change historical evidence/imports")
    require(git(root, "rev-list", "--parents", "-n", "1", source).decode().split() == [source, BASELINE],
            "source must be the baseline's direct child")
    require({row["role"] for row in config["approval_pins"]} == {
        "algebra", "dynamics", "arithmetic", "counting", "integration"}, "five approval roles required")
    require(len(config["approval_pins"]) == 5, "duplicate approval role")
    for pin in config["approval_pins"]:
        p = relative_path(root, REL + "/" + pin["path"])
        require(identity(p) == pin["identity"], "approval receipt identity: " + pin["role"])
        record = load_json(p)
        require(pin["required_values"], "approval decision constraints must be explicit")
        for pointer, expected in pin["required_values"].items():
            require(encode(get_pointer(record, pointer)) == encode(expected), "approval condition failed: " + pointer)
        if pin["role"] == "integration":
            require(approved_source_map(record, pin) == approved, "final integrated source approval differs")
    for path, expected in approved.items():
        require(digest(relative_path(root, path)) == sha256(commit_blob(root, source, path)).hexdigest() == expected,
                "approved working/source-commit bytes differ: " + path)
    return source, approved


def source_checkpoint_receipts(root, source, approved, config):
    outer = root.parent / "execution/counting-mixing-review-2026-11-01"
    return verify_source_receipts(root, outer, source, approved, config)


def tree(root, commit):
    entries = {}
    for row in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if row:
            fields, raw_path = row.split(b"\t", 1)
            mode, kind, oid = fields.split()
            require(kind == b"blob", "non-blob tree entry")
            entries[raw_path.decode()] = (mode.decode(), oid.decode())
    return entries


def preservation(root, outer, source, approved, config):
    old, current = tree(root, BASELINE), tree(root, source)
    require(len(old) == 1914, "baseline must contain 1914 tracked files")
    expected_changes = {p: "M" if p in old else "A" for p in approved}
    actual_changes = {}
    for row in git(root, "diff", "--no-renames", "--name-status", BASELINE, source).decode().splitlines():
        status, path = row.split("\t")
        actual_changes[path] = status
    require(actual_changes == expected_changes, "source commit differs from reviewed path allowlist")
    require(set(current) == set(old) | set(approved), "source tree added or removed undeclared paths")
    require(all(current[p][0] == old[p][0] for p in old), "baseline file mode changed")
    require(all(current[p][0] == "100644" for p in set(approved) - set(old)), "new source mode is not regular 100644")
    require(all(current[p] == old[p] for p in set(old) - set(approved)), "protected baseline Git object changed")
    inventory = load_json(root / REL / "structure/baseline-tracked-inventory.json")
    require(inventory["baseline_commit"] == BASELINE and len(inventory["files"]) == 1914, "baseline inventory scope")
    indexed = {row["path"]: row for row in inventory["files"]}
    require(len(indexed) == 1914 and set(indexed) == set(old), "baseline inventory path mismatch")
    protected = [p for p in old if p not in approved]
    result = subprocess.run(["git", "cat-file", "--batch"], cwd=root, env=ENV,
                            input=("\n".join(old[p][1] for p in protected) + "\n").encode(),
                            capture_output=True, check=False)
    require(result.returncode == 0 and not result.stderr, "baseline blob batch failed")
    offset, lfs = 0, 0
    for p in protected:
        row = indexed[p]
        require((row["git_mode"], row["git_blob"]) == old[p], "baseline inventory Git identity: " + p)
        end = result.stdout.index(b"\n", offset)
        oid, kind, length = result.stdout[offset:end].split()
        size, start = int(length), end + 1
        blob = result.stdout[start:start + size]
        require(oid.decode() == old[p][1] and kind == b"blob" and result.stdout[start + size:start + size + 1] == b"\n",
                "cat-file framing/identity")
        offset = start + size + 1
        path = relative_path(root, p)
        if row["git_mode"] == "120000":
            data = os.readlink(path).encode()
            actual = {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
        else:
            actual = identity(path)
        require(actual == {"sha256": row["sha256"], "bytes": row["bytes"]}, "protected working file changed: " + p)
        pointer = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", blob)
        if pointer:
            require(actual == {"sha256": pointer[1].decode(), "bytes": int(pointer[2])}, "materialized LFS identity: " + p)
            lfs += 1
        else:
            require(actual == {"sha256": sha256(blob).hexdigest(), "bytes": len(blob)}, "protected committed blob differs: " + p)
    require(offset == len(result.stdout) and lfs == 412, "baseline batch framing/LFS count")
    original_path = root.parent / "audit/2026-10-31/source-inventory.json"
    require(identity(original_path) == config["original_inventory_identity"], "original inventory identity")
    originals = load_json(original_path)
    n = 0
    for repo in originals["repositories"]:
        directory = root.parent / repo["path"]
        require(git(directory, "rev-parse", "HEAD").decode().strip() == repo["head"], "original repository HEAD changed")
        require(not git(directory, "status", "--porcelain=v1", "--untracked-files=all"), "original repository dirty")
        git(root, "merge-base", "--is-ancestor", repo["head"], source)
        for row in repo["files"]:
            require(identity(relative_path(directory, row["path"])) == {"sha256": row["sha256"], "bytes": row["bytes"]},
                    "preserved original file changed: " + row["path"])
            n += 1
    require(n == 953, "953 original files required")
    archive = originals["monograph_archive"]
    require(identity(root.parent / archive["path"]) == {"sha256": archive["sha256"], "bytes": archive["bytes"]}, "original ZIP changed")
    return {"baseline_tracked_files": len(old), "protected_baseline_files": len(protected),
            "source_tracked_files": len(current), "materialized_LFS_files": lfs, "original_files": n}


def freeze_controls(root):
    frozen = {}
    for name in (CONTRACT, MANIFEST, COPY_MANIFEST):
        data, frozen_identity = json_snapshot(root / name)
        frozen[name] = {"data": data, "identity": frozen_identity}
    frozen["paths"] = frozenset(frozen[MANIFEST]["data"]["files"]) | {MANIFEST}
    controls_unchanged(root, frozen)
    return frozen


def controls_unchanged(root, frozen):
    for name in (CONTRACT, MANIFEST, COPY_MANIFEST):
        require_unchanged(root / name, frozen[name]["identity"], "frozen checkpoint control " + name)


def artifacts(root, outer, source, approved, config, candidate, frozen):
    controls_unchanged(root, frozen)
    manifest = frozen[MANIFEST]["data"]
    require(manifest["baseline_commit"] == BASELINE and manifest["source_commit"] == source, "candidate manifest ancestry")
    require(MANIFEST not in manifest["files"], "candidate manifest may not hash itself")
    paths = frozen["paths"]
    expected = {str(p.relative_to(root)) for p in (root / REL).rglob("*")
                if p.is_file() and not p.name.startswith("._")}
    expected.update({*RESULTS.values(), PDF})
    require(paths == expected, "candidate artifact inventory differs from allowlist")
    require(not set(approved) & paths, "source and artifact commit allowlists overlap")
    require(not git(root, "diff", "--cached", "--name-only"), "index must be empty for verification")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    head_tree = tree(root, head)
    if candidate:
        require(head == source and not git(root, "diff", "--name-only"), "candidate requires source HEAD with unchanged tracked files")
        require(set(git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()) == paths,
                "candidate untracked files differ from artifact manifest")
    else:
        require(git(root, "rev-list", "--parents", "-n", "1", head).decode().split() == [head, source], "artifact commit must be source's direct child")
        require(not git(root, "status", "--porcelain=v1", "--untracked-files=all"), "postcommit state must be clean")
        changes = git(root, "diff", "--no-renames", "--name-status", source, head).decode().splitlines()
        require(set(changes) == {"A\t" + p for p in paths}, "artifact commit must only add manifest paths")
    for p in paths:
        path = relative_path(root, p)
        if p != MANIFEST:
            require(identity(path) == manifest["files"][p], "candidate identity mismatch: " + p)
        if not candidate:
            require(head_tree[p][0] == "100644", "artifact file mode")
            require(commit_blob(root, head, p) == path.read_bytes(), "committed artifact bytes differ: " + p)
    copies = frozen[COPY_MANIFEST]["data"]
    require(copies["source_commit"] == source and copies["baseline_commit"] == BASELINE, "copy manifest source identity")
    require(copies["omissions"], "copy manifest must describe omitted outer evidence")
    copy_paths = [row["path"] for row in copies["files"]]
    require(len(copy_paths) == len(set(copy_paths)), "duplicate evidence copy")
    require(set(copy_paths) == paths - {MANIFEST, COPY_MANIFEST}, "every payload needs an exact outer copy mapping")
    for row in copies["files"]:
        expected_identity = {"sha256": row["sha256"], "bytes": row["bytes"]}
        require(identity(relative_path(root, row["path"])) == expected_identity == identity(outer_path(outer, row["outer_source"])),
                "copy differs from exact outer evidence: " + row["path"])
    return head, paths


def scientific_results(root, outer, source, config):
    summaries = {}
    for kind in ("counting", "torus"):
        spec = config["replays"][kind]
        runtime = spec["runtime_sha256"]
        require(runtime, "runtime source set must not be empty")
        for name, expected in runtime.items():
            require(digest(relative_path(root, name)) == sha256(commit_blob(root, source, name)).hexdigest() == expected,
                    "runtime source differs from final commit: " + name)
        result_path = root / RESULTS[kind]
        before_path = root / REL / spec["reference"]
        require(identity(before_path) == spec["reference_identity"], "author reference identity: " + kind)
        require(identity(result_path) == spec["result_identity"], "fresh result identity: " + kind)
        before, after = load_json(before_path), load_json(result_path)
        command = load_json(root / REL / spec["command_receipt"])
        require(command["schema_version"] == 1 and command["kind"] == kind and command["returncode"] == 0
                and command["checks_passed"] is True and command["source_commit"] == source, "successful actual replay receipt required")
        require(command["spec_identity"] == identity(root / REL / "clean-source/replay-spec.json"), "actual replay specification identity")
        integration_pin = next(row for row in config["approval_pins"] if row["role"] == "integration")
        require(command["source_approval_identity"] == integration_pin["identity"], "actual replay integration approval identity")
        expected_state = {"head": source, "status_porcelain": "", "sha256": config["replay_guard_sha256"]}
        require(command["source_before"] == command["source_after"] == expected_state, "replay requires unchanged source HEAD/files and empty status before/after")
        require(command["result"] == identity(result_path) and command["argv"] == spec["argv"], "replay command/result identity")
        require(Path(command["output_path"]).resolve().is_relative_to(outer.resolve()), "replay wrote inside canonical or outside outer evidence")
        if kind == "counting":
            state = after["source"]
            require(state == after["source_at_completion"] and state["git_commit"] == source
                    and state["git_dirty"] is False and state["git_status_porcelain"] == [], "finite clean source provenance")
            require({r["path"]: r["sha256"] for r in state["sources"]} == runtime, "finite internal runtime identity")
            for row in state["sources"]:
                require(identity(root / row["path"]) == {"sha256": row["sha256"], "bytes": row["bytes"]}, "finite source byte count")
            require(after["check_counts"] == spec["expected_check_counts"], "final reviewed finite counts differ")
            summaries[kind] = counting_comparison(before, after)
        else:
            provenance = after["provenance"]
            require(after["phase"] == "clean_replay" and provenance["source_commit"] == source
                    and provenance["repository_dirty_at_start"] is False and provenance["git_status_porcelain_at_start"] == [], "torus clean source provenance")
            require(provenance["source_sha256"] == runtime, "torus internal runtime identity")
            preflight = provenance["moderate_preflight"]
            preflight_path = outer_path(outer, preflight["path"])
            require(digest(preflight_path) == preflight["sha256"] == spec["accepted_preflight_sha256"], "same-source preflight identity")
            data = load_json(preflight_path)
            require(data["cutoff"] == 512 and data["checks_passed"] is True
                    and data["provenance"]["source_sha256"] == runtime, "successful same-source512 preflight")
            binary = outer_path(outer, after["command_receipts"][0]["argv"][-1])
            require(digest(binary) == provenance["native_binary_sha256"], "actual replay binary identity")
            summaries[kind] = torus_report_comparison(before, after)
            summaries[kind].update(torus_raw_comparison(before, after, outer))
    return summaries


def expand_tex(getter, name="book/main.tex", seen=None):
    seen = set() if seen is None else seen
    require(name not in seen, "TeX input cycle: " + name)
    seen.add(name)
    data = getter(name)
    active = re.sub(rb"(?<!\\)%[^\n]*", b"", data)
    children = re.findall(rb"\\input\{([^{}\n]+)\}", active)
    graph = {name: sha256(data).hexdigest()}
    for raw in children:
        child = "book/" + raw.decode()
        if not child.endswith(".tex"):
            child += ".tex"
        expanded, nested = expand_tex(getter, child, seen.copy())
        data = data.replace(b"\\input{" + raw + b"}", expanded)
        graph.update(nested)
    return data, graph


def manuscript_pdf_links(root, outer, source, approved, config):
    before, _ = expand_tex(lambda p: commit_blob(root, BASELINE, p))
    after, graph = expand_tex(lambda p: (root / p).read_bytes())
    for pattern, count, name in ((rb"\\label\{([^{}]+)\}", 607, "labels"),
                                 (rb"\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}", 129, "bibliography keys")):
        old, new = re.findall(pattern, before), re.findall(pattern, after)
        require(old == new and len(new) == len(set(new)) == count, "manuscript " + name + "/order changed")
    inputs = config["pdf"]["input_sha256"]
    require(graph == inputs and len(inputs) == 26, "PDF must bind all 26 actual active TeX inputs")
    for name, expected in inputs.items():
        require(sha256(commit_blob(root, source, name)).hexdigest() == expected, "precommit PDF input differs from source commit")
    n, ledger_paths = 0, set()
    def visit(value):
        if isinstance(value, dict):
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)
        elif isinstance(value, str) and re.fullmatch(r"(?:book|docs|experiments|artifacts)/[^\s]+", value):
            ledger_paths.add(value)
    for name, expected_count in config["claim_ledgers"].items():
        require(name in approved, "claim ledger not in reviewed source allowlist")
        data = load_json(root / name)
        claims = data["claims"]
        require(len(claims) == len({c["id"] for c in claims}) == expected_count, "claim count/unique IDs: " + name)
        n += len(claims)
        visit(data)
    require(n == 168 and len(config["claim_ledgers"]) == 4, "168 claims in four ledgers required")
    for p in ledger_paths:
        require(relative_path(root, p).exists(), "missing claim-ledger path: " + p)
    pdf = identity(root / PDF)
    require(pdf == config["pdf"]["identity"] == identity(outer_path(outer, config["pdf"]["reviewed_outer_pdf"])), "PDF differs from exact precommit reviewed output")
    require(config["pdf"]["build_timing_claim"] == "actual independently reviewed precommit build copied byte-for-byte", "PDF build chronology must remain explicit")
    pdf_scope = verify_pdf_receipts(root, outer, source, config, inputs, pdf)
    docs = {root / p for p in approved if p.endswith(".md")} | set((root / REL).rglob("*.md"))
    links = 0
    for p in docs:
        if p.name.startswith("._"):
            continue
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", p.read_text()):
            parsed = urlsplit(target.strip("<>"))
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            require((p.parent / unquote(parsed.path)).resolve().exists(), "missing local link: " + str(p) + " -> " + target)
            links += 1
    return {"claims": n, "labels": 607, "bibliography_keys": 129, "PDF_inputs": 26,
            **pdf_scope,
            "local_links": links, "ledger_paths": len(ledger_paths)}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root, outer = args.root.resolve(), args.outer.resolve()
    require(not outer.is_relative_to(root), "outer evidence must be outside canonical")
    report = {"mode": "candidate" if args.candidate else "postcommit", "baseline_commit": BASELINE,
              "stage": "repository_guards", "source_commit": None, "head": None,
              "scope": "Identity, source/run provenance, strict finite-result comparison, preservation and links only; no replay, PDF build, visual review, publication or metadata cleanup."}
    with receipt_record(outer, args.receipt, report):
        repository(root)
        report["stage"] = "freeze_control_inputs"
        frozen = freeze_controls(root)
        config = frozen[CONTRACT]["data"]
        report["frozen_control_identities"] = {name: frozen[name]["identity"] for name in (CONTRACT, MANIFEST, COPY_MANIFEST)}
        report["candidate_manifest_sha256"] = frozen[MANIFEST]["identity"]["sha256"]
        report["frozen_artifact_paths"] = sorted(frozen["paths"])
        report["stage"] = "approval_and_source_checkpoint_guards"
        source, approved = approved_contract(root, config)
        report["source_commit"] = source
        report["source_checkpoint"] = source_checkpoint_receipts(root, source, approved, config)
        require(config["replay_guard_sha256"] == merge_hashes(approved, config["pdf"]["input_sha256"],
                config["replays"]["counting"]["runtime_sha256"], config["replays"]["torus"]["runtime_sha256"]),
                "replay guard must bind all reviewed and active inputs")
        report["stage"] = "initial_artifact_guards"
        head, artifact_paths = artifacts(root, outer, source, approved, config, args.candidate, frozen)
        report.update({"head": head, "source_paths": len(approved), "artifact_paths": len(artifact_paths)})
        report["stage"] = "preservation_guards"
        report["preservation"] = preservation(root, outer, source, approved, config)
        report["stage"] = "scientific_comparison_guards"
        report["scientific_comparison"] = scientific_results(root, outer, source, config)
        report["stage"] = "manuscript_PDF_link_guards"
        report["manuscript_PDF_links"] = manuscript_pdf_links(root, outer, source, approved, config)
        report["stage"] = "Git_integrity_guards"
        report["git_integrity"] = fsck(root)
        report["stage"] = "final_source_and_artifact_guards"
        require(git(root, "rev-parse", "HEAD").decode().strip() == head, "HEAD drifted during verification")
        for name, expected in config["replay_guard_sha256"].items():
            require(identity(root / name)["sha256"] == sha256(commit_blob(root, source, name)).hexdigest()
                    == sha256(commit_blob(root, head, name)).hexdigest() == expected, "source drift during verification: " + name)
        final_head, final_paths = artifacts(root, outer, source, approved, config, args.candidate, frozen)
        require(final_head == head and final_paths == artifact_paths == frozen["paths"], "verification path set or HEAD drift")
        external_inputs_unchanged(report["scientific_comparison"]["torus"]["external_input_identities"])
        # Recheck the ORIGINAL three identities after all other work. A newly
        # consistent replacement manifest/copy/payload set is not this candidate.
        controls_unchanged(root, frozen)
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "mode": report["mode"], "head": report["head"],
                      "receipt": str(args.receipt), "scope": report["scope"]}, indent=2))


if __name__ == "__main__":
    main()
