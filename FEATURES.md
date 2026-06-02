# BatteryPack — feature inventory

What exists in this repository today, what is simplified, and what is not implemented.

---

## Implemented (Python modules)

| Area | Module | What it does |
|------|--------|----------------|
| **Core simulation** | `cell.py`, `pack.py`, `thermal.py`, `simulation.py` | First-order ECM cell, Ns×Np pack, lumped thermal, charge/discharge, round-trip efficiency |
| **Chemistry presets** | `config.py` | `CHEMISTRY_PRESETS` + `cell_params_for_chemistry()` for LFP, NMC811, NCA, LCO |
| **Drive cycles** | `drive_cycles.py` | Synthetic UDDS-like profile; load cycles from DataFrames |
| **Automotive-style cycles** | `drive_cycles_real.py` | Parametric EPA UDDS / WLTP / NEDC *generators*; CSV velocity → current; vehicle-dynamics mapping |
| **Power limits** | `limits.py` | Max charge/discharge power vs SoC |
| **Thermal network** | `thermal_network.py` | Multi-node thermal (beyond single lumped node) |
| **Aging** | `aging.py` | Capacity fade / resistance growth helpers |
| **Cell variation & balancing** | `variation.py` | Random cell spread; passive balancing |
| **Advanced pack** | `pack_advanced.py` | Multi-node thermal + variation on pack object |
| **Fast charging** | `charging.py` | CCS, CHAdeMO, Supercharger-style *curves* (protocol enums + power/current profiles) |
| **BMS protection** | `bms.py` | Voltage, current, temperature, short-circuit checks |
| **Safety / runaway** | `safety.py` | Trigger checks, propagation model, hazard index, FMEA table |
| **Mission profiles** | `mission.py` | Aircraft / eVTOL / satellite / emergency segment builders → drive cycle |
| **Metrics** | `metrics.py` | RTE, power, thermal, voltage, SOC, C-rate, cycle-life helpers |
| **Parameter sweeps** | `sweep.py` | Grid sweeps (optionally parallel via joblib in callers) |
| **Monte Carlo** | `uncertainty.py` | Parameter sampling, failure-rate / reliability stats |
| **Economics** | `economics.py` | Pack cost, LCOE, V2G / arbitrage / grid-service revenue models |
| **UPS / backup** | `ups_backup.py` | Runtime sizing; simple OESC/CSA/UL threshold checks |
| **Export** | `export.py` | CSV / JSON / HDF5 export and load |
| **Config files** | `config_loader.py` | YAML/JSON → simulation parameters |
| **Logging** | `logger.py` | Structured file/console logging |
| **Plots** | `plots.py` | Time series, temperature, RTE, power limits, safety, chemistry comparison |
| **Validation** | `validation.py` | SOC/temperature bound checks, energy balance sanity |
| **ML (optional use)** | `ml.py` | Train Random Forest on sweep data for temp/RTE (needs sweep outputs first) |
| **PyBaMM hook** | `pybamm_adapter.py` | Optional high-fidelity OCV if `pybamm` is installed |

**Scripts:** `run_demo.py`, `run_sweeps.py`, `run_advanced_demo.py`, `run_ups_demo.py`, `generate_readme_plots.py`, `train_ml.py`

**Tests:** `tests/test_basic.py`, `test_advanced.py`, `test_safety.py` (pytest + GitHub Actions on 3.10–3.12)

---

## Simplified (not certification or regulatory sign-off)

- **EPA / WLTP / NEDC** — Built-in cycles are *parametric approximations*, not official regulatory trace files. Use `load_cycle_from_csv()` for your own measured profiles.
- **Fast-charge protocols** — Charging *curves* and thermal throttling logic, not hardware-in-the-loop CCS/CHAdeMO stacks.
- **UPS compliance flags** — Rule-of-thumb voltage/current/temperature checks against named standards; not a substitute for formal compliance testing.
- **Sensitivity analysis** — `uncertainty.sensitivity_analysis()` runs a **parameter sweep**, not full Sobol/Morris indices (see below).

---

## Not implemented

- **Sobol / Morris global sensitivity** — Described in older docs only; `sensitivity_analysis()` is a one-at-a-time sweep placeholder.
- **PyBaMM** — Requires optional `pip install pybamm`; adapter returns `None` if missing.
- **MyPy / Flake8 in CI** — CI runs **Black + pytest** only.
- **Codecov upload** — Not wired in the current workflow.

---

## Optional dependencies

```bash
pip install -e ".[optional]"   # PyBaMM
pip install -e ".[dev]"          # pytest-cov, black, mypy, flake8
```

Examples: [EXAMPLES.md](EXAMPLES.md)
