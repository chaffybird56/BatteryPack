# 📚 BatteryPack Simulator - Code Examples

This document contains detailed code examples for using BatteryPack Simulator.

## Table of Contents

- [Basic Simulation](#basic-simulation)
- [Real-World Drive Cycles](#real-world-drive-cycles)
- [Fast Charging Simulation](#fast-charging-simulation)
- [Monte Carlo Uncertainty Analysis](#monte-carlo-uncertainty-analysis)
- [Economic Analysis](#economic-analysis)
- [Safety Analysis](#safety-analysis)
- [Mission Profile (Aerospace)](#mission-profile-aerospace)
- [Configuration Management](#configuration-management)
- [BMS Integration](#bms-integration)
- [Data Export](#data-export)

---

## Basic Simulation

```python
from battery_pack import (
    BatteryPack, Simulator,
    default_cell_params, default_pack_params,
    default_thermal_params, default_simulation_params
)
from battery_pack.drive_cycles import synthetic_cycle

# Create pack
pack = BatteryPack(
    cell_params=default_cell_params(),
    pack_params=default_pack_params(),
    thermal_params=default_thermal_params(),
)

# Generate drive cycle
cycle = synthetic_cycle(t_total_s=1800, dt_s=1.0, peak_current_a=80.0)

# Run simulation
simulator = Simulator(pack, default_simulation_params())
results = simulator.run(cycle)

# Calculate round-trip efficiency
rte = simulator.round_trip_efficiency(cycle, initial_soc=0.8)
print(f"Round-Trip Efficiency: {rte.RTE_percent:.2f}%")
```

---

## Real-World Drive Cycles

### EPA Drive Cycles

```python
from battery_pack.drive_cycles_real import get_standard_cycle, DriveCycleType

# Load EPA UDDS cycle
cycle = get_standard_cycle(DriveCycleType.EPA_UDDS)

# Run simulation
simulator = Simulator(pack, default_simulation_params())
results = simulator.run(cycle)

# Analyze results
print(f"Peak Temperature: {results['temp_k'].max():.2f} K")
print(f"Min Voltage: {results['v_pack_v'].min():.2f} V")
```

### WLTP and NEDC Cycles

```python
# WLTP Class 3 cycle
wltp_cycle = get_standard_cycle(DriveCycleType.WLTP_CLASS3)

# NEDC cycle
nedc_cycle = get_standard_cycle(DriveCycleType.NEDC)

# Custom drive cycle from CSV
from battery_pack.drive_cycles_real import load_cycle_from_csv
custom_cycle = load_cycle_from_csv("my_drive_cycle.csv")
```

---

## Fast Charging Simulation

### Tesla Supercharger

```python
from battery_pack.charging import tesla_supercharger_profile

# Generate Tesla Supercharger V3 profile
profile = tesla_supercharger_profile(
    cell_params=default_cell_params(),
    pack_params=default_pack_params(),
    soc_start=0.1,
    soc_target=0.8,
)

# Simulate charging
for t, I in zip(profile.time_s, profile.current_a):
    result = pack.step(I, dt_s=1.0)
    # Apply thermal throttling if needed
    if result['temp_k'] > 318.15:  # 45°C
        I_limited = thermal_limited_charging(...)
```

### CCS Combo Charging

```python
from battery_pack.charging import ccs_combo_profile

# Generate CCS Combo profile (350 kW)
profile = ccs_combo_profile(
    cell_params=default_cell_params(),
    pack_params=default_pack_params(),
    max_power_kw=350.0,
    soc_start=0.1,
    soc_target=0.8,
)
```

### CHAdeMO Charging

```python
from battery_pack.charging import get_charging_profile, ChargingProtocol

# Generate CHAdeMO profile
profile = get_charging_profile(
    protocol=ChargingProtocol.CHAdeMO,
    cell_params=default_cell_params(),
    pack_params=default_pack_params(),
    soc_start=0.1,
    soc_target=0.8,
)
```

---

## Monte Carlo Uncertainty Analysis

### Basic Monte Carlo Analysis

```python
from battery_pack.uncertainty import MonteCarloAnalysis, UncertaintyParams

# Setup uncertainty analysis
uncertainty = UncertaintyParams(
    n_samples=1000,
    capacity_cv=0.02,  # 2% variation
    R0_cv=0.05,       # 5% variation
    R1_cv=0.05,
    thermal_UA_cv=0.10,
)

mc = MonteCarloAnalysis(
    cell_base=default_cell_params(),
    pack_params=default_pack_params(),
    thermal_base=default_thermal_params(),
    uncertainty=uncertainty,
)

# Run analysis (parallel processing)
result = mc.run_analysis(cycle, default_simulation_params(), n_jobs=-1)

print(f"Failure Rate: {result.failure_rate:.4f}")
print(f"Reliability: {result.reliability_metrics['reliability']:.4f}")
print(f"95th Percentile Peak Temp: {result.summary['p95_peak_temp_k']:.2f} K")
print(f"99th Percentile Peak Temp: {result.summary['p99_peak_temp_k']:.2f} K")
```

### Sensitivity Analysis

```python
from battery_pack.uncertainty import sensitivity_analysis

# Parameter ranges for sensitivity analysis
param_ranges = {
    "R0_ohm": [0.001, 0.002, 0.003, 0.004, 0.005],
    "UA_w_per_k": [4.0, 6.0, 8.0, 10.0, 12.0],
}

sensitivity_results = sensitivity_analysis(
    base_cell=default_cell_params(),
    base_pack=default_pack_params(),
    base_thermal=default_thermal_params(),
    cycle=cycle,
    sim_params=default_simulation_params(),
    param_ranges=param_ranges,
)

print(sensitivity_results)
```

---

## Economic Analysis

### Cost Modeling

```python
from battery_pack.economics import CostModel, CostParams

# Calculate pack costs
cost_model = CostModel(CostParams())
costs = cost_model.calculate_capital_cost(
    pack_params=default_pack_params(),
    cell_capacity_ah=3.0,
    nominal_voltage_v=400.0,
    cooling_power_w=5000.0,
)

print(f"Capital Cost: ${costs['total_cost_usd']:,.2f}")
print(f"Cost per kWh: ${costs['cost_per_kwh']:.2f}")
print(f"Cost per Cell: ${costs['cost_per_cell']:.2f}")
```

### LCOE Calculation

```python
from battery_pack.economics import LCOECalculator, LCOEParams

# Calculate LCOE
lcoe_calc = LCOECalculator(LCOEParams())
lcoe = lcoe_calc.calculate_lcoe(
    capital_cost_usd=costs['total_cost_usd'],
    operating_cost_usd_per_year=1000.0,
    annual_energy_kwh=10000.0,
)

print(f"LCOE: ${lcoe['lcoe_usd_per_kwh']:.3f}/kWh")
print(f"NPV: ${lcoe['npv_usd']:,.2f}")
```

### Grid Integration and V2G

```python
from battery_pack.economics import GridEconomics, GridParams

# Grid/V2G revenue
grid_econ = GridEconomics(GridParams())
v2g_revenue = grid_econ.calculate_v2g_revenue(
    pack_energy_kwh=100.0,
    pack_power_kw=150.0,
    vehicles_in_fleet=100,
    utilization_rate=0.3,
    hours_per_day=8.0,
)

print(f"V2G Revenue: ${v2g_revenue['total_revenue_usd_per_year']:,.2f}/year")
print(f"Grid Service Revenue: ${v2g_revenue['grid_service_revenue_usd_per_year']:,.2f}/year")
print(f"Arbitrage Revenue: ${v2g_revenue['arbitrage_revenue_usd_per_year']:,.2f}/year")
```

### Energy Arbitrage

```python
# Calculate energy arbitrage revenue
arbitrage = grid_econ.calculate_arbitrage_revenue(
    pack_energy_kwh=100.0,
    round_trip_efficiency=0.90,
    cycles_per_day=2,
)

print(f"Annual Arbitrage Revenue: ${arbitrage['annual_revenue_usd']:,.2f}")
print(f"Net Revenue: ${arbitrage['net_revenue_usd_per_year']:,.2f}")
```

---

## Safety Analysis

### Basic Safety Analysis

```python
from battery_pack.safety import SafetyAnalyzer, ThermalRunawayParams, SafetyLimits

# Setup safety analysis
safety = SafetyAnalyzer(
    runaway_params=ThermalRunawayParams(),
    safety_limits=SafetyLimits(),
)

# Analyze operating conditions
analysis = safety.analyze_operating_conditions(
    voltage_v=400.0,
    current_a=100.0,
    temperature_k=323.15,
    soc=0.5,
    cell_count=100,
)

print(f"Failure Probability: {analysis.failure_probability:.6f}")
print(f"Hazard Index: {analysis.hazard_index:.4f}")
print(f"Status: {analysis.status}")
```

### FMEA Analysis

```python
# Perform FMEA analysis
fmea_results = safety.fmea_analysis(
    cell_params=default_cell_params(),
    pack_params=default_pack_params(),
    thermal_params=default_thermal_params(),
)

# Sort by Risk Priority Number (RPN)
print(fmea_results.sort_values('RPN', ascending=False))
```

### Thermal Runaway Simulation

```python
from battery_pack.safety import ThermalRunawayModel, ThermalRunawayParams

# Setup thermal runaway model
runaway = ThermalRunawayModel(ThermalRunawayParams())

# Check trigger conditions
temperature_k = np.array([310.0, 315.0, 405.0, 320.0])  # One cell at trigger temp
voltage_v = np.array([4.0, 4.0, 4.0, 4.0])

triggered, triggered_cells = runaway.check_trigger_conditions(
    temperature_k=temperature_k,
    voltage_v=voltage_v,
    current_a=100.0,
)

print(f"Thermal Runaway Triggered: {triggered}")
print(f"Triggered Cells: {triggered_cells}")

# Simulate propagation
propagation = runaway.simulate_propagation(
    initial_cells=triggered_cells,
    num_cells=len(temperature_k),
    cell_spacing_m=0.01,
)

print(f"Full Propagation Time: {propagation['full_propagation_time_s']:.2f} s")
print(f"Total Energy Released: {propagation['total_energy_released_wh']:.2f} Wh")
```

---

## Mission Profile (Aerospace)

### Electric Aircraft Mission

```python
from battery_pack.mission import typical_electric_aircraft_mission, mission_to_drive_cycle

# Create mission profile
mission = typical_electric_aircraft_mission()

# Convert to drive cycle
cycle = mission_to_drive_cycle(
    mission,
    pack_params=default_pack_params(),
    nominal_voltage_v=400.0,
)

# Run simulation
results = simulator.run(cycle)

# Analyze mission compliance
from battery_pack.mission import analyze_mission_compliance

safety_limits = {
    "T_max_k": 328.15,
    "V_min_v": 100.0,
    "soc_min": 0.1,
    "I_max_a": 500.0,
}

compliance = analyze_mission_compliance(
    mission=mission,
    simulation_results=results,
    safety_limits=safety_limits,
)

print(f"All Requirements Met: {compliance['compliance']['all_requirements_met']}")
```

### eVTOL Mission

```python
from battery_pack.mission import typical_evtol_mission

# Create eVTOL mission profile
mission = typical_evtol_mission()

# Convert and simulate
cycle = mission_to_drive_cycle(mission, pack_params, nominal_voltage_v=400.0)
results = simulator.run(cycle)
```

### Satellite Mission

```python
from battery_pack.mission import typical_satellite_mission

# Create satellite mission profile
mission = typical_satellite_mission()

# Convert and simulate
cycle = mission_to_drive_cycle(mission, pack_params, nominal_voltage_v=100.0)
results = simulator.run(cycle)
```

---

## Configuration Management

### YAML Configuration

```python
from battery_pack.config_loader import ConfigLoader, save_config_template

# Save configuration template
save_config_template("config_template.yaml")

# Load configuration
loader = ConfigLoader()
params = loader.load_all_params("config.yaml")

# Use loaded parameters
pack = BatteryPack(
    cell_params=params['cell'],
    pack_params=params['pack'],
    thermal_params=params['thermal'],
)
```

### JSON Configuration

```python
# Save JSON template
save_config_template("config_template.json")

# Load JSON configuration
params = loader.load_all_params("config.json")
```

### Programmatic Configuration

```python
from battery_pack.config import (
    CellParams, PackParams, ThermalParams,
    SimulationParams, LimitsParams
)

# Create custom configuration
cell_params = CellParams(
    capacity_ah=5.0,
    R0_ohm=0.002,
    R1_ohm=0.001,
    C1_f=2500.0,
    V_min=2.8,
    V_max=4.25,
)

pack_params = PackParams(
    series_cells=96,
    parallel_cells=4,
    max_current_a=200.0,
    min_soc=0.1,
    max_soc=0.9,
)

pack = BatteryPack(
    cell_params=cell_params,
    pack_params=pack_params,
    thermal_params=default_thermal_params(),
)
```

---

## BMS Integration

### Protection Algorithms

```python
from battery_pack.bms import BMSProtection, ProtectionLimits

# Setup BMS protection
bms = BMSProtection(ProtectionLimits())

# Check protection during simulation
for result in simulation_results:
    protection = bms.check_protection(
        voltage_v=result['v_pack_v'],
        current_a=result['i_pack_a'],
        temperature_k=result['temp_k'],
        cell_count=pack_params.series_cells,
    )
    
    if protection.status != ProtectionStatus.OK:
        print(f"Protection Triggered: {protection.message}")
        # Apply current limit
        limited_current = bms.apply_current_limit(
            requested_current_a=result['i_pack_a'],
            protection_result=protection,
        )
```

### Passive Balancing

```python
from battery_pack.bms import PassiveBalancer, BalancingParams

# Setup passive balancing
balancer = PassiveBalancer(BalancingParams(
    balance_threshold=0.05,
    balance_current_a=0.1,
    enable=True,
))

# Apply balancing during simulation
soc_updated, energy_lost = balancer.balance(
    soc_array=pack.soc,
    voltage_array=cell_voltages,
    dt_s=1.0,
)

print(f"Energy Lost to Balancing: {energy_lost:.4f} Wh")
```

### Active Balancing

```python
from battery_pack.bms import ActiveBalancer

# Setup active balancing
active_balancer = ActiveBalancer(efficiency=0.85)

# Apply active balancing
soc_updated, energy_consumed = active_balancer.balance(
    soc_array=pack.soc,
    voltage_array=cell_voltages,
    capacity_array=cell_capacities,
    dt_s=1.0,
)

print(f"Energy Consumed by Balancing: {energy_consumed:.4f} Wh")
```

---

## Data Export

### CSV Export

```python
import pandas as pd

# Save results to CSV
results.to_csv("simulation_results.csv", index=False)
```

### JSON Export

```python
from battery_pack.export import export_to_json

# Export simulation results
export_to_json(
    data=results,
    output_path="results.json",
    pretty=True,
)
```

### HDF5 Export

```python
from battery_pack.export import export_to_hdf5

# Export to HDF5 (efficient for large datasets)
export_to_hdf5(
    data=results,
    output_path="results.h5",
    group="/simulation",
    compression="gzip",
)
```

### Comprehensive Export

```python
from battery_pack.export import export_simulation_results

# Export in multiple formats
metadata = {
    "simulation_params": sim.__dict__,
    "cell_params": cell.__dict__,
    "pack_params": pack_params.__dict__,
    "thermal_params": thermal.__dict__,
}

export_paths = export_simulation_results(
    results=results,
    metadata=metadata,
    output_dir="outputs/",
    formats=["csv", "json", "hdf5"],
)

print(f"Exported to: {export_paths}")
```

---

## Advanced Features

### Comprehensive Metrics

```python
from battery_pack.metrics import calculate_comprehensive_metrics

# Calculate comprehensive metrics
metrics = calculate_comprehensive_metrics(
    simulation_data=results,
    pack_energy_wh=pack_energy_wh,
    pack_mass_kg=pack_mass_kg,
    initial_soc=0.8,
    capacity_ah=3.0,
)

print(f"Peak Power: {metrics.peak_power_w:.2f} W")
print(f"Power Density: {metrics.power_density_w_per_kg:.2f} W/kg")
print(f"Average C-Rate: {metrics.c_rate_avg:.2f} C")
print(f"Peak C-Rate: {metrics.c_rate_peak:.2f} C")
print(f"Equivalent Full Cycles: {metrics.equivalent_full_cycles:.2f}")
```

### Statistical Summary

```python
from battery_pack.metrics import calculate_statistical_summary

# Calculate statistical summary
summary = calculate_statistical_summary(
    data=results,
    metrics=["mean", "std", "min", "max", "p95", "p99"],
)

print(summary)
```

### Cycle Life Estimation

```python
from battery_pack.metrics import calculate_cycle_life_estimate

# Estimate cycle life
cycle_life = calculate_cycle_life_estimate(
    throughput_ah=metrics.throughput_ah,
    capacity_ah=3.0,
    degradation_per_cycle_percent=0.05,
    capacity_fade_limit_percent=20.0,
)

print(f"Cycles Completed: {cycle_life['cycles_completed']:.2f}")
print(f"Remaining Cycles: {cycle_life['remaining_cycles']:.2f}")
print(f"Current Capacity: {cycle_life['current_capacity_percent']:.2f}%")
```

---

For more information, see the [main README](README.md) or [API documentation](API.md).

