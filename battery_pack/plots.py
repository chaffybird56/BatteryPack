from __future__ import annotations

from pathlib import Path
from typing import Iterable, Tuple

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

_PALETTE = ["#2E86AB", "#A23B72", "#F18F01", "#C73E1D", "#3B1F2B"]


def apply_plot_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.05)
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "#fafafa",
            "axes.edgecolor": "#cccccc",
            "grid.alpha": 0.35,
            "font.family": "sans-serif",
        }
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def plot_time_series(df: pd.DataFrame, out_dir: Path, title: str = "Pack Time Series") -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, axes = plt.subplots(4, 1, figsize=(8, 6), sharex=True)
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
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(8, 2.5))
    ax.plot(df["time_s"], df["temp_k"] - 273.15, color="#b07aa1")
    ax.set_ylabel("Temp (°C)")
    ax.set_xlabel("Time (s)")
    ax.set_title(title)
    fig.tight_layout()
    path = out_dir / "temperature.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_rte_bar(rte_percent: float, out_dir: Path, title: str = "Round-Trip Efficiency") -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(4, 3))
    ax.bar(["RTE"], [rte_percent], color=_PALETTE[0], width=0.5)
    ax.set_ylim(0, 100)
    ax.set_ylabel("%")
    ax.set_title(title)
    for i, v in enumerate([rte_percent]):
        ax.text(i, v + 1, f"{v:.1f}%", ha="center")
    fig.tight_layout()
    path = out_dir / "rte.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_power_limits(soc_grid: np.ndarray, p_dis: np.ndarray, p_chg: np.ndarray, out_dir: Path) -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(6, 3))
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


def plot_chemistry_rte(labels: list[str], rte_values: list[float], out_dir: Path) -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(6, 3.5))
    colors = [_PALETTE[i % len(_PALETTE)] for i in range(len(labels))]
    bars = ax.bar(labels, rte_values, color=colors)
    ax.set_ylabel("Round-trip efficiency (%)")
    ax.set_ylim(0, max(100, max(rte_values) * 1.15 if rte_values else 100))
    ax.set_title("RTE by cell chemistry (same pack topology)")
    for bar, v in zip(bars, rte_values):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 0.8, f"{v:.1f}%", ha="center", fontsize=9)
    fig.tight_layout()
    path = out_dir / "chemistry_rte.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_safety_hazard(temps_c: np.ndarray, hazard: np.ndarray, trigger_c: float, out_dir: Path) -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.fill_between(temps_c, hazard, alpha=0.25, color=_PALETTE[3])
    ax.plot(temps_c, hazard, color=_PALETTE[3], linewidth=2, label="Hazard index")
    ax.axvline(trigger_c, color="#888888", linestyle="--", linewidth=1.2, label=f"Runaway trigger (~{trigger_c:.0f}°C)")
    ax.set_xlabel("Pack temperature (°C)")
    ax.set_ylabel("Hazard index (0–1)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Thermal runaway risk vs temperature (pre-sign-off gate)")
    ax.legend(loc="upper left")
    fig.tight_layout()
    path = out_dir / "safety_runaway.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def plot_load_profile(
    time_s: np.ndarray, current_a: np.ndarray, out_dir: Path, title: str = "Charge / load profile"
) -> Path:
    apply_plot_style()
    ensure_dir(out_dir)
    fig, ax = plt.subplots(figsize=(8, 2.8))
    ax.plot(time_s, current_a, color=_PALETTE[0], linewidth=1.2)
    ax.axhline(0, color="#999999", linewidth=0.8)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Pack current (A)")
    ax.set_title(title)
    fig.tight_layout()
    path = out_dir / "load_profile.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
