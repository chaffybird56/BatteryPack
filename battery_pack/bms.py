"""Battery Management System (BMS) algorithms for protection and balancing."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np

from .config import PackParams, ThermalParams


class ProtectionStatus(Enum):
	"""BMS protection status codes."""

	OK = "ok"
	UNDER_VOLTAGE = "under_voltage"
	OVER_VOLTAGE = "over_voltage"
	OVER_CURRENT_DISCHARGE = "over_current_discharge"
	OVER_CURRENT_CHARGE = "over_current_charge"
	OVER_TEMPERATURE = "over_temperature"
	UNDER_TEMPERATURE = "under_temperature"
	SHORT_CIRCUIT = "short_circuit"


@dataclass
class ProtectionLimits:
	"""BMS protection thresholds."""

	V_min_v: float = 3.0
	V_max_v: float = 4.2
	I_max_discharge_a: float = 120.0
	I_max_charge_a: float = 120.0
	T_min_k: float = 273.15  # 0°C
	T_max_k: float = 328.15  # 55°C
	short_circuit_current_a: float = 500.0
	voltage_hysteresis_v: float = 0.1  # Hysteresis to prevent oscillation
	temp_hysteresis_k: float = 5.0


@dataclass
class ProtectionResult:
	"""Result of BMS protection check."""

	status: ProtectionStatus
	current_limit_a: float
	voltage_ok: bool
	current_ok: bool
	temperature_ok: bool
	message: str


class BMSProtection:
	"""Battery Management System protection algorithms."""

	def __init__(self, limits: ProtectionLimits):
		self.limits = limits
		self._last_status = ProtectionStatus.OK

	def check_protection(
		self,
		voltage_v: float,
		current_a: float,
		temperature_k: float,
		cell_count: int = 1,
	) -> ProtectionResult:
		"""Check if operating conditions violate protection limits.

		Args:
			voltage_v: Pack voltage (V)
			current_a: Pack current (A), positive for discharge
			temperature_k: Pack temperature (K)
			cell_count: Number of cells in series for voltage scaling

		Returns:
			ProtectionResult with status and current limit
		"""
		# Normalize voltage to cell level
		V_cell = voltage_v / max(1, cell_count)

		# Voltage protection
		voltage_ok = self.limits.V_min_v <= V_cell <= self.limits.V_max_v
		if V_cell < self.limits.V_min_v:
			status = ProtectionStatus.UNDER_VOLTAGE
			current_limit = 0.0
			message = f"Under voltage: {V_cell:.3f}V < {self.limits.V_min_v}V"
		elif V_cell > self.limits.V_max_v:
			status = ProtectionStatus.OVER_VOLTAGE
			current_limit = 0.0
			message = f"Over voltage: {V_cell:.3f}V > {self.limits.V_max_v}V"
		else:
			# Temperature protection
			temperature_ok = self.limits.T_min_k <= temperature_k <= self.limits.T_max_k
			if temperature_k > self.limits.T_max_k:
				status = ProtectionStatus.OVER_TEMPERATURE
				current_limit = 0.0
				message = f"Over temperature: {temperature_k:.2f}K > {self.limits.T_max_k}K"
			elif temperature_k < self.limits.T_min_k:
				status = ProtectionStatus.UNDER_TEMPERATURE
				current_limit = 0.0
				message = f"Under temperature: {temperature_k:.2f}K < {self.limits.T_min_k}K"
			else:
				# Current protection
				if abs(current_a) > self.limits.short_circuit_current_a:
					status = ProtectionStatus.SHORT_CIRCUIT
					current_limit = 0.0
					current_ok = False
					message = "Short circuit detected"
				elif current_a > self.limits.I_max_discharge_a:
					status = ProtectionStatus.OVER_CURRENT_DISCHARGE
					current_limit = self.limits.I_max_discharge_a
					current_ok = False
					message = f"Over current discharge: {current_a:.2f}A > {self.limits.I_max_discharge_a}A"
				elif current_a < -self.limits.I_max_charge_a:
					status = ProtectionStatus.OVER_CURRENT_CHARGE
					current_limit = -self.limits.I_max_charge_a
					current_ok = False
					message = f"Over current charge: {abs(current_a):.2f}A > {self.limits.I_max_charge_a}A"
				else:
					status = ProtectionStatus.OK
					current_limit = current_a
					current_ok = True
					message = "OK"
					temperature_ok = True

		self._last_status = status

		return ProtectionResult(
			status=status,
			current_limit=current_limit,
			voltage_ok=voltage_ok,
			current_ok=current_ok if "current_ok" in locals() else True,
			temperature_ok=temperature_ok if "temperature_ok" in locals() else True,
			message=message,
		)

	def apply_current_limit(self, requested_current_a: float, protection_result: ProtectionResult) -> float:
		"""Apply current limiting based on protection check.

		Args:
			requested_current_a: Desired current (A)
			protection_result: Result from protection check

		Returns:
			Limited current (A)
		"""
		if protection_result.status == ProtectionStatus.OK:
			return requested_current_a
		else:
			return protection_result.current_limit


@dataclass
class BalancingParams:
	"""Passive balancing parameters."""

	balance_threshold: float = 0.05  # SOC difference to trigger balancing
	balance_current_a: float = 0.1  # Balancing resistor current
	enable: bool = True


class PassiveBalancer:
	"""Passive cell balancing using shunt resistors."""

	def __init__(self, params: BalancingParams):
		self.params = params

	def balance(
		self,
		soc_array: np.ndarray,
		voltage_array: np.ndarray,
		dt_s: float,
	) -> Tuple[np.ndarray, float]:
		"""Apply passive balancing to reduce SOC spread.

		Args:
			soc_array: Array of cell SOCs [0-1]
			voltage_array: Array of cell voltages (V)
			dt_s: Time step (s)

		Returns:
			Tuple of (updated SOCs, energy lost to balancing in Wh)
		"""
		if not self.params.enable:
			return soc_array, 0.0

		soc_updated = soc_array.copy()
		soc_mean = np.mean(soc_array)
		soc_std = np.std(soc_array)

		# Only balance if spread exceeds threshold
		if soc_std < self.params.balance_threshold:
			return soc_updated, 0.0

		# Discharge cells above mean SOC
		above_mean = soc_array > soc_mean + self.params.balance_threshold / 2
		balance_current_cell_a = self.params.balance_current_a

		# Estimate SOC change from balancing
		# Assume average capacity for simplicity
		capacity_ah = 3.0  # Default, should be passed as parameter
		d_soc = balance_current_cell_a * dt_s / (capacity_ah * 3600.0)

		energy_lost_wh = 0.0
		for i in range(len(soc_array)):
			if above_mean[i]:
				# Discharge high cells
				old_soc = soc_updated[i]
				soc_updated[i] = max(soc_mean, old_soc - d_soc)
				# Energy lost = I * V * dt
				energy_lost_wh += balance_current_cell_a * voltage_array[i] * dt_s / 3600.0

		return soc_updated, energy_lost_wh


class ActiveBalancer:
	"""Active cell balancing using charge transfer (simplified model)."""

	def __init__(self, efficiency: float = 0.85):
		self.efficiency = efficiency

	def balance(
		self,
		soc_array: np.ndarray,
		voltage_array: np.ndarray,
		capacity_array: np.ndarray,
		dt_s: float,
	) -> Tuple[np.ndarray, float]:
		"""Apply active balancing using charge shuttling.

		Args:
			soc_array: Array of cell SOCs [0-1]
			voltage_array: Array of cell voltages (V)
			capacity_array: Array of cell capacities (Ah)
			dt_s: Time step (s)

		Returns:
			Tuple of (updated SOCs, energy consumed by balancing in Wh)
		"""
		soc_updated = soc_array.copy()
		soc_mean = np.mean(soc_array)

		# Identify highest and lowest SOC cells
		high_idx = np.argmax(soc_array)
		low_idx = np.argmin(soc_array)

		# Balance if difference is significant
		soc_diff = soc_array[high_idx] - soc_array[low_idx]
		if soc_diff < 0.02:  # 2% threshold
			return soc_updated, 0.0

		# Transfer charge from high to low (simplified)
		# Transfer rate limited by balancing power
		balance_power_w = 5.0  # Typical active balancer power
		balance_current_a = balance_power_w / voltage_array[high_idx]

		# Estimate SOC change
		d_soc_high = balance_current_a * dt_s / (capacity_array[high_idx] * 3600.0)
		d_soc_low = balance_current_a * dt_s * self.efficiency / (capacity_array[low_idx] * 3600.0)

		soc_updated[high_idx] = max(soc_mean, soc_updated[high_idx] - d_soc_high)
		soc_updated[low_idx] = min(soc_mean + 0.05, soc_updated[low_idx] + d_soc_low)

		# Energy consumed by balancing electronics
		energy_consumed_wh = balance_power_w * dt_s / 3600.0

		return soc_updated, energy_consumed_wh

