"""Targeted independent acceptance runner for the final source freeze.

The independent reference/algebra scripts never import the author code.
This harness deliberately imports it to check contracts and compare fixtures.
It writes only a new result in the review directory.
"""

import argparse
import contextlib
import copy
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import mpmath as mp

from independent_reference import whole_q


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "consolidated"


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), "refusing to overwrite")
    sys.path.insert(0, str(ROOT))
    before_dps = mp.mp.dps
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        driver = importlib.import_module("experiments.section15_quantum.check")
        evaluator = importlib.import_module("experiments.section15_quantum.evaluate")
    require(not output.getvalue(), "package import produced output")
    require(mp.mp.dps == before_dps, "package import changed precision")
    initial = driver.source_snapshot()
    records = [{"check": "quiet_package_import_preserves_precision", "passed": True}]

    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONDONTWRITEBYTECODE="1")
    optimized_code = """
from experiments.section15_quantum import check
check.cot_polynomials = lambda terms: []
try:
    check.independent_checks(30)
except ArithmeticError as error:
    if 'polynomial' not in str(error):
        raise
    print('optimized executable polynomial check rejected injected fault')
else:
    raise RuntimeError('optimized Python silently disabled the check')
"""
    optimized = subprocess.run([sys.executable, "-O", "-c", optimized_code],
                               cwd="/private/tmp", env=env, text=True,
                               capture_output=True, check=True)
    records.append({"check": "optimized_python_injected_polynomial_failure", "passed": True,
                    "stdout": optimized.stdout.strip(), "stderr": optimized.stderr})

    for name in ("commit", *driver.SOURCE_PATHS):
        changed = copy.deepcopy(initial)
        if name == "commit":
            changed["commit"] = "injected-drift"
        else:
            changed["sha256"][name] = "injected-drift"
        try:
            driver.validate_source_stability(initial, changed)
        except RuntimeError:
            records.append({"check": "source_drift_rejected", "source": name, "passed": True})
        else:
            raise ArithmeticError("source gate accepted injected drift: " + name)

    direct_checks = [driver.independent_checks(digits) for digits in (40, 60)]
    require([len(item["records"]) for item in direct_checks] == [28, 28],
            "unexpected number of direct checks")
    for result in direct_checks:
        cross = next(item for item in result["records"] if item["name"] == "D_alternate_method_and_panels_argument_3")
        require(cross["details"]["integration_domain"] == ["0", "infinity"],
                "alternate D domain is not explicit")
        require("not an omitted-tail error" in cross["details"]["tail_bound_role"],
                "alternate D tail role is ambiguous")

    with tempfile.TemporaryDirectory(prefix="contract-probe-", dir=HERE) as folder:
        target = Path(folder) / "existing.json"
        target.write_text("preserve these bytes\n")
        previous_run = driver.run
        def should_not_compute(profile):
            raise ArithmeticError("output rejection occurred after computation")
        driver.run = should_not_compute
        try:
            for candidate in (target, Path(folder)/"missing-parent"/"result.json"):
                with contextlib.redirect_stderr(io.StringIO()):
                    try:
                        driver.main(["--profile", "smoke", "--output", str(candidate)])
                    except SystemExit as error:
                        require(error.code == 2, "unexpected parser error status")
                    else:
                        raise ArithmeticError("invalid output destination accepted")
            require(target.read_text() == "preserve these bytes\n", "existing output overwritten")
        finally:
            driver.run = previous_run
    records.append({"check": "overwrite_and_missing_parent_rejected_before_computation", "passed": True})

    original_quad = mp.quad
    try:
        mp.quad = lambda *args, **kwargs: (mp.nan, mp.mpf(0))
        try:
            evaluator.integrate(evaluator.Parameters("1/80", "0", "1", 12, 30))
        except ArithmeticError as error:
            require("nonfinite" in str(error), "wrong injected-nonfinite failure")
        else:
            raise ArithmeticError("nonfinite quadrature result accepted")
    finally:
        mp.quad = original_quad
    records.append({"check": "nonfinite_quadrature_result_rejected", "passed": True})

    odd = evaluator.integrate(evaluator.Parameters("1/80", "0", "2", 5, 30))
    pieces = odd["cutoff_comparison"]
    with mp.workdps(50):
        residual = abs(pieces["Q_at_shorter_cutoff"] + pieces["extension_contribution"] - odd["Q"])
        require(residual < mp.mpf("1e-28"), "odd-cutoff accounting is wrong")
        require(odd["panels"] == [0, 2, 3, 4, 5], "odd-cutoff partition is wrong")
        independent_full = whole_q(contour="2", cutoff=5)
        independent_short = whole_q(contour="2", cutoff=3)
        full_difference = abs(mp.mpf(independent_full["Q"]) - odd["Q"])
        short_difference = abs(mp.mpf(independent_short["Q"]) - pieces["Q_at_shorter_cutoff"])
        require(max(full_difference, short_difference) < mp.mpf("1e-10"),
                "odd-cutoff independent-reference comparison failed")
        records.append({"check": "odd_cutoff_real_quadrature_and_independent_shorter_integral", "passed": True,
                        "partition": odd["panels"], "accounting_residual": mp.nstr(residual, 40),
                        "full_reference_difference": mp.nstr(full_difference, 40),
                        "short_reference_difference": mp.nstr(short_difference, 40)})
    require(mp.mp.dps == before_dps, "numerical operations leaked precision context")
    final = driver.source_snapshot()
    driver.validate_source_stability(initial, final)
    result = {"status": "targeted_independent_acceptance_passed", "source_at_start": initial,
              "source_at_finish": final, "checks": records, "direct_double_sine_checks": direct_checks,
              "odd_cutoff_result": driver.encode(odd, 40),
              "independent_odd_cutoff_references": [independent_full, independent_short],
              "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "scope": "Targeted corrected-source replay and failure paths; not the full21-setting matrix or an interval certificate."}
    with args.output.open("x") as handle:
        handle.write(json.dumps(result, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"status": result["status"], "contract_checks": len(records),
                      "direct_check_counts": [len(x["records"]) for x in direct_checks],
                      "odd_cutoff_checks": records[-1], "source_sha256": final["sha256"]}, indent=2))


if __name__ == "__main__":
    main()
