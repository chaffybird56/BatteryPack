from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
import pandas as pd


@dataclass
class DriveCycle:
    time_s: np.ndarray
    current_a: np.ndarray  # positive = discharge


def synthetic_cycle(
    t_total_s: float,
    dt_s: float,
    peak_current_a: float = 80.0,
    seed: int = 42,
) -> DriveCycle:
    """Generate a UDDS-like current profile with bursts and regen pulses."""
    rng = np.random.default_rng(seed)
    n = int(np.round(t_total_s / dt_s)) + 1
    t = np.arange(n) * dt_s
    # Create a random walk of accelerations mapped to current
    acc = rng.normal(0.0, 1.0, size=n)
    acc = pd.Series(acc).rolling(window=25, min_periods=1, center=True).mean().to_numpy()
    acc = np.clip(acc, -2.5, 3.0)
    I = peak_current_a * acc / 3.0
    # Mix in idling and braking regens
    mask_idle = rng.random(n) < 0.25
    I[mask_idle] *= 0.15
    mask_brake = rng.random(n) < 0.10
    I[mask_brake] = -0.5 * peak_current_a * rng.random(np.count_nonzero(mask_brake))
    # Smooth
    I = pd.Series(I).rolling(window=10, min_periods=1, center=True).mean().to_numpy()
    return DriveCycle(time_s=t, current_a=I.astype(float))


def from_dataframe(df: pd.DataFrame, time_col: str = "time_s", current_col: str = "current_a") -> DriveCycle:
    t = df[time_col].to_numpy(dtype=float)
    I = df[current_col].to_numpy(dtype=float)
    return DriveCycle(time_s=t, current_a=I)
