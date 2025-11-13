"""Monte Carlo uncertainty quantification for defense, aerospace, and critical systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .config import CellParams, PackParams, SimulationParams, ThermalParams
from .drive_cycles import DriveCycle
from .pack import BatteryPack
from .simulation import Simulator
from .variation import VariationParams, make_varied_cells


@dataclass
class UncertaintyParams:
	"""Parameters for uncertainty quantification analysis."""

	# Parameter distributions
	capacity_cv: float = 0.02  # Coefficient of variation
	R0_cv: float = 0.05
	R1_cv: float = 0.05
	thermal_UA_cv: float = 0.10  # Cooling uncertainty
	mass_cv: float = 0.05
	
	# Monte Carlo settings
	n_samples: int = 1000
	seed: Optional[int] = None
	
	# Failure criteria
	T_max_k: float = 328.15
	V_min_cell_v: float = 2.8  # Safety margin below nominal
	V_max_cell_v: float = 4.25  # Safety margin above nominal
	soc_min: float = 0.05  # Critical SOC threshold


@dataclass
class UncertaintyResult:
	"""Results from Monte Carlo uncertainty analysis."""

	metrics: pd.DataFrame  # One row per sample
	summary: Dict[str, float]  # Statistical summary
	failure_rate: float  # Fraction of samples that violate constraints
	reliability_metrics: Dict[str, float]


class MonteCarloAnalysis:
	"""Monte Carlo uncertainty quantification for battery pack performance."""

	def __init__(
		self,
		cell_base: CellParams,
		pack_params: PackParams,
		thermal_base: ThermalParams,
		uncertainty: UncertaintyParams,
	):
		self.cell_base = cell_base
		self.pack_params = pack_params
		self.thermal_base = thermal_base
		self.uncertainty = uncertainty
		self.rng = np.random.default_rng(uncertainty.seed)

	def sample_parameters(self) -> tuple[CellParams, ThermalParams]:
		"""Generate a random sample of cell and thermal parameters."""
		# Sample cell parameters
		capacity_scale = self.rng.normal(1.0, self.uncertainty.capacity_cv)
		R0_scale = self.rng.normal(1.0, self.uncertainty.R0_cv)
		R1_scale = self.rng.normal(1.0, self.uncertainty.R1_cv)
		
		cell_sample = CellParams(
			capacity_ah=self.cell_base.capacity_ah * max(0.5, capacity_scale),
			R0_ohm=self.cell_base.R0_ohm * max(0.5, R0_scale),
			R1_ohm=self.cell_base.R1_ohm * max(0.5, R1_scale),
			C1_f=self.cell_base.C1_f,
			V_min=self.cell_base.V_min,
			V_max=self.cell_base.V_max,
			T_ref_k=self.cell_base.T_ref_k,
			R_temp_coeff_per_k=self.cell_base.R_temp_coeff_per_k,
			ocv_floor_v=self.cell_base.ocv_floor_v,
			ocv_ceiling_v=self.cell_base.ocv_ceiling_v,
		)
		
		# Sample thermal parameters
		UA_scale = self.rng.normal(1.0, self.uncertainty.thermal_UA_cv)
		mass_scale = self.rng.normal(1.0, self.uncertainty.mass_cv)
		
		thermal_sample = ThermalParams(
			mass_kg=self.thermal_base.mass_kg * max(0.5, mass_scale),
			Cp_j_per_kgk=self.thermal_base.Cp_j_per_kgk,
			UA_w_per_k=self.thermal_base.UA_w_per_k * max(0.1, UA_scale),
			T_ambient_k=self.thermal_base.T_ambient_k,
			T_max_k=self.thermal_base.T_max_k,
		)
		
		return cell_sample, thermal_sample

	def run_single_sample(
		self,
		cycle: DriveCycle,
		sim_params: SimulationParams,
		sample_idx: int,
	) -> Dict[str, float]:
		"""Run simulation for a single parameter sample."""
		cell_sample, thermal_sample = self.sample_parameters()
		
		pack = BatteryPack(
			cell_params=cell_sample,
			pack_params=self.pack_params,
			thermal_params=thermal_sample,
			initial_soc=sim_params.initial_soc,
		)
		
		simulator = Simulator(pack, sim_params)
		result = simulator.run(cycle)
		
		# Extract metrics
		peak_temp_k = float(result["temp_k"].max())
		min_voltage_v = float(result["v_pack_v"].min())
		min_soc = float(result["soc"].min())
		max_current_a = float(result["i_pack_a"].abs().max())
		
		# Check failure conditions
		V_cell_min = min_voltage_v / self.pack_params.series_cells
		temp_failure = peak_temp_k > self.uncertainty.T_max_k
		voltage_failure = (V_cell_min < self.uncertainty.V_min_cell_v) or (
			V_cell_min > self.uncertainty.V_max_cell_v
		)
		soc_failure = min_soc < self.uncertainty.soc_min
		
		failed = temp_failure or voltage_failure or soc_failure
		
		# RTE calculation
		rte_result = simulator.round_trip_efficiency(cycle, sim_params.initial_soc)
		
		return {
			"sample_idx": sample_idx,
			"peak_temp_k": peak_temp_k,
			"min_voltage_v": min_voltage_v,
			"min_voltage_cell_v": V_cell_min,
			"min_soc": min_soc,
			"max_current_a": max_current_a,
			"RTE_percent": rte_result.RTE_percent,
			"energy_out_wh": rte_result.energy_out_wh,
			"temp_failure": int(temp_failure),
			"voltage_failure": int(voltage_failure),
			"soc_failure": int(soc_failure),
			"any_failure": int(failed),
			"capacity_ah": cell_sample.capacity_ah,
			"R0_ohm": cell_sample.R0_ohm,
			"UA_w_per_k": thermal_sample.UA_w_per_k,
		}

	def run_analysis(
		self,
		cycle: DriveCycle,
		sim_params: SimulationParams,
		n_jobs: int = -1,
	) -> UncertaintyResult:
		"""Run Monte Carlo analysis with parallel processing.
		
		Args:
			cycle: Drive cycle to simulate
			sim_params: Simulation parameters
			n_jobs: Number of parallel jobs (-1 for all cores)
			
		Returns:
			UncertaintyResult with metrics and statistics
		"""
		# Run samples in parallel
		results = Parallel(n_jobs=n_jobs)(
			delayed(self.run_single_sample)(cycle, sim_params, i)
			for i in range(self.uncertainty.n_samples)
		)
		
		df = pd.DataFrame(results)
		
		# Compute summary statistics
		summary = {
			"mean_peak_temp_k": df["peak_temp_k"].mean(),
			"std_peak_temp_k": df["peak_temp_k"].std(),
			"p95_peak_temp_k": df["peak_temp_k"].quantile(0.95),
			"p99_peak_temp_k": df["peak_temp_k"].quantile(0.99),
			"mean_RTE_percent": df["RTE_percent"].mean(),
			"std_RTE_percent": df["RTE_percent"].std(),
			"min_RTE_percent": df["RTE_percent"].min(),
			"mean_min_voltage_v": df["min_voltage_v"].mean(),
			"std_min_voltage_v": df["min_voltage_v"].std(),
		}
		
		# Reliability metrics
		failure_rate = df["any_failure"].mean()
		temp_failure_rate = df["temp_failure"].mean()
		voltage_failure_rate = df["voltage_failure"].mean()
		soc_failure_rate = df["soc_failure"].mean()
		
		reliability = {
			"failure_rate": failure_rate,
			"reliability": 1.0 - failure_rate,
			"temp_failure_rate": temp_failure_rate,
			"voltage_failure_rate": voltage_failure_rate,
			"soc_failure_rate": soc_failure_rate,
			"mean_time_to_failure": float("inf") if failure_rate == 0.0 else 1.0 / failure_rate,
		}
		
		return UncertaintyResult(
			metrics=df,
			summary=summary,
			failure_rate=failure_rate,
			reliability_metrics=reliability,
		)


def sensitivity_analysis(
	base_cell: CellParams,
	base_pack: PackParams,
	base_thermal: ThermalParams,
	cycle: DriveCycle,
	sim_params: SimulationParams,
	param_ranges: Dict[str, List[float]],
) -> pd.DataFrame:
	"""Global sensitivity analysis using Sobol sequences or Morris screening.
	
	Args:
		base_cell: Base cell parameters
		base_pack: Base pack parameters
		base_thermal: Base thermal parameters
		cycle: Drive cycle
		sim_params: Simulation parameters
		param_ranges: Dictionary of parameter names to value ranges
		
	Returns:
		DataFrame with sensitivity indices
	"""
	# Placeholder for sensitivity analysis
	# Would implement Sobol indices or Morris screening
	results = []
	
	for param_name, values in param_ranges.items():
		for val in values:
			# Create modified parameters
			cell = base_cell
			thermal = base_thermal
			
			if param_name == "R0_ohm":
				cell = CellParams(
					**{**base_cell.__dict__, "R0_ohm": val}
				)
			elif param_name == "UA_w_per_k":
				thermal = ThermalParams(
					**{**base_thermal.__dict__, "UA_w_per_k": val}
				)
			
			pack = BatteryPack(cell, base_pack, thermal, sim_params.initial_soc)
			simulator = Simulator(pack, sim_params)
			result = simulator.run(cycle)
			
			peak_temp = float(result["temp_k"].max())
			rte = simulator.round_trip_efficiency(cycle, sim_params.initial_soc)
			
			results.append({
				"parameter": param_name,
				"value": val,
				"peak_temp_k": peak_temp,
				"RTE_percent": rte.RTE_percent,
			})
	
	return pd.DataFrame(results)

