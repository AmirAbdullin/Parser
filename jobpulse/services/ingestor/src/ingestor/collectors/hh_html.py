"""HH.ru vacancy search via public HTML (fallback when API returns 403)."""

from __future__ import annotations

import logging
import re
import time
from typing import Any

import requests
from bs4 import BeautifulSoup

from ingestor.config import settings
from ingestor.roles import ANALYST_ROLES, ANALYST_SEARCH_QUERIES

logger = logging.getLogger(__name__)

SEARCH_URL = "https://hh.ru/search/vacancy"
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Accept": "text/html,application/xhtml+xml",
}

_SALARY_RE = re.compile(
    r"(?:от\s*)?([\d\s\u202f\u00a0]+)\s*(?:[-–—]\s*([\d\s\u202f\u00a0]+)|(?:до\s*([\d\s\u202f\u00a0]+)))?\s*₽",
    re.IGNORECASE,
)
_VACANCY_ID_RE = re.compile(r"/vacancy/(\d+)")


def _parse_salary_text(text: str) -> tuple[float | None, float | None, bool | None]:
    if not text or "₽" not in text:
        return None, None, None
    match = _SALARY_RE.search(text.replace("\u202f", " ").replace("\u00a0", " "))
    if not match:
        return None, None, None

    def _num(raw: str | None) -> float | None:
        if not raw:
            return None
        digits = re.sub(r"\s+", "", raw.strip())
        return float(digits) if digits.isdigit() else None

    salary_from = _num(match.group(1))
    salary_to = _num(match.group(2) or match.group(3))
    gross = "до вычета" in text.lower() or "на руки" not in text.lower()
    if "на руки" in text.lower():
        gross = False
    return salary_from, salary_to, gross


def _parse_card(card: BeautifulSoup, *, analyst_role: str) -> dict[str, Any] | None:
    title_el = card.select_one('[data-qa="serp-item__title-text"]')
    link_el = card.select_one('[data-qa="serp-item__title"]')
    if not title_el or not link_el:
        return None

    href = link_el.get("href") or ""
    ext_match = _VACANCY_ID_RE.search(href)
    if not ext_match:
        card_id = card.select_one("[id]")
        ext_id = card_id.get("id") if card_id else None
    else:
        ext_id = ext_match.group(1)
    if not ext_id:
        return None

    employer_el = card.select_one('[data-qa="vacancy-serp__vacancy-employer-text"]')
    area_el = card.select_one('[data-qa="vacancy-serp__vacancy-address"]')
    exp_el = card.select_one('[data-qa^="vacancy-serp__vacancy-work-experience"]')

    salary_el = card.select_one(
        'span[class*="typography-label-1-regular"], span[class*="compensation"]'
    )
    salary_text = ""
    for span in card.select("span"):
        t = span.get_text(" ", strip=True)
        if "₽" in t:
            salary_text = t
            break
    if not salary_text and salary_el:
        salary_text = salary_el.get_text(" ", strip=True)

    salary_from, salary_to, salary_gross = _parse_salary_text(salary_text)

    return {
        "source": "hh",
        "external_id": str(ext_id),
        "title": title_el.get_text(strip=True),
        "analyst_role": analyst_role,
        "employer": employer_el.get_text(strip=True) if employer_el else None,
        "area": area_el.get_text(strip=True) if area_el else None,
        "experience": exp_el.get_text(strip=True) if exp_el else None,
        "employment": None,
        "schedule": None,
        "salary_from": salary_from,
        "salary_to": salary_to,
        "salary_currency": "RUR" if salary_from or salary_to else None,
        "salary_gross": salary_gross,
        "description": None,
        "url": href.split("?")[0] if href.startswith("http") else f"https://hh.ru/vacancy/{ext_id}",
        "published_at": None,
    }


def collect_hh_html_for_role(
    *,
    analyst_role: str,
    text: str,
    area_id: int | None = None,
    max_pages: int | None = None,
    only_with_salary: bool = False,
) -> list[dict[str, Any]]:
    if max_pages is None:
        max_pages = settings.ingest_max_pages
    results: list[dict[str, Any]] = []

    page = 0
    while True:
        if max_pages > 0 and page >= max_pages:
            break

        params: dict[str, Any] = {"text": text, "page": page}
        if area_id:
            params["area"] = area_id
        if only_with_salary:
            params["only_with_salary"] = "true"

        resp = requests.get(
            SEARCH_URL,
            params=params,
            headers=BROWSER_HEADERS,
            timeout=45,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select('[data-qa="vacancy-serp__vacancy"]')
        if not cards:
            break

        for card in cards:
            row = _parse_card(card, analyst_role=analyst_role)
            if row:
                if only_with_salary and not (row.get("salary_from") or row.get("salary_to")):
                    continue
                results.append(row)

        page += 1
        time.sleep(1.0)

    tag = " salary" if only_with_salary else ""
    logger.info("HH HTML%s role=%s query=%r collected %s vacancies", tag, analyst_role, text, len(results))
    return results


def collect_hh_html_analyst_vacancies(
    *,
    area_id: int | None = None,
    max_pages: int | None = None,
    only_with_salary: bool = False,
) -> list[dict[str, Any]]:
    area_id = area_id if area_id is not None else settings.ingest_area_id
    seen: set[str] = set()
    results: list[dict[str, Any]] = []

    for role_key in ANALYST_ROLES:
        queries = ANALYST_SEARCH_QUERIES.get(role_key, [ANALYST_ROLES[role_key]])
        for query in queries:
            text = query.strip('"')
            batch = collect_hh_html_for_role(
                analyst_role=role_key,
                text=text,
                area_id=area_id,
                max_pages=max_pages,
                only_with_salary=only_with_salary,
            )
            for row in batch:
                if row["external_id"] in seen:
                    continue
                seen.add(row["external_id"])
                results.append(row)
            time.sleep(0.5)

    tag = " salary-only" if only_with_salary else ""
    logger.info("HH HTML%s total unique analyst vacancies: %s", tag, len(results))
    return results
