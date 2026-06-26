#!/usr/bin/env python3
"""Phase 0: fetch IT analyst vacancies sample (SkillCompass).

Usage (from skillcompass/):
  pip install requests python-dotenv pydantic-settings
  copy .env.example .env
  python scripts/fetch_sample.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGESTOR_SRC = ROOT / "services" / "ingestor" / "src"
sys.path.insert(0, str(INGESTOR_SRC))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from ingestor.collectors.hh import collect_hh_analyst_vacancies  # noqa: E402
from ingestor.roles import ANALYST_ROLE_LABELS  # noqa: E402

OUTPUT = ROOT / "data" / "raw" / "hh_analysts_sample.json"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = collect_hh_analyst_vacancies(max_pages=3)
    by_role: dict[str, int] = {}
    for r in rows:
        role = r.get("analyst_role") or "unknown"
        by_role[role] = by_role.get(role, 0) + 1

    payload = {
        "project": "SkillCompass",
        "count": len(rows),
        "by_role": {
            ANALYST_ROLE_LABELS.get(k, k): v for k, v in sorted(by_role.items())
        },
        "source": "hh.ru",
        "fetch_mode": "html_fallback" if not any(r.get("published_at") for r in rows) else "api",
        "items": [
            {
                **r,
                "published_at": r["published_at"].isoformat() if r["published_at"] else None,
            }
            for r in rows
        ],
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"SkillCompass: saved {len(rows)} analyst vacancies -> {OUTPUT}")
    print("By role:", payload["by_role"])
    if rows:
        s = rows[0]
        print(f"Sample: [{s.get('analyst_role')}] {s['title']}")


if __name__ == "__main__":
    main()
