"""Persist collected vacancies and ingest run logs."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ingestor.models import IngestRun, Vacancy

logger = logging.getLogger(__name__)

_VACANCY_COLS = {c.key for c in Vacancy.__table__.columns}


def _vacancy_payload(row: dict, *, collected_at: datetime) -> dict:
    payload = {k: v for k, v in row.items() if k in _VACANCY_COLS}
    payload["collected_at"] = collected_at
    return payload


def upsert_vacancies(session: Session, rows: list[dict]) -> int:
    if not rows:
        return 0

    now = datetime.now(timezone.utc)
    saved = 0

    update_cols = tuple(
        c
        for c in (
            "title",
            "analyst_role",
            "employer",
            "area",
            "experience",
            "employment",
            "schedule",
            "salary_from",
            "salary_to",
            "salary_currency",
            "salary_gross",
            "description",
            "key_skills",
            "url",
            "published_at",
            "collected_at",
        )
        if c in _VACANCY_COLS
    )

    for row in rows:
        payload = _vacancy_payload(row, collected_at=now)
        insert_stmt = insert(Vacancy).values(**payload)
        stmt = insert_stmt.on_conflict_do_update(
            index_elements=["source", "external_id"],
            set_={col: insert_stmt.excluded[col] for col in update_cols},
        )
        session.execute(stmt)
        saved += 1

    session.commit()
    return saved


def log_ingest_run(
    session: Session,
    *,
    source: str,
    status: str,
    records_fetched: int,
    started_at: datetime,
    error_message: str | None = None,
) -> None:
    run = IngestRun(
        source=source,
        status=status,
        records_fetched=records_fetched,
        error_message=error_message,
        started_at=started_at,
        finished_at=datetime.now(timezone.utc),
    )
    session.add(run)
    session.commit()
