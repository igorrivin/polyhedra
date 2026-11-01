#!/usr/bin/env python3
"""Independent diagnostics for the Section 9 companion audit.

Uses only Python's standard library, imports no maintained/historical solver,
and supplies floating-point checks plus exact rational constant checks. These
are diagnostics, not interval certificates or a proof of global optimization.
"""
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import random
import subprocess

BASELINE = "26b3c134d9308d345cb76f1240db9de982b2e5a6"
ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / "consolidated"


def triangle_probe():
    rng = random.Random(20261031)
    max_a_error = max_t_error = max_compat_ratio = 0.0
    max_sum_h = 0.0
    for _ in range(10000):
        parts = [rng.randint(1, 100) for _ in range(3)]
        alpha = [math.pi * p / sum(parts) for p in parts]
        s = [math.sin(a) for a in alpha]
        tau = rng.uniform(-math.pi, math.pi)
        scale = rng.uniform(0.1, 3.0)
        psi = [0.0, alpha[0] + alpha[1], math.pi + alpha[1]]
        phi = [p - tau for p in psi]
        h = [scale * si * math.cos(p) for si, p in zip(s, phi)]
        a = sum(hi * hi / math.tan(ai) for hi, ai in zip(h, alpha))
        b = sum((hi / si) ** 2 for hi, si in zip(h, s))
        third = sum(hi**3 / si**2 for hi, si in zip(h, s))
        a_closed = scale**2 * math.prod(s)
        t_closed = scale**3 * math.prod(s) * math.cos(sum(phi))
        max_a_error = max(max_a_error, abs(a - a_closed) / a_closed)
        max_t_error = max(max_t_error, abs(third - t_closed) / (scale**3 * math.prod(s)))
        max_sum_h = max(max_sum_h, abs(sum(h)))
        max_compat_ratio = max(max_compat_ratio, abs(third) / (a_closed * math.sqrt(b)))
    return dict(samples=10000, seed=20261031, arithmetic="binary64", max_relative_A_identity_error=max_a_error,
                max_scaled_third_identity_error=max_t_error, max_tangent_sum_residual=max_sum_h,
                max_compatibility_ratio=max_compat_ratio, proved_upper_bound=math.sqrt(3))


def boundary_probe():
    z = [0j, -1j / math.sqrt(3), 1+0j, complex(-0.5, math.sqrt(3)/2)]
    triangles = [(0, 1, 2), (0, 2, 3)]
    angles = []
    totals = [0.0] * 4
    for tri in triangles:
        row = []
        for j, v in enumerate(tri):
            a, b = (z[tri[(j+1) % 3]]-z[v]), (z[tri[(j+2) % 3]]-z[v])
            c = (a.real*b.real+a.imag*b.imag)/(abs(a)*abs(b))
            angle = math.acos(max(-1.0, min(1.0, c)))
            row.append(angle * 180/math.pi)
            totals[v] += angle*180/math.pi
        angles.append(row)
    return dict(coordinates=[[q.real, q.imag] for q in z], triangles=triangles,
                triangle_angles_degrees=angles, boundary_angles_degrees=totals,
                internal_opposite_angle_sum_degrees=angles[0][1]+angles[1][2],
                interpretation="Positive locally Delaunay disk angles do not imply a convex developed boundary.")


def degeneration_probe():
    records = []
    for eps in [1e-2, 1e-4, 1e-6, 1e-8]:
        a = 1/math.tan(eps) + 1/math.tan(2*eps)
        third = 1/math.sin(eps)**2 - 1/math.sin(2*eps)**2
        records.append(dict(epsilon=eps, bare_SC_ratio=third/a**1.5,
                            scaled_ratio=math.sqrt(eps)*third/a**1.5))
    target = [math.pi/3]*3
    slopes = []
    for eps in [1e-2, 1e-4, 1e-6, 1e-8]:
        row = dict(epsilon=eps)
        for name, initial in [("needle", [0., 1., math.pi-1.]), ("flat", [math.pi, 0., 0.])]:
            h = [y-x for x,y in zip(initial,target)]
            x = [v+eps*d for v,d in zip(initial,h)]
            row[name+"_directional_derivative"] = sum(-d*math.log(2*math.sin(v)) for d,v in zip(h,x))
        slopes.append(row)
    return dict(bare_SC_asymptotic=records, scaled_limit=1/math.sqrt(6), boundary_slopes=slopes,
                flat_derivative_limit=2*math.pi/3*math.log(2))


def short_step_constants():
    eta = Fraction(1,4)
    c = Fraction(1,20)
    fresh = eta + c + c*eta  # m >= 1
    recentered = (fresh/(1-fresh))**2
    value_gap_multiplier = 1 + (1+eta)*eta/(1-eta)  # sqrt(m),1 <= m
    # Optional sufficient inexact solve rule: relative energy-norm error <=1/100.
    delta = fresh/Fraction(100)
    step = fresh+delta
    inexact_recentered = delta/(1-step) + step**2/(1-step)**2
    assert fresh == Fraction(5,16)
    assert recentered == Fraction(25,121) < eta
    assert value_gap_multiplier == Fraction(17,12)
    assert inexact_recentered == Fraction(10420,47961) < eta
    return {"arithmetic":"exact rational", "decrement_target":str(eta), "parameter_step_c":str(c),
            "decrement_after_parameter_change_bound":str(fresh), "exact_Newton_result_bound":str(recentered),
            "gap_multiplier_for_m_over_t":str(value_gap_multiplier),
            "optional_inexact_energy_relative_error":"1/100", "optional_inexact_Newton_result_bound":str(inexact_recentered)}


def source_identity():
    names = ["book/polyhedral_volumes_and_geodesic_identities.tex",
             "research/ipoly/duffin_rivin_volume_laplacian_solvers.tex",
             "audit/2026-10-31/ipoly-audit.md"]
    return {name:hashlib.sha256(subprocess.check_output(["git","show",f"{BASELINE}:{name}"],cwd=REPO)).hexdigest() for name in names}


if __name__ == "__main__":
    output = dict(baseline=BASELINE, source_sha256=source_identity(),
                  evidence_status="Independent algebra diagnostics; sampled floating point is not proof.",
                  compatibility=triangle_probe(), boundary_counterexample=boundary_probe(),
                  degeneration=degeneration_probe(), short_step_constants=short_step_constants())
    path = Path(__file__).with_name("companion_reference_probes.json")
    path.write_text(json.dumps(output, indent=2)+"\n")
    print(path)
    print(json.dumps({"compatibility":output["compatibility"],"short_step_constants":output["short_step_constants"]}, indent=2))
