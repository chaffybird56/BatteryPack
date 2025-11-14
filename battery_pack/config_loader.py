"""Configuration loading from YAML/JSON files for flexible parameter management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import yaml

from .config import (
    CellParams,
    LimitsParams,
    PackParams,
    SimulationParams,
    ThermalParams,
)


class ConfigLoader:
    """Load simulation parameters from YAML or JSON configuration files."""

    @staticmethod
    def load_from_file(config_path: Path | str) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file.

        Args:
                config_path: Path to configuration file (.yaml, .yml, or .json)

        Returns:
                Dictionary containing configuration sections

        Raises:
                FileNotFoundError: If config file doesn't exist
                ValueError: If file format is unsupported or invalid
        """
        config_path = Path(config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_path, "r") as f:
            if config_path.suffix.lower() in (".yaml", ".yml"):
                config = yaml.safe_load(f)
            elif config_path.suffix.lower() == ".json":
                config = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {config_path.suffix}. Use .yaml or .json")

        if config is None:
            raise ValueError(f"Configuration file is empty: {config_path}")

        return config

    @staticmethod
    def parse_cell_params(config: Dict[str, Any]) -> CellParams:
        """Parse cell parameters from config dictionary."""
        cell_config = config.get("cell", {})
        return CellParams(
            capacity_ah=cell_config.get("capacity_ah", 3.0),
            R0_ohm=cell_config.get("R0_ohm", 0.0025),
            R1_ohm=cell_config.get("R1_ohm", 0.0015),
            C1_f=cell_config.get("C1_f", 2000.0),
            V_min=cell_config.get("V_min", 3.0),
            V_max=cell_config.get("V_max", 4.2),
            T_ref_k=cell_config.get("T_ref_k", 298.15),
            R_temp_coeff_per_k=cell_config.get("R_temp_coeff_per_k", 0.003),
            ocv_floor_v=cell_config.get("ocv_floor_v", 3.0),
            ocv_ceiling_v=cell_config.get("ocv_ceiling_v", 4.2),
        )

    @staticmethod
    def parse_thermal_params(config: Dict[str, Any]) -> ThermalParams:
        """Parse thermal parameters from config dictionary."""
        thermal_config = config.get("thermal", {})
        return ThermalParams(
            mass_kg=thermal_config.get("mass_kg", 10.0),
            Cp_j_per_kgk=thermal_config.get("Cp_j_per_kgk", 900.0),
            UA_w_per_k=thermal_config.get("UA_w_per_k", 6.0),
            T_ambient_k=thermal_config.get("T_ambient_k", 298.15),
            T_max_k=thermal_config.get("T_max_k", 328.15),
        )

    @staticmethod
    def parse_pack_params(config: Dict[str, Any]) -> PackParams:
        """Parse pack parameters from config dictionary."""
        pack_config = config.get("pack", {})
        return PackParams(
            series_cells=pack_config.get("series_cells", 40),
            parallel_cells=pack_config.get("parallel_cells", 3),
            max_current_a=pack_config.get("max_current_a", 120.0),
            min_soc=pack_config.get("min_soc", 0.1),
            max_soc=pack_config.get("max_soc", 0.9),
        )

    @staticmethod
    def parse_simulation_params(config: Dict[str, Any]) -> SimulationParams:
        """Parse simulation parameters from config dictionary."""
        sim_config = config.get("simulation", {})
        return SimulationParams(
            dt_s=sim_config.get("dt_s", 1.0),
            t_total_s=sim_config.get("t_total_s", 1800.0),
            initial_soc=sim_config.get("initial_soc", 0.8),
        )

    @staticmethod
    def parse_limits_params(config: Dict[str, Any]) -> LimitsParams:
        """Parse limits parameters from config dictionary."""
        limits_config = config.get("limits", {})
        return LimitsParams(
            voltage_margin_v=limits_config.get("voltage_margin_v", 0.0),
            temp_margin_k=limits_config.get("temp_margin_k", 0.0),
        )

    @classmethod
    def load_all_params(cls, config_path: Path | str) -> Dict[str, Any]:
        """Load all parameter types from a configuration file.

        Returns:
                Dictionary with keys: 'cell', 'thermal', 'pack', 'simulation', 'limits'
        """
        config = cls.load_from_file(config_path)
        return {
            "cell": cls.parse_cell_params(config),
            "thermal": cls.parse_thermal_params(config),
            "pack": cls.parse_pack_params(config),
            "simulation": cls.parse_simulation_params(config),
            "limits": cls.parse_limits_params(config),
        }


def save_config_template(output_path: Path | str) -> None:
    """Save a template configuration file with default values."""
    template = {
        "cell": {
            "capacity_ah": 3.0,
            "R0_ohm": 0.0025,
            "R1_ohm": 0.0015,
            "C1_f": 2000.0,
            "V_min": 3.0,
            "V_max": 4.2,
            "T_ref_k": 298.15,
            "R_temp_coeff_per_k": 0.003,
            "ocv_floor_v": 3.0,
            "ocv_ceiling_v": 4.2,
        },
        "thermal": {
            "mass_kg": 10.0,
            "Cp_j_per_kgk": 900.0,
            "UA_w_per_k": 6.0,
            "T_ambient_k": 298.15,
            "T_max_k": 328.15,
        },
        "pack": {
            "series_cells": 40,
            "parallel_cells": 3,
            "max_current_a": 120.0,
            "min_soc": 0.1,
            "max_soc": 0.9,
        },
        "simulation": {
            "dt_s": 1.0,
            "t_total_s": 1800.0,
            "initial_soc": 0.8,
        },
        "limits": {
            "voltage_margin_v": 0.0,
            "temp_margin_k": 0.0,
        },
    }

    output_path = Path(output_path)
    if output_path.suffix.lower() in (".yaml", ".yml"):
        with open(output_path, "w") as f:
            yaml.dump(template, f, default_flow_style=False, sort_keys=False)
    elif output_path.suffix.lower() == ".json":
        with open(output_path, "w") as f:
            json.dump(template, f, indent=2, sort_keys=False)
    else:
        raise ValueError(f"Unsupported output format: {output_path.suffix}. Use .yaml or .json")
