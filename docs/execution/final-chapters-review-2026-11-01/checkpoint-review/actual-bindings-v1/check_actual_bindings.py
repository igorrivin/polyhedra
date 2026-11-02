"""Read-only final binding delta; accepted helper admission, never numerical launch."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent.parent
ROOT = OUTER.parent.parent / "consolidated"
ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"}
result = {"passed": False, "scope": "Actual replay specification/source receipt delta before launch",
          "numerical_command_executed": False, "candidate_report_synthesized": False,
          "helper_tests_repeated": False, "canonical_or_Git_mutation": False, "commands": []}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def identity(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def load(path):
    return json.loads(path.read_text())


def git(*args):
    argv = ["git", *args]
    proc = subprocess.run(argv, cwd=ROOT, env=ENV, text=True, capture_output=True)
    result["commands"].append({"argv": argv, "cwd": str(ROOT), "returncode": proc.returncode,
                               "stdout": proc.stdout, "stderr": proc.stderr})
    require(proc.returncode == 0 and not proc.stderr, "Read-only Git command failed")
    return proc.stdout


def main():
    frozen = load(HERE / "subject-freeze.json")["files"]
    for path, expected in frozen.items():
        require(identity(Path(path)) == expected, "Initial frozen input drift: " + path)
    accepted = load(OUTER / "checkpoint-review/revision-v3/final-acceptance.json")
    for name, expected in accepted["accepted_preparation_files"].items():
        require(identity(OUTER / "checkpoint-work/revision-v3" / name) == expected, "Accepted tool drift")
    module_spec = importlib.util.spec_from_file_location("accepted_checkpoint_lib", OUTER / "checkpoint-work/revision-v3/checkpoint_lib.py")
    lib = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(lib)
    spec, spec_identity = lib.json_snapshot(OUTER / "clean-source/replay-spec.json")
    receipt, receipt_identity = lib.json_snapshot(OUTER / "source-checkpoint/source-checkpoint.json")
    approval, _ = lib.load_pin(OUTER, spec["source_approval"])
    computation, _ = lib.load_pin(OUTER, spec["computation_approval"])
    require(spec_identity["sha256"] == "7fbcdc3ca5c2443fff1b89096c6a5b94c3ddd233794fb1949d5737eb99f2266e", "Wrong actual spec")
    require(receipt_identity["sha256"] == "56df9d0d5bfc155c8f0bcc077bbb4320290896d87d602b7cf823e18f42b88bd0", "Wrong source receipt")
    root, outer, reference, helper_frozen = lib.approved_spec(spec)
    require(root == ROOT and outer == OUTER, "Wrong actual roots")
    before = lib.source_state(ROOT, spec["source_commit"], spec["replay_guard_sha256"])
    result["source_before"] = before
    require(spec["approved_source_sha256"] == approval["approved_source_sha256"] == receipt["approved_source_sha256"], "40-path source map differs")
    require(spec["tex_input_sha256"] == approval["approved_active_tex_sha256"] == receipt["tex_input_sha256"], "Approved active TeX binding differs")
    require(spec["runtime_sha256"] == approval["approved_runtime_sha256"] == computation["accepted_runtime_sha256"]
            == receipt["runtime_sha256"], "24-file runtime map differs")
    require(receipt["guard_sha256"] == spec["replay_guard_sha256"] == before["sha256"], "78-path source guard differs")
    require(receipt["author_reference"] == approval["immutable_reviewed_author_result"] == computation["accepted_author_result"],
            "Original author reference differs")
    require(receipt["source_commit"] == spec["source_commit"] == before["head"]
            and receipt["baseline_commit"] == receipt["parent_commit"] == spec["baseline_commit"], "Source commit/parent differs")
    require(receipt["passed"] is True and receipt["checks_passed"] is True and receipt["exit_status"] == 0
            and receipt["index_clean"] is True and receipt["git_status_porcelain"] == "", "Source receipt did not pass")
    require(receipt["before"]["sha256"] == receipt["after"]["sha256"] == spec["replay_guard_sha256"], "Source bytes drifted across commit")
    require(receipt["after"] == before and receipt["before"]["head"] == spec["baseline_commit"]
            and receipt["before"]["index_clean"] is True, "Source receipt stage fields differ")
    require(identity(OUTER / "source-checkpoint/attempt-1/receipt.json") == receipt_identity, "Final source receipt not verbatim attempt receipt")
    initial = {" M " + p for p in receipt["modified"]} | {"?? " + p for p in receipt["added"]}
    require(set(receipt["before"]["status_porcelain"].splitlines()) == initial, "Initial source status differs")
    require(git("rev-parse", "--show-toplevel").strip() == str(ROOT), "Git root differs")
    require(git("rev-list", "--parents", "-n", "1", "HEAD").split() == [spec["source_commit"], spec["baseline_commit"]], "Not exact direct child")
    delta = git("diff", "--name-status", "--no-renames", spec["baseline_commit"], spec["source_commit"])
    require(set(delta.splitlines()) == {"M\t" + p for p in receipt["modified"]} | {"A\t" + p for p in receipt["added"]}, "Commit status/path set differs")
    require(len(receipt["modified"]) == 6 and len(receipt["added"]) == 34, "Source path counts differ")
    tree = {}
    for row in git("ls-tree", "-rz", spec["source_commit"]).split("\0"):
        if row:
            attrs, name = row.split("\t", 1)
            tree[name] = attrs.split()
    require(len(tree) == 2307 and all(tree[p][0:2] == ["100644", "blob"] for p in spec["approved_source_sha256"]), "Source tree count/modes differ")
    require(not git("status", "--porcelain=v1", "--untracked-files=all") and not git("diff", "--cached", "--name-only"), "Git is not clean")
    require(not git("diff", "--check", spec["baseline_commit"], spec["source_commit"]), "Committed source whitespace differs")

    commands = [json.loads(line) for line in (OUTER / receipt["commands"]).read_text().splitlines()]
    require([c["sequence"] for c in commands] == list(range(1, 95)), "Source command receipt sequence differs")
    staged_blobs, new_whitespace, mutations = {}, [], []
    for command in commands:
        require(command["cwd"] == str(ROOT) and command["argv"][0] == "git", "Unexpected source command/root")
        for stream in ("stdout", "stderr"):
            row = command[stream]
            path = lib.outer_path(OUTER, row["path"])
            require(identity(path) == {k: row[k] for k in ("sha256", "bytes")}, "Command stream identity differs")
        require(command["stderr"]["bytes"] == 0, "Unexpected source-command stderr")
        argv = command["argv"]
        if argv[1:4] == ["diff", "--no-index", "--check"]:
            require(command["returncode"] in (0, 1) and command["stdout"]["bytes"] == 0, "Source whitespace check failed")
            new_whitespace.append(str(Path(argv[-1]).relative_to(ROOT)))
        else:
            require(command["returncode"] == 0, "Source command failed")
        if argv[1] == "show" and argv[-1].startswith(":"):
            staged_blobs[argv[-1][1:]] = command["stdout"]["sha256"]
        if "add" in argv or argv[1] == "commit":
            mutations.append(command)
    require(staged_blobs == spec["approved_source_sha256"] and sorted(new_whitespace) == receipt["added"], "Staged blob/whitespace coverage differs")
    require(len(mutations) == 2 and mutations[0]["argv"][1:3] == ["--literal-pathspecs", "add"]
            and mutations[0]["argv"][-1] == "--pathspec-file-nul"
            and mutations[1]["argv"][1:3] == ["commit", "--file"], "Source mutation commands differ")
    path_list = lib.outer_path(OUTER, receipt["path_list"]["path"])
    require(identity(path_list) == {k: receipt["path_list"][k] for k in ("sha256", "bytes")}
            and path_list.read_bytes() == b"\0".join(p.encode() for p in sorted(spec["approved_source_sha256"])) + b"\0", "Actual literal staging list differs")
    require(all(row["returncode"] == 0 and row["cleanup_performed"] is False for row in receipt["integrity_attempts"]), "Integrity/cleanup stage differs")
    result["source_receipt_checks"] = {"source_commit": spec["source_commit"], "commands": 94, "staged_blobs": 40,
        "new_files_default_whitespace": 34, "literal_source_only_mutations": 2, "no_cleanup_performed": True,
        "recorded_preservation": receipt["preservation"], "recorded_manuscript": receipt["manuscript"]}

    changed_manuscript = sorted(p for p in spec["reference_manuscript_sha256"]
                               if spec["reference_manuscript_sha256"][p] != spec["manuscript_observation_sha256"][p])
    changed_tex = sorted(p for p in spec["reference_tex_observation_sha256"]
                        if spec["reference_tex_observation_sha256"][p] != spec["tex_observation_sha256"][p])
    require(changed_manuscript == spec["allowed_manuscript_changes"] and len(changed_manuscript) == 10, "Manuscript exceptions differ")
    require(changed_tex == spec["allowed_tex_observation_changes"] and len(changed_tex) == 10, "TeX exceptions differ")
    inactive = sorted(set(spec["tex_observation_sha256"]) - set(spec["tex_input_sha256"]))
    require(len(inactive) == 10 and not set(inactive) & set(changed_tex), "Inactive TeX became an exception")
    require(reference["fixture"]["accepted_manuscript_sha256"] == computation["author_accepted_manuscript_sha256"], "Immutable mathematical pins differ")
    result["exact_metadata_change_paths"] = {"manuscript": changed_manuscript, "active_TeX": changed_tex, "inactive_TeX_fixed": inactive}
    output = lib.outer_path(OUTER, spec["output"])
    require(output == OUTER / "clean-source/result.json" and output.parent.is_dir()
            and not output.exists() and not output.is_symlink(), "Fresh output is unsafe or already exists")
    require(Path(spec["python"]).is_absolute() and Path(spec["python"]).is_file(), "Python executable absent")

    pdf_inputs = OUTER / "integration-review/tex-input-freeze.json"
    pdf_receipt = OUTER / "integration-review/pdf-build-receipt.json"
    pdf_extra = {str(p): identity(p) for p in (pdf_inputs, pdf_receipt)}
    with (HERE / "pdf-binding-inputs.json").open("x") as handle:
        json.dump(pdf_extra, handle, indent=2)
        handle.write("\n")
    for path in (pdf_inputs, pdf_receipt):
        require(identity(path) == approval["evidence"][path.name], "Approved PDF evidence identity differs")
    pdf_freeze, pdf_build = load(pdf_inputs), load(pdf_receipt)
    require(pdf_freeze["files"] == spec["tex_input_sha256"], "Precommit PDF 36 inputs differ from committed inputs")
    require(pdf_build["tex_input_freeze_sha256"] == identity(pdf_inputs)["sha256"]
            and pdf_build["pdf"] == approval["precommit_pdf"] == receipt["precommit_pdf"], "PDF binding differs")
    require(pdf_build["postcommit_build"] is False and set(pdf_build["recorder_active_custom_inputs"]) == set(spec["tex_input_sha256"]), "PDF timing/recorder input claim differs")
    pdf = lib.outer_path(OUTER, approval["precommit_pdf"]["path"])
    require(identity(pdf) == {k: approval["precommit_pdf"][k] for k in ("sha256", "bytes")}, "Approved PDF bytes differ")
    result["precommit_PDF_binding"] = {"pdf": approval["precommit_pdf"], "all_36_inputs_match_committed_and_live": True,
                                       "postcommit_build_claimed": False}
    lib.recheck(helper_frozen)
    require(lib.source_state(ROOT, spec["source_commit"], spec["replay_guard_sha256"]) == before, "Clean source drift during binding review")
    for path, expected in {**frozen, **pdf_extra}.items():
        require(identity(Path(path)) == expected, "Final frozen input drift: " + path)
    result.update({"spec_identity": spec_identity, "source_receipt_identity": receipt_identity,
                   "accepted_helper_admission": True, "frozen_inputs_unchanged": len(frozen) + len(pdf_extra),
                   "guarded_paths": len(spec["replay_guard_sha256"]), "source_after": before,
                   "fresh_output_absent": True, "passed": True})


try:
    main()
except Exception as error:
    result["error"] = type(error).__name__ + ": " + str(error)
finally:
    with (HERE / "independent-checks.json").open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({k: result[k] for k in ("passed", "error", "frozen_inputs_unchanged", "guarded_paths") if k in result}))
if not result["passed"]:
    raise SystemExit(1)
