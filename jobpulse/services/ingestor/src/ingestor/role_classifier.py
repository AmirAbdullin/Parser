"""Classify IT analyst role from vacancy title (RU + EN)."""

from __future__ import annotations

import re

# Reject titles containing these fragments (lowercase match).
NOISE_IN_TITLE = (
    "кредитн",
    "ипотеч",
    "страхов",
    "бухгалтер",
    "экономист",
    "лаборант",
    "laborant",
    "медицин",
    "фарма",
    "брокер",
    "недвижим",
    "риэлтор",
    "риелтор",
    "химик",
    "хим-",
    "эколог",
    "металлург",
    "геолог",
    "финансовый аналитик",
    "financial analyst",
    "credit analyst",
    "investment analyst",
    "marketing analyst",
    "маркетинг",
)

# Order matters: more specific roles first.
_ROLE_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "product_analyst",
        (
            r"продуктов\w*\s+аналитик",
            r"product\s+analyst",
        ),
    ),
    (
        "data_analyst",
        (
            r"аналитик\s+данн",
            r"data\s+analyst",
            r"\bda\b",
        ),
    ),
    (
        "systems_analyst",
        (
            r"системн\w*\s+аналитик",
            r"system\s+analyst",
            r"systems\s+analyst",
            r"it\s+аналитик",
            r"it-аналитик",
        ),
    ),
    (
        "business_analyst",
        (
            r"бизнес[\s-]*аналитик",
            r"business\s+analyst",
            r"\bba\b",
        ),
    ),
)

# Composite titles: pick primary role by priority above.
_ROLE_PRIORITY = ("product_analyst", "data_analyst", "systems_analyst", "business_analyst")


def is_relevant_analyst_title(title: str) -> bool:
    t = (title or "").lower()
    if not t:
        return False
    if any(word in t for word in NOISE_IN_TITLE):
        return False
    return classify_role_from_title(title) is not None


def classify_role_from_title(title: str) -> str | None:
    t = (title or "").lower()
    if not t:
        return None

    matched: list[str] = []
    for role_key, patterns in _ROLE_RULES:
        for pattern in patterns:
            if re.search(pattern, t, flags=re.IGNORECASE):
                matched.append(role_key)
                break

    if not matched:
        # Fallback: generic "аналитик" without noise already filtered
        if "аналитик" in t or "analyst" in t:
            return "business_analyst"
        return None

    for role in _ROLE_PRIORITY:
        if role in matched:
            return role
    return matched[0]


def resolve_vacancy_role(title: str, search_role: str | None = None) -> str | None:
    """Prefer title-based classification; fall back to search role if title is ambiguous."""
    classified = classify_role_from_title(title)
    if classified:
        return classified
    if search_role:
        return search_role
    return None
