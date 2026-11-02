"""Frozen-input gates adapted from the independently reviewed counting checkpoint.

Only one finite companion is supported. This module performs no cleanup, commit,
PDF build, scientific calculation or publication. Exact metadata exclusions are
checked individually; no scientific or complete source object is discarded.
"""
from __future__ import annotations

import copy
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess

BASELINE = "151673b1817e66aae493eb7da1be5ddf49adfe0f"
REL = "docs/execution/final-chapters-review-2026-11-01"
RESULT = "artifacts/quantum_geodesics/result.json"
PDF = "artifacts/final-chapters-review-2026-11-01/monograph-working-draft.pdf"
DRIVER = "experiments/quantum_geodesics/run.py"
ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"}
NEW_LABELS = {"eq:figurekerneltail", "eq:figurefiniteidentity", "eq:localdistancehessian",
              "eq:torustwistderivatives", "eq:torusintegraltail", "eq:Hpartialsumtail"}

class CheckpointError(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise CheckpointError(message)


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def parse_json(data):
    def bad_constant(value):
        raise CheckpointError("nonfinite JSON constant: " + value)
    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), "nonfinite JSON number: " + value)
        # Keep only the subset whose exact decimal value survives JSON's
        # ordinary float serialization. This is rejection of lossy tokens,
        # not arbitrary-precision numeric parsing or a binary64 error bound.
        try:
            lossless = Decimal(value) == Decimal(str(parsed))
        except InvalidOperation as exc:
            raise CheckpointError("unsupported JSON decimal token: " + value) from exc
        require(lossless, "JSON fractional number cannot round-trip without loss: " + value)
        return parsed
    return json.loads(data, object_pairs_hook=object_pairs,
                      parse_constant=bad_constant, parse_float=finite_float)


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    h = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def identity(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "expected ordinary file: " + str(path))
    return {"sha256": digest(path), "bytes": path.stat().st_size}


def json_snapshot(path):
    """Bind parsed data to the SAME initial read, then check its live identity."""
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), "expected ordinary JSON file: " + str(path))
    data = path.read_bytes()
    frozen_identity = {"sha256": sha256(data).hexdigest(), "bytes": len(data)}
    require(identity(path) == frozen_identity, "JSON changed during snapshot: " + str(path))
    return parse_json(data), frozen_identity


def require_unchanged(path, frozen_identity, description):
    require(identity(path) == frozen_identity, description + " identity changed during operation")


def relative_path(base, name):
    p = Path(name)
    require(not p.is_absolute() and p.parts and ".." not in p.parts,
            "expected relative path without traversal: " + str(name))
    require(not any(part.startswith("._") for part in p.parts), "AppleDouble sidecar path: " + name)
    result = Path(base) / p
    require(result.resolve().is_relative_to(Path(base).resolve()), "path escapes base: " + name)
    return result


def outer_path(outer, name):
    p = Path(name)
    if p.is_absolute():
        require(p.resolve().is_relative_to(Path(outer).resolve()), "path is outside execution evidence: " + name)
        return p
    return relative_path(outer, name)


@contextmanager
def receipt_record(outer, name, report):
    """Reserve a new outer receipt before audited work; retain success or failure.

Path/root safety checks belong before this reservation. No existing path is
ever overwritten. Once the exclusive file is opened, guard, launch, comparison
and verification failures leave checks_passed=false and an explicit exit status.
"""
    receipt = outer_path(outer, str(name))
    require(receipt.parent.is_dir(), "receipt parent must already exist")
    require(not receipt.exists() and not receipt.is_symlink(), "receipt path already exists")
    report.update({"checks_passed": False, "exit_status": None,
                   "started_at_utc": datetime.now(timezone.utc).isoformat()})
    with receipt.open("x") as handle:
        try:
            yield report
            require(report["checks_passed"] is True, "operation did not complete all acceptance gates")
            report["exit_status"] = 0
        except BaseException as exc:
            report["checks_passed"] = False
            report["exit_status"] = (130 if isinstance(exc, KeyboardInterrupt) else
                                     exc.code if isinstance(exc, SystemExit) and type(exc.code) is int else 1)
            report["failure"] = type(exc).__name__ + ": " + str(exc)
            report["failure_stage"] = report.get("stage", "unspecified")
            raise
        finally:
            report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
            json.dump(report, handle, indent=2, allow_nan=False)
            handle.write("\n")


def git(root, *args):
    completed = subprocess.run(["git", *args], cwd=root, env=ENV, capture_output=True, check=False)
    require(completed.returncode == 0, "git command failed: " + " ".join(args) + "\n" + completed.stderr.decode())
    return completed.stdout


def commit_blob(root, commit, path):
    relative_path(root, path)
    return git(root, "show", commit + ":" + path)


def repository(root):
    root = Path(root).resolve()
    require(git(root, "rev-parse", "--show-toplevel").decode().strip() == str(root), "unexpected Git root")
    require(not git(root, "remote"), "checkpoint requires no remotes")
    return root


def source_state(root, source, expected, clean=True):
    """Direct HEAD, Git-status, committed-byte and working-file checks each time."""
    head = git(root, "rev-parse", "HEAD").decode().strip()
    status = git(root, "status", "--porcelain=v1", "--untracked-files=all").decode()
    require(head == source, "HEAD differs from final source commit")
    if clean:
        require(status == "", "clean-source stage has nonempty Git status")
    observed = {}
    for name, value in expected.items():
        path = relative_path(root, name)
        actual = digest(path)
        require(actual == value == sha256(commit_blob(root, source, name)).hexdigest(),
                "working/committed/approved source identity mismatch: " + name)
        observed[name] = actual
    return {"head": head, "status_porcelain": status, "sha256": observed}


def merge_hashes(*maps):
    result = {}
    for mapping in maps:
        for path, value in mapping.items():
            require(path not in result or result[path] == value, "conflicting approval/input/runtime hash: " + path)
            result[path] = value
    return result


def expand_tex(getter, name="book/main.tex", seen=None):
    """Expand this book's literal braced input syntax; reject unsupported inputs.

    Raw file bytes determine hashes. Comments are removed only for traversal
    and label inspection. This is not a general TeX interpreter.
    """
    require(isinstance(name, str) and name.startswith("book/") and name.endswith(".tex")
            and str(Path(name)) == name, "noncanonical TeX input path: " + str(name))
    relative_path(Path("/"), name)
    seen = set() if seen is None else seen
    require(name not in seen, "repeated or cyclic TeX input: " + name)
    seen.add(name)
    try:
        raw_data = getter(name)
    except (OSError, KeyError) as exc:
        raise CheckpointError("missing TeX input: " + name) from exc
    graph = {name: sha256(raw_data).hexdigest()}
    active_lines = []
    for line in raw_data.splitlines(keepends=True):
        for index, character in enumerate(line):
            if character == ord("%"):
                back = index - 1
                while back >= 0 and line[back] == ord("\\"):
                    back -= 1
                if (index - back - 1) % 2 == 0:
                    line = line[:index] + (b"\n" if line.endswith(b"\n") else b"")
                    break
        active_lines.append(line)
    data = b"".join(active_lines)
    pattern = rb"\\input\s*\{([A-Za-z0-9_./-]+)\}"
    require(not re.search(rb"\\(?:input|include|includeonly)\b", re.sub(pattern, b"", data)),
            "unsupported TeX input syntax in " + name)
    def replace(match):
        raw = match[1]
        require(not raw.startswith(b"/"), "absolute TeX input path")
        child = "book/" + raw.decode() + ("" if raw.endswith(b".tex") else ".tex")
        expanded, nested = expand_tex(getter, child, seen)
        graph.update(nested)
        return expanded
    return re.sub(pattern, replace, data), graph


def verify_tex_graphs(root, source, declared):
    """Bind the actual committed and live recursive graph before a replay."""
    _, committed = expand_tex(lambda p: commit_blob(root, source, p))
    _, current = expand_tex(lambda p: relative_path(root, p).read_bytes())
    require(committed == current == declared and len(declared) == 36,
            "declared 36-file TeX map differs from committed/current active graph")
    return current


def get_pointer(value, pointer):
    require(pointer.startswith("/"), "JSON pointer must start with slash")
    current = value
    for component in pointer[1:].split("/"):
        token = component.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            require(token.isdigit() and int(token) < len(current), "missing JSON pointer: " + pointer)
            current = current[int(token)]
        else:
            require(isinstance(current, dict) and token in current, "missing JSON pointer: " + pointer)
            current = current[token]
    return current


def masked(value, pointers):
    result = copy.deepcopy(value)
    require(len(pointers) == len(set(pointers)), "duplicate comparison exclusion")
    require(not any(a != b and b.startswith(a + "/") for a in pointers for b in pointers),
            "overlapping comparison exclusions")
    for pointer in pointers:
        get_pointer(result, pointer)  # Missing expected locations fail, never silently skip.
        parent_path, _, token = pointer.rpartition("/")
        parent = result if not parent_path else get_pointer(result, parent_path)
        token = token.replace("~1", "/").replace("~0", "~")
        replacement = {"checkpoint_excluded_exact_pointer": pointer}
        if isinstance(parent, list):
            parent[int(token)] = replacement
        else:
            parent[token] = replacement
    return result


def strict_equal(before, after, pointers):
    require(encode(masked(before, pointers)) == encode(masked(after, pointers)),
            "scientific JSON differs outside enumerated provenance/timing exclusions")
    return [{"pointer": p, "before": get_pointer(before, p), "after": get_pointer(after, p)}
            for p in pointers]


def finite_nonnegative(value, name):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            "invalid timing/resource value: " + name)


def hash_map(value, label):
    require(isinstance(value, dict) and value, "missing " + label)
    for name, digest_value in value.items():
        require(isinstance(name, str) and str(Path(name)) == name, "noncanonical source path in " + label)
        relative_path(Path("/"), name)
        require(isinstance(digest_value, str) and re.fullmatch(r"[0-9a-f]{64}", digest_value),
                "invalid hash in " + label + ": " + name)
    return dict(value)


def mapped_hashes(record, pointer, shape="mapping"):
    value = get_pointer(record, pointer)
    if shape == "path-record-list":
        require(isinstance(value, list) and value, "empty approval path records")
        require(all(isinstance(row, dict) and "path" in row and "sha256" in row for row in value),
                "invalid approval path record")
        require(len(value) == len({row["path"] for row in value}), "duplicate approval path")
        value = {row["path"]: row["sha256"] for row in value}
    elif shape == "path-record-mapping":
        require(isinstance(value, dict) and value
                and all(isinstance(row, dict) and "sha256" in row for row in value.values()),
                "invalid approval path-record mapping")
        value = {path: row["sha256"] for path, row in value.items()}
    else:
        require(shape == "mapping", "unknown approval hash-map shape")
    return hash_map(value, "approval hash map")


def load_pin(base, pin):
    path = outer_path(base, pin["path"])
    record, frozen = json_snapshot(path)
    require(frozen == pin["identity"], "pinned receipt identity: " + str(path))
    require(isinstance(pin["required_values"], dict) and pin["required_values"],
            "explicit receipt decision predicates required")
    for pointer, value in pin["required_values"].items():
        require(encode(get_pointer(record, pointer)) == encode(value), "receipt predicate failed: " + pointer)
    return record, {str(path): frozen}


def approved_reference_identity(record, pin, outer, declared_reference):
    """Read either supported receipt shape without rewriting the approval."""
    value = get_pointer(record, pin["reference_identity_pointer"])
    shape = pin.get("reference_identity_shape", "identity")
    require(shape in ("identity", "path-record"), "unsupported approved reference identity shape")
    keys = {"sha256", "bytes"} | ({"path"} if shape == "path-record" else set())
    require(isinstance(value, dict) and set(value) == keys, "unexpected approved reference identity keys")
    require(isinstance(value["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", value["sha256"])
            and type(value["bytes"]) is int and value["bytes"] >= 0, "invalid approved reference identity types")
    if shape == "path-record":
        name = value["path"]
        require(isinstance(name, str) and str(Path(name)) == name, "noncanonical approved reference path")
        approved_path = relative_path(outer, name)
        declared_path = outer_path(outer, declared_reference)
        require(approved_path == declared_path and approved_path.resolve() == declared_path.resolve(),
                "approved reference path differs from declared outer reference")
    return {"sha256": value["sha256"], "bytes": value["bytes"]}


def recheck(frozen):
    for path, expected in frozen.items():
        require_unchanged(path, expected, "frozen input " + path)


def ready_spec(spec):
    require(type(spec.get("schema_version")) is int and spec["schema_version"] == 1
            and spec.get("ready") is True, "replay specification is unfinished")
    require(type(spec.get("unresolved")) is list and spec["unresolved"] == [],
            "explicit empty unresolved list required")
    require(spec["baseline_commit"] == BASELINE, "wrong baseline")
    require(isinstance(spec["source_commit"], str) and re.fullmatch(r"[0-9a-f]{40}", spec["source_commit"]),
            "final source commit required")
    root, outer = Path(spec["root"]).resolve(), Path(spec["outer"]).resolve()
    require(not outer.is_relative_to(root) and not root.is_relative_to(outer),
            "canonical and outer evidence directories must be disjoint")
    require(Path(spec["python"]).is_absolute(), "explicit Python executable required")
    for key in ("approved_source_sha256", "tex_input_sha256", "runtime_sha256",
                "reference_manuscript_sha256", "manuscript_observation_sha256",
                "reference_tex_observation_sha256", "tex_observation_sha256", "replay_guard_sha256"):
        hash_map(spec[key], key)
    require(len(spec["tex_input_sha256"]) == 36, "all 36 TeX inputs required")
    require(spec["replay_guard_sha256"] == merge_hashes(spec["approved_source_sha256"],
            spec["tex_input_sha256"], spec["runtime_sha256"], spec["manuscript_observation_sha256"],
            spec["tex_observation_sha256"]),
            "replay guard omits a reviewed, runtime or manuscript input")
    groups = spec["expected_groups"]
    require(isinstance(groups, list) and len(groups) == len(set(groups)) == 14,
            "all 14 final reviewed groups required")
    require({re.match(r"^(Q[1-4]|G(?:10|[1-9]))_", name).group(1)
             for name in groups if isinstance(name, str) and re.match(r"^(Q[1-4]|G(?:10|[1-9]))_", name)}
            == {*("Q" + str(i) for i in range(1, 5)), *("G" + str(i) for i in range(1, 11))},
            "unexpected finite group identifiers")
    changes = spec["allowed_manuscript_changes"]
    require(isinstance(changes, list) and len(changes) == len(set(changes))
            and set(changes) <= set(spec["approved_source_sha256"]),
            "manuscript metadata exceptions need exact approved source paths")
    require(set(spec["reference_manuscript_sha256"]) == set(spec["manuscript_observation_sha256"]),
            "manuscript observations may not add or remove paths")
    changed = {p for p, h in spec["reference_manuscript_sha256"].items()
               if h != spec["manuscript_observation_sha256"][p]}
    require(changed == set(changes), "metadata exceptions must equal actual stage-specific manuscript changes")
    old_tex, new_tex = spec["reference_tex_observation_sha256"], spec["tex_observation_sha256"]
    require(len(old_tex) == len(new_tex) == 46 and set(old_tex) == set(new_tex)
            and set(spec["tex_input_sha256"]) <= set(new_tex), "46 fixed TeX observations, including 36 active inputs, required")
    changes = spec["allowed_tex_observation_changes"]
    require(isinstance(changes, list) and len(changes) == len(set(changes))
            and set(changes) <= set(spec["approved_source_sha256"]) & set(spec["tex_input_sha256"]),
            "TeX observation exceptions need approved active source paths")
    require({p for p in old_tex if old_tex[p] != new_tex[p]} == set(changes),
            "TeX observation exceptions must equal actual stage-specific changes")
    merge_hashes(spec["reference_manuscript_sha256"], old_tex)
    return root, outer


def approved_spec(spec):
    root, outer = ready_spec(spec)
    repository(root)
    source = spec["source_commit"]
    require(git(root, "rev-list", "--parents", "-n", "1", source).decode().split() == [source, BASELINE],
            "source commit must be the baseline's direct child")
    changed = set(git(root, "diff", "--no-renames", "--name-only", BASELINE, source).decode().splitlines())
    require(changed == set(spec["approved_source_sha256"]), "source commit differs from exact approval allowlist")
    require(all(not p.startswith(("artifacts/", "site/", "research/", "packages/", "provenance/", "docs/execution/"))
                for p in spec["approved_source_sha256"]), "source checkpoint may not change preserved imports/artifacts")
    source_record, frozen = load_pin(outer, spec["source_approval"])
    pin = spec["source_approval"]
    require(mapped_hashes(source_record, pin["source_sha256_pointer"], pin.get("source_sha256_shape", "mapping"))
            == spec["approved_source_sha256"], "integration approval source map differs")
    code_record, code_frozen = load_pin(outer, spec["computation_approval"])
    frozen.update(code_frozen)
    pin = spec["computation_approval"]
    require(mapped_hashes(code_record, pin["runtime_sha256_pointer"], pin.get("runtime_sha256_shape", "mapping"))
            == spec["runtime_sha256"], "computation approval runtime map differs")
    require(mapped_hashes(code_record, pin["reference_manuscript_sha256_pointer"])
            == spec["reference_manuscript_sha256"], "author-stage manuscript freeze differs")
    require(mapped_hashes(code_record, pin["reference_tex_observation_sha256_pointer"])
            == spec["reference_tex_observation_sha256"], "author-stage 46-file TeX observation freeze differs")
    require(get_pointer(code_record, pin["expected_groups_pointer"]) == spec["expected_groups"],
            "exact group names differ from independent computation approval")
    reference_path = outer_path(outer, spec["reference"]["path"])
    reference, reference_identity = json_snapshot(reference_path)
    require(reference_identity == spec["reference"]["identity"]
            == approved_reference_identity(code_record, pin, outer, spec["reference"]["path"]),
            "approved author result identity differs")
    frozen[str(reference_path)] = reference_identity
    validate_report(reference, spec, clean=False)
    verify_tex_graphs(root, source, spec["tex_input_sha256"])
    for name, expected in spec["replay_guard_sha256"].items():
        require(identity(relative_path(root, name))["sha256"] == sha256(commit_blob(root, source, name)).hexdigest()
                == expected, "working/committed/approved input differs: " + name)
    recheck(frozen)
    return root, outer, reference, frozen


def source_rows(rows):
    require(isinstance(rows, list) and rows, "empty runtime source records")
    require(all(isinstance(row, dict) and set(row) == {"path", "sha256", "bytes"}
                and type(row["bytes"]) is int and row["bytes"] >= 0 for row in rows), "invalid runtime source row")
    require(len(rows) == len({row["path"] for row in rows}), "duplicate runtime source path")
    require([row["path"] for row in rows] == sorted(row["path"] for row in rows), "runtime paths must be sorted")
    return hash_map({row["path"]: row["sha256"] for row in rows}, "runtime source rows")


def timestamp(value):
    require(isinstance(value, str), "timestamp must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CheckpointError("invalid generated timestamp") from exc
    require(parsed.tzinfo is not None and parsed.utcoffset().total_seconds() == 0, "UTC timestamp required")
    return parsed


def validate_report(report, spec, clean):
    require(type(report["schema_version"]) is int and report["schema_version"] == 1
            and report["checks_passed"] is True, "finite report did not pass")
    require(encode(report["source_before"]) == encode(report["source_after"]),
            "report source metadata changed during run")
    require(set(report["groups"]) == set(spec["expected_groups"]), "finite group coverage differs")
    require(report["check_counts"] == spec["expected_check_counts"], "reviewed finite check counts differ")
    require(report["fixture"]["precisions"] == [70, 110], "70/110 requested precision pair required")
    timestamp(report["generated_at_utc"])
    finite_nonnegative(report["runtime"]["elapsed_seconds"], "elapsed_seconds")
    state = report["source_before"]
    required = {"git_commit", "git_dirty", "git_status_porcelain", "sources", "guarded_dependencies",
                "source_set_sha256", "live_manuscript_observation", "live_tex_source_observations", "scope"}
    require(set(state) == required, "unexpected finite source-state schema")
    sources, dependencies = source_rows(state["sources"]), source_rows(state["guarded_dependencies"])
    require(not sources.keys() & dependencies.keys(), "runtime and guarded dependency paths overlap")
    require(merge_hashes(sources, dependencies) == spec["runtime_sha256"], "runtime source hashes differ")
    require(sha256(encode({"sources": state["sources"], "dependencies": state["guarded_dependencies"]})).hexdigest()
            == state["source_set_sha256"], "runtime source aggregate digest differs")
    require(type(state["git_dirty"]) is bool and type(state["git_status_porcelain"]) is list
            and all(isinstance(line, str) for line in state["git_status_porcelain"])
            and state["git_dirty"] == bool(state["git_status_porcelain"]), "inconsistent Git metadata")
    require(state["git_commit"] == (spec["source_commit"] if clean else BASELINE), "wrong report Git stage")
    require(state["git_dirty"] is (not clean), "wrong report clean/author stage")
    observations = state["live_manuscript_observation"]
    expected = spec["manuscript_observation_sha256"] if clean else spec["reference_manuscript_sha256"]
    require(isinstance(observations, list) and len(observations) == len(expected)
            and len({row["path"] for row in observations}) == len(observations), "manuscript observation coverage")
    require([row["path"] for row in observations] == sorted(expected), "manuscript observations must be sorted")
    for row in observations:
        require(set(row) == {"path", "accepted_contract_source_sha256", "current_sha256", "matches_accepted_snapshot"},
                "unexpected manuscript observation schema")
        require(row["current_sha256"] == expected[row["path"]], "manuscript stage snapshot differs: " + row["path"])
        require(row["accepted_contract_source_sha256"] == report["fixture"]["accepted_manuscript_sha256"][row["path"]],
                "accepted mathematical source pin differs")
        require(type(row["matches_accepted_snapshot"]) is bool and row["matches_accepted_snapshot"]
                == (row["current_sha256"] == row["accepted_contract_source_sha256"]), "invalid manuscript-match flag")
    observations = state["live_tex_source_observations"]
    expected = spec["tex_observation_sha256"] if clean else spec["reference_tex_observation_sha256"]
    require(isinstance(observations, list) and len(observations) == 46
            and all(isinstance(row, dict) and set(row) == {"path", "sha256"} for row in observations),
            "unexpected broader TeX observation schema")
    require([row["path"] for row in observations] == sorted(expected)
            and {row["path"]: row["sha256"] for row in observations} == expected,
            "46-file TeX observation path/order/hash snapshot differs")


def finite_comparison(reference, candidate, spec):
    ready_spec(spec)
    validate_report(reference, spec, clean=False)
    validate_report(candidate, spec, clean=True)
    require(timestamp(candidate["generated_at_utc"]) >= timestamp(reference["generated_at_utc"]),
            "clean replay predates approved author result")
    allowed = ["/generated_at_utc", "/runtime/elapsed_seconds"]
    for name in ("source_before", "source_after"):
        allowed += [f"/{name}/{key}" for key in ("git_commit", "git_dirty", "git_status_porcelain")]
        for index, row in enumerate(reference[name]["live_manuscript_observation"]):
            if row["path"] in spec["allowed_manuscript_changes"]:
                allowed += [f"/{name}/live_manuscript_observation/{index}/{key}"
                            for key in ("current_sha256", "matches_accepted_snapshot")]
        for index, row in enumerate(reference[name]["live_tex_source_observations"]):
            if row["path"] in spec["allowed_tex_observation_changes"]:
                allowed.append(f"/{name}/live_tex_source_observations/{index}/sha256")
    # Only actually differing, individually checked metadata fields are masked.
    pointers = [p for p in allowed if encode(get_pointer(reference, p)) != encode(get_pointer(candidate, p))]
    exclusions = strict_equal(reference, candidate, pointers)
    return {"identical_scientific_payload": True, "check_counts": candidate["check_counts"],
            "groups": sorted(candidate["groups"]), "excluded_exact_JSON_pointers": pointers,
            "excluded_values": exclusions,
            "scope": "Strict report equality apart from individually validated stage metadata; no numerical replay or error certificate."}
