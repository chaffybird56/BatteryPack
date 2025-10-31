from __future__ import annotations

import numpy as np

from battery_pack.config import default_cell_params, default_pack_params, default_simulation_params, default_thermal_params
from battery_pack.pack_advanced import AdvancedPackParams, BatteryPackAdvanced


def test_advanced_pack_runs():
	cell = default_cell_params()
	packp = default_pack_params()
	therm = default_thermal_params()
	adv = AdvancedPackParams(thermal_mode="fin", use_pybamm_ocv=False)
	pack = BatteryPackAdvanced(cell_base=cell, pack_params=packp, thermal_params=therm, adv=adv, initial_soc=0.8)

	# Run a few steps with small current
	for _ in range(10):
		row = pack.step(10.0, 1.0)
		assert 0.0 <= row["soc"] <= 1.0
		assert 200.0 < row["temp_k"] < 500.0

