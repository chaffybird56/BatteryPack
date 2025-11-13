from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class AgingParams:
    capacity_fade_per_ah: float = 2e-5  # fractional loss per Ah throughput
    resistance_growth_per_ah: float = 3e-5  # fractional gain per Ah throughput
    thermal_sensitivity_beta: float = 0.04  # per 10K factor in Arrhenius-like multiplier
    T_ref_k: float = 298.15
    min_capacity_fraction: float = 0.7
    max_resistance_scale: float = 2.5


def arrhenius_multiplier(T_k: float, T_ref_k: float, beta: float) -> float:
    # Simple temperature acceleration factor
    return float(np.exp(beta * (T_k - T_ref_k) / 10.0))


def apply_aging(
    capacity_ah: float, R0_ohm: float, R1_ohm: float, dAh: float, T_k: float, p: AgingParams
) -> tuple[float, float, float]:
    acc = arrhenius_multiplier(T_k, p.T_ref_k, p.thermal_sensitivity_beta)
    cap_new = capacity_ah * (1.0 - p.capacity_fade_per_ah * acc * max(0.0, dAh))
    R0_new = R0_ohm * (1.0 + p.resistance_growth_per_ah * acc * max(0.0, dAh))
    R1_new = R1_ohm * (1.0 + p.resistance_growth_per_ah * 0.5 * acc * max(0.0, dAh))
    cap_new = max(p.min_capacity_fraction * capacity_ah, cap_new)
    R0_new = min(p.max_resistance_scale * R0_ohm, R0_new)
    R1_new = min(p.max_resistance_scale * R1_ohm, R1_new)
    return float(cap_new), float(R0_new), float(R1_new)
