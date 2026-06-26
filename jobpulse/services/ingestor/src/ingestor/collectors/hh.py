"""HH.ru vacancies: API first, HTML search fallback on 403."""

from __future__ import annotations

import logging
from typing import Any

import requests

from ingestor.collectors import hh_api, hh_html
from ingestor.config import settings
from ingestor.roles import ANALYST_ROLES

logger = logging.getLogger(__name__)

_use_api: bool | None = None


def _api_available() -> bool:
    global _use_api
    if _use_api is not None:
        return _use_api
    try:
        hh_api.collect_hh_vacancies_for_role(
            analyst_role="business_analyst",
            text="бизнес-аналитик",
            max_pages=1,
        )
        _use_api = True
    except requests.HTTPError as exc:
        if exc.response is not None and exc.response.status_code == 403:
            logger.warning("HH API blocked (403) — using HTML search fallback")
            _use_api = False
        else:
            raise
    return _use_api


def collect_hh_analyst_vacancies(
    *,
    area_id: int | None = None,
    max_pages: int | None = None,
    only_with_salary: bool = False,
    fetch_descriptions: bool = False,
) -> list[dict[str, Any]]:
    if _api_available():
        return hh_api.collect_hh_analyst_vacancies(
            area_id=area_id,
            max_pages=max_pages,
            only_with_salary=only_with_salary,
            fetch_descriptions=fetch_descriptions,
        )

    return hh_html.collect_hh_html_analyst_vacancies(
        area_id=area_id,
        max_pages=max_pages,
        only_with_salary=only_with_salary,
    )
