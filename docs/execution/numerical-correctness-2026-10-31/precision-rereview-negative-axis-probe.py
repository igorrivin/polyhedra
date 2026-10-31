"""Independent follow-up using the raw definition, without argument maps."""

from hashlib import sha256
import json
from pathlib import Path
import sys

import mpmath as mp

ROOT = Path(__file__).resolve().parents[2] / "consolidated"
sys.path.insert(0, str(ROOT / "packages/volume-toolkit"))
from ideal_poly_volume_toolkit import geometry  # noqa: E402


def main():
    rows = []
    for real in ("-0.000001", "-0.25", "-1", "-4", "-1000000"):
        for height in ("1e-150", "1e-300"):
            for imaginary in (height, "-" + height):
                with mp.workdps(450):
                    z = mp.mpc(real, imaginary)
                    # No reciprocal/reflection/Mobius reduction in this oracle.
                    reference = mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z))
                    coefficient = -mp.log(1 - z.real) / z.real - mp.log(abs(z.real)) / (1 - z.real)
                    leading_relative = abs(reference / (z.imag * coefficient) - 1)
                observed = geometry.bloch_wigner_mp((real, imaginary), dps=120)
                triangle = geometry.triangle_volume_from_points_mp((real, imaginary), 1, 0, dps=120)
                wrapper = geometry.bloch_wigner_mpmath((real, imaginary), dps=120)
                with mp.workdps(450):
                    relative = abs(observed / reference - 1)
                    triangle_relative = abs(triangle / abs(reference) - 1)
                    sign_matches = bool(observed * reference > 0)
                    wrapper_matches = wrapper == float(reference)
                    passed = (relative < mp.mpf("1e-112")
                              and triangle_relative < mp.mpf("1e-112")
                              and leading_relative < mp.mpf("1e-130")
                              and sign_matches and wrapper_matches)
                    rows.append({
                        "real": real, "imaginary": imaginary,
                        "raw_reference_dps": 450, "working_dps": 120,
                        "reference": mp.nstr(reference, 145),
                        "observed": mp.nstr(observed, 130),
                        "mp_relative_error": mp.nstr(relative, 20),
                        "triangle_relative_error": mp.nstr(triangle_relative, 20),
                        "leading_term_relative_error": mp.nstr(leading_relative, 20),
                        "sign_matches": sign_matches,
                        "float_wrapper_matches_rounded_reference": wrapper_matches,
                        "passed": bool(passed),
                    })
    module = Path(geometry.__file__).resolve()
    result = {
        "source_module": str(module),
        "source_sha256": sha256(module.read_bytes()).hexdigest(),
        "probe_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "Bounded independent raw-formula and first-order comparisons, not a uniform error bound.",
        "cases": rows, "case_count": len(rows),
        "all_passed": all(row["passed"] for row in rows),
    }
    destination = Path(__file__).with_name("precision-rereview-negative-axis.json")
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"case_count": len(rows), "all_passed": result["all_passed"],
                      "report": str(destination)}, indent=2))
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
