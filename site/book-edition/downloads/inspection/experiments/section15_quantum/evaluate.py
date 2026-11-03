"""Exact cleared Section 15 integral, with a bounded double-sine expansion.

The outer quadrature is ordinary multiprecision arithmetic, not an interval
certificate. The explicit remainder and tail bound functions return exact
rational bounds conditional on the stated centered strip. No Airy
approximation occurs in ``integrate``.
"""

from dataclasses import dataclass
from fractions import Fraction
from math import factorial
from time import perf_counter

import mpmath as mp


WEIGHTS = (4, 3, 1, 2, -6)
EPSILON = Fraction(1, 100)


def finite(value):
    """Reject NaN and infinities before a comparison can hide them."""
    if not mp.isfinite(value):
        raise ArithmeticError(f"nonfinite numerical value: {value}")
    return value


def rational(value):
    q = Fraction(value)
    return mp.mpf(q.numerator) / q.denominator


def d_remainder_bound(b, epsilon, terms):
    """Exact rational upper bound for one centered D_b on the closed strip.

    Uses pi>3, zeta(2K+2)<2, and the integral comparison bound for
    Hurwitz zeta.  Valid for real b>0, 0<epsilon<=1/2 and integer K>=1.
    """
    b, epsilon = Fraction(b), Fraction(epsilon)
    if b <= 0 or not 0 < epsilon <= Fraction(1, 2):
        raise ValueError("positive b and 0 < epsilon <= 1/2 required")
    if not isinstance(terms, int) or terms < 1:
        raise ValueError("terms must be a positive integer")
    s = 2 * terms + 1
    return (b ** (4 * terms + 2) * 4 * factorial(2 * terms)
            * (epsilon ** (-s) + epsilon ** (1 - s) / (s - 1))
            / (3 ** (2 * terms + 2) * 2 ** (2 * terms + 1)))


def d_tail_bound(b, epsilon, cutoff):
    """Exact rational bound for the direct D integral beyond cutoff>=1.

    Conditional on epsilon<=Re(z)<=1-epsilon.  Uses |csch(u)-1/u|<=u/6,
    e>2, and 1-exp(-2*cutoff)>1/2.  This does not bound finite quadrature.
    """
    b, epsilon, cutoff = Fraction(b), Fraction(epsilon), Fraction(cutoff)
    if b <= 0 or not 0 < epsilon <= Fraction(1, 2) or cutoff < 1:
        raise ValueError("positive b, 0<epsilon<=1/2, and cutoff>=1 required")
    exponent = 2 * epsilon * cutoff
    integer_exponent = exponent.numerator // exponent.denominator
    return b ** 2 / (6 * epsilon * 2 ** integer_exponent)


def cot_polynomials(terms):
    """Integer P_n with d_z^n cot(pi*z)=pi^n P_n(cot(pi*z))."""
    result, p = [], [0, 1]
    for order in range(2 * terms - 1):
        if order % 2 == 0:
            result.append(tuple(reversed(p)))
        q = [0] * (len(p) + 1)
        for index in range(1, len(p)):
            q[index - 1] -= index * p[index]
            q[index + 1] -= index * p[index]
        p = q
    return result


def lobachevsky(z):
    """Lambda(pi*z), holomorphic on 0<Re z<1 and zero at z=1/2.

    The two polylogarithms use their principal branches.  In this strip
    their arguments do not cross [1,infinity); the difference continues
    the real Lobachevsky primitive with derivative -pi*log(2*sin(pi*z)).
    """
    if not 0 < mp.re(z) < 1:
        raise ValueError("Lobachevsky argument must lie in its open strip")
    return finite((mp.polylog(2, mp.exp(2j * mp.pi * z))
                   - mp.polylog(2, mp.exp(-2j * mp.pi * z))) / (4j))


class DoubleSine:
    """Centered log S_b(z/b+b/2), using a finite, bounded D_b expansion."""

    def __init__(self, b, digits, epsilon=EPSILON, extra_terms=0):
        self.b_fraction = Fraction(b)
        self.b = rational(self.b_fraction)
        self.epsilon = Fraction(epsilon)
        if not isinstance(digits, int) or digits < 10:
            raise ValueError("digits must be an integer >= 10")
        if not isinstance(extra_terms, int) or extra_terms < 0:
            raise ValueError("extra_terms must be a nonnegative integer")
        target = Fraction(1, 10 ** digits)
        for terms in range(1, 201):
            bound = 16 * d_remainder_bound(self.b_fraction, self.epsilon, terms)
            if bound < target:
                break
        else:
            raise ArithmeticError("D series did not reach its requested bound")
        self.terms = terms + extra_terms
        self.log_bound = 16 * d_remainder_bound(
            self.b_fraction, self.epsilon, self.terms)
        if self.log_bound >= target:
            raise ArithmeticError("extra terms degraded the D remainder bound")
        self.polynomials = cot_polynomials(self.terms)
        self.coefficients = [
            2 * (-1) ** k * (1 - mp.mpf(2) ** (1 - 2 * k)) * mp.zeta(2 * k)
            * self.b ** (4 * k - 2) / (mp.pi * 2 ** (2 * k))
            for k in range(1, self.terms + 1)
        ]

    def check_strip(self, z):
        finite(z)
        eps = rational(self.epsilon)
        if not eps <= mp.re(z) <= 1 - eps:
            raise ValueError("centered argument is outside the bounded strip")

    def correction(self, z):
        self.check_strip(z)
        c = mp.cot(mp.pi * z)
        return finite(mp.fsum(a * mp.polyval(p, c)
                              for a, p in zip(self.coefficients, self.polynomials)))

    def log(self, z):
        return finite(-lobachevsky(z) / (mp.pi * self.b ** 2)
                      + self.correction(z))


def csch_minus_inverse(u):
    """Stable real csch(u)-1/u, independent of the cot-polynomial expansion."""
    if u == 0:
        return mp.mpf(0)
    if u < 0:
        return -csch_minus_inverse(-u)
    if u < mp.mpf('0.5'):
        # Compute sinh(u)-u by its positive Taylor series, avoiding subtraction.
        term, terms, degree = u ** 3 / 6, [], 3
        while True:
            terms.append(term)
            term *= u ** 2 / ((degree + 1) * (degree + 2))
            degree += 2
            if abs(term) <= abs(terms[0]) * mp.eps / 8:
                break
        return -mp.fsum(terms) / (u * mp.sinh(u))
    return 1 / mp.sinh(u) - 1 / u


def direct_correction(b, z, method='gauss-legendre', finer=False):
    """Independent quadrature of the convergent real D_b integral."""
    b = rational(b)
    if not 0 < mp.re(z) < 1:
        raise ValueError("direct correction requires the centered strip")
    if method not in ('gauss-legendre', 'tanh-sinh'):
        raise ValueError("unsupported direct quadrature method")

    def kernel(s):
        if s == 0:
            return -(1 - 2 * z) * b ** 2 / 12
        return (mp.sinh((1 - 2 * z) * s) / (2 * s * mp.sinh(s))
                * csch_minus_inverse(b ** 2 * s))

    panels = [0, 1, 4, 16, 64, 256, 1024, 2048, 4096, 8192, mp.inf]
    if finer:
        panels = [0, mp.mpf('0.5')] + [2 ** k for k in range(15)] + [mp.inf]
    value, estimate = mp.quad(kernel, panels, method=method, error=True)
    return finite(value), finite(estimate)


def direct_log_sine(b, z):
    """Full convergent log S_b real integral, without Lambda or D polynomials.

    Substitution t=2*b*s gives the explicit kernel below.  Dynamic guard
    digits handle the removable cancellation at s=0.  This uses the
    convergent linear subtraction, correcting TV v3 Appendix A.1's typo.
    """
    b = rational(b)
    a = 1 - 2 * z
    if not 0 < mp.re(z) < 1:
        raise ValueError("direct log S requires the centered strip")

    def kernel(s):
        if s == 0:
            return a * (a ** 2 - 1 - b ** 4) / (12 * b ** 2)
        guard = 30 + max(0, int(-2 * mp.log10(abs(s))))
        with mp.extradps(guard):
            return (mp.sinh(a * s) / (2 * mp.sinh(s) * mp.sinh(b ** 2 * s))
                    - a / (2 * b ** 2 * s)) / s

    value, estimate = mp.quad(kernel, [0, 1, 4, 16],
                              method='gauss-legendre', error=True)
    # The subtraction has an algebraic tail. Integrate that tail exactly,
    # leaving an exponentially decaying kernel for the infinite quadrature.
    def tail(s):
        return mp.sinh(a * s) / (2 * s * mp.sinh(s) * mp.sinh(b ** 2 * s))

    tail_value, tail_estimate = mp.quad(tail, [16, 64, 256, 1024, 2048, 4096, 8192, mp.inf],
                                       method='gauss-legendre', error=True)
    return finite(value + tail_value - a / (32 * b ** 2)), finite(estimate + tail_estimate)


@dataclass(frozen=True)
class Parameters:
    b: str
    zeta: str
    contour_real: str
    cutoff: int
    digits: int
    extra_terms: int = 0


class ClearedIntegrand:
    def __init__(self, parameters):
        self.parameters = parameters
        self.b = rational(parameters.b)
        self.zeta = rational(parameters.zeta)
        self.contour_real = rational(parameters.contour_real)
        if self.b <= 0 or self.contour_real <= 0:
            raise ValueError("b and contour_real must be positive")
        self.h = 2 * mp.pi * self.b ** 2
        self.lam = self.h ** (mp.mpf(1) / 3)
        self.eta_e = mp.acos(mp.mpf(1) / 3)
        self.eta = self.eta_e - self.lam ** 2 * self.zeta / (6 * mp.sqrt(2))
        self.v_star = 4 * mp.pi - 5 * self.eta_e
        self.sb = DoubleSine(parameters.b, parameters.digits + 5,
                             extra_terms=parameters.extra_terms)
        self.real_arguments = self.arguments(mp.mpf(0))
        for z in self.real_arguments:
            self.sb.check_strip(z)
        self.external_leading = mp.fsum(
            -w * lobachevsky(z) / (mp.pi * self.b ** 2)
            for w, z in zip(WEIGHTS[3:], self.real_arguments[3:]))
        self.external_correction = mp.fsum(
            w * self.sb.correction(z)
            for w, z in zip(WEIGHTS[3:], self.real_arguments[3:]))
        self.cache = {}

    def arguments(self, t):
        v = self.v_star + self.lam * (self.contour_real + 1j * t) / 3
        s = (mp.pi - self.eta) / 2
        return (
            (v - 3 * mp.pi + 3 * self.eta) / (2 * mp.pi) - self.b ** 2 / 2,
            (4 * mp.pi - 4 * self.eta - v) / (2 * mp.pi) - self.b ** 2 / 2,
            (4 * mp.pi - v) / (2 * mp.pi) + 3 * self.b ** 2 / 2,
            3 * s / mp.pi - 3 * self.b ** 2 / 2,
            s / mp.pi - self.b ** 2 / 2,
        )

    def leading_log(self, t):
        return finite(self.external_leading + mp.fsum(
            -w * lobachevsky(z) / (mp.pi * self.b ** 2)
            for w, z in zip(WEIGHTS[:3], self.arguments(t)[:3])))

    def log(self, t):
        return finite(self.leading_log(t) + self.external_correction + mp.fsum(
            w * self.sb.correction(z)
            for w, z in zip(WEIGHTS[:3], self.arguments(t)[:3])))

    def __call__(self, t):
        t = mp.mpf(t)
        key = t._mpf_
        if key not in self.cache:
            self.cache[key] = finite(mp.exp(self.log(t)))
        return self.cache[key]

    def tail_diagnostic(self, cutoff):
        """Analytic majorant formula, evaluated WITHOUT outward rounding.

        Positivity of the three numerator coefficients implies monotonic
        Psi on r>=0.  The sign checks and all transcendental quantities
        here are floating point, so this is not a certified tail bound.
        """
        c1, c2, c3 = [mp.re(mp.cot(mp.pi * z)) for z in self.real_arguments[:3]]
        coefficients = (
            4 * c1 + 3 * c2 + c3,
            4 * c1 * (c2 ** 2 + c3 ** 2) + 3 * c2 * (c1 ** 2 + c3 ** 2)
            + c3 * (c1 ** 2 + c2 ** 2),
            4 * c1 * c2 ** 2 * c3 ** 2 + 3 * c2 * c1 ** 2 * c3 ** 2
            + c3 * c1 ** 2 * c2 ** 2,
        )
        if any(finite(c) <= 0 for c in coefficients):
            raise ArithmeticError("positive-coefficient tail condition failed")
        r = mp.tanh(self.lam * cutoff / 6)
        psi = finite(4 * mp.atan(c1 * r) + 3 * mp.atan(c2 * r) + mp.atan(c3 * r))
        if psi <= 0:
            raise ArithmeticError("positive tail slope failed")
        d_majorant = finite(mp.pi * self.b ** 2 / 24 * mp.fsum(
            abs(w) * abs(mp.cot(mp.pi * mp.re(z)))
            for w, z in zip(WEIGHTS, self.real_arguments)))
        majorant = finite(4 / (9 * mp.pi) * 3 * self.h / (self.lam * psi)
                           * mp.exp(mp.re(self.leading_log(cutoff)) + d_majorant))
        return {'positive_numerator_coefficients': coefficients,
                'psi_at_cutoff': psi, 'global_real_D_majorant': d_majorant,
                'normalized_two_sided_tail_majorant_estimate': majorant,
                'status': 'analytic_formula_evaluated_without_outward_rounding'}


def integrate(parameters):
    """Return the exact-integrand quadrature and explicitly separated diagnostics."""
    if not isinstance(parameters.digits, int) or parameters.digits < 30:
        raise ValueError("at least 30 working decimal digits required")
    if not isinstance(parameters.cutoff, int) or parameters.cutoff < 4:
        raise ValueError("an integer cutoff >=4 required")
    started = perf_counter()
    with mp.workdps(parameters.digits):
        integrand = ClearedIntegrand(parameters)
        endpoint = parameters.cutoff
        split = min(12, endpoint - 2)
        # The shorter cutoff must be a panel endpoint, including for odd T.
        panels = sorted(set(range(0, endpoint, 2)) | {split, endpoint})
        norm = 4 / (9 * mp.pi)
        part_values, part_errors = [], []
        for left, right in zip(panels, panels[1:]):
            value, error = mp.quad(lambda t: mp.re(integrand(t)), [left, right],
                                   method='gauss-legendre', error=True)
            part_values.append(finite(value))
            part_errors.append(finite(error))
        value = norm * mp.fsum(part_values)
        absolute, absolute_error = mp.quad(lambda t: abs(integrand(t)), panels,
                                           method='gauss-legendre', error=True)
        absolute, absolute_error = finite(norm * absolute), finite(norm * absolute_error)
        error = finite(norm * mp.fsum(part_errors))
        tail = integrand.tail_diagnostic(endpoint)
        tolerance = mp.mpf(10) ** (-(parameters.digits - 15))
        if max(error, absolute_error,
               tail['normalized_two_sided_tail_majorant_estimate']) >= tolerance:
            raise ArithmeticError("quadrature/tail diagnostics exceed the acceptance threshold")
        before = norm * mp.fsum(v for right, v in zip(panels[1:], part_values)
                                if right <= split)
        extension = norm * mp.fsum(v for left, v in zip(panels, part_values)
                                   if left >= split)
        correction = mp.airyai(integrand.zeta) - 3 * mp.sqrt(2) * integrand.lam * mp.airyai(
            integrand.zeta, derivative=1)
        log_bound = rational(integrand.sb.log_bound)
        return {
            'parameters': parameters.__dict__,
            'Q': finite(value), 'Airy_Q1': finite(correction),
            'Q_minus_Q1': finite(value - correction),
            'scaled_remainder': finite((value - correction) / integrand.lam ** 2),
            'h': integrand.h, 'lambda': integrand.lam, 'eta': integrand.eta,
            'centered_real_arguments': tuple(mp.re(z) for z in integrand.real_arguments),
            'centered_strip_epsilon_exact': str(integrand.sb.epsilon),
            'D_terms': integrand.sb.terms,
            'D_full_log_remainder_bound_exact': str(integrand.sb.log_bound),
            'D_full_log_remainder_bound_decimal': log_bound,
            'D_propagated_error_estimate': finite(mp.expm1(log_bound) * absolute),
            'normalized_absolute_integral_estimate': absolute,
            'quadrature_internal_error_estimate': error,
            'absolute_quadrature_internal_error_estimate': absolute_error,
            'quadrature_acceptance_threshold': tolerance,
            'cutoff_comparison': {'shorter_cutoff': split, 'Q_at_shorter_cutoff': before,
                                  'extension_contribution': extension,
                                  'shorter_tail_diagnostic': integrand.tail_diagnostic(split)},
            'tail_diagnostic': tail,
            'panels': panels, 'integrand_evaluations': len(integrand.cache),
            'elapsed_seconds': perf_counter() - started,
            'evidence_status': 'uncertified_multiprecision_exact_integrand_quadrature',
        }
