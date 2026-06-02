from __future__ import annotations

import numpy as np

from battery_pack.config import CHEMISTRY_PRESETS, cell_params_for_chemistry
from battery_pack.safety import FailureMode, SafetyAnalyzer, SafetyLimits, ThermalRunawayModel, ThermalRunawayParams


def test_chemistry_presets_load():
    lfp = cell_params_for_chemistry("LFP")
    assert lfp.V_max < 4.0
    assert "NMC811" in CHEMISTRY_PRESETS


def test_thermal_runaway_risk_increases_with_temperature():
    analyzer = SafetyAnalyzer(ThermalRunawayParams(), SafetyLimits())
    cool = analyzer.analyze_operating_conditions(140.0, 50.0, 298.15, 0.5, cell_count=40)
    hot = analyzer.analyze_operating_conditions(140.0, 50.0, 410.0, 0.5, cell_count=40)
    assert hot.hazard_index > cool.hazard_index
    assert hot.failure_modes[FailureMode.THERMAL_RUNAWAY] > cool.failure_modes[FailureMode.THERMAL_RUNAWAY]


def test_runaway_trigger_detects_high_temperature():
    model = ThermalRunawayModel(ThermalRunawayParams())
    temps = np.array([300.0, 310.0, 420.0])
    volts = np.array([3.7, 3.7, 3.7])
    triggered, cells = model.check_trigger_conditions(temps, volts, 10.0)
    assert triggered
    assert 2 in cells
