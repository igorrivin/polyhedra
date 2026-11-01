#!/usr/bin/env python3
"""Independent exact finite probes and source/label pins for review A.

The Gram grid probes the algebra supporting the written general argument.
It is not a replacement for that argument or a geometric certification tool.
"""
from fractions import Fraction as Q
from hashlib import sha256
from itertools import combinations, product
import json
from pathlib import Path
import re
import subprocess

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = ROOT.parent / 'execution/normalization-review-2026-11-01/math-review-a'
BASE = 'ad63b7ac9821040cb69e19c61bfbc46c68eff1a3'


def det(rows):
    a = [list(map(Q, row)) for row in rows]
    result = Q(1)
    for k in range(len(a)):
        choices = [i for i in range(k, len(a)) if a[i][k]]
        if not choices:
            return Q(0)
        pivot = choices[0]
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            result = -result
        diagonal = a[k][k]
        result *= diagonal
        for i in range(k+1, len(a)):
            factor = a[i][k] / diagonal
            for j in range(k+1, len(a)):
                a[i][j] -= factor*a[k][j]
    return result


def check(condition, message):
    if not condition:
        raise ArithmeticError(message)


def expand(path, baseline=False):
    data = (subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
            if baseline else (ROOT/path).read_bytes())
    def replace(match):
        name = match.group(1).decode()
        if not name.endswith('.tex'):
            name += '.tex'
        return expand('book/'+name, baseline)
    return re.sub(rb'\\input\{([^{}]+)\}', replace, data)


def main():
    files = [f'book/chapters/{name}' for name in (
        '01-volume-normalization.tex', '02-ideal-angle-cells.tex',
        '03-ideal-tetrahedron.tex', '04-hyperideal-integrand.tex',
        '05-boundary-cone-continuation.tex', '06-torus-sphere.tex',
        'appendix-a-fricke.tex')]
    files += ['book/claims/sections1-6.json']
    pins = {name: sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    original = re.findall(rb'\\label\{([^{}]+)\}', expand('book/main.tex', True))
    current = re.findall(rb'\\label\{([^{}]+)\}', expand('book/main.tex'))
    check(original == current and len(set(current)) == 607, 'global label/order drift')
    ledger = json.loads((ROOT/files[-1]).read_text())
    check(len(ledger['claims']) == len({c['id'] for c in ledger['claims']}), 'duplicate claims')
    check(all(label.encode() in current for c in ledger['claims'] for label in c['labels']),
          'claim label does not exist')

    perimeter = ((1,1,1,0,0,0), (1,0,0,1,1,0),
                 (0,1,0,1,0,1), (0,0,1,0,1,1))
    minors = {str(cols): str(det([[row[j] for j in cols] for row in perimeter]))
              for cols in combinations(range(6), 4)}
    check(minors['(2, 3, 4, 5)'] == '-2', 'elimination determinant')
    check(set(map(Q, minors.values())) <= {Q(-2), Q(0), Q(2)}, 'unexpected perimeter minor')

    counts = {'negative': 0, 'zero': 0, 'positive': 0, 'schur_checks': 0}
    edges = tuple(combinations(range(4), 2))
    for values in product((Q(6,5), Q(2), Q(4)), repeat=6):
        g = [[Q(i == j) for j in range(4)] for i in range(4)]
        for (i,j), value in zip(edges, values):
            g[i][j] = g[j][i] = -value
        full = det(g)
        counts['negative' if full < 0 else 'positive' if full > 0 else 'zero'] += 1
        for i in range(4):
            others = [j for j in range(4) if j != i]
            s = [[g[j][k]-g[j][i]*g[i][k] for k in others] for j in others]
            check(det(s) == full, 'Schur determinant identity')
            check(all(s[j][j] < 0 for j in range(3)), 'projected timelike norms')
            check(all(s[j][k] < 0 and s[j][k]**2 > s[j][j]*s[k][k]
                      for j,k in combinations(range(3),2)), 'same-sheet distance inequality')
            counts['schur_checks'] += 1
        principal = [Q(1)] + [det([row[:k] for row in g[:k]]) for k in range(1,5)]
        if full:
            pivots = [principal[k+1]/principal[k] for k in range(4)]
            inertia = (sum(x > 0 for x in pivots), sum(x < 0 for x in pivots))
            check(inertia == ((3,1) if full < 0 else (2,2)), 'exact LDL inertia')
    report = {
        'status': 'passed', 'arithmetic': 'exact fractions; determinant elimination, no tolerances',
        'baseline': BASE, 'approved_source_sha256': pins,
        'all_book_labels_preserved_in_order': len(current), 'claims': len(ledger['claims']),
        'tetrahedron_all_4x4_minors': minors, 'gram_grid': counts,
        'gram_grid_values': ['6/5','2','4'], 'gram_grid_assignments': 729,
        'scope': 'Finite independent algebra probes only. General geometry follows the separately reviewed written proof and cited theorem inputs.'}
    (OUT/'verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('status','all_book_labels_preserved_in_order','claims','gram_grid')},indent=2))


if __name__ == '__main__':
    main()
