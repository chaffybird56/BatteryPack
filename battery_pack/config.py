from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CellParams:
    capacity_ah: float = 3.0
    R0_ohm: float = 0.0025
    R1_ohm: float = 0.0015
    C1_f: float = 2000.0
    V_min: float = 3.0
    V_max: float = 4.2
    T_ref_k: float = 298.15
    R_temp_coeff_per_k: float = 0.003
    ocv_floor_v: float = 3.0
    ocv_ceiling_v: float = 4.2


@dataclass
class ThermalParams:
    mass_kg: float = 10.0
    Cp_j_per_kgk: float = 900.0
    UA_w_per_k: float = 6.0
    T_ambient_k: float = 298.15
    T_max_k: float = 328.15


@dataclass
class PackParams:
    series_cells: int = 40
    parallel_cells: int = 3
    max_current_a: float = 120.0
    min_soc: float = 0.1
    max_soc: float = 0.9


@dataclass
class LimitsParams:
    voltage_margin_v: float = 0.0
    temp_margin_k: float = 0.0


@dataclass
class SimulationParams:
    dt_s: float = 1.0
    t_total_s: float = 1800.0
    initial_soc: float = 0.8


def default_cell_params() -> CellParams:
    return CellParams()


def default_thermal_params() -> ThermalParams:
    return ThermalParams()


def default_pack_params() -> PackParams:
    return PackParams()


def default_limits_params() -> LimitsParams:
    return LimitsParams()


def default_simulation_params() -> SimulationParams:
    return SimulationParams()
