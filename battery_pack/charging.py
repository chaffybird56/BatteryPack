"""Fast charging protocol simulation for EV applications (CCS, CHAdeMO, Supercharger)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional

import numpy as np

from .config import CellParams, PackParams


class ChargingProtocol(Enum):
	"""EV fast charging protocol types."""

	LEVEL1 = "level1"  # 120V AC, ~1.4 kW
	LEVEL2 = "level2"  # 240V AC, ~7-19 kW
	CHAdeMO = "chademo"  # DC fast charging, up to 62.5 kW
	CCS_COMBO1 = "ccs_combo1"  # Combined Charging System Type 1, up to 350 kW
	CCS_COMBO2 = "ccs_combo2"  # CCS Type 2, up to 350 kW
	TESLA_SUPERCHARGER = "tesla_supercharger"  # Up to 250 kW (V3)
	TESLA_MEGACHARGER = "tesla_megacharger"  # For Semi, up to 1 MW


@dataclass
class ChargingProfile:
	"""Charging current/voltage profile."""

	time_s: np.ndarray
	current_a: np.ndarray  # Negative for charging
	voltage_v: Optional[np.ndarray] = None
	power_kw: Optional[np.ndarray] = None


@dataclass
class ChargingParams:
	"""Parameters for charging protocol."""

	protocol: ChargingProtocol
	max_power_kw: float
	max_current_a: float
	max_voltage_v: float = 500.0
	soc_start: float = 0.1
	soc_target: float = 0.8
	T_max_k: float = 318.15  # 45°C - thermal throttling threshold
	cell_V_max: float = 4.2
	cell_V_min: float = 3.0
	
	# Charging curve parameters
	cc_phase_soc: float = 0.3  # SOC where constant current phase ends
	cv_phase_start_soc: float = 0.8  # SOC where constant voltage phase starts
	taper_current_a: float = 10.0  # Minimum charging current before termination


def constant_current_constant_voltage(
	cell_params: CellParams,
	pack_params: PackParams,
	charging_params: ChargingParams,
	dt_s: float = 1.0,
) -> ChargingProfile:
	"""Generate CC-CV charging profile.
	
	Constant Current phase: Charge at max current until voltage limit
	Constant Voltage phase: Maintain voltage limit, current tapers
	"""
	soc_current = charging_params.soc_start
	time_points = []
	current_points = []
	voltage_points = []
	power_points = []
	
	t = 0.0
	max_I_charge = -abs(charging_params.max_current_a)  # Negative for charge
	pack_V_max = pack_params.series_cells * charging_params.cell_V_max
	
	while soc_current < charging_params.soc_target:
		# Estimate cell voltage at current SOC
		# Simplified: linear OCV approximation
		ocv_cell = cell_params.ocv_floor_v + (
			cell_params.ocv_ceiling_v - cell_params.ocv_floor_v
		) * soc_current
		V_pack_est = pack_params.series_cells * ocv_cell
		
		# Constant Current phase
		if soc_current < charging_params.cc_phase_soc or V_pack_est < pack_V_max * 0.95:
			I_charge = max_I_charge
		# Constant Voltage phase
		elif soc_current >= charging_params.cv_phase_start_soc:
			# Taper current to maintain voltage
			I_charge = max(
				-charging_params.taper_current_a,
				max_I_charge * (1.0 - (soc_current - charging_params.cv_phase_start_soc) / 0.1),
			)
		# Transition phase
		else:
			# Linear transition
			transition_factor = (
				soc_current - charging_params.cc_phase_soc
			) / (charging_params.cv_phase_start_soc - charging_params.cc_phase_soc)
			I_charge = max_I_charge * (1.0 - transition_factor * 0.5)
		
		# Update SOC
		capacity_ah = cell_params.capacity_ah
		d_soc = abs(I_charge) * dt_s / (capacity_ah * 3600.0)
		soc_current = min(charging_params.soc_target, soc_current + d_soc)
		
		# Calculate voltage and power
		V_pack = V_pack_est  # Simplified - would use actual pack model
		P_w = V_pack * I_charge
		
		time_points.append(t)
		current_points.append(I_charge)
		voltage_points.append(V_pack)
		power_points.append(P_w / 1000.0)  # Convert to kW
		
		t += dt_s
		
		if soc_current >= charging_params.soc_target:
			break
	
	return ChargingProfile(
		time_s=np.array(time_points),
		current_a=np.array(current_points),
		voltage_v=np.array(voltage_points),
		power_kw=np.array(power_points),
	)


def tesla_supercharger_profile(
	cell_params: CellParams,
	pack_params: PackParams,
	soc_start: float = 0.1,
	soc_target: float = 0.8,
	dt_s: float = 1.0,
) -> ChargingProfile:
	"""Tesla Supercharger V3 charging profile (~250 kW peak).
	
	Tesla uses a sophisticated charging curve that adapts based on:
	- Battery temperature
	- SOC
	- Number of vehicles sharing power
	- Battery health
	"""
	charging_params = ChargingParams(
		protocol=ChargingProtocol.TESLA_SUPERCHARGER,
		max_power_kw=250.0,
		max_current_a=400.0,  # Typical for V3
		max_voltage_v=500.0,
		soc_start=soc_start,
		soc_target=soc_target,
		cc_phase_soc=0.5,  # Extended CC phase
		cv_phase_start_soc=0.8,
	)
	
	return constant_current_constant_voltage(cell_params, pack_params, charging_params, dt_s)


def ccs_combo_profile(
	cell_params: CellParams,
	pack_params: PackParams,
	max_power_kw: float = 350.0,
	soc_start: float = 0.1,
	soc_target: float = 0.8,
	dt_s: float = 1.0,
) -> ChargingProfile:
	"""CCS (Combined Charging System) charging profile.
	
	CCS supports up to 350 kW with adaptive power curves.
	"""
	max_current = (max_power_kw * 1000.0) / (pack_params.series_cells * 4.2)  # Estimate
	
	charging_params = ChargingParams(
		protocol=ChargingProtocol.CCS_COMBO1,
		max_power_kw=max_power_kw,
		max_current_a=max_current,
		max_voltage_v=1000.0,  # CCS supports up to 1000V
		soc_start=soc_start,
		soc_target=soc_target,
		cc_phase_soc=0.6,
		cv_phase_start_soc=0.85,
	)
	
	return constant_current_constant_voltage(cell_params, pack_params, charging_params, dt_s)


def thermal_limited_charging(
	soc: float,
	temperature_k: float,
	base_charging_current_a: float,
	T_max_k: float = 318.15,
	T_optimal_k: float = 303.15,
) -> float:
	"""Apply thermal throttling to charging current.
	
	Args:
		soc: Current state of charge [0-1]
		temperature_k: Pack temperature (K)
		base_charging_current_a: Base charging current (A)
		T_max_k: Maximum allowed temperature (K)
		T_optimal_k: Optimal temperature for charging (K)
		
	Returns:
		Thermally-limited charging current (A)
	"""
	if temperature_k > T_max_k:
		# Severe throttling or shutdown
		return base_charging_current_a * 0.1
	
	elif temperature_k > T_optimal_k + 5.0:
		# Linear throttling above optimal
		throttle_factor = 1.0 - (temperature_k - (T_optimal_k + 5.0)) / (T_max_k - T_optimal_k - 5.0)
		return base_charging_current_a * max(0.3, throttle_factor)
	
	elif temperature_k < T_optimal_k - 10.0:
		# Cold charging - reduced current
		cold_factor = 1.0 - (T_optimal_k - 10.0 - temperature_k) / 20.0
		return base_charging_current_a * max(0.5, cold_factor)
	
	else:
		# Optimal temperature range
		return base_charging_current_a


def get_charging_profile(
	protocol: ChargingProtocol | str,
	cell_params: CellParams,
	pack_params: PackParams,
	soc_start: float = 0.1,
	soc_target: float = 0.8,
	**kwargs,
) -> ChargingProfile:
	"""Get charging profile for specified protocol.
	
	Args:
		protocol: Charging protocol type
		cell_params: Cell parameters
		pack_params: Pack parameters
		soc_start: Starting SOC
		soc_target: Target SOC
		**kwargs: Additional protocol-specific parameters
		
	Returns:
		ChargingProfile object
	"""
	if isinstance(protocol, str):
		protocol = ChargingProtocol(protocol)
	
	if protocol == ChargingProtocol.TESLA_SUPERCHARGER:
		return tesla_supercharger_profile(
			cell_params,
			pack_params,
			soc_start,
			soc_target,
			kwargs.get("dt_s", 1.0),
		)
	elif protocol in (ChargingProtocol.CCS_COMBO1, ChargingProtocol.CCS_COMBO2):
		return ccs_combo_profile(
			cell_params,
			pack_params,
			kwargs.get("max_power_kw", 350.0),
			soc_start,
			soc_target,
			kwargs.get("dt_s", 1.0),
		)
	elif protocol == ChargingProtocol.CHAdeMO:
		# CHAdeMO supports up to 62.5 kW
		max_power = kwargs.get("max_power_kw", 62.5)
		max_current = (max_power * 1000.0) / (pack_params.series_cells * 4.2)
		params = ChargingParams(
			protocol=protocol,
			max_power_kw=max_power,
			max_current_a=max_current,
			max_voltage_v=500.0,
			soc_start=soc_start,
			soc_target=soc_target,
		)
		return constant_current_constant_voltage(
			cell_params,
			pack_params,
			params,
			kwargs.get("dt_s", 1.0),
		)
	else:
		raise ValueError(f"Protocol {protocol} not yet implemented")

