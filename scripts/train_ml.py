from __future__ import annotations

from pathlib import Path

import click
import pandas as pd

from battery_pack.ml import save_models, train_models_from_sweep


@click.command()
@click.option("--sweep-csv", type=click.Path(exists=True, dir_okay=False, path_type=Path), default=Path("outputs/sweeps/latest/sweep_results.csv"))
@click.option("--out-dir", type=click.Path(file_okay=False, path_type=Path), default=Path("outputs/ml"))
def main(sweep_csv: Path, out_dir: Path) -> None:
	df = pd.read_csv(sweep_csv)
	models, metrics = train_models_from_sweep(df)
	save_models(models, out_dir)
	print(f"ML models saved to: {out_dir} | Metrics: {metrics}")


if __name__ == "__main__":
	main()

