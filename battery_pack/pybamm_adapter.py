from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np


@dataclass
class PyBaMMOCV:
    soc: np.ndarray
    ocv_v: np.ndarray


def try_generate_ocv_curve() -> Optional[PyBaMMOCV]:
    """Attempt to create an OCV(SOC) curve using PyBaMM if available.

    Returns None if PyBaMM is not installed.
    """
    try:
        import pybamm  # type: ignore

        chem = pybamm.parameter_sets.Marquis2019
        model = pybamm.lithium_ion.SPM()
        param = pybamm.ParameterValues(chem)
        param.update({"Current function": 0.0})
        soc = np.linspace(0.0, 1.0, 101)
        ocv = []
        for s in soc:
            param.update({"Initial SoC": float(s)})
            # Evaluate open-circuit full-cell voltage via electrode OCV difference
            U_p = float(
                param["Positive electrode OCP entropic change [V/K]"] * 0.0 + param["Positive electrode OCP [V]"]
            )
            U_n = float(
                param["Negative electrode OCP entropic change [V/K]"] * 0.0 + param["Negative electrode OCP [V]"]
            )
            ocv.append(U_p - U_n)
        return PyBaMMOCV(soc=soc.astype(float), ocv_v=np.array(ocv, dtype=float))
    except Exception:
        return None


class OCVLookup:
    def __init__(self, soc: np.ndarray, ocv_v: np.ndarray):
        self.soc = np.clip(soc, 0.0, 1.0)
        self.ocv_v = ocv_v

    def __call__(self, s: float) -> float:
        return float(np.interp(np.clip(s, 0.0, 1.0), self.soc, self.ocv_v))
