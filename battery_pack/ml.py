from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score


@dataclass
class MLModels:
    peak_temp_model: RandomForestRegressor
    RTE_model: RandomForestRegressor
    feature_names: list[str]


def train_models_from_sweep(df: pd.DataFrame) -> Tuple[MLModels, dict]:
    features = [
        "Ns",
        "Np",
        "UA_w_per_k",
        "peak_current_a",
    ]
    X = df[features].to_numpy(dtype=float)
    y_temp = df["peak_temp_k"].to_numpy(dtype=float)
    y_rte = df["RTE_percent"].to_numpy(dtype=float)

    X_train, X_test, yT_train, yT_test = train_test_split(X, y_temp, test_size=0.25, random_state=42)
    _, _, yR_train, yR_test = train_test_split(X, y_rte, test_size=0.25, random_state=42)

    mt = RandomForestRegressor(n_estimators=300, random_state=42)
    mr = RandomForestRegressor(n_estimators=300, random_state=42)
    mt.fit(X_train, yT_train)
    mr.fit(X_train, yR_train)

    predT = mt.predict(X_test)
    predR = mr.predict(X_test)
    metrics = {
        "r2_peak_temp": float(r2_score(yT_test, predT)),
        "r2_RTE": float(r2_score(yR_test, predR)),
    }
    return MLModels(peak_temp_model=mt, RTE_model=mr, feature_names=features), metrics


def save_models(models: MLModels, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "peak_temp_model": models.peak_temp_model,
            "RTE_model": models.RTE_model,
            "feature_names": models.feature_names,
        },
        out_dir / "models.joblib",
    )


def load_models(path: Path) -> MLModels:
    obj = joblib.load(path)
    return MLModels(
        peak_temp_model=obj["peak_temp_model"],
        RTE_model=obj["RTE_model"],
        feature_names=list(obj["feature_names"]),
    )
