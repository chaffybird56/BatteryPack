from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from .config import CellParams


@dataclass
class VariationParams:
	std_capacity_frac: float = 0.02
	std_R0_frac: float = 0.05
	std_R1_frac: float = 0.05
	seed: int = 123


def make_varied_cells(base: CellParams, Ns: int, vp: VariationParams) -> List[CellParams]:
	rng = np.random.default_rng(vp.seed)
	cap_scale = (1.0 + rng.normal(0.0, vp.std_capacity_frac, size=Ns)).astype(float)
	R0_scale = (1.0 + rng.normal(0.0, vp.std_R0_frac, size=Ns)).astype(float)
	R1_scale = (1.0 + rng.normal(0.0, vp.std_R1_frac, size=Ns)).astype(float)
	cells: List[CellParams] = []
	for i in range(Ns):
		c = CellParams(
			capacity_ah=float(base.capacity_ah * cap_scale[i]),
			R0_ohm=float(base.R0_ohm * R0_scale[i]),
			R1_ohm=float(base.R1_ohm * R1_scale[i]),
			C1_f=base.C1_f,
			V_min=base.V_min,
			V_max=base.V_max,
			T_ref_k=base.T_ref_k,
			R_temp_coeff_per_k=base.R_temp_coeff_per_k,
			ocv_floor_v=base.ocv_floor_v,
			ocv_ceiling_v=base.ocv_ceiling_v,
		)
		cells.append(c)
	return cells


@dataclass
class BalancingParams:
	enable: bool = True
	bleed_current_a: float = 0.2
	idle_current_threshold_a: float = 2.0
	soc_over_delta: float = 0.01


def apply_passive_balancing(soc: np.ndarray, capacity_ah: np.ndarray, pack_current_a: float, dt_s: float, bp: BalancingParams) -> np.ndarray:
	if not bp.enable or abs(pack_current_a) > bp.idle_current_threshold_a:
		return soc
	mean_soc = float(soc.mean())
	next_soc = soc.copy()
	for i in range(soc.shape[0]):
		if soc[i] > mean_soc + bp.soc_over_delta:
			dsoc = (bp.bleed_current_a * dt_s) / max(1e-9, capacity_ah[i] * 3600.0)
			next_soc[i] = max(0.0, soc[i] - dsoc)
	return next_soc.astype(float)

