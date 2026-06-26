"""Run data collection from all sources."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import sessionmaker

from ingestor.collectors.hh import collect_hh_analyst_vacancies
from ingestor.collectors.hh_detail import enrich_hh_rows_with_details
from ingestor.collectors.superjob import collect_superjob_analyst_vacancies
from ingestor.config import settings
from ingestor.row_processing import merge_and_clean_rows
from ingestor.snapshots import save_salary_snapshots
from ingestor.storage import log_ingest_run, upsert_vacancies

logger = logging.getLogger(__name__)


def run_ingest(session_factory: sessionmaker) -> dict[str, int]:
    stats: dict[str, int] = {}
    all_rows: list[dict] = []

    started = datetime.now(timezone.utc)
    try:
        hh_all = collect_hh_analyst_vacancies(only_with_salary=False)
        all_rows.extend(hh_all)
        stats["hh_all_raw"] = len(hh_all)

        if settings.ingest_collect_salary_stream:
            salary_pages = settings.ingest_max_pages_salary
            hh_salary = collect_hh_analyst_vacancies(
                only_with_salary=True,
                max_pages=salary_pages,
            )
            all_rows.extend(hh_salary)
            stats["hh_salary_raw"] = len(hh_salary)
        else:
            stats["hh_salary_raw"] = 0
    except Exception as exc:
        logger.exception("HH ingest failed")
        stats["hh_all_raw"] = 0
        stats["hh_salary_raw"] = 0
        session = session_factory()
        try:
            log_ingest_run(
                session,
                source="hh",
                status="error",
                records_fetched=0,
                started_at=started,
                error_message=str(exc),
            )
        finally:
            session.close()

    if settings.superjob_api_key:
        started_sj = datetime.now(timezone.utc)
        try:
            sj_rows = collect_superjob_analyst_vacancies()
            all_rows.extend(sj_rows)
            stats["superjob_raw"] = len(sj_rows)
        except Exception as exc:
            logger.exception("SuperJob ingest failed")
            stats["superjob_raw"] = 0
            session = session_factory()
            try:
                log_ingest_run(
                    session,
                    source="superjob",
                    status="error",
                    records_fetched=0,
                    started_at=started_sj,
                    error_message=str(exc),
                )
            finally:
                session.close()
    else:
        logger.warning("SUPERJOB_API_KEY not set — skipping SuperJob")
        stats["superjob_raw"] = 0

    cleaned = merge_and_clean_rows(all_rows)
    stats["clean_unique"] = len(cleaned)

    cleaned = enrich_hh_rows_with_details(cleaned)
    stats["with_salary"] = sum(
        1 for r in cleaned if r.get("salary_from") is not None or r.get("salary_to") is not None
    )
    stats["with_skills"] = sum(1 for r in cleaned if r.get("key_skills"))

    session = session_factory()
    try:
        count = upsert_vacancies(session, cleaned)
        log_ingest_run(session, source="all", status="ok", records_fetched=count, started_at=started)
        stats["saved"] = count
        stats["snapshots"] = save_salary_snapshots(session)
    finally:
        session.close()

    return stats


def run_skills_backfill(session_factory: sessionmaker) -> dict[str, int]:
    """Re-fetch key_skills (and missing salary) for HH rows already in DB."""
    from sqlalchemy import select

    from ingestor.models import Vacancy

    session = session_factory()
    try:
        rows_db = session.scalars(
            select(Vacancy).where(Vacancy.source == "hh", Vacancy.key_skills.is_(None))
        ).all()
        rows = [
            {
                "source": r.source,
                "external_id": r.external_id,
                "title": r.title,
                "analyst_role": r.analyst_role,
                "employer": r.employer,
                "area": r.area,
                "experience": r.experience,
                "employment": r.employment,
                "schedule": r.schedule,
                "salary_from": r.salary_from,
                "salary_to": r.salary_to,
                "salary_currency": r.salary_currency,
                "salary_gross": r.salary_gross,
                "description": r.description,
                "key_skills": r.key_skills,
                "url": r.url,
                "published_at": r.published_at,
            }
            for r in rows_db
        ]
    finally:
        session.close()

    stats: dict[str, int] = {"hh_without_skills": len(rows)}
    if not rows:
        return stats

    enriched = enrich_hh_rows_with_details(rows, skills_only=True)
    stats["with_skills"] = sum(1 for r in enriched if r.get("key_skills"))

    session = session_factory()
    try:
        stats["saved"] = upsert_vacancies(session, enriched)
    finally:
        session.close()

    return stats
