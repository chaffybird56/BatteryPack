#!/usr/bin/env python3
"""
Demo script for UPS/Backup Power Systems
Demonstrates battery backup systems and uninterrupted power supply solutions.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from battery_pack import (
    BatteryPack,
    default_cell_params,
    default_pack_params,
    default_thermal_params,
    UPSBackupSystem,
    UPSRequirements,
    design_ups_system,
)


def main():
    print("=" * 60)
    print("UPS & Battery Backup Systems Demo")
    print("=" * 60)
    print()
    
    # Define UPS requirements
    requirements = UPSRequirements(
        backup_power_kw=5.0,  # 5kW backup power
        backup_duration_hours=2.0,  # 2 hours backup duration
        input_voltage_v=120.0,
        efficiency_target=0.85,
        max_temperature_c=40.0,
        compliance_standards=["OESC", "CSA"]  # Ontario Electrical Safety Code, CSA
    )
    
    print("UPS Requirements:")
    print(f"  Backup Power: {requirements.backup_power_kw} kW")
    print(f"  Backup Duration: {requirements.backup_duration_hours} hours")
    print(f"  Input Voltage: {requirements.input_voltage_v} V")
    print(f"  Compliance Standards: {', '.join(requirements.compliance_standards)}")
    print()
    
    # Design UPS system
    print("Designing UPS system...")
    ups_pack = design_ups_system(requirements)
    print(f"  Pack Configuration: {ups_pack.Ns}S{ups_pack.Np}P")
    print(f"  Cell Capacity: {ups_pack.cell.params.capacity_ah} Ah")
    print()
    
    # Analyze backup requirements
    print("Analyzing backup power requirements...")
    ups_system = UPSBackupSystem(ups_pack)
    analysis = ups_system.analyze_backup_requirements(requirements)
    
    print("Backup Power Analysis Results:")
    print(f"  Backup Capacity: {analysis.backup_capacity_kwh} kWh")
    print(f"  Estimated Backup Duration: {analysis.estimated_backup_duration_hours} hours")
    print(f"  Peak Power Capability: {analysis.peak_power_kw} kW")
    print(f"  Efficiency: {analysis.efficiency_percent}%")
    print()
    
    print("Compliance Status:")
    for standard, status in analysis.compliance_status.items():
        status_str = "✓ PASS" if status else "✗ FAIL"
        print(f"  {standard}: {status_str}")
    print()
    
    print("Recommendations:")
    for rec in analysis.recommendations:
        print(f"  • {rec}")
    print()
    
    # Simulate backup scenario
    print("Simulating backup power scenario...")
    simulation_results = ups_system.simulate_backup_scenario(requirements)
    
    print("Simulation Results:")
    print(f"  Total Energy Delivered: {simulation_results['total_energy_kwh']} kWh")
    print(f"  Actual Backup Duration: {simulation_results['actual_backup_duration_hours']} hours")
    print(f"  Meets Requirement: {'✓ YES' if simulation_results['meets_requirement'] else '✗ NO'}")
    print(f"  Final SOC: {simulation_results['final_soc']:.1%}")
    print(f"  Max Temperature: {simulation_results['max_temperature_c']} °C")
    print()
    
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
