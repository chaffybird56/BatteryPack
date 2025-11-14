"""Mission profile simulation for aerospace and defense applications."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import PackParams
from .drive_cycles import DriveCycle


class MissionPhase(Enum):
    """Aerospace mission phases."""

    GROUND_STARTUP = "ground_startup"
    TAKEOFF = "takeoff"
    CLIMB = "climb"
    CRUISE = "cruise"
    DESCENT = "descent"
    APPROACH = "approach"
    LANDING = "landing"
    LOITER = "loiter"
    COMBAT = "combat"
    EMERGENCY = "emergency"
    HOVER = "hover"  # For VTOL/rotorcraft


@dataclass
class MissionSegment:
    """Mission segment definition."""

    phase: MissionPhase
    duration_s: float
    power_kw: float
    description: str
    altitude_m: Optional[float] = None
    ambient_temp_k: Optional[float] = None


@dataclass
class MissionProfile:
    """Complete mission profile."""

    segments: List[MissionSegment]
    name: str
    total_duration_s: float
    max_power_kw: float


def mission_segment_to_current(
    segment: MissionSegment,
    pack_params: PackParams,
    nominal_voltage_v: float,
) -> float:
    """Convert mission segment power to battery current.

    Args:
            segment: Mission segment
            pack_params: Pack configuration
            nominal_voltage_v: Nominal pack voltage (V)

    Returns:
            Battery current (A), positive for discharge
    """
    power_w = segment.power_kw * 1000.0
    current_a = power_w / nominal_voltage_v
    return current_a


def create_mission_profile(segments: List[MissionSegment], name: str = "mission") -> MissionProfile:
    """Create mission profile from segments."""
    total_duration = sum(seg.duration_s for seg in segments)
    max_power = max(seg.power_kw for seg in segments)
    return MissionProfile(
        segments=segments,
        name=name,
        total_duration_s=total_duration,
        max_power_kw=max_power,
    )


def mission_to_drive_cycle(
    mission: MissionProfile,
    pack_params: PackParams,
    nominal_voltage_v: float,
    dt_s: float = 1.0,
) -> DriveCycle:
    """Convert mission profile to drive cycle.

    Args:
            mission: Mission profile
            pack_params: Pack configuration
            nominal_voltage_v: Nominal pack voltage (V)
            dt_s: Time step (s)

    Returns:
            DriveCycle object
    """
    time_points = []
    current_points = []

    t = 0.0
    for segment in mission.segments:
        current = mission_segment_to_current(segment, pack_params, nominal_voltage_v)
        steps = int(segment.duration_s / dt_s)

        for _ in range(steps):
            time_points.append(t)
            current_points.append(current)
            t += dt_s

    return DriveCycle(
        time_s=np.array(time_points),
        current_a=np.array(current_points),
    )


def typical_electric_aircraft_mission() -> MissionProfile:
    """Generate typical electric aircraft mission profile.

    Phases: Ground, Takeoff, Climb, Cruise, Descent, Approach, Landing
    """
    segments = [
        MissionSegment(
            phase=MissionPhase.GROUND_STARTUP,
            duration_s=300.0,  # 5 minutes
            power_kw=10.0,
            description="Ground operations and pre-flight checks",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.TAKEOFF,
            duration_s=60.0,  # 1 minute
            power_kw=200.0,  # High power for takeoff
            description="Takeoff roll and initial climb",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.CLIMB,
            duration_s=600.0,  # 10 minutes
            power_kw=150.0,  # Sustained climb power
            description="Climb to cruise altitude",
            altitude_m=3000.0,
            ambient_temp_k=273.15,  # Colder at altitude
        ),
        MissionSegment(
            phase=MissionPhase.CRUISE,
            duration_s=3600.0,  # 60 minutes
            power_kw=80.0,  # Efficient cruise power
            description="Cruise flight",
            altitude_m=3000.0,
            ambient_temp_k=273.15,
        ),
        MissionSegment(
            phase=MissionPhase.DESCENT,
            duration_s=300.0,  # 5 minutes
            power_kw=30.0,  # Low power descent
            description="Descent to approach altitude",
            ambient_temp_k=285.15,
        ),
        MissionSegment(
            phase=MissionPhase.APPROACH,
            duration_s=180.0,  # 3 minutes
            power_kw=50.0,
            description="Approach pattern",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.LANDING,
            duration_s=120.0,  # 2 minutes
            power_kw=40.0,
            description="Final approach and landing",
            ambient_temp_k=298.15,
        ),
    ]

    return create_mission_profile(segments, name="electric_aircraft_mission")


def typical_evtol_mission() -> MissionProfile:
    """Generate typical eVTOL (electric Vertical Take-Off and Landing) mission.

    Phases: Hover takeoff, Transition, Cruise, Transition, Hover landing
    """
    segments = [
        MissionSegment(
            phase=MissionPhase.HOVER,
            duration_s=60.0,
            power_kw=250.0,  # High power for hover
            description="Vertical takeoff and hover",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.CLIMB,
            duration_s=120.0,
            power_kw=180.0,
            description="Transition to forward flight",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.CRUISE,
            duration_s=1200.0,  # 20 minutes
            power_kw=100.0,  # Efficient cruise
            description="Cruise flight",
            ambient_temp_k=285.15,
        ),
        MissionSegment(
            phase=MissionPhase.DESCENT,
            duration_s=120.0,
            power_kw=180.0,
            description="Transition to hover",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.HOVER,
            duration_s=60.0,
            power_kw=250.0,
            description="Hover and vertical landing",
            ambient_temp_k=298.15,
        ),
    ]

    return create_mission_profile(segments, name="evtol_mission")


def typical_satellite_mission() -> MissionProfile:
    """Generate typical satellite mission profile.

    Phases: Launch, Orbit insertion, Operations, Eclipse, Emergency
    """
    segments = [
        MissionSegment(
            phase=MissionPhase.EMERGENCY,  # Launch phase
            duration_s=600.0,  # 10 minutes
            power_kw=500.0,  # Very high power for launch
            description="Launch and orbit insertion",
            ambient_temp_k=273.15,
        ),
        MissionSegment(
            phase=MissionPhase.CRUISE,
            duration_s=5400.0,  # 90 minutes (half orbit)
            power_kw=2.0,  # Low power for normal operations
            description="Normal operations (daylight)",
            ambient_temp_k=273.15,
        ),
        MissionSegment(
            phase=MissionPhase.EMERGENCY,  # Eclipse
            duration_s=5400.0,  # 90 minutes (half orbit)
            power_kw=0.0,  # No discharge during eclipse (battery depleted)
            description="Eclipse period (battery discharge)",
            ambient_temp_k=273.15,
        ),
    ]

    return create_mission_profile(segments, name="satellite_mission")


def typical_ev_emergency_mission() -> MissionProfile:
    """Generate emergency/defense mission profile with high power demands."""
    segments = [
        MissionSegment(
            phase=MissionPhase.GROUND_STARTUP,
            duration_s=30.0,
            power_kw=5.0,
            description="System startup",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.CRUISE,
            duration_s=1800.0,  # 30 minutes
            power_kw=50.0,
            description="Normal operations",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.COMBAT,
            duration_s=300.0,  # 5 minutes
            power_kw=300.0,  # Very high power for combat systems
            description="High-power operation",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.EMERGENCY,
            duration_s=60.0,  # 1 minute
            power_kw=500.0,  # Maximum emergency power
            description="Emergency maximum power",
            ambient_temp_k=298.15,
        ),
        MissionSegment(
            phase=MissionPhase.CRUISE,
            duration_s=600.0,  # 10 minutes
            power_kw=30.0,
            description="Return to base (low power)",
            ambient_temp_k=298.15,
        ),
    ]

    return create_mission_profile(segments, name="emergency_mission")


def analyze_mission_compliance(
    mission: MissionProfile,
    simulation_results: pd.DataFrame,
    safety_limits: Dict[str, float],
) -> Dict[str, any]:
    """Analyze mission compliance with safety and performance requirements.

    Args:
            mission: Mission profile
            simulation_results: Simulation results DataFrame
            safety_limits: Dictionary of safety limits

    Returns:
            Dictionary with compliance analysis
    """
    # Extract metrics
    peak_temp_k = simulation_results["temp_k"].max()
    min_voltage_v = simulation_results["v_pack_v"].min()
    min_soc = simulation_results["soc"].min()
    max_current_a = simulation_results["i_pack_a"].abs().max()

    # Check compliance
    compliance = {
        "temperature_ok": peak_temp_k <= safety_limits.get("T_max_k", 328.15),
        "voltage_ok": min_voltage_v >= safety_limits.get("V_min_v", 100.0),
        "soc_ok": min_soc >= safety_limits.get("soc_min", 0.1),
        "current_ok": max_current_a <= safety_limits.get("I_max_a", 500.0),
    }

    compliance["all_requirements_met"] = all(compliance.values())

    # Mission performance
    performance = {
        "peak_temp_k": peak_temp_k,
        "min_voltage_v": min_voltage_v,
        "min_soc": min_soc,
        "max_current_a": max_current_a,
        "mission_duration_s": mission.total_duration_s,
        "peak_power_kw": mission.max_power_kw,
    }

    return {
        "compliance": compliance,
        "performance": performance,
        "mission_name": mission.name,
    }
