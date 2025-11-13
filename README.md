## 🔋 BatteryPack Simulator: Advanced Battery Simulation & Analysis Framework

<p align="left">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="#testing--quality"><img alt="Tests" src="https://img.shields.io/badge/Tests-pytest%20passing-brightgreen"></a>
  <a href="https://github.com/chaffybird56/BatteryPack"><img alt="Repo" src="https://img.shields.io/badge/GitHub-BatteryPack%20Simulator-181717?logo=github"></a>
  <a href=".github/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/badge/CI-GitHub%20Actions-blue"></a>
</p>

### 📖 What is This Project?

**BatteryPack Simulator** is a comprehensive simulation framework for modeling and analyzing battery pack performance across multiple domains. It combines electro-thermal modeling, safety analysis, and economic evaluation to help engineers design, optimize, and validate battery systems for electric vehicles, aerospace applications, grid storage, and more.

At its core, the framework simulates how battery packs behave under real-world conditions:

- **Electrical behavior** - Voltage, current, and power dynamics as cells charge and discharge
- **Thermal response** - How packs heat up during operation and cool down with different cooling strategies
- **Efficiency analysis** - Energy losses and round-trip efficiency calculations
- **Safety assessment** - Thermal runaway risk, failure modes, and protection algorithms
- **Economic evaluation** - Cost modeling, lifecycle economics, and grid integration revenue

The simulation uses equivalent circuit models (ECM) for individual cells, models them in series-parallel pack configurations, and tracks thermal dynamics as energy flows in and out. It's designed to answer critical design questions like: *"Will this pack configuration meet power requirements?"*, *"How hot will it get during fast charging?"*, *"What's the expected efficiency and lifetime?"*, and *"Does it meet safety requirements?"*

The framework includes industry-standard drive cycles (EPA, WLTP, NEDC) for automotive validation, mission profiles for aerospace applications, fast charging protocols (CCS, CHAdeMO, Supercharger), Monte Carlo uncertainty analysis for reliability assessment, and economic tools for grid storage applications. All results are exportable in multiple formats for integration into design workflows and reports.

---

### 🎯 Key Capabilities

- ✅ **Electro-Thermal Modeling** - Coupled electrical and thermal simulation with multiple cooling strategies
- ✅ **Real-World Validation** - Industry-standard drive cycles and mission profiles
- ✅ **Fast Charging Simulation** - Support for major EV charging protocols with thermal management
- ✅ **Safety Analysis** - Thermal runaway modeling, FMEA, and comprehensive protection algorithms
- ✅ **Uncertainty Quantification** - Monte Carlo analysis for reliability and safety margin assessment
- ✅ **Economic Modeling** - Cost analysis, LCOE calculation, and grid integration revenue modeling
- ✅ **Enterprise Features** - Configuration management, data export, structured logging, parallel processing
- ✅ **Production-Ready Code** - Type hints, comprehensive testing, CI/CD pipeline, code quality tools

---

### 📊 Visual Results & Output Gallery

**Real simulation outputs generated from actual tests** - See the results below:

#### Core Simulation Results

**1. Time Series Analysis** - Current, voltage, power, and SOC during discharge cycle

![Time Series](assets/time_series.png)

**2. Thermal Profile** - Pack temperature evolution during charge/discharge phases

![Temperature Profile](assets/temperature.png)

**3. Round-Trip Efficiency** - Energy efficiency metrics after full charge/discharge cycle

![Round-Trip Efficiency](assets/rte.png)

**4. Power Limits** - Maximum discharge/charge power vs SOC (critical for BMS design)

![Power Limits](assets/power_limits.png)

#### How to Generate These Results

```bash
# Generate README assets (plots shown above)
python scripts/generate_readme_plots.py

# Run full demo with timestamped outputs
python scripts/run_demo.py

# Run parameter sweeps with heatmaps
python scripts/run_sweeps.py

# Run advanced features demo
python scripts/run_advanced_demo.py --thermal-mode fin
```

All outputs are saved with timestamps in `outputs/` directory for reproducibility and documentation.

---

### 🚀 Key Features

#### Core Capabilities
- **Electro-Thermal Modeling** - First-order ECM (R0 + R1||C1) with lumped/multi-node thermal networks
- **Pack-Level Simulation** - Ns×Np series-parallel configurations with cell-to-cell variation
- **Aging & Degradation** - Capacity fade and resistance growth modeling
- **Balancing Strategies** - Passive and active cell balancing algorithms
- **Comprehensive Metrics** - 30+ performance indicators (RTE, C-rate, power density, thermal metrics, etc.)

#### Industry-Specific Features
- **🚗 Automotive** - Real-world drive cycles (EPA, WLTP, NEDC), fast charging (CCS, CHAdeMO, Supercharger), BMS algorithms
- **✈️ Aerospace & Defense** - Mission profiles, Monte Carlo uncertainty quantification, thermal runaway modeling, FMEA
- **⚡ Energy & Grid** - Economic analysis (LCOE), grid integration (V2G), energy arbitrage, capacity market analysis
- **🏥 Healthcare** - Safety analysis, compliance verification, thermal runaway prevention
- **💻 Semiconductors** - Parameter sensitivity analysis, statistical process variation, yield analysis

#### Enterprise Features
- **Configuration Management** - YAML/JSON config files for reproducible simulations
- **Data Export** - CSV, JSON, HDF5 formats for cloud/enterprise integration
- **Structured Logging** - Production-ready logging with configurable levels
- **Parallel Processing** - Multi-core parameter sweeps with progress bars
- **CI/CD Pipeline** - GitHub Actions with automated testing, linting, type checking
- **Code Quality** - Black formatting, MyPy type checking, pytest coverage

> 📚 **For detailed feature documentation, see [FEATURES.md](FEATURES.md)**

---

### 🔧 Installation

```bash
# Clone repository
git clone https://github.com/yourusername/BatteryPack.git
cd BatteryPack

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install pytest-cov black mypy flake8

# Optional: Install PyBaMM integration
pip install -r requirements-optional.txt
```

---

### 🎮 Quick Start

#### Basic Simulation

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

> 📖 **For comprehensive code examples, see [EXAMPLES.md](EXAMPLES.md)**

---

### 📊 Example Use Cases

1. **EV Pack Design** - Optimize series/parallel configuration for target range and power
2. **Fast Charging Analysis** - Simulate CCS/Supercharger sessions with thermal management
3. **Grid Storage Economics** - Calculate LCOE and revenue from V2G/arbitrage
4. **Aerospace Mission Planning** - Verify battery can support mission profile with safety margins
5. **Defense Reliability Analysis** - Monte Carlo simulation to ensure 99.9% reliability
6. **Thermal Management Design** - Compare air/fin/PCM/liquid cooling strategies

> 🎓 **For detailed industry applications, see [INDUSTRY_APPLICATIONS.md](INDUSTRY_APPLICATIONS.md)**

---

### 📁 Project Structure

```
battery_pack/
├── config.py              # Parameter dataclasses
├── config_loader.py       # YAML/JSON configuration management
├── cell.py                # Single-cell ECM model
├── pack.py                # Basic pack model
├── pack_advanced.py       # Advanced pack with variation/aging
├── thermal.py             # Lumped thermal model
├── thermal_network.py     # Multi-node thermal network
├── simulation.py          # Time-stepping simulator
├── drive_cycles.py        # Synthetic drive cycles
├── drive_cycles_real.py   # Real-world drive cycles (EPA, WLTP, NEDC)
├── charging.py            # Fast charging protocols
├── bms.py                 # Battery Management System algorithms
├── safety.py              # Safety analysis and thermal runaway
├── uncertainty.py         # Monte Carlo uncertainty quantification
├── economics.py           # Economic analysis and grid integration
├── mission.py             # Mission profile simulation (aerospace)
├── metrics.py             # Comprehensive battery metrics
├── export.py              # Data export (JSON, HDF5)
└── logger.py              # Structured logging

scripts/
├── run_demo.py            # Basic demo
├── run_advanced_demo.py   # Advanced features demo
├── run_sweeps.py          # Parameter sweeps
├── train_ml.py            # Train ML models
└── generate_readme_plots.py

tests/
├── test_basic.py          # Basic functionality tests
└── test_advanced.py       # Advanced features tests
```

---

### 🧪 Testing & Quality

```bash
# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=battery_pack --cov-report=html

# Type checking
mypy battery_pack/

# Code formatting
black battery_pack/ scripts/ tests/

# Linting
flake8 battery_pack/ scripts/ tests/
```

---

### 📚 Documentation

- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive code examples for all features
- **[FEATURES.md](FEATURES.md)** - Detailed feature documentation  
- **[INDUSTRY_APPLICATIONS.md](INDUSTRY_APPLICATIONS.md)** - Industry-specific use cases
- **API Documentation** - Comprehensive docstrings with type hints in code
- **Configuration Templates** - Use `battery_pack.config_loader.save_config_template()`

### 📋 Table of Contents

- [What is This Project?](#-what-is-this-project)
- [Key Capabilities](#-key-capabilities)
- [Visual Results](#-visual-results--output-gallery)
- [Features](#-key-features)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [Use Cases](#-example-use-cases)
- [Project Structure](#-project-structure)
- [Testing & Quality](#-testing--quality)
- [Documentation](#-documentation)
- [Advanced Features](#-advanced-features)

---

### 🔬 Advanced Features

#### Machine Learning Integration
Train lightweight Random Forest models to predict peak temperature and RTE in milliseconds:

```bash
python scripts/train_ml.py --sweep-csv outputs/sweeps/latest/sweep_results.csv --out-dir outputs/ml
```

#### PyBaMM Integration (Optional)
Swap ECM with high-fidelity PyBaMM models for detailed electrochemistry:

```bash
pip install -r requirements-optional.txt
python scripts/generate_pybamm_ocv.py
python scripts/run_advanced_demo.py --use-pybamm-ocv
```

---

### 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass and code is formatted
5. Submit a pull request

---

### 📄 License

MIT License - See `LICENSE` file for details.

---

### 🙏 Acknowledgments

Built with:
- NumPy, SciPy, Pandas for numerical computing
- Matplotlib, Seaborn for visualization
- Joblib for parallel processing
- PyYAML for configuration
- H5py for efficient data storage
- scikit-learn for ML capabilities

---

### 📧 Contact & Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**A comprehensive toolkit for battery pack simulation, analysis, and optimization across industries.**
