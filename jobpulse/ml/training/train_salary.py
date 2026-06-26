"""Train salary regression model for SkillCompass."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml"))

import joblib
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split

from load_data import load_vacancies, prepare_salary_target  # noqa: E402

ARTIFACTS = ROOT / "ml" / "artifacts"
MODEL_PATH = ARTIFACTS / "salary_model.joblib"
METRICS_PATH = ARTIFACTS / "salary_metrics.json"

CAT_FEATURES = ["analyst_role", "experience", "area", "source", "employment", "salary_spec"]
NUM_FEATURES: list[str] = []


def main() -> None:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    df = load_vacancies()
    df = prepare_salary_target(df)
    df = df.dropna(subset=["salary_mid"])
    if len(df) < 50:
        raise SystemExit(f"Not enough labeled salaries: {len(df)} (need ~50+)")

    for col in CAT_FEATURES:
        df[col] = df[col].fillna("unknown").astype(str)

    X = df[CAT_FEATURES + NUM_FEATURES]
    y = df["salary_mid"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    naive_pred = np.full_like(y_test, fill_value=y_train.median())
    naive_mae = mean_absolute_error(y_test, naive_pred)

    model = CatBoostRegressor(
        iterations=300,
        depth=6,
        learning_rate=0.08,
        loss_function="RMSE",
        verbose=False,
        random_seed=42,
    )
    model.fit(X_train, y_train, cat_features=CAT_FEATURES)

    pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, pred)
    rmse = float(np.sqrt(mean_squared_error(y_test, pred)))

    bundle = {
        "model": model,
        "cat_features": CAT_FEATURES,
        "num_features": NUM_FEATURES,
        "feature_columns": CAT_FEATURES + NUM_FEATURES,
    }
    joblib.dump(bundle, MODEL_PATH)

    metrics = {
        "samples": len(df),
        "test_mae": round(mae, 2),
        "test_rmse": round(rmse, 2),
        "naive_mae": round(float(naive_mae), 2),
        "beats_naive": mae < naive_mae,
    }
    METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    print(f"Model saved: {MODEL_PATH}")
    print(f"Metrics: MAE={mae:.0f} RMSE={rmse:.0f} (naive MAE={naive_mae:.0f})")
    print(f"Beats naive: {metrics['beats_naive']}")


if __name__ == "__main__":
    main()
