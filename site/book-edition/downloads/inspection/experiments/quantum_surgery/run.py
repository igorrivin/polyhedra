"""Run bounded exact algebra and multiprecision quantum/surgery companion checks."""

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
    # Direct script execution is independent of the caller's working directory.
    sys.path.insert(0, str(ROOT))

from experiments.quantum_surgery.algebra import (  # noqa: E402
    fricke_checks, hessian_checks, regular_checks, surgery_checks, tensor_checks,
)
from experiments.quantum_surgery.exact import json_exact, require  # noqa: E402
from experiments.quantum_surgery.periods import (  # noqa: E402
    balanced_check, context, gram_check, period_check, precision_comparison,
)


def source_state():
    def git(*args):
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).rstrip("\n")

    paths = sorted(path for path in HERE.rglob("*")
                   if path.is_file() and path.suffix in (".py", ".json", ".md"))
    paths += [ROOT/"book/polyhedral_volumes_and_geodesic_identities.tex"]
    for number in (12, 13, 14, 16):
        paths += sorted((ROOT/"book/chapters").glob(f"{number}-*.tex"))
    status = git("status", "--porcelain", "--untracked-files=all")
    sources = []
    for path in paths:
        data = path.read_bytes()
        sources.append({"path": str(path.relative_to(ROOT)), "sha256": sha256(data).hexdigest(), "bytes": len(data)})
    return {"git_commit": git("rev-parse", "HEAD"), "git_dirty": bool(status),
            "git_status_porcelain": status.splitlines(), "sources": sources}


def calculate(fixture):
    precisions = fixture["precisions"]
    if len(precisions) != 2 or precisions[0] >= precisions[1]:
        raise ValueError("fixture must specify two strictly increasing precisions")
    for digits in precisions:
        context(digits)  # Validate before running any numerical section.
    exact = {"section12": fricke_checks(fixture), "regular_section14": regular_checks(),
             "formal_section16": surgery_checks(fixture), "figure_eight_tensors": tensor_checks(fixture),
             "peripheral_Hessians": hessian_checks()}
    periods, balanced, grams = [], [], []
    for row in fixture["period_weights"]:
        for z in fixture["period_z"]:
            runs = [period_check(row, z, digits) for digits in precisions]
            periods.append({"id": row["id"], "z": z, "runs": runs,
                            "precision_comparison": precision_comparison(*runs)})
        grams.append({"id": row["id"], "runs": [gram_check(row, fixture["gram_h_over_pi"], digits)
                                                 for digits in precisions]})
    for z in fixture["balanced_z"]:
        runs = [balanced_check(z, digits) for digits in precisions]
        balanced.append({"z": z, "runs": runs, "precision_comparison": precision_comparison(*runs)})
    return {"exact": exact, "nonresonant_periods": periods, "balanced_periods": balanced,
            "screened_Gram": grams}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new JSON path; parent directory must exist")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite existing evidence")
    if not args.output.parent.is_dir():
        parser.error("the output parent directory must already exist")
    started = time.perf_counter()
    source_before = source_state()
    fixture = json.loads((HERE/"fixture.json").read_text())
    calculations = calculate(fixture)
    source_after = source_state()
    require(source_before["sources"] == source_after["sources"]
            and source_before["git_commit"] == source_after["git_commit"],
            "source changed during the run; no successful output will be written")
    result = {"schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "all fixed checks passed; author computation, not independent review",
              "checks_passed": True, "source": source_before, "source_at_completion": source_after,
              "fixture": fixture, "python_version": platform.python_version(),
              "python_executable": sys.executable, "mpmath_version": mpmath.__version__,
              "arithmetic": {"exact": "fractions.Fraction and explicit quadratic fields with radicands -3,-2,2,3",
                             "numerical": "cloned local mpmath contexts; independent integral formulas share the mpmath backend",
                             "precision": fixture["precisions"],
                             "tolerance": "10^(-(dps-15)); observed residuals and cross-precision differences recorded separately"},
              "conventions": {"period_branch": "principal cut plane C minus ((-infinity,0] union [1,infinity))",
                              "period_weights": "four rational mu_i in (0,1), sum=2; nonresonant s/t requires delta0*delta1!=0",
                              "density": "curvature -1: -4*d_z*d_zbar log(area)",
                              "surgery": "multiplier logs u,v; a=pu+qv; formal a=i*theta; q!=0 for the action chart",
                              "quadratic_encoding": "a+b*sqrt(radicand), exact rational a,b"},
              **calculations,
              "coverage_limits": [
                  "Finite exact algebra checks use the printed geometric identities as inputs; they do not prove their geometric hypotheses.",
                  "Euler quadrature and special-function evaluations are independent formulas using the same mpmath arithmetic library.",
                  "Numerical tolerances, two-precision agreement, and finite-series differences are not interval certificates or rigorous tail bounds.",
                  "Balanced periods use a separate logarithmic basis, never substitution into a singular nonresonant connection matrix.",
                  "No full double-sine or DOZZ evaluation, spectral integral, quantum tail estimate, global Airy claim, or arbitrary rank/intersection engine.",
                  "Formal filling and fixed Hessian tensors do not compute a filled manifold, a verified filling volume, or a torsion invariant.",
                  "The two-cusp example is conditional matrix algebra, not the construction of a manifold or deformation family.",
                  "Regular fold polynomial/Taylor checks come directly from Section14; no code or numerical outputs from the previous Section15 companion are reused."
              ], "elapsed_seconds": time.perf_counter()-started}
    # Exclusive creation also closes the race between the early guard and writing.
    with args.output.open("x") as handle:
        json.dump(json_exact(result), handle, indent=2, allow_nan=False)
        handle.write("\n")
    print(f"All fixed exact/numerical checks passed; wrote {args.output}")


if __name__ == "__main__":
    main()
