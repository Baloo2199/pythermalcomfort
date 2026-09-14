import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from pythermalcomfort.models import pmv_ppd_iso
from pythermalcomfort.plots.matplotlib import PsychrometricPlot, ThresholdPlotResult
from pythermalcomfort.utilities import hr_to_rh


def _new_plot() -> PsychrometricPlot:
    """Initialize a basic PsychrometricPlot."""
    return (
        PsychrometricPlot(pmv_ppd_iso)
        .set_params(vr=0.1, met=1.2, clo=0.5, tr=25.0)
        .set_regions(output="pmv", thresholds=[-0.5, 0.5])
    )


def test_import_export() -> None:
    """Test import/export from pythermalcomfort.plots.matplotlib."""
    try:
        from pythermalcomfort.plots.matplotlib import PsychrometricPlot

        assert PsychrometricPlot is not None
    except ImportError as exc:
        pytest.fail(f"Failed to import PsychrometricPlot: {exc}")


def test_set_x_axis_accepts_any_model_temperature_param() -> None:
    """tdb and tr are both valid x-axis parameters; unknown params are rejected."""
    # tdb is always accepted
    plot = _new_plot()
    plot.set_x_axis("tdb", 10.0, 40.0, resolution=1.0)

    # tr is also a valid model parameter when it is not already in fixed params
    plot_tr = PsychrometricPlot(pmv_ppd_iso).set_params(vr=0.1, met=1.2, clo=0.5)
    plot_tr.set_x_axis("tr", 10.0, 40.0, resolution=1.0)

    with pytest.raises(ValueError):
        plot.set_x_axis("not_a_model_param", 10.0, 40.0, resolution=1.0)


def test_set_y_axis_only_accepts_hr() -> None:
    """Test set_y_axis strictly enforces 'hr'."""
    plot = _new_plot()
    with pytest.raises(ValueError, match="requires the y-axis to be 'hr'"):
        plot.set_y_axis("rh", 0.0, 30.0, resolution=1.0)

    # Valid input should not raise
    plot.set_y_axis("hr", 0.0, 30.0, resolution=1.0)


def test_set_y_axis_warns_on_kg_per_kg_range() -> None:
    """A pre-4.5.0 kg/kg range warns rather than silently rendering a blank chart.

    It warns rather than raises because humidity ratios below 1 g/kg are
    physically real in cold air, which this package supports.
    """
    plot = _new_plot()
    with pytest.warns(UserWarning, match="g/kg dry air rather than kg/kg"):
        plot.set_y_axis("hr", 0.0, 0.03, resolution=0.002)


def test_set_y_axis_accepts_cold_climate_range() -> None:
    """A sub-1 g/kg range is accepted; at -20 degC, 0.5 g/kg is about 80 % RH."""
    plot = _new_plot()
    plot.set_y_axis("hr", 0.0, 0.5, resolution=0.05)
    assert plot._y_axis.max_val == 0.5


def test_basic_plot_renders_and_preserves_limits() -> None:
    """Test a basic plot renders, masks invalid RH, and preserves requested axis limits."""
    plot = _new_plot()
    plot.set_x_axis("tdb", 10.0, 40.0, resolution=1.0)
    plot.set_y_axis("hr", 0.0, 30.0, resolution=2.0)

    result = plot.plot()

    # Verify the return object
    assert isinstance(result, ThresholdPlotResult)
    assert result.fig is not None
    assert result.ax is not None

    # Verify requested axis limits are preserved perfectly
    xlim = result.ax.get_xlim()
    ylim = result.ax.get_ylim()
    assert xlim == (10.0, 40.0)
    assert ylim == (0.0, 30.0)

    plt.close(result.fig)


def test_y_axis_has_default_humidity_ratio_label() -> None:
    """The chart labels its own y-axis instead of falling back to the bare 'hr'."""
    plot = _new_plot()
    plot.set_x_axis("tdb", 10.0, 40.0, resolution=1.0)
    plot.set_y_axis("hr", 0.0, 30.0, resolution=2.0)

    result = plot.plot()

    ylabel = result.ax.get_ylabel()
    assert ylabel != "hr"
    assert "Humidity ratio" in ylabel
    # The units have to be stated, and stated as g/kg dry air: the whole point
    # of #338 was that callers disagreed about them.
    assert "g" in ylabel
    assert "kg" in ylabel
    assert "dry" in ylabel
    assert "kg/kg" not in ylabel.replace(" ", "")

    plt.close(result.fig)


def test_grid_is_evaluated_as_g_per_kg() -> None:
    """A y value of 10 must reach the model as 10 g/kg, i.e. 0.010 kg/kg.

    This pins the conversion itself rather than inspecting rendered artists.
    An earlier version of this test scanned ``ax.collections``, which includes
    the white saturation mask; that mask is drawn up to the axis maximum
    whatever the units, so its assertion held even when the conversion was
    wrong.
    """
    plot = _new_plot()
    plot.set_x_axis("tdb", 20.0, 30.0, resolution=5.0)
    plot.set_y_axis("hr", 0.0, 20.0, resolution=10.0)

    tdb = np.array([[25.0]])
    hr_g_kg = np.array([[10.0]])
    actual = plot._evaluate_grid_output(x=tdb, y=hr_g_kg, output_name="pmv")

    expected_rh = hr_to_rh(10.0 / 1000.0, 25.0)
    expected = pmv_ppd_iso(
        tdb=25.0, tr=25.0, vr=0.1, rh=float(expected_rh), met=1.2, clo=0.5
    ).pmv

    assert float(actual[0, 0]) == pytest.approx(float(expected), abs=1e-9)
