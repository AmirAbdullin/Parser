from __future__ import annotations

from functools import lru_cache

import pandas as pd
from sqlalchemy import create_engine, text


@lru_cache(maxsize=1)
def get_engine(database_url: str):
    return create_engine(database_url, pool_pre_ping=True)


def read_vacancies(database_url: str) -> pd.DataFrame:
    engine = get_engine(database_url)
    return pd.read_sql(text("SELECT * FROM vacancies ORDER BY collected_at DESC"), engine)


def read_salary_history(
    database_url: str,
    *,
    role: str | None = None,
    experience: str | None = None,
) -> list[dict]:
    engine = get_engine(database_url)
    clauses = ["1=1"]
    params: dict = {}
    if role:
        clauses.append("analyst_role = :role")
        params["role"] = role
    if experience:
        clauses.append("experience = :experience")
        params["experience"] = experience
    sql = f"""
        SELECT snapshot_at, analyst_role, experience, avg_salary, median_salary, vacancy_count
        FROM salary_snapshots
        WHERE {' AND '.join(clauses)}
        ORDER BY snapshot_at, analyst_role, experience
    """
    df = pd.read_sql(text(sql), engine, params=params)
    if df.empty:
        return []
    df["snapshot_at"] = df["snapshot_at"].astype(str)
    return df.to_dict(orient="records")


def read_last_successful_ingest(database_url: str) -> dict | None:
    engine = get_engine(database_url)
    sql = text("""
        SELECT finished_at, records_fetched, source, status
        FROM ingest_runs
        WHERE status = 'ok' AND source = 'all'
        ORDER BY finished_at DESC NULLS LAST
        LIMIT 1
    """)
    df = pd.read_sql(sql, engine)
    if df.empty:
        return None
    row = df.iloc[0]
    finished = row["finished_at"]
    return {
        "finished_at": str(finished) if finished is not None else None,
        "records_fetched": int(row["records_fetched"]),
        "source": str(row["source"]),
        "status": str(row["status"]),
    }
