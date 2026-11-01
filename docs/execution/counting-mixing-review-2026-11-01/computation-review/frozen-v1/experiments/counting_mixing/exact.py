"""Small exact arithmetic helpers, with explicit input and check accounting."""

from collections import defaultdict
from fractions import Fraction as Q
from math import gcd


def rational(value):
    if isinstance(value, Q):
        return value
    if type(value) not in (str, int):
        raise ValueError("exact inputs must be rational strings or integers")
    try:
        return Q(value)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError("invalid finite rational input") from exc


def integer(value, minimum=0, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"integer required in [{minimum}, {maximum}]")
    return value


def positive(value):
    value = rational(value)
    if value <= 0:
        raise ValueError("positive rational required")
    return value


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Checks:
    def __init__(self, scope):
        self.scope, self.count = scope, 0

    def equal(self, actual, expected, description):
        self.count += 1
        require(actual == expected, f"{self.scope}: {description}: {actual!r} != {expected!r}")

    def true(self, condition, description):
        self.count += 1
        require(condition, f"{self.scope}: {description}")

    def result(self, **values):
        return {"status": "exact finite checks passed", "check_count": self.count, **values}


ZERO = (0, 0, 0)
ONE = {ZERO: Q(1)}
X = {(1, 0, 0): Q(1)}
Y = {(0, 1, 0): Q(1)}
Z = {(0, 0, 1): Q(1)}


def clean(poly):
    return {power: value for power, value in poly.items() if value}


def add(*polys):
    result = defaultdict(Q)
    for poly in polys:
        for power, value in poly.items():
            result[power] += value
    return clean(result)


def scale(poly, scalar):
    scalar = rational(scalar)
    return clean({power: scalar*value for power, value in poly.items()})


def mul(left, right):
    result = defaultdict(Q)
    for a, av in left.items():
        for b, bv in right.items():
            result[tuple(x+y for x, y in zip(a, b))] += av*bv
    return clean(result)


def power(poly, exponent):
    exponent = integer(exponent)
    result = ONE
    for _ in range(exponent):
        result = mul(result, poly)
    return result


def chebyshev(poly, maximum):
    integer(maximum, 1, 30)
    result = [scale(ONE, 2), poly]
    for _ in range(1, maximum):
        result.append(add(mul(poly, result[-1]), scale(result[-2], -1)))
    return result


def identify_cuffs(poly):
    result = defaultdict(Q)
    for (a, b, c), coefficient in poly.items():
        result[(a+b, 0, c)] += coefficient
    return clean(result)


def polynomial_records(poly):
    return [{"powers_xyz": list(p), "coefficient": c} for p, c in sorted(poly.items())]


def matrix(values):
    if (not isinstance(values, (list, tuple)) or len(values) != 2
            or any(not isinstance(row, (list, tuple)) or len(row) != 2 for row in values)):
        raise ValueError("a 2 by 2 rational matrix is required")
    result = tuple(tuple(rational(v) for v in row) for row in values)
    if determinant(result) != 1:
        raise ValueError("matrix determinant must equal one exactly")
    return result


def determinant(a):
    return a[0][0]*a[1][1]-a[0][1]*a[1][0]


IDENTITY = ((Q(1), Q(0)), (Q(0), Q(1)))


def mmul(a, b):
    return tuple(tuple(sum(a[i][k]*b[k][j] for k in range(2)) for j in range(2))
                 for i in range(2))


def mpower(a, exponent):
    integer(exponent)
    result = IDENTITY
    for _ in range(exponent):
        result = mmul(result, a)
    return result


def inverse(a):
    if determinant(a) != 1:
        raise ValueError("inverse helper requires determinant one")
    return ((a[1][1], -a[0][1]), (-a[1][0], a[0][0]))


def trace(a):
    return a[0][0]+a[1][1]


def word(*matrices):
    result = IDENTITY
    for a in matrices:
        result = mmul(result, a)
    return result


def divisors(n):
    integer(n, 1)
    return [d for d in range(1, n+1) if n % d == 0]


def mobius(n):
    integer(n, 1)
    answer, p = 1, 2
    while p*p <= n:
        if n % p == 0:
            n //= p
            answer = -answer
            if n % p == 0:
                return 0
        p += 1
    return -answer if n > 1 else answer


def phi(n):
    integer(n, 1)
    return sum(gcd(k, n) == 1 for k in range(1, n+1))


def floor(value):
    value = rational(value)
    return value.numerator // value.denominator


def ceil(value):
    return -floor(-rational(value))


def json_exact(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, dict):
        return {str(k): json_exact(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_exact(v) for v in value]
    return value
