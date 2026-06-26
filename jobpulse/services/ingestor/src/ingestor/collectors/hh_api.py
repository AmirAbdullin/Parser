"""HH.ru public vacancies API collector."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

import requests

from ingestor.config import settings
from ingestor.roles import ANALYST_ROLES, hh_text_query

logger = logging.getLogger(__name__)

API_URL = "https://api.hh.ru/vacancies"


def _headers() -> dict[str, str]:
    ua = settings.hh_user_agent
    return {"HH-User-Agent": ua}


def _parse_salary(raw: dict[str, Any] | None) -> tuple[float | None, float | None, str | None, bool | None]:
    if not raw:
        return None, None, None, None
    return raw.get("from"), raw.get("to"), raw.get("currency"), raw.get("gross")


def _normalize_item(item: dict[str, Any], *, analyst_role: str) -> dict[str, Any]:
    salary_from, salary_to, currency, gross = _parse_salary(item.get("salary"))
    area = (item.get("area") or {}).get("name")
    experience = (item.get("experience") or {}).get("name")
    employment = (item.get("employment") or {}).get("name")
    schedule = (item.get("schedule") or {}).get("name")
    employer = (item.get("employer") or {}).get("name")
    published = item.get("published_at")
    published_at = None
    if published:
        published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))

    return {
        "source": "hh",
        "external_id": str(item["id"]),
        "title": item.get("name") or "",
        "analyst_role": analyst_role,
        "employer": employer,
        "area": area,
        "experience": experience,
        "employment": employment,
        "schedule": schedule,
        "salary_from": salary_from,
        "salary_to": salary_to,
        "salary_currency": currency,
        "salary_gross": gross,
        "description": None,
        "url": item.get("alternate_url"),
        "published_at": published_at,
    }


def collect_hh_vacancies_for_role(
    *,
    analyst_role: str,
    text: str,
    area_id: int | None = None,
    max_pages: int | None = None,
    only_with_salary: bool = False,
    fetch_descriptions: bool = False,
) -> list[dict[str, Any]]:
    area_id = area_id if area_id is not None else settings.ingest_area_id
    if max_pages is None:
        max_pages = settings.ingest_max_pages

    results: list[dict[str, Any]] = []
    page = 0

    while True:
        if max_pages > 0 and page >= max_pages:
            break

        params: dict[str, Any] = {
            "text": text,
            "per_page": 100,
            "page": page,
        }
        if area_id:
            params["area"] = area_id
        if only_with_salary:
            params["only_with_salary"] = True

        resp = requests.get(API_URL, params=params, headers=_headers(), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items = payload.get("items") or []
        if not items:
            break

        for item in items:
            row = _normalize_item(item, analyst_role=analyst_role)
            results.append(row)

        page += 1
        total_pages = payload.get("pages", 0)
        if page >= total_pages:
            break

    tag = " salary" if only_with_salary else ""
    logger.info(
        "HH API%s role=%s query=%r collected %s vacancies",
        tag,
        analyst_role,
        text,
        len(results),
    )
    return results


def collect_hh_analyst_vacancies(
    *,
    area_id: int | None = None,
    max_pages: int | None = None,
    only_with_salary: bool = False,
    fetch_descriptions: bool = False,
) -> list[dict[str, Any]]:
    area_id = area_id if area_id is not None else settings.ingest_area_id
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for role_key in ANALYST_ROLES:
        text = hh_text_query(role_key)
        batch = collect_hh_vacancies_for_role(
            analyst_role=role_key,
            text=text,
            area_id=area_id,
            max_pages=max_pages,
            only_with_salary=only_with_salary,
            fetch_descriptions=fetch_descriptions,
        )
        for row in batch:
            if row["external_id"] in seen:
                continue
            seen.add(row["external_id"])
            results.append(row)

    tag = " salary-only" if only_with_salary else ""
    logger.info("HH API%s total unique analyst vacancies: %s", tag, len(results))
    return results
