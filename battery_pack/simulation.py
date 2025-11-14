from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd

from .config import SimulationParams
from .drive_cycles import DriveCycle
from .pack import BatteryPack


@dataclass
class SimulationResult:
    data: pd.DataFrame
    RTE_percent: float
    energy_out_wh: float
    energy_in_wh: float


class Simulator:
    def __init__(self, pack: BatteryPack, sim_params: SimulationParams):
        self.pack = pack
        self.sim = sim_params

    def run(self, cycle: DriveCycle) -> pd.DataFrame:
        rows = []
        prev_t = float(cycle.time_s[0])
        for t, I in zip(cycle.time_s, cycle.current_a):
            dt = max(1e-9, float(t - prev_t))
            prev_t = float(t)
            row = self.pack.step(float(I), float(dt))
            row["time_s"] = float(t)
            rows.append(row)
        return pd.DataFrame(rows)

    def round_trip_efficiency(self, cycle: DriveCycle, initial_soc: float) -> SimulationResult:
        # Discharge on provided cycle from initial_soc
        self.pack.reset(initial_soc=initial_soc)
        df_dis = self.run(cycle)
        # Energy out positive when discharging
        energy_out_wh = float(np.trapz(np.maximum(df_dis["power_w"].to_numpy(), 0.0), df_dis["time_s"]) / 3600.0)

        # Charge with mirrored profile until SOC returns to initial
        self.pack.reset(initial_soc=df_dis["soc"].iloc[-1])
        neg_cycle = DriveCycle(time_s=cycle.time_s, current_a=-cycle.current_a)
        df_chg = self.run(neg_cycle)
        # Stop when SOC reaches initial
        mask = df_chg["soc"] <= initial_soc + 1e-6
        if mask.any():
            last_idx = int(np.argmax(mask.to_numpy()))
            df_chg = df_chg.iloc[: last_idx + 1]

        energy_in_wh = float(np.trapz(np.maximum(-df_chg["power_w"].to_numpy(), 0.0), df_chg["time_s"]) / 3600.0)
        RTE = 100.0 * (energy_out_wh / energy_in_wh) if energy_in_wh > 1e-9 else 0.0

        df_dis["phase"] = "discharge"
        df_chg["phase"] = "charge"
        data = pd.concat([df_dis, df_chg], ignore_index=True)
        return SimulationResult(
            data=data, RTE_percent=float(RTE), energy_out_wh=energy_out_wh, energy_in_wh=energy_in_wh
        )
