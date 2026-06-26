#!/usr/bin/env python3
"""Export vacancies from PostgreSQL to parquet for ML training.

From Windows (Docker Postgres on localhost):

  cd jobpulse
  python scripts/export_parquet_from_db.py

Uses DATABASE_URL from .env; rewrites host ``db`` -> ``localhost`` for host runs.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "services" / "ingestor" / "src"))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import pandas as pd  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from ingestor.config import settings  # noqa: E402
from ingestor.roles import ANALYST_ROLE_LABELS  # noqa: E402

OUT = ROOT / "data" / "processed" / "vacancies.parquet"


def resolve_database_url() -> str:
    """Build URL for running the script on the host against Docker Postgres."""
    url = os.getenv("DATABASE_URL") or settings.database_url
    url = url.replace("@db:", "@localhost:")
    if "localhost" not in url and "127.0.0.1" not in url:
        user = os.getenv("DB_USER", "datapulse")
        password = os.getenv("DB_PASSWORD", "datapulse_secret")
        db = os.getenv("DB_NAME", "datapulse")
        url = f"postgresql://{user}:{password}@localhost:5432/{db}"
    return url


def main() -> None:
    url = resolve_database_url()
    print(f"Connecting: {url.split('@')[-1]}")  # hide password
    engine = create_engine(url)
    df = pd.read_sql(text("SELECT * FROM vacancies"), engine)
    if "role_label" not in df.columns:
        df["role_label"] = df["analyst_role"].map(ANALYST_ROLE_LABELS)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT, index=False)
    print(f"Exported {len(df)} rows -> {OUT}")


if __name__ == "__main__":
    main()