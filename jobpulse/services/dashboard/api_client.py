"""SkillCompass dashboard — API client helpers."""

from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=60)
def api_get(path: str) -> dict | list:
    r = requests.get(f"{API_URL}{path}", timeout=30)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict) -> dict:
    timeout = 90 if path == "/predict" else 30
    r = requests.post(f"{API_URL}{path}", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()


def check_api() -> tuple[bool, str]:
    try:
        data = api_get("/health")
        src = data.get("data_source", "")
        return True, f"OK — {data.get('vacancies_loaded', 0)} вакансий ({src})"
    except Exception as exc:
        return False, str(exc)


ROLE_OPTIONS = {
    "Бизнес-аналитик": "business_analyst",
    "Системный аналитик": "systems_analyst",
    "Продуктовый аналитик": "product_analyst",
    "Аналитик данных": "data_analyst",
}

SOURCE_OPTIONS = {
    "Все источники": "all",
    "HH.ru": "hh",
    "SuperJob": "superjob",
}

SALARY_SPEC_OPTIONS = {
    "Все": "all",
    "Диапазон (от и до)": "range",
    "Только «от»": "from_only",
    "Только «до»": "to_only",
}

ALL_CITIES_LABEL = "По всем городам"

EXPERIENCE_OPTIONS = [
    "Нет опыта",
    "Опыт 1-3 года",
    "Опыт 3-6 лет",
    "Опыт более 6 лет",
]


def format_api_datetime(value: str | None) -> str:
    if not value or value == "—":
        return "—"
    try:
        import pandas as pd

        ts = pd.to_datetime(value, utc=True).tz_convert("Europe/Moscow")
        return ts.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(value)
