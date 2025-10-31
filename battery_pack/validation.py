from __future__ import annotations

import numpy as np
import pandas as pd


def check_soc_bounds(df: pd.DataFrame) -> bool:
	s = df["soc"].to_numpy()
	return bool((s.min() >= -1e-6) and (s.max() <= 1.0 + 1e-6))


def check_temperature_reasonable(df: pd.DataFrame) -> bool:
	T = df["temp_k"].to_numpy()
	return bool((T > 200.0).all() and (T < 500.0).all())


def energy_balance_sanity(df: pd.DataFrame) -> float:
	"""Return absolute Wh magnitude of net energy; 
	values near zero are expected for a symmetric discharge/charge cycle."""
	E_wh = float(np.trapz(df["power_w"].to_numpy(), df["time_s"]) / 3600.0)
	return abs(E_wh)

