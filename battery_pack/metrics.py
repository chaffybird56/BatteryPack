"""Comprehensive battery metrics and analytics for engineering analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass
class BatteryMetrics:
    """Comprehensive battery performance metrics."""

    # Energy metrics
    energy_throughput_wh: float
    round_trip_efficiency_percent: float
    energy_loss_wh: float

    # Power metrics
    peak_power_w: float
    avg_power_w: float
    power_density_w_per_kg: float

    # Temperature metrics
    peak_temperature_k: float
    avg_temperature_k: float
    temp_rise_k: float
    temp_variance_k: float

    # Voltage metrics
    min_voltage_v: float
    max_voltage_v: float
    voltage_sag_v: float
    voltage_variance_v: float

    # Current metrics
    peak_current_a: float
    avg_current_a: float
    rms_current_a: float

    # SOC metrics
    initial_soc: float
    final_soc: float
    soc_used: float
    soc_range: Tuple[float, float]

    # Capacity metrics
    capacity_ah: float
    usable_capacity_ah: float
    capacity_utilization_percent: float

    # Performance metrics
    c_rate_avg: float  # Average C-rate
    c_rate_peak: float  # Peak C-rate

    # Lifetime metrics
    equivalent_full_cycles: float
    throughput_ah: float
    degradation_estimate_percent: Optional[float] = None


def calculate_comprehensive_metrics(
    simulation_data: pd.DataFrame,
    pack_energy_wh: float,
    pack_mass_kg: float,
    initial_soc: float,
    capacity_ah: float,
) -> BatteryMetrics:
    """Calculate comprehensive battery metrics from simulation data.

    Args:
            simulation_data: Simulation results DataFrame
            pack_energy_wh: Total pack energy (Wh)
            pack_mass_kg: Pack mass (kg)
            initial_soc: Initial state of charge [0-1]
            capacity_ah: Cell capacity (Ah)

    Returns:
            BatteryMetrics object with all calculated metrics
    """
    # Energy metrics
    power_w = simulation_data["power_w"].to_numpy()
    time_s = simulation_data["time_s"].to_numpy()

    # Energy throughput (discharge)
    energy_discharge_wh = float(np.trapz(np.maximum(power_w, 0.0), time_s) / 3600.0)
    # Energy input (charge)
    energy_charge_wh = float(np.trapz(np.minimum(power_w, 0.0), time_s) / 3600.0)

    energy_throughput_wh = energy_discharge_wh + energy_charge_wh
    energy_loss_wh = abs(energy_charge_wh) - energy_discharge_wh

    round_trip_efficiency = 100.0 * energy_discharge_wh / abs(energy_charge_wh) if abs(energy_charge_wh) > 1e-6 else 0.0

    # Power metrics
    peak_power_w = float(np.abs(power_w).max())
    avg_power_w = float(np.abs(power_w).mean())
    power_density_w_per_kg = peak_power_w / max(1e-6, pack_mass_kg)

    # Temperature metrics
    temp_k = simulation_data["temp_k"].to_numpy()
    peak_temp_k = float(temp_k.max())
    avg_temp_k = float(temp_k.mean())
    temp_rise_k = float(peak_temp_k - temp_k[0])
    temp_variance_k = float(temp_k.std())

    # Voltage metrics
    voltage_v = simulation_data["v_pack_v"].to_numpy()
    min_voltage_v = float(voltage_v.min())
    max_voltage_v = float(voltage_v.max())
    voltage_sag_v = float(max_voltage_v - min_voltage_v)
    voltage_variance_v = float(voltage_v.std())

    # Current metrics
    current_a = simulation_data["i_pack_a"].to_numpy()
    peak_current_a = float(np.abs(current_a).max())
    avg_current_a = float(np.abs(current_a).mean())
    rms_current_a = float(np.sqrt(np.mean(current_a**2)))

    # SOC metrics
    soc = simulation_data["soc"].to_numpy()
    initial_soc_val = float(soc[0])
    final_soc_val = float(soc[-1])
    soc_used = abs(final_soc_val - initial_soc_val)
    soc_range = (float(soc.min()), float(soc.max()))

    # Capacity metrics
    usable_capacity_ah = capacity_ah * (soc_range[1] - soc_range[0])
    capacity_utilization = 100.0 * soc_used / max(1e-6, (soc_range[1] - soc_range[0]))

    # C-rate metrics
    c_rate_avg = avg_current_a / max(1e-6, capacity_ah)
    c_rate_peak = peak_current_a / max(1e-6, capacity_ah)

    # Lifetime metrics
    throughput_ah = float(np.trapz(np.abs(current_a), time_s) / 3600.0)
    equivalent_full_cycles = throughput_ah / max(1e-6, capacity_ah)

    return BatteryMetrics(
        energy_throughput_wh=energy_throughput_wh,
        round_trip_efficiency_percent=round_trip_efficiency,
        energy_loss_wh=energy_loss_wh,
        peak_power_w=peak_power_w,
        avg_power_w=avg_power_w,
        power_density_w_per_kg=power_density_w_per_kg,
        peak_temperature_k=peak_temp_k,
        avg_temperature_k=avg_temp_k,
        temp_rise_k=temp_rise_k,
        temp_variance_k=temp_variance_k,
        min_voltage_v=min_voltage_v,
        max_voltage_v=max_voltage_v,
        voltage_sag_v=voltage_sag_v,
        voltage_variance_v=voltage_variance_v,
        peak_current_a=peak_current_a,
        avg_current_a=avg_current_a,
        rms_current_a=rms_current_a,
        initial_soc=initial_soc_val,
        final_soc=final_soc_val,
        soc_used=soc_used,
        soc_range=soc_range,
        capacity_ah=capacity_ah,
        usable_capacity_ah=usable_capacity_ah,
        capacity_utilization_percent=capacity_utilization,
        c_rate_avg=c_rate_avg,
        c_rate_peak=c_rate_peak,
        equivalent_full_cycles=equivalent_full_cycles,
        throughput_ah=throughput_ah,
        degradation_estimate_percent=None,
    )


def calculate_statistical_summary(
    data: pd.DataFrame | np.ndarray,
    metrics: List[str] = None,
) -> pd.DataFrame:
    """Calculate statistical summary of simulation data.

    Args:
            data: Simulation data DataFrame or array
            metrics: List of metrics to calculate (default: all)

    Returns:
            DataFrame with statistical summary
    """
    if isinstance(data, np.ndarray):
        data = pd.DataFrame(data)

    if metrics is None:
        metrics = ["mean", "std", "min", "max", "p25", "p50", "p75", "p95", "p99"]

    summary_stats = {}
    for col in data.columns:
        if data[col].dtype in (np.float64, np.float32, np.int64, np.int32):
            stats = {}
            if "mean" in metrics:
                stats["mean"] = data[col].mean()
            if "std" in metrics:
                stats["std"] = data[col].std()
            if "min" in metrics:
                stats["min"] = data[col].min()
            if "max" in metrics:
                stats["max"] = data[col].max()
            if "p25" in metrics:
                stats["p25"] = data[col].quantile(0.25)
            if "p50" in metrics:
                stats["p50"] = data[col].median()
            if "p75" in metrics:
                stats["p75"] = data[col].quantile(0.75)
            if "p95" in metrics:
                stats["p95"] = data[col].quantile(0.95)
            if "p99" in metrics:
                stats["p99"] = data[col].quantile(0.99)

            summary_stats[col] = stats

    return pd.DataFrame(summary_stats).T


def calculate_cycle_life_estimate(
    throughput_ah: float,
    capacity_ah: float,
    degradation_per_cycle_percent: float = 0.05,
    capacity_fade_limit_percent: float = 20.0,
) -> Dict[str, float]:
    """Estimate cycle life from throughput and degradation rate.

    Args:
            throughput_ah: Total throughput (Ah)
            capacity_ah: Nominal capacity (Ah)
            degradation_per_cycle_percent: Degradation per cycle (%)
            capacity_fade_limit_percent: Capacity fade limit (%)

    Returns:
            Dictionary with cycle life estimates
    """
    cycles_completed = throughput_ah / max(1e-6, capacity_ah)

    # Linear degradation model (simplified)
    cycles_to_eol = capacity_fade_limit_percent / max(1e-6, degradation_per_cycle_percent)

    # Remaining cycles
    remaining_cycles = max(0.0, cycles_to_eol - cycles_completed)

    # Remaining capacity
    current_capacity_percent = 100.0 - (cycles_completed / max(1e-6, cycles_to_eol)) * capacity_fade_limit_percent
    current_capacity_percent = max(0.0, min(100.0, current_capacity_percent))

    return {
        "cycles_completed": cycles_completed,
        "cycles_to_eol": cycles_to_eol,
        "remaining_cycles": remaining_cycles,
        "current_capacity_percent": current_capacity_percent,
        "capacity_fade_percent": 100.0 - current_capacity_percent,
    }
