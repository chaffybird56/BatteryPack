from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np

from .aging import AgingParams, apply_aging
from .cell import CellECM
from .config import CellParams, PackParams, ThermalParams
from .pybamm_adapter import OCVLookup, try_generate_ocv_curve
from .thermal_network import ThermalNetwork, ThermalNetworkParams
from .variation import BalancingParams, VariationParams, apply_passive_balancing, make_varied_cells


@dataclass
class AdvancedPackParams:
    thermal_mode: str = "air"  # "air" | "fin" | "pcm" | "liquid"
    use_pybamm_ocv: bool = False
    variation: VariationParams = field(default_factory=VariationParams)
    balancing: BalancingParams = field(default_factory=BalancingParams)
    aging: AgingParams = field(default_factory=AgingParams)


class BatteryPackAdvanced:
    """Series pack with per-cell variation, multi-node thermal, aging, and balancing.

    Parallels (Np) are modeled as identical strings; heat scales by Np.
    """

    def __init__(
        self,
        cell_base: CellParams,
        pack_params: PackParams,
        thermal_params: ThermalParams,
        adv: AdvancedPackParams,
        initial_soc: float = 0.8,
    ):
        self.pp = pack_params
        self.tp = thermal_params
        self.adv = adv

        self.Ns = int(pack_params.series_cells)
        self.Np = int(pack_params.parallel_cells)

        # Per-cell varied parameters and ECMs
        self.cell_params: List[CellParams] = make_varied_cells(cell_base, self.Ns, adv.variation)
        self.cells: List[CellECM] = [CellECM(p) for p in self.cell_params]

        # Optional PyBaMM OCV lookup
        self._ocv_lookup: OCVLookup | None = None
        if adv.use_pybamm_ocv:
            ocv = try_generate_ocv_curve()
            if ocv is not None:
                self._ocv_lookup = OCVLookup(ocv.soc, ocv.ocv_v)

        # States
        self.soc = np.full(self.Ns, float(np.clip(initial_soc, 0.0, 1.0)))
        self.V_rc1 = np.zeros(self.Ns, dtype=float)
        self.throughput_ah = np.zeros(self.Ns, dtype=float)

        # Thermal network
        net_params = ThermalNetworkParams(
            num_nodes=self.Ns,
            mass_kg_total=self.tp.mass_kg,
            Cp_j_per_kgk=self.tp.Cp_j_per_kgk,
            cell_to_cell_w_per_k=0.5,
            cell_to_sink_w_per_k=self.tp.UA_w_per_k,
            sink_temperature_k=self.tp.T_ambient_k,
            mode=adv.thermal_mode,
        )
        self.thermal = ThermalNetwork(net_params)

    def reset(self, initial_soc: float) -> None:
        self.soc[:] = float(np.clip(initial_soc, 0.0, 1.0))
        self.V_rc1[:] = 0.0
        self.throughput_ah[:] = 0.0
        self.thermal.reset(self.tp.T_ambient_k)

    def _ocv(self, i: int, soc: float) -> float:
        if self._ocv_lookup is not None:
            return self._ocv_lookup(soc)
        return self.cells[i].ocv(soc)

    def step(self, I_pack_a: float, dt_s: float) -> Dict[str, float]:
        I_cell = float(I_pack_a) / max(1, self.Np)
        V_cells = np.zeros(self.Ns, dtype=float)
        Q_nodes = np.zeros(self.Ns, dtype=float)

        for i in range(self.Ns):
            cell = self.cells[i]
            # Update ECM state (with current per string)
            R0, R1 = cell.temperature_adjusted_resistances(self.thermal.T[i])
            # Semi-analytic update for RC branch and SOC using cell.params but with ocv override
            # Use cell.step and then replace OCV if PyBaMM lookup provided
            V_term, Vrc_next, soc_next = cell.step_voltage_states(
                I_cell, dt_s, self.V_rc1[i], self.thermal.T[i], self.soc[i]
            )
            if self._ocv_lookup is not None:
                # Recompute terminal voltage using lookup OCV and updated states
                V_term = self._ocv_lookup(soc_next) - R0 * I_cell - Vrc_next

            V_cells[i] = V_term
            self.V_rc1[i] = Vrc_next
            self.soc[i] = soc_next

            # Joule heat per node scaled by Np parallel strings
            Q_nodes[i] = (I_cell**2) * (R0 + R1) * self.Np

        # Passive balancing (applied during low-current periods)
        cap_vec = np.array([c.capacity_ah for c in self.cell_params], dtype=float)
        self.soc = apply_passive_balancing(self.soc, cap_vec, I_pack_a, dt_s, self.adv.balancing)

        # Thermal update
        T_next = self.thermal.step(Q_nodes, dt_s)

        # Aging update by throughput per cell
        dAh = abs(I_cell) * dt_s / 3600.0
        for i in range(self.Ns):
            c = self.cell_params[i]
            cap_new, R0_new, R1_new = apply_aging(
                c.capacity_ah, c.R0_ohm, c.R1_ohm, dAh, self.thermal.T[i], self.adv.aging
            )
            c.capacity_ah = cap_new
            c.R0_ohm = R0_new
            c.R1_ohm = R1_new
            self.throughput_ah[i] += dAh

        V_pack = float(np.sum(V_cells))
        power_w = V_pack * float(I_pack_a)
        return {
            "v_pack_v": V_pack,
            "i_pack_a": float(I_pack_a),
            "soc": float(self.soc.mean()),
            "temp_k": float(self.thermal.T.mean()),
            "temp_max_k": float(self.thermal.T.max()),
            "power_w": power_w,
        }
