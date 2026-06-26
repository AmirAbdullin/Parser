from __future__ import annotations

import json
from collections import Counter
from functools import lru_cache

import pandas as pd

from area_utils import normalize_city_name
from config import settings
from db import read_salary_history, read_vacancies
from experience_utils import EXPERIENCE_OPTIONS, experience_variants
from schemas import SkillOut, VacancyOut

ROLE_LABELS = {
    "business_analyst": "Бизнес-аналитик",
    "systems_analyst": "Системный аналитик",
    "product_analyst": "Продуктовый аналитик",
    "data_analyst": "Аналитик данных",
}


def _attach_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "role_label" not in out.columns and "analyst_role" in out.columns:
        out["role_label"] = out["analyst_role"].map(ROLE_LABELS).fillna(out["analyst_role"])
    return out


@lru_cache(maxsize=1)
def load_dataframe() -> pd.DataFrame:
    if settings.use_db:
        try:
            df = read_vacancies(settings.database_url)
            if not df.empty:
                return _attach_labels(df)
        except Exception:
            pass
    path = settings.parquet_file
    if not path.exists():
        raise FileNotFoundError(f"Data not found: {path}. Run ingestor or scripts/fetch_all.py")
    df = pd.read_parquet(path)
    return _attach_labels(df)


def get_city_options(df: pd.DataFrame | None = None) -> list[str]:
    df = df if df is not None else load_dataframe()
    cities: set[str] = set()
    for raw in df["area"].dropna().unique():
        city = normalize_city_name(str(raw))
        if city:
            cities.add(city)
    return sorted(cities)


def get_stats() -> dict:
    df = load_dataframe()
    paid = df[df["salary_from"].notna() | df["salary_to"].notna()].copy()
    paid["salary_mid"] = paid[["salary_from", "salary_to"]].mean(axis=1)
    paid.loc[paid["salary_mid"].isna(), "salary_mid"] = paid["salary_from"]
    paid.loc[paid["salary_mid"].isna(), "salary_mid"] = paid["salary_to"]
    paid = paid.dropna(subset=["salary_mid"])

    avg_by_role: dict[str, float] = {}
    roles_by_source: dict[str, dict[str, int]] = {}
    role_counts: dict[str, int] = {}
    if "role_label" in df.columns:
        role_counts = df["role_label"].value_counts().to_dict()
        if "source" in df.columns:
            grouped = df.groupby(["role_label", "source"], dropna=False).size().unstack(fill_value=0)
            for role in grouped.index:
                roles_by_source[str(role)] = {
                    str(src): int(grouped.loc[role, src]) for src in grouped.columns
                }

    if not paid.empty and "role_label" in paid.columns:
        grouped = paid.groupby("role_label", dropna=False)["salary_mid"].mean()
        avg_by_role = {str(role): round(float(val), 0) for role, val in grouped.items()}

    last_ingest = None
    if settings.use_db:
        try:
            from db import read_last_successful_ingest

            last_ingest = read_last_successful_ingest(settings.database_url)
        except Exception:
            pass

    return {
        "total_vacancies": len(df),
        "sources": df["source"].value_counts().to_dict(),
        "roles": {str(k): int(v) for k, v in role_counts.items()},
        "roles_by_source": roles_by_source,
        "with_salary": int(len(paid)),
        "avg_salary_by_role": avg_by_role,
        "updated_at": str(df["collected_at"].max()) if "collected_at" in df.columns else None,
        "last_ingest_at": last_ingest.get("finished_at") if last_ingest else None,
        "last_ingest_records": last_ingest.get("records_fetched") if last_ingest else None,
        "data_source": "postgresql" if settings.use_db else "parquet",
    }


def get_filter_options() -> dict:
    df = load_dataframe()
    cities = get_city_options(df)
    return {
        "areas": cities,
        "cities": cities,
        "experiences": list(EXPERIENCE_OPTIONS),
        "sources": ["all", "hh", "superjob"],
        "roles": ROLE_LABELS,
    }


def query_vacancies(
    *,
    role: str | None = None,
    source: str | None = None,
    experience: str | None = None,
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[VacancyOut], int]:
    df = load_dataframe().copy()
    if role:
        df = df[df["analyst_role"] == role]
    if source and source != "all":
        df = df[df["source"] == source]
    if experience:
        variants = experience_variants(experience)
        if variants:
            df = df[df["experience"].isin(variants)]
        else:
            df = df[df["experience"] == experience]
    if search:
        mask = df["title"].str.contains(search, case=False, na=False)
        df = df[mask]
    total = len(df)
    page = df.iloc[offset : offset + limit]
    items = [VacancyOut.from_row(row) for _, row in page.iterrows()]
    return items, total


def get_top_skills(
    *,
    analyst_role: str,
    experience: str | None = None,
    source: str | None = None,
    limit: int = 10,
) -> tuple[list[SkillOut], int]:
    """Top HH key_skills for role (+ experience). Returns (skills, vacancy_count)."""
    df = load_dataframe()
    df = df[df["analyst_role"] == analyst_role]
    if source and source != "all":
        df = df[df["source"] == source]
    else:
        df = df[df["source"] == "hh"]
    if experience:
        variants = experience_variants(experience)
        if variants:
            df = df[df["experience"].isin(variants)]
        else:
            df = df[df["experience"] == experience]

    with_skills = df[df["key_skills"].notna()] if "key_skills" in df.columns else df.iloc[0:0]
    vacancy_count = len(with_skills)

    counter: Counter[str] = Counter()
    for raw in with_skills.get("key_skills", pd.Series(dtype=object)).dropna():
        try:
            skills = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            continue
        if isinstance(skills, list):
            for name in skills:
                name = str(name).strip()
                if name:
                    counter[name] += 1

    top = [SkillOut(name=name, count=count) for name, count in counter.most_common(limit)]
    return top, vacancy_count


def get_salary_history(*, role: str | None = None, experience: str | None = None) -> list[dict]:
    if not settings.use_db:
        return _salary_history_from_vacancies(role=role, experience=experience)
    try:
        rows = read_salary_history(settings.database_url, role=role, experience=experience)
        if rows:
            return rows
    except Exception:
        pass
    return _salary_history_from_vacancies(role=role, experience=experience)


def _salary_history_from_vacancies(*, role: str | None, experience: str | None) -> list[dict]:
    """Fallback: aggregate by published month when snapshots table is empty."""
    df = load_dataframe()
    df = df[df["salary_from"].notna() | df["salary_to"].notna()].copy()
    if role:
        df = df[df["analyst_role"] == role]
    if experience:
        variants = experience_variants(experience)
        if variants:
            df = df[df["experience"].isin(variants)]
        else:
            df = df[df["experience"] == experience]
    if df.empty or "published_at" not in df.columns:
        return []
    df["salary_mid"] = df[["salary_from", "salary_to"]].mean(axis=1)
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce")
    df = df.dropna(subset=["published_at", "salary_mid"])
    if df.empty:
        return []
    df["month"] = df["published_at"].dt.to_period("M").astype(str)
    out = []
    for month, grp in df.groupby("month"):
        out.append(
            {
                "snapshot_at": f"{month}-01",
                "analyst_role": role or "all",
                "experience": experience or "all",
                "avg_salary": float(grp["salary_mid"].mean()),
                "median_salary": float(grp["salary_mid"].median()),
                "vacancy_count": int(len(grp)),
            }
        )
    return sorted(out, key=lambda x: x["snapshot_at"])


def load_metrics() -> dict:
    path = settings.metrics_file
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}
