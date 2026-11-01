"""Small exact arithmetic for the fixed fixtures, not a symbolic geometry engine."""

from dataclasses import dataclass
from fractions import Fraction as Q
from itertools import permutations


def rational(value):
    if type(value) is not str:
        raise ValueError("rational fixture inputs must be strings")
    return Q(value)


def require(condition, message):
    if not condition:
        raise ArithmeticError(message)


def _fraction(value):
    if type(value) not in (int, str, Q):
        raise TypeError("exact arithmetic does not accept floats")
    return Q(value)


def _scalar(value):
    return value if isinstance(value, Quadratic) else _fraction(value)


@dataclass(frozen=True, eq=False)
class Quadratic:
    """a+b*sqrt(d), only in the four fields needed by these fixtures."""

    a: Q
    b: Q
    d: int

    def __post_init__(self):
        if type(self.d) is not int or self.d not in (-3, -2, 2, 3):
            raise ValueError("supported radicands are -3,-2,2,3")
        object.__setattr__(self, "a", _fraction(self.a))
        object.__setattr__(self, "b", _fraction(self.b))

    def _coerce(self, value):
        if isinstance(value, Quadratic):
            if value.d != self.d:
                raise ValueError("cannot mix quadratic fields")
            return value
        return Quadratic(_fraction(value), Q(0), self.d)

    def __add__(self, other):
        other = self._coerce(other)
        return Quadratic(self.a+other.a, self.b+other.b, self.d)

    __radd__ = __add__

    def __neg__(self):
        return Quadratic(-self.a, -self.b, self.d)

    def __sub__(self, other):
        return self+-self._coerce(other)

    def __rsub__(self, other):
        return self._coerce(other)+-self

    def __mul__(self, other):
        other = self._coerce(other)
        return Quadratic(self.a*other.a+self.d*self.b*other.b,
                         self.a*other.b+self.b*other.a, self.d)

    __rmul__ = __mul__

    def conjugate(self):
        return Quadratic(self.a, -self.b, self.d)

    def __truediv__(self, other):
        other = self._coerce(other)
        norm = other.a**2-self.d*other.b**2
        if not norm:
            raise ZeroDivisionError("zero quadratic denominator")
        product = self*other.conjugate()
        return Quadratic(product.a/norm, product.b/norm, self.d)

    def __rtruediv__(self, other):
        return self._coerce(other)/self

    def __pow__(self, exponent):
        if type(exponent) is not int:
            raise TypeError("only integer powers are supported")
        if exponent < 0:
            return (1/self)**(-exponent)
        result = self._coerce(1)
        for _ in range(exponent):
            result *= self
        return result

    def __bool__(self):
        return bool(self.a or self.b)

    def __eq__(self, other):
        try:
            other = self._coerce(other)
        except (TypeError, ValueError):
            return False
        return self.a == other.a and self.b == other.b


def constant(value, degree=6):
    if type(degree) is not int or not 0 <= degree <= 6:
        raise ValueError("fixed series degree must be between zero and six")
    value = _scalar(value)
    return [value]+[Q(0)]*degree


def variable(degree=6):
    if degree < 1:
        raise ValueError("a variable needs degree at least one")
    result = constant(Q(0), degree)
    result[1] = Q(1)
    return result


def add(*series):
    if not series or len({len(s) for s in series}) != 1:
        raise ValueError("series must have equal lengths")
    return [sum(_scalar(value) for value in values) for values in zip(*series)]


def scale(series, scalar):
    scalar = _scalar(scalar)
    return [scalar*_scalar(value) for value in series]


def multiply(left, right):
    if len(left) != len(right):
        raise ValueError("series must have equal lengths")
    left, right = [list(map(_scalar, s)) for s in (left, right)]
    return [sum(left[k]*right[n-k] for k in range(n+1)) for n in range(len(left))]


def power(series, exponent):
    if type(exponent) is not int or exponent < 0:
        raise ValueError("series power must be a nonnegative integer")
    result = constant(Q(1), len(series)-1)
    for _ in range(exponent):
        result = multiply(result, series)
    return result


def reciprocal(series):
    series = list(map(_scalar, series))
    if not series[0]:
        raise ValueError("series reciprocal needs a nonzero constant")
    result = constant(1/series[0], len(series)-1)
    for n in range(1, len(series)):
        result[n] = -sum(series[k]*result[n-k] for k in range(1, n+1))/series[0]
    return result


def derivative(series):
    return [(n+1)*series[n+1] for n in range(len(series)-1)]


def cosh(series):
    if series[0]:
        raise ValueError("the finite cosh expansion requires zero constant")
    return add(constant(Q(1), len(series)-1), scale(power(series, 2), Q(1, 2)),
               scale(power(series, 4), Q(1, 24)), scale(power(series, 6), Q(1, 720)))


def transpose(matrix):
    if not matrix or not matrix[0] or len({len(row) for row in matrix}) != 1:
        raise ValueError("matrix must be nonempty and rectangular")
    return [[_scalar(value) for value in row] for row in zip(*matrix)]


def matmul(left, right):
    columns = transpose(right)
    left = transpose(transpose(left))
    if len(left[0]) != len(right):
        raise ValueError("matrix dimensions do not match")
    return [[sum(a*b for a, b in zip(row, col)) for col in columns] for row in left]


def matadd(left, right, sign=1):
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right)):
        raise ValueError("matrix dimensions do not match")
    sign = _scalar(sign)
    return [[_scalar(a)+sign*_scalar(b) for a, b in zip(row, other)] for row, other in zip(left, right)]


def matscale(matrix, scalar):
    return [scale(row, scalar) for row in matrix]


def eye(size):
    return [[Q(i == j) for j in range(size)] for i in range(size)]


def determinant(matrix):
    n = len(matrix)
    if not 1 <= n <= 4 or any(len(row) != n for row in matrix):
        raise ValueError("only square matrices of sizes one through four are supported")
    matrix = [[_scalar(value) for value in row] for row in matrix]
    result = Q(0)
    for p in permutations(range(n)):
        term = Q((-1)**sum(p[i] > p[j] for i in range(n) for j in range(i+1, n)))
        for i in range(n):
            term *= matrix[i][p[i]]
        result += term
    return result


def inverse(matrix):
    n = len(matrix)
    determinant(matrix)  # Shape and size validation; pivoting is independent of this value.
    work = [[x if isinstance(x, Quadratic) else _fraction(x) for x in row]+unit
            for row, unit in zip(matrix, eye(n))]
    for col in range(n):
        pivot = next((i for i in range(col, n) if work[i][col]), None)
        if pivot is None:
            raise ValueError("singular matrix")
        work[col], work[pivot] = work[pivot], work[col]
        divisor = work[col][col]
        work[col] = [x/divisor for x in work[col]]
        for row in range(n):
            if row != col:
                factor = work[row][col]
                work[row] = [x-factor*y for x, y in zip(work[row], work[col])]
    return [row[n:] for row in work]


def json_exact(value):
    if isinstance(value, Q):
        return str(value)
    if isinstance(value, Quadratic):
        return {"a": str(value.a), "b": str(value.b), "radicand": value.d}
    if isinstance(value, dict):
        return {str(key): json_exact(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_exact(item) for item in value]
    return value


class ExactChecks:
    def __init__(self):
        self.names = []

    def equal(self, name, actual, expected):
        require(actual == expected, f"exact identity failed: {name}; {actual!r} != {expected!r}")
        self.names.append(name)

    def result(self, **values):
        return {"status": "exact finite identities passed", "check_count": len(self.names),
                "zero_residual_identities": self.names, **values}
