from __future__ import annotations

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
from battery_pack.limits import compute_power_limits
from battery_pack.pack import BatteryPack
from battery_pack.plots import (
	plot_power_limits,
	plot_rte_bar,
	plot_temperature,
	plot_time_series,
)
from battery_pack.simulation import Simulator


@click.command()
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=Path("assets"))
def main(out_dir: Path) -> None:
	out_dir.mkdir(parents=True, exist_ok=True)
	cell = default_cell_params()
	packp = default_pack_params()
	therm = default_thermal_params()
	sim = default_simulation_params()
	pack = BatteryPack(cell_params=cell, pack_params=packp, thermal_params=therm, initial_soc=sim.initial_soc)
	cycle = synthetic_cycle(t_total_s=sim.t_total_s, dt_s=sim.dt_s, peak_current_a=min(80.0, packp.max_current_a))
	simulator = Simulator(pack, sim)
	res = simulator.round_trip_efficiency(cycle, initial_soc=sim.initial_soc)
	plot_time_series(res.data[res.data["phase"] == "discharge"], out_dir, title="Discharge Time Series")
	plot_temperature(res.data, out_dir, title="Pack Temperature (Both Phases)")
	plot_rte_bar(res.RTE_percent, out_dir)
	soc_grid = np.linspace(packp.min_soc, packp.max_soc, 21)
	p_dis, p_chg = [], []
	for s in soc_grid:
		limits = compute_power_limits(pack, soc=float(s))
		p_dis.append(limits.max_discharge_w)
		p_chg.append(limits.max_charge_w)
	plot_power_limits(soc_grid, np.array(p_dis), np.array(p_chg), out_dir)
	print(f"Assets generated in: {out_dir}")


if __name__ == "__main__":
	main()

