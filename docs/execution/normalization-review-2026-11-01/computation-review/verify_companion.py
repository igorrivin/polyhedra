"""Bounded independent arithmetic and execution review; writes outer evidence only."""
from fractions import Fraction as F
from itertools import combinations, product, permutations
from pathlib import Path
from math import factorial
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time

ROOT = Path('/Volumes/Lexar/lambda/devel/polyhedra/consolidated')
OUT = Path(__file__).resolve().parent
SRC = ROOT / 'experiments/normalizations'
SPEC = importlib.util.spec_from_file_location('reviewed_normalizations', SRC / 'run.py')
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
COMMANDS = []


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name, argv, cwd=ROOT, expected=0):
    start = time.monotonic()
    process = subprocess.run(list(map(str, argv)), cwd=cwd, text=True, capture_output=True,
                             env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
    (OUT / f'{name}.stdout').write_text(process.stdout)
    (OUT / f'{name}.stderr').write_text(process.stderr)
    COMMANDS.append(dict(name=name, argv=list(map(str, argv)), cwd=str(cwd),
                         returncode=process.returncode, elapsed_seconds=time.monotonic()-start))
    (OUT / 'commands.json').write_text(json.dumps(COMMANDS, indent=2)+'\n')
    require(process.returncode == expected, f'{name}: exit {process.returncode}')
    return process


def divisors(n):
    """All subsets encoded by masks, retaining the side containing mark zero."""
    return [mask for mask in range(1, 1 << n)
            if mask & 1 and 2 <= mask.bit_count() <= n-2]


def side_weight(weights, mask):
    return sum(w for i, w in enumerate(weights) if mask >> i & 1)


def boundary_vector(n, mask):
    if n == 4:
        return (F(1),)
    side = [i for i in range(5) if mask >> i & 1]
    pair = side if len(side) == 2 else [i for i in range(5) if i not in side]
    v = [F(0)]*5
    if 4 in pair:
        v[1+next(i for i in pair if i != 4)] = 1
    else:
        v[0] = 1
        for i in range(4):
            if i not in pair:
                v[i+1] = -1
    return tuple(v)


def psis(n):
    # Kapranov blowup model Mbar_0,5 = Bl_4(P^2), H^2=1, E_i^2=-1.
    # psi_4=H; psi_i=2H-sum_{j!=i}E_j; kappa=3H-sum_i E_i.
    return [(F(1),)]*4 if n == 4 else [
        tuple([F(2)] + [F(0 if i == j else -1) for j in range(4)])
        for i in range(4)] + [(F(1), F(0), F(0), F(0), F(0))]


def add_term(target, coefficient, vector):
    for i, x in enumerate(vector):
        target[i] += coefficient*x


def dot(a, b):
    return a[0]*b[0]-sum(x*y for x, y in zip(a[1:], b[1:]))


def reference_classes(mu):
    n, D = len(mu), len(mu)-2
    B, Xi = [F(0)]*(1 if n == 4 else 5), [F(0)]*(1 if n == 4 else 5)
    for w, psi in zip(mu, psis(n)):
        add_term(B, -w/2, psi)
        add_term(Xi, -(1-w)**2/(2*D*D), psi)
    for mask in divisors(n):
        left, right = side_weight(mu, mask), 2-side_weight(mu, mask)
        add_term(B, min(left, right)/2, boundary_vector(n, mask))
        size = mask.bit_count()
        if left < 1:
            add_term(Xi, (size-left)**2/(2*D*D), boundary_vector(n, mask))
        elif right < 1:
            add_term(Xi, (n-size-right)**2/(2*D*D), boundary_vector(n, mask))
    return B, Xi


def direct_wp(weights):
    n = len(weights)
    beta = [F(1)] if n == 4 else list(map(F, (3, -1, -1, -1, -1)))
    for w, psi in zip(weights, psis(n)):
        add_term(beta, -(1-w)**2, psi)
    for mask in divisors(n):
        a = side_weight(weights, mask)
        b = sum(weights)-a
        add_term(beta, max(F(0), 1-a, 1-b)**2, boundary_vector(n, mask))
    return 2*beta[0] if n == 4 else 2*dot(beta, beta)


def reference_polynomial(mu):
    B, X = reference_classes(mu)
    return ({1: 2*B[0], 2: X[0]} if len(mu) == 4 else
            {2: 2*dot(B, B), 3: 2*dot(B, X), 4: dot(X, X)/2})


def restricted_growth(n):
    """A partition enumerator independent of the author's insertion recursion."""
    for rest in product(range(n), repeat=n-1):
        word = (0,)+rest
        if all(word[i] <= 1+max(word[:i]) for i in range(1, n)):
            yield tuple(tuple(i for i, v in enumerate(word) if v == j)
                        for j in range(max(word)+1))


PARTITIONS = {n: list(restricted_growth(n)) for n in (4, 5, 6)}


def partition_volume(mu):
    n, total = len(mu), F(0)
    for parts in PARTITIONS[n]:
        k = len(parts)
        if k < 3:
            continue
        term = F((-1)**(k+1)*factorial(k-3))
        for part in parts:
            term *= max(F(0), 1-sum(mu[i] for i in part))**(len(part)-1)
        total += term
    return F((-4)**(n-3), factorial(n-2))*total


def chamber(mu):
    candidates = []
    for mask in range(1, 1 << len(mu)):
        size = mask.bit_count()
        s = side_weight(mu, mask)
        if 2 <= size <= len(mu)-2 and s < 1:
            candidates.append((1-s)/(size-s))
    return (min(candidates), True) if candidates else (F(1), False)


def flat_probes():
    fixtures = json.loads((SRC/'fixture.json').read_text())
    inputs = {n: set(tuple(F(i, 6) for i in ints)
                     for ints in product(range(1, 6), repeat=n) if sum(ints) == 12)
              for n in (4, 5)}
    for row in fixtures['flat_weights']:
        weights = tuple(map(F, row['mu']))
        inputs[len(weights)].update(permutations(weights))
    total_samples = 0
    for n, rows in inputs.items():
        for mu in sorted(rows):
            polynomial = reference_polynomial(mu)
            require(module.wp_polynomial(mu) == polynomial, 'blowup polynomial')
            B, _ = reference_classes(mu)
            ch = 4*B[0] if n == 4 else 8*dot(B, B)
            require(module.mcmullen_volume(mu)[0] == partition_volume(mu) == ch,
                    'independent partition/top-intersection')
            upper, strict = chamber(mu)
            require(module.final_chamber(mu) == (upper, strict), 'chamber boundary')
            require(not module.in_final_chamber(mu, F(0)), 'zero area accepted')
            require(module.in_final_chamber(mu, upper) == (not strict), 'wall endpoint')
            for eps in (upper/4, 3*upper/4, upper):
                weights = tuple(w+eps*(1-w) for w in mu)
                a = 2*(n-2)*eps
                predicted = sum(c*a**degree for degree, c in polynomial.items())
                require(module.wp_from_weights(weights) == direct_wp(weights) == predicted,
                        'direct class/polynomial')
                total_samples += 1
    return {'n4_weight_vectors': len(inputs[4]), 'n5_weight_vectors': len(inputs[5]),
            'direct_class_samples_including_continuous_wall_values': total_samples,
            'partition_counts': {str(n): len(PARTITIONS[n]) for n in PARTITIONS},
            'domain': 'denominator-six positive flat grid plus every distinct fixture relabeling'}


def mm(a, b):
    return (a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3],
            a[2]*b[0]+a[3]*b[2], a[2]*b[1]+a[3]*b[3])


def tr(a):
    return a[0]+a[3]


def sl2_probes():
    matrices = [tuple(map(F, row)) for row in
                ((1,0,0,1), (1,1,0,1), (1,0,1,1), (2,1,1,1),
                 (1,1,1,2), (1,-1,0,1), (1,0,-1,1), ('3/2',0,0,'2/3'))]
    count = degenerate = 0
    for A, B, C in product(matrices, repeat=3):
        X, Y, Z = mm(A, B), mm(A, C), mm(B, C)
        a,b,c,d,x,y,z = tr(A),tr(B),tr(C),tr(mm(X,C)),tr(X),tr(Y),tr(Z)
        derivative = 2*z+x*y-a*d-b*c
        def conjugated_trace(s):
            positive = (1+s*X[0],s*X[1],s*X[2],1+s*X[3])
            negative = (1-s*X[0],-s*X[1],-s*X[2],1-s*X[3])
            return tr(mm(mm(mm(A, positive), C), negative))
        # The expression is exactly quadratic in s, so this extracts its
        # linear coefficient without a numerical differentiation error.
        difference = (conjugated_trace(F(1))-conjugated_trace(F(-1)))/2
        record = {'id': str(count), 'chart_nondegenerate': derivative != 0}
        for name, value in zip('ABC', (A,B,C)):
            record[name] = [[str(value[0]),str(value[1])],[str(value[2]),str(value[3])]]
        result = module.fricke_fixture(record)
        require(result['Phi_z'] == derivative == -difference, 'SL2 linear coefficient')
        require(result['Fricke_residual'] == 0, 'Fricke residual')
        count += 1
        degenerate += derivative == 0
    return {'triples': count, 'degenerate_trace_charts': degenerate,
            'independent_twist_test': 'exact odd part of a quadratic conjugation expression'}


def f_curves():
    rows = [tuple(map(F, values)) for values in
            (('1/3',)*6, ('1/10','1/5','3/10','2/5','9/20','11/20'),
             ('1/6','1/6','1/6','1/2','1/2','1/2'))]
    count = 0
    for mu in rows:
        for parts in PARTITIONS[6]:
            if len(parts) != 4:
                continue
            result = module.f_curve_probe(mu, parts)
            block_weights = [sum(mu[i] for i in part) for part in parts]
            # B restricted to an F-curve reduces to the four block weights;
            # this formulation never expands six-mark psi/boundary classes.
            B = (-sum(min(w,2-w) for w in block_weights)
                 +sum(min(block_weights[0]+block_weights[i],
                          2-block_weights[0]-block_weights[i]) for i in (1,2,3)))/2
            require(result['B_pairing'] == B and result['beta_epsilon_linear_pairing'] == 8*B,
                    'F-curve block reduction')
            count += 1
    return {'weight_vectors': len(rows), 'four_block_partitions_per_vector': 65, 'probes': count}


def finite_matrix_checks():
    def det_gauss(matrix):
        a = [[F(x) for x in row] for row in matrix]
        result = F(1)
        for i in range(len(a)):
            pivot = next((j for j in range(i,len(a)) if a[j][i]), None)
            if pivot is None:
                return F(0)
            if pivot != i:
                a[i],a[pivot] = a[pivot],a[i]
                result *= -1
            diagonal = a[i][i]
            result *= diagonal
            for j in range(i+1,len(a)):
                multiple = a[j][i]/diagonal
                a[j] = [x-multiple*y for x,y in zip(a[j],a[i])]
        return result
    norms = module.normalization_checks()
    require(det_gauss(norms['perimeter_minor']) == -2, 'Gaussian perimeter determinant')
    require(norms['WP_two_sheets_over_pi2'] == 4*F(1,2)*2*F(1,2), 'measure factors')
    gram = module.gram_pfaffian_checks()
    require(gram['gram_determinant'] == (-5)*3**3, 'Gram eigenvalue determinant')
    require(gram['arc_density_coefficient'] == 2*(2*gram['uniform_q']+1), 'triple-angle density')
    require(det_gauss(gram['skew_matrix']) == 144, 'Gaussian skew determinant')
    require(gram['inverse_poisson_density_coefficient'] == F(1,12), 'inverse Pfaffian density')
    return {'perimeter_determinant': -2, 'gram_eigenvalues': [-5,3,3,3],
            'skew_determinant': 144, 'scope': 'finite fixtures conditional on geometric input formulas'}


def main():
    paths = [SRC/'run.py',SRC/'fixture.json',SRC/'README.md',SRC/'tests/test_normalizations.py']
    before = {str(p.relative_to(ROOT)):digest(p) for p in paths}
    require(before['experiments/normalizations/run.py'] ==
            'cd74141cb4ed4230b84f3e156c96ec67dbbed27bc4047c05fc2f8106e74d018d', 'author source drift')
    run('unittest', [sys.executable,'-B','-m','unittest','discover','-s',SRC/'tests','-v'])
    run('ruff', ['/opt/anaconda3/bin/ruff','check',SRC])
    run('fixed-replay', [sys.executable,'-B',SRC/'run.py','--output',OUT/'replay.json'],Path('/private/tmp'))
    run('optimized-replay', [sys.executable,'-B','-O',SRC/'run.py','--output',OUT/'replay-optimized.json'],Path('/private/tmp'))
    replay = json.loads((OUT/'replay.json').read_text())
    optimized = json.loads((OUT/'replay-optimized.json').read_text())
    author = json.loads((OUT.parent/'computation/result-author-01.json').read_text())
    ignored = ['generated_at_utc','elapsed_seconds','source']
    science = lambda row: {k:v for k,v in row.items() if k not in ignored}
    require(science(author) == science(replay) == science(optimized), 'scientific replay mismatch')
    for item in replay['source']['sources']:
        if item['path'] in before:
            require(before[item['path']] == item['sha256'], 'source hash mismatch')
    require(replay['source']['git_dirty'] is True, 'dirty provenance')
    result = {'flat_checks':flat_probes(), 'sl2_checks':sl2_probes(),
              'f_curve_checks':f_curves(), 'matrix_checks':finite_matrix_checks()}
    with tempfile.TemporaryDirectory() as temp:
        target = Path(temp)/'not-created.json'
        failure_code = (
            'import importlib.util\n'
            f's=importlib.util.spec_from_file_location("reviewed",{str(SRC/"run.py")!r})\n'
            'm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n'
            'def fail(): m.check(False,"injected failed exact check")\n'
            'm.normalization_checks=fail\n'
            f'm.main(["--output",{str(target)!r}])\n')
        failure = run('optimized-failure', [sys.executable,'-B','-O','-c',failure_code],Path(temp),1)
        require('injected failed exact check' in failure.stderr and not target.exists(), 'failed-check output contract')
        import_code = (
            'import importlib.util,subprocess\n'
            'def fail(*args,**kwargs): raise RuntimeError("import invoked a subprocess")\n'
            'subprocess.check_output=fail\n'
            f's=importlib.util.spec_from_file_location("reviewed",{str(SRC/"run.py")!r})\n'
            'm=importlib.util.module_from_spec(s);s.loader.exec_module(m)\n')
        imported = run('import-only', [sys.executable,'-B','-c',import_code],Path(temp))
        require(not imported.stdout and not imported.stderr and not list(Path(temp).iterdir()), 'import side effects')
    result.update({'status':'pass', 'author_owned_source_sha256':before,
                   'unit_test_cases':11, 'scientific_replay_equal':True,
                   'scientific_comparison_omitted_top_level_fields':ignored,
                   'omission_reason':'timestamps/timing and development source record; stable code hashes checked separately; concurrent manuscript edits are outside this review',
                   'optimized_checks_active':True,'failure_before_output':True,'import_safe':True,
                   'limits':['Finite arithmetic only; external intersection and geometric theorems are inputs.',
                             'No general divisor proof, local convergence proof, full cell integration or global realization is asserted.',
                             'Manuscript sources may change during parallel authorship and are not frozen by this code review.']})
    require(before == {str(p.relative_to(ROOT)):digest(p) for p in paths}, 'source changed during review')
    (OUT/'independent-result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
