"""Fetch salary + key_skills from HH vacancy detail (API + HTML fallback)."""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import datetime
from typing import Any

import requests

from ingestor.collectors.hh_html import BROWSER_HEADERS, _parse_salary_text
from ingestor.config import settings
from ingestor.salary_utils import sanitize_salary_row

logger = logging.getLogger(__name__)

DETAIL_URL = "https://api.hh.ru/vacancies/{vacancy_id}"
VACANCY_HTML_URL = "https://hh.ru/vacancy/{vacancy_id}"

_KEY_SKILL_RE = re.compile(r'"keySkill"\s*:\s*(\[[^\]]+\])')
_WORK_EXP_RE = re.compile(r'"workExperience"\s*:\s*"([^"]+)"')
_SALARY_VISIBLE_RE = re.compile(r'data-qa="vacancy-salary"[^>]*>([^<]+)<')
_SALARY_JSON_RE = re.compile(r'"from"\s*:\s*(\d+)\s*,\s*"to"\s*:\s*(?:(\d+)|null)')

_api_blocked_logged = False


def _api_headers() -> dict[str, str]:
    return {"HH-User-Agent": settings.hh_user_agent}


def _needs_detail(row: dict) -> bool:
    if row.get("source") != "hh":
        return False
    has_salary = row.get("salary_from") is not None or row.get("salary_to") is not None
    has_skills = bool(row.get("key_skills"))
    return not has_salary or not has_skills


def _parse_detail_from_html(html: str) -> dict[str, Any]:
    out: dict[str, Any] = {}

    skill_match = _KEY_SKILL_RE.search(html)
    if skill_match:
        try:
            names = json.loads(skill_match.group(1))
            if names:
                out["key_skills"] = json.dumps(names, ensure_ascii=False)
        except json.JSONDecodeError:
            logger.debug("HH detail HTML: keySkill JSON parse failed")

    exp_match = _WORK_EXP_RE.search(html)
    if exp_match:
        out["experience"] = exp_match.group(1)

    salary_match = _SALARY_JSON_RE.search(html)
    if salary_match:
        out["salary_from"] = float(salary_match.group(1))
        if salary_match.group(2):
            out["salary_to"] = float(salary_match.group(2))
        out["salary_currency"] = "RUR"
    else:
        visible = _SALARY_VISIBLE_RE.search(html)
        if visible:
            salary_from, salary_to, salary_gross = _parse_salary_text(visible.group(1))
            if salary_from is not None or salary_to is not None:
                out["salary_from"] = salary_from
                out["salary_to"] = salary_to
                out["salary_currency"] = "RUR"
                out["salary_gross"] = salary_gross

    return out


def _parse_detail_from_api(data: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    raw_salary = data.get("salary")
    if raw_salary:
        out["salary_from"] = raw_salary.get("from")
        out["salary_to"] = raw_salary.get("to")
        out["salary_currency"] = raw_salary.get("currency")
        out["salary_gross"] = raw_salary.get("gross")

    skills = data.get("key_skills") or []
    names = [s.get("name", "") for s in skills if s.get("name")]
    if names:
        out["key_skills"] = json.dumps(names, ensure_ascii=False)

    exp = (data.get("experience") or {}).get("name")
    if exp:
        out["experience"] = exp
    area = (data.get("area") or {}).get("name")
    if area:
        out["area"] = area
    employment = (data.get("employment") or {}).get("name")
    if employment:
        out["employment"] = employment

    published = data.get("published_at")
    if published:
        out["published_at"] = datetime.fromisoformat(published.replace("Z", "+00:00"))

    return out


def fetch_hh_vacancy_detail(external_id: str, *, retry: bool = True) -> dict[str, Any]:
    global _api_blocked_logged

    try:
        resp = requests.get(
            DETAIL_URL.format(vacancy_id=external_id),
            headers=_api_headers(),
            timeout=25,
        )
        if resp.status_code == 200:
            return _parse_detail_from_api(resp.json())
        if resp.status_code == 403 and not _api_blocked_logged:
            logger.warning("HH detail API blocked (403) — using HTML vacancy page fallback")
            _api_blocked_logged = True
    except Exception as exc:
        logger.debug("HH detail API failed id=%s: %s", external_id, exc)

    attempts = 2 if retry else 1
    for attempt in range(attempts):
        try:
            resp = requests.get(
                VACANCY_HTML_URL.format(vacancy_id=external_id),
                headers=BROWSER_HEADERS,
                timeout=25,
            )
            if resp.status_code != 200:
                continue
            detail = _parse_detail_from_html(resp.text)
            if detail.get("key_skills") or attempt == attempts - 1:
                return detail
            time.sleep(1.5)
        except Exception as exc:
            logger.debug("HH detail HTML failed id=%s: %s", external_id, exc)
    return {}


def _apply_detail(row: dict, detail: dict[str, Any]) -> tuple[dict, bool, bool]:
    had_salary = row.get("salary_from") is not None or row.get("salary_to") is not None
    had_skills = bool(row.get("key_skills"))

    for key, val in detail.items():
        if val is None:
            continue
        if key == "key_skills" and row.get("key_skills"):
            continue
        if key.startswith("salary_") and had_salary:
            continue
        if key == "experience" and row.get("experience"):
            continue
        row[key] = val

    salary_added = not had_salary and (
        row.get("salary_from") is not None or row.get("salary_to") is not None
    )
    skills_added = not had_skills and bool(row.get("key_skills"))
    return sanitize_salary_row(row), salary_added, skills_added


def enrich_hh_rows_with_details(
    rows: list[dict[str, Any]],
    *,
    limit: int | None = None,
    skills_only: bool = False,
) -> list[dict]:
    if not settings.ingest_detail_enrich:
        return rows

    cap = settings.ingest_detail_limit if limit is None else limit
    sleep_sec = settings.ingest_detail_sleep_sec
    out: list[dict] = []
    fetched = 0
    salary_added = 0
    skills_added = 0
    total_need = sum(
        1
        for r in rows
        if r.get("source") == "hh"
        and (not r.get("key_skills") if skills_only else _needs_detail(r))
    )

    for row in rows:
        row = dict(row)
        needs = (
            row.get("source") == "hh" and not row.get("key_skills")
            if skills_only
            else _needs_detail(row)
        )
        if not needs:
            out.append(row)
            continue
        if cap > 0 and fetched >= cap:
            out.append(row)
            continue

        detail = fetch_hh_vacancy_detail(str(row["external_id"]))
        fetched += 1
        row, got_salary, got_skills = _apply_detail(row, detail)
        salary_added += int(got_salary)
        skills_added += int(got_skills)
        out.append(row)

        if fetched % 200 == 0:
            logger.info(
                "HH detail progress: %s/%s fetched, +%s skills so far",
                fetched,
                total_need,
                skills_added,
            )
        time.sleep(sleep_sec)

    logger.info(
        "HH detail enrich: %s requests, +%s salaries, +%s skills",
        fetched,
        salary_added,
        skills_added,
    )
    return out
