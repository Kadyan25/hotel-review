"""Shared scrape orchestration -- used by the CLI script (scripts/run_scrape.py),
the cron orchestrator (scripts/run_all_properties.py), and the gated
POST /api/scrape endpoint, so there's exactly one implementation of
"scrape a property and persist it", not three copies that can drift.
"""

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.db.session import async_session_maker
from app.models import Property, Review, ScrapeRun
from app.scraper.apify_fallback import fetch_reviews_via_apify
from app.scraper.booking_scraper import ScraperBlockedError, scrape_property_reviews
from app.scraper.human import human_delay
from app.scraper.properties import PROPERTIES, PropertyDef

logger = logging.getLogger(__name__)


def _json_safe(parsed: dict) -> dict:
    """SQLAlchemy's JSON column needs plain JSON-serializable values --
    the parser returns real date objects for review_date/stay_date."""
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in parsed.items()}


async def _get_or_create_property(session: AsyncSession, prop_def: PropertyDef) -> Property:
    result = await session.execute(select(Property).where(Property.slug == prop_def.slug))
    prop = result.scalar_one_or_none()
    if prop is None:
        prop = Property(name=prop_def.name, slug=prop_def.slug, booking_url=prop_def.booking_url, city=prop_def.city)
        session.add(prop)
        await session.flush()
        logger.info("created property row: %s (id=%d)", prop.name, prop.id)
    return prop


async def scrape_one_property(
    session: AsyncSession, prop_def: PropertyDef, max_pages: int, settings: Settings | None = None
) -> dict:
    """Scrapes one property and persists results. Returns a small summary
    dict -- never raises for expected failure modes (blocked scraper, no
    Apify configured); those are recorded on the ScrapeRun row instead.
    """
    settings = settings or get_settings()
    cutoff_date: date | None = None
    if not settings.scrape_full_history:
        cutoff_date = date.today() - timedelta(days=settings.scrape_lookback_days)

    prop = await _get_or_create_property(session, prop_def)

    existing_ids_result = await session.execute(select(Review.external_review_id).where(Review.property_id == prop.id))
    known_ids = {row[0] for row in existing_ids_result.all()}
    logger.info("property=%s known_reviews=%d cutoff_date=%s", prop.slug, len(known_ids), cutoff_date)

    run = ScrapeRun(property_id=prop.id, started_at=datetime.now(timezone.utc), status="running", source="patchright")
    session.add(run)
    await session.flush()

    scraped: list[dict] = []
    thumbnail_url: str | None = None

    try:
        result = await scrape_property_reviews(prop_def, max_pages=max_pages, known_external_ids=known_ids, cutoff_date=cutoff_date)
        scraped = result.reviews
        thumbnail_url = result.thumbnail_url
    except ScraperBlockedError as exc:
        logger.warning("primary scraper blocked for %s: %s -- trying Apify fallback", prop.slug, exc)
        if not settings.apify_configured:
            run.status = "failed"
            run.error_message = f"Playwright blocked and Apify not configured: {exc}"
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return {"property": prop.slug, "status": "failed", "reviews_new": 0, "error": run.error_message}

        run.source = "apify"
        try:
            all_apify_reviews = await fetch_reviews_via_apify(
                prop_def.booking_url, max_reviews=settings.max_reviews_per_property_apify, settings=settings, cutoff_date=cutoff_date
            )
            scraped = [r for r in all_apify_reviews if r["external_review_id"] not in known_ids]
        except Exception as apify_exc:
            logger.error("Apify fallback also failed for %s: %s", prop.slug, apify_exc)
            run.status = "failed"
            run.error_message = f"Playwright blocked ({exc}); Apify fallback also failed: {apify_exc}"
            run.finished_at = datetime.now(timezone.utc)
            await session.commit()
            return {"property": prop.slug, "status": "failed", "reviews_new": 0, "error": run.error_message}

    if thumbnail_url and prop.thumbnail_url != thumbnail_url:
        prop.thumbnail_url = thumbnail_url

    new_count = 0
    for parsed in scraped:
        session.add(
            Review(
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
        )
        new_count += 1

    run.status = "success"
    run.reviews_found = len(scraped)
    run.reviews_new = new_count
    run.finished_at = datetime.now(timezone.utc)

    await session.commit()
    logger.info("property=%s reviews_found=%d reviews_new=%d", prop.slug, len(scraped), new_count)

    return {"property": prop.slug, "status": "success", "reviews_new": new_count, "error": None}


async def scrape_single_property_task(prop_def: PropertyDef) -> None:
    """Opens its own session -- for use as a FastAPI BackgroundTask or a
    standalone script entrypoint, decoupled from any request-scoped session.
    Swallows exceptions after logging: a background task has no caller to
    propagate to, and scrape_one_property already records failures on the
    ScrapeRun row, which is what the UI polls.
    """
    settings = get_settings()
    try:
        async with async_session_maker() as session:
            await scrape_one_property(session, prop_def, max_pages=settings.scrape_max_pages_per_run, settings=settings)
    except Exception:
        logger.exception("background scrape task crashed for %s", prop_def.slug)


async def scrape_all_properties_task() -> None:
    """Loops all properties with human-paced spacing between them -- not
    just within one property's pagination. Used by the cron orchestrator
    and the "scrape all" API trigger.
    """
    settings = get_settings()
    for index, prop_def in enumerate(PROPERTIES):
        if index > 0:
            await human_delay(30.0, 90.0)
        try:
            async with async_session_maker() as session:
                await scrape_one_property(session, prop_def, max_pages=settings.scrape_max_pages_per_run, settings=settings)
        except Exception:
            logger.exception("scrape_all: property %s failed, continuing with the rest", prop_def.slug)
