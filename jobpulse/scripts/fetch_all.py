#!/usr/bin/env python3
"""Full fetch: HH + SuperJob -> parquet (same pipeline as Docker ingestor)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGESTOR_SRC = ROOT / "services" / "ingestor" / "src"
sys.path.insert(0, str(INGESTOR_SRC))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

import pandas as pd  # noqa: E402

from ingestor.collectors.hh import collect_hh_analyst_vacancies  # noqa: E402
from ingestor.collectors.hh_detail import enrich_hh_rows_with_details  # noqa: E402
from ingestor.collectors.superjob import collect_superjob_analyst_vacancies  # noqa: E402
from ingestor.config import settings  # noqa: E402
from ingestor.row_processing import merge_and_clean_rows  # noqa: E402

OUT_DIR = ROOT / "data" / "processed"
PARQUET = OUT_DIR / "vacancies.parquet"
JSON_OUT = OUT_DIR / "vacancies.json"


def _serialize_rows(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        row = dict(r)
        if row.get("published_at") and hasattr(row["published_at"], "isoformat"):
            row["published_at"] = row["published_at"].isoformat()
        out.append(row)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: list[dict] = []

    print("Fetching HH.ru — all vacancies (4 roles, RU+EN)...")
    hh_all = collect_hh_analyst_vacancies(only_with_salary=False)
    all_rows.extend(hh_all)
    print(f"  HH all: {len(hh_all)}")

    if settings.ingest_collect_salary_stream:
        print("Fetching HH.ru — only_with_salary...")
        hh_sal = collect_hh_analyst_vacancies(
            only_with_salary=True,
            max_pages=settings.ingest_max_pages_salary,
        )
        all_rows.extend(hh_sal)
        print(f"  HH salary stream: {len(hh_sal)}")

    if settings.superjob_api_key:
        print("Fetching SuperJob...")
        try:
            sj_rows = collect_superjob_analyst_vacancies(max_pages=settings.ingest_max_pages)
            all_rows.extend(sj_rows)
            print(f"  SuperJob: {len(sj_rows)}")
        except Exception as exc:
            print(f"  SuperJob error: {exc}")
    else:
        print("  SuperJob skipped (no SUPERJOB_API_KEY)")

    rows = merge_and_clean_rows(all_rows)
    print(f"After classify + dedup: {len(rows)}")

    print("Enriching HH details (salary + skills)...")
    rows = enrich_hh_rows_with_details(rows)
    with_salary = sum(1 for r in rows if r.get("salary_from") or r.get("salary_to"))
    with_skills = sum(1 for r in rows if r.get("key_skills"))
    print(f"  with salary: {with_salary}, with skills: {with_skills}")

    for r in rows:
        r["collected_at"] = datetime.now(timezone.utc).isoformat()

    df = pd.DataFrame(_serialize_rows(rows))
    df.to_parquet(PARQUET, index=False)
    JSON_OUT.write_text(
        json.dumps({"count": len(rows), "items": _serialize_rows(rows)}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nSkillCompass: {len(rows)} vacancies -> {PARQUET}")


if __name__ == "__main__":
    main()
