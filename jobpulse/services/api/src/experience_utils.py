"""Map UI / HH experience labels to equivalent DB values."""

from __future__ import annotations

EXPERIENCE_OPTIONS: list[str] = [
    "Нет опыта",
    "Опыт 1-3 года",
    "Опыт 3-6 лет",
    "Опыт более 6 лет",
]

EXPERIENCE_GROUPS: dict[str, set[str]] = {
    "Нет опыта": {
        "Нет опыта",
        "Без опыта",
        "noExperience",
        "Не требуется",
        "Нет опыта работы",
    },
    "Опыт 1-3 года": {
        "Опыт 1-3 года",
        "От 1 года до 3 лет",
        "between1And3",
        "1–3 года",
        "1-3 года",
        "Опыт 1–3 года",
    },
    "Опыт 3-6 лет": {
        "Опыт 3-6 лет",
        "От 3 до 6 лет",
        "between3And6",
        "3–6 лет",
        "3-6 лет",
        "Опыт 3–6 лет",
    },
    "Опыт более 6 лет": {
        "Опыт более 6 лет",
        "Более 6 лет",
        "От 6 лет",
        "moreThan6",
        "6+ лет",
    },
}


def normalize_experience(raw: str | None) -> str | None:
    if not raw or not str(raw).strip():
        return None
    value = str(raw).strip()
    for canonical, variants in EXPERIENCE_GROUPS.items():
        if value in variants:
            return canonical
    return value


def experience_variants(label: str | None) -> set[str] | None:
    if not label or label == "Все":
        return None
    for canonical, variants in EXPERIENCE_GROUPS.items():
        if label == canonical or label in variants:
            return set(variants) | {canonical}
    return {label}
