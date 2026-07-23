"""Orchestrator for scraping all 4 properties in one run -- this is what
the daily scheduled task (see README "Keeping data fresh") actually calls.

Loops with human-paced spacing between properties (not just within one
property's pagination) and keeps going if one property fails, so a bad
run on property 2 doesn't lose properties 1, 3, 4.

Usage: python scripts/run_all_properties.py
(run from the backend/ directory, with the venv active)
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scrape_service import scrape_all_properties_task

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

if __name__ == "__main__":
    asyncio.run(scrape_all_properties_task())
