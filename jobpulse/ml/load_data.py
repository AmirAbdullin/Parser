"""Shared data loading for EDA and ML."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "processed" / "vacancies.parquet"
RAW_JSON = ROOT / "data" / "raw" / "hh_analysts_sample.json"


def load_vacancies() -> pd.DataFrame:
    if PARQUET.exists():
        return pd.read_parquet(PARQUET)
    if RAW_JSON.exists():
        import json

        payload = json.loads(RAW_JSON.read_text(encoding="utf-8"))
        return pd.DataFrame(payload.get("items", []))
    raise FileNotFoundError(
        "No data. Run: python scripts/export_parquet_from_db.py "
        "(or scripts/fetch_all.py without Docker DB)"
    )


def prepare_salary_target(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["salary_from"] = pd.to_numeric(out.get("salary_from"), errors="coerce")
    out["salary_to"] = pd.to_numeric(out.get("salary_to"), errors="coerce")
    out["salary_mid"] = out[["salary_from", "salary_to"]].mean(axis=1)
    out.loc[out["salary_mid"].isna(), "salary_mid"] = out["salary_from"]
    out.loc[out["salary_mid"].isna(), "salary_mid"] = out["salary_to"]
    lo, hi = 30_000, 600_000
    mask = out["salary_mid"].notna() & ((out["salary_mid"] < lo) | (out["salary_mid"] > hi))
    out.loc[mask, ["salary_from", "salary_to", "salary_mid"]] = pd.NA
    return add_salary_spec(out)


def add_salary_spec(df: pd.DataFrame) -> pd.DataFrame:
    """How salary is stated: from only, to only, or full range."""
    out = df.copy()
    has_from = out["salary_from"].notna()
    has_to = out["salary_to"].notna()
    out["salary_spec"] = "from_only"
    out.loc[has_to & ~has_from, "salary_spec"] = "to_only"
    out.loc[has_from & has_to, "salary_spec"] = "range"
    out.loc[~has_from & ~has_to, "salary_spec"] = "none"
    return out
