#!/usr/bin/env python3
"""Read-only verification of the curated candidate or its artifact commit.

The prepared contract is deliberately unready. This program does not create
evidence, calculate science, render a PDF, inspect pages, clean Git or commit.
Only its exclusive outer verification receipt is written.
"""
from argparse import ArgumentParser
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess

from checkpoint_lib import (
    BASELINE, ENV, NEW_LABELS, PDF, REL, RESULT, approved_spec, commit_blob, expand_tex, finite_comparison,
    get_pointer, git, identity, json_snapshot, load_pin, mapped_hashes, outer_path, receipt_record,
    recheck, relative_path, repository, require,
)

MANIFEST = REL + "/candidate-artifact-manifest.json"
COPIES = REL + "/evidence-copy-manifest.json"
CONTRACT = REL + "/checkpoint-contract.json"
KNOWN_DANGLING = {"dangling blob dba78d2f1770521c3cfaef91091f1c296ec57abd",
                  "dangling blob 4c37b26b85df0662fbc6ab71661713083ac3a7c1"}


def tree(root, commit):
    result = {}
    for row in git(root, "ls-tree", "-r", "-z", commit).split(b"\0"):
        if row:
            fields, path = row.split(b"\t", 1)
            mode, kind, oid = fields.decode().split()
            require(kind == "blob", "non-blob tree entry")
            result[path.decode()] = (mode, oid)
    return result


def preservation(root, outer, source, approved, config):
    before, after = tree(root, BASELINE), tree(root, source)
    require(len(before) == 2273, "baseline must contain 2273 tracked paths")
    changes = {row.split("\t")[1]: row.split("\t")[0]
               for row in git(root, "diff", "--no-renames", "--name-status", BASELINE, source).decode().splitlines()}
    require(changes == {p: "M" if p in before else "A" for p in approved}, "source path/status allowlist differs")
    require(set(after) == set(before) | set(approved), "source added or removed undeclared paths")
    require(all(after[p][0] == before[p][0] for p in before), "baseline Git mode changed")
    require(all(after[p][0] == "100644" for p in set(after) - set(before)), "new source mode must be 100644")
    require(all(after[p] == before[p] for p in set(before) - set(approved)), "protected baseline Git blob changed")
    inventory_path = outer_path(outer, config["baseline_inventory"]["path"])
    inventory, frozen = json_snapshot(inventory_path)
    require(frozen == config["baseline_inventory"]["identity"] and inventory["baseline_commit"] == BASELINE,
            "baseline inventory identity differs")
    indexed = {row["path"]: row for row in inventory["files"]}
    require(len(inventory["files"]) == len(indexed) == 2273 and set(indexed) == set(before), "baseline inventory coverage")
    protected = sorted(set(before) - set(approved))
    batch = subprocess.run(["git", "cat-file", "--batch"], cwd=root, env=ENV,
                           input=("\n".join(before[p][1] for p in protected) + "\n").encode(),
                           capture_output=True, check=False)
    require(batch.returncode == 0 and not batch.stderr, "baseline blob batch failed")
    offset, lfs = 0, 0
    for p in protected:
        row = indexed[p]
        require((row["git_mode"], row["git_blob"]) == before[p], "baseline Git identity: " + p)
        end = batch.stdout.index(b"\n", offset)
        oid, kind, length = batch.stdout[offset:end].split()
        start, size = end + 1, int(length)
        blob = batch.stdout[start:start + size]
        require(oid.decode() == before[p][1] and kind == b"blob"
                and batch.stdout[start + size:start + size + 1] == b"\n", "Git blob framing")
        offset = start + size + 1
        require(len(blob) == row["git_blob_bytes"] and sha256(blob).hexdigest() == row["git_blob_sha256"],
                "baseline inventory blob checksum: " + p)
        path = relative_path(root, p)
        if row["git_mode"] == "120000":
            data = os.readlink(path).encode()
            actual = {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
        else:
            actual = identity(path)
        require(actual == {"sha256": row["materialized_sha256"], "bytes": row["materialized_bytes"]},
                "protected working file changed: " + p)
        pointer = re.fullmatch(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([0-9a-f]{64})\nsize ([0-9]+)\n", blob)
        require(row["materialized_lfs"] is bool(pointer), "baseline inventory LFS flag: " + p)
        if pointer:
            require(actual == {"sha256": pointer[1].decode(), "bytes": int(pointer[2])}, "materialized LFS bytes: " + p)
            lfs += 1
        else:
            require(actual == {"sha256": sha256(blob).hexdigest(), "bytes": len(blob)}, "protected blob bytes: " + p)
    require(offset == len(batch.stdout) and lfs == 412, "baseline blob framing/LFS count")
    original_path = root.parent / "audit/2026-10-31/source-inventory.json"
    originals, original_identity = json_snapshot(original_path)
    require(original_identity == config["original_inventory_identity"], "original inventory identity")
    count = 0
    for repo in originals["repositories"]:
        directory = root.parent / repo["path"]
        require(git(directory, "rev-parse", "HEAD").decode().strip() == repo["head"]
                and not git(directory, "status", "--porcelain=v1", "--untracked-files=all"), "original repository changed")
        git(root, "merge-base", "--is-ancestor", repo["head"], source)
        for row in repo["files"]:
            require(identity(relative_path(directory, row["path"])) == {"sha256": row["sha256"], "bytes": row["bytes"]},
                    "original file changed: " + row["path"])
            count += 1
    archive = originals["monograph_archive"]
    require(count == 953 and identity(root.parent / archive["path"])
            == {"sha256": archive["sha256"], "bytes": archive["bytes"]}, "original file count or ZIP changed")
    recheck({str(inventory_path): frozen, str(original_path): original_identity})
    return {"baseline_paths": 2273, "protected_paths": len(protected), "source_paths": len(after),
            "materialized_LFS": lfs, "original_files": count}


def candidate_state(root, outer, source, approved, manifest, copies, candidate):
    require(manifest["baseline_commit"] == copies["baseline_commit"] == BASELINE
            and manifest["source_commit"] == copies["source_commit"] == source, "candidate ancestry differs")
    require(MANIFEST not in manifest["files"], "candidate manifest may not hash itself")
    paths = set(manifest["files"]) | {MANIFEST}
    actual = {str(p.relative_to(root)) for p in (root / REL).rglob("*")
              if p.is_file() and not p.name.startswith("._")} | {PDF, RESULT}
    require(paths == actual and not paths & set(approved), "artifact/source inventories differ or overlap")
    require(not git(root, "diff", "--cached", "--name-only"), "index must be empty during verification")
    head = git(root, "rev-parse", "HEAD").decode().strip()
    if candidate:
        require(head == source and not git(root, "diff", "--name-only"), "candidate must retain unchanged source HEAD")
        require(set(git(root, "ls-files", "--others", "--exclude-standard").decode().splitlines()) == paths,
                "untracked candidate differs from manifest")
    else:
        require(git(root, "rev-list", "--parents", "-n", "1", head).decode().split() == [head, source]
                and not git(root, "status", "--porcelain=v1", "--untracked-files=all"), "artifact child must be clean")
        require(set(git(root, "diff", "--no-renames", "--name-status", source, head).decode().splitlines())
                == {"A\t" + p for p in paths}, "artifact commit may only add manifest paths")
    committed = tree(root, head)
    for p in paths:
        path = relative_path(root, p)
        if p != MANIFEST:
            require(identity(path) == manifest["files"][p], "artifact identity differs: " + p)
        if not candidate:
            require(committed[p][0] == "100644" and commit_blob(root, head, p) == path.read_bytes(),
                    "artifact Git bytes/mode differ: " + p)
    require(isinstance(copies["omissions"], list) and copies["omissions"], "explicit curation omissions required")
    rows = copies["files"]
    require(len(rows) == len({row["path"] for row in rows})
            and {row["path"] for row in rows} == paths - {MANIFEST, COPIES}, "exact outer copy mapping coverage")
    for row in rows:
        expected = {"sha256": row["sha256"], "bytes": row["bytes"]}
        require(identity(relative_path(root, row["path"])) == identity(outer_path(outer, row["outer_source"]))
                == expected, "curated bytes differ from outer evidence")
    return head, paths


def manuscript(root, source, spec, config):
    old, _ = expand_tex(lambda p: commit_blob(root, BASELINE, p))
    new, graph = expand_tex(lambda p: (root / p).read_bytes())
    def labels(data):
        return re.findall(rb"\\label\{([^{}]+)\}", data)
    before, after = labels(old), labels(new)
    additions = {p.encode() for p in NEW_LABELS}
    require(len(before) == len(set(before)) == 607 and len(after) == len(set(after)) == 613
            and set(after) - set(before) == additions and [p for p in after if p not in additions] == before,
            "original label order or exact six additions differ")
    pattern = rb"\\bibitem(?:\[[^\]]*\])?\{([^{}]+)\}"
    keys = re.findall(pattern, new)
    require(keys == re.findall(pattern, old) and len(keys) == len(set(keys)) == 129, "bibliography key order differs")
    require(graph == spec["tex_input_sha256"] and len(graph) == 36, "all 36 TeX input hashes required")
    for p, expected in graph.items():
        require(sha256(commit_blob(root, source, p)).hexdigest() == expected, "PDF input differs from source commit")
    claims = 0
    for p, count in config["claim_ledgers"].items():
        require(p in spec["approved_source_sha256"], "new ledger not in source approval")
        data, _ = json_snapshot(root / p)
        require(len(data["claims"]) == len({c["id"] for c in data["claims"]}) == count, "claim ledger coverage")
        claims += count
    require(len(config["claim_ledgers"]) == 3 and claims == 186, "three final ledgers/186 claims required")
    return {"labels": 613, "original_ordered_labels": 607, "bibliography_keys": 129, "TeX_inputs": 36, "claims": claims}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--outer", type=Path, required=True)
    parser.add_argument("--candidate", action="store_true")
    parser.add_argument("--receipt", type=Path, required=True)
    args = parser.parse_args()
    root, outer = args.root.resolve(), args.outer.resolve()
    require(not outer.is_relative_to(root) and not root.is_relative_to(outer), "canonical/outer roots must be disjoint")
    report = {"schema_version": 1, "mode": "candidate" if args.candidate else "postcommit",
              "stage": "control_freeze", "scope": "Identity, preservation, replay provenance and report equality; no new science, PDF build, visual inspection, metadata cleanup or publication."}
    with receipt_record(outer, args.receipt, report):
        repository(root)
        controls = {p: json_snapshot(root / p) for p in (CONTRACT, MANIFEST, COPIES)}
        frozen = {str(root / p): row[1] for p, row in controls.items()}
        config, manifest, copies = (controls[p][0] for p in (CONTRACT, MANIFEST, COPIES))
        report["frozen_control_identities"] = dict(frozen)
        require(type(config.get("schema_version")) is int and config["schema_version"] == 1
                and config.get("ready") is True and type(config.get("unresolved")) is list
                and config["unresolved"] == [], "checkpoint contract is unfinished")
        require(config["baseline_commit"] == BASELINE, "checkpoint baseline differs")
        base = root / REL
        spec_path = relative_path(base, config["replay_spec"]["path"])
        spec, spec_identity = json_snapshot(spec_path)
        require(spec_identity == config["replay_spec"]["identity"], "replay spec copy identity differs")
        frozen[str(spec_path)] = spec_identity
        original_spec = outer_path(outer, config["replay_spec"]["outer_source"])
        require(identity(original_spec) == spec_identity, "original replay specification differs")
        frozen[str(original_spec)] = spec_identity
        report["stage"] = "source_and_approval_guards"
        spec_root, spec_outer, reference, spec_frozen = approved_spec(spec)
        require(spec_root == root and spec_outer == outer and config["source_commit"] == spec["source_commit"],
                "contract/replay roots or source commit differ")
        frozen.update(spec_frozen)
        run_inputs = {**spec_frozen, str(original_spec): spec_identity}
        source, approved = spec["source_commit"], spec["approved_source_sha256"]
        source_receipt, source_frozen = load_pin(base, config["source_receipt"])
        frozen.update(source_frozen)
        require(source_receipt["passed"] is True and source_receipt["source_commit"] == source
                and source_receipt["baseline_commit"] == source_receipt["parent_commit"] == BASELINE
                and source_receipt["git_status_porcelain"] == "" and source_receipt["index_clean"] is True,
                "actual clean source-commit receipt required")
        pins = config["approval_pins"]
        require(len(pins) == 6 and {p["role"] for p in pins}
                == {"structure", "quantum", "geodesic", "conventions", "computation", "integration"}, "six independent approval roles required")
        for pin in pins:
            _, pin_frozen = load_pin(base, pin)
            frozen.update(pin_frozen)
            if pin["role"] in ("computation", "integration"):
                require(pin["identity"] == spec["computation_approval" if pin["role"] == "computation" else "source_approval"]["identity"],
                        "candidate approval differs from actual replay approval")
        report["stage"] = "candidate_inventory_guards"
        head, paths = candidate_state(root, outer, source, approved, manifest, copies, args.candidate)
        report.update({"head": head, "source_commit": source, "artifact_paths": len(paths)})
        report["preservation"] = preservation(root, outer, source, approved, config)
        whitespace = subprocess.run(["git", "diff-tree", "--check", BASELINE, source], cwd=root,
                                    env=ENV, capture_output=True, text=True, check=False)
        require(whitespace.returncode == 0 and not whitespace.stdout and not whitespace.stderr,
                "source checkpoint must pass the default whitespace check")
        report["stage"] = "actual_replay_provenance"
        run, run_frozen = load_pin(base, config["replay_receipt"])
        frozen.update(run_frozen)
        expected_state = {"head": source, "status_porcelain": "", "sha256": spec["replay_guard_sha256"]}
        output = outer_path(outer, spec["output"])
        expected_command = [spec["python"], "-B", str(root / "experiments/quantum_geodesics/run.py"), "--output", str(output)]
        require(run["command_executed"] is True and run["returncode"] == 0 and run["checks_passed"] is True
                and run["source_commit"] == source and run["spec_identity"] == spec_identity
                and run["source_before"] == run["source_after"] == expected_state
                and run["argv"] == expected_command and run["cwd"] == str(root)
                and run["output_path"] == str(output) and run["frozen_input_identities"] == run_inputs,
                "successful actual clean-source command receipt required")
        result, result_identity = json_snapshot(root / RESULT)
        require(result_identity == run["result"] == identity(output), "canonical result differs from actual replay")
        report["scientific_comparison"] = finite_comparison(reference, result, spec)
        comparison, comparison_frozen = load_pin(base, config["comparison_receipt"])
        frozen.update(comparison_frozen)
        require(comparison["checks_passed"] is True and comparison["candidate"] == result_identity
                and comparison["spec_identity"] == spec_identity
                and comparison["frozen_input_identities"] == {**run_inputs, str(output): result_identity},
                "retained comparison identity/status differs")
        for key, value in report["scientific_comparison"].items():
            require(comparison[key] == value, "retained strict-comparison field differs: " + key)
        report["stage"] = "manuscript_and_PDF_identity"
        report["manuscript"] = manuscript(root, source, spec, config)
        pdf = config["pdf"]
        require(pdf["build_timing_claim"] == "actual independently reviewed precommit build copied byte-for-byte"
                and identity(root / PDF) == pdf["identity"] == identity(outer_path(outer, pdf["reviewed_outer_pdf"])),
                "PDF must be exact reviewed precommit build")
        for key in ("input_freeze", "build_receipt", "visual_receipt"):
            pin = pdf[key]
            record, pin_frozen = load_pin(base, pin)
            frozen.update(pin_frozen)
            if key == "input_freeze":
                require(mapped_hashes(record, pin["input_sha256_pointer"], pin.get("input_sha256_shape", "mapping"))
                        == spec["tex_input_sha256"], "reviewed PDF freeze differs from committed TeX inputs")
            else:
                require(get_pointer(record, pin["pdf_sha256_pointer"]) == pdf["identity"]["sha256"], "PDF receipt hash differs")
        report["stage"] = "Git_integrity"
        check = subprocess.run(["git", "fsck", "--full"], cwd=root, env=ENV, capture_output=True, text=True, check=False)
        lines = set((check.stdout + check.stderr).splitlines())
        require(check.returncode == 0 and lines <= KNOWN_DANGLING, "Git integrity failed; this verifier performs no cleanup")
        report["git_integrity"] = {"returncode": check.returncode, "output": sorted(lines), "cleanup_performed": False}
        report["stage"] = "final_identity_guards"
        for p, value in spec["replay_guard_sha256"].items():
            require(identity(root / p)["sha256"] == sha256(commit_blob(root, source, p)).hexdigest()
                    == sha256(commit_blob(root, head, p)).hexdigest() == value, "source drift during checkpoint verification")
        require(candidate_state(root, outer, source, approved, manifest, copies, args.candidate) == (head, paths),
                "candidate state changed during verification")
        recheck(frozen)
        report.update({"checks_passed": True, "stage": "complete"})
    print(json.dumps({"checks_passed": True, "receipt": str(args.receipt), "head": head}))


if __name__ == "__main__":
    main()
