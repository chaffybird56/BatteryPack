from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np

from .cell import CellECM
from .config import CellParams, PackParams, ThermalParams
from .thermal import LumpedThermal


@dataclass
class PackState:
	soc: float
	T_k: float
	V_rc1_v: float


class BatteryPack:
	"""Series-parallel pack composed of identical cells and a lumped thermal node."""

	def __init__(
		self,
		cell_params: CellParams,
		pack_params: PackParams,
		thermal_params: ThermalParams,
		initial_soc: float = 0.8,
	):
		self.pack_params = pack_params
		self.cell = CellECM(cell_params)
		self.thermal = LumpedThermal(thermal_params)
		self.state = PackState(
			soc=float(np.clip(initial_soc, 0.0, 1.0)),
			T_k=thermal_params.T_ambient_k,
			V_rc1_v=0.0,
		)

	def reset(self, initial_soc: float) -> None:
		self.state.soc = float(np.clip(initial_soc, 0.0, 1.0))
		self.state.T_k = self.thermal.params.T_ambient_k
		self.state.V_rc1_v = 0.0

	@property
	def Ns(self) -> int:
		return self.pack_params.series_cells

	@property
	def Np(self) -> int:
		return self.pack_params.parallel_cells

	def pack_voltage_current(self, I_pack_a: float) -> Tuple[float, float, float]:
		"""Compute terminal voltages given current, advance internal states one step delayed.

		Note: voltage state update occurs in `step` with dt.
		"""
		I_cell_a = I_pack_a / max(1, self.Np)
		V_cell = self.cell.ocv(self.state.soc) - self.cell.params.R0_ohm * I_cell_a - self.state.V_rc1_v
		V_pack = self.Ns * V_cell
		return float(V_pack), float(V_cell), float(I_cell_a)

	def step(self, I_pack_a: float, dt_s: float) -> Dict[str, float]:
		"""Advance pack by one step with given pack current (I>0 discharge)."""
		V_pack_before, V_cell_before, I_cell_a = self.pack_voltage_current(I_pack_a)
		V_cell_new, V_rc1_new, soc_new = self._step_cell(I_cell_a, dt_s)
		V_pack_new = self.Ns * V_cell_new

		# Joule heating approximation: Ns * (I/Np)^2 * (R0 + R1)
		R0, R1 = self.cell.temperature_adjusted_resistances(self.state.T_k)
		R_sum = R0 + R1
		Q_pack_w = self.Ns * (I_pack_a ** 2) * R_sum / max(1, self.Np)
		T_next = self.thermal.step(self.state.T_k, Q_pack_w, dt_s)

		# Commit state
		self.state.V_rc1_v = V_rc1_new
		self.state.soc = soc_new
		self.state.T_k = T_next

		power_w = V_pack_new * I_pack_a
		return {
			"v_pack_v": V_pack_new,
			"v_cell_v": V_cell_new,
			"i_pack_a": I_pack_a,
			"i_cell_a": I_cell_a,
			"soc": soc_new,
			"temp_k": T_next,
			"power_w": power_w,
			"heat_w": Q_pack_w,
		}

	def _step_cell(self, I_cell_a: float, dt_s: float) -> Tuple[float, float, float]:
		V_term, V_rc1_next, soc_next = self.cell.step_voltage_states(
			I_a=I_cell_a,
			dt_s=dt_s,
			V_rc1_v=self.state.V_rc1_v,
			T_k=self.state.T_k,
			initial_soc=self.state.soc,
		)
		return V_term, V_rc1_next, soc_next

