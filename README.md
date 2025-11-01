## 🔋 BatteryPack: Electro-Thermal N-Cell Pack Modeling & Analysis

<p align="left">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="#tests"><img alt="Tests" src="https://img.shields.io/badge/Tests-pytest%20passing-brightgreen"></a>
  <a href="https://github.com/chaffybird56/BatteryPack"><img alt="Repo" src="https://img.shields.io/badge/GitHub-BatteryPack-181717?logo=github"></a>
</p>

<em>Fast, observable pack‑level simulations with electro‑thermal coupling, sweeps, ML hooks, and publication‑ready plots ⚡🌡️📈</em>

This project provides a complete, observable, and testable battery pack simulator with:
- **Electrical ECM** per cell (R0 + R1||C1) and smooth OCV(SOC)
- **Lumped thermal node** for the pack with ambient cooling
- **Drive-cycle current input** (synthetic UDDS-like)
- **Metrics**: Round-Trip Efficiency (RTE), temperature rise traces, power-limit curves
- **Sensitivity & sweeps**: series/parallel counts, thermal conductance, current profiles, and internal resistance impact
- **Validation checks** and unit tests

#### 🎯 What This Does (In Plain Terms)

Imagine you're designing a battery pack for an EV, drone, or grid storage. You need to answer three questions:

1. **How much energy actually comes out vs. what went in?** (Efficiency)
   - Energy is lost as heat through internal resistance. Higher resistance → lower efficiency.
   - Operating at extreme temperatures further reduces efficiency.

2. **How hot does the pack get during use?** (Thermal limits)
   - Too hot can degrade the battery or trigger safety shutdowns.
   - Cooling effectiveness determines your safe operating envelope.

3. **How much power can I safely pull or push as the battery drains?** (Power limits)
   - Voltage drops as charge depletes, limiting max power.
   - SOC windows and temperature constraints shrink what's available.

This toolkit simulates all three together—packing hundreds of N‑cells into a series‑parallel configuration, running realistic drive cycles or load profiles, and showing exactly where the limits are.

### Table of contents
- [Getting started 🚀](#getting-started)
- [Advanced usage 🧪](#advanced-usage)
- [Who is this for and real-world applications 🌍](#applications)
- [Model overview 🧩](#model-overview)
- [Plot gallery 📊](#plot-gallery)
- [How to read the plots 📖](#how-to-read-the-plots)
- [What to look for 🔎](#what-to-look-for)
- [Repo layout 🗂️](#repo-layout)
- [Advanced features and extensions 🧠](#advanced-features)
- [License 📝](#license)

<a id="applications"></a>
### Who is this for and real-world applications 🌍
- **EV/HEV pack sizing and BMS prototyping**: Explore (Ns, Np) tradeoffs, SOC windows, and thermal/cooling needs before hardware.
- **Stationary storage and microgrids**: Evaluate round‑trip efficiency and thermal behavior across daily cycling patterns.
- **Drones/robots/power tools**: Check short‑burst power limits and temperature rise under aggressive current spikes.
- **Thermal design**: Compare cooling assumptions (UA) and their impact on safe operating zones and lifespan.
- **Safety and compliance**: Identify conditions where thermal or voltage limits may be violated for certification prep.
- **Digital twins / HIL**: Generate fast surrogate behavior for system‑level simulations and control prototyping.

<a id="plot-gallery"></a>
### Plot gallery 📊 (generated via `scripts/generate_readme_plots.py`)

![Time Series](assets/time_series.png)

![Temperature](assets/temperature.png)

![RTE](assets/rte.png)

![Power Limits](assets/power_limits.png)

<a id="how-to-read-the-plots"></a>
### How to read the plots 📖

- **Time series**: Current, voltage, power, and SOC vs time on the discharge cycle. Highlights transient voltage sag and recovery.
- **Temperature**: Pack temperature (°C) across both discharge and charge phases, showing thermal rise and cooldown with assumed UA.
- **RTE bar**: Energy out vs energy in after returning to the starting SOC. Lower R or higher Np generally improves RTE.
- **Power limits**: Max discharge/charge power vs SOC, constrained by pack voltage limits and SOC window. Use this to define BMS power envelopes.

<a id="getting-started"></a>
### Getting started 🚀
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD  # ensure local package is importable

# Generate assets for README (plots)
python scripts/generate_readme_plots.py

# Run a demo simulation with outputs timestamped under outputs/
python scripts/run_demo.py

# Run parameter sweeps and heatmaps
python scripts/run_sweeps.py

# Run tests
pytest -q
```

<a id="advanced-usage"></a>
### Advanced usage 🧪
- **Advanced demo (multi-node thermal + variation + aging + balancing):**
```bash
python scripts/run_advanced_demo.py --thermal-mode fin --no-pybamm-ocv
```
- **Train ML predictors (peak temperature and RTE) from sweep results:**
```bash
# After running run_sweeps.py, point to the latest sweep CSV
python scripts/train_ml.py --sweep-csv outputs/sweeps/latest/sweep_results.csv --out-dir outputs/ml
```
- **Optional PyBaMM OCV coupling:** install optional deps then enable `--use-pybamm-ocv` in the advanced demo. Alternatively, generate an OCV curve independently.
```bash
pip install -r requirements-optional.txt
python scripts/generate_pybamm_ocv.py --out-path assets/pybamm_ocv_curve.png
python scripts/run_advanced_demo.py --thermal-mode liquid --use-pybamm-ocv
```

<a id="model-overview"></a>
### Model overview (results and design connections) 🧩
- **System setup**: Pack of `Ns x Np` identical cells with a first‑order ECM and a **single thermal node**; defaults: 40s × 3p.
- **Drive cycle**: Synthetic UDDS‑like profile with bursts and regen; amplitude easily tuned.
- **RTE**: Discharge on the cycle, then charge on a mirrored cycle until SOC returns to the start.
- **Temperature**: Lumped thermal node with UA‑based cooling to ambient guides thermal constraints.
- **Power limits**: Instantaneous discharge/charge limits vs SOC from voltage and SOC windows.
- **Sensitivities**: Cell resistance, cooling (UA), SOC window, and (Ns, Np) affect RTE, peak temperature, and limits.

 

<a id="what-to-look-for"></a>
### What to look for 🔎
- **RTE vs resistance**: Higher resistance lowers RTE and raises temperature; design implication: reduce I²R via lower R or higher Np.
- **Cooling vs safe zone**: Higher UA (better cooling) enlarges safe operating area under aggressive current profiles.
- **SOC window effects**: Narrower windows reduce voltage/thermal stress but restrict usable energy.
- **(Ns, Np) tradeoffs**: Ns scales voltage (power at given I); Np reduces per-cell current and I²R losses.

<a id="repo-layout"></a>
### Repo layout 🗂️
```
battery_pack/
  cell.py           # Single-cell ECM
  thermal.py        # Lumped thermal model
  pack.py           # Ns x Np pack integration
  drive_cycles.py   # Synthetic drive-cycle generator
  simulation.py     # Time-stepping and RTE
  limits.py         # Power-limit curves
  sweep.py          # Parameter sweeps
  plots.py          # Plot helpers
  validation.py     # Sanity checks
scripts/
  run_demo.py       # End-to-end demo + plots
  run_sweeps.py     # Parameter sweeps + heatmaps
  generate_readme_plots.py # Assets for README
tests/
  test_basic.py
assets/             # Generated figures shown above
```

<a id="advanced-features"></a>
### Advanced features and extensions 🧠
- **Multi‑node thermal modeling**: Extend beyond a single lumped node to cell/segment‑level nodes; compare **fin/PCM/liquid‑cooling parameterizations** by adjusting thermal conductance paths and sink temperatures.
- **Aging effects**: Add simple laws for capacity fade and resistance growth with throughput and temperature to study long‑term RTE and power limits.
- **Cell‑to‑cell variation & balancing**: Randomize cell parameters to assess imbalance, then test balancing strategies and their thermal/electrical impact.
- **ML hooks**: Train a lightweight regressor on sweep data to predict peak temperature and RTE, enabling fast design‑space exploration.
- **PyBaMM coupling**: Swap the ECM with PyBaMM models for high‑fidelity electrochemistry when needed.

<a id="license"></a>
### License 📝
MIT. See `LICENSE`.

