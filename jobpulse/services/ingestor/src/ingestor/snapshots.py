"""Aggregate salary snapshots after ingest."""

from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd
from sqlalchemy.orm import Session

from ingestor.models import SalarySnapshot, Vacancy


def save_salary_snapshots(session: Session) -> int:
    rows = session.query(Vacancy).all()
    if not rows:
        return 0

    data = []
    for v in rows:
        sf, st = v.salary_from, v.salary_to
        if sf is None and st is None:
            continue
        mid = (sf + st) / 2 if sf is not None and st is not None else (sf or st)
        if mid is None:
            continue
        data.append(
            {
                "analyst_role": v.analyst_role or "unknown",
                "experience": v.experience or "unknown",
                "salary_mid": float(mid),
            }
        )

    if not data:
        return 0

    df = pd.DataFrame(data)
    now = datetime.now(timezone.utc)
    saved = 0
    for (role, exp), grp in df.groupby(["analyst_role", "experience"]):
        session.add(
            SalarySnapshot(
                snapshot_at=now,
                analyst_role=str(role),
                experience=str(exp),
                avg_salary=float(grp["salary_mid"].mean()),
                median_salary=float(grp["salary_mid"].median()),
                vacancy_count=int(len(grp)),
            )
        )
        saved += 1
    session.commit()
    return saved
