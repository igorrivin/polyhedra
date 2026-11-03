"""Reproduce three fixed Section 9 log-sine barrier examples.

The solver is owned by ideal_poly_volume_toolkit.angle_barrier. This driver
owns fixed fixtures, independent mpmath references and publication provenance.
No high-precision comparison here is an interval enclosure.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
from html import escape
import json
import math
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import zipfile

import mpmath as mp
import numpy as np
import scipy

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BUNDLE_MANIFEST = ROOT / "barrier-bundle.json"
if BUNDLE_MANIFEST.is_file():
    sys.path.insert(0, str(ROOT / "packages/volume-toolkit"))

from ideal_poly_volume_toolkit import angle_barrier as solver  # noqa: E402
from ideal_poly_volume_toolkit import geometry, variational as var  # noqa: E402


def read_json(path):
    def reject(value):
        raise ValueError(f"nonfinite JSON value: {value}")
    return json.loads(Path(path).read_text(), parse_constant=reject)


def source_provenance(fixture_path):
    def record(role, path, required=True):
        path = Path(path).resolve()
        try:
            location, kind = str(path.relative_to(ROOT)), "project-relative"
        except ValueError:
            location, kind = str(path), "external"
        row = {"role": role, "path": location, "location_kind": kind, "required": required}
        if not path.is_file():
            if required:
                raise FileNotFoundError(f"required reproduction source is missing: {role}: {path}")
            return {**row, "available": False, "reason": "optional chapter source absent in this execution context"}
        return {**row, "available": True, "sha256": sha256(path.read_bytes()).hexdigest()}

    records = [record("experiment.driver", __file__),
               record("experiment.fixture", fixture_path),
               record("experiment.template", HERE / "barrier-page.html"),
               record("toolkit.angle_barrier", solver.__file__),
               record("toolkit.variational", var.__file__),
               record("toolkit.geometry", geometry.__file__),
               record("book.chapter", ROOT / "book/chapters/09-volume-hessians.tex", False)]
    commit, status, dirty = None, [], None
    if (ROOT / ".git").exists():
        commit = subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        status = subprocess.check_output(["git", "-C", str(ROOT), "status", "--porcelain"], text=True).splitlines()
        dirty = bool(status)
    bundle = read_json(BUNDLE_MANIFEST) if BUNDLE_MANIFEST.is_file() else None
    mismatches = []
    if bundle:
        for name, expected in bundle["payload_sha256"].items():
            path = (ROOT / name).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
                mismatches.append(name)
    return {
        "source_commit": commit,
        "execution_context": "git-checkout" if commit else ("detached-bundle" if bundle else "source-without-git"),
        "repository_dirty_at_start": dirty,
        "git_status_porcelain_at_start": status,
        "input_sha256": sha256(Path(fixture_path).read_bytes()).hexdigest(),
        "source_files": records,
        "source_sha256": {row["role"]: row["sha256"] for row in records if row["available"]},
        "bundle_origin": bundle["origin_provenance"] if bundle else None,
        "bundle_payload_hashes_match": not mismatches if bundle else None,
        "bundle_payload_mismatches": mismatches,
        "python": platform.python_version(), "numpy": np.__version__,
        "scipy": scipy.__version__, "mpmath": mp.__version__,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }


def mathematical_base(case):
    """Construct reference angles from exact decimal/rational fixture inputs."""
    if case["kind"] == "full_triangle":
        return [[mp.pi * mp.mpf(value.split("/")[0]) / int(value.split("/")[1])
                 for value in case["base_pi_fractions"]]]
    if case["kind"] == "boundary_slice":
        s, width, a = (mp.mpf(case[key]) for key in ("s0", "width", "second_angle"))
        return [[mp.pi - 2*s, s, s], [width-s, a+s, mp.pi-width-a]]
    if case["kind"] != "geometric_disk":
        raise ValueError("unsupported fixed-fixture kind")
    points = [[mp.mpf(value) for value in point] for point in case["points"]]
    angles = []
    for face in case["triangles"]:
        row = []
        for k in range(3):
            p, q, r = (points[face[j % 3]] for j in (k, k+1, k+2))
            a, b = ([q[j]-p[j] for j in range(2)], [r[j]-p[j] for j in range(2)])
            row.append(mp.atan2(abs(a[0]*b[1]-a[1]*b[0]), mp.fsum(x*y for x, y in zip(a, b))))
        angles.append(row)
    return angles


def numerical_input(case):
    incidence = np.asarray(case["incidence"], dtype=float)
    if case["kind"] == "geometric_disk":
        base = var.corner_angles(np.asarray(case["points"], dtype=float), case["triangles"])
        actual = var.leading_trailing_matrix(case["triangles"], case["interior_vertices"])
        if not np.array_equal(actual, incidence):
            raise ValueError("disk incidence disagrees with the independent fixture convention")
    elif case["kind"] == "full_triangle":
        base = np.array([[np.pi * int(x.split("/")[0]) / int(x.split("/")[1])
                          for x in case["base_pi_fractions"]]])
    elif case["kind"] == "boundary_slice":
        s, width, a = (float(case[key]) for key in ("s0", "width", "second_angle"))
        base = np.array([[np.pi-2*s, s, s], [width-s, a+s, np.pi-width-a]])
    else:
        raise ValueError("unsupported fixed-fixture kind")
    return base, incidence, np.asarray(case["initial_parameters"], dtype=float)


def mp_angles(base, incidence, parameters):
    flat = [angle for row in base for angle in row]
    return [angle + mp.fsum(c*u for c, u in zip(row, parameters))
            for angle, row in zip(flat, incidence)]


def mp_volume(angles):
    # clsin(2,2a)/2 is the independent Clausen representation of Lambda(a).
    # https://mpmath.org/doc/current/functions/zeta.html#clsin
    return mp.fsum(mp.clsin(2, 2*angle)/2 for angle in angles)


def mp_bloch_wigner_volume(angles):
    total = []
    for i in range(0, len(angles), 3):
        a, b, c = angles[i:i+3]
        z = mp.sin(b)/mp.sin(c) * mp.exp(1j*a)
        total.append(mp.im(mp.polylog(2, z)) + mp.arg(1-z)*mp.log(abs(z)))
    return mp.fsum(total)


def scalar_gradient(base, incidence, u):
    angles = mp_angles(base, incidence, [u])
    return mp.fsum(-row[0]*mp.log(2*mp.sin(a)) for a, row in zip(angles, incidence))


def lifted_stationary_reference(case, lifted, incidence):
    """A high-precision stationary reference for the rounded Clausen model.

    This is distinct from the exact-space maximum and from a rigorous global
    certificate. In the near-flat example, rounding moves the critical point
    by about machine precision and changes limiting derivative behavior.
    """
    if case["kind"] == "full_triangle":
        mean = mp.fsum(lifted[0])/3
        parameters = [mean-lifted[0][0], mean-lifted[0][1]]
        residual = mp.mpf(0)
    else:
        lower, upper = [], []
        for a, row in zip([v for triangle in lifted for v in triangle], incidence):
            c = row[0]
            if c:
                ends = sorted([-a/c, (mp.pi-a)/c])
                lower.append(ends[0])
                upper.append(ends[1])
        left, right = max(lower), min(upper)
        margin = (right-left)*mp.mpf("1e-55")
        def f(u):
            return scalar_gradient(lifted, incidence, u)
        if f(left+margin) <= 0 or f(right-margin) >= 0:
            raise ValueError("lifted scalar stationary reference lacks its expected bracket")
        # Bisection is independent of the production Newton solver and Hessian.
        # https://mpmath.org/doc/current/calculus/optimization.html
        u = mp.findroot(f, (left+margin, right-margin), solver="bisect", tol=mp.mpf("1e-60"), maxsteps=300)
        parameters, residual = [u], abs(f(u))
    return parameters, mp_volume(mp_angles(lifted, incidence, parameters)), residual


def mp_decrement(base, incidence, parameters, t):
    """Re-evaluate the affine Phi derivatives in high precision, independently."""
    angles = mp_angles(base, incidence, parameters)
    n = len(parameters)
    g = mp.matrix([mp.fsum(row[j]*(-mp.cot(a)+t*mp.log(2*mp.sin(a)))
                          for a, row in zip(angles, incidence)) for j in range(n)])
    h = mp.matrix([[mp.fsum(row[j]*row[k]*(1/mp.sin(a)**2+t*mp.cot(a))
                           for a, row in zip(angles, incidence)) for k in range(n)] for j in range(n)])
    step = mp.lu_solve(h, g)
    squared = mp.fsum(g[j]*step[j] for j in range(n))
    if squared < 0:
        raise ValueError("independent decrement quadratic form is negative")
    return mp.sqrt(squared)


def reference_record(case, base, incidence, result, dps):
    # workdps restores the caller's precision, including on failure:
    # https://mpmath.org/doc/current/basics.html
    with mp.workdps(dps):
        exact = mathematical_base(case)
        lifted = [[mp.mpf(float(a)) for a in row] for row in base]
        coefficients = [[mp.mpf(float(c)) for c in row] for row in incidence]
        parameters = [mp.mpf(float(u)) for u in result["parameters"]]
        if case["kind"] == "full_triangle":
            optimum = [mp.pi/3-exact[0][0], mp.pi/3-exact[0][1]]
        elif case["kind"] == "geometric_disk":
            optimum = [mp.mpf(0)]
        else:
            optimum = [-mp.mpf(case["s0"])]
        maximum = mp_volume(mp_angles(exact, coefficients, optimum))
        exact_endpoint = mp_volume(mp_angles(exact, coefficients, parameters))
        lifted_endpoint_angles = mp_angles(lifted, coefficients, parameters)
        lifted_endpoint = mp_volume(lifted_endpoint_angles)
        lifted_parameters, lifted_maximum, residual = lifted_stationary_reference(case, lifted, coefficients)
        decrement = mp_decrement(lifted, coefficients, parameters, mp.mpf(result["t"]))
        initial = [mp.mpf(float(u)) for u in case["initial_parameters"]]
        initial_decrement = mp_decrement(lifted, coefficients, initial, mp.mpf(result["history"][0]["t"]))
        history = result["history"]
        sample_indices = sorted({0, len(history)-1, *[round(i*(len(history)-1)/24) for i in range(25)]})
        samples = []
        for index in sample_indices:
            row = history[index]
            point = [mp.mpf(float(u)) for u in row["parameters"]]
            gap = maximum-mp_volume(mp_angles(exact, coefficients, point))
            lam, t = mp.mpf(row["newton_decrement"]), mp.mpf(row["t"])
            bound = (len(coefficients)+(mp.sqrt(len(coefficients))+lam)*lam/(1-lam))/t if lam < 1 else None
            samples.append({"history_index": index, "phase": row["phase"], "t": row["t"],
                            "exact_space_reference_gap_decimal": mp.nstr(gap, 50),
                            "numerical_formula_bound": float(bound) if bound is not None else None})
        record = {
            "working_decimal_digits": dps,
            "method": "Clausen volume from exact decimal/geometric definitions; separate exact lifts of binary64 inputs; bracketed scalar stationary reference; high-precision affine derivative check",
            "evidence_status": "multiprecision numerical comparison, not an interval enclosure or floating-point certificate",
            "exact_space_maximizer_parameters_decimal": [mp.nstr(x, 65) for x in optimum],
            "exact_space_maximum_volume_decimal": mp.nstr(maximum, 65),
            "exact_space_endpoint_volume_decimal": mp.nstr(exact_endpoint, 65),
            "exact_space_observed_gap_decimal": mp.nstr(maximum-exact_endpoint, 65),
            "lifted_input_stationary_parameters_decimal": [mp.nstr(x, 65) for x in lifted_parameters],
            "lifted_input_stationary_volume_decimal": mp.nstr(lifted_maximum, 65),
            "lifted_input_stationarity_residual_decimal": mp.nstr(residual, 65),
            "lifted_input_endpoint_volume_decimal": mp.nstr(lifted_endpoint, 65),
            "lifted_input_observed_gap_decimal": mp.nstr(lifted_maximum-lifted_endpoint, 65),
            "lifted_input_bloch_wigner_endpoint_decimal": mp.nstr(mp_bloch_wigner_volume(lifted_endpoint_angles), 65),
            "reference_maximum_representation_difference_decimal": mp.nstr(abs(maximum-lifted_maximum), 65),
            "reference_endpoint_representation_difference_decimal": mp.nstr(abs(exact_endpoint-lifted_endpoint), 65),
            "maximum_base_angle_representation_difference_decimal": mp.nstr(max(abs(a-b) for x,y in zip(exact,lifted) for a,b in zip(x,y)), 65),
            "lifted_triangle_sum_residual_decimal": mp.nstr(max(abs(mp.fsum(row)-mp.pi) for row in lifted), 65),
            "independent_final_decrement_decimal": mp.nstr(decrement, 65),
            "independent_initial_decrement_decimal": mp.nstr(initial_decrement, 65),
            "trace_samples": samples,
        }
        if case["kind"] == "boundary_slice":
            derivative = 2*mp.log(2)+mp.log(mp.sin(mp.mpf(case["width"]))/mp.sin(mp.mpf(case["second_angle"])))
            record["exact_space_boundary_right_derivative_decimal"] = mp.nstr(derivative, 65)
            record["representation_note"] = "The exact-space maximum has a flat triangle. Rounded triangle sums can change the endpoint singularity; the lifted Clausen model has its own nearby stationary reference. Neither is an interval certificate for machine arithmetic."
        if case["kind"] == "geometric_disk":
            flat = [a for row in exact for a in row]
            def fprime(u):
                return mp.fsum(-row[0]*mp.cot(a+row[0]*u) for a,row in zip(flat,coefficients))
            def phi1prime(u):
                return fprime(u)-scalar_gradient(exact, coefficients, u)
            record["exact_space_barrier_gradient_at_volume_maximum_decimal"] = mp.nstr(fprime(0), 65)
            record["exact_space_pure_barrier_center_decimal"] = mp.nstr(mp.findroot(fprime, (0, mp.mpf("0.05"))), 65)
            record["exact_space_phi1_center_decimal"] = mp.nstr(mp.findroot(phi1prime, (0, mp.mpf("0.05"))), 65)
            record["exact_space_volume_gradient_at_geometric_maximum_decimal"] = mp.nstr(scalar_gradient(exact, coefficients, 0), 65)
        return record


def invariance_diagnostics(case, base, incidence, result):
    """Check the entire accepted trace against its supplied affine constraints."""
    parameters = np.asarray([row["parameters"] for row in result["history"]])
    trace = base.ravel()[None, :] + parameters @ incidence.T
    diagnostic = {
        "parameter_dimension": int(incidence.shape[1]),
        "parameter_minimum": parameters.min(axis=0).tolist(),
        "parameter_maximum": parameters.max(axis=0).tolist(),
        "maximum_triangle_sum_change": float(np.max(np.abs(trace.reshape(-1, len(base), 3).sum(axis=2)-base.sum(axis=1)))),
        "maximum_recorded_angle_extrema_residual": max(
            max(abs(float(angles.min())-row["minimum_angle"]), abs(float(angles.max())-row["maximum_angle"]))
            for angles, row in zip(trace, result["history"])),
    }
    if case["kind"] == "geometric_disk":
        opposite = {}
        for face_index, face in enumerate(case["triangles"]):
            for corner in range(3):
                edge = tuple(sorted(face[j] for j in range(3) if j != corner))
                opposite.setdefault(edge, []).append(3*face_index+corner)
        pairs = [indices for indices in opposite.values() if len(indices) == 2]
        diagnostic["interior_edge_opposite_corner_pairs"] = pairs
        diagnostic["maximum_interior_edge_opposite_sum_change"] = max(
            float(np.max(np.abs(trace[:, pair].sum(axis=1)-base.ravel()[pair].sum()))) for pair in pairs)
        diagnostic["maximum_opposite_sum_tangent_residual"] = max(
            float(np.max(np.abs(incidence[pair].sum(axis=0)))) for pair in pairs)
    return diagnostic


def case_checks(base, incidence, result, reference, tolerance):
    rows, m = result["history"], base.size
    factor = 1+1/(20*math.sqrt(m))
    path = [row for row in rows if row["phase"] == "path"]
    reconstruction = (base.ravel()+incidence @ np.asarray(result["parameters"])).reshape(base.shape)
    max_constraint_error = float(np.max(np.abs(reconstruction.sum(axis=1)-np.pi)))
    reconstruction_error = float(np.max(np.abs(reconstruction-np.asarray(result["angles"]))))
    formula_volume_error = abs(result["volume"]-float(reference["lifted_input_endpoint_volume_decimal"]))
    bw_volume_error = abs(result["volume"]-float(reference["lifted_input_bloch_wigner_endpoint_decimal"]))
    decrement_error = abs(result["newton_decrement"]-float(reference["independent_final_decrement_decimal"]))
    exact_gap = float(reference["exact_space_observed_gap_decimal"])
    lifted_gap = float(reference["lifted_input_observed_gap_decimal"])
    bounds = result["gap_bound_estimate"], result["conservative_gap_bound_estimate"]

    def check(value, limit):
        return {"residual": float(value), "tolerance": float(limit), "passed": bool(value <= limit)}

    checks = {
        "solver_converged": {"passed": bool(result["converged"])},
        "result_is_not_a_rigorous_certificate": {"passed": result["certified"] is False},
        "positive_trace": {"passed": all(row["minimum_angle"] > 0 and row["maximum_angle"] < np.pi for row in rows)},
        "triangle_sums": check(max_constraint_error, 1e-12),
        "final_affine_reconstruction": check(reconstruction_error, 1e-14),
        "clausen_endpoint_comparison": check(formula_volume_error, tolerance),
        "bloch_wigner_endpoint_comparison": check(bw_volume_error, tolerance),
        "independent_final_decrement": check(decrement_error, 1e-8),
        "independent_initial_decrement": check(abs(rows[0]["newton_decrement"]-float(reference["independent_initial_decrement_decimal"])), 1e-10),
        "final_centering": check(result["newton_decrement"], 0.25),
        "scheduled_gap_target": check(bounds[1], result["epsilon"]*(1+1e-12)),
        "exact_space_gap_below_estimate": {"gap": exact_gap, "estimate": bounds[0], "allowance": tolerance,
                                            "passed": exact_gap >= -tolerance and exact_gap <= bounds[0]+tolerance},
        "lifted_input_gap_below_estimate": {"gap": lifted_gap, "estimate": bounds[0], "allowance": tolerance,
                                             "passed": lifted_gap >= -tolerance and lifted_gap <= bounds[0]+tolerance},
        "reference_representation_difference": check(float(reference["reference_maximum_representation_difference_decimal"]), tolerance),
        "path_centering_invariants": {"passed": all(row["newton_decrement"] <= 0.25 and row["decrement_before_step"] <= 5/16+1e-12 for row in path)},
        "path_parameter_schedule": {"passed": all(1 < row["parameter_multiplier"] <= factor+1e-12 and row["step_size"] == 1 for row in path)},
        "work_counts": {"passed": result["path_steps"] == len(path) and result["centering_steps"] == sum(row["phase"] == "centering" for row in rows)},
    }
    return checks


def build_report(fixture_path=HERE / "barrier-fixtures.json"):
    fixture_path = Path(fixture_path).resolve()
    provenance = source_provenance(fixture_path)
    if provenance["bundle_payload_mismatches"]:
        raise ValueError("detached barrier bundle payload integrity check failed")
    fixture = read_json(fixture_path)
    if fixture != read_json(HERE / "barrier-fixtures.json"):
        raise ValueError("--fixture must be an unchanged copy of the supplied barrier fixtures; this is not a general experiment renderer")
    cases = []
    for case in fixture["cases"]:
        base, incidence, initial = numerical_input(case)
        # Normalize immutable tuple fields at the artifact boundary; JSON
        # round-trips then compare the same structures during render-only work.
        result = json.loads(json.dumps(solver.solve_angle_barrier(
            base, incidence, initial, **fixture["solver_options"]).to_dict(), allow_nan=False))
        if not result["converged"]:
            cases.append({"id": case["id"], "title": case["title"], "kind": case["kind"],
                          "input": {"base_angles": base.tolist(), "incidence": incidence.tolist(), "initial_parameters": initial.tolist()},
                          "solver": result, "reference": None, "checks": {"solver_converged": {"passed": False}}})
            continue
        reference = reference_record(case, base, incidence, result, fixture["precision"]["reference_decimal_digits"])
        checks = case_checks(base, incidence, result, reference, float(fixture["precision"]["reference_comparison_tolerance"]))
        diagnostic = invariance_diagnostics(case, base, incidence, result)
        checks["full_trace_affine_invariants"] = {"passed": all(
            diagnostic[key] <= 1e-12 for key in diagnostic if key.startswith("maximum_"))}
        cases.append({"id": case["id"], "title": case["title"], "kind": case["kind"],
                      "input": {"base_angles": base.tolist(), "incidence": incidence.tolist(), "initial_parameters": initial.tolist()},
                      "solver": result, "reference": reference, "invariance_diagnostics": diagnostic, "checks": checks})
    exercises_centering = any(case["reference"] is not None
                             and float(case["reference"]["independent_initial_decrement_decimal"]) > 0.25
                             and case["solver"]["centering_steps"] > 0 for case in cases)
    return {
        "schema_version": 1, "experiment_id": fixture["id"], "provenance": provenance,
        "cases": cases, "exercises_initial_centering": exercises_centering,
        "all_checks_passed": exercises_centering and all(check["passed"] for case in cases for check in case["checks"].values()),
        "scope": {
            "coordinates": "alpha=base+C*u, positive triangle angles; fixed affine incidence supplied explicitly",
            "arithmetic": "binary64 dense solver; 80-digit independent references",
            "gap": "finite-iterate theorem formula evaluated numerically, not an interval certificate",
            "centering": "strict feasible inputs are supplied; starting-point centering and path steps are counted separately",
            "not_claimed": ["nearly-linear solver", "certified floating-point volume gap", "automatic geometric realization", "full three-manifold tangent basis", "scaling benchmark"]
        },
    }


def validate_render_sources(report, fixture_path):
    if report.get("schema_version") != 1 or report.get("experiment_id") != read_json(fixture_path).get("id"):
        raise ValueError("stored barrier report schema or experiment identity differs")
    old, current = report["provenance"], source_provenance(fixture_path)
    if old.get("input_sha256") != current["input_sha256"]:
        raise ValueError("stored barrier report input hash differs")
    records = {row["role"]: row for row in old.get("source_files", [])}
    if len(records) != len(old.get("source_files", [])):
        raise ValueError("stored barrier report has duplicate source roles")
    for row in current["source_files"]:
        previous = records.get(row["role"])
        if previous is None or previous.get("available") != row["available"]:
            raise ValueError(f"stored barrier report source availability differs: {row['role']}")
        if row["available"] and (previous.get("sha256") != row["sha256"] or old.get("source_sha256", {}).get(row["role"]) != row["sha256"]):
            raise ValueError(f"stored barrier report source hash differs: {row['role']}")
    if current["bundle_payload_mismatches"]:
        raise ValueError("detached barrier bundle payload integrity check failed")


def create_reproduction_bundle(report, fixture_path, destination):
    license_path = ROOT / "packages/volume-toolkit/LICENSE"
    if not license_path.is_file():
        license_path = ROOT / "LICENSES/volume-toolkit-MIT.txt"
    if not license_path.is_file():
        raise FileNotFoundError("the toolkit MIT license is required in the barrier bundle")
    payload = {f"experiments/section9/{name}": (HERE / name).read_bytes()
               for name in ("barrier_run.py", "barrier-page.html")}
    payload["experiments/section9/barrier-fixtures.json"] = Path(fixture_path).read_bytes()
    for module in (solver, var, geometry):
        path = Path(module.__file__)
        payload["packages/volume-toolkit/ideal_poly_volume_toolkit/" + path.name] = path.read_bytes()
    payload["packages/volume-toolkit/ideal_poly_volume_toolkit/__init__.py"] = (
        b'"""Generated Section 9 barrier subset; not the complete toolkit API.\n'
        b'Maintained numerical modules are copied unchanged; see barrier-bundle.json.\n"""\n')
    payload["LICENSES/volume-toolkit-MIT.txt"] = license_path.read_bytes()
    origin = report["provenance"]
    payload["requirements.txt"] = "".join(f"{name}=={origin[name]}\n" for name in ("numpy", "scipy", "mpmath")).encode()
    payload["README.md"] = (
        "# Section 9 barrier reproduction\n\n"
        "This is a labeled numerical subset, not the complete toolkit. Maintained angle_barrier.py, "
        "variational.py and geometry.py are copied unchanged; the original MIT license is under LICENSES. "
        "The captured computation used CPython " + origin["python"] + ". Other runtimes are not validated by that record.\n\n"
        "From this extracted directory install `python -m pip install -r requirements.txt`, then run "
        "`python experiments/section9/barrier_run.py`. An absolute script path works from another working directory. "
        "Outputs default to artifacts/section9/barrier-result.json and site/section9/barrier.html. "
        "The fixed fixtures include independent 80-digit reference comparisons. Reported gap estimates are not "
        "interval certificates, and this dense solver is not a nearly-linear implementation.\n\n"
        "The monograph assets are optional and absent. Detached Git status is unavailable; barrier-bundle.json "
        "retains origin provenance and verifies every payload hash. Rendering an existing report preserves "
        "its computation versions and timestamp. Inspection downloads are not standalone programs; use this ZIP.\n"
    ).encode()
    manifest = {"schema_version": 1, "scope": "Section 9 dense barrier numerical subset",
                "origin_provenance": origin, "payload_sha256": {name: sha256(data).hexdigest() for name, data in payload.items()}}
    payload["barrier-bundle.json"] = (json.dumps(manifest, indent=2, allow_nan=False)+"\n").encode()
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo("barrier-reproduction/"+name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)


def trace_table(case):
    samples = case["reference"]["trace_samples"]
    selected = sorted({0, len(samples)-1, *[round(i*(len(samples)-1)/5) for i in range(6)]})
    pieces = ['<table><caption>Selected trace checkpoints</caption><thead><tr><th scope="col">t</th><th scope="col">Reference gap</th><th scope="col">Formula estimate</th></tr></thead><tbody>']
    for index in selected:
        item = samples[index]
        gap, bound = float(item["exact_space_reference_gap_decimal"]), item["numerical_formula_bound"]
        bound_text = f"{bound:.4g}" if bound is not None else "Not available (λ≥1)"
        pieces.append(f'<tr><td>{item["t"]:.5g}</td><td>{gap:.4g}</td><td>{escape(bound_text)}</td></tr>')
    pieces.append('</tbody></table>')
    return "".join(pieces)


def case_html(case, definition):
    result, reference = case["solver"], case["reference"]
    if reference is None:
        return f'<section id="{escape(case["id"])}"><h2>{escape(case["title"])}</h2><p>Solver did not converge: {escape(result["message"])}</p></section>'
    rows = [
        ("Initial centering steps", str(result["centering_steps"])),
        ("Path steps", str(result["path_steps"])),
        ("Final parameter t", f'{result["t"]:.8g}'),
        ("Final Newton decrement", f'{result["newton_decrement"]:.5g}'),
        ("Minimum final angle (radians)", f'{float(np.min(result["angles"])):.8g}'),
        ("Observed exact-space reference gap", f'{float(reference["exact_space_observed_gap_decimal"]):.6g}'),
        ("Numerical finite-iterate bound estimate", f'{result["gap_bound_estimate"]:.6g}'),
        ("Scheduled conservative bound estimate", f'{result["conservative_gap_bound_estimate"]:.6g}'),
    ]
    table = "".join(f'<tr><th scope="row">{escape(k)}</th><td>{escape(v)}</td></tr>' for k,v in rows)
    passed = sum(check["passed"] for check in case["checks"].values())
    return (f'<section id="{escape(case["id"])}"><h2>{escape(case["title"])}</h2><p>{escape(definition["reference"])}</p>'
            f'<div class="case-grid"><table><caption>Recorded numerical endpoint</caption><tbody>{table}</tbody></table>'
            f'<div>{trace_table(case)}<p class="meta">Reference gaps use 80-digit arithmetic. Formula estimates use recorded numerical decrements. Every accepted iterate and the sampled high-precision comparisons are in the JSON.</p></div></div>'
            f'<p class="meta">{passed}/{len(case["checks"])} checks passed. The independent initial decrement is '
            f'{float(reference["independent_initial_decrement_decimal"]):.6g}; the exact-space and lifted-input reference maxima differ by '
            f'{float(reference["reference_maximum_representation_difference_decimal"]):.3g}. All values, trace rows, methods and tolerances are in the JSON download.</p>'
            + (f'<p class="note">{escape(reference["representation_note"])}</p>' if "representation_note" in reference else "") + '</section>')


def render_site(report, fixture_path, result_path, site_dir, *, chapter_page=None):
    fixture_path, result_path, site_dir = map(Path, (fixture_path, result_path, site_dir))
    validate_render_sources(report, fixture_path)
    if read_json(result_path) != report:
        raise ValueError("barrier result file does not contain the supplied report")
    if chapter_page is not None:
        chapter_page = Path(chapter_page)
        if not chapter_page.is_file():
            raise FileNotFoundError("requested chapter page is missing")
        if chapter_page.resolve() != (site_dir / "chapter.html").resolve():
            raise ValueError("chapter page must be in the same exported site directory")
    fixture = read_json(fixture_path)
    definitions = {case["id"]: case for case in fixture["cases"]}
    content = "".join(case_html(case, definitions[case["id"]]) for case in report["cases"])
    site_dir.mkdir(parents=True, exist_ok=True)
    downloads = site_dir / "downloads"
    downloads.mkdir(exist_ok=True)
    for source, name in ((fixture_path, "barrier-fixtures.json"), (result_path, "barrier-result.json"),
                         (Path(__file__), "barrier_run.py"), (Path(solver.__file__), "angle_barrier.py")):
        target = downloads / name
        if source.resolve() != target.resolve():
            shutil.copyfile(source, target)
    create_reproduction_bundle(report, fixture_path, downloads / "barrier-reproduction.zip")
    chapter_link = '<a href="chapter.html">Read Section 9 and its claim ledger</a>' if chapter_page is not None else '<span>The chapter assets are not included in this standalone numerical export.</span>'
    provenance = report["provenance"]
    status = "All fixed-fixture numerical checks passed." if report["all_checks_passed"] else "At least one fixed-fixture check failed; inspect the JSON before using this result."
    summary = f'{status} Source commit: {provenance["source_commit"] or "unavailable in this execution context"}; checkout dirty at start: {provenance["repository_dirty_at_start"]}. Captured Python {provenance["python"]}; NumPy {provenance["numpy"]}, SciPy {provenance["scipy"]}, mpmath {provenance["mpmath"]}.'
    data = json.dumps({"report": report, "fixture": fixture}, allow_nan=False, ensure_ascii=False).replace("</", "<\\/")
    html = (HERE / "barrier-page.html").read_text().replace("__CASE_CARDS__", content).replace("__CHAPTER_LINK__", chapter_link).replace("__RUN_SUMMARY__", escape(summary)).replace("__BARRIER_DATA__", data)
    (site_dir / "barrier.html").write_text(html)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, default=HERE / "barrier-fixtures.json")
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/section9/barrier-result.json")
    parser.add_argument("--site-dir", type=Path, default=ROOT / "site/section9")
    parser.add_argument("--render-result", type=Path, help="render an identity-checked existing report without recomputing")
    parser.add_argument("--chapter-page", type=Path, help="actual chapter.html in the same exported site directory")
    args = parser.parse_args()
    if args.render_result:
        result_path, report = args.render_result, read_json(args.render_result)
    else:
        report, result_path = build_report(args.fixture), args.output
        result_path.parent.mkdir(parents=True, exist_ok=True)
        result_path.write_text(json.dumps(report, indent=2, allow_nan=False)+"\n")
    render_site(report, args.fixture, result_path, args.site_dir, chapter_page=args.chapter_page)
    print(json.dumps({"operation": "render_existing_report" if args.render_result else "compute_and_render",
                      "all_checks_passed": report["all_checks_passed"], "source_commit": report["provenance"]["source_commit"],
                      "dirty_at_start": report["provenance"]["repository_dirty_at_start"],
                      "result": str(result_path), "html": str(args.site_dir / "barrier.html")}, indent=2))
    return 0 if report["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
