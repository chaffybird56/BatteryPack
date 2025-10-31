from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np

from .config import CellParams


@dataclass
class CellECM:
	"""First-order ECM with R0 + R1||C1 and simple OCV(SOC)."""
	params: CellParams

	def ocv(self, soc: float) -> float:
		# Smooth, monotonic OCV curve shaped via sigmoids; clipped to bounds
		s = np.clip(soc, 0.0, 1.0)
		v = 3.0 + 1.2 * s + 0.3 * np.exp(-20.0 * (1.0 - s)) - 0.08 * np.exp(-20.0 * s)
		return float(np.clip(v, self.params.ocv_floor_v, self.params.ocv_ceiling_v))

	def temperature_adjusted_resistances(self, T_k: float) -> Tuple[float, float]:
		alpha = self.params.R_temp_coeff_per_k
		delta_T = T_k - self.params.T_ref_k
		scale = 1.0 + alpha * delta_T
		return self.params.R0_ohm * scale, self.params.R1_ohm * scale

	def step_voltage_states(
		self,
		I_a: float,
		dt_s: float,
		V_rc1_v: float,
		T_k: float,
		initial_soc: float,
	) -> Tuple[float, float, float]:
		"""Advance RC state and compute terminal voltage and SOC.

		Returns (V_terminal_v, next_V_rc1_v, next_soc)
		"""
		R0, R1 = self.temperature_adjusted_resistances(T_k)
		tau = R1 * self.params.C1_f

		# Update RC branch voltage (forward Euler with exponential exact solution)
		if tau > 1e-9:
			exp_fac = np.exp(-dt_s / tau)
			next_V_rc1_v = float(exp_fac * V_rc1_v + (1.0 - exp_fac) * (R1 * I_a))
		else:
			next_V_rc1_v = float(R1 * I_a)

		# SOC update by coulomb counting (positive I is discharge)
		q_as = self.params.capacity_ah * 3600.0
		next_soc = float(np.clip(initial_soc - (I_a * dt_s) / q_as, 0.0, 1.0))

		V_term = self.ocv(next_soc) - R0 * I_a - next_V_rc1_v
		return float(V_term), next_V_rc1_v, next_soc

	def instantaneous_heat_w(self, I_a: float, V_term_v: float) -> float:
		# I*V negative is charge; heat approximated as I^2*R0 + I*V_rc losses
		# For simplicity, estimate joule loss as I*(OCV - V_term)
		return float(abs(I_a) * max(0.0, self.ocv(0.5) - V_term_v))

