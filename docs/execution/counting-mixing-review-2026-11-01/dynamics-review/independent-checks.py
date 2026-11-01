#!/usr/bin/env python3
"""Reviewer-owned integrity and exact finite probes; not a proof of mixing."""
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2] / "consolidated"
BASE = "9c8b61790aaa674902b9d60e80122c318a578bcc"
EXPECTED = {
    "book/chapters/26-counting-to-mixing.tex": "64562ebf631c59b84b9c991a632926107b3e24cb5b08b29c21e263bd50a9e901",
    "book/chapters/27-weighted-mixing-converse.tex": "79fb4660fe87a5723eea0d410e55e954913b0386057a31542473d6486492dcc1",
    "book/chapters/28-genus-two-model.tex": "18c05143e86fb9630868bb2824ddf44643c1ee1c84a40dc77a8c9d5354663fb4",
    "book/chapters/29-controlled-observables.tex": "79dd4ae151f95aa445cbf9f67fb512ec5dbc6df8922c43aa05591a8ef48b273f",
    "book/claims/sections26-29.json": "0585f7efdb6f703eaea3a76e2d3f970cc71e033fc4977ab265bc7f43a57ec514",
}

def labels(text):
    return re.findall(r"\\label\{([^}]+)\}", text)

integrity = []
all_labels = []
baseline_monolith = subprocess.check_output(
    ["git", "show", BASE + ":book/polyhedral_volumes_and_geodesic_identities.tex"],
    cwd=ROOT, text=True)
for rel, expected in EXPECTED.items():
    raw = (ROOT / rel).read_bytes()
    actual = sha256(raw).hexdigest()
    assert actual == expected, (rel, actual)
    row = {"path": rel, "sha256": actual, "bytes": len(raw)}
    if rel.endswith(".tex"):
        current = labels(raw.decode())
        # These four chapters were still inline at the baseline commit.
        # Locate the section independently by its preserved heading, then stop
        # at the next section or monograph part (not author-supplied line spans).
        heading = raw.decode().splitlines()[0]
        start = baseline_monolith.index(heading)
        tail = baseline_monolith[start+len(heading):]
        boundary = re.search(r"(?m)^\\(?:section\{|monographpart\{)", tail)
        assert boundary is not None, rel
        baseline = labels(heading + tail[:boundary.start()])
        assert Counter(current) == Counter(baseline), rel
        assert len(current) == len(set(current)), rel
        row.update(label_count=len(current), baseline_labels_identical=True)
        all_labels.extend(current)
    integrity.append(row)

ledger = json.loads((ROOT / "book/claims/sections26-29.json").read_text())
claims = ledger["claims"]
assert len(claims) == 59
assert len({row["id"] for row in claims}) == 59
ledger_labels = [lab for row in claims for lab in row["labels"]]
assert Counter(ledger_labels) == Counter(all_labels)
assert len(all_labels) == 125

def add(a, b):
    return [[x+y for x, y in zip(ar, br)] for ar, br in zip(a, b)]

def scale(s, a):
    return [[s*x for x in ar] for ar in a]

def mul(a, b):
    return [[sum(a[i][k]*b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]

def identity(n):
    return [[Q(i == j) for j in range(n)] for i in range(n)]

# A positive integer adjacency matrix with a genuine non-Perron Jordan block.
# Its trace has no polynomial factor, but its transition operator does.
A = [[Q(x) for x in row] for row in [[5, 4, 1], [2, 3, 5], [3, 3, 4]]]
I = identity(3)
Pi = [[Q(1, 3)]*3 for _ in range(3)]
u, v = [1, -1, 0], [1, 1, -2]
N = [[Q(x*y) for y in v] for x in u]
Z = [[Q(0)]*3 for _ in range(3)]
assert mul(N, N) == Z
assert mul(Pi, N) == Z and mul(N, Pi) == Z
assert add(add(scale(10, Pi), add(I, scale(-1, Pi))), N) == A
P = scale(Q(1, 10), A)
An, Pn = I, I
for n in range(1, 41):
    An, Pn = mul(An, A), mul(Pn, P)
    assert sum(An[i][i] for i in range(3)) == 10**n + 2
    expected_error = scale(Q(1, 10**n), add(add(I, scale(-1, Pi)), scale(n, N)))
    assert add(Pn, scale(-1, Pi)) == expected_error

# Exact Bruhat factorization, including negative residues and independent c.
bruhat_count = 0
for c in range(1, 25):
    for a in range(-2*c, 2*c+1):
        for d in range(-2*c, 2*c+1):
            if (a*d-1) % c:
                continue
            b = (a*d-1)//c
            left = [[Q(1), Q(a, c)], [Q(0), Q(1)]]
            middle = [[Q(0), Q(-1, c)], [Q(c), Q(0)]]
            right = [[Q(1), Q(d, c)], [Q(0), Q(1)]]
            assert mul(mul(left, middle), right) == [[a, b], [c, d]]
            bruhat_count += 1

# Independent normalization bookkeeping for the two balancing formulae.
# Substitute epsilon=e^-x t, H=e^y t and compare all exponents exactly.
balance_cases = []
for delta, a, b, d, k in [(Q(1, 3), Q(2), Q(3), Q(0), 1),
                           (Q(2, 5), Q(3), Q(1, 2), Q(2), 4),
                           (Q(1), Q(1), Q(0), Q(0), 5)]:
    eta = delta / (1+b/a+(1+d/a)/k)
    y = eta/a
    x = (eta+d*y)/k
    assert delta-b*y-x == eta
    assert k*x-d*y == eta
    assert a*y == eta
    balance_cases.append({"delta": str(delta), "a": str(a), "b": str(b),
                          "d": str(d), "k": k, "eta": str(eta)})

result = {
    "role": "fresh independent reviewer",
    "baseline_commit": BASE,
    "frozen_files": integrity,
    "label_audit": {"preserved_labels": len(all_labels), "ledger_labels": len(ledger_labels),
                    "claim_count": len(claims), "exact_once_coverage": True},
    "exact_probes": {
        "positive_integer_jordan_matrix": [[int(x) for x in row] for row in A],
        "jordan_n_values": list(range(1, 41)),
        "jordan_identity": "tr(A^n)=10^n+2; P^n-Pi=10^-n[(I-Pi)+nN]",
        "bruhat_factorizations": bruhat_count,
        "smoothing_cusp_balances": balance_cases,
    },
    "evidence_limits": [
        "These finite exact probes are independently authored sanity checks, not proofs of general mixing.",
        "The chapter proofs and external theorem applications were reviewed separately.",
        "No floating-point certification, root-owned companion execution, build, publication, or upload is asserted."
    ]
}
(OUT / "independent-checks.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"status": "pass", "labels": len(all_labels), "claims": len(claims),
                  "jordan_cases": 40, "bruhat_cases": bruhat_count,
                  "balance_cases": len(balance_cases)}, indent=2))
