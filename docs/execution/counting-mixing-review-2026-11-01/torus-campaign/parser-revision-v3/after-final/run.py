"""New full torus campaign; every output is exclusive and numerical in scope.

The native core holds sorted binary64 lengths, streams slope identities, and
computes exact rational *conditional* M envelopes. This driver independently
checks the fixed64 exact oracle, a moderate direct-trace traversal, selected
100/140-digit paths, raw hashes, and direct metric counts. It never overwrites
the historical bounded experiment or claims recovery of the missing archive.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left, bisect_right
from collections import deque
from datetime import datetime, timezone
from decimal import Decimal, localcontext
from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
import math
import mmap
from pathlib import Path
import platform
import struct
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / "experiments/section30"
FROZEN_RESULT = ROOT / "artifacts/section30/result.json"
FROZEN_SHA256 = "762b07184f76893c810f3e9832fd44dc7e4b292c1a64aae61aa26832e02884a1"
BASELINE_COMMIT = "9c8b61790aaa674902b9d60e80122c318a578bcc"
FLAGS = ["-O3", "-std=c++17", "-Wall", "-Wextra", "-Werror",
         "-fno-fast-math", "-ffp-contract=off"]
RADIUS = Fraction(1, 1_000_000)
SCALE = 2**53 * 5**6


def digest(path):
    h = sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def source_hashes():
    paths = sorted(p for p in HERE.rglob("*") if p.is_file()
                   and "__pycache__" not in p.parts)
    paths += [OLD / "run.py", OLD / "fixture.json", FROZEN_RESULT]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def write_json(path, report):
    with Path(path).open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write("\n")


def load_frozen_driver():
    spec = importlib.util.spec_from_file_location("frozen_section30_oracle", OLD / "run.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical(p, q):
    if math.gcd(p, q) != 1:
        raise ValueError("nonprimitive slope")
    return (-p, -q) if q < 0 or (q == 0 and p < 0) else (p, q)


def sector_path(slope):
    """Invert a sector's Stern--Brocot coordinates, without recursive calls."""
    p, q = canonical(*slope)
    if (p, q) in ((1, 0), (0, 1), (1, 1)):
        return -1, ""
    if p < 0:
        sector, a, b = 0, -p, q
    elif p > q:
        sector, a, b = 1, p-q, q
    else:
        sector, a, b = 2, q-p, p
    path = []
    while a != b:
        if a > b:
            n = (a-1)//b
            path.append("L"*n)
            a -= n*b
        else:
            n = (b-1)//a
            path.append("R"*n)
            b -= n*a
    if a != 1:
        raise ArithmeticError("nonprimitive sector coordinates")
    return sector, "".join(path)


def decimal_roots(record):
    """Evaluate input coefficients, rationalizing opposite signs exactly."""
    def rational(value):
        f = Fraction(value)
        return Decimal(f.numerator)/Decimal(f.denominator)
    values = []
    for a_text, b_text in record["traces_qsqrt11"]:
        a, b = Fraction(a_text), Fraction(b_text)
        if a*b < 0:
            values.append(rational(a*a-11*b*b)/(rational(a)-rational(b)*Decimal(11).sqrt()))
        else:
            values.append(rational(a)+rational(b)*Decimal(11).sqrt())
    return tuple(values)


def direct_path_length(record, slope, digits):
    """Independent non-log direct traces, with genuine scoped decimal precision."""
    sector, path = sector_path(slope)
    with localcontext() as ctx:
        ctx.prec = digits
        x, y, z = decimal_roots(record)
        if sector == -1:
            trace = {(1, 0): x, (0, 1): y, (1, 1): z}[tuple(slope)]
        else:
            a, b, opposite = ((x, y, z), (x, z, y), (y, z, x))[sector]
            for turn in path:
                c = a*b-opposite
                if c <= max(a, b):
                    raise ArithmeticError("direct precision path lost outward growth")
                if turn == "L":
                    a, b, opposite = a, c, b
                else:
                    a, b, opposite = c, b, a
            trace = a*b-opposite
        return 2*((trace+(trace*trace-4).sqrt())/2).ln()


def direct_moderate_spectrum(record, cutoff):
    """Independent FIFO direct-trace traversal, never using logarithmic updates.

    At cutoff <=512, one outward product is below exp(512), so ordinary
    binary64 direct traces cannot overflow on these fixtures. This is an
    independent arithmetic/traversal comparison, not a completeness proof.
    """
    if cutoff > 512:
        raise ValueError("direct binary64 traversal is restricted to cutoff512")
    with localcontext() as ctx:
        ctx.prec = 100
        x, y, z = map(float, decimal_roots(record))
    rows = {(1, 0): 2*math.acosh(x/2), (0, 1): 2*math.acosh(y/2),
            (1, 1): 2*math.acosh(z/2)}
    queue = deque([((1, 0), (0, -1), x, y, z),
                   ((1, 0), (1, 1), x, z, y),
                   ((0, 1), (1, 1), y, z, x)])
    while queue:
        left, right, a, b, opposite = queue.popleft()
        trace = a*b-opposite
        if not math.isfinite(trace):
            raise ArithmeticError("moderate direct trace overflow")
        ell = 2*math.acosh(trace/2)
        if ell > cutoff:
            continue
        raw = left[0]+right[0], left[1]+right[1]
        slope = canonical(*raw)
        if slope in rows:
            raise ArithmeticError("duplicate direct-trace slope")
        rows[slope] = ell
        queue.append((left, raw, a, trace, b))
        queue.append((raw, right, trace, b, a))
    return rows


def native_records(path):
    data = Path(path).read_bytes()
    if len(data) % 16:
        raise ValueError("malformed native curve stream")
    rows = {}
    for p, q, length in struct.iter_unpack("<iid", data):
        if (p, q) in rows:
            raise ArithmeticError("duplicate native slope")
        rows[p, q] = length
    return rows


class MappedLengths:
    """Read-only random access to the compact external stream."""
    def __init__(self, path):
        self.stream = Path(path).open("rb")
        self.data = mmap.mmap(self.stream.fileno(), 0, access=mmap.ACCESS_READ)
        if len(self.data) % 8:
            raise ValueError("malformed binary64 stream")
    def __len__(self):
        return len(self.data)//8
    def __getitem__(self, i):
        if i < 0:
            i += len(self)
        if not 0 <= i < len(self):
            raise IndexError(i)
        return struct.unpack_from("<d", self.data, 8*i)[0]
    def close(self):
        self.data.close()
        self.stream.close()


def validate_small(native, record, old_report, oracle):
    roots = oracle.fixture_roots(record)  # Exact Markoff and reduced inequalities.
    reference, coverage100 = oracle.box_spectrum(roots, 64, 100)
    higher, coverage140 = oracle.box_spectrum(roots, 64, 140)
    frozen = {tuple(c["slope"]): c for c in old_report["curves"]}
    observed = {tuple(c["slope"]): c["length_binary64"]
                for c in native["curves_through_64"]}
    if observed.keys() != reference.keys() or reference.keys() != higher.keys() or higher.keys() != frozen.keys():
        raise ArithmeticError("full64 native/exact100/exact140/frozen slope-set mismatch")
    with localcontext() as ctx:
        ctx.prec = 160
        precision = max(abs(reference[s][1]-higher[s][1]) for s in observed)
        native_error = max(abs(Decimal.from_float(observed[s])-higher[s][1]) for s in observed)
        frozen_error = max(abs(higher[s][1]-Decimal(frozen[s]["length_decimal"])) for s in observed)
    if precision > Decimal("1e-90") or native_error > Decimal("1e-9") or frozen_error > Decimal("1e-120"):
        raise ArithmeticError("fixed64 reference comparison tolerance failed")
    for slope in frozen:
        if higher[slope][0].json() != frozen[slope]["trace_qsqrt11"]:
            raise ArithmeticError("exact algebraic trace differs from frozen record")
    return {"curve_count": len(observed), "all_four_slope_sets_equal": True,
            "fresh_exact_trace_box_at_100_digits": coverage100,
            "fresh_exact_trace_box_at_140_digits": coverage140,
            "maximum_100_vs_140_digit_length_residual": str(precision),
            "maximum_native_vs_140_digit_length_residual": str(native_error),
            "maximum_fresh140_vs_frozen140_length_residual": str(frozen_error),
            "exact_trace_pairs_equal_frozen": True}


def validate_samples(native, record):
    rows = []
    for sample in native["selected_curves"]:
        slope = tuple(sample["slope"])
        sector, path = sector_path(slope)
        if sample["sector"] != sector or sample["depth"] != (0 if sector == -1 else len(path)+1):
            raise ArithmeticError("slope-to-path reconstruction disagrees with native depth/sector")
        lower = direct_path_length(record, slope, 100)
        higher = direct_path_length(record, slope, 140)
        with localcontext() as ctx:
            ctx.prec = 160
            precision = abs(lower-higher)
            residual = abs(Decimal.from_float(sample["length_binary64"])-higher)
        if precision > Decimal("1e-85") or residual > Decimal("1e-6"):
            raise ArithmeticError("selected-path comparison tolerance failed")
        rows.append({**sample, "path_after_first_mediant": path,
                     "direct_trace_length_100_digits": str(lower),
                     "direct_trace_length_140_digits": str(higher),
                     "precision_absolute_residual": str(precision),
                     "native_absolute_residual": str(residual)})
    long = [r for r in rows if r["length_binary64"] > 64]
    if native["cutoff"] == 8192 and len(long) < 30:
        raise ArithmeticError("fewer than thirty declared long-path samples")
    near_final = [r for r in rows if "declared_twelve_nearest_below_final_cutoff_per_sector" in r["selection_reasons"]]
    near_sector_counts = [sum(r["sector"] == sector for r in near_final) for sector in range(3)]
    if native["cutoff"] == 8192:
        if (len({tuple(r["slope"]) for r in near_final}) != 36 or near_sector_counts != [12, 12, 12]
                or min(r["length_binary64"] for r in near_final) < 6144):
            raise ArithmeticError("declared thirty-six near-final-scale samples are missing")
    return {"selection_declared_in_source": True, "samples": rows,
            "sample_count": len(rows), "long_sample_count_length_above_64": len(long),
            "sample_count_length_at_least4096": sum(r["length_binary64"] >= 4096 for r in rows),
            "sample_count_length_at_least6144": sum(r["length_binary64"] >= 6144 for r in rows),
            "sample_count_depth_at_least1024": sum(r["depth"] >= 1024 for r in rows),
            "near_final_declared_sample_count": len(near_final), "near_final_per_sector_counts": near_sector_counts,
            "near_final_minimum_length": min(r["length_binary64"] for r in near_final),
            "near_final_maximum_length": max(r["length_binary64"] for r in near_final),
            "maximum_precision_absolute_residual": str(max(Decimal(r["precision_absolute_residual"]) for r in rows)),
            "maximum_native_absolute_residual": str(max(Decimal(r["native_absolute_residual"]) for r in rows)),
            "every_node_error_certified": False}


def moderate_check(native, record, records_path):
    cutoff = native["cutoff"]
    observed = {s: ell for s, ell in native_records(records_path).items() if ell <= cutoff}
    independent = direct_moderate_spectrum(record, cutoff)
    if observed.keys() != independent.keys():
        raise ArithmeticError("independent moderate traversal slope sets differ")
    residual = max(abs(observed[s]-independent[s]) for s in observed)
    if residual > 1e-8:
        raise ArithmeticError("independent moderate trace length comparison failed")
    # Declared deterministic coordinate-box probes, including points far beyond
    # the selected length cutoff; direct decimal traces decide membership.
    box = math.ceil(5*cutoff/2)
    probes = {(1, 0), (0, 1), (1, 1), (1, box), (-1, box), (box, 1)}
    state = 20261101
    while len(probes) < 128:
        state = (1664525*state+1013904223) % 2**32
        p = state % (2*box+1)-box
        state = (1664525*state+1013904223) % 2**32
        q = state % box+1
        if math.gcd(p, q) == 1:
            probes.add((p, q))
    probe_rows = []
    for slope in sorted(probes):
        ell = direct_path_length(record, slope, 100)
        contained = ell <= cutoff
        if contained != (slope in observed):
            raise ArithmeticError("deterministic slope membership probe mismatch")
        probe_rows.append({"slope": list(slope), "direct_decimal_length": str(ell), "included": contained})
    return {"method": "separately_written_FIFO_direct_binary64_trace_traversal",
            "same_slope_set": True, "count": len(observed),
            "maximum_native_vs_direct_length_residual": residual,
            "deterministic_decimal_membership_probes": probe_rows}


def check_stream_metrics(native, path, oracle):
    lengths = MappedLengths(path)
    try:
        if len(lengths) != native["count_through_guard"]:
            raise ArithmeticError("raw length count mismatch")
        checks = []
        for row in native["counts"]:
            if bisect_right(lengths, row["L"]) != row["N"]:
                raise ArithmeticError("independent dyadic count mismatch")
        for row in native["blocks"]:
            point = row["M"]["position_binary64"]
            selector = bisect_left if row["M"]["side"] == "left_limit" else bisect_right
            d = selector(lengths, 2*point)-4*selector(lengths, point)
            if d != row["M"]["D"]:
                raise ArithmeticError("independent maximizing direct count mismatch")
            exact = Fraction(abs(d), 1)/Fraction.from_float(point)
            if exact != Fraction(row["M"]["exact_rational_for_stored_events"]):
                raise ArithmeticError("independent maximizing rational mismatch")
            checks.append({"T": row["T"], "maximizing_D": d, "exact_M_fraction_verified": True})
        # Full direct metrics and Fraction sensitivity through64 use a separate
        # Python implementation; large rows use native every-100003rd interval
        # direct counts plus Python checks at each retained maximizer.
        short = [lengths[i] for i in range(bisect_right(lengths, 64))]
        small_checks = []
        for row, bounds in zip(native["blocks"], native["conditional_M_bounds"]):
            # Final fraction differences and ordering use Python's unbounded
            # integers, independent of the native checked 128-bit comparison.
            lo, hi = Fraction(bounds["lower_exact_rational"]), Fraction(bounds["upper_exact_rational"])
            if lo > hi:
                raise ArithmeticError("Python rational bound ordering failed")
            bounds["width_exact_rational"] = str(hi-lo)
            bounds["width_approx"] = float(hi-lo)
            if row["T"] > 16:
                continue
            direct = oracle.direct_block_metrics(short, row["T"])
            conditional = oracle.conditional_maximum_bounds(short, row["T"], "1e-6")
            residual = {"M": abs(direct["M"]-row["M"]["value"]), "Q": abs(direct["Q"]-row["Q"])}
            if max(residual.values()) > 1e-12:
                raise ArithmeticError("independent small full metric integration failed")
            for key in ("lower_exact_rational", "upper_exact_rational"):
                if Fraction(conditional[key]) != Fraction(bounds[key]):
                    raise ArithmeticError("independent exact Fraction sensitivity differs")
            small_checks.append({"T": row["T"], "direct_full_metrics": direct,
                                 "absolute_residuals": residual, "exact_sensitivity_fractions_agree": True})
        all_point_small = []
        for row in native["counts"]:
            if row["L"] > 64:
                continue
            exact = 2*sum(Fraction(row["L"], 1)//Fraction.from_float(ell) for ell in short)
            if exact != row["A_signed_all_point_for_stored_lengths"]:
                raise ArithmeticError("independent exact all-point floor identity mismatch")
            all_point_small.append({"L": row["L"], "A": exact})
        return {"python_maximizer_checks": checks, "small_full_direct_checks": small_checks,
                "all_point_direct_fraction_checks_through64": all_point_small}
    finally:
        lengths.close()


def build_report(output_dir, cutoff, phase, preflight=None):
    if cutoff not in (64, 512, 8192):
        raise ValueError("reviewed driver cutoffs are64,512,8192")
    if digest(FROZEN_RESULT) != FROZEN_SHA256:
        raise ArithmeticError("frozen64 result identity drift")
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=False)
    frozen_sources = source_hashes()
    preflight_record = None
    if cutoff == 8192:
        if not preflight:
            raise ValueError("full campaign requires a successful same-source512 preflight")
        preflight_record = json.loads(Path(preflight).read_text())
        if (preflight_record["cutoff"] != 512 or not preflight_record["checks_passed"]
                or preflight_record["provenance"]["source_sha256"] != frozen_sources):
            raise ArithmeticError("preflight is not a successful current-source512 run")
    head = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).splitlines()
    if phase == "clean_replay" and status:
        raise ArithmeticError("clean replay requires a clean source checkout")
    compiler = "/usr/bin/clang++"
    compiler_version = subprocess.check_output([compiler, "--version"], text=True)
    binary = output_dir / "torus_campaign"
    command = [compiler, *FLAGS, str(HERE / "campaign.cpp"), "-o", str(binary)]
    receipts = []
    def run_command(argv):
        start = time.perf_counter()
        result = subprocess.run(argv, text=True, capture_output=True, check=False)
        receipts.append({"argv": list(map(str, argv)), "returncode": result.returncode,
                         "elapsed_seconds": time.perf_counter()-start,
                         "stdout": result.stdout, "stderr": result.stderr})
        if result.returncode:
            write_json(output_dir / "failed-command-receipts.json", receipts)
            raise RuntimeError("campaign subprocess failed: "+result.stderr)
    begun = time.perf_counter()
    run_command(command)
    oracle = load_frozen_driver()
    fixture = json.loads((OLD / "fixture.json").read_text())
    frozen = json.loads(FROZEN_RESULT.read_text())
    report = {"schema_version": "1.0", "experiment_id": "section30-new-full-torus-campaign-v1",
              "phase": phase, "cutoff": cutoff, "evidence_status": "new_numerical_campaign_pending_independent_review",
              "certified": False, "recovered_historical_provenance": False,
              "provenance": {"source_commit": head, "initial_revision_baseline": BASELINE_COMMIT,
                  "repository_dirty_at_start": bool(status), "git_status_porcelain_at_start": status,
                  "source_sha256": frozen_sources, "frozen64_result_sha256": FROZEN_SHA256,
                  "native_binary_sha256": digest(binary), "compiler": compiler_version, "compiler_flags": FLAGS,
                  "python": sys.version, "platform": platform.platform(), "machine": platform.machine(),
                  "generated_at_utc": datetime.now(timezone.utc).isoformat()},
              "fixture": {"surfaces": fixture["surfaces"], "unoriented_slope_convention": fixture["count_convention"]},
              "sensitivity_hypotheses": {"epsilon_exact": str(RADIUS), "all_listed_length_errors_at_most_epsilon_assumed": True,
                  "complete_list_and_no_omitted_curve_entry_assumed": True, "hypotheses_certified": False,
                  "scope": "fixed finite list; true-spectrum interpretation additionally requires completeness/no-entry",
                  "full_and_half_events_derived_from_length_error": True,
                  "common_denominator": str(SCALE), "endpoint_numerators_below": "2^81",
                  "curve_count_below": "2^26", "D_absolute_values_below": "2^29",
                  "ratio_comparison_products_below": "2^110",
                  "arithmetic": "exact IEEE754 extraction, checked signed128 products, Python integer final fraction checks"},
              "all_point_convention": "A(L)=2 sum floor(L/ell), signed positive multiples of unoriented primitive slopes; hyperbolic length units, not shortest-vector rescaling",
              "raw_stream_layout": {"lengths.f64le": "sorted IEEE754 little-endian binary64;8 bytes/curve; multiplicity retained",
                  "slopes.i32le": "two little-endian signed32 coordinates;8 bytes/curve; roots then sectors0,1,2, left-child-first DFS",
                  "curves.i32-i32-f64le": "moderate runs only: aligned little-endian int32 p,int32 q,binary64 length;16 bytes/curve"},
              "surfaces": []}
    if preflight_record:
        report["provenance"]["moderate_preflight"] = {"path": str(Path(preflight).resolve()), "sha256": digest(preflight)}
    for record in fixture["surfaces"]:
        start = time.perf_counter()
        oracle.fixture_roots(record)
        with localcontext() as ctx:
            ctx.prec = 100
            roots = [format(float(x), ".17g") for x in decimal_roots(record)]
        prefix = output_dir / record["id"]
        run_command([str(binary), "campaign", record["id"], str(cutoff), str(prefix),
                     *roots, "1" if cutoff <= 512 else "0"])
        native = json.loads(Path(str(prefix)+".native.json").read_text())
        old_surface = next(s for s in frozen["surfaces"] if s["id"] == record["id"])
        native["fixed64_validation"] = validate_small(native, record, old_surface, oracle)
        if cutoff <= 512:
            native["independent_moderate_validation"] = moderate_check(native, record, str(prefix)+".curves.i32-i32-f64le")
        else:
            native["independent_moderate_validation"] = {"same_source_preflight_reference": str(Path(preflight).resolve()),
                                                        "scope": "moderate512 comparison, not a full8192 oracle"}
        native["precision_samples"] = validate_samples(native, record)
        native["independent_metric_validation"] = check_stream_metrics(native, str(prefix)+".lengths.f64le", oracle)
        native["raw_streams"] = [{"path": str(p), "bytes": p.stat().st_size, "sha256": digest(p)}
                                  for p in sorted(output_dir.glob(record["id"]+".*")) if p.suffix != ".json"]
        native["peak_rss_bytes"] = native["raw_peak_rss"] * (1 if sys.platform == "darwin" else 1024)
        native["validation_and_native_elapsed_seconds"] = time.perf_counter()-start
        # Full small list and native selected rows remain in the hashed native
        # report; the compact result carries their validations and enriched samples.
        native.pop("curves_through_64")
        native.pop("selected_curves")
        native["raw_native_report"] = {"path": str(prefix)+".native.json", "sha256": digest(str(prefix)+".native.json")}
        report["surfaces"].append(native)
        print(json.dumps({"surface": record["id"], "cutoff": cutoff, "count": native["count_through_cutoff"],
                          "checks_passed": True, "native_seconds": native["timing_seconds"]["native_total"],
                          "peak_rss_bytes": native["peak_rss_bytes"]}), flush=True)
    if source_hashes() != frozen_sources:
        raise ArithmeticError("campaign source or fixed input drifted during execution")
    if subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip() != head:
        raise ArithmeticError("source commit changed during campaign")
    report["source_input_immutability_gate_passed"] = True
    report["checks_passed"] = True
    report["elapsed_seconds"] = time.perf_counter()-begun
    report["command_receipts"] = receipts
    write_json(output_dir / "result.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoff", type=int, choices=(64, 512, 8192), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--phase", choices=("author", "clean_replay"), default="author")
    parser.add_argument("--preflight", type=Path)
    args = parser.parse_args()
    report = build_report(args.output_dir, args.cutoff, args.phase, args.preflight)
    print(json.dumps({"result": str(args.output_dir / "result.json"), "checks_passed": report["checks_passed"]}))


if __name__ == "__main__":
    main()
