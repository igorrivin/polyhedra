# Adapted for standalone repository replay; see ../evidence-files.json.
"""Independent precision review; does not reuse the implementation's reductions."""

from __future__ import annotations

import argparse

from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import platform
import sys

import mpmath as mp
import numpy as np

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True, help="Consolidated repository root")
parser.add_argument("--output", type=Path, required=True, help="New JSON output path outside preserved evidence")
replay_options = parser.parse_args()
ROOT = replay_options.repo.resolve()
if not (ROOT / "packages/volume-toolkit").is_dir():
    parser.error("--repo must name the consolidated repository root")
if replay_options.output.exists():
    parser.error("--output must not already exist; preserve prior evidence")
replay_options.output.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "packages/volume-toolkit"))
from ideal_poly_volume_toolkit import geometry as geometry  # noqa: E402


def raw_reference(z, dps):
    # Direct definition at sufficient precision to resolve the cancellation.
    # There is deliberately no 1/z or 1-z reduction of the argument.
    with mp.workdps(dps):
        point = mp.mpc(mp.mpf(z.real), mp.mpf(z.imag))
        return mp.im(mp.polylog(2, point)) + mp.arg(1 - point) * mp.log(abs(point))


def main():
    rng = np.random.default_rng(61031)
    cases = []
    for exponent in (-308, -300, -100, -20, -4, 0, 4, 20, 100, 300, 308):
        scale = 10.0 ** exponent
        for _ in range(4):
            angle = rng.uniform(-np.pi, np.pi)
            cases.append((f"radial-{exponent}", complex(scale * np.cos(angle), scale * np.sin(angle)), 450))
    smallest = np.nextafter(0.0, 1.0)
    maximum = np.finfo(float).max
    for label, z in (
        ("largest-both", complex(maximum, maximum)),
        ("largest-negative-real", complex(-maximum, maximum)),
        ("smallest-both", complex(smallest, smallest)),
        ("smallest-imag-at-one", complex(1, smallest)),
        ("smallest-imag-at-minus-one", complex(-1, smallest)),
        ("below-one-tiny-imag", complex(np.nextafter(1.0, 0.0), 1e-300)),
        ("above-one-tiny-imag", complex(np.nextafter(1.0, np.inf), 1e-300)),
        ("unit-upper", complex(0.5, np.sqrt(3) / 2)),
        ("unit-lower", complex(0.5, -np.sqrt(3) / 2)),
        ("reduction-boundary-left", complex(np.nextafter(0.5, 0), 0.75)),
        ("reduction-boundary-right", complex(np.nextafter(0.5, 1), 0.75)),
        ("huge-skew-positive", complex(1e308, 1e-308)),
        ("huge-skew-negative", complex(-1e308, 1e-308)),
        ("huge-skew-smallest", complex(maximum, smallest)),
        ("huge-skew-axis-swapped", complex(smallest, maximum)),
    ):
        precision = 1100 if "skew" in label else 450
        cases.append((label, z, precision))
        cases.append((label + "-conjugate", z.conjugate(), precision))

    points = np.asarray([z for _, z, _ in cases], dtype=np.complex128)
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        batch = geometry.bloch_wigner(points.reshape(2, -1)).ravel()
        scalar = np.asarray([geometry.bloch_wigner(z) for z in points])
    assert np.array_equal(batch, scalar)
    rows = []
    for (label, z, dps), observed in zip(cases, batch):
        reference = raw_reference(z, dps)
        high = geometry.bloch_wigner_mp(z, dps=120)
        expected = float(reference)
        tolerance = 8 * abs(np.spacing(expected)) + 4e-14 * abs(expected)
        error = abs(observed - expected)
        with mp.workdps(dps):
            high_relative = abs((high - reference) / reference)
            binary_relative = abs((mp.mpf(float(observed)) - reference) / reference)
            rows.append({
                "case": label, "real_hex": z.real.hex(), "imag_hex": z.imag.hex(),
                "raw_reference_dps": dps, "reference": mp.nstr(reference, 145),
                "observed_binary64": float(observed), "reference_binary64": expected,
                "absolute_binary64_error": float(error), "absolute_tolerance": float(tolerance),
                "binary64_relative_error": mp.nstr(binary_relative, 20),
                "mp120_relative_error": mp.nstr(high_relative, 20),
                "binary64_passed": bool(error <= tolerance),
                "mp120_passed": bool(high_relative < mp.mpf("1e-112")),
            })
    failures = [row for row in rows if not row["binary64_passed"] or not row["mp120_passed"]]

    compatibility = []
    with mp.workdps(160):
        values = [Fraction(1, 10**400), Decimal("0.12345678901234567890123456789"),
                  np.int64(1), np.float32(0.3), np.longdouble("0.12345678901234567890123456789")]
        for value in values:
            if isinstance(value, Fraction):
                point = mp.mpf(value.numerator) / value.denominator
            elif isinstance(value, Decimal):
                point = mp.mpf(str(value))
            elif isinstance(value, np.floating):
                numerator, denominator = value.as_integer_ratio()
                point = mp.mpf(numerator) / denominator
            else:
                point = mp.mpf(int(value))
            # Direct integral is independent of the Clausen evaluation.
            reference = point * mp.quad(lambda s: -mp.log(2 * mp.sin(point * s)), [0, 1])
            observed = geometry.lob_exact(value, dps=120)
            relative = abs((observed - reference) / reference)
            compatibility.append({"input_type": type(value).__name__,
                                  "relative_error": mp.nstr(relative, 20),
                                  "passed": bool(relative < mp.mpf("1e-112"))})

    with mp.workdps(29):
        for function, args in (
            (geometry.lobachevsky_mp, ("not-a-number",)),
            (geometry.bloch_wigner_mp, (("nan", "1"),)),
            (geometry.triangle_volume_from_points_mp, (0, 0, 1)),
        ):
            try:
                function(*args, dps=95)
            except (ValueError, TypeError):
                pass
            else:
                raise AssertionError("invalid input did not raise")
            assert mp.mp.dps == 29
    for z in (0j, 1 + 0j, -maximum + 0j, maximum + 0j):
        assert geometry.bloch_wigner(z) == 0
        assert geometry.bloch_wigner_mp(z) == 0
    for z in (complex(np.nan, 0), complex(np.inf, 0), complex(0, np.inf)):
        for function in (geometry.bloch_wigner, geometry.bloch_wigner_mp):
            try:
                function(z)
            except ValueError:
                pass
            else:
                raise AssertionError("nonfinite input did not raise")

    module = Path(geometry.__file__).resolve()
    report = {
        "source_module": str(module), "source_sha256": sha256(module.read_bytes()).hexdigest(),
        "probe_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "python": platform.python_version(), "numpy": np.__version__, "mpmath": mp.__version__,
        "scope": "Bounded independent raw-formula comparison, not a uniform floating-point error enclosure.",
        "case_count": len(rows), "binary64_and_mp_failures": failures, "cases": rows,
        "compatibility": compatibility,
        "scalar_batch_parity": True, "real_axis_limits": True,
        "nonfinite_rejected": True, "exception_precision_restored": True,
        "all_passed": not failures and all(row["passed"] for row in compatibility),
    }
    destination = replay_options.output
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"cases": len(rows), "failures": len(failures),
                      "compatibility_passed": all(row["passed"] for row in compatibility),
                      "all_passed": report["all_passed"], "report": str(destination)}, indent=2))
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
