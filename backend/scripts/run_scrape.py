"""CLI entrypoint for manual/cron scraping.

Usage: python scripts/run_scrape.py --property surry-hills [--max-pages N]
(run from the backend/ directory, with the venv active)

Deliberately not exposed as a live-trigger API endpoint on the deployed app
-- see architecture.md "Where the scraper is allowed to run". Run this
locally, from a residential connection.
"""

import argparse
import asyncio
import logging
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.config import get_settings
from app.db.session import async_session_maker
from app.models import Property, Review, ScrapeRun
from app.scraper.apify_fallback import fetch_reviews_via_apify
from app.scraper.booking_scraper import ScraperBlockedError, scrape_property_reviews
from app.scraper.properties import PROPERTIES

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("run_scrape")


def _json_safe(parsed: dict) -> dict:
    """SQLAlchemy's JSON column needs plain JSON-serializable values --
    the parser returns real date objects for review_date/stay_date."""
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in parsed.items()}


async def _get_or_create_property(session, prop_def) -> Property:
    result = await session.execute(select(Property).where(Property.slug == prop_def.slug))
    prop = result.scalar_one_or_none()
    if prop is None:
        prop = Property(
            name=prop_def.name,
            slug=prop_def.slug,
            booking_url=prop_def.booking_url,
            city=prop_def.city,
        )
        session.add(prop)
        await session.flush()
        logger.info("created property row: %s (id=%d)", prop.name, prop.id)
    return prop


async def run_for_property(prop_def, max_pages: int) -> None:
    settings = get_settings()
    cutoff_date: date | None = None
    if not settings.scrape_full_history:
        cutoff_date = date.today() - timedelta(days=settings.scrape_lookback_days)

    async with async_session_maker() as session:
        prop = await _get_or_create_property(session, prop_def)

        existing_ids_result = await session.execute(
            select(Review.external_review_id).where(Review.property_id == prop.id)
        )
        known_ids = {row[0] for row in existing_ids_result.all()}
        logger.info("property=%s known_reviews=%d cutoff_date=%s", prop.slug, len(known_ids), cutoff_date)

        run = ScrapeRun(
            property_id=prop.id,
            started_at=datetime.now(timezone.utc),
            status="running",
            source="patchright",
        )
        session.add(run)
        await session.flush()

        try:
            scraped = await scrape_property_reviews(
                prop_def, max_pages=max_pages, known_external_ids=known_ids, cutoff_date=cutoff_date
            )
        except ScraperBlockedError as exc:
            logger.warning("primary scraper blocked for %s: %s -- trying Apify fallback", prop.slug, exc)
            if not settings.apify_configured:
                logger.error("no APIFY_API_TOKEN configured, cannot fall back. marking run failed.")
                run.status = "failed"
                run.error_message = f"Playwright blocked and Apify not configured: {exc}"
                run.finished_at = datetime.now(timezone.utc)
                await session.commit()
                return

            run.source = "apify"
            try:
                all_apify_reviews = await fetch_reviews_via_apify(
                    prop_def.booking_url,
                    max_reviews=settings.max_reviews_per_property_apify,
                    settings=settings,
                    cutoff_date=cutoff_date,
                )
                scraped = [r for r in all_apify_reviews if r["external_review_id"] not in known_ids]
            except Exception as apify_exc:
                logger.error("Apify fallback also failed for %s: %s", prop.slug, apify_exc)
                run.status = "failed"
                run.error_message = f"Playwright blocked ({exc}); Apify fallback also failed: {apify_exc}"
                run.finished_at = datetime.now(timezone.utc)
                await session.commit()
                return

        new_count = 0
        for parsed in scraped:
            review = Review(
                property_id=prop.id,
                external_review_id=parsed["external_review_id"],
                reviewer_name=parsed["reviewer_name"],
                reviewer_country=parsed["reviewer_country"],
                rating=parsed["rating"],
                review_date=parsed["review_date"],
                stay_date=parsed["stay_date"],
                room_type=parsed["room_type"],
                length_of_stay=parsed["length_of_stay"],
                positive_text=parsed["positive_text"],
                negative_text=parsed["negative_text"],
                full_text=parsed["full_text"],
                raw_json=_json_safe(parsed),
            )
            session.add(review)
            new_count += 1

        run.status = "success"
        run.reviews_found = len(scraped)
        run.reviews_new = new_count
        run.finished_at = datetime.now(timezone.utc)

        await session.commit()
        logger.info("property=%s reviews_found=%d reviews_new=%d", prop.slug, len(scraped), new_count)


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
    await run_for_property(prop_def, max_pages=max_pages)


if __name__ == "__main__":
    asyncio.run(main())
