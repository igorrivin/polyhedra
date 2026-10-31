# Adapted for standalone repository replay; see ../evidence-files.json.
"""Read-only independent numerical review; run from source package cwd."""
import argparse
from collections import defaultdict
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import sys

import mpmath as mp
import numpy as np
import scipy
from scipy.optimize import linprog, minimize
from scipy.spatial import Delaunay

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--repo", type=Path, required=True, help="Consolidated repository root")
parser.add_argument("--output", type=Path, required=True, help="New JSON output path outside preserved evidence")
args = parser.parse_args()
ROOT = args.repo.resolve()
if not (ROOT / "packages/volume-toolkit").is_dir():
    parser.error("--repo must name the consolidated repository root")
if args.output.exists():
    parser.error("--output must not already exist; preserve prior evidence")
args.output.parent.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "packages/volume-toolkit"))
from ideal_poly_volume_toolkit import rivin_delaunay as rd
from ideal_poly_volume_toolkit import geometry

FACES = [(2,4,3),(2,7,1),(5,2,3),(2,5,7),(6,5,0),(5,6,7),(6,0,1),(7,6,1)]
START = np.pi*np.array([[.2,.6,.2],[.2,.6,.2],[.4,.4,.2],[.2,.2,.6],
                        [.6,.2,.2],[.2,.6,.2],[.6,.2,.2],[.6,.2,.2]])


def independent_constraints(faces):
    """Construct incidences without any toolkit topology/matrix helpers."""
    corners, edges = defaultdict(list), defaultdict(list)
    n = 3*len(faces)
    for t, face in enumerate(faces):
        for k, v in enumerate(face):
            corners[int(v)].append(3*t+k)
            edge = tuple(sorted((int(face[(k+1)%3]), int(face[(k+2)%3]))))
            edges[edge].append(3*t+k)
    boundary = set(v for edge, uses in edges.items() if len(uses)==1 for v in edge)
    def row(indices):
        r = np.zeros(n)
        r[indices] = 1
        return r
    A = [row(list(range(3*t,3*t+3))) for t in range(len(faces))]
    b = [1]*len(faces)
    for v in sorted(set(corners)-boundary):
        A.append(row(corners[v])); b.append(2)
    B = [row(uses) for _, uses in sorted(edges.items()) if len(uses)==2]
    B += [row(corners[v]) for v in sorted(boundary)]
    return np.array(A), np.array(b), np.array(B).reshape(-1,n), np.ones(len(B))


def mp_volume(x, dps=35):
    with mp.workdps(dps):
        return float(mp.fsum(mp.clsin(2,2*mp.mpf(float(a)))/2 for a in np.ravel(x)))


evidence = {
    "review_stage": "portable replay of original independent checks on the imported source",
    "replay_driver_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
    "source_import": rd.__file__,
    "versions": {"numpy": np.__version__, "scipy": scipy.__version__, "mpmath": mp.__version__},
    "source_hashes": {str(Path(m.__file__).name): sha256(Path(m.__file__).read_bytes()).hexdigest()
                      for m in [rd, geometry]},
    "independent_comparisons": [],
}

cases = [("triangle",[(0,1,2)],None), ("square",[(0,1,2),(0,2,3)],None),
         ("four_fan",[(0,1,2),(0,2,3),(0,3,4),(0,4,1)],None),
         ("release_fixture",FACES,START)]
for n, seed in [(8,0),(8,3),(15,2)]:
    points = np.random.default_rng(seed).random((n,2))
    cases.append((f"random_{n}_{seed}", Delaunay(points).simplices.tolist(), None))
for name, faces, initial in cases:
    A,b,B,d = independent_constraints(faces)
    b,d = np.pi*b,np.pi*d
    result = rd.optimize_hyperbolic_volume(faces, initial)
    x0 = (rd.check_delaunay_realizability(faces)["angles_radians"] if initial is None else initial).ravel()
    ref = minimize(lambda x:-mp_volume(x), x0, method="SLSQP",
                   jac=lambda x:np.log(2*np.sin(x)), bounds=[(1e-9,np.pi-1e-9)]*len(x0),
                   constraints=[{"type":"eq","fun":lambda x:A@x-b,"jac":lambda x:A},
                                {"type":"ineq","fun":lambda x:d-B@x,"jac":lambda x:-B}],
                   options={"ftol":1e-12,"maxiter":150})
    x = result["angles"].ravel()
    sample = {"name":name,"faces":len(faces),"toolkit_success":result["success"],
              "reference_success":bool(ref.success),"reference_message":str(ref.message),
              "value":result["volume"],"mp_value":mp_volume(x,60),
              "reference_value":-float(ref.fun), "reference_iterations":int(ref.nit),
              "reference_value_difference":abs(result["volume"]+float(ref.fun)),
              "reference_angle_max_difference":float(np.max(np.abs(x-ref.x))),
              "original_equality_error":float(np.max(np.abs(A@x-b))),
              "original_inequality_violation":max(0.,float(np.max(B@x-d))),
              "active_set_history":result["active_set_history"],"kkt":result["kkt"]}
    assert result["success"] and ref.success, sample
    assert sample["original_equality_error"] <= 1e-10
    assert sample["original_inequality_violation"] <= 1e-10
    assert abs(sample["value"]-sample["mp_value"]) <= 5e-13
    assert sample["reference_value_difference"] <= 2e-9, sample
    if name=="release_fixture":
        assert any(e["action"]=="release" for e in sample["active_set_history"])
    evidence["independent_comparisons"].append(sample)

# A separately constructed one-margin LP supplies an exact rational dual
# upper bound in addition to the exact feasible primal witness.
A,b,B,d=independent_constraints(FACES)
n=A.shape[1]
C=np.vstack([np.column_stack([-np.eye(n),np.ones(n)]),np.column_stack([B,np.ones(len(B))])])
rhs=np.r_[np.zeros(n),d]
E=np.column_stack([A,np.zeros(len(A))])
c=np.r_[np.zeros(n),-1.]
lp=linprog(c,A_ub=C,b_ub=rhs,A_eq=E,b_eq=b,bounds=[(None,None)]*n+[(0,None)],method="highs")
assert lp.success
y=[Q(float(v)).limit_denominator(10000) for v in lp.eqlin.marginals]
z=[Q(float(v)).limit_denominator(10000) for v in lp.ineqlin.marginals]
assert all(v<=0 for v in z)
assert all(sum(Q(int(E[i,j]))*y[i] for i in range(len(y)))+
           sum(Q(int(C[i,j]))*z[i] for i in range(len(z)))==Q(int(c[j])) for j in range(n+1))
dual=sum(Q(int(b[i]))*y[i] for i in range(len(y)))+sum(Q(int(rhs[i]))*z[i] for i in range(len(z)))
assert dual == -Q(1,7)
witness=[Q(v,7) for row in [[1,3,3],[1,5,1],[1,3,3],[1,3,3],[3,1,3],[1,5,1],[5,1,1],[5,1,1]] for v in row]+[Q(1,7)]
assert all(sum(Q(int(a))*v for a,v in zip(row,witness))==Q(int(r)) for row,r in zip(E,b))
assert all(sum(Q(int(a))*v for a,v in zip(row,witness))<=Q(int(r)) for row,r in zip(C,rhs))
evidence["exact_common_margin"]={"primal_margin":"1/7","dual_objective":str(dual),
    "dual_stationarity_exact":True,"dual_signs_exact":True,"all_primal_constraints_exact":True,
    "equality_dual":[str(v) for v in y],"inequality_dual":[str(v) for v in z]}

# These are exact represented-float arguments, including tiny positive
# values and the largest representable values below binary64 pi.
evidence["lobachevsky_endpoint_probes"]=[]
for a in [np.nextafter(0.,1.),1e-300,1e-150,1e-30,1e-12,np.pi/2,
          np.pi-1e-12,np.nextafter(np.pi,0.)]:
    with mp.workdps(400):
        ref=mp.clsin(2,2*mp.mpf(float(a)))/2
        got=rd.lobachevsky_function(a)
        error=abs(mp.mpf(got)-ref)
        evidence["lobachevsky_endpoint_probes"].append({"angle":float(a),"value":got,
            "reference":mp.nstr(ref,25),"absolute_error":float(error)})
        assert error < mp.mpf("3e-15")

evidence["work_counter_probes"]=[]
original=rd._angle_structure_volume
for name,initial in [("stationary",None),("nonstationary",[[.2,1.,np.pi-1.2]])]:
    observed=[]
    def count(x):
        observed.append(1)
        return original(x)
    rd._angle_structure_volume=count
    result=rd.optimize_hyperbolic_volume([(0,1,2)],initial)
    rd._angle_structure_volume=original
    evidence["work_counter_probes"].append({"name":name,"reported":result["n_volume_evaluations"],"observed":len(observed)})

failed=rd.check_delaunay_realizability([(0,1,2)])
failed.update(realizable=False,success=True,min_angle=5e-7,min_angle_radians=5e-7*np.pi)
evidence["formatter_subthreshold_probe"]={"positive_minimum":failed["min_angle"],"formatted":rd.format_realizability_report(failed)}
strict=rd.check_delaunay_realizability(FACES,strict=True)
evidence["formatter_strict_probe"]={"objective":strict["strict_objective"],"formatted":rd.format_realizability_report(strict)}

def jsonable(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)

failure=rd.optimize_hyperbolic_volume([(0,1,2)],[[.2,1.,np.pi-1.2]],max_iter=0)
json.dumps(failure,default=jsonable,allow_nan=False)
evidence["failure_metadata"]={"strict_json_after_numpy_conversion":True,
    "success":failure["success"],"termination_reason":failure["termination_reason"],
    "stationarity_residual":failure["kkt"]["stationarity_residual"]}

armijo=rd._angle_armijo_step
rd._angle_armijo_step=lambda *args,**kwargs:(None,0.0,80)
failure=rd.optimize_hyperbolic_volume([(0,1,2)],[[.2,1.,np.pi-1.2]])
rd._angle_armijo_step=armijo
assert not failure["success"] and failure["termination_reason"]=="line_search_failed"
evidence["forced_line_search_failure"]={"success":failure["success"],
    "reason":failure["termination_reason"],"stationarity_residual":failure["kkt"]["stationarity_residual"]}
solve=np.linalg.solve
def singular(*args,**kwargs):
    raise np.linalg.LinAlgError("forced singularity")
np.linalg.solve=singular
fallback=rd.optimize_hyperbolic_volume([(0,1,2)],[[.2,1.,np.pi-1.2]])
np.linalg.solve=solve
assert fallback["success"] and fallback["kkt"]["stationarity_residual"]<1e-10
evidence["forced_singular_curvature"]={"success":fallback["success"],
    "reason":fallback["termination_reason"],"stationarity_residual":fallback["kkt"]["stationarity_residual"]}
disconnected=[(0,1,2),(3,4,5)]
complex_result=rd.check_delaunay_realizability(disconnected)
assert complex_result["realizable"]
evidence["disconnected_complex"]={"faces":disconnected,"realizable":bool(complex_result["realizable"]),
    "formatted":rd.format_realizability_report(complex_result),"evidence_status":complex_result["evidence_status"]}

subthreshold=rd.check_delaunay_realizability([(0,1,2)])
subthreshold.update(realizable=False,min_angle=5e-7,min_angle_radians=5e-7*np.pi,
                    feasibility_status="no_positive_witness_verified")
checker=rd.check_delaunay_realizability
rd.check_delaunay_realizability=lambda *args,**kwargs:subthreshold
failure=rd.optimize_hyperbolic_volume([(0,1,2)])
rd.check_delaunay_realizability=checker
evidence["positive_start_failure_message"]={"injected_valid_api_state":True,
    "solver_success":subthreshold["solver_success"],"lp_audit_success":subthreshold["success"],
    "min_angle":subthreshold["min_angle"],"feasibility_status":subthreshold["feasibility_status"],
    "optimizer_success":failure["success"],"optimizer_reason":failure["termination_reason"],
    "optimizer_message":failure["message"]}

args.output.write_text(json.dumps(evidence,indent=2,allow_nan=False)+"\n")
print(json.dumps({"comparisons":len(evidence["independent_comparisons"]),
                 "exact_margin":"1/7","endpoint_probes":len(evidence["lobachevsky_endpoint_probes"]),
                 "counter_probes":evidence["work_counter_probes"],
                 "evidence":str(args.output)},indent=2))
