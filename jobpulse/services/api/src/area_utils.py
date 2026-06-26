"""Normalize HH area strings to city names for filters and ML."""

from __future__ import annotations

import re

_STREET_MARKERS = (
    "улица",
    "ул.",
    "проспект",
    "пр-т",
    "бульвар",
    "переулок",
    "пер.",
    "шоссе",
    "проезд",
    "набережная",
    "площадь",
    "пл.",
    "микрорайон",
    "мкр.",
    "район",
    "махаллинский",
)

_DISTRICT_RE = re.compile(r"\s+р-н\s+.+$", re.IGNORECASE)


def normalize_city_name(area: str | None) -> str:
    if not area or not str(area).strip():
        return ""
    part = str(area).split(",")[0].strip()
    part = _DISTRICT_RE.sub("", part).strip()
    lower = part.lower()
    if any(marker in lower for marker in _STREET_MARKERS):
        return ""
    if re.search(r"\d", part):
        return ""
    return part
