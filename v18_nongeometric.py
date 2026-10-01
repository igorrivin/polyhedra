# Non-geometric triangulations: apply random 2-3 moves (no re-simplification) until SnapPy's solution has flat or negatively oriented tetrahedra,
# then run the barrier method on the angle polytope (if it has interior) and compare max V with vol(M).
import warnings; warnings.filterwarnings("ignore")
import numpy as np, snappy, random, sys
from snappy.snap.t3mlite import Mcomplex
from snappy.snap.t3mlite.simplex import TwoSubsimplices
exec(open('v17_threemanifolds.py').read().split("for name in (")[0])
random.seed(int(sys.argv[1]) if len(sys.argv)>1 else 1); shown=0; tried=0; noang=0
for name in ("m004","m009","m015","m125","m203","s776"):
    for attempt in range(60):
        C=Mcomplex(snappy.Manifold(name)); k=random.randint(1,4)
        for _ in range(k):
            cand=[(f,t) for t in C.Tetrahedra for f in TwoSubsimplices]; random.shuffle(cand)
            for f,t in cand:
                if C.two_to_three(f,t): break
        try: C.rebuild(); M=C.snappy_manifold()
        except Exception: continue
        st=M.solution_type()
        if st=="all tetrahedra positively oriented" or "degenerate" in st or "no solution" in st: continue
        tried+=1
        import io,contextlib
        buf=io.StringIO()
        with contextlib.redirect_stdout(buf): run(M,"%s + %d 2-3 moves"%(name,k))
        out=buf.getvalue()
        if "no strict angle structure" in out: noang+=1; continue
        print(out,end=""); shown+=1
        if shown>=7: break
    if shown>=7: break
print("non-geometric triangulations tried: %d, of which without strict angle structures: %d"%(tried,noang))
