"""Merge, classify and deduplicate collected vacancy rows."""

from __future__ import annotations

from ingestor.filters import is_relevant_analyst_vacancy
from ingestor.role_classifier import resolve_vacancy_role
from ingestor.roles import ANALYST_ROLE_LABELS
from ingestor.salary_utils import sanitize_salary_row


def _combine_rows(prev: dict, new: dict) -> dict:
    """Merge duplicate (source, id): take best fields from both."""
    if _row_score(new) >= _row_score(prev):
        primary, secondary = new, prev
    else:
        primary, secondary = prev, new
    out = dict(primary)
    for key in (
        "salary_from",
        "salary_to",
        "salary_currency",
        "salary_gross",
        "key_skills",
        "experience",
        "area",
        "employment",
        "schedule",
        "published_at",
        "employer",
        "title",
        "url",
    ):
        if out.get(key) in (None, ""):
            val = secondary.get(key)
            if val not in (None, ""):
                out[key] = val
    return out


def merge_and_clean_rows(rows: list[dict]) -> list[dict]:
    """Dedupe by (source, external_id), classify role from title, drop noise, cap salaries."""
    best: dict[tuple[str, str], dict] = {}

    for row in rows:
        title = row.get("title") or ""
        if not is_relevant_analyst_vacancy(title):
            continue

        search_role = row.get("analyst_role")
        role = resolve_vacancy_role(title, search_role)
        if not role:
            continue

        row = sanitize_salary_row({**row, "analyst_role": role})
        row["role_label"] = ANALYST_ROLE_LABELS.get(role, role)

        key = (str(row["source"]), str(row["external_id"]))
        if key not in best:
            best[key] = row
            continue

        best[key] = sanitize_salary_row(_combine_rows(best[key], row))

    return list(best.values())


def _row_score(row: dict) -> int:
    score = 0
    if row.get("salary_from") or row.get("salary_to"):
        score += 2
    if row.get("key_skills"):
        score += 1
    if row.get("description"):
        score += 1
    return score
