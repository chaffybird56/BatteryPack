from __future__ import annotations

from dataclasses import dataclass

from .config import ThermalParams


@dataclass
class LumpedThermal:
    params: ThermalParams

    def step(self, T_k: float, heat_w: float, dt_s: float) -> float:
        m = self.params.mass_kg
        Cp = self.params.Cp_j_per_kgk
        UA = self.params.UA_w_per_k
        T_amb = self.params.T_ambient_k
        dTdt = (heat_w - UA * (T_k - T_amb)) / max(1e-9, m * Cp)
        return float(T_k + dt_s * dTdt)
