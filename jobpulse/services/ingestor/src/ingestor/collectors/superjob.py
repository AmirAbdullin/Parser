"""SuperJob.ru vacancies API — IT analyst niches only."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import requests

from ingestor.config import settings
from ingestor.roles import ANALYST_ROLES

logger = logging.getLogger(__name__)

API_URL = "https://api.superjob.ru/2.0/vacancies/"


def _headers() -> dict[str, str]:
    if not settings.superjob_api_key:
        raise ValueError(
            "SUPERJOB_API_KEY is empty. Register at https://api.superjob.ru/register/"
        )
    return {"X-Api-App-Id": settings.superjob_api_key}


def _normalize_item(item: dict[str, Any], *, analyst_role: str) -> dict[str, Any]:
    published_at = None
    if item.get("date_published"):
        published_at = datetime.fromtimestamp(item["date_published"], tz=timezone.utc)

    payment_from = item.get("payment_from")
    payment_to = item.get("payment_to")
    if payment_from == 0:
        payment_from = None
    if payment_to == 0:
        payment_to = None

    town = (item.get("town") or {}).get("title")
    experience = (item.get("experience") or {}).get("title")
    type_of_work = (item.get("type_of_work") or {}).get("title")

    return {
        "source": "superjob",
        "external_id": str(item["id"]),
        "title": item.get("profession") or item.get("vacancyRichText") or "",
        "analyst_role": analyst_role,
        "employer": item.get("firm_name"),
        "area": town,
        "experience": experience,
        "employment": type_of_work,
        "schedule": None,
        "salary_from": float(payment_from) if payment_from is not None else None,
        "salary_to": float(payment_to) if payment_to is not None else None,
        "salary_currency": item.get("currency") or "rub",
        "salary_gross": None,
        "description": item.get("vacancyRichText"),
        "url": item.get("link"),
        "published_at": published_at,
    }


def collect_superjob_vacancies_for_role(
    *,
    analyst_role: str,
    keyword: str,
    town_id: int = 0,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    max_pages = max_pages or settings.ingest_max_pages
    results: list[dict[str, Any]] = []
    page = 0

    while page < max_pages:
        params: dict[str, Any] = {
            "keyword": keyword,
            "count": 100,
            "page": page,
        }
        if town_id:
            params["town"] = town_id

        resp = requests.get(API_URL, params=params, headers=_headers(), timeout=30)
        resp.raise_for_status()
        payload = resp.json()
        items = payload.get("objects") or []
        if not items:
            break

        for item in items:
            results.append(_normalize_item(item, analyst_role=analyst_role))

        page += 1
        total = payload.get("total") or 0
        total_pages = max(1, (total + 99) // 100)
        if page >= total_pages:
            break

    logger.info(
        "SuperJob role=%s query=%r collected %s vacancies",
        analyst_role,
        keyword,
        len(results),
    )
    return results


def collect_superjob_analyst_vacancies(
    *,
    town_id: int = 0,
    max_pages: int | None = None,
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for role_key, query in ANALYST_ROLES.items():
        batch = collect_superjob_vacancies_for_role(
            analyst_role=role_key,
            keyword=query,
            town_id=town_id,
            max_pages=max_pages,
        )
        for row in batch:
            ext_id = row["external_id"]
            if ext_id in seen:
                continue
            seen.add(ext_id)
            results.append(row)

    logger.info("SuperJob total unique analyst vacancies: %s", len(results))
    return results
