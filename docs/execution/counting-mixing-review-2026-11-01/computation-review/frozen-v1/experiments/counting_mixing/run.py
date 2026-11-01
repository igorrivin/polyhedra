"""Run finite exact and multiprecision counting/mixing formula fixtures."""

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


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if not __package__:
    sys.path.insert(0, str(ROOT))

from experiments.counting_mixing import algebra, arithmetic, dynamics, numerics  # noqa: E402
from experiments.counting_mixing.exact import (  # noqa: E402
    integer, json_exact, matrix, positive, rational, require,
)


def validate_fixture(fixture):
    """Validate the bounded experiment before any expensive arithmetic starts."""
    keys = {
        "schema_version", "scope", "formula_contracts", "precisions", "polynomial_maximum", "sl2_matrices",
        "support_genera", "formal_length_cutoff", "mobius_maximum", "scalar_m", "matrix_power_maximum",
        "bruhat_c_maximum", "endpoint_frequencies", "primitive_matrices", "primitive_radii",
        "gaussian_pairs", "gaussian_times", "rank_one_boxes", "rank_two_terms", "orbit_determinants",
        "terminal_families", "lattice_cutoffs", "primitive_formal_lengths", "dyadic_starts", "dyadic_depths",
        "row_endpoints", "row_n", "balance_thetas",
    }
    if (not isinstance(fixture, dict) or set(fixture) != keys
            or type(fixture["schema_version"]) is not int or fixture["schema_version"] != 1):
        raise ValueError("unexpected fixture schema or keys")
    if (not isinstance(fixture["precisions"], list) or len(fixture["precisions"]) != 2
            or any(type(value) is not int for value in fixture["precisions"])
            or fixture["precisions"][0] >= fixture["precisions"][1]):
        raise ValueError("two increasing decimal precisions are required")
    for digits in fixture["precisions"]:
        numerics.context(digits)
    limits = {"polynomial_maximum": (12, 16), "formal_length_cutoff": (14, 20),
              "mobius_maximum": (1, 100), "matrix_power_maximum": (1, 64),
              "bruhat_c_maximum": (2, 50), "rank_two_terms": (20, 50)}
    for key, bounds in limits.items():
        integer(fixture[key], *bounds)
    sequence_keys = keys-set(limits)-{"schema_version", "scope", "formula_contracts"}
    for key in sequence_keys:
        if not isinstance(fixture[key], list) or not fixture[key] or len(fixture[key]) > 100:
            raise ValueError(f"{key} must be a bounded nonempty list")
    for key, bounds in (("support_genera", (2, 8)), ("scalar_m", (2, 20)),
                        ("orbit_determinants", (1, 3)), ("dyadic_depths", (1, 10)), ("row_n", (1, 100))):
        for value in fixture[key]:
            integer(value, *bounds)
    boxes = fixture["rank_one_boxes"]
    for value in boxes:
        integer(value, 1, 64)
    if boxes != sorted(set(boxes)):
        raise ValueError("rank-one boxes must strictly increase")
    for key in ("sl2_matrices", "primitive_matrices"):
        seen = set()
        for row in fixture[key]:
            needed = {"id", "A", "B"} if key == "sl2_matrices" else {"id", "matrix"}
            if not isinstance(row, dict) or set(row) != needed or not isinstance(row["id"], str) or row["id"] in seen:
                raise ValueError("matrix rows require distinct string IDs and exactly the documented keys")
            seen.add(row["id"])
            for item in needed-{"id"}:
                matrix(row[item])
    for key in ("primitive_radii", "lattice_cutoffs", "primitive_formal_lengths", "dyadic_starts"):
        for value in fixture[key]:
            if positive(value) > 20:
                raise ValueError(f"{key} exceeds finite fixture range")
    for pair in fixture["gaussian_pairs"]:
        if not isinstance(pair, list) or len(pair) != 2 or any(not rational("1/10") <= positive(v) <= 10 for v in pair):
            raise ValueError("Gaussian pairs must contain two positive bounded rational parameters")
    for value in fixture["gaussian_times"]:
        if abs(rational(value)) > 2:
            raise ValueError("Gaussian time range is [-2,2]")
    for pair in fixture["endpoint_frequencies"]:
        if not isinstance(pair, list) or len(pair) != 2 or any(type(v) is not int or abs(v) > 50 for v in pair):
            raise ValueError("endpoint frequency pair must contain two bounded integers")
    for row in fixture["terminal_families"]:
        if not isinstance(row, dict) or set(row) != {"h", "r", "c", "M", "T"}:
            raise ValueError("terminal family requires h,r,c,M,T")
        if any(not 0 < positive(row[key]) <= 5 for key in ("h", "r")) or not 1 <= positive(row["T"]) <= 5:
            raise ValueError("terminal family is outside the bounded domain")
        rational(row["c"])
        rational(row["M"])
    for pair in fixture["row_endpoints"]:
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError("row endpoints require two rationals")
        a, b = map(rational, pair)
        if a > b or max(abs(a), abs(b)) > 100:
            raise ValueError("row endpoints must be ordered and bounded")
    if {rational(v) for v in fixture["balance_thetas"]} != {rational(v) for v in ("1/2", "7/8", "11/12")}:
        raise ValueError("balance fixtures must retain the three contracted exponents")
    contracts = fixture["formula_contracts"]
    if not isinstance(contracts, dict) or not isinstance(fixture["scope"], str):
        raise ValueError("formula contracts and scope are required")
    metadata = {"extraction_baseline_commit", "author_contract_sha256"}
    formulas = {"trace_coefficients", "global_filter", "support_and_euler", "dynamics", "primitive_and_affine", "arithmetic"}
    if set(contracts) != metadata | formulas:
        raise ValueError("formula contract groups are incomplete")

    def is_digest(value, width):
        return isinstance(value, str) and len(value) == width and all(c in "0123456789abcdef" for c in value)

    if not is_digest(contracts["extraction_baseline_commit"], 40):
        raise ValueError("formula baseline must be a full commit identity")
    hashes = contracts["author_contract_sha256"]
    if (not isinstance(hashes, dict) or len(hashes) != 3
            or any(not isinstance(key, str) or not is_digest(value, 64) for key, value in hashes.items())):
        raise ValueError("three author contract SHA256 identities are required")
    for key in formulas:
        row = contracts[key]
        if (not isinstance(row, dict) or set(row) != {"labels", "formula"}
                or not isinstance(row["formula"], str) or not row["formula"]
                or not isinstance(row["labels"], list) or not row["labels"]
                or any(not isinstance(label, str) or not label for label in row["labels"])):
            raise ValueError("each formula contract requires nonempty labels and formula text")
    return fixture


def source_state():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).rstrip("\n")

    paths = sorted(path for path in HERE.rglob("*") if path.is_file() and path.suffix in (".py", ".json", ".md"))
    sources = []
    for path in paths:
        data = path.read_bytes()
        sources.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(data).hexdigest(), "bytes": len(data)})
    encoded = json.dumps(sources, sort_keys=True, separators=(",", ":")).encode()
    status = git("status", "--porcelain", "--untracked-files=all")
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(status),
            "git_status_porcelain": status.splitlines(), "source_set_sha256": sha256(encoded).hexdigest(),
            "sources": sources,
            "scope": "Companion code, tests, README, and pinned formula/input data only; no manuscript source freeze claimed."}


def verify_source_unchanged(before, after):
    require(before["sources"] == after["sources"] and before["git_commit"] == after["git_commit"],
            "companion source/input or repository HEAD changed during run; successful evidence will not be written")


def calculate(fixture):
    validate_fixture(fixture)
    exact = {
        "trace_coefficients": algebra.coefficient_checks(fixture["polynomial_maximum"]),
        "SL2_words": algebra.matrix_checks(fixture["sl2_matrices"]),
        "global_filter": algebra.global_filter_checks(fixture["polynomial_maximum"]),
        "finite_support": algebra.support_checks(fixture["support_genera"], fixture["formal_length_cutoff"],
                                                 fixture["mobius_maximum"]),
        "finite_Euler_convolution": algebra.euler_checks(fixture["formal_length_cutoff"]),
        "scalar_trace_mixing": dynamics.scalar_checks(fixture["scalar_m"], fixture["matrix_power_maximum"]),
        "terminal_exponential_algebra": dynamics.terminal_algebra_checks(fixture["terminal_families"]),
        "Bruhat_residues": dynamics.bruhat_checks(fixture["bruhat_c_maximum"], fixture["endpoint_frequencies"]),
        "primitive_parity": dynamics.primitive_checks(fixture["primitive_matrices"], fixture["primitive_radii"]),
        "Gaussian_algebra": dynamics.gaussian_exact_checks(fixture["gaussian_pairs"], fixture["rank_one_boxes"]),
        "Mobius_lattice": arithmetic.mobius_checks(fixture["lattice_cutoffs"]),
        "dyadic_events": arithmetic.dyadic_checks(fixture["primitive_formal_lengths"], fixture["dyadic_starts"],
                                                  fixture["dyadic_depths"]),
        "row_and_balance": arithmetic.row_balance_checks(fixture["row_endpoints"], fixture["row_n"],
                                                         fixture["balance_thetas"]),
    }
    numerical = {}
    for name, function in (
        ("affine_Gaussian", lambda ctx: numerics.gaussian_checks(ctx, fixture["gaussian_pairs"], fixture["gaussian_times"])),
        ("rank_two_Gaussian", lambda ctx: numerics.rank_two_checks(ctx, fixture["gaussian_times"],
                                                                 fixture["rank_two_terms"], fixture["orbit_determinants"])),
        ("endpoint_Fourier", lambda ctx: numerics.endpoint_checks(ctx, fixture["bruhat_c_maximum"], fixture["endpoint_frequencies"])),
        ("terminal_family", lambda ctx: numerics.terminal_checks(ctx, fixture["terminal_families"])),
    ):
        runs = [function(numerics.context(dps)) for dps in fixture["precisions"]]
        numerical[name] = {"runs": runs, "precision_comparison": numerics.precision_comparison(*runs)}
    return {"exact": exact, "numerical": numerical,
            "check_counts": {"exact": sum(group["check_count"] for group in exact.values()),
                             "numerical_formula_comparisons": sum(run["check_count"] for group in numerical.values() for run in group["runs"]),
                             "cross_precision_observations": sum(group["precision_comparison"]["comparison_count"] for group in numerical.values())}}


def write_result(output, result):
    # Serialize before exclusive creation, so NaN/Infinity cannot leave partial evidence.
    payload = json.dumps(json_exact(result), indent=2, allow_nan=False)+"\n"
    with output.open("x") as handle:
        handle.write(payload)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new JSON path; output may be outside the repository")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite existing evidence")
    if not args.output.parent.is_dir():
        parser.error("the output parent directory must already exist")
    if args.output.resolve().is_relative_to(HERE):
        parser.error("put evidence outside the companion source directory")
    started = time.perf_counter()
    before = source_state()
    fixture = json.loads((HERE/"fixture.json").read_text())
    calculations = calculate(fixture)
    after = source_state()
    verify_source_unchanged(before, after)
    result = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "all fixed checks passed; author computation, not independent approval", "checks_passed": True,
              "source": before, "source_at_completion": after, "fixture": fixture,
              "python_version": platform.python_version(), "python_executable": sys.executable,
              "platform": platform.platform(), "mpmath_version": mpmath.__version__,
              "arithmetic": {"exact": "Python integers and fractions.Fraction; sparse polynomial/length convolutions",
                             "floating": "mpmath cloned contexts with decimal precision 60 and 90 in the shipped fixture",
                             "comparison_tolerance": "10^(-(dps-15)) times max(1,abs(actual),abs(expected)); analytic tail allowance reported separately",
                             "certified_interval_backend": False},
              **calculations,
              "coverage_limits": [
                  "Finite formula fixtures do not prove global identities, asymptotic rates, spectral recovery, or geometric hypotheses.",
                  "SL2 trace inputs are rational matrices, not a common hyperbolic surface metric or geodesic classification.",
                  "The Euler model has formal generator lengths 2,3,4,7 and is truncated at its declared finite cutoff.",
                  "Primitive searches are complete only for the declared rational flat lattices and radii using exact coordinate bounds.",
                  "Gaussian identities concern moduli-averaged affine observables; the companion does not sample curve counts or construct genus-two models.",
                  "Independent numerical formulas share mpmath; precision agreement and residual tolerances are not interval certificates.",
                  "Analytic series and integral tail bounds exclude quadrature and roundoff errors; their numerical evaluations are uncertified.",
                  "Increasing finite rank-one sums do not prove divergence or turn a truncated raw product into an L2 observable.",
                  "No rectangle clipping, optional elementary gap plots, arbitrary affine-quotient mixing, or nonsquare-stratum classification.",
                  "No torus spectrum enumeration, full length-8192 campaign, historical-data recovery, or conditional sensitivity enclosure is performed here.",
                  "Author formula contracts are pinned in fixture data; concurrent manuscript edits are not part of this source freeze."
              ], "elapsed_seconds": time.perf_counter()-started}
    write_result(args.output, result)
    print(json.dumps({"output": str(args.output), "status": result["status"],
                      "source_set_sha256": before["source_set_sha256"], "check_counts": result["check_counts"],
                      "elapsed_seconds": result["elapsed_seconds"]}, sort_keys=True))


if __name__ == "__main__":
    main()
