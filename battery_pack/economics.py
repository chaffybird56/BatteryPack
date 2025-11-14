"""Economic analysis and cost modeling for energy sector applications."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import PackParams


@dataclass
class CostParams:
    """Battery pack cost parameters."""

    cell_cost_per_wh: float = 0.15  # $/Wh at pack level (typical 2024)
    bms_cost_per_cell: float = 5.0  # $/cell for BMS
    packaging_cost_per_cell: float = 2.0  # $/cell for structure
    cooling_cost_per_w: float = 0.50  # $/W cooling capacity
    installation_cost_percent: float = 0.20  # 20% installation overhead
    maintenance_cost_per_year_percent: float = 0.02  # 2% annual maintenance
    replacement_cost_percent: float = 0.30  # 30% replacement cost after EOL


@dataclass
class GridParams:
    """Grid/utility parameters for economic analysis."""

    electricity_price_per_kwh: float = 0.12  # $/kWh retail
    peak_price_per_kwh: float = 0.25  # $/kWh during peak
    off_peak_price_per_kwh: float = 0.08  # $/kWh during off-peak
    demand_charge_per_kw: float = 15.0  # $/kW monthly demand charge
    grid_service_revenue_per_kw: float = 50.0  # $/kW/year for grid services
    capacity_market_price_per_kw_year: float = 100.0  # $/kW/year


@dataclass
class LCOEParams:
    """Levelized Cost of Energy (LCOE) parameters."""

    discount_rate: float = 0.06  # 6% discount rate
    system_lifetime_years: float = 15.0
    cycles_per_year: float = 300.0
    degradation_rate_per_year: float = 0.02  # 2% capacity fade per year
    round_trip_efficiency: float = 0.90  # 90% RTE


@dataclass
class EconomicResult:
    """Economic analysis results."""

    capital_cost_usd: float
    operating_cost_usd_per_year: float
    revenue_usd_per_year: Optional[float]
    net_present_value_usd: float
    levelized_cost_per_kwh: float
    payback_period_years: Optional[float]
    internal_rate_of_return: Optional[float]


class CostModel:
    """Battery pack cost modeling."""

    def __init__(self, cost_params: CostParams):
        self.params = cost_params

    def calculate_capital_cost(
        self,
        pack_params: PackParams,
        cell_capacity_ah: float,
        nominal_voltage_v: float,
        cooling_power_w: float = 5000.0,
    ) -> Dict[str, float]:
        """Calculate battery pack capital costs.

        Args:
                pack_params: Pack configuration
                cell_capacity_ah: Cell capacity (Ah)
                nominal_voltage_v: Nominal pack voltage (V)
                cooling_power_w: Cooling system power (W)

        Returns:
                Dictionary with cost breakdown
        """
        num_cells = pack_params.series_cells * pack_params.parallel_cells
        total_energy_wh = num_cells * cell_capacity_ah * nominal_voltage_v / pack_params.series_cells

        # Cell costs
        cell_cost = total_energy_wh * self.params.cell_cost_per_wh

        # BMS costs
        bms_cost = num_cells * self.params.bms_cost_per_cell

        # Packaging costs
        packaging_cost = num_cells * self.params.packaging_cost_per_cell

        # Cooling costs
        cooling_cost = cooling_power_w * self.params.cooling_cost_per_w

        # Base cost
        base_cost = cell_cost + bms_cost + packaging_cost + cooling_cost

        # Installation overhead
        installation_cost = base_cost * self.params.installation_cost_percent

        # Total capital cost
        total_cost = base_cost + installation_cost

        return {
            "cell_cost_usd": cell_cost,
            "bms_cost_usd": bms_cost,
            "packaging_cost_usd": packaging_cost,
            "cooling_cost_usd": cooling_cost,
            "base_cost_usd": base_cost,
            "installation_cost_usd": installation_cost,
            "total_cost_usd": total_cost,
            "cost_per_kwh": total_cost / (total_energy_wh / 1000.0),
            "cost_per_cell": total_cost / num_cells,
        }

    def calculate_operating_cost(
        self,
        total_energy_wh: float,
        cycles_per_year: float,
        round_trip_efficiency: float = 0.90,
    ) -> Dict[str, float]:
        """Calculate annual operating costs.

        Args:
                total_energy_wh: Total pack energy (Wh)
                cycles_per_year: Number of cycles per year
                round_trip_efficiency: Round-trip efficiency [0-1]
                electricity_price_per_kwh: Electricity price ($/kWh)

        Returns:
                Dictionary with operating cost breakdown
        """
        total_energy_kwh = total_energy_wh / 1000.0

        # Energy losses per cycle
        energy_loss_kwh = total_energy_kwh * (1.0 - round_trip_efficiency)

        # Annual energy losses
        annual_energy_loss_kwh = energy_loss_kwh * cycles_per_year

        # Assume average electricity price
        electricity_price = 0.12  # $/kWh
        energy_cost = annual_energy_loss_kwh * electricity_price

        # Maintenance costs (based on capital cost - would need to pass)
        # maintenance_cost = capital_cost * self.params.maintenance_cost_per_year_percent

        return {
            "energy_loss_kwh_per_year": annual_energy_loss_kwh,
            "energy_cost_usd_per_year": energy_cost,
            # "maintenance_cost_usd_per_year": maintenance_cost,
            # "total_operating_cost_usd_per_year": energy_cost + maintenance_cost,
        }


class LCOECalculator:
    """Levelized Cost of Energy (LCOE) calculator."""

    def __init__(self, lcoe_params: LCOEParams):
        self.params = lcoe_params

    def calculate_lcoe(
        self,
        capital_cost_usd: float,
        operating_cost_usd_per_year: float,
        annual_energy_kwh: float,
        degradation_rate: Optional[float] = None,
    ) -> Dict[str, float]:
        """Calculate Levelized Cost of Energy (LCOE).

        Args:
                capital_cost_usd: Initial capital cost ($)
                operating_cost_usd_per_year: Annual operating cost ($)
                annual_energy_kwh: Annual energy throughput (kWh)
                degradation_rate: Annual capacity degradation rate (optional)

        Returns:
                Dictionary with LCOE results
        """
        if degradation_rate is None:
            degradation_rate = self.params.degradation_rate_per_year

        years = self.params.system_lifetime_years
        discount_rate = self.params.discount_rate

        # Calculate discounted costs
        pv_capital = capital_cost_usd

        pv_operating = 0.0
        pv_energy = 0.0

        for year in range(1, int(years) + 1):
            # Degraded capacity
            capacity_factor = (1.0 - degradation_rate) ** (year - 1)
            energy_year = annual_energy_kwh * capacity_factor

            # Discounted values
            discount_factor = 1.0 / ((1.0 + discount_rate) ** year)
            pv_operating += operating_cost_usd_per_year * discount_factor
            pv_energy += energy_year * discount_factor

        # LCOE = (PV capital + PV operating) / PV energy
        lcoe = (pv_capital + pv_operating) / max(1e-6, pv_energy)

        # Net Present Value (simplified)
        npv = -pv_capital - pv_operating  # Negative = cost

        return {
            "lcoe_usd_per_kwh": lcoe,
            "npv_usd": npv,
            "pv_capital_usd": pv_capital,
            "pv_operating_usd": pv_operating,
            "pv_energy_kwh": pv_energy,
        }


class GridEconomics:
    """Grid integration and V2G economic analysis."""

    def __init__(self, grid_params: GridParams):
        self.params = grid_params

    def calculate_arbitrage_revenue(
        self,
        pack_energy_kwh: float,
        round_trip_efficiency: float = 0.90,
        cycles_per_day: int = 1,
    ) -> Dict[str, float]:
        """Calculate energy arbitrage revenue.

        Args:
                pack_energy_kwh: Pack energy capacity (kWh)
                round_trip_efficiency: Round-trip efficiency [0-1]
                cycles_per_day: Number of charge/discharge cycles per day

        Returns:
                Dictionary with revenue breakdown
        """
        # Charge during off-peak, discharge during peak
        price_difference = self.params.peak_price_per_kwh - self.params.off_peak_price_per_kwh

        # Energy available for discharge (accounting for losses)
        discharge_energy_kwh = pack_energy_kwh * round_trip_efficiency

        # Revenue per cycle
        revenue_per_cycle = discharge_energy_kwh * price_difference

        # Annual revenue
        annual_revenue = revenue_per_cycle * cycles_per_day * 365.0

        # Energy cost (charging)
        annual_energy_cost = pack_energy_kwh * self.params.off_peak_price_per_kwh * cycles_per_day * 365.0

        # Net revenue
        net_revenue = annual_revenue - annual_energy_cost

        return {
            "revenue_per_cycle_usd": revenue_per_cycle,
            "annual_revenue_usd": annual_revenue,
            "annual_energy_cost_usd": annual_energy_cost,
            "net_revenue_usd_per_year": net_revenue,
        }

    def calculate_grid_service_revenue(
        self,
        pack_power_kw: float,
        utilization_hours_per_year: float = 500.0,
    ) -> Dict[str, float]:
        """Calculate grid service revenue (frequency regulation, spinning reserve).

        Args:
                pack_power_kw: Pack power rating (kW)
                utilization_hours_per_year: Hours per year providing grid services

        Returns:
                Dictionary with revenue breakdown
        """
        # Capacity market revenue
        capacity_revenue = pack_power_kw * self.params.capacity_market_price_per_kw_year

        # Grid service revenue
        service_revenue = (
            pack_power_kw * self.params.grid_service_revenue_per_kw * (utilization_hours_per_year / 8760.0)
        )

        # Total revenue
        total_revenue = capacity_revenue + service_revenue

        return {
            "capacity_revenue_usd_per_year": capacity_revenue,
            "service_revenue_usd_per_year": service_revenue,
            "total_revenue_usd_per_year": total_revenue,
        }

    def calculate_v2g_revenue(
        self,
        pack_energy_kwh: float,
        pack_power_kw: float,
        vehicles_in_fleet: int = 100,
        utilization_rate: float = 0.3,  # 30% of fleet participates
        hours_per_day: float = 8.0,  # 8 hours per day available
    ) -> Dict[str, float]:
        """Calculate Vehicle-to-Grid (V2G) revenue.

        Args:
                pack_energy_kwh: Pack energy capacity (kWh)
                pack_power_kw: Pack power rating (kW)
                vehicles_in_fleet: Number of vehicles in fleet
                utilization_rate: Fraction of fleet participating
                hours_per_day: Hours per day available for V2G

        Returns:
                Dictionary with V2G revenue breakdown
        """
        participating_vehicles = vehicles_in_fleet * utilization_rate

        # Aggregate power and energy
        total_power_kw = participating_vehicles * pack_power_kw
        total_energy_kwh = participating_vehicles * pack_energy_kwh

        # Revenue from grid services
        grid_service = self.calculate_grid_service_revenue(
            total_power_kw,
            utilization_hours_per_year=hours_per_day * 365.0,
        )

        # Revenue from arbitrage
        arbitrage = self.calculate_arbitrage_revenue(
            pack_energy_kwh,
            cycles_per_day=int(hours_per_day / 2.0),
        )

        # Scale arbitrage by number of vehicles
        arbitrage["annual_revenue_usd"] *= participating_vehicles
        arbitrage["net_revenue_usd_per_year"] *= participating_vehicles

        return {
            "participating_vehicles": participating_vehicles,
            "total_power_kw": total_power_kw,
            "total_energy_kwh": total_energy_kwh,
            "grid_service_revenue_usd_per_year": grid_service["total_revenue_usd_per_year"],
            "arbitrage_revenue_usd_per_year": arbitrage["net_revenue_usd_per_year"],
            "total_revenue_usd_per_year": (
                grid_service["total_revenue_usd_per_year"] + arbitrage["net_revenue_usd_per_year"]
            ),
        }
