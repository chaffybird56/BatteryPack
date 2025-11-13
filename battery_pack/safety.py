"""Thermal runaway and safety analysis for critical systems (aerospace, defense, automotive)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .config import CellParams, PackParams, ThermalParams


class FailureMode(Enum):
    """Battery failure modes."""

    THERMAL_RUNAWAY = "thermal_runaway"
    OVERCHARGE = "overcharge"
    OVERDISCHARGE = "overdischarge"
    OVERHEATING = "overheating"
    SHORT_CIRCUIT = "short_circuit"
    MECHANICAL_DAMAGE = "mechanical_damage"
    CURRENT_ABUSE = "current_abuse"


@dataclass
class ThermalRunawayParams:
    """Parameters for thermal runaway modeling."""

    T_trigger_k: float = 403.15  # ~130°C - onset temperature
    T_critical_k: float = 423.15  # ~150°C - critical temperature
    self_heat_rate_w_per_kg: float = 50.0  # Self-heating rate
    propagation_speed_ms: float = 0.01  # Cell-to-cell propagation speed
    energy_release_wh_per_cell: float = 50.0  # Energy released per cell
    probability_base: float = 1e-6  # Base probability per hour


@dataclass
class SafetyLimits:
    """Safety operating limits."""

    V_cell_min_safe_v: float = 2.5  # Safe minimum voltage
    V_cell_max_safe_v: float = 4.25  # Safe maximum voltage
    T_max_safe_k: float = 318.15  # 45°C - safe operating limit
    T_shutdown_k: float = 333.15  # 60°C - emergency shutdown
    I_max_safe_a: float = 500.0  # Safe current limit
    soc_min_safe: float = 0.05  # Safe minimum SOC
    soc_max_safe: float = 0.95  # Safe maximum SOC


@dataclass
class SafetyAnalysisResult:
    """Results from safety analysis."""

    failure_probability: float
    failure_modes: Dict[FailureMode, float]
    safe_operating_zone: Dict[str, Tuple[float, float]]
    time_to_failure_s: Optional[float]
    hazard_index: float  # Combined hazard metric


class ThermalRunawayModel:
    """Simplified thermal runaway model for safety analysis."""

    def __init__(self, params: ThermalRunawayParams):
        self.params = params

    def check_trigger_conditions(
        self,
        temperature_k: np.ndarray,
        voltage_v: np.ndarray,
        current_a: float,
    ) -> Tuple[bool, List[int]]:
        """Check if thermal runaway trigger conditions are met.

        Args:
                temperature_k: Array of cell temperatures (K)
                voltage_v: Array of cell voltages (V)
                current_a: Pack current (A)

        Returns:
                Tuple of (triggered, list of triggered cell indices)
        """
        triggered_cells = []

        # Temperature trigger
        temp_triggered = temperature_k > self.params.T_trigger_k
        triggered_cells.extend(np.where(temp_triggered)[0].tolist())

        # Voltage abuse triggers
        overcharge = voltage_v > 4.5  # Extreme overcharge
        overdischarge = voltage_v < 2.0  # Extreme overdischarge
        triggered_cells.extend(np.where(overcharge)[0].tolist())
        triggered_cells.extend(np.where(overdischarge)[0].tolist())

        # Current abuse
        if abs(current_a) > 500.0:  # Extreme current
            # All cells at risk
            triggered_cells = list(range(len(temperature_k)))

        return len(triggered_cells) > 0, list(set(triggered_cells))

    def simulate_propagation(
        self,
        initial_cells: List[int],
        num_cells: int,
        cell_spacing_m: float = 0.01,
    ) -> Dict[str, any]:
        """Simulate thermal runaway propagation.

        Args:
                initial_cells: List of cell indices that have triggered
                num_cells: Total number of cells
                cell_spacing_m: Physical spacing between cells (m)

        Returns:
                Dictionary with propagation simulation results
        """
        # Simplified propagation model
        propagation_time_s = cell_spacing_m / self.params.propagation_speed_ms

        affected_cells = set(initial_cells)
        time_points = [0.0]
        affected_counts = [len(affected_cells)]

        t = 0.0
        max_time = 60.0  # Maximum simulation time (s)
        dt = 0.1

        while t < max_time and len(affected_cells) < num_cells:
            t += dt
            # Propagate to adjacent cells
            new_affected = set()
            for cell_idx in affected_cells:
                if cell_idx > 0:
                    new_affected.add(cell_idx - 1)
                if cell_idx < num_cells - 1:
                    new_affected.add(cell_idx + 1)

            affected_cells.update(new_affected)
            time_points.append(t)
            affected_counts.append(len(affected_cells))

            if len(affected_cells) >= num_cells:
                break

        return {
            "time_s": np.array(time_points),
            "affected_cells": np.array(affected_counts),
            "total_energy_released_wh": len(affected_cells) * self.params.energy_release_wh_per_cell,
            "full_propagation_time_s": time_points[-1] if time_points else None,
        }


class SafetyAnalyzer:
    """Safety analysis and failure mode evaluation."""

    def __init__(
        self,
        runaway_params: ThermalRunawayParams,
        safety_limits: SafetyLimits,
    ):
        self.runaway = ThermalRunawayModel(runaway_params)
        self.limits = safety_limits

    def analyze_operating_conditions(
        self,
        voltage_v: float,
        current_a: float,
        temperature_k: float,
        soc: float,
        cell_count: int = 1,
    ) -> SafetyAnalysisResult:
        """Analyze safety of operating conditions.

        Args:
                voltage_v: Pack voltage (V)
                current_a: Pack current (A)
                temperature_k: Pack temperature (K)
                soc: State of charge [0-1]
                cell_count: Number of cells in series

        Returns:
                SafetyAnalysisResult with failure probabilities and safety metrics
        """
        V_cell = voltage_v / max(1, cell_count)

        # Check each failure mode
        failure_modes = {}

        # Thermal runaway risk
        if temperature_k > self.runaway.params.T_trigger_k:
            risk_temp = min(1.0, (temperature_k - self.runaway.params.T_trigger_k) / 50.0)
            failure_modes[FailureMode.THERMAL_RUNAWAY] = risk_temp
        else:
            failure_modes[FailureMode.THERMAL_RUNAWAY] = 0.0

        # Overcharge
        if V_cell > self.limits.V_cell_max_safe_v:
            risk_overcharge = min(1.0, (V_cell - self.limits.V_cell_max_safe_v) / 0.5)
            failure_modes[FailureMode.OVERCHARGE] = risk_overcharge
        else:
            failure_modes[FailureMode.OVERCHARGE] = 0.0

        # Overdischarge
        if V_cell < self.limits.V_cell_min_safe_v:
            risk_overdischarge = min(1.0, (self.limits.V_cell_min_safe_v - V_cell) / 0.5)
            failure_modes[FailureMode.OVERDISCHARGE] = risk_overdischarge
        else:
            failure_modes[FailureMode.OVERDISCHARGE] = 0.0

        # Overheating
        if temperature_k > self.limits.T_max_safe_k:
            risk_overheat = min(1.0, (temperature_k - self.limits.T_max_safe_k) / 50.0)
            failure_modes[FailureMode.OVERHEATING] = risk_overheat
        else:
            failure_modes[FailureMode.OVERHEATING] = 0.0

        # Current abuse
        if abs(current_a) > self.limits.I_max_safe_a:
            risk_current = min(1.0, (abs(current_a) - self.limits.I_max_safe_a) / 500.0)
            failure_modes[FailureMode.CURRENT_ABUSE] = risk_current
        else:
            failure_modes[FailureMode.CURRENT_ABUSE] = 0.0

        # Overall failure probability (simplified - would use more sophisticated model)
        failure_probability = 1.0 - np.prod([1.0 - risk for risk in failure_modes.values()])

        # Safe operating zone
        safe_zone = {
            "voltage_v": (self.limits.V_cell_min_safe_v * cell_count, self.limits.V_cell_max_safe_v * cell_count),
            "current_a": (-self.limits.I_max_safe_a, self.limits.I_max_safe_a),
            "temperature_k": (273.15, self.limits.T_max_safe_k),
            "soc": (self.limits.soc_min_safe, self.limits.soc_max_safe),
        }

        # Hazard index (weighted combination)
        hazard_index = (
            0.4 * failure_modes.get(FailureMode.THERMAL_RUNAWAY, 0.0)
            + 0.2 * failure_modes.get(FailureMode.OVERCHARGE, 0.0)
            + 0.2 * failure_modes.get(FailureMode.OVERHEATING, 0.0)
            + 0.1 * failure_modes.get(FailureMode.CURRENT_ABUSE, 0.0)
            + 0.1 * failure_modes.get(FailureMode.OVERDISCHARGE, 0.0)
        )

        return SafetyAnalysisResult(
            failure_probability=failure_probability,
            failure_modes=failure_modes,
            safe_operating_zone=safe_zone,
            time_to_failure_s=None,  # Would calculate based on abuse conditions
            hazard_index=hazard_index,
        )

    def fmea_analysis(
        self,
        cell_params: CellParams,
        pack_params: PackParams,
        thermal_params: ThermalParams,
    ) -> pd.DataFrame:
        """Perform Failure Mode and Effects Analysis (FMEA).

        Args:
                cell_params: Cell parameters
                pack_params: Pack parameters
                thermal_params: Thermal parameters

        Returns:
                DataFrame with FMEA results
        """
        fmea_data = []

        # Failure modes to analyze
        failure_modes = [
            ("High Resistance", "Cell resistance increases", "Performance degradation", 5, 3, 4),
            ("Capacity Fade", "Cell capacity decreases", "Reduced range", 4, 2, 3),
            ("Thermal Runaway", "Temperature exceeds trigger", "Safety hazard", 10, 2, 10),
            ("Overcharge", "Voltage exceeds safe limit", "Safety hazard", 10, 3, 8),
            ("Overdischarge", "Voltage below safe limit", "Cell damage", 8, 3, 7),
            ("Cooling Failure", "Thermal management fails", "Overheating", 9, 2, 9),
            ("Balancing Failure", "Cells become imbalanced", "Reduced capacity", 6, 3, 5),
        ]

        for failure_mode, description, effect, severity, occurrence, detection in failure_modes:
            rpn = severity * occurrence * detection  # Risk Priority Number
            fmea_data.append(
                {
                    "Failure_Mode": failure_mode,
                    "Description": description,
                    "Effect": effect,
                    "Severity": severity,
                    "Occurrence": occurrence,
                    "Detection": detection,
                    "RPN": rpn,
                }
            )

        df = pd.DataFrame(fmea_data)
        df = df.sort_values("RPN", ascending=False)

        return df
