"""Data export capabilities for cloud/enterprise integration (JSON, HDF5, CSV)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import h5py
import json
import numpy as np
import pandas as pd


def export_to_json(
    data: Dict[str, Any] | pd.DataFrame,
    output_path: Path | str,
    pretty: bool = True,
) -> None:
    """Export data to JSON format.

    Args:
            data: Dictionary or DataFrame to export
            output_path: Output file path
            pretty: If True, format with indentation
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, pd.DataFrame):
        # Convert DataFrame to JSON-friendly format
        json_data = {
            "columns": data.columns.tolist(),
            "data": data.values.tolist(),
            "index": data.index.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in data.dtypes.items()},
        }
    else:
        json_data = data

    with open(output_path, "w") as f:
        if pretty:
            json.dump(json_data, f, indent=2, default=str)
        else:
            json.dump(json_data, f, default=str)


def export_to_hdf5(
    data: Dict[str, np.ndarray] | pd.DataFrame,
    output_path: Path | str,
    group: str = "/",
    compression: Optional[str] = "gzip",
) -> None:
    """Export data to HDF5 format (efficient for large datasets).

    Args:
            data: Dictionary of arrays or DataFrame to export
            output_path: Output file path
            group: HDF5 group path (default: root)
            compression: Compression algorithm ("gzip", "lzf", None)
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, pd.DataFrame):
        # Convert DataFrame to HDF5
        data.to_hdf(output_path, key=group, mode="w", format="table", complib=compression)
    else:
        # Write dictionary of arrays
        with h5py.File(output_path, "w") as f:
            grp = f if group == "/" else f.create_group(group)
            for key, value in data.items():
                if isinstance(value, np.ndarray):
                    grp.create_dataset(key, data=value, compression=compression)
                elif isinstance(value, (int, float, str)):
                    grp.attrs[key] = value
                else:
                    # Try to convert to array
                    try:
                        arr = np.array(value)
                        grp.create_dataset(key, data=arr, compression=compression)
                    except Exception:
                        grp.attrs[key] = str(value)


def export_simulation_results(
    results: pd.DataFrame,
    metadata: Dict[str, Any],
    output_dir: Path | str,
    formats: list[str] = ["csv", "json", "hdf5"],
) -> Dict[str, Path]:
    """Export simulation results in multiple formats.

    Args:
            results: Simulation results DataFrame
            metadata: Metadata dictionary (parameters, configuration, etc.)
            output_dir: Output directory
            formats: List of formats to export ("csv", "json", "hdf5")

    Returns:
            Dictionary mapping format names to output paths
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_paths = {}

    if "csv" in formats:
        csv_path = output_dir / "simulation_results.csv"
        results.to_csv(csv_path, index=False)
        output_paths["csv"] = csv_path

    if "json" in formats:
        json_path = output_dir / "simulation_results.json"
        json_data = {
            "metadata": metadata,
            "results": {
                "columns": results.columns.tolist(),
                "data": results.values.tolist(),
            },
        }
        export_to_json(json_data, json_path)
        output_paths["json"] = json_path

    if "hdf5" in formats:
        hdf5_path = output_dir / "simulation_results.h5"
        with h5py.File(hdf5_path, "w") as f:
            # Write results as table
            results.to_hdf(hdf5_path, key="/results", mode="w", format="table")
            # Write metadata as attributes
            meta_grp = f.create_group("/metadata")
            for key, value in metadata.items():
                if isinstance(value, (int, float, str, bool)):
                    meta_grp.attrs[key] = value
                elif isinstance(value, (list, tuple)):
                    meta_grp.create_dataset(key, data=np.array(value))
                elif isinstance(value, dict):
                    # Nested dictionary
                    sub_grp = meta_grp.create_group(key)
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, (int, float, str, bool)):
                            sub_grp.attrs[sub_key] = sub_value
                        else:
                            sub_grp.create_dataset(sub_key, data=np.array(sub_value))

        output_paths["hdf5"] = hdf5_path

    return output_paths


def export_configuration(
    config: Dict[str, Any],
    output_path: Path | str,
    format: str = "json",
) -> None:
    """Export configuration to file.

    Args:
            config: Configuration dictionary
            output_path: Output file path
            format: Export format ("json" or "yaml")
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if format.lower() == "json":
        export_to_json(config, output_path)
    elif format.lower() in ("yaml", "yml"):
        import yaml

        with open(output_path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'json' or 'yaml'")


def load_from_hdf5(file_path: Path | str, group: str = "/") -> Dict[str, np.ndarray]:
    """Load data from HDF5 file.

    Args:
            file_path: HDF5 file path
            group: HDF5 group path

    Returns:
            Dictionary of arrays
    """
    file_path = Path(file_path)
    data = {}

    with h5py.File(file_path, "r") as f:
        grp = f[group] if group != "/" else f

        # Load datasets
        for key in grp.keys():
            if isinstance(grp[key], h5py.Dataset):
                data[key] = grp[key][:]

        # Load attributes
        for key in grp.attrs.keys():
            data[f"attr_{key}"] = grp.attrs[key]

    return data
