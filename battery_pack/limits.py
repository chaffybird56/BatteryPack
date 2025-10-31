from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .pack import BatteryPack


@dataclass
class PowerLimits:
	max_discharge_w: float
	max_charge_w: float  # negative sign not applied; magnitude only


def _voltage_at_current(pack: BatteryPack, I_a: float, soc: float) -> float:
	# Instantaneous voltage estimate ignoring dynamic RC voltage
	cell = pack.cell
	R0, R1 = cell.temperature_adjusted_resistances(pack.state.T_k)
	I_cell = I_a / max(1, pack.Np)
	V_cell = cell.ocv(soc) - (R0 + R1) * I_cell
	return pack.Ns * V_cell


def compute_power_limits(pack: BatteryPack, soc: float) -> PowerLimits:
	pp = pack.pack_params
	cellp = pack.cell.params
	Vmin_pack = pack.Ns * cellp.V_min
	Vmax_pack = pack.Ns * cellp.V_max

	I_abs_max = float(pp.max_current_a)

	# Discharge limit: ensure voltage >= Vmin and SOC >= min_soc
	def can_discharge(I: float) -> bool:
		if soc <= pp.min_soc + 1e-6:
			return False
		V = _voltage_at_current(pack, I, soc)
		return V >= Vmin_pack - 1e-6

	lo, hi = 0.0, I_abs_max
	for _ in range(30):
		mid = 0.5 * (lo + hi)
		if can_discharge(mid):
			lo = mid
		else:
			hi = mid
	I_dis_max = lo
	P_dis_max = I_dis_max * _voltage_at_current(pack, I_dis_max, soc)

	# Charge limit: ensure voltage <= Vmax and SOC <= max_soc
	def can_charge(I: float) -> bool:
		if soc >= pp.max_soc - 1e-6:
			return False
		V = _voltage_at_current(pack, -I, soc)
		return V <= Vmax_pack + 1e-6

	lo, hi = 0.0, I_abs_max
	for _ in range(30):
		mid = 0.5 * (lo + hi)
		if can_charge(mid):
			lo = mid
		else:
			hi = mid
	I_chg_max = lo
	P_chg_max = I_chg_max * _voltage_at_current(pack, -I_chg_max, soc)

	return PowerLimits(max_discharge_w=float(P_dis_max), max_charge_w=float(P_chg_max))

