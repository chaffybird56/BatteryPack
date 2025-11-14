from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_time_series(df: pd.DataFrame, out_dir: Path, title: str = "Pack Time Series") -> Path:
    ensure_dir(out_dir)
    fig, axes = plt.subplots(4, 1, figsize=(6.4, 4.8), sharex=True)
    t = df["time_s"].to_numpy()
    axes = axes
    axes[0].plot(t, df["i_pack_a"], label="Current (A)", color="#4e79a7")
    axes[0].set_ylabel("I (A)")
    axes[0].legend(loc="best")

    axes[1].plot(t, df["v_pack_v"], label="Voltage (V)", color="#59a14f")
    axes[1].set_ylabel("V (V)")
    axes[1].legend(loc="best")

    axes[2].plot(t, df["power_w"], label="Power (W)", color="#e15759")
    axes[2].set_ylabel("P (W)")
    axes[2].legend(loc="best")

    axes[3].plot(t, df["soc"], label="SoC", color="#f28e2b")
    axes[3].set_ylabel("SoC")
    axes[3].set_xlabel("Time (s)")
    axes[3].legend(loc="best")

    fig.suptitle(title)
    fig.tight_layout()
    path = out_dir / "time_series.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_temperature(df: pd.DataFrame, out_dir: Path, title: str = "Pack Temperature") -> Path:
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(6.4, 2.0))
    ax.plot(df["time_s"], df["temp_k"] - 273.15, color="#b07aa1")
    ax.set_ylabel("Temp (°C)")
    ax.set_xlabel("Time (s)")
    ax.set_title(title)
    fig.tight_layout()
    path = out_dir / "temperature.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_rte_bar(rte_percent: float, out_dir: Path) -> Path:
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(3.2, 2.4))
    ax.bar(["RTE"], [rte_percent], color="#76b7b2")
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")
    for i, v in enumerate([rte_percent]):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center")
    fig.tight_layout()
    path = out_dir / "rte.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_power_limits(soc_grid: np.ndarray, p_dis: np.ndarray, p_chg: np.ndarray, out_dir: Path) -> Path:
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(4.8, 2.4))
    ax.plot(soc_grid, p_dis / 1000.0, label="Max Discharge", color="#59a14f")
    ax.plot(soc_grid, -p_chg / 1000.0, label="Max Charge", color="#e15759")
    ax.set_xlabel("SoC")
    ax.set_ylabel("Power (kW)")
    ax.legend(loc="best")
    ax.set_title("Power Limits vs SoC")
    fig.tight_layout()
    path = out_dir / "power_limits.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_sweep_heatmap(
    df: pd.DataFrame,
    x: str,
    y: str,
    value: str,
    out_dir: Path,
    title: str,
    cmap: str = "viridis",
) -> Path:
    ensure_dir(out_dir)
    pt = df.pivot_table(index=y, columns=x, values=value, aggfunc="mean")
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(pt, cmap=cmap, ax=ax, cbar_kws={"label": value})
    ax.set_title(title)
    fig.tight_layout()
    path = out_dir / f"heatmap_{x}_vs_{y}_{value}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
