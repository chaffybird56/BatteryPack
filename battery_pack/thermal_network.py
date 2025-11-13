from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class ThermalNetworkParams:
    num_nodes: int
    mass_kg_total: float
    Cp_j_per_kgk: float
    cell_to_cell_w_per_k: float = 0.5
    cell_to_sink_w_per_k: float = 4.0
    sink_temperature_k: float = 298.15
    mode: str = "air"  # "air" | "fin" | "pcm" | "liquid"


class ThermalNetwork:
    """1D chain thermal network with per-node heat inputs and a global sink.

    Nodes are arranged in a line (cells/segments in series). Each node exchanges heat with
    its immediate neighbors via `cell_to_cell_w_per_k` and to an external sink via
    `cell_to_sink_w_per_k` adjusted by `mode`.
    """

    def __init__(self, params: ThermalNetworkParams):
        self.p = params
        self.num_nodes = int(params.num_nodes)
        self.mass_per_node_kg = float(params.mass_kg_total) / max(1, self.num_nodes)
        self.Cp = params.Cp_j_per_kgk
        self.T = np.full(self.num_nodes, float(params.sink_temperature_k), dtype=float)
        self._g_sink = self._mode_sink_conductance(params.mode, params.cell_to_sink_w_per_k)

    def reset(self, temperature_k: float | None = None) -> None:
        self.T[:] = float(temperature_k if temperature_k is not None else self.p.sink_temperature_k)

    def _mode_sink_conductance(self, mode: str, base: float) -> float:
        m = (mode or "air").lower()
        if m == "air":
            return base
        if m == "fin":
            return 2.5 * base
        if m == "pcm":
            return 4.0 * base
        if m == "liquid":
            return 6.0 * base
        return base

    def step(self, heat_w: np.ndarray, dt_s: float) -> np.ndarray:
        T = self.T
        n = self.num_nodes
        g_cc = self.p.cell_to_cell_w_per_k
        g_sink = self._g_sink
        T_sink = self.p.sink_temperature_k
        mC = self.mass_per_node_kg * self.Cp

        dTdt = np.zeros_like(T)
        for i in range(n):
            q = float(heat_w[i]) if i < heat_w.shape[0] else 0.0
            neighbors = 0.0
            if i > 0:
                neighbors += g_cc * (T[i - 1] - T[i])
            if i < n - 1:
                neighbors += g_cc * (T[i + 1] - T[i])
            sink_term = g_sink * (T_sink - T[i])
            dTdt[i] = (q + neighbors + sink_term) / max(1e-9, mC)

        self.T = (T + dt_s * dTdt).astype(float)
        return self.T
