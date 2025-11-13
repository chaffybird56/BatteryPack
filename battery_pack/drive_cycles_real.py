"""Real-world drive cycle support for automotive applications (EPA, WLTP, NEDC, etc.)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from .drive_cycles import DriveCycle


class DriveCycleType(Enum):
	"""Standard automotive drive cycle types."""

	EPA_FTP75 = "epa_ftp75"  # Federal Test Procedure
	EPA_HWFET = "epa_hwfet"  # Highway Fuel Economy Test
	EPA_UDDS = "epa_udds"  # Urban Dynamometer Driving Schedule
	WLTP_CLASS3 = "wltp_class3"  # Worldwide harmonized Light vehicles Test Procedure
	NEDC = "nedc"  # New European Driving Cycle
	SC03 = "sc03"  # Air conditioning test
	US06 = "us06"  # High-speed/acceleration test
	CUSTOM = "custom"  # User-defined cycle


@dataclass
class CycleProfile:
	"""Drive cycle velocity profile."""

	time_s: np.ndarray  # Time in seconds
	velocity_ms: np.ndarray  # Velocity in m/s
	acceleration_ms2: Optional[np.ndarray] = None  # Acceleration in m/s²
	grade_deg: Optional[np.ndarray] = None  # Road grade in degrees


def velocity_to_current(
	velocity_ms: np.ndarray,
	acceleration_ms2: np.ndarray,
	vehicle_mass_kg: float = 1500.0,
	rolling_resistance: float = 0.015,
	air_density_kgm3: float = 1.225,
	drag_coefficient: float = 0.3,
	frontal_area_m2: float = 2.0,
	grade_deg: Optional[np.ndarray] = None,
	pack_voltage_v: float = 400.0,
	motor_efficiency: float = 0.90,
	transmission_efficiency: float = 0.95,
	regenerative_braking_efficiency: float = 0.70,
) -> np.ndarray:
	"""Convert velocity profile to battery current using vehicle dynamics.
	
	Args:
		velocity_ms: Vehicle velocity (m/s)
		acceleration_ms2: Vehicle acceleration (m/s²)
		vehicle_mass_kg: Vehicle mass (kg)
		rolling_resistance: Rolling resistance coefficient
		air_density_kgm3: Air density (kg/m³)
		drag_coefficient: Aerodynamic drag coefficient
		frontal_area_m2: Vehicle frontal area (m²)
		grade_deg: Road grade in degrees (optional)
		pack_voltage_v: Nominal pack voltage (V)
		motor_efficiency: Motor efficiency [0-1]
		transmission_efficiency: Transmission efficiency [0-1]
		regenerative_braking_efficiency: Regen efficiency [0-1]
		
	Returns:
		Battery current (A), positive for discharge
	"""
	# Calculate forces
	F_aero = 0.5 * air_density_kgm3 * drag_coefficient * frontal_area_m2 * velocity_ms ** 2
	F_roll = rolling_resistance * vehicle_mass_kg * 9.81
	F_accel = vehicle_mass_kg * acceleration_ms2
	
	# Grade force
	if grade_deg is not None:
		F_grade = vehicle_mass_kg * 9.81 * np.sin(np.deg2rad(grade_deg))
	else:
		F_grade = np.zeros_like(velocity_ms)
	
	# Total force
	F_total = F_aero + F_roll + F_accel + F_grade
	
	# Power required
	P_mechanical_w = F_total * velocity_ms
	
	# Battery power (accounting for efficiency)
	# Discharge: P_batt = P_mech / (motor_eff * trans_eff)
	# Charge (regen): P_batt = P_mech * regen_eff
	discharge_mask = P_mechanical_w > 0
	charge_mask = P_mechanical_w < 0
	
	P_battery_w = np.zeros_like(P_mechanical_w)
	P_battery_w[discharge_mask] = P_mechanical_w[discharge_mask] / (
		motor_efficiency * transmission_efficiency
	)
	P_battery_w[charge_mask] = (
		P_mechanical_w[charge_mask] * regenerative_braking_efficiency
	)
	
	# Current (positive = discharge)
	I_battery_a = P_battery_w / pack_voltage_v
	
	return I_battery_a


def load_cycle_from_csv(
	csv_path: Path | str,
	time_col: str = "time_s",
	velocity_col: str = "velocity_kmh",
	velocity_units: str = "kmh",  # "kmh" or "ms"
) -> CycleProfile:
	"""Load drive cycle from CSV file.
	
	Args:
		csv_path: Path to CSV file
		time_col: Column name for time
		velocity_col: Column name for velocity
		velocity_units: Units of velocity ("kmh" or "ms")
		
	Returns:
		CycleProfile object
	"""
	df = pd.read_csv(csv_path)
	
	time_s = df[time_col].to_numpy()
	velocity = df[velocity_col].to_numpy()
	
	# Convert velocity to m/s if needed
	if velocity_units.lower() == "kmh":
		velocity_ms = velocity / 3.6
	else:
		velocity_ms = velocity
	
	# Calculate acceleration
	dt = np.diff(time_s)
	acceleration_ms2 = np.diff(velocity_ms) / np.maximum(dt, 1e-6)
	# Pad to match length
	acceleration_ms2 = np.concatenate([[acceleration_ms2[0]], acceleration_ms2])
	
	return CycleProfile(
		time_s=time_s,
		velocity_ms=velocity_ms,
		acceleration_ms2=acceleration_ms2,
	)


def generate_epa_udds() -> DriveCycle:
	"""Generate EPA Urban Dynamometer Driving Schedule (UDDS).
	
	The UDDS is a 1369-second cycle representing city driving.
	"""
	# Simplified UDDS profile (simplified - full implementation would use exact cycle data)
	t = np.arange(0, 1369, 1.0)
	# Typical UDDS has many stop-and-go segments
	# This is a simplified approximation - real implementation would use lookup tables
	velocity_kmh = 30.0 + 20.0 * np.sin(2 * np.pi * t / 200.0) * np.exp(-t / 1000.0)
	velocity_kmh = np.clip(velocity_kmh, 0, 91.2)  # UDDS max speed
	velocity_ms = velocity_kmh / 3.6
	
	dt = 1.0
	acceleration_ms2 = np.diff(velocity_ms) / dt
	acceleration_ms2 = np.concatenate([[0], acceleration_ms2])
	
	# Convert to current (typical EV parameters)
	current_a = velocity_to_current(
		velocity_ms,
		acceleration_ms2,
		vehicle_mass_kg=1500.0,
		pack_voltage_v=400.0,
	)
	
	return DriveCycle(time_s=t, current_a=current_a)


def generate_wltp_class3() -> DriveCycle:
	"""Generate WLTP Class 3 drive cycle (30-minute cycle).
	
	WLTP (Worldwide harmonized Light vehicles Test Procedure) has multiple phases.
	"""
	# WLTP Class 3 is approximately 1800 seconds
	t = np.arange(0, 1800, 1.0)
	# Simplified WLTP profile (would use exact cycle data in production)
	# WLTP has Low, Medium, High, and Extra-High speed phases
	velocity_kmh = (
		40.0
		+ 30.0 * np.sin(2 * np.pi * t / 300.0)
		+ 15.0 * np.sin(2 * np.pi * t / 600.0)
	)
	velocity_kmh = np.clip(velocity_kmh, 0, 131.3)  # WLTP max speed
	velocity_ms = velocity_kmh / 3.6
	
	dt = 1.0
	acceleration_ms2 = np.diff(velocity_ms) / dt
	acceleration_ms2 = np.concatenate([[0], acceleration_ms2])
	
	current_a = velocity_to_current(
		velocity_ms,
		acceleration_ms2,
		vehicle_mass_kg=1500.0,
		pack_voltage_v=400.0,
	)
	
	return DriveCycle(time_s=t, current_a=current_a)


def generate_nedc() -> DriveCycle:
	"""Generate New European Driving Cycle (NEDC).
	
	NEDC is a 1180-second cycle with urban and extra-urban phases.
	"""
	t = np.arange(0, 1180, 1.0)
	# Simplified NEDC (would use exact cycle data)
	# NEDC has 4 urban cycles + 1 extra-urban cycle
	velocity_kmh = 45.0 + 25.0 * np.sin(2 * np.pi * t / 400.0)
	velocity_kmh = np.clip(velocity_kmh, 0, 120.0)  # NEDC max speed
	velocity_ms = velocity_kmh / 3.6
	
	dt = 1.0
	acceleration_ms2 = np.diff(velocity_ms) / dt
	acceleration_ms2 = np.concatenate([[0], acceleration_ms2])
	
	current_a = velocity_to_current(
		velocity_ms,
		acceleration_ms2,
		vehicle_mass_kg=1500.0,
		pack_voltage_v=400.0,
	)
	
	return DriveCycle(time_s=t, current_a=current_a)


def get_standard_cycle(cycle_type: DriveCycleType | str) -> DriveCycle:
	"""Get a standard automotive drive cycle.
	
	Args:
		cycle_type: Type of drive cycle
		
	Returns:
		DriveCycle object
	"""
	if isinstance(cycle_type, str):
		cycle_type = DriveCycleType(cycle_type)
	
	if cycle_type == DriveCycleType.EPA_UDDS:
		return generate_epa_udds()
	elif cycle_type == DriveCycleType.WLTP_CLASS3:
		return generate_wltp_class3()
	elif cycle_type == DriveCycleType.NEDC:
		return generate_nedc()
	else:
		raise ValueError(f"Unsupported cycle type: {cycle_type}")

