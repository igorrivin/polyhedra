"""Read-only checks of the frozen actual-evidence preparation; no replay or commit."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import posixpath
import re
import subprocess
from urllib.parse import unquote, urlsplit

HERE = Path(__file__).resolve().parent
OUTER = HERE.parent.parent
ROOT = OUTER.parent.parent / "consolidated"
PREP = OUTER / "checkpoint-curation-preparation"
ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"}
observations = {}
commands = []


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def identity(path):
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def load(path):
    return json.loads(path.read_text())


def safe(base, name):
    path = Path(name)
    require(isinstance(name, str) and not path.is_absolute() and str(path) == name
            and ".." not in path.parts, "Unsafe path: " + str(name))
    full = base / path
    require(full.resolve().is_relative_to(base.resolve()), "Path escaped base")
    require(not any((base / Path(*path.parts[:n])).is_symlink()
                    for n in range(1, len(path.parts) + 1)), "Symlink path")
    return full


def command(argv, stdin=None):
    proc = subprocess.run(argv, cwd=ROOT, env=ENV, text=True, input=stdin, capture_output=True)
    commands.append({"argv": argv, "cwd": str(ROOT), "stdin": stdin,
                     "returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr})
    return proc


def main():
    frozen = load(HERE / "subject-freeze.json")["files"]
    for name, expected in frozen.items():
        require(identity(Path(name)) == expected, "Input drift before review: " + name)
    binding = load(PREP / "binding-plan.unready.json")
    spec = binding["known_replay_spec_bindings"]
    plan = load(PREP / "source-checkpoint-plan.unready.json")
    catalog = load(PREP / "curation-map.unready.json")
    validation = load(PREP / "validation.json")
    library_path = OUTER / "checkpoint-work/revision-v3/checkpoint_lib.py"
    require(identity(library_path)["sha256"] == binding["v3_tool_adapter"]["live_tool_sha256"]["checkpoint_lib.py"],
            "Accepted v3 helper identity changed")
    module_spec = importlib.util.spec_from_file_location("accepted_checkpoint_lib", library_path)
    lib = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(lib)

    pins = binding["known_checkpoint_approval_pins"]
    require([p["role"] for p in pins] == ["structure", "quantum", "geodesic", "conventions", "computation", "integration"],
            "Six role names/order differ")
    for pin in pins[:5] + [binding["known_tool_acceptance"], binding["v3_tool_adapter"]["independent_acceptance"]]:
        lib.load_pin(OUTER, pin)
    require(pins[-1]["path"] is None and pins[-1]["identity"] is None, "Premature final integration binding")
    approval, _ = lib.load_pin(OUTER, spec["computation_approval"])
    pin = spec["computation_approval"]
    reference_path = safe(OUTER, spec["reference"]["path"])
    reference, ref_identity = lib.json_snapshot(reference_path)
    require(ref_identity == spec["reference"]["identity"]
            == lib.approved_reference_identity(approval, pin, OUTER, spec["reference"]["path"]),
            "Actual full-v2 reference binding differs")
    for key, pointer in [("runtime_sha256", "runtime_sha256_pointer"),
                         ("reference_manuscript_sha256", "reference_manuscript_sha256_pointer"),
                         ("reference_tex_observation_sha256", "reference_tex_observation_sha256_pointer")]:
        require(spec[key] == lib.mapped_hashes(approval, pin[pointer]), "Actual approval map differs: " + key)
    require(spec["expected_groups"] == lib.get_pointer(approval, pin["expected_groups_pointer"]), "Group pin differs")
    require(spec["expected_check_counts"] == approval["derived_check_counts"], "Count pin differs")
    lib.validate_report(reference, spec, clean=False)
    rules = binding["author_and_final_stage_rules"]
    require(rules["accepted_contract_sha256_fixed"] == reference["fixture"]["accepted_manuscript_sha256"]
            == approval["author_accepted_manuscript_sha256"], "Accepted contract observations were substituted")
    require(rules["approved_source_set_sha256"] == approval["accepted_source_set_sha256"]
            == reference["source_before"]["source_set_sha256"], "Runtime aggregate differs")
    require(len(spec["runtime_sha256"]) == 24 and len(spec["reference_manuscript_sha256"]) == 14
            and len(spec["reference_tex_observation_sha256"]) == 46, "Observation cardinality differs")
    observations["actual_approval_bindings"] = {"completed_roles": [p["role"] for p in pins[:5]],
        "author_result": {"path": str(reference_path), **ref_identity}, "runtime_files": 24,
        "manuscript_observations": 14, "tex_observations": 46, "groups": spec["expected_groups"],
        "counts": spec["expected_check_counts"], "complete_author_source_before_after_equal": True}

    inventory = load(safe(OUTER, plan["author_inventory"]["path"]))
    author_freeze = load(safe(OUTER, plan["author_freeze"]["path"]))
    for key in ("author_inventory", "author_freeze"):
        require(identity(safe(OUTER, plan[key]["path"])) == {k: plan[key][k] for k in ("sha256", "bytes")}, key)
    source_map = plan["exact_source_sha256_provisional"]
    require(source_map == inventory["source_sha256"] == author_freeze["source_sha256"], "Source inventories differ")
    literal = (PREP / "source-paths.provisional.nul").read_bytes()
    require(literal.endswith(b"\0"), "NUL path list terminator missing")
    names = [x.decode() for x in literal[:-1].split(b"\0")]
    require(names == inventory["expected_source_paths"] == sorted(source_map), "Literal source allowlist differs")
    require(plan["tracked_modified"] == inventory["tracked_modified"] and plan["new"] == inventory["new"],
            "Source status classification differs")
    require(len(source_map) == 40 and len(plan["tracked_modified"]) == 6 and len(plan["new"]) == 34, "Source cardinality")
    for name, expected in {**source_map, **spec["runtime_sha256"]}.items():
        require(identity(safe(ROOT, name))["sha256"] == expected, "Current source differs: " + name)
    old_runtime = set(spec["runtime_sha256"]) - set(source_map)
    require(old_runtime == {"experiments/quantum_surgery/" + f for f in ("__init__.py", "algebra.py", "exact.py")},
            "Wrong existing runtime dependency split")
    inactive_tex = set(spec["reference_tex_observation_sha256"]) - set(author_freeze["tex_input_sha256"])
    require(len(author_freeze["tex_input_sha256"]) == 36 and len(inactive_tex) == 10, "Active/inactive TeX count")
    for name in inactive_tex:
        require(identity(safe(ROOT, name))["sha256"] == spec["reference_tex_observation_sha256"][name],
                "Inactive TeX changed")
    before = load(HERE / "git-before.json")
    expected_status = {" M " + name for name in plan["tracked_modified"]} | {"?? " + name for name in plan["new"]}
    require(set(before[3]["stdout"].split("\0")[:-1]) == expected_status and before[2]["stdout"] == "",
            "Initial source-only status/index differs")
    observations["source_plan"] = {"paths": names, "modified": 6, "new": 34,
        "unchanged_runtime_dependencies_not_staged": sorted(old_runtime), "inactive_tex_fixed": sorted(inactive_tex),
        "inventory_matches_live_at_review": True, "initial_index_empty": True,
        "final_source_approval_and_commit_not_inferred": True}

    rows = catalog["existing_files"]
    targets = {r["target"] for r in rows}
    require(len(rows) == len(targets) == 317 and sum(r["bytes"] for r in rows) == 16017571, "Catalog counts/unique targets")
    renames, links = [], []
    link_re = re.compile(r"\[[^\]]*\]\(([^\s)]+)\)|^\s*\[[^\]]+\]:\s*(\S+)", re.M)
    for row in rows:
        source = safe(OUTER, row["outer_source"])
        target = safe(ROOT, row["target"])
        require(target.is_relative_to(ROOT / catalog["candidate_prefix"]) and not target.exists(), "Unsafe/existing copy destination")
        require(identity(source) == {k: row[k] for k in ("sha256", "bytes")} and row["byte_preserving"] is True,
                "Curation byte identity differs")
        if source.suffix in {".log", ".fls"}:
            require(str(target).endswith(source.name + ".txt"), "Ignored raw extension was not renamed exactly")
            renames.append({"source": row["outer_source"], "target": row["target"]})
        if source.suffix == ".md":
            for match in link_re.finditer(source.read_text()):
                link = (match[1] or match[2]).strip("<>")
                parsed = urlsplit(link)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                resolved = posixpath.normpath(posixpath.join(str(Path(row["target"]).parent), unquote(parsed.path)))
                require(resolved in targets or safe(ROOT, resolved).is_file(), "Unresolved proposed reader link: " + link)
                links.append({"from": row["target"], "link": link, "target": resolved})
    require(len(renames) == 7 and len(links) == 15, "Renamed raw files or reader links changed")
    ignored = command(["git", "check-ignore", "--no-index", "--stdin"], "\n".join(sorted(targets)) + "\n")
    require(ignored.returncode == 1 and not ignored.stdout and not ignored.stderr, "Proposed copy paths are ignored")
    by_source = {r["outer_source"]: r for r in rows}
    for required in [spec["reference"]["path"], "computation-review/subject-v1/author-result-70-110.json"]:
        require(required in by_source, "Required approved author/oracle input omitted")
    prelim = binding["final_pdf_bindings"]["preliminary_pdf_excluded_sha256"]
    require(all(r["sha256"] != prelim for r in rows), "Preliminary PDF copied as final evidence")
    whitespace = validation["prospective_verbatim_whitespace"]
    require(len(whitespace) == 22 and not any(r["exception_authorized"] or r["authored_document"] for r in whitespace),
            "Whitespace observations became authorization")
    for row in whitespace:
        require(row["identity"] == {k: by_source[row["outer_source"]][k] for k in ("sha256", "bytes")},
                "Whitespace observation identity differs")
        check = command(["git", "diff", "--no-index", "--check", "--", "/dev/null", str(OUTER / row["outer_source"])])
        require(check.returncode == row["check_returncode"] and check.stdout == row["diagnostics"] and not check.stderr,
                "Verbatim whitespace diagnostics differ")
    drafts = [r for r in rows if r["binding_status"] == "unready_draft"]
    require(len(drafts) == 4, "Unexpected draft-document count")
    for row in drafts:
        check = command(["git", "diff", "--no-index", "--check", "--", "/dev/null", str(OUTER / row["outer_source"])])
        require(check.returncode in (0, 1) and not check.stdout and not check.stderr, "Authored draft whitespace failed")
    observations["curation"] = {"files": len(rows), "bytes": sum(r["bytes"] for r in rows), "renames": renames,
        "local_markdown_links": links, "verbatim_whitespace_files": 22, "whitespace_exception_authorized": False,
        "authored_drafts_default_whitespace_pass": True, "candidate_copy_not_performed": True}
    require(binding["ready"] is False and plan["ready"] is False and plan["execution_authorized"] is False
            and catalog["copy_execution_authorized_by_this_plan"] is False, "Premature execution readiness")
    require(all(v is None for k, v in binding["final_source_bindings"].items() if k != "rule"), "Final source placeholders filled")
    require(all(binding["final_pdf_bindings"][k] is None for k in
                ("reviewed_outer_pdf", "identity", "input_freeze", "build_receipt", "visual_receipt")), "Final PDF placeholders filled")
    for name, expected in frozen.items():
        require(identity(Path(name)) == expected, "Frozen input drift during review: " + name)
    observations["all_384_frozen_inputs_unchanged"] = True


result = {"scope": "Actual-evidence preparation bindings and unexecuted source-only plan; not final execution approval",
          "passed": False, "helper_tests_repeated": False, "numerical_replay_performed": False,
          "canonical_or_git_mutation": False}
try:
    main()
    result["passed"] = True
except Exception as error:
    result["error"] = type(error).__name__ + ": " + str(error)
finally:
    result["observations"] = observations
    result["commands"] = commands
    with (HERE / "independent-checks.json").open("x") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"observations", "commands"}}))
if not result["passed"]:
    raise SystemExit(1)
