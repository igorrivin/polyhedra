"""Replay the independently discovered MP negative-real-axis defect and fix."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
import types

import mpmath as mp


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(args.repo.resolve() / "packages/volume-toolkit"))
    from ideal_poly_volume_toolkit import geometry

    source = Path(__file__).with_name("precision-reviewed-geometry.py").read_bytes()
    before_hash = hashlib.sha256(source).hexdigest()
    if before_hash != "6b779e418e9a5328404b7cb18be9c2cdf7226a6c480fe5e235df0490cceaa51e":
        raise ValueError("reviewed source snapshot hash mismatch")
    before = types.ModuleType("reviewed_geometry_before_negative_axis_fix")
    exec(compile(source, "reviewed-geometry:" + before_hash, "exec"), before.__dict__)
    cases = []
    for real in ("-0.125", "-0.8", "-1", "-1.25", "-2"):
        for magnitude in ("1e-150", "1e-300"):
            for imag in (magnitude, "-" + magnitude):
                old_value = before.bloch_wigner_mp((real, imag), dps=120)
                value = geometry.bloch_wigner_mp((real, imag), dps=120)
                triangle = geometry.triangle_volume_from_points_mp((real, imag), 1, 0, dps=120)
                with mp.workdps(450):
                    z = mp.mpc(real, imag)
                    # Deliberately no reciprocal/reflection/fractional-linear map.
                    reference = mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z))
                    coefficient = -mp.log(1 - z.real) / z.real - mp.log(abs(z.real)) / (1 - z.real)
                    leading = z.imag * coefficient
                    error = abs(value / reference - 1)
                    triangle_error = abs(triangle / abs(reference) - 1)
                    row = {
                        "real": real, "imaginary": imag, "working_dps": 120,
                        "reference_dps": 450, "before": mp.nstr(old_value, 130),
                        "after": mp.nstr(value, 130), "direct_reference": mp.nstr(reference, 130),
                        "before_relative_error": mp.nstr(abs(old_value / reference - 1), 25),
                        "after_relative_error": mp.nstr(error, 25),
                        "triangle_relative_error": mp.nstr(triangle_error, 25),
                        "reference_vs_linear_limit_relative_error": mp.nstr(abs(reference / leading - 1), 25),
                        "passed": bool(value * reference > 0 and error < mp.mpf("1e-110")
                                       and triangle_error < mp.mpf("1e-110")),
                    }
                    cases.append(row)
    result = {
        "scope": "Uncommitted reviewed patch versus corrected MP kernel; direct 450-digit definition and real-axis derivative reference, not an interval proof.",
        "before_geometry_sha256": before_hash,
        "after_geometry_sha256": hashlib.sha256(Path(geometry.__file__).read_bytes()).hexdigest(),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "cases": cases, "all_passed": all(row["passed"] for row in cases),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    before_record = {
        "source_snapshot": "precision-reviewed-geometry.py",
        "geometry_sha256": before_hash,
        "provenance": "Fresh replay of the hash-verified reviewed source snapshot by precision-negative-axis-probe.py.",
        "cases": [{"real": row["real"], "imag": row["imaginary"],
                   "observed_120dps": row["before"],
                   "raw_reference_450dps": row["direct_reference"],
                   "relative_error": row["before_relative_error"]} for row in cases],
    }
    args.output.with_name("precision-negative-axis-before.json").write_text(
        json.dumps(before_record, indent=2, allow_nan=False) + "\n"
    )
    print(json.dumps({"cases": len(cases), "all_passed": result["all_passed"],
                      "geometry_sha256": result["after_geometry_sha256"]}))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
