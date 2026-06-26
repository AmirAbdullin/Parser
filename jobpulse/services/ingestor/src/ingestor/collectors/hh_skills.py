"""Backward-compatible re-export."""

from __future__ import annotations

from typing import Any

from ingestor.collectors.hh_detail import enrich_hh_rows_with_details


def enrich_hh_rows_with_skills(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict]:
    return enrich_hh_rows_with_details(rows, limit=limit)
