# BatteryPack

[![CI](https://img.shields.io/github/actions/workflow/status/chaffybird56/BatteryPack/ci.yml?label=CI&logo=github)](https://github.com/chaffybird56/BatteryPack/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)

Python simulation framework for **DC pack power**, **lumped thermal dynamics**, and **round-trip energy efficiency** across configurable Li-ion cell chemistries (NMC, LFP, NCA, LCO). Models voltage, current, and energy losses under synthetic charge/load profiles; includes **failure-mode and thermal-runaway screening** before pack sign-off.

## What this demonstrates

| Resume focus | In this repo |
|--------------|--------------|
| Pack simulation (electrical + thermal + RTE) | ECM cell model, Ns×Np pack, coupled thermal network |
| Voltage / current / losses under varied profiles | `drive_cycles`, time-series V/I/P/SoC, power limits vs SoC |
| Failure-mode & runaway risk (Python) | `battery_pack/safety.py`, hazard index vs temperature, FMEA helper |

## Quickstart

```bash
git clone https://github.com/chaffybird56/BatteryPack.git && cd BatteryPack
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

pytest tests/ -q
python scripts/generate_readme_plots.py   # refresh assets/*.png
```

Compare chemistries in code:

```python
from battery_pack.config import cell_params_for_chemistry
from battery_pack.pack import BatteryPack

cell = cell_params_for_chemistry("LFP")  # or NMC811, NCA, LCO
pack = BatteryPack(cell_params=cell, ...)
```

## Screenshots

**Time series** — pack current, voltage, power, SoC during discharge:

![Time series](assets/time_series.png)

**Thermal** — temperature through charge/discharge:

![Temperature](assets/temperature.png)

**Round-trip efficiency**:

![RTE](assets/rte.png)

**Charge / load profile** — configurable current vs time:

![Load profile](assets/load_profile.png)

**Chemistry comparison** — RTE across cell presets (same topology):

![Chemistry RTE](assets/chemistry_rte.png)

**Safety gate** — thermal-runaway hazard vs pack temperature (pre-sign-off):

![Safety](assets/safety_runaway.png)

**Power limits** — max charge/discharge vs SoC:

![Power limits](assets/power_limits.png)

## Layout

```
battery_pack/
  cell.py, pack.py, thermal.py   # ECM + pack + thermal
  simulation.py                  # charge/discharge, RTE
  drive_cycles.py                # load / charge profiles
  safety.py                      # runaway trigger, FMEA, hazard index
  config.py                      # CHEMISTRY_PRESETS (LFP, NMC811, …)
scripts/
  generate_readme_plots.py       # assets for README
  run_demo.py                    # full demo → outputs/
tests/
```

## Optional depth

Drive cycles (EPA/WLTP), fast-charge protocols, Monte Carlo sweeps, grid economics, and PyBaMM hooks live in the same tree — see [FEATURES.md](FEATURES.md) and [EXAMPLES.md](EXAMPLES.md) when you need more than the core pack/thermal/safety path.

## License

MIT — see [LICENSE](LICENSE).
