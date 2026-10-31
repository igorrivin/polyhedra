"""Compare a named historical geometry source with the corrected checkout."""

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import types

import mpmath as mp
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    sys.path.insert(0, str(repo / "packages/volume-toolkit"))
    from ideal_poly_volume_toolkit import geometry as new

    base = "285a6cb71473ba1f238983e062662cf890cbba05"
    source = subprocess.check_output([
        "git", "-C", str(repo), "show",
        base + ":packages/volume-toolkit/ideal_poly_volume_toolkit/geometry.py",
    ], text=True)
    old = types.ModuleType("precision_baseline_geometry")
    exec(compile(source, "git:" + base + ":geometry.py", "exec"), old.__dict__)
    report = {
        "base_commit": base,
        "old_geometry_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "new_geometry_sha256": hashlib.sha256(Path(new.__file__).read_bytes()).hexdigest(),
        "new_module_path": new.__file__,
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "comparison_scope": "Same represented inputs; MP comparisons are numerical, not enclosures. Current source may be uncommitted.",
        "cases": [],
    }
    for value, description in [
        ("0.123456789012345678901234567890123456789", "decimal string"),
        ("1e-400", "decimal string below binary64 range"),
        (Fraction(1, 10**400), "Fraction(1, 10**400)"),
    ]:
        with mp.workdps(23):
            old_value = old.lob_exact(value, dps=105)
            old_precision = mp.mp.dps
        with mp.workdps(23):
            new_value = new.lob_exact(value, dps=105)
            new_precision = mp.mp.dps
        with mp.workdps(130):
            theta = (mp.mpf(value.numerator) / value.denominator
                     if isinstance(value, Fraction) else mp.mpf(value))
            reference = (mp.quad(lambda t: -mp.log(2 * mp.sin(t)), [0, theta])
                         if theta > mp.mpf("1e-100") else theta * (1 - mp.log(2 * theta)))
            report["cases"].append({
                "case": "lobachevsky", "input_kind": description,
                "input": str(value), "old": mp.nstr(old_value, 115),
                "new": mp.nstr(new_value, 115), "reference": mp.nstr(reference, 115),
                "old_absolute_error": mp.nstr(abs(old_value - reference), 20),
                "new_absolute_error": mp.nstr(abs(new_value - reference), 20),
                "old_precision_after_from_23": old_precision,
                "new_precision_after_from_23": new_precision,
            })
    for point in [0j, 1 + 0j, complex(1e300, 1e300), complex(1e308, 1e308)]:
        with np.errstate(all="ignore"):
            old_value = old.bloch_wigner(point)
        report["cases"].append({
            "case": "binary64_bloch_wigner", "input_real_hex": point.real.hex(),
            "input_imag_hex": point.imag.hex(),
            "old": old_value if np.isfinite(old_value) else None,
            "old_is_finite": bool(np.isfinite(old_value)),
            "new": new.bloch_wigner(point),
            "reference_float": float(new.bloch_wigner_mp(point, dps=120)),
        })
    report["compatibility_removable_zero"] = {
        "old": str(old.bloch_wigner_mpmath(0)), "new": new.bloch_wigner_mpmath(0),
    }
    finite = np.array([0j, 1 + 0j, 0.2 + 0.8j, -0.5 + 0.4j, 2 - 0.3j])
    with mp.workdps(23):
        old_volume = old.ideal_poly_volume_via_delaunay(finite, mode="exact", dps=80)
    with mp.workdps(23):
        new_volume = new.ideal_poly_volume_via_delaunay(finite, mode="mpmath", dps=80)
    report["cases"].append({
        "case": "five_vertices_legacy_vs_mpmath",
        "inputs_real_imag": [[float(z.real), float(z.imag)] for z in finite],
        "old_float": old_volume, "new_float": new_volume,
        "difference": new_volume - old_volume,
        "scope": "Both use binary64 Qhull geometry; new evaluation uses MP cross-ratios and fsum before float conversion.",
    })
    rng = np.random.default_rng(1031)
    max_relative, max_absolute = 0.0, 0.0
    for exponent, phase in zip(rng.uniform(-308, 308, 128), rng.uniform(-np.pi, np.pi, 128)):
        point = complex((10.0**exponent) * np.cos(phase), (10.0**exponent) * np.sin(phase))
        observed = new.bloch_wigner(point)
        reference = float(new.bloch_wigner_mp(point, dps=100))
        absolute = abs(observed - reference)
        allowed = 8 * abs(np.spacing(reference)) + 4e-14 * abs(reference)
        if not np.isfinite(observed) or absolute > allowed:
            raise AssertionError((point, observed, reference))
        max_absolute = max(max_absolute, absolute)
        if reference:
            max_relative = max(max_relative, absolute / abs(reference))
    report["logarithmic_range_sample"] = {
        "seed": 1031, "count": 128, "exponent_range": [-308, 308],
        "max_absolute_error": max_absolute, "max_relative_error": max_relative,
        "acceptance": "8 output ulps + 4e-14 relative against 100-digit MP; no interval guarantee",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.output), "geometry_sha256": report["new_geometry_sha256"]}))


if __name__ == "__main__":
    main()
