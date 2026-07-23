"""CLI entrypoint for manual/cron scraping of one property.

Usage: python scripts/run_scrape.py --property surry-hills [--max-pages N]
(run from the backend/ directory, with the venv active)

Uses the same scrape_one_property service the "Refresh reviews" UI button
and the cron orchestrator (run_all_properties.py) call -- one implementation,
not three copies that can drift.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from app.db.session import async_session_maker
from app.scraper.properties import PROPERTIES
from app.services.scrape_service import scrape_one_property

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--property", required=True, help="property slug, e.g. surry-hills")
    parser.add_argument("--max-pages", type=int, default=None)
    args = parser.parse_args()

    prop_def = next((p for p in PROPERTIES if p.slug == args.property), None)
    if prop_def is None:
        available = ", ".join(p.slug for p in PROPERTIES)
        raise SystemExit(f"unknown property '{args.property}'. available: {available}")

    settings = get_settings()
    max_pages = args.max_pages or settings.scrape_max_pages_per_run

    async with async_session_maker() as session:
        result = await scrape_one_property(session, prop_def, max_pages=max_pages, settings=settings)
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
