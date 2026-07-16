# BatteryPack

<!-- battery simulation, lithium-ion pack, BMS, thermal runaway, equivalent circuit model, EV battery, energy storage, Python -->

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)

**BatteryPack** is a Python framework that simulates how a lithium-ion battery pack behaves electrically and thermally under charge, discharge, and load—so you can estimate efficiency, temperature rise, power limits, and safety margins before hardware sign-off.

It couples a first-order equivalent-circuit cell model with pack-level series/parallel topology, lumped (and optional multi-node) thermal dynamics, configurable cell chemistries, drive-cycle profiles, and Python-based failure-mode / thermal-runaway screening.

---

## Key capabilities

- **Electro-thermal modeling** 
- **DC power & efficiency** 
- **Configurable chemistries** 
- **Load & charge profiles** 
- **Automotive-style cycles** 
- **BMS & safety**
- **Analysis extras** 
- **CI** 

> Full module-by-module inventory (including what is *not* built): **[FEATURES.md](FEATURES.md)**

---

## Screenshots

**Time series** — pack current, voltage, power, SoC during discharge:

![Time series](assets/time_series.png)

**Thermal** — temperature through charge/discharge:

![Temperature](assets/temperature.png)

**Round-trip efficiency**:

![RTE](assets/rte.png)

**Charge / load profile**:

![Load profile](assets/load_profile.png)

**Chemistry comparison** — RTE across cell presets (same pack topology):

![Chemistry RTE](assets/chemistry_rte.png)

**Safety** — thermal-runaway hazard vs pack temperature:

![Safety](assets/safety_runaway.png)

**Power limits** — max charge/discharge vs SoC:

![Power limits](assets/power_limits.png)

---

## Project layout

```
battery_pack/
  cell.py, pack.py, thermal.py   # ECM + pack + thermal
  simulation.py                  # charge/discharge, RTE
  drive_cycles.py                # synthetic / dataframe cycles
  drive_cycles_real.py           # EPA/WLTP/NEDC-style generators
  charging.py, bms.py, safety.py
  config.py                      # chemistry presets
scripts/
  generate_readme_plots.py       # figures in assets/
  run_demo.py, run_sweeps.py, run_ups_demo.py
tests/
```

More examples: [EXAMPLES.md](EXAMPLES.md)

---

## Quickstart

```bash
git clone https://github.com/chaffybird56/BatteryPack.git && cd BatteryPack
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

pytest tests/ -q
python scripts/generate_readme_plots.py   # refresh assets/*.png
```

```python
from battery_pack.config import cell_params_for_chemistry
from battery_pack.pack import BatteryPack

cell = cell_params_for_chemistry("LFP")  # or NMC811, NCA, LCO
pack = BatteryPack(cell_params=cell, ...)
```

## Topics

Search-friendly tags for this project:

`battery-simulation` · `lithium-ion` · `battery-pack` · `battery-modeling` · `equivalent-circuit-model` · `electro-thermal` · `bms` · `thermal-runaway` · `state-of-charge` · `round-trip-efficiency` · `drive-cycle` · `fast-charging` · `electric-vehicle` · `energy-storage` · `grid-storage` · `ups-backup` · `monte-carlo` · `python` · `open-source`

GitHub **Topics** for this repo are defined in `.github/repository-topics.json`. Re-apply after edits: `bash scripts/set_github_topics.sh` (uses your existing git GitHub credentials).

## License

MIT — see [LICENSE](LICENSE).
