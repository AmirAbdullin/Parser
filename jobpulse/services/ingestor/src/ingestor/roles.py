"""IT analyst vacancy niches for SkillCompass."""

from __future__ import annotations

# role_key -> primary RU label
ANALYST_ROLES: dict[str, str] = {
    "business_analyst": "бизнес-аналитик",
    "systems_analyst": "системный аналитик",
    "product_analyst": "продуктовый аналитик",
    "data_analyst": "аналитик данных",
}

ANALYST_ROLE_LABELS: dict[str, str] = {
    "business_analyst": "Бизнес-аналитик",
    "systems_analyst": "Системный аналитик",
    "product_analyst": "Продуктовый аналитик",
    "data_analyst": "Аналитик данных",
}

# HH text search: RU + EN per role (OR inside query).
ANALYST_SEARCH_QUERIES: dict[str, list[str]] = {
    "business_analyst": ['"бизнес-аналитик"', '"business analyst"'],
    "systems_analyst": ['"системный аналитик"', '"system analyst"'],
    "product_analyst": ['"продуктовый аналитик"', '"product analyst"'],
    "data_analyst": ['"аналитик данных"', '"data analyst"'],
}


def hh_text_query(role_key: str) -> str:
    parts = ANALYST_SEARCH_QUERIES.get(role_key, [ANALYST_ROLES[role_key]])
    return " OR ".join(parts)
