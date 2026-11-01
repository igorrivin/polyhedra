"""Independent finite checks for the Section 15 proof review.

No maintained experiment or author companion is imported.  These exact checks
are algebraic evidence, not certificates for the analytic estimates.
"""
import json
import sympy as s

r = s.sqrt(2)
half = s.Rational(1, 2)
# coefficient, d(angle)/dv, d(angle)/deta, sine, cotangent
terms = [
    (-8, half, 3*half, s.Rational(1, 3), 2*r),
    (-6, -half, -2, 1/s.sqrt(3), r),
    (-2, -half, 0, 1/(9*s.sqrt(3)), -11*r),
    (12, 0, -half, s.sqrt(s.Rational(2, 3)), 1/r),
    (-4, 0, -3*half, s.sqrt(s.Rational(2, 3))/3, -5/r),
]
c = s.symbols('c')
# Lambda''=-cot; each further angle derivative sends c to -(1+c^2).
ld = {2: -c}
for n in range(3, 5):
    ld[n] = s.expand(-(1+c*c)*s.diff(ld[n-1], c))

actual = {}
expected = {'vv': 0, 'vvv': 54, 'veta': 18*r,
            'etaeta': 36*r, 'vvvv': -648*r, 'vveta': -18}
orders = {'vv': (2, 0), 'vvv': (3, 0), 'veta': (1, 1),
          'etaeta': (0, 2), 'vvvv': (4, 0), 'vveta': (2, 1)}
for label, (j, k) in orders.items():
    got = s.simplify(sum(C*av**j*ae**k*ld[j+k].subs(c, cot)
                         for C, av, ae, sin, cot in terms))
    assert s.simplify(got-expected[label]) == 0
    actual[label] = str(got)

v_log_ratio = s.simplify((2*terms[0][3])**4 /
                         ((2*terms[1][3])**3*(2*terms[2][3])))
eta_log_ratio = s.simplify((terms[0][3]/terms[1][3])**2 *
                           terms[3][3]/terms[4][3])
assert v_log_ratio == eta_log_ratio == 1
A = s.simplify((2*terms[0][3])**(-2) *
               (2*terms[1][3])**(-3*half) *
               (2*terms[2][3])**(3*half) *
               (terms[3][3]/terms[4][3])**3)
logAv = s.simplify(-2*half*terms[0][4] +
                   (-3*half)*(-half)*terms[1][4] +
                   3*half*(-half)*terms[2][4])
assert A == s.Rational(9, 4)
assert logAv == 7*r

u = s.symbols('u', real=True)
psi_prime = 4*2*r/(1+8*u*u) + 3*r/(1+2*u*u) - 11*r/(1+242*u*u)
psi_expected = 864*r*u*u*(3+11*u*u)/((1+8*u*u)*(1+2*u*u)*(1+242*u*u))
assert s.simplify(psi_prime-psi_expected) == 0

wr, alpha, Q = s.symbols('wr alpha Q', real=True)
tail = s.expand(4*(wr-3*alpha-Q/2) + 3*(4*alpha-wr-Q/2) + (2*Q-wr-Q/2))
assert tail == -2*Q

Ai, Aip, z = s.symbols('Ai Aip z')
corr = s.expand(7*r/s.Integer(3)*(-Aip) - r/s.Integer(3)*(2*Aip+z*z*Ai)
                + z/(6*r)*(z*Ai) + r/s.Integer(4)*z*z*Ai)
assert s.simplify(corr+3*r*Aip) == 0
measure = s.Rational(9, 4)*s.Rational(1, 3)
assert measure == s.Rational(3, 4)

print(json.dumps({
    'status': 'independent exact finite algebra passed',
    'proof_scope': 'Finite algebra only; no claim of numerical enclosure or full analytic proof.',
    'derivatives': actual,
    'Gv_log_ratio': str(v_log_ratio), 'Geta_log_ratio': str(eta_log_ratio),
    'A_star': str(A), 'log_A_v': str(logAv),
    'Psi_prime_identity': True, 'fixed_b_tail_coefficient': str(tail),
    'Airy_first_correction': str(corr), 'oriented_measure_prefactor': str(measure),
}, indent=2))
