"""Reviewer-owned exact finite and matrix-word checks, independent of author oracles."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from hashlib import sha256
from itertools import product
import json
import math
from pathlib import Path
import random
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
OUT = HERE / "independent-results"
OUT.mkdir(exist_ok=False)
BINARY = HERE / "campaign-reviewed"
AUTHOR = HERE.parent / "torus-campaign/full8192-author-v2"
EPS = F(1, 10**6)
COUNTS = {}


def record(name, amount=1):
    COUNTS[name] = COUNTS.get(name, 0) + amount


def exact_metrics(lengths, start):
    values = list(map(F, lengths))
    start, end = F(start), F(2*start)
    events = sorted({start, end} | {x for v in values for x in (v, v/2) if start <= x <= end})

    def d(x, left=False):
        if left:
            return sum(v < 2*x for v in values) - 4*sum(v < x for v in values)
        return sum(v <= 2*x for v in values) - 4*sum(v <= x for v in values)

    maximum = max([abs(d(x))/x for x in events] + [abs(d(x, True))/x for x in events if x > start])
    integral = sum((d((a+b)/2)**2 * (1/a-1/b) for a, b in zip(events, events[1:])), F(0))/start
    return maximum, integral


def exact_envelope(lengths, start, epsilon):
    values = list(map(F, lengths))
    start, end = F(start), F(2*start)
    events = sorted({start, end} | {x for v in values for x in
                    (v-epsilon, v+epsilon, (v-epsilon)/2, (v+epsilon)/2) if start <= x <= end})
    low = high = F(0)
    for x in events:
        for left in (False, True) if x > start else (False,):
            cmp = (lambda a, b: a < b) if left else (lambda a, b: a <= b)
            nlo = lambda t: sum(cmp(v+epsilon, t) for v in values)
            nhi = lambda t: sum(cmp(v-epsilon, t) for v in values)
            a, b = nlo(2*x)-4*nhi(x), nhi(2*x)-4*nlo(x)
            low = max(low, F(0) if a <= 0 <= b else min(abs(a), abs(b))/x)
            high = max(high, max(abs(a), abs(b))/x)
    return low, high


def metric_checks():
    rng = random.Random(30112026)
    cases = [([], 1), ([1], 1), ([2, 2, 4, 5, 8], 2),
             ([8193], 2048), ([8192, math.nextafter(8192, math.inf)], 2048),
             ([1.5, math.nextafter(1.5, math.inf), 3, 6], 1)]
    for _ in range(130):
        start = rng.choice([1, 2, 4, 16, 2048])
        values = [float(F(rng.randrange(4, 96), 4)*start) for _ in range(rng.randrange(1, 18))]
        values = [v for v in values if 1 <= v <= 8193]
        if rng.randrange(2):
            values += [float(start), float(2*start), float(4*start)]
        cases.append((values, start))
    for i, (lengths, start) in enumerate(cases):
        p = OUT / f"metrics-{i}.txt"
        p.write_text("\n".join(map(repr, lengths)))
        maximum, q2 = exact_metrics(lengths, start)
        for epsilon_text, epsilon in [("0", F(0)), ("1e-6", EPS)]:
            result = OUT / f"metrics-{i}-{epsilon_text}.json"
            run = subprocess.run([str(BINARY), "metrics", str(p), str(start), str(result), epsilon_text, "1"],
                                 capture_output=True, text=True)
            assert run.returncode == 0, run.stderr
            native = json.loads(result.read_text())
            assert F(native["block"]["M"]["exact_rational_for_stored_events"]) == maximum
            assert math.isclose(native["block"]["Q_squared"], float(q2), abs_tol=2e-13, rel_tol=3e-15)
            low, high = exact_envelope(lengths, start, epsilon)
            assert F(native["sensitivity"]["lower_exact_rational"]) == low
            assert F(native["sensitivity"]["upper_exact_rational"]) == high
            record("independent_exact_metric_and_envelope_cases")
            if epsilon and 0 < len(lengths) <= 5:
                for shifts in product((-epsilon, F(0), epsilon), repeat=len(lengths)):
                    perturbed = [F(v)+s for v, s in zip(lengths, shifts)]
                    actual, _ = exact_metrics(perturbed, start)
                    assert low <= actual <= high
                    record("exact_perturbed_spectrum_enclosures")
    return {"cases": len(cases), "native_M_and_envelopes_exact": True, "Q_compared_to_exact_rational_integral": True}


def finite_checks():
    mu = [0, 1] + [0]*79
    for n in range(2, len(mu)):
        mu[n] = -sum(mu[d] for d in range(1, n) if n % d == 0)
    mertens = lambda x: sum(mu[1:math.floor(x)+1])
    gauges = [lambda p, q: F(max(abs(p), abs(q))),
              lambda p, q: F(abs(p)+abs(q)),
              lambda p, q: 3*max(F(p) if p >= 0 else F(-p, 2), F(q) if q >= 0 else F(-q, 3))]
    for gauge in gauges:
        for L in sorted({F(n, d) for d in (1, 2, 5) for n in range(d, 46)}):
            points = [(p, q, gauge(p, q)) for p in range(-math.ceil(L), math.ceil(L)+1)
                      for q in range(-math.ceil(L), math.ceil(L)+1) if p or q]
            count = lambda u: sum(r <= u for _, _, r in points)
            direct = sum(r <= L and math.gcd(p, q) == 1 for p, q, r in points)
            assert direct == sum(mu[d]*count(L/d) for d in range(1, math.floor(L)+1))
            record("primitive_mobius_square_diamond_asymmetric")
            for D in range(1, math.floor(L)+1):
                lhs = sum(mu[d]*count(L/d) for d in range(D+1, math.floor(L)+1))
                rhs = sum(mertens(L/r)-mertens(D) for _, _, r in points if r <= L/D)
                assert lhs == rhs
                record("large_divisor_exact_reversal")
    for n in range(1, 36):
        for a in (F(k, 4) for k in range(-24, 25)):
            for width in (F(0), F(1, 3), F(1), F(13, 4)):
                b = a+width
                direct = sum(math.gcd(k, n) == 1 for k in range(math.ceil(a), math.floor(b)+1))
                assert direct == sum(mu[d]*(math.floor(b/d)-math.ceil(a/d)+1) for d in range(1, n+1) if n % d == 0)
                record("closed_row_divisor_identity")
    for a, b, c in [(F(7, 3), F(-9, 7), F(2)), (F(-1, 3), F(11, 6), F(-8))]:
        N = lambda x: a*x*x+b*x+c
        E = lambda x: b*x+c
        for L in (F(1), F(13, 7), F(4)):
            for k in range(1, 11):
                assert E(L) == E(2**k*L)/4**k - sum((N(2**(j+1)*L)-4*N(2**j*L))/4**(j+1) for j in range(k))
                record("finite_dyadic_telescoping")
    for theta, result in [(F(1, 2), F(10, 11)), (F(7, 8), F(34, 35)), (F(11, 12), F(50, 51))]:
        a = F(2, 3)
        d = (2-a)/(3-a-theta)
        assert a+d*(1-a) == 2-d*(2-theta) == result
        record("exact_conditional_balance")
    lengths = [F(3, 2), F(3, 2), F(7, 3), F(4)]
    for L in (F(k, 3) for k in range(1, 61)):
        direct = sum(1 for ell in lengths for sign in (-1, 1) for k in range(1, 42) if k*ell <= L)
        assert direct == 2*sum(L//ell for ell in lengths)
        record("signed_all_point_multiple_identity")


def multiply(a, b):
    return (a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3],
            a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3])


def matrix_word_length(surface, slope, digits):
    """Christoffel mechanical words in explicit SL(2) matrices, no Farey recursion."""
    p, q = slope
    assert q >= 0 and math.gcd(p, q) == 1
    with localcontext() as ctx:
        ctx.prec = digits
        one, zero = Decimal(1), Decimal(0)
        if surface == "modular":
            A = tuple(map(Decimal, (2, 1, 1, 1)))
            B = tuple(map(Decimal, (2, -1, -1, 1)))
        else:
            y = 5-Decimal(11).sqrt()/2
            a = (8-y)/3
            d = y-a
            A = (Decimal(2), zero, zero, one/2)
            B = (a, one, a*d-one, d)
        if p < 0:
            A = (A[3], -A[1], -A[2], A[0])
        n = abs(p)+q
        matrix = (one, zero, zero, one)
        for i in range(n):
            matrix = multiply(matrix, B if (i+1)*q//n > i*q//n else A)
        trace = matrix[0]+matrix[3]
        assert trace > 2
        return 2*((trace+(trace*trace-4).sqrt())/2).ln()


def matrix_checks():
    report = json.loads((AUTHOR / "result.json").read_text())
    results = []
    for s in report["surfaces"]:
        surface = s["surface"]
        # Fresh native length32 output, followed by a non-pruned coordinate-box calculation.
        prefix = OUT / surface
        roots = ["3", "3", "3"] if surface == "modular" else ["2.5", format(5-math.sqrt(11)/2, ".17g"), "4"]
        run = subprocess.run([str(BINARY), "campaign", surface, "32", str(prefix), *roots, "1"], capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        raw = Path(str(prefix)+".curves.i32-i32-f64le").read_bytes()
        native = {(p, q): ell for p, q, ell in struct.iter_unpack("<iid", raw) if ell <= 32}
        direct = {}
        minimum_margin = Decimal("Infinity")
        max_small_error = Decimal(0)
        for q in range(81):
            for p in range(-80, 81):
                if math.gcd(p, q) != 1 or (q == 0 and p != 1):
                    continue
                ell = matrix_word_length(surface, (p, q), 100)
                minimum_margin = min(minimum_margin, abs(ell-32))
                if ell <= 32:
                    direct[p, q] = ell
                record("nonpruned_matrix_box_slope_evaluations")
        assert native.keys() == direct.keys()
        for slope, ell in direct.items():
            max_small_error = max(max_small_error, abs(ell-Decimal.from_float(native[slope])))
        assert max_small_error < Decimal("1e-10")
        selected = [r for r in s["precision_samples"]["samples"] if
                    "declared_twelve_nearest_below_final_cutoff_per_sector" in r["selection_reasons"] or
                    "maximum_sector_depth" in r["selection_reasons"]]
        long_rows = []
        for r in selected:
            slope = tuple(r["slope"])
            a = matrix_word_length(surface, slope, 100)
            b = matrix_word_length(surface, slope, 160)
            with localcontext() as ctx:
                ctx.prec = 170
                precision = abs(a-b)
                residual = abs(Decimal.from_float(r["length_binary64"])-b)
                author140 = abs(Decimal(r["direct_trace_length_140_digits"])-b)
            assert precision < Decimal("1e-85")
            assert author140 < Decimal("1e-120")
            assert residual < Decimal("1e-6")
            long_rows.append({"slope": list(slope), "word_length": abs(slope[0])+slope[1],
                              "matrix_length_100": str(a), "matrix_length_160": str(b),
                              "100_vs_160_residual": str(precision), "native_residual": str(residual),
                              "author_direct140_vs_matrix160": str(author140)})
            record("independent_long_matrix_words_two_precisions")
        results.append({"surface": surface, "cutoff": 32, "box": 80, "count": len(native),
                        "all_box_slope_membership_agrees": True, "minimum_matrix_cutoff_margin": str(minimum_margin),
                        "maximum_small_native_matrix_residual": str(max_small_error), "long_samples": long_rows})
    return results


def hash_audit():
    report = json.loads((AUTHOR / "result.json").read_text())
    rows = []
    for s in report["surfaces"]:
        for entry in s["raw_streams"]+[s["raw_native_report"]]:
            path = Path(entry["path"])
            h = sha256()
            with path.open("rb") as source:
                for chunk in iter(lambda: source.read(1 << 20), b""):
                    h.update(chunk)
            assert h.hexdigest() == entry["sha256"]
            if "bytes" in entry:
                assert path.stat().st_size == entry["bytes"] == 8*s["count_through_guard"]
            rows.append({"path": str(path), "sha256": h.hexdigest(), "bytes": path.stat().st_size})
    return rows


if __name__ == "__main__":
    begun = time.perf_counter()
    result = {"metrics": metric_checks()}
    print("Independent rational event tests passed", flush=True)
    finite_checks()
    print("Independent finite arithmetic identities passed", flush=True)
    result["matrix_word_checks"] = matrix_checks()
    print("Independent nonpruned matrix box and long word checks passed", flush=True)
    result["full_author_raw_hash_audit"] = hash_audit()
    result["checks"] = COUNTS
    result["seconds"] = time.perf_counter()-begun
    result["scope"] = "Exact finite rational identities and independent numerical matrix words; no every-node enclosure or asymptotic theorem."
    with (OUT / "summary.json").open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"checks": COUNTS, "seconds": result["seconds"]}), flush=True)
