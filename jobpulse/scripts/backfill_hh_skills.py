"""Backfill HH key_skills via HTML (run on host, not in Docker)."""
from __future__ import annotations

import logging
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "services", "ingestor", "src"))

from ingestor.config import settings
from ingestor.models import init_db
from ingestor.pipeline import run_skills_backfill

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

if __name__ == "__main__":
    db_url = os.getenv("DATABASE_URL", settings.database_url).replace("@db:", "@localhost:")
    session_factory = init_db(db_url)
    stats = run_skills_backfill(session_factory)
    print("Done:", stats)
