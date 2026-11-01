"""Independent reviewer probes for Sections 23--25.

Only Python integer/Fraction arithmetic is used. These are bounded exact
checks, except that the dense-chart Laurent identities are symbolic identities
on that chart. No companion implementation is imported or approved here.
"""
from collections import defaultdict
from fractions import Fraction
from math import comb, factorial, gcd
from pathlib import Path
import hashlib
import json
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] / "consolidated"
COUNTS = defaultdict(int)


def check(group, condition):
    assert condition, group
    COUNTS[group] += 1


def clean(p):
    return {e: c for e, c in p.items() if c}


def const(c, n):
    return {(0,) * n: Fraction(c)} if c else {}


def mon(e, c=1):
    return {tuple(e): Fraction(c)} if c else {}


def add(*ps):
    out = defaultdict(Fraction)
    for p in ps:
        for e, c in p.items():
            out[e] += c
    return clean(out)


def scale(p, c):
    return clean({e: c * a for e, a in p.items()})


def mul(p, q, cutoff=None):
    out = defaultdict(Fraction)
    for e, a in p.items():
        for f, b in q.items():
            ef = tuple(x + y for x, y in zip(e, f))
            if cutoff is None or ef[0] <= cutoff:
                out[ef] += a * b
    return clean(out)


def power(p, k, n, cutoff=None):
    out = const(1, n)
    for _ in range(k):
        out = mul(out, p, cutoff)
    return out


def cheb(p, count, n):
    seq = [const(2, n), p]
    for k in range(1, count):
        seq.append(add(mul(p, seq[k]), scale(seq[k - 1], -1)))
    return seq


def mm(a, b):
    return [[add(*(mul(a[i][k], b[k][j]) for k in range(2)))
             for j in range(2)] for i in range(2)]


def inv(a):
    return [[a[1][1], scale(a[0][1], -1)],
            [scale(a[1][0], -1), a[0][0]]]


def trace(a):
    return add(a[0][0], a[1][1])


def word_trace(word, a, b):
    mats = {"a": a, "b": b, "A": inv(a), "B": inv(b)}
    out = [[const(1, 4), {}], [{}, const(1, 4)]]
    for letter in word:
        out = mm(out, mats[letter])
    return trace(out)


# Exact Laurent polynomial chart: A=diag(a,a^-1),
# B=[[b,c],[d,(1+cd)/b]]. Both determinants are identically one.
A = [[mon((1, 0, 0, 0)), {}], [{}, mon((-1, 0, 0, 0))]]
B = [[mon((0, 1, 0, 0)), mon((0, 0, 1, 0))],
     [mon((0, 0, 0, 1)), add(mon((0, -1, 0, 0)), mon((0, -1, 1, 1)))]]
one4 = const(1, 4)
for mat in (A, B):
    check("dense_chart", add(mul(mat[0][0], mat[1][1]), scale(mul(mat[0][1], mat[1][0]), -1)) == one4)
x, y, z = trace(A), trace(B), trace(mm(A, B))
x2, y2, z2 = mul(x, x), mul(y, y), mul(z, z)
comm = add(x2, y2, z2, scale(mul(mul(x, y), z), -1), const(-2, 4))
check("dense_chart", comm == word_trace("abAB", A, B))
words = ["aabAB", "aaabb", "aabab"]
rhs = [mul(x, add(comm, const(-1, 4))),
       add(mul(mul(add(x2, const(-1, 4)), y), z), scale(mul(x, y2), -1), scale(mul(x2, x), -1), scale(x, 3)),
       add(mul(x, z2), scale(mul(y, z), -1), scale(x, -1))]
actual = [word_trace(w, A, B) for w in words]
for a, b in zip(actual, rhs):
    check("dense_chart", a == b)
check("dense_chart", add(actual[0], actual[1], scale(actual[2], -1)) == x)
v = word_trace("aB", A, B)
def p2(p):
    return add(mul(p, p), const(-2, 4))
check("dense_chart", add(p2(z), p2(v), scale(mul(p2(x), p2(y)), -1)) == scale(add(comm, const(-2, 4)), 2))
for w, expected in zip(words, [(1, 0), (3, 2), (3, 2)]):
    hom = (w.count("a") - w.count("A"), w.count("b") - w.count("B"))
    check("word_combinatorics", hom == expected and gcd(*hom) == 1)
    check("word_combinatorics", all(a.swapcase() != b for a, b in zip(w, w[1:] + w[:1])))

# Polynomial recurrence is compared to the independent closed coefficient rule.
ORDER = 24
P = cheb(mon((1,)), ORDER, 1)
for n in range(1, ORDER + 1):
    expected = {(n - 2*j,): Fraction((-1)**j * n * factorial(n-j-1), factorial(j) * factorial(n-2*j))
                for j in range(n//2 + 1)}
    check("chebyshev_polynomials", P[n] == expected)
    for r in range(1, n + 1):
        # q^r(1-q^2)/(1+q^2)^(r+1), by the binomial series.
        coefficient = 0
        if n >= r and (n-r) % 2 == 0:
            j = (n-r)//2
            coefficient = (-1)**j * comb(r+j, j)
            if j:
                coefficient -= (-1)**(j-1) * comb(r+j-1, j-1)
        check("fixed_power_generating", P[n].get((r,), 0) == coefficient)

F = cheb(add(mon((1, 1, 0)), mon((0, 0, 1), -1)), ORDER, 3)
for n in range(1, ORDER + 1):
    expected = defaultdict(Fraction)
    for j in range(n//2 + 1):
        d = n - 2*j
        factor = Fraction((-1)**j * n * factorial(n-j-1), factorial(j) * factorial(d))
        for m in range(d + 1):
            r = d-m
            expected[(r, r, m)] += factor * comb(d, m) * (-1)**m
    check("figure_eight_polynomials", F[n] == clean(expected))
    check("figure_eight_pair_cancellation", F[n].get((1, 1, 0), 0) + F[n].get((0, 0, 1), 0) == 0)

# Root-sum recurrence and exact arcsine moments; no floating roots or quadrature.
S = [const(2, 1), const(1, 1)]
for n in range(2, 2*ORDER + 1):
    S.append(add(S[-1], mul(mon((1,)), S[-2])))
weights = [sum(c*comb(e[0], e[0]//2) for e, c in p.items() if e[0] % 2 == 0) for p in S]
for n in range(1, ORDER + 1):
    check("root_sum_filter", sum(c*weights[sum(e)] for e, c in F[n].items()) == 0)
    identified = defaultdict(Fraction)
    for (a, b, c), coefficient in F[n].items():
        identified[(a+b, c)] += coefficient
    check("coincident_cuff_filter", sum(c*weights[sum(e)] for e, c in clean(identified).items()) == 0)
# Verify the generating function by its squared identity; constant term 2 fixes branch.
W = {(n,): c for n, c in enumerate(weights)}
denom = {(0,): Fraction(1), (1,): Fraction(-2), (2,): Fraction(1), (4,): Fraction(-4)}
square_identity = mul(mul(W, W, 2*ORDER), denom, 2*ORDER)
check("weight_generating_identity", square_identity == {(0,): Fraction(4), (1,): Fraction(-4), (2,): Fraction(1)})

# Different formal lengths from the author's fixture; no common surface asserted.
cutoff = 18
generators = [mon((3, 1, 0, 0)), mon((4, 0, 1, 0)), mon((5, 0, 0, 1)),
              add(mon((9, 1, 1, 0)), mon((9, 0, 0, 1), -1))]
lengths = [3, 4, 5, 9]
product = const(1, 4)
for q, length in zip(generators, lengths):
    product = mul(product, add(*(power(q, n, 4, cutoff) for n in range(cutoff//length + 1))), cutoff)
enumerated = defaultdict(Fraction)
for i in range(cutoff//3 + 1):
    for j in range(cutoff//4 + 1):
        for k in range(cutoff//5 + 1):
            for m in range(cutoff//9 + 1):
                length = 3*i + 4*j + 5*k + 9*m
                if length <= cutoff:
                    for h in range(m+1):
                        enumerated[(length, i+m-h, j+m-h, k+h)] += (-1)**h * comb(m, h)
check("finite_euler", product == clean(enumerated))
for r in range(cutoff//3+1):
    for s in range(cutoff//4+1):
        for m in range(cutoff//5+1):
            length = 3*r+4*s+5*m
            if length <= cutoff:
                atoms = {e[0]: c for e, c in product.items() if e[1:] == (r, s, m)}
                check("finite_euler_first_atom", min(atoms) == length and atoms[length] == 1)
u = add(product, const(-1, 4))
log_product = add(*(scale(power(u, j, 4, cutoff), Fraction((-1)**(j+1), j)) for j in range(1, cutoff//3+1)))
log_expected = add(*(scale(power(q, j, 4, cutoff), Fraction(1, j))
                     for q, length in zip(generators, lengths) for j in range(1, cutoff//length+1)))
check("finite_euler_log", log_product == log_expected)
# Adams replacement differs already for the x generator at length 6.
check("ordinary_vs_adams", log_product.get((6, 0, 0, 0), 0) == 0)
check("ordinary_vs_adams", Fraction(-2, 2) != log_product.get((6, 0, 0, 0), 0))

# Check claim coverage and exact frozen bytes independently.
ledger_path = ROOT / "book/claims/sections23-25.json"
ledger = json.loads(ledger_path.read_text())
chapters = [ROOT / p for p in ledger["chapter_sources"]]
all_labels = [label for path in chapters for label in re.findall(r"\\label\{([^}]+)\}", path.read_text())]
claim_labels = [label for claim in ledger["claims"] for label in claim["labels"]]
structural = ledger["label_coverage"]["structural_or_figure_labels"]
check("coverage", len(ledger["claims"]) == 52)
check("coverage", len(all_labels) == len(set(all_labels)) == 91)
check("coverage", len(claim_labels) == len(set(claim_labels)) == 80)
check("coverage", set(all_labels) == set(claim_labels) | set(structural))
manifest = json.loads((HERE.parent / "algebra-author/author-freeze-manifest.json").read_text())
hashes = {}
for filename, expected in manifest["files"].items():
    raw = (ROOT / filename).read_bytes()
    hashes[filename] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
    check("frozen_bytes", hashes[filename] == expected)

result = {
    "status": "passed",
    "arithmetic": "Python integer and fractions.Fraction only; no numerical tolerances",
    "exact_checks": sum(COUNTS.values()),
    "groups": dict(COUNTS),
    "chebyshev_order": ORDER,
    "root_weight_order": 2*ORDER,
    "finite_euler_formal_lengths": lengths,
    "finite_euler_cutoff": cutoff,
    "first_weights": [int(w) for w in weights[:13]],
    "hashes": hashes,
    "scope": "Independent bounded algebra and structural probes. Dense-chart checks establish symbolic Laurent identities; extension to all SL(2) pairs uses the open-dense conjugacy argument in the review. No geometric enumeration, analytic tail computation, external theorem proof audit, companion code approval, or manuscript build is claimed.",
}
(HERE / "independent-probes-result.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
