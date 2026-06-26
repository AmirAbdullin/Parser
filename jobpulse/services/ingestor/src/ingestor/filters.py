"""Filter HH noise outside IT analyst niches."""

from __future__ import annotations

from ingestor.role_classifier import is_relevant_analyst_title


def is_relevant_analyst_vacancy(title: str) -> bool:
    return is_relevant_analyst_title(title)
