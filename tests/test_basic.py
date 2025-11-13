from __future__ import annotations

from battery_pack.config import (
    default_cell_params,
    default_pack_params,
    default_simulation_params,
    default_thermal_params,
)
from battery_pack.drive_cycles import synthetic_cycle
from battery_pack.pack import BatteryPack
from battery_pack.simulation import Simulator
from battery_pack.validation import check_soc_bounds, check_temperature_reasonable


def test_short_simulation_runs_and_bounds():
    cell = default_cell_params()
    packp = default_pack_params()
    therm = default_thermal_params()
    sim = default_simulation_params()
    sim.t_total_s = 60.0
    pack = BatteryPack(cell_params=cell, pack_params=packp, thermal_params=therm, initial_soc=sim.initial_soc)
    cycle = synthetic_cycle(t_total_s=sim.t_total_s, dt_s=sim.dt_s, peak_current_a=min(60.0, packp.max_current_a))
    res = Simulator(pack, sim).run(cycle)
    assert check_soc_bounds(res)
    assert check_temperature_reasonable(res)
