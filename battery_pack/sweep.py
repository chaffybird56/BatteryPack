from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tqdm import tqdm

from .config import (
    CellParams,
    PackParams,
    SimulationParams,
    ThermalParams,
)
from .drive_cycles import DriveCycle, synthetic_cycle
from .pack import BatteryPack
from .simulation import Simulator


def _run_single_sweep_point(
    Ns: int,
    Np: int,
    UA: float,
    peak: float,
    sim: SimulationParams,
    cell: CellParams,
    thermal: ThermalParams,
) -> Dict:
    """Run a single sweep point (for parallel processing)."""
    p = PackParams(series_cells=Ns, parallel_cells=Np, max_current_a=thermal_sensitive_current_limit(Ns, Np, peak))
    th = ThermalParams(
        mass_kg=thermal.mass_kg,
        Cp_j_per_kgk=thermal.Cp_j_per_kgk,
        UA_w_per_k=UA,
        T_ambient_k=thermal.T_ambient_k,
        T_max_k=thermal.T_max_k,
    )
    pack = BatteryPack(cell_params=cell, pack_params=p, thermal_params=th, initial_soc=sim.initial_soc)
    cycle = synthetic_cycle(t_total_s=sim.t_total_s, dt_s=sim.dt_s, peak_current_a=peak)
    SimulatorObj = Simulator(pack, sim)
    res = SimulatorObj.run(cycle)
    peak_temp_k = float(res["temp_k"].max())
    # Compute RTE on the same cycle from starting SOC
    RTEres = SimulatorObj.round_trip_efficiency(cycle, initial_soc=sim.initial_soc)
    viol_temp = peak_temp_k > th.T_max_k + 1e-6
    viol_soc = bool((res["soc"].min() < 0.1) or (res["soc"].max() > 0.9))
    return {
        "Ns": Ns,
        "Np": Np,
        "UA_w_per_k": UA,
        "peak_current_a": peak,
        "peak_temp_k": peak_temp_k,
        "RTE_percent": RTEres.RTE_percent,
        "energy_out_wh": RTEres.energy_out_wh,
        "energy_in_wh": RTEres.energy_in_wh,
        "viol_temp": int(viol_temp),
        "viol_soc": int(viol_soc),
    }


def run_parameter_sweep(
    series_list: Iterable[int],
    parallel_list: Iterable[int],
    UA_list: Iterable[float],
    peak_current_list: Iterable[float],
    sim: SimulationParams,
    cell: CellParams,
    thermal: ThermalParams,
    n_jobs: int = -1,
    show_progress: bool = True,
) -> pd.DataFrame:
    """Run parameter sweep with parallel processing.

    Args:
            series_list: List of series cell counts
            parallel_list: List of parallel cell counts
            UA_list: List of thermal conductances (W/K)
            peak_current_list: List of peak currents (A)
            sim: Simulation parameters
            cell: Cell parameters
            thermal: Thermal parameters
            n_jobs: Number of parallel jobs (-1 for all cores)
            show_progress: Show progress bar

    Returns:
            DataFrame with sweep results
    """
    # Generate all parameter combinations
    param_combinations = list(product(series_list, parallel_list, UA_list, peak_current_list))

    # Run in parallel
    if show_progress:
        results = Parallel(n_jobs=n_jobs)(
            delayed(_run_single_sweep_point)(Ns, Np, UA, peak, sim, cell, thermal)
            for Ns, Np, UA, peak in tqdm(param_combinations, desc="Running sweep")
        )
    else:
        results = Parallel(n_jobs=n_jobs)(
            delayed(_run_single_sweep_point)(Ns, Np, UA, peak, sim, cell, thermal)
            for Ns, Np, UA, peak in param_combinations
        )

    return pd.DataFrame(results)


def thermal_sensitive_current_limit(Ns: int, Np: int, peak: float) -> float:
    # Keep peak bounded by a simple rule of thumb
    return float(min(peak, 300.0 * Np))
