"""Run finite quantum/geodesic checks; output is computation evidence, not approval."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import platform
import subprocess
import sys
import time

import mpmath
import sympy


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if not __package__:
    sys.path.insert(0, str(ROOT))

from experiments.quantum_geodesics import (  # noqa: E402
    figure_eight, geodesic_exact, geometry, kernels, klein, normalization, twist_integrals,
)
from experiments.quantum_geodesics.common import (  # noqa: E402
    json_exact, precision_comparison, require,
)


# Independently frozen required-fixture-profile-v1.json, reviewed as CR01/CR02.
# SHA256 uses UTF-8 canonical JSON with sorted keys, separators (",", ":"), no newline.
# These pins are not calculated from a fresh read of the mutable fixture.
SCIENTIFIC_PROFILE_SHA256 = "6ae75ae311c390acbb70234f4ea486940bcb46d47b6d9162105eba9f4d691735"
PROVENANCE_PROFILE_SHA256 = "fe470dc45b830a1458fb1bb4a7a5cdc5eb7e499ebe95cd522f4564b3b7b334f2"
SCIENTIFIC_PROFILE_KEYS = ("precisions", "guard_digits", "quantum", "geodesic")
PROVENANCE_PROFILE_KEYS = ("formula_contracts", "accepted_manuscript_sha256", "guarded_dependency_sha256")


def parse_fixture(text):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate fixture key: {key}")
            result[key] = value
        return result

    def reject_noninteger(token):
        raise ValueError(f"fixture numbers must be integers or exact rational strings: {token}")

    return json.loads(text, object_pairs_hook=unique_object, parse_constant=reject_noninteger,
                      parse_float=reject_noninteger)


def load_fixture():
    return parse_fixture((HERE/"fixture.json").read_text())


def profile_digest(profile):
    try:
        encoded = json.dumps(profile, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    except (TypeError, ValueError) as error:
        raise ValueError("fixture profile must contain finite JSON data") from error
    return sha256(encoded).hexdigest()


def validate_local_provenance(fixture):
    """Bind accepted declarations to local copies, never to mutable live sources."""
    contracts = fixture["formula_contracts"]
    bindings = (
        ("quantum", "sha256", "quantum-targets.md"),
        ("quantum", "review_acceptance_sha256", "quantum-mathematical-acceptance.json"),
        ("quantum", "accepted_source_freeze_sha256", "quantum-source-freeze.json"),
        ("geodesic", "sha256", "geodesic-targets.md"),
        ("geodesic", "review_acceptance_sha256", "geodesic-contract-acceptance.json"),
        ("geodesic", "final_source_review_sha256", "geodesic-source-acceptance.json"),
    )
    copies = {}
    for group, field, filename in bindings:
        data = (HERE/"contracts"/filename).read_bytes()
        if sha256(data).hexdigest() != contracts[group][field]:
            raise ValueError(f"accepted local provenance copy changed: {filename}")
        if filename.endswith(".json"):
            copies[filename] = json.loads(data)
    quantum = copies["quantum-mathematical-acceptance.json"]
    geodesic_contract = copies["geodesic-contract-acceptance.json"]
    geodesic_source = copies["geodesic-source-acceptance.json"]
    declared_source_set = contracts["geodesic"]["accepted_source_set_sha256"]
    if (quantum["accepted_author_freeze_sha256"] != contracts["quantum"]["accepted_source_freeze_sha256"]
            or geodesic_contract["contract_sha256"] != contracts["geodesic"]["sha256"]
            or geodesic_contract["independent_finite_evidence"]["sha256"] != contracts["geodesic"]["independent_probe_result_sha256"]
            or geodesic_source["companion_contract_acceptance_sha256"] != contracts["geodesic"]["review_acceptance_sha256"]
            or geodesic_source["companion_contract_sha256"] != contracts["geodesic"]["sha256"]
            or geodesic_source["canonical_source_set_sha256"] != declared_source_set
            or profile_digest(geodesic_source["canonical_sources_sha256"]) != declared_source_set):
        raise ValueError("accepted local contract/source provenance links disagree")
    accepted = {**quantum["accepted_canonical_sha256"], **quantum["all_live_dependency_sha256"],
                **geodesic_source["canonical_sources_sha256"]}
    for path, pin in fixture["accepted_manuscript_sha256"].items():
        if accepted.get(path) != pin:
            raise ValueError(f"accepted manuscript pin disagrees with local provenance: {path}")


def validate_fixture(fixture):
    keys = {"schema_version", "scope", "precisions", "guard_digits", "formula_contracts",
            "accepted_manuscript_sha256", "guarded_dependency_sha256", "quantum", "geodesic"}
    if (not isinstance(fixture, dict) or set(fixture) != keys
            or type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1):
        raise ValueError("unexpected fixture keys or version")
    if not isinstance(fixture["scope"], str) or not fixture["scope"].strip():
        raise ValueError("fixture scope must be a nonempty description")
    scientific = {key: fixture[key] for key in SCIENTIFIC_PROFILE_KEYS}
    if profile_digest(scientific) != SCIENTIFIC_PROFILE_SHA256:
        raise ValueError("complete accepted scientific profile changed: missing, duplicate, substituted or partial coverage")
    provenance = {key: fixture[key] for key in PROVENANCE_PROFILE_KEYS}
    if profile_digest(provenance) != PROVENANCE_PROFILE_SHA256:
        raise ValueError("complete accepted provenance profile changed: contracts, 14 source pins and 3 dependency guards required")
    validate_local_provenance(fixture)
    return fixture


def source_state(fixture):
    validate_fixture(fixture)

    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).rstrip("\n")

    paths = sorted(path for path in HERE.rglob("*")
                   if path.is_file() and not path.name.startswith(".") and path.suffix in (".py", ".json", ".md"))
    sources = []
    for path in paths:
        data = path.read_bytes()
        sources.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(data).hexdigest(), "bytes": len(data)})
    dependencies = []
    for relative, expected in sorted(fixture["guarded_dependency_sha256"].items()):
        data = (ROOT/relative).read_bytes()
        actual = sha256(data).hexdigest()
        require(actual == expected, f"guarded dependency changed: {relative}")
        dependencies.append({"path": relative, "sha256": actual, "bytes": len(data)})
    live_manuscript = []
    for relative, accepted in sorted(fixture["accepted_manuscript_sha256"].items()):
        path = ROOT/relative
        actual = sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        live_manuscript.append({"path": relative, "accepted_contract_source_sha256": accepted,
                                "current_sha256": actual, "matches_accepted_snapshot": actual == accepted})
    encoded = json.dumps({"sources": sources, "dependencies": dependencies}, sort_keys=True,
                         separators=(",", ":")).encode()
    status = git("status", "--porcelain", "--untracked-files=all")
    live_tex = [{"path": str(path.relative_to(ROOT)), "sha256": sha256(path.read_bytes()).hexdigest()}
                for path in sorted((ROOT/"book").rglob("*.tex")) if not path.name.startswith(".")]
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(status),
            "git_status_porcelain": status.splitlines(), "sources": sources, "guarded_dependencies": dependencies,
            "source_set_sha256": sha256(encoded).hexdigest(), "live_manuscript_observation": live_manuscript,
            "live_tex_source_observations": live_tex,
            "scope": "Runtime code, fixture, tests, README, local accepted contracts and guarded old algebra are frozen. Live manuscript is observed separately; outer author evidence is not a runtime dependency."}


def verify_source_unchanged(before, after):
    require(before == after, "full source observations, dependency, Git HEAD, or Git dirty status changed during run")


def paired_runs(function, fixture, guards=None):
    guards = fixture["guard_digits"] if guards is None else guards
    runs = [function(digits, guards) for digits in fixture["precisions"]]
    return {"runs": runs, "cross_precision": precision_comparison(*runs)}


def calculate(fixture):
    validate_fixture(fixture)
    quantum = fixture["quantum"]
    groups = {
        "Q1_figure_eight": {
            "labels": ["eq:introfigureproduct"],
            "exact": figure_eight.exact_checks(quantum["figure_eight_N"]),
            "numerical": paired_runs(lambda d, g: figure_eight.numerical_checks(quantum["figure_eight_N"], d, g), fixture)},
        "Q2_klein_geometry": {"labels": ["eq:Kleinvolumeexpansion", "eq:firstcurvaturevolume"],
                              "exact": klein.exact_checks(quantum["klein"])},
        "Q3_peripheral_filling": {
            "labels": ["eq:introfillingkernel", "eq:introRTgrowth"],
            "exact": normalization.peripheral_checks(quantum["peripheral"], fixture["guarded_dependency_sha256"]),
            "numerical": paired_runs(lambda d, g: normalization.shift_checks(quantum["peripheral"], d, g), fixture)},
        "Q4_charge_curvature": {"labels": ["eq:introfirstmoment", "eq:introcurvaturemeasure", "eq:flatSeibergbounds"],
                                "exact": normalization.charge_checks(quantum["charges"])},
    }
    geo = fixture["geodesic"]
    default = geo["guard_digits"]["default"]
    groups.update({
        "G1_torus_unfolding": {"exact": geodesic_exact.unfolding_factors(),
                              "numerical": paired_runs(lambda d, g: kernels.fermi_checks(geo["unfolding"], d, g), fixture, default)},
        "G2_pants_traces": {"exact": geodesic_exact.trace_checks(geo["traces"])},
        "G3_figure_eight_kernel": {"exact": geodesic_exact.kernel_telescope(geo["kernel"]["depths"]),
                                   "numerical": paired_runs(lambda d, g: kernels.kernel_checks(geo["kernel"], d, g), fixture, geo["guard_digits"]["kernel"])},
        "G4_local_distance": {"exact": geodesic_exact.hessian_checks(),
                              "numerical": paired_runs(lambda d, g: geometry.distance_checks(geo["distance"], d, g), fixture, default)},
        "G5_seams_torus_holonomy": {"numerical": paired_runs(lambda d, g: geometry.holonomy_checks(geo["holonomy"], d, g), fixture, geo["guard_digits"]["holonomy"])},
        "G6_twist_coarea": {"numerical": paired_runs(lambda d, g: twist_integrals.integral_checks(geo["integrals"], d, g), fixture, default)},
        "G7_twist_partition": {"exact": geodesic_exact.partition_checks(geo["partition"]),
                               "numerical": paired_runs(lambda d, g: kernels.twist_checks(geo["partition"], d, g), fixture, default)},
        "G8_endpoint_matching": {"exact": geodesic_exact.position_checks(geo["matching"]),
                                 "numerical": paired_runs(lambda d, g: geometry.matching_checks(geo["matching"], d, g), fixture, default)},
        "G9_cusp_decoration": {"exact": geodesic_exact.cusp_checks(geo["cusp"]),
                               "numerical": paired_runs(lambda d, g: geometry.cusp_numerics(geo["cusp"], d, g), fixture, default)},
        "G10_boundary_shadows": {"exact": geodesic_exact.shadow_factor(),
                                  "numerical": paired_runs(lambda d, g: kernels.shadow_checks(geo["shadow"], d, g), fixture, default)},
    })
    counts = {"exact": sum(group["exact"]["check_count"] for group in groups.values() if "exact" in group),
              "numerical_formula_comparisons": sum(run["check_count"] for group in groups.values()
                                                   for run in group.get("numerical", {}).get("runs", [])),
              "cross_precision_observations": sum(group["numerical"]["cross_precision"]["comparison_count"]
                                                  for group in groups.values() if "numerical" in group)}
    return {"groups": groups, "check_counts": counts}


def write_result(path, result):
    payload = json.dumps(json_exact(result), indent=2, allow_nan=False)+"\n"
    with path.open("x") as handle:
        handle.write(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new evidence file in an existing directory")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite existing evidence")
    if not args.output.parent.is_dir():
        parser.error("output parent must already exist")
    if args.output.resolve().is_relative_to(HERE):
        parser.error("put evidence outside companion source")
    started = time.perf_counter()
    fixture = load_fixture()
    validate_fixture(fixture)
    before = source_state(fixture)
    calculations = calculate(fixture)
    after = source_state(fixture)
    verify_source_unchanged(before, after)
    result = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "finite checks passed; evidence stage and independent reviews are recorded separately",
              "checks_passed": True, "source_before": before, "source_after": after, "fixture": fixture,
              "runtime": {"python_version": platform.python_version(), "python_executable": sys.executable,
                          "platform": platform.platform(), "mpmath_version": mpmath.__version__,
                          "sympy_version": sympy.__version__, "elapsed_seconds": time.perf_counter()-started},
              "arithmetic": {"exact": "SymPy integer/rational/polynomial and radical algebra; guarded Fraction series helper",
                             "floating": "cloned mpmath contexts; precision and guard digits recorded per group",
                             "acceptance": "positive signals require positive inputs and relative residual <=10^(-(requested_digits-15)); other checks require explicit scales",
                             "interval_certified": False},
              **calculations,
              "coverage_limits": [
                  "Finite checks do not prove asymptotic theorems, global geometry, completeness or moduli identities.",
                  "No general colored-Jones/6j evaluator, filling/GMC solver, thimble or torsion computation.",
                  "Exact series-tail formulas bound truncation only; numerical rounding and quadrature are separate.",
                  "Floating formulas share mpmath; cross-precision observations are not independent or interval certificates.",
                  "Accepted source/review hashes are provenance; successful computation is not reviewer approval.",
                  "Geodesic checks concern finite local formulas, one kernel iteration and one twist lattice; no whole-surface sum, topology, discreteness or reconstruction certificate."
              ]}
    write_result(args.output, result)
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "source_set_sha256": before["source_set_sha256"], "check_counts": result["check_counts"],
                      "elapsed_seconds": result["runtime"]["elapsed_seconds"]}, sort_keys=True))


if __name__ == "__main__":
    main()
