## BatteryPack: Electro-Thermal N-Cell Pack Modeling & Analysis

This project provides a complete, observable, and testable battery pack simulator with:
- **Electrical ECM** per cell (R0 + R1||C1) and smooth OCV(SOC)
- **Lumped thermal node** for the pack with ambient cooling
- **Drive-cycle current input** (synthetic UDDS-like)
- **Metrics**: Round-Trip Efficiency (RTE), temperature rise traces, power-limit curves
- **Sensitivity & sweeps**: series/parallel counts, thermal conductance, current profiles, and internal resistance impact
- **Validation checks** and unit tests

The README serves as the requested one-page summary with plots and screenshots embedded.

### Quick start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Generate assets for README (plots)
python scripts/generate_readme_plots.py

# Run a demo simulation with outputs timestamped under outputs/
python scripts/run_demo.py

# Run parameter sweeps and heatmaps
python scripts/run_sweeps.py

# Run tests
pytest -q
```

### One-page summary (results + design connections)
- **System setup**: Pack of `Ns x Np` identical cells with ECM and a **single thermal node**. Default: 40s x 3p.
- **Drive cycle**: Synthetic UDDS-like profile with bursts and regen; adjustable amplitude.
- **RTE**: Computed by discharging on the cycle then charging on a mirrored profile until SOC returns to the start.
- **Temperature**: Lumped node captures heat generation and UA-based cooling to ambient.
- **Power limits**: Instantaneous discharge/charge limits vs SOC based on voltage and SOC windows.
- **Sensitivities**: Impact of cell resistance, cooling (UA), SOC window, and (Ns, Np) on RTE, peak temperature, and limits.

### Embedded plots (generated via `scripts/generate_readme_plots.py`)
![Time Series](assets/time_series.png)
![Temperature](assets/temperature.png)
![RTE](assets/rte.png)
![Power Limits](assets/power_limits.png)

### What to look for
- **RTE vs resistance**: Higher resistance lowers RTE and raises temperature; design implication: reduce I²R via lower R or higher Np.
- **Cooling vs safe zone**: Higher UA (better cooling) enlarges safe operating area under aggressive current profiles.
- **SOC window effects**: Narrower windows reduce voltage/thermal stress but restrict usable energy.
- **(Ns, Np) tradeoffs**: Ns scales voltage (power at given I); Np reduces per-cell current and I²R losses.

### Repo layout
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

### Extendability (ideas included or ready to add)
- **Thermal modeling**: Multi-node pack cooling; fin/PCM/liquid-cooling parameterizations.
- **Aging**: Simple capacity/resistance growth with throughput and temperature.
- **Cell-to-cell variation**: Randomized cell parameters and balancing strategies.
- **ML hooks**: Fit a lightweight regressor from sweep data to predict peak temperature and RTE (ready to add in a follow-up PR).
- **PyBaMM coupling**: Swap ECM with PyBaMM models for high-fidelity studies.

### License
MIT. See `LICENSE`.

