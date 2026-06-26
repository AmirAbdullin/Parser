"""Ingestor entry point: one-shot or scheduled."""

from __future__ import annotations

import logging
import sys
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from ingestor.config import settings
from ingestor.models import init_db
from ingestor.pipeline import run_ingest, run_skills_backfill

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    session_factory = init_db(settings.database_url)
    run_once = "--once" in sys.argv or settings.ingest_schedule_hours <= 0
    skills_backfill = "--skills-backfill" in sys.argv

    def job() -> None:
        if skills_backfill:
            stats = run_skills_backfill(session_factory)
            logger.info("Skills backfill finished: %s", stats)
            return
        stats = run_ingest(session_factory)
        logger.info("Ingest finished: %s", stats)

    if run_once or skills_backfill:
        job()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", hours=settings.ingest_schedule_hours, id="ingest")
    logger.info("Scheduler started, interval=%sh", settings.ingest_schedule_hours)
    job()
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Ingestor stopped")


if __name__ == "__main__":
    main()
