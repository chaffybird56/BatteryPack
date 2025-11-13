from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click
import numpy as np

from battery_pack.config import (
    default_cell_params,
    default_pack_params,
    default_simulation_params,
    default_thermal_params,
)
from battery_pack.drive_cycles import synthetic_cycle
from battery_pack.pack_advanced import AdvancedPackParams, BatteryPackAdvanced
from battery_pack.plots import plot_temperature, plot_time_series
from battery_pack.simulation import Simulator


@click.command()
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=Path("outputs/advanced_demo"))
@click.option("--thermal-mode", type=click.Choice(["air", "fin", "pcm", "liquid"]), default="fin")
@click.option("--use-pybamm-ocv/--no-pybamm-ocv", default=False)
def main(out_dir: Path, thermal_mode: str, use_pybamm_ocv: bool) -> None:
    out_dir = out_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)

    cell = default_cell_params()
    packp = default_pack_params()
    therm = default_thermal_params()
    sim = default_simulation_params()

    adv = AdvancedPackParams(thermal_mode=thermal_mode, use_pybamm_ocv=use_pybamm_ocv)
    pack = BatteryPackAdvanced(
        cell_base=cell, pack_params=packp, thermal_params=therm, adv=adv, initial_soc=sim.initial_soc
    )
    cycle = synthetic_cycle(t_total_s=sim.t_total_s, dt_s=sim.dt_s, peak_current_a=min(80.0, packp.max_current_a))

    class AdvancedSimulator:
        def __init__(self, pack: BatteryPackAdvanced, dt_s: float):
            self.pack = pack
            self.dt = dt_s

        def run(self, t: np.ndarray, I: np.ndarray):
            rows = []
            prev_t = float(t[0])
            for ti, Ii in zip(t, I):
                dt = max(1e-9, float(ti - prev_t))
                prev_t = float(ti)
                row = self.pack.step(float(Ii), dt)
                row["time_s"] = float(ti)
                rows.append(row)
            import pandas as pd

            return pd.DataFrame(rows)

    sim_adv = AdvancedSimulator(pack, sim.dt_s)
    df = sim_adv.run(cycle.time_s, cycle.current_a)
    plot_time_series(df, out_dir, title="Advanced Pack Time Series (mean)")
    plot_temperature(df.rename(columns={"temp_k": "temp_k"}), out_dir, title="Advanced Pack Temperature (mean)")
    print(f"Advanced demo complete. Outputs saved to: {out_dir}")


if __name__ == "__main__":
    main()
