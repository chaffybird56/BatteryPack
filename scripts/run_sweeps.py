from __future__ import annotations

from pathlib import Path
from datetime import datetime

import click
import numpy as np

from battery_pack.config import (
	default_cell_params,
	default_simulation_params,
	default_thermal_params,
)
from battery_pack.plots import plot_sweep_heatmap
from battery_pack.sweep import run_parameter_sweep


@click.command()
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=Path("outputs/sweeps"))
def main(out_dir: Path) -> None:
	out_dir = out_dir / datetime.now().strftime("%Y%m%d_%H%M%S")
	out_dir.mkdir(parents=True, exist_ok=True)

	cell = default_cell_params()
	sim = default_simulation_params()
	therm = default_thermal_params()

	df = run_parameter_sweep(
		series_list=[24, 32, 40, 48],
		parallel_list=[1, 2, 3, 4],
		UA_list=[4.0, 6.0, 8.0, 12.0],
		peak_current_list=[40.0, 60.0, 80.0, 100.0],
		sim=sim,
		cell=cell,
		thermal=therm,
	)

	(df).to_csv(out_dir / "sweep_results.csv", index=False)
	plot_sweep_heatmap(df, x="Ns", y="Np", value="peak_temp_k", out_dir=out_dir, title="Peak Temperature (K)")
	plot_sweep_heatmap(df, x="Ns", y="Np", value="viol_temp", out_dir=out_dir, title="Temp Violations (1=yes)", cmap="Reds")
	plot_sweep_heatmap(df, x="peak_current_a", y="UA_w_per_k", value="peak_temp_k", out_dir=out_dir, title="Peak T vs Current & UA")

	print(f"Sweep complete. Outputs saved to: {out_dir}")


if __name__ == "__main__":
	main()

