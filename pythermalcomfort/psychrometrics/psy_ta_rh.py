from __future__ import annotations

import numpy as np

from pythermalcomfort.classes_return import PsychrometricValues
from pythermalcomfort.utilities import NumericInput

from .dew_point_tmp import dew_point_tmp
from .enthalpy_air import enthalpy_air
from .p_sat import p_sat
from .wet_bulb_tmp import wet_bulb_tmp


def psy_ta_rh(
    tdb: NumericInput,
    rh: NumericInput,
    p_atm: float = 101325,
) -> PsychrometricValues:
    """Calculate psychrometric values of air based on dry bulb air temperature and
    relative humidity.

    For more accurate results we recommend the use of the Python
    package `psychrolib`_.

    .. _psychrolib: https://pypi.org/project/PsychroLib/

    Parameters
    ----------
    tdb: float or list of floats
        air temperature, [°C]
    rh: float or list of floats
        relative humidity, [%]
    p_atm: float or list of floats
        atmospheric pressure, [Pa]

    Returns
    -------
    p_vap: float or list of floats
        partial pressure of water vapor in moist air, [Pa]
    hr: float or list of floats
        humidity ratio, [kg water/kg dry air]
    wet_bulb_tmp: float or list of floats
        wet bulb temperature, [°C]
    dew_point_tmp: float or list of floats
        dew point temperature, [°C]
    h: float or list of floats
        enthalpy_air [J/kg dry air]
    """
    tdb = np.asarray(tdb, dtype=np.float64)
    rh = np.asarray(rh, dtype=np.float64)
    p_atm = np.asarray(p_atm, dtype=np.float64)

    p_saturation = p_sat(tdb)
    p_vap = rh / 100 * p_saturation
    hr = 0.62198 * p_vap / (p_atm - p_vap)
    tdp = dew_point_tmp(tdb, rh)
    twb = wet_bulb_tmp(tdb, rh)
    h = enthalpy_air(tdb, hr)

    return PsychrometricValues(
        p_sat=p_saturation,
        p_vap=p_vap,
        hr=hr,
        wet_bulb_tmp=twb,
        dew_point_tmp=tdp,
        h=h,
    )
