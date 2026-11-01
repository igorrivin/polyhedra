"""Independently rederive every dyadic N/A count from all retained binary64 lengths."""
from collections import Counter
from hashlib import sha256
import json
import math
from pathlib import Path
import struct
import time

HERE = Path(__file__).resolve().parent
AUTHOR = HERE.parent / "torus-campaign/full8192-author-v2"
report = json.loads((AUTHOR / "result.json").read_text())
started = time.perf_counter()
rows = []
for surface in report["surfaces"]:
    entry = next(x for x in surface["raw_streams"] if x["path"].endswith(".lengths.f64le"))
    histogram = Counter()
    h = sha256()
    previous = 0.0
    count = 0
    with Path(entry["path"]).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
            assert len(chunk) % 8 == 0
            for (ell,) in struct.iter_unpack("<d", chunk):
                assert math.isfinite(ell) and 1 <= ell <= 8193 and ell >= previous
                numerator, denominator = ell.as_integer_ratio()
                histogram[(8192*denominator)//numerator] += 1
                previous = ell
                count += 1
    assert count == surface["count_through_guard"]
    assert h.hexdigest() == entry["sha256"]
    derived = []
    for row in surface["counts"]:
        ratio = 8192//row["L"]
        primitive = sum(v for k, v in histogram.items() if k >= ratio)
        all_point = 2*sum((k//ratio)*v for k, v in histogram.items())
        assert primitive == row["N"]
        assert all_point == row["A_signed_all_point_for_stored_lengths"]
        doubled = None if row["L"] == 8192 else 2*sum((k//(ratio//2))*v for k, v in histogram.items())
        delta = None if doubled is None else doubled-4*all_point
        assert delta == row["Delta2_A"]
        derived.append({"L": row["L"], "N": primitive, "A": all_point, "Delta2_A": delta})
    rows.append({"surface": surface["surface"], "raw_sha256": h.hexdigest(), "count": count,
                 "lengths_checked_sorted_finite_and_in_range": True,
                 "floor_8192_over_length_histogram": sorted(histogram.items()), "dyadic_counts": derived})
    print(json.dumps({"surface": surface["surface"], "count": count, "all_dyadic_N_A_Delta_verified": True}), flush=True)
result = {"scope": "Exact arithmetic for every stored binary64 length; this does not certify the true spectrum.",
          "method": "Python integers compute floor(8192*denominator/numerator); floor(x/2^j)=floor(floor(x)/2^j) supplies all dyadic rows.",
          "surfaces": rows, "seconds": time.perf_counter()-started}
with (HERE / "full-stream-arithmetic.json").open("x") as stream:
    json.dump(result, stream, indent=2, allow_nan=False)
    stream.write("\n")
print(json.dumps({"seconds": result["seconds"]}), flush=True)
