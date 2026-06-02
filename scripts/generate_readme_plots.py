from __future__ import annotations

from pathlib import Path

import click
import numpy as np

from battery_pack.config import (
    CHEMISTRY_PRESETS,
    cell_params_for_chemistry,
    default_pack_params,
    default_simulation_params,
    default_thermal_params,
)
from battery_pack.drive_cycles import synthetic_cycle
from battery_pack.limits import compute_power_limits
from battery_pack.pack import BatteryPack
from battery_pack.plots import (
    plot_chemistry_rte,
    plot_load_profile,
    plot_power_limits,
    plot_rte_bar,
    plot_safety_hazard,
    plot_temperature,
    plot_time_series,
)
from battery_pack.safety import SafetyAnalyzer, SafetyLimits, ThermalRunawayParams
from battery_pack.simulation import Simulator


@click.command()
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=Path("assets"))
def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    packp = default_pack_params()
    therm = default_thermal_params()
    sim = default_simulation_params()
    sim.t_total_s = 600.0

    cell = cell_params_for_chemistry("NMC811")
    pack = BatteryPack(cell_params=cell, pack_params=packp, thermal_params=therm, initial_soc=sim.initial_soc)
    cycle = synthetic_cycle(t_total_s=sim.t_total_s, dt_s=sim.dt_s, peak_current_a=min(80.0, packp.max_current_a))
    simulator = Simulator(pack, sim)
    res = simulator.round_trip_efficiency(cycle, initial_soc=sim.initial_soc)

    plot_time_series(
        res.data[res.data["phase"] == "discharge"], out_dir, title="Voltage, current, power, SoC (discharge)"
    )
    plot_temperature(res.data, out_dir, title="Pack temperature — charge / discharge")
    plot_rte_bar(res.RTE_percent, out_dir, title="Round-trip energy efficiency")
    plot_load_profile(cycle.time_s, cycle.current_a, out_dir, title="Configurable charge & load profile")

    soc_grid = np.linspace(packp.min_soc, packp.max_soc, 21)
    p_dis, p_chg = [], []
    for s in soc_grid:
        limits = compute_power_limits(pack, soc=float(s))
        p_dis.append(limits.max_discharge_w)
        p_chg.append(limits.max_charge_w)
    plot_power_limits(soc_grid, np.array(p_dis), np.array(p_chg), out_dir)

    labels, rtes = [], []
    for name in ("LFP", "NMC811", "NCA", "LCO"):
        c = cell_params_for_chemistry(name)
        p = BatteryPack(cell_params=c, pack_params=packp, thermal_params=therm, initial_soc=sim.initial_soc)
        short = default_simulation_params()
        short.t_total_s = 300.0
        cy = synthetic_cycle(t_total_s=short.t_total_s, dt_s=short.dt_s, peak_current_a=min(60.0, packp.max_current_a))
        rte = Simulator(p, short).round_trip_efficiency(cy, initial_soc=short.initial_soc).RTE_percent
        labels.append(name)
        rtes.append(rte)
    plot_chemistry_rte(labels, rtes, out_dir)

    runaway = ThermalRunawayParams()
    analyzer = SafetyAnalyzer(runaway, SafetyLimits())
    temps_c = np.linspace(25, 160, 50)
    hazard = []
    for t_c in temps_c:
        r = analyzer.analyze_operating_conditions(
            voltage_v=140.0,
            current_a=80.0,
            temperature_k=t_c + 273.15,
            soc=0.6,
            cell_count=packp.series_cells,
        )
        hazard.append(r.hazard_index)
    plot_safety_hazard(temps_c, np.array(hazard), runaway.T_trigger_k - 273.15, out_dir)

    print(f"Assets generated in: {out_dir}")
    print(f"  Chemistries compared: {list(CHEMISTRY_PRESETS.keys())}")


if __name__ == "__main__":
    main()
