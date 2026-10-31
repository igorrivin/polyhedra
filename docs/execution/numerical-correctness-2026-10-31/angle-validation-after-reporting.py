"""Bounded before/after Rivin checks, without altering either source snapshot."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import mpmath as mp
import numpy as np
import scipy
from scipy.spatial import Delaunay

ROOT = Path(__file__).resolve().parents[2] / "consolidated"
sys.path.insert(0, str(ROOT / "packages/volume-toolkit"))

# Import the maintained source instead of any installed baseline wheel.
from ideal_poly_volume_toolkit import geometry  # noqa: E402
from ideal_poly_volume_toolkit import rivin_delaunay as current  # noqa: E402

BASELINE = "285a6cb71473ba1f238983e062662cf890cbba05"
SOURCE_PATH = "packages/volume-toolkit/ideal_poly_volume_toolkit/rivin_delaunay.py"
FACES = [(2, 4, 3), (2, 7, 1), (5, 2, 3), (2, 5, 7),
         (6, 5, 0), (5, 6, 7), (6, 0, 1), (7, 6, 1)]


def faces_for(n, seed):
    return [tuple(map(int, t)) for t in Delaunay(np.random.default_rng(seed).random((n, 2))).simplices]


def summary(result):
    return {
        "success": bool(result["success"]),
        "reported_volume": float(result["volume"]) if result["volume"] is not None else None,
        "angle_sum_residual": result["residuals"]["max_equality_residual"],
        "reduced_gradient_norm": result["reduced_gradient_norm"],
        "n_iterations": result["n_iterations"],
        "n_active_constraints": result["n_active_constraints"],
        "termination_reason": result.get("termination_reason"),
        "volume_method": result.get("volume_method", "64-term Fourier series"),
        "kkt": {k: result["kkt"][k] for k in (
            "passed", "stationarity_residual", "equality_residual",
            "inequality_violation", "complementarity_residual", "dual_sign_violation"
        )} if result.get("kkt") else None,
    }


def rational_witness():
    numerators = [[1, 3, 3], [1, 5, 1], [1, 3, 3], [1, 3, 3],
                  [3, 1, 3], [1, 5, 1], [5, 1, 1], [5, 1, 1]]
    angles = [[Fraction(a, 7) for a in row] for row in numerators]
    incidence, opposites = {}, {}
    for t, face in enumerate(FACES):
        for k, v in enumerate(face):
            incidence.setdefault(v, []).append(angles[t][k])
            edge = tuple(sorted(face[j] for j in range(3) if j != k))
            opposites.setdefault(edge, []).append(angles[t][k])
    boundary = {v for edge, a in opposites.items() if len(a) == 1 for v in edge}
    assert all(sum(a) == 1 and min(a) >= Fraction(1, 7) for a in angles)
    assert all(sum(a) <= Fraction(6, 7) for a in opposites.values() if len(a) == 2)
    assert all(sum(a) <= Fraction(6, 7) if v in boundary else sum(a) == 2
               for v, a in incidence.items())
    return {"faces": FACES, "normalized_angle_numerators": numerators,
            "denominator": 7, "common_margin": "1/7",
            "exact_rational_constraints_verified": True,
            "scope": "A witness for this one angle complex, not an exact global solver or embedding certificate"}


def main():
    source = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{BASELINE}:{SOURCE_PATH}"])
    with tempfile.TemporaryDirectory(prefix="rivin-baseline-") as directory:
        old_path = Path(directory) / "rivin_delaunay.py"
        old_path.write_bytes(source)
        spec = importlib.util.spec_from_file_location("ideal_poly_volume_toolkit._before_numerics", old_path)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)

        cases = []
        for name, faces, initial in (
            ("regular_triangle", [(0, 1, 2)], None),
            ("near_flat_triangle", [(0, 1, 2)], np.array([[1e-12, 1e-12, np.pi-2e-12]])),
            ("n15_seed2", faces_for(15, 2), None),
            ("n50_seed1002", faces_for(50, 1002), None),
            ("n50_seed1007", faces_for(50, 1007), None),
        ):
            before = old.optimize_hyperbolic_volume(faces, initial)
            after = current.optimize_hyperbolic_volume(faces, initial)
            cases.append({"name": name, "before": summary(before), "after": summary(after)})

        strict_scan = []
        for n in (8, 15, 30):
            for seed in range(30):
                faces = faces_for(n, seed)
                before = old.check_delaunay_realizability(faces, strict=True)
                after = current.check_delaunay_realizability(faces, strict=True)
                strict_scan.append({
                    "n_points": n, "seed": seed,
                    "before_realizable": bool(before["realizable"]),
                    "before_min_angle": float(before["min_angle"]),
                    "before_slack": float(before["slack"]),
                    "after_realizable": bool(after["realizable"]),
                    "after_common_margin": float(after["slack"]),
                    "after_primal_residuals_pass": bool(after["primal_residuals"]["passed"]),
                })
        legalization = {}
        for label, module in (("before", old), ("after", current)):
            result = module.legalize_to_interior_maximum(faces_for(15, 2), max_flips=8)
            legalization[label] = {"success": result["success"], "n_flips": result["n_flips"],
                                   "residuals": result["residuals"]}

    with mp.workdps(60):
        reference = mp.nstr(3*mp.clsin(2, 2*mp.pi/3)/2, 60)
    report = {
        "baseline_commit": BASELINE,
        "baseline_source_sha256": sha256(source).hexdigest(),
        "current_source_sha256": sha256(Path(current.__file__).read_bytes()).hexdigest(),
        "geometry_source_sha256": sha256(Path(geometry.__file__).read_bytes()).hexdigest(),
        "source_import": current.__file__,
        "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "mpmath": mp.__version__},
        "reference_regular_volume_60_digits": reference,
        "cases": cases,
        "strict_feasibility_scan": strict_scan,
        "strict_false_negatives_corrected": sum(not r["before_realizable"] and r["after_realizable"] for r in strict_scan),
        "strict_new_positive_witnesses": sum(r["after_realizable"] for r in strict_scan),
        "exact_strict_witness": rational_witness(),
        "legalization_seed2": legalization,
        "scope": "Bounded deterministic local replay on copied dependencies; no performance or global-classification claim",
    }
    output = Path(__file__).with_name("angle-solver-validation-after-reporting.json")
    output.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"output": str(output), "cases": len(cases), "strict_scan_cases": len(strict_scan),
                      "strict_false_negatives_corrected": report["strict_false_negatives_corrected"],
                      "strict_new_positive_witnesses": report["strict_new_positive_witnesses"]}, indent=2))


if __name__ == "__main__":
    main()
