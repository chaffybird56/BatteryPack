from __future__ import annotations

from pathlib import Path

import click
import matplotlib.pyplot as plt
import numpy as np

from battery_pack.pybamm_adapter import PyBaMMOCV, try_generate_ocv_curve


@click.command()
@click.option("--out-path", type=click.Path(path_type=Path), default=Path("assets/pybamm_ocv_curve.png"))
def main(out_path: Path) -> None:
    """Generate and save a PyBaMM OCV(SOC) curve if available."""
    ocv_curve = try_generate_ocv_curve()
    if ocv_curve is None:
        print("PyBaMM not installed; skipping OCV generation.")
        print("Install with: pip install -r requirements-optional.txt")
        return
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(ocv_curve.soc, ocv_curve.ocv_v, color="#59a14f", linewidth=2)
    ax.set_xlabel("SoC", fontsize=12)
    ax.set_ylabel("OCV (V)", fontsize=12)
    ax.set_title("PyBaMM-generated OCV(SOC) curve", fontsize=14)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"PyBaMM OCV curve saved to: {out_path}")


if __name__ == "__main__":
    main()
