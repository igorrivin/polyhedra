"""Read-only checkpoint gates, adapted from the Section 15 checkpoint pattern.

No assertion is an acceptance gate. JSON equality retains all fields except the
concrete pointers enumerated below; unknown fields remain comparison inputs.
"""
from __future__ import annotations

import copy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import subprocess

BASELINE = "9c8b61790aaa674902b9d60e80122c318a578bcc"
REL = "docs/execution/counting-mixing-review-2026-11-01"
RESULTS = {
    "counting": "artifacts/counting_mixing/result.json",
    "torus": "artifacts/torus_campaign/result.json",
}
PDF = "artifacts/counting-mixing-review-2026-11-01/monograph-working-draft.pdf"
ENV = {**os.environ, "GIT_OPTIONAL_LOCKS": "0", "PYTHONDONTWRITEBYTECODE": "1"}
TIMING_KEYS = (
    "enumeration_and_identity_io", "sort", "sorted_stream_io", "metrics",
    "sensitivity", "sample_replay", "all_point_counts", "native_total",
)
KNOWN_DANGLING = {
    "dangling blob dba78d2f1770521c3cfaef91091f1c296ec57abd",
    "dangling blob 4c37b26b85df0662fbc6ab71661713083ac3a7c1",
}


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


def load_json(path):
    def bad_constant(value):
        raise CheckpointError("nonfinite JSON constant: " + value)
    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), "nonfinite JSON number: " + value)
        return parsed
    return json.loads(Path(path).read_text(), object_pairs_hook=object_pairs,
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


def counting_comparison(before, after):
    required = {"git_commit", "git_dirty", "git_status_porcelain", "source_set_sha256", "sources", "scope"}
    for report in (before, after):
        require(report["checks_passed"] is True, "finite companion did not pass")
        require(report["source"] == report["source_at_completion"], "finite companion source drift")
        for key in ("source", "source_at_completion"):
            state = report[key]
            require(set(state) == required, "unexpected finite source-state schema")
            require(sha256(encode(state["sources"])).hexdigest() == state["source_set_sha256"],
                    "invalid finite source-set digest")
            require(len(state["sources"]) == len({row["path"] for row in state["sources"]}),
                    "duplicate finite source path")
            require(all(set(row) == {"path", "sha256", "bytes"} for row in state["sources"]),
                    "unexpected finite source row schema")
        finite_nonnegative(report["elapsed_seconds"], "finite elapsed_seconds")
    # The complete source objects are retained in the receipt, independently
    # bound to approved and committed files by verify_checkpoint.py.
    pointers = ["/generated_at_utc", "/elapsed_seconds", "/source", "/source_at_completion"]
    require(before["source"]["scope"] == after["source"]["scope"], "finite source scope changed")
    exclusions = strict_equal(before, after, pointers)
    return {"identical_scientific_payload": True, "check_counts": after["check_counts"],
            "excluded_exact_JSON_pointers": pointers, "excluded_values": exclusions}


def torus_pointers():
    pointers = [
        "/phase", "/elapsed_seconds", "/provenance/source_commit",
        "/provenance/repository_dirty_at_start", "/provenance/git_status_porcelain_at_start",
        "/provenance/source_sha256", "/provenance/native_binary_sha256",
        "/provenance/generated_at_utc", "/provenance/moderate_preflight/path",
        "/provenance/moderate_preflight/sha256", "/command_receipts/0/argv/10",
    ]
    for i in (0, 1):
        prefix = "/surfaces/" + str(i)
        pointers += [prefix + "/timing_seconds/" + key for key in TIMING_KEYS]
        pointers += [prefix + "/" + key for key in (
            "raw_peak_rss", "peak_rss_bytes", "validation_and_native_elapsed_seconds",
            "raw_native_report/path", "raw_native_report/sha256",
            "independent_moderate_validation/same_source_preflight_reference",
        )]
        pointers += [prefix + "/raw_streams/" + str(j) + "/path" for j in (0, 1)]
    for i in (0, 1, 2):
        pointers.append("/command_receipts/" + str(i) + "/elapsed_seconds")
    for i in (1, 2):
        pointers += ["/command_receipts/" + str(i) + suffix for suffix in ("/argv/0", "/argv/4", "/stdout")]
    return pointers


def torus_report_comparison(before, after):
    """Pure report comparison. Raw/native file identity checks are separate."""
    for report in (before, after):
        require(report["checks_passed"] is True and report["source_input_immutability_gate_passed"] is True,
                "full campaign checks did not pass")
        require(report["certified"] is False and report["recovered_historical_provenance"] is False,
                "campaign status overstates finite evidence")
        require(report["cutoff"] == 8192 and [s["surface"] for s in report["surfaces"]] == ["modular", "asymmetric"],
                "full campaign surfaces/cutoff")
        require(len(report["command_receipts"]) == 3, "expected compile and two native commands")
        require(len(report["command_receipts"][0]["argv"]) == 11, "compiler command shape changed")
        for i, command in enumerate(report["command_receipts"]):
            require(command["returncode"] == 0 and command["stderr"] == "", "campaign command failed")
            finite_nonnegative(command["elapsed_seconds"], "command elapsed_seconds")
            if i:
                require(len(command["argv"]) == 9, "native command shape changed")
                s = report["surfaces"][i - 1]
                prefix = re.escape(s["surface"] + " cutoff=8192 count=" + str(s["count_through_cutoff"]))
                require(re.fullmatch(prefix + r" native_seconds=[0-9.e+\-]+ raw_peak_rss=[0-9]+\n", command["stdout"]),
                        "native stdout has unexpected content")
        for s in report["surfaces"]:
            require(set(s["timing_seconds"]) == set(TIMING_KEYS), "native timing schema changed")
            require(len(s["raw_streams"]) == 2, "full run needs exactly two streams per surface")
            require([b["T"] for b in s["blocks"]] == [2**k for k in range(2, 12)], "all ten blocks per surface required")
            require([b["T"] for b in s["conditional_M_bounds"]] == [2**k for k in range(2, 12)], "all conditional rows required")
            for value in s["timing_seconds"].values():
                finite_nonnegative(value, "native timing")
            for key in ("raw_peak_rss", "peak_rss_bytes", "validation_and_native_elapsed_seconds"):
                finite_nonnegative(s[key], key)
        finite_nonnegative(report["elapsed_seconds"], "campaign elapsed_seconds")
    require(set(before["provenance"]["source_sha256"]) == set(after["provenance"]["source_sha256"]),
            "campaign source paths changed")
    pointers = torus_pointers()
    exclusions = strict_equal(before, after, pointers)
    return {"identical_scientific_payload": True, "blocks": 20,
            "surface_counts": {s["surface"]: s["count_through_cutoff"] for s in after["surfaces"]},
            "excluded_exact_JSON_pointers": pointers, "excluded_values": exclusions}


def torus_raw_comparison(before, after, outer):
    rows = []
    native_exclusions = ["/raw_peak_rss"] + ["/timing_seconds/" + key for key in TIMING_KEYS]
    for old, new in zip(before["surfaces"], after["surfaces"], strict=True):
        native = []
        for report in (old, new):
            record = report["raw_native_report"]
            p = outer_path(outer, record["path"])
            require(digest(p) == record["sha256"], "native report identity mismatch")
            payload = load_json(p)
            require(set(payload["timing_seconds"]) == set(TIMING_KEYS), "native report timing schema")
            native.append(payload)
        strict_equal(*native, native_exclusions)
        for a, b in zip(old["raw_streams"], new["raw_streams"], strict=True):
            require(Path(a["path"]).name == Path(b["path"]).name, "stream filename changed")
            expected = {"sha256": a["sha256"], "bytes": a["bytes"]}
            require(expected == {"sha256": b["sha256"], "bytes": b["bytes"]}, "raw stream identity changed")
            for record in (a, b):
                require(identity(outer_path(outer, record["path"])) == expected, "raw stream bytes changed")
            rows.append({"name": Path(a["path"]).name, **expected})
    return {"native_reports_identical_except_exact_pointers": native_exclusions,
            "four_raw_streams_verified_both_runs": rows}


def fsck(root):
    process = subprocess.run(["git", "fsck", "--full"], cwd=root, env=ENV, capture_output=True, text=True)
    require(process.returncode == 0 and not process.stderr, "Git fsck failed; verifier never removes metadata: " + process.stdout + process.stderr)
    require(set(process.stdout.splitlines()) <= KNOWN_DANGLING, "unexpected Git fsck output: " + process.stdout)
    return {"returncode": process.returncode, "stdout": process.stdout, "stderr": process.stderr,
            "metadata_cleanup_performed": False}
