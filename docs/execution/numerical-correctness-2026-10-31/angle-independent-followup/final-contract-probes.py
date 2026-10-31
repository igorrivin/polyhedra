"""Independent public reporting, work-count, and failure-metadata probes."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
sys.path.insert(0,str(Path.cwd()))
from ideal_poly_volume_toolkit import rivin_delaunay as rd

out=Path(__file__).parent
evidence={"source_import":rd.__file__,"source_sha256":sha256(Path(rd.__file__).read_bytes()).hexdigest(),
          "counter_cases":[],"lp_failure_cases":[]}
original=rd._angle_structure_volume
for name,start,budget,expected in [
    ("stationary_zero_budget",None,0,1),
    ("nonstationary",[[.2,1.,np.pi-1.2]],300,None),
    ("nonstationary_zero_budget",[[.2,1.,np.pi-1.2]],0,1),
    ("nonpositive_initial",[[0.,np.pi/2,np.pi/2]],300,0),
    ("infeasible_initial",[[1.,1.,1.]],300,0),
]:
    observed=[]
    def counted(x):
        observed.append(np.array(x,copy=True))
        return original(x)
    rd._angle_structure_volume=counted
    result=rd.optimize_hyperbolic_volume([(0,1,2)],start,max_iter=budget)
    rd._angle_structure_volume=original
    assert result["n_volume_evaluations"]==len(observed)
    if expected is not None:assert len(observed)==expected
    evidence["counter_cases"].append({"name":name,"reported":result["n_volume_evaluations"],
        "observed":len(observed),"success":result["success"],"reason":result["termination_reason"]})

observed=[]
def reject(x):
    observed.append(np.array(x,copy=True))
    return original(x) if np.array_equal(x,observed[0]) else original(x)-1e6
rd._angle_structure_volume=reject
failure=rd.optimize_hyperbolic_volume([(0,1,2)],[[.2,1.,np.pi-1.2]])
rd._angle_structure_volume=original
assert not failure["success"] and failure["termination_reason"]=="line_search_failed"
assert len(observed)>2 and failure["n_volume_evaluations"]==len(observed)
evidence["counter_cases"].append({"name":"rejected_trials","reported":failure["n_volume_evaluations"],
    "observed":len(observed),"success":failure["success"],"reason":failure["termination_reason"]})

def jsonable(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    raise TypeError(type(value).__name__)

checker=rd.check_delaunay_realizability
base=checker([(0,1,2)])
for state,expected_reason in [("solver","feasibility_lp_failed"),
                              ("audit","feasibility_lp_audit_failed"),
                              ("subthreshold","no_positive_initial_witness")]:
    lp=deepcopy(base)
    lp.update(realizable=False,feasibility_status="no_positive_witness_verified",solver_iterations=17)
    if state=="solver":
        lp.update(success=False,solver_success=False,status=1,message="Iteration limit reached",
                  angles=None,angles_radians=None)
    elif state=="audit":
        lp.update(success=False,message="Rejected by original-constraint feasibility audit")
        lp["primal_residuals"]["passed"]=False
    else:
        lp.update(min_angle=5e-7,min_angle_radians=5e-7*np.pi)
    rd.check_delaunay_realizability=lambda *args,**kwargs:lp
    result=rd.optimize_hyperbolic_volume([(0,1,2)])
    rd.check_delaunay_realizability=checker
    assert not result["success"] and result["termination_reason"]==expected_reason
    assert result["n_volume_evaluations"]==0 and result["n_iterations"]==0
    assert result["evidence_status"]=="not_verified"
    assert result["feasibility_lp"] is lp and result["feasibility_lp"]["solver_iterations"]==17
    json.dumps(result,default=jsonable,allow_nan=False)
    formatted=rd.format_realizability_report(lp)
    assert "No positive angle witness verified by this run" in formatted
    assert "NOT REALIZABLE" not in formatted and "not certified" in formatted
    if state=="subthreshold":
        assert "5e-07" in formatted and "5e-07" in result["message"]
        assert "LP failed" not in result["message"] and "≤ 0" not in formatted
    evidence["lp_failure_cases"].append({"name":state,"reason":result["termination_reason"],
        "message":result["message"],"formatted":formatted,"strict_json_after_numpy_conversion":True,
        "solver_iterations_retained":17,"volume_calls":result["n_volume_evaluations"]})

disconnected=checker([(0,1,2),(3,4,5)])
report=rd.format_realizability_report(disconnected)
assert "Positive angle witness verified numerically" in report
assert "REALIZABLE as Delaunay triangulation" not in report
strict=checker([(0,1,2)],strict=True)
report=rd.format_realizability_report(strict)
assert "common angle/inequality margin" in report and "Measured min angle" in report
assert "Maximum min angle" not in report
evidence["formatter_success_scope_passed"]=True

base_path=out.parent
prior=json.loads((out/'prior-evidence-hashes.json').read_text())
assert all(sha256((base_path/name).read_bytes()).hexdigest()==digest for name,digest in prior.items())
evidence["prior_failure_evidence_preserved"]=True
(out/'final-contract-probes.json').write_text(json.dumps(evidence,indent=2,allow_nan=False)+'\n')
print(json.dumps({"counter_cases":evidence["counter_cases"],
    "lp_failure_cases":len(evidence["lp_failure_cases"]),"prior_evidence_preserved":True},indent=2))
