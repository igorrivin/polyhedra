#!/usr/bin/env python3
"""Bounded exact reviewer checks; imports no author implementation."""
from fractions import Fraction as F
from itertools import combinations, product
from math import gcd
import json
from pathlib import Path


def n4(mu):
    # Direct four-point class: kappa and each psi/boundary have degree one.
    pairs = tuple(combinations(range(4), 2))
    light = tuple(pair for pair in pairs if sum(mu[i] for i in pair) < 1)
    r = tuple(1-m for m in mu)
    beta0 = 1-sum(x*x for x in r)
    linear = 2*sum(x*x for x in r)
    quad = -sum(x*x for x in r)
    for pair in light:
        c = 1-sum(mu[i] for i in pair)
        s = sum(r[i] for i in pair)
        beta0 += c*c
        linear -= 2*c*s
        quad += s*s
    # A different expression uses three unordered bipartitions and B_mu.
    b = (-2+sum(min(mu[0]+mu[i], 2-mu[0]-mu[i]) for i in (1, 2, 3)))/2
    xi = quad/8
    assert beta0 == 0
    assert linear == 4*b
    width = min(((1-sum(mu[i] for i in p))/sum(r[i] for i in p)
                 for p in light), default=F(1))
    epsilon = width/3
    a = tuple(mu[i]+epsilon*r[i] for i in range(4))
    direct = 2*(1-sum((1-x)**2 for x in a)
                +sum((1-sum(a[i] for i in p))**2 for p in pairs
                     if sum(a[i] for i in p) < 1))
    area_over_pi = 4*epsilon
    predicted = 2*b*area_over_pi+xi*area_over_pi**2
    assert direct == predicted
    return b, xi, width


def main():
    cases = []
    for numerators in product(range(1, 6), repeat=4):
        if sum(numerators) == 12:
            mu = tuple(F(m, 6) for m in numerators)
            n4(mu)
            cases.append(mu)
    assert n4((F(1, 2),)*4) == (F(1, 2), F(-1, 8), F(1))
    assert n4(tuple(map(F, ('3/10', '2/5', '3/5', '7/10')))) == (
        F(3, 10), F(9, 40), F(1, 11))
    for delta in (F(1, 10), F(1, 100)):
        assert n4((F(1, 2)-delta,)*2+(F(1, 2)+delta,)*2) == (
            F(1, 2)-delta, delta/2, 2*delta/(1+2*delta))
    # A symmetric Mbar_0,5 computation uses only the boundary incidence graph.
    pairs = tuple(combinations(range(5), 2))
    disjoint = sum(set(a).isdisjoint(b) for a, b in combinations(pairs, 2))
    t_square = -len(pairs)+2*disjoint
    b_square = t_square*F(1, 10)**2
    b_xi = t_square*F(1, 10)*F(1, 20)
    xi_square = t_square*F(1, 20)**2
    coefficients = (2*b_square, 2*b_xi, xi_square/2)
    # Unordered set partitions by collision type: 1^5, 2+1^3, 2+2+1.
    partition_sum = F(2)-10*F(1, 5)+15*F(1, 5)**2
    assert 16*partition_sum/6 == 8*b_square == F(8, 5)
    assert coefficients == (F(2, 5), F(1, 5), F(1, 40))
    # Local cyclic-cover orders: w-p=t^(q/g), y=t^(m/g)*unit.
    cyclic_cases = 0
    for q in range(2, 31):
        for m in range(1, q):
            g = gcd(q, m)
            order = (q-m)//g-1
            assert (q-m) % g == 0 and order >= 0
            cyclic_cases += 1
    # Pillowcase affine deformation gives |nu_(partial_tau)|^2=1/(4y^2).
    # FN form iG d tau wedge dbar tau has real coefficient 2G, whereas
    # the curvature -1 form has coefficient 1/y^2, independently of volumes.
    pillowcase = []
    for y in (F(1), F(3, 2), F(7, 3)):
        raw_g = F(1)/(4*y*y)
        ratio = (2*raw_g)/(F(1)/(y*y))
        assert ratio == F(1, 2)
        pillowcase.append({'Im_tau': str(y), 'WP_CH_ratio': str(ratio)})
    report = {
        'status': 'passed',
        'arithmetic': 'fractions.Fraction; no floating arithmetic or author-code import',
        'n4_denominator_6_weight_vectors': len(cases),
        'named_n4_cases': 4,
        'n5_boundary_disjoint_pairs': disjoint,
        'n5_T_squared': t_square,
        'n5_CH_over_pi_squared': str(8*b_square),
        'n5_WP_over_pi4_coefficients_in_A_over_pi': list(map(str, coefficients)),
        'cyclic_cover_local_orders_checked': cyclic_cases,
        'pillowcase_local_pairing_checks': pillowcase,
        'scope': 'Finite checks of the written derivations, not proof of general class identities, metric convergence, or geometric realization.'
    }
    print(json.dumps(report, indent=2))
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__':
    main()
