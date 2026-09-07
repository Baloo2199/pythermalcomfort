import importlib

import numpy as np
import pytest

import pythermalcomfort.utilities as utilities
from pythermalcomfort.utilities import Units, body_surface_area, units_converter


def test_ip_units_converter() -> None:
    """Test the units converter for IP and SI units."""
    assert (units_converter(tdb=77, tr=77, v=3.2, from_units=Units.IP.value)) == [
        25.0,
        25.0,
        0.975312404754648,
    ]
    assert (units_converter(pressure=1, area=1 / 0.09, from_units=Units.IP.value)) == [
        101325,
        1.0322474090590033,
    ]

    expected_result = [25.0, 3.047]
    assert np.allclose(
        units_converter(Units.IP.value, tdb=77, v=10),
        expected_result,
        atol=0.01,
    )

    # Test case 2: Conversion from SI to IP for temperature and velocity
    expected_result = [68, 6.562]
    assert np.allclose(
        units_converter(Units.SI.value, tdb=20, v=2),
        expected_result,
        atol=0.01,
    )

    # Test case 3: Conversion from IP to SI for area and pressure
    expected_result = [9.29, 1489477.5]
    assert np.allclose(
        units_converter(Units.IP.value, area=100, pressure=14.7),
        expected_result,
        atol=0.01,
    )

    # Test case 4: Conversion from SI to IP for area and pressure
    expected_result = [538.199, 1]
    assert np.allclose(
        units_converter(Units.SI.value, area=50, pressure=101325),
        expected_result,
        atol=0.01,
    )


def test_body_surface_area() -> None:
    """Test the body surface area calculations with various formulas."""
    assert body_surface_area(weight=80, height=1.8) == pytest.approx(1.9917, rel=1e-2)
    assert body_surface_area(70, 1.8, "dubois") == pytest.approx(1.88, rel=1e-2)
    assert body_surface_area(75, 1.75, "takahira") == pytest.approx(1.91, rel=1e-2)
    assert body_surface_area(80, 1.7, "fujimoto") == pytest.approx(1.872, rel=1e-2)
    assert body_surface_area(85, 1.65, "kurazumi") == pytest.approx(1.89, rel=1e-2)
    with pytest.raises(ValueError):
        body_surface_area(70, 1.8, "invalid_formula")


MOVED_PUBLIC_FUNCTIONS = [
    ("mean_radiant_tmp", "environment"),
    ("operative_tmp", "environment"),
    ("running_mean_outdoor_temperature", "environment"),
    ("transpose_sharp_altitude", "environment"),
    ("f_svv", "environment"),
    ("v_relative", "environment"),
    ("p_sat", "psychrometrics"),
    ("p_sat_torr", "psychrometrics"),
    ("antoine", "psychrometrics"),
    ("psy_ta_rh", "psychrometrics"),
    ("hr_to_rh", "psychrometrics"),
    ("wet_bulb_tmp", "psychrometrics"),
    ("dew_point_tmp", "psychrometrics"),
    ("enthalpy_air", "psychrometrics"),
    ("clo_dynamic_ashrae", "clothing"),
    ("clo_dynamic_iso", "clothing"),
    ("clo_intrinsic_insulation_ensemble", "clothing"),
    ("clo_area_factor", "clothing"),
    ("clo_insulation_air_layer", "clothing"),
    ("clo_total_insulation", "clothing"),
    ("clo_correction_factor_environment", "clothing"),
]


@pytest.mark.parametrize(("function_name", "new_module"), MOVED_PUBLIC_FUNCTIONS)
def test_moved_public_utility_shims(
    function_name: str, new_module: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every old public utility forwards to its new package and warns."""
    expected = object()
    module = importlib.import_module(f"pythermalcomfort.{new_module}")
    monkeypatch.setattr(module, function_name, lambda *args, **kwargs: expected)

    with pytest.warns(DeprecationWarning, match=f"pythermalcomfort.{new_module}"):
        result = getattr(utilities, function_name)("argument", keyword="value")

    assert result is expected


def test_internal_helpers_have_no_utility_shims() -> None:
    """Private implementation helpers are available only from _internal."""
    assert not hasattr(utilities, "validate_type")
    assert not hasattr(utilities, "_check_ashrae55_compliance")
    assert not hasattr(utilities, "adaptive_cooling_effect")
