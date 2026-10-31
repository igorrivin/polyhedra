"""Independent numerical references and precision-contract regressions for H3."""

from decimal import Decimal
from fractions import Fraction

import mpmath as mp
import numpy as np
import pytest

from ideal_poly_volume_toolkit.geometry import (
    bloch_wigner,
    bloch_wigner_mp,
    bloch_wigner_mpmath,
    ideal_poly_volume_from_sphere,
    ideal_poly_volume_via_delaunay,
    ideal_poly_volume_via_hull_project_back,
    lob_exact,
    lobachevsky_mp,
    triangle_volume_from_points,
    triangle_volume_from_points_mp,
)


def test_decimal_angle_preserves_precision_and_matches_independent_quadrature():
    decimal = "0.123456789012345678901234567890123456789"
    with mp.workdps(130):
        angle = mp.mpf(decimal)
        reference = mp.quad(lambda t: -mp.log(2 * mp.sin(t)), [0, angle])
    with mp.workdps(23):
        value = lobachevsky_mp(decimal, dps=105)
        existing_mp = lobachevsky_mp(angle, dps=105)
        legacy = lob_exact(angle, dps=105)
        assert mp.mp.dps == 23
        assert isinstance(value, mp.mpf)
    with mp.workdps(130):
        assert abs(value - reference) < mp.mpf("1e-100")
        assert abs(existing_mp - reference) < mp.mpf("1e-100")
        assert legacy == existing_mp


def test_nonzero_angle_below_binary64_range_remains_nonzero():
    value = lobachevsky_mp("1e-400", dps=110)
    with mp.workdps(130):
        theta = mp.mpf("1e-400")
        # Integrating -log(2 sin theta) gives this leading term; the next
        # correction is theta**3/18, far below the requested relative error.
        reference = theta * (1 - mp.log(2 * theta))
        assert value > 0
        assert abs(value / reference - 1) < mp.mpf("1e-105")


def test_legacy_real_scalar_forms_preserve_their_actual_precision():
    decimal = Decimal("0.123456789012345678901234567890123456789")
    rational = Fraction(1, 3)
    binary32 = np.float32("0.3")
    integer64 = np.int64(1)
    extended = np.longdouble("0.123456789012345678901234567890123456789")
    with mp.workdps(130):
        def binary_value(value):
            numerator, denominator = value.as_integer_ratio()
            return mp.mpf(numerator) / denominator

        cases = (
            (decimal, mp.mpf(str(decimal))),
            (rational, mp.mpf(1) / 3),
            (binary32, binary_value(binary32)),
            (integer64, mp.mpf(1)),
            (extended, binary_value(extended)),
        )
        references = [mp.quad(lambda t: -mp.log(2 * mp.sin(t)), [0, angle]) for _, angle in cases]
    with mp.workdps(23):
        values = [lob_exact(value, dps=110) for value, _ in cases]
        assert mp.mp.dps == 23
    with mp.workdps(130):
        for value, reference in zip(values, references):
            assert abs(value - reference) < mp.mpf("1e-105")
        tiny = lob_exact(Fraction(1, 10**400), dps=110)
        theta = mp.mpf(1) / 10**400
        assert tiny > 0
        assert abs(tiny / (theta * (1 - mp.log(2 * theta))) - 1) < mp.mpf("1e-105")


def test_decimal_rational_and_numpy_complex_coordinate_components():
    with mp.workdps(130):
        shift = Decimal("1e50")
        vertices = ((shift, Fraction(0)), (10**50 + 1, np.int64(0)), (shift, Fraction(1)))
        value = triangle_volume_from_points_mp(*vertices, dps=110)
        assert abs(value - mp.catalan) < mp.mpf("1e-100")
        binary_point = np.complex64(0.3 + 0.7j)
        real = mp.mpf(float(binary_point.real))
        imag = mp.mpf(float(binary_point.imag))
        reference = bloch_wigner_mp(mp.mpc(real, imag), dps=110)
        assert bloch_wigner_mp(binary_point, dps=110) == reference
        assert bloch_wigner_mp(Fraction(1, 3), dps=80) == 0
        assert bloch_wigner_mp(Decimal("0.2"), dps=80) == 0


@pytest.mark.parametrize("point", [0, 1, -3, 2, "0", "1"])
def test_real_axis_and_removable_bloch_wigner_values(point):
    high_precision = bloch_wigner_mp(point, dps=80)
    compatibility = bloch_wigner_mpmath(point, dps=80)
    assert isinstance(high_precision, mp.mpf)
    assert high_precision == 0
    assert isinstance(compatibility, float)
    assert compatibility == 0.0


def test_bloch_wigner_matches_angle_integrals_and_sixfold_symmetries():
    with mp.workdps(130):
        z = mp.mpc("0.234567890123456789", "0.876543210987654321")
        alpha, beta = mp.arg(z), -mp.arg(1 - z)
        gamma = mp.pi - alpha - beta
        reference = mp.fsum(
            mp.quad(lambda t: -mp.log(2 * mp.sin(t)), [0, angle])
            for angle in (alpha, beta, gamma)
        )
        positive_shapes = (z, 1 / (1 - z), (z - 1) / z)
        negative_shapes = (1 - z, 1 / z, z / (z - 1), z.conjugate())
        for shape in positive_shapes:
            assert abs(bloch_wigner_mp(shape, dps=110) - reference) < mp.mpf("1e-105")
        for shape in negative_shapes:
            assert abs(bloch_wigner_mp(shape, dps=110) + reference) < mp.mpf("1e-105")


def test_bloch_wigner_resolves_degenerations_near_zero_one_and_infinity():
    with mp.workdps(130):
        epsilon = mp.mpf("1e-400")
        small = mp.mpc(epsilon, epsilon)
        # D(z) = Im(z) * (1-log|z|) + O(|z|**2 * |log|z||) near zero.
        cases = [
            (small, epsilon * (1 - mp.log(abs(small)))),
            (mp.mpc(1, epsilon), epsilon * (1 - mp.log(epsilon))),
        ]
        large = mp.mpc(1 / epsilon, 1 / epsilon)
        inverse = 1 / large
        cases.append((large, -inverse.imag * (1 - mp.log(abs(inverse)))))
        for shape, reference in cases:
            value = bloch_wigner_mp(shape, dps=115)
            assert value > 0
            assert abs(value / reference - 1) < mp.mpf("1e-108")


@pytest.mark.parametrize("real", ["-0.125", "-0.8", "-1", "-1.25", "-2"])
@pytest.mark.parametrize("imaginary_magnitude", ["1e-150", "1e-300"])
def test_mp_near_negative_real_axis_against_unreduced_high_precision_definition(
    real, imaginary_magnitude
):
    for imaginary in (imaginary_magnitude, "-" + imaginary_magnitude):
        with mp.workdps(450):
            z = mp.mpc(real, imaginary)
            # An independent direct-definition oracle at enough precision to
            # resolve the small imaginary part without the implementation's
            # argument maps. The first-order real-axis derivative cross-checks
            # that oracle; the omitted relative term is O(imaginary**2).
            reference = mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z))
            coefficient = -mp.log(1 - z.real) / z.real - mp.log(abs(z.real)) / (1 - z.real)
            leading_term = z.imag * coefficient
            assert abs(reference / leading_term - 1) < mp.mpf("1e-140")
        value = bloch_wigner_mp((real, imaginary), dps=120)
        triangle = triangle_volume_from_points_mp((real, imaginary), 1, 0, dps=120)
        compatibility = bloch_wigner_mpmath((real, imaginary), dps=120)
        with mp.workdps(140):
            assert value * reference > 0
            assert abs(value / reference - 1) < mp.mpf("1e-110")
            assert abs(triangle / abs(reference) - 1) < mp.mpf("1e-110")
        assert compatibility == pytest.approx(float(reference), rel=3e-15, abs=0)


def test_mp_subnormal_height_and_near_one_reduction_order():
    smallest = np.nextafter(0.0, 1.0)
    points = [
        complex(-1, smallest), complex(-1, -smallest),
        complex(np.nextafter(1.0, np.inf), 1e-300),
        complex(np.nextafter(1.0, np.inf), -1e-300),
    ]
    for point in points:
        with mp.workdps(450):
            z = mp.mpc(point)
            reference = mp.im(mp.polylog(2, z)) + mp.arg(1 - z) * mp.log(abs(z))
        value = bloch_wigner_mp(point, dps=120)
        with mp.workdps(140):
            assert value * reference > 0
            assert abs(value / reference - 1) < mp.mpf("1e-112")


def test_binary64_bloch_wigner_is_stable_for_extreme_finite_arguments():
    positive = np.array([
        complex(1e-300, 1e-300),
        complex(1e-18, 1e-18),
        complex(1, 1e-300),
        complex(np.nextafter(1.0, 0.0), 1e-300),
        complex(1e300, 1e300),
        complex(1e308, 1e308),
        complex(np.finfo(float).max, np.finfo(float).max),
    ])
    points = np.concatenate((positive, positive.conjugate(), [0j, 1 + 0j, -1e308 + 0j, 1e308 + 0j]))
    reference = np.array([float(bloch_wigner_mp(z, dps=100)) for z in points])
    # Overflow, invalid products and division by zero must not be hidden in
    # an otherwise finite small volume. Subnormal reciprocals are intentional.
    with np.errstate(over="raise", invalid="raise", divide="raise"):
        batch = bloch_wigner(points)
        scalar = np.array([bloch_wigner(z) for z in points])
    np.testing.assert_allclose(batch, reference, rtol=4e-15, atol=0)
    np.testing.assert_array_equal(batch, scalar)
    assert np.all(batch[:len(positive)] > 0)


@pytest.mark.parametrize("point", [complex(np.nan), complex(np.inf), complex(0, np.inf)])
def test_binary64_bloch_wigner_rejects_nonfinite_values(point):
    with pytest.raises(ValueError, match="finite"):
        bloch_wigner(point)
    with pytest.raises(ValueError, match="finite"):
        bloch_wigner([0.3 + 0.7j, point])


def test_mp_triangle_preserves_translated_decimal_geometry():
    # At binary64 the three real coordinates below would collapse to one.
    shift = 10**50
    vertices = ((str(shift), "0"), (str(shift + 1), "0"), (str(shift), "1"))
    with mp.workdps(21):
        value = triangle_volume_from_points_mp(*vertices, dps=110)
        assert mp.mp.dps == 21
        assert isinstance(value, mp.mpf)
    with mp.workdps(130):
        assert abs(value - mp.catalan) < mp.mpf("1e-100")


def test_mp_triangle_flat_limit_and_duplicate_rejection():
    assert triangle_volume_from_points_mp(0, 1, 2, dps=80) == 0
    for vertices in ((0, 0, 1), (0, 1, 0), (0, 1, 1)):
        with pytest.raises(ValueError, match="distinct"):
            triangle_volume_from_points_mp(*vertices, dps=80)


def test_precision_is_restored_after_success_and_exceptions(monkeypatch):
    with mp.workdps(27):
        for function in (lobachevsky_mp, lob_exact):
            function("0.2", dps=80)
            assert mp.mp.dps == 27
            with pytest.raises(ValueError):
                function("not-a-number", dps=80)
            assert mp.mp.dps == 27
        with pytest.raises(ValueError, match="finite"):
            bloch_wigner_mp(("nan", "0.2"), dps=80)
        assert mp.mp.dps == 27
        with pytest.raises(ValueError, match="distinct"):
            triangle_volume_from_points_mp(0, 1, 1, dps=80)
        assert mp.mp.dps == 27

        def failed_polylog(*args):
            raise RuntimeError("simulated special-function failure")

        monkeypatch.setattr(mp, "polylog", failed_polylog)
        with pytest.raises(RuntimeError, match="special-function failure"):
            bloch_wigner_mp(("0.2", "0.7"), dps=80)
        assert mp.mp.dps == 27


@pytest.mark.parametrize("digits", [True, 0, -5, 12.5])
def test_invalid_precision_is_rejected_without_changing_context(digits):
    before = mp.mp.dps
    for function in (lobachevsky_mp, bloch_wigner_mp):
        with pytest.raises(ValueError, match="positive integer"):
            function("0.2", dps=digits)
    assert mp.mp.dps == before


@pytest.mark.parametrize("value", ["inf", "-inf", "nan"])
def test_nonfinite_mp_input_is_rejected(value):
    with pytest.raises(ValueError, match="finite"):
        lobachevsky_mp(value, dps=80)
    with pytest.raises(ValueError, match="finite"):
        bloch_wigner_mp((value, "0.2"), dps=80)
    with pytest.raises(ValueError, match="finite"):
        triangle_volume_from_points_mp(0, 1, ("0.2", value), dps=80)


def test_high_level_mpmath_and_legacy_aliases_keep_float_returns():
    shape = np.exp(1j * np.pi / 3)
    finite = np.array([0j, 1 + 0j, shape])
    extended = np.array([complex(np.inf), *finite])
    sphere = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]]) / np.sqrt(3)
    with mp.workdps(100):
        reference = float(mp.clsin(2, mp.pi / 3))
    with mp.workdps(19):
        results = []
        for mode in ("mpmath", "exact", "eval_only"):
            results.append([
                triangle_volume_from_points(*finite, mode=mode, dps=80),
                ideal_poly_volume_via_delaunay(finite, mode=mode, dps=80),
                ideal_poly_volume_via_hull_project_back(extended, mode=mode, dps=80),
                ideal_poly_volume_from_sphere(sphere, mode=mode, dps=80),
            ])
        assert mp.mp.dps == 19
        for row in results:
            assert all(isinstance(value, float) for value in row)
            np.testing.assert_allclose(row, reference, rtol=0, atol=2e-15)
        assert results[0] == results[1] == results[2]

