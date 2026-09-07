from __future__ import annotations

import warnings

from pythermalcomfort.environment import scale_wind_speed_log as _scale_wind_speed_log


def scale_wind_speed_log(*args, **kwargs):
    """Call the relocated wind-profile helper."""
    warnings.warn(
        "pythermalcomfort.utils.scale_wind_speed_log is deprecated; "
        "import it from pythermalcomfort.environment instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _scale_wind_speed_log(*args, **kwargs)


__all__ = ["scale_wind_speed_log"]
