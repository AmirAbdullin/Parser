"""Salary normalization and outlier handling."""

from __future__ import annotations

SALARY_MIN_RUB = 30_000
SALARY_MAX_RUB = 600_000


def _to_float(value) -> float | None:
    if value is None:
        return None
    try:
        v = float(value)
        return v if v > 0 else None
    except (TypeError, ValueError):
        return None


def sanitize_salary_row(row: dict) -> dict:
    """Cap RUR salaries and compute salary_mid for analytics."""
    out = dict(row)
    currency = (out.get("salary_currency") or "RUR").upper()
    sf = _to_float(out.get("salary_from"))
    st = _to_float(out.get("salary_to"))

    if currency in ("RUR", "RUB"):
        if sf is not None and (sf < SALARY_MIN_RUB or sf > SALARY_MAX_RUB):
            sf = None
            out["salary_outlier"] = True
        if st is not None and (st < SALARY_MIN_RUB or st > SALARY_MAX_RUB):
            st = None
            out["salary_outlier"] = True

    out["salary_from"] = sf
    out["salary_to"] = st
    if sf is not None and st is not None:
        out["salary_mid"] = (sf + st) / 2
    elif sf is not None:
        out["salary_mid"] = sf
    elif st is not None:
        out["salary_mid"] = st
    else:
        out["salary_mid"] = None
    return out
