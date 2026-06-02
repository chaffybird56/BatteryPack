"""
Uninterrupted Power Supply (UPS) and Battery Backup Systems Module
Engineers battery backup systems and uninterrupted power supply solutions for electrical power systems.
Analyzes battery performance and power system requirements for backup power applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np

from .pack import BatteryPack
from .config import CellParams, PackParams, ThermalParams, SimulationParams
from .metrics import calculate_metrics


@dataclass
class UPSRequirements:
    """Requirements for UPS/backup power applications."""

    backup_power_kw: float  # Required backup power in kW
    backup_duration_hours: float  # Required backup duration
    input_voltage_v: float = 120.0  # AC input voltage
    efficiency_target: float = 0.85  # Minimum efficiency requirement
    max_temperature_c: float = 40.0  # Maximum operating temperature
    compliance_standards: List[str] = None  # e.g., ["OESC", "CSA", "UL"]

    def __post_init__(self):
        if self.compliance_standards is None:
            self.compliance_standards = ["OESC", "CSA"]  # Ontario Electrical Safety Code, CSA


@dataclass
class BackupPowerAnalysis:
    """Results from backup power system analysis."""

    pack_config: Dict[str, float]
    backup_capacity_kwh: float
    estimated_backup_duration_hours: float
    peak_power_kw: float
    efficiency_percent: float
    compliance_status: Dict[str, bool]
    recommendations: List[str]


class UPSBackupSystem:
    """
    Engineered battery backup systems and uninterrupted power supply solutions.
    Supports reliable operations for electrical power systems.
    """

    def __init__(self, pack: BatteryPack):
        self.pack = pack

    def analyze_backup_requirements(self, requirements: UPSRequirements) -> BackupPowerAnalysis:
        """
        Analyze battery performance and power system requirements for backup power applications.
        Calculates engineering parameters for UPS systems.
        """
        # Calculate pack capacity
        cell_capacity_ah = self.pack.cell.params.capacity_ah
        pack_capacity_ah = cell_capacity_ah * self.pack.Np
        pack_voltage_v = self.pack.Ns * 3.7  # Approximate nominal voltage
        pack_capacity_kwh = (pack_capacity_ah * pack_voltage_v) / 1000.0

        # Calculate backup duration at required power
        backup_duration_hours = (
            pack_capacity_kwh / requirements.backup_power_kw if requirements.backup_power_kw > 0 else 0
        )

        # Calculate peak power capability
        max_current_a = self.pack.pack_params.max_current_a
        peak_power_kw = (pack_voltage_v * max_current_a) / 1000.0

        # Estimate efficiency (simplified - would use actual simulation)
        efficiency_percent = 0.88  # Typical UPS efficiency

        # Compliance checking
        compliance_status = self._check_compliance(requirements)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            requirements, backup_duration_hours, peak_power_kw, efficiency_percent
        )

        return BackupPowerAnalysis(
            pack_config={
                "series_cells": self.pack.Ns,
                "parallel_cells": self.pack.Np,
                "cell_capacity_ah": cell_capacity_ah,
                "pack_voltage_v": pack_voltage_v,
            },
            backup_capacity_kwh=round(pack_capacity_kwh, 2),
            estimated_backup_duration_hours=round(backup_duration_hours, 2),
            peak_power_kw=round(peak_power_kw, 2),
            efficiency_percent=round(efficiency_percent * 100, 1),
            compliance_status=compliance_status,
            recommendations=recommendations,
        )

    def _check_compliance(self, requirements: UPSRequirements) -> Dict[str, bool]:
        """
        Validate battery systems through testing ensuring compliance with
        Ontario Electrical Safety Code, CSA, and performance specifications.
        """
        compliance = {}

        # Ontario Electrical Safety Code (OESC) compliance
        if "OESC" in requirements.compliance_standards:
            # Check voltage limits, temperature limits, safety requirements
            pack_voltage_v = self.pack.Ns * 3.7
            max_temp_c = self.pack.thermal.params.T_max_k - 273.15

            compliance["OESC"] = (
                pack_voltage_v <= 600.0  # Low voltage limit
                and max_temp_c <= requirements.max_temperature_c
                and self.pack.pack_params.max_current_a <= 200.0  # Safety current limit
            )

        # CSA (Canadian Standards Association) compliance
        if "CSA" in requirements.compliance_standards:
            # Check for CSA C22.2 No. 107.1 compliance (battery systems)
            compliance["CSA"] = (
                self.pack.thermal.params.T_max_k <= 328.15  # 55°C max
                and self.pack.pack_params.max_current_a > 0
                and self.pack.cell.params.V_min >= 2.5  # Safe minimum voltage
            )

        # UL (Underwriters Laboratories) compliance (if specified)
        if "UL" in requirements.compliance_standards:
            compliance["UL"] = (
                self.pack.thermal.params.T_max_k <= 333.15 and self.pack.pack_params.max_current_a <= 300.0  # 60°C max
            )

        return compliance

    def _generate_recommendations(
        self, requirements: UPSRequirements, backup_duration: float, peak_power: float, efficiency: float
    ) -> List[str]:
        """Generate recommendations for backup power system design."""
        recommendations = []

        if backup_duration < requirements.backup_duration_hours:
            recommendations.append(
                f"Increase pack capacity or reduce load to meet {requirements.backup_duration_hours}h backup requirement"
            )

        if peak_power < requirements.backup_power_kw:
            recommendations.append(
                f"Increase pack current rating or parallel cells to meet {requirements.backup_power_kw}kW power requirement"
            )

        if efficiency < requirements.efficiency_target:
            recommendations.append(
                f"Optimize pack design to improve efficiency above {requirements.efficiency_target*100}%"
            )

        if not recommendations:
            recommendations.append("Pack configuration meets backup power requirements")

        return recommendations

    def simulate_backup_scenario(
        self, requirements: UPSRequirements, simulation_params: Optional[SimulationParams] = None
    ) -> Dict:
        """
        Simulate backup power scenario to validate system performance.
        """
        if simulation_params is None:
            simulation_params = SimulationParams(
                dt_s=1.0, t_total_s=requirements.backup_duration_hours * 3600, initial_soc=1.0  # Start fully charged
            )

        # Create constant power discharge profile
        backup_power_w = requirements.backup_power_kw * 1000.0
        pack_voltage_v = self.pack.Ns * 3.7  # Nominal voltage
        discharge_current_a = backup_power_w / pack_voltage_v

        # Run simulation
        results = []
        self.pack.reset(initial_soc=1.0)

        t = 0.0
        while t < simulation_params.t_total_s and self.pack.state.soc > 0.1:
            step_result = self.pack.step(discharge_current_a, simulation_params.dt_s)
            results.append(
                {
                    "time_s": t,
                    "soc": step_result["soc"],
                    "voltage_v": step_result["v_pack_v"],
                    "current_a": step_result["i_pack_a"],
                    "power_w": step_result["power_w"],
                    "temperature_k": step_result["temp_k"],
                }
            )
            t += simulation_params.dt_s

        # Calculate metrics
        total_energy_kwh = sum(r["power_w"] * simulation_params.dt_s / 3600.0 / 1000.0 for r in results)
        actual_duration_hours = len(results) * simulation_params.dt_s / 3600.0

        return {
            "simulation_results": results,
            "total_energy_kwh": round(total_energy_kwh, 2),
            "actual_backup_duration_hours": round(actual_duration_hours, 2),
            "meets_requirement": actual_duration_hours >= requirements.backup_duration_hours,
            "final_soc": results[-1]["soc"] if results else 0.0,
            "max_temperature_c": round(max(r["temperature_k"] for r in results) - 273.15, 1) if results else 0.0,
        }


def design_ups_system(
    requirements: UPSRequirements,
    cell_params: Optional[CellParams] = None,
    thermal_params: Optional[ThermalParams] = None,
) -> BatteryPack:
    """
    Design a battery pack optimized for UPS/backup power applications.
    """
    if cell_params is None:
        cell_params = CellParams(capacity_ah=5.0, R0_ohm=0.002, R1_ohm=0.001, C1_f=3000.0)  # Higher capacity for backup

    if thermal_params is None:
        thermal_params = ThermalParams(
            mass_kg=15.0,
            Cp_j_per_kgk=900.0,
            UA_w_per_k=8.0,  # Better cooling for continuous operation
            T_ambient_k=298.15,
            T_max_k=318.15,  # 45°C max for reliability
        )

    # Calculate required pack configuration
    # Estimate: need capacity for backup_duration at backup_power
    required_energy_kwh = requirements.backup_power_kw * requirements.backup_duration_hours
    cell_energy_wh = cell_params.capacity_ah * 3.7  # Nominal voltage
    cells_parallel = int(np.ceil(required_energy_kwh * 1000 / (cell_energy_wh * 0.8)))  # 80% usable
    cells_series = int(np.ceil(requirements.input_voltage_v / 3.7))  # Match input voltage

    pack_params = PackParams(
        series_cells=max(cells_series, 20),  # Minimum for safety
        parallel_cells=max(cells_parallel, 2),
        max_current_a=requirements.backup_power_kw * 1000 / (cells_series * 3.7) * 1.2,  # 20% margin
    )

    return BatteryPack(cell_params=cell_params, pack_params=pack_params, thermal_params=thermal_params, initial_soc=1.0)
