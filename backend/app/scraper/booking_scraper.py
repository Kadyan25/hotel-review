"""Playwright/Patchright-based Booking.com review scraper.

Runs headed (not headless=new) and paced by app.scraper.human -- see
architecture.md "Human-mimicking behavior" for why. This is meant to be run
locally (residential IP), not triggered from a cloud-hosted API -- see
architecture.md "Where the scraper is allowed to run".
"""

import logging
from dataclasses import dataclass
from datetime import date

from patchright.async_api import async_playwright

from app.config import get_settings
from app.scraper.dedupe import compute_external_review_id
from app.scraper.human import (
    PAGE_LOAD_DELAY,
    PAGINATION_CLICK_DELAY,
    human_delay,
    human_move_and_click,
    maybe_reading_pause,
)
from app.scraper.parser import parse_review_card
from app.scraper.properties import PropertyDef

logger = logging.getLogger(__name__)

REVIEWS_TAB_SELECTOR = '[data-testid="Property-Header-Nav-Tab-Trigger-reviews"]'
REVIEW_CARD_SELECTOR = '[data-testid="review-card"]'
SORT_SELECT_SELECTOR = '[data-testid="review-sorter"] select'
NEXT_PAGE_SELECTOR = 'button[aria-label="Next page"]'

NAVIGATION_RETRIES = 3


class ScraperBlockedError(Exception):
    """Raised when Booking.com appears to have blocked/CAPTCHA'd the session."""


@dataclass
class ScrapeResult:
    reviews: list[dict]
    thumbnail_url: str | None


async def _extract_thumbnail(page) -> str | None:
    """Grabs the first real gallery photo URL while we're already on the
    property page -- no extra navigation/request. Hotlinked directly (not
    downloaded/rehosted), so it depends on Booking's CDN token in the URL
    staying valid; frontend falls back to an icon if the image 404s.
    """
    try:
        img = page.locator('img[src*="bstatic.com"][src*="/hotel/"]').first
        if await img.count() == 0:
            return None
        return await img.get_attribute("src")
    except Exception:
        return None


async def _goto_with_retry(page, url: str) -> None:
    last_error: Exception | None = None
    for attempt in range(NAVIGATION_RETRIES):
        try:
            # referer= applies only to this one navigation request (real
            # browser semantics) -- unlike a blanket extra_http_headers
            # override, it doesn't leak onto subsequent same-page XHR/GraphQL
            # calls, which would look inconsistent (arrived via Google, but
            # every API call also claims Google as its referer).
            await page.goto(url, wait_until="domcontentloaded", timeout=30000, referer="https://www.google.com/")
            return
        except Exception as exc:  # navigation/timeout errors
            last_error = exc
            logger.warning("navigation attempt %d/%d failed: %s", attempt + 1, NAVIGATION_RETRIES, exc)
            await human_delay(5.0, 10.0)
    raise ScraperBlockedError(f"could not load {url} after {NAVIGATION_RETRIES} attempts") from last_error


async def scrape_property_reviews(
    property_def: PropertyDef,
    max_pages: int,
    known_external_ids: set[str] | None = None,
    cutoff_date: date | None = None,
) -> ScrapeResult:
    """Scrapes newest-first reviews for one property, plus its thumbnail.

    Stops on whichever of these comes first:
      - a full page is entirely already-seen (known_external_ids) -- the
        incremental-update mechanism for repeat runs;
      - a review older than cutoff_date is reached -- deliberately scoped to
        a recent window (e.g. last 30 days) while building/demoing, so we
        don't hammer Booking.com with 220 pages per property or burn LLM
        tokens classifying years of history before this even ships. Full
        historical backfill is a separate, deliberate later run with
        cutoff_date=None;
      - max_pages, as a hard ceiling regardless of the above.
    """
    known_external_ids = known_external_ids or set()
    reviews: list[dict] = []
    settings = get_settings()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=settings.scrape_headless)
        context = await browser.new_context(
            locale="en-AU",
            timezone_id="Australia/Sydney",
            # Headless Chromium self-identifies as "HeadlessChrome" in the
            # User-Agent header -- confirmed by live testing that Booking.com's
            # reviews API rejects that specific string with a 400 "Request not
            # supported" (a simple check, not sophisticated fingerprinting).
            # Patchright's CDP-level patches don't cover this header, so it
            # needs an explicit override.
            # Version matched to the bundled Chromium build (chromium-1228 ==
            # 149.x at time of writing) -- a mismatched declared-vs-actual
            # version is its own inconsistency signal, so this should track
            # whatever Chromium version Patchright ships, not be arbitrary.
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/149.0.7827.55 Safari/537.36"
            ),
        )
        page = await context.new_page()

        thumbnail_url: str | None = None

        try:
            await _goto_with_retry(page, property_def.booking_url)
            await human_delay(*PAGE_LOAD_DELAY)
            thumbnail_url = await _extract_thumbnail(page)

            reviews_tab = page.locator(REVIEWS_TAB_SELECTOR)
            if await reviews_tab.count() == 0:
                raise ScraperBlockedError("reviews tab not found -- page structure changed or we were blocked")

            await human_move_and_click(page, reviews_tab)
            await page.wait_for_selector(REVIEW_CARD_SELECTOR, timeout=15000)
            await human_delay(1.0, 2.5)

            sorter = page.locator(SORT_SELECT_SELECTOR)
            if await sorter.count() > 0:
                await sorter.select_option("NEWEST_FIRST")
                await page.wait_for_timeout(1500)
                await human_delay(1.0, 2.0)

            for page_index in range(max_pages):
                cards = page.locator(REVIEW_CARD_SELECTOR)
                count = await cards.count()

                page_had_new_review = False
                hit_cutoff = False
                for i in range(count):
                    parsed = await parse_review_card(cards.nth(i))

                    if cutoff_date is not None and parsed["review_date"] is not None:
                        if parsed["review_date"] < cutoff_date:
                            hit_cutoff = True
                            break  # newest-first: everything after this is older still

                    external_id = compute_external_review_id(
                        parsed["reviewer_name"],
                        parsed["review_date_iso"],
                        parsed["positive_text"],
                        parsed["negative_text"],
                    )
                    if external_id in known_external_ids:
                        continue
                    page_had_new_review = True
                    parsed["external_review_id"] = external_id
                    reviews.append(parsed)

                if hit_cutoff:
                    logger.info("page %d reached cutoff_date=%s, stopping (recent-window scrape)", page_index, cutoff_date)
                    break

                if known_external_ids and count > 0 and not page_had_new_review:
                    logger.info("page %d entirely already-seen, stopping (incremental update)", page_index)
                    break

                next_button = page.locator(NEXT_PAGE_SELECTOR)
                if await next_button.count() == 0:
                    break
                if await next_button.get_attribute("disabled") is not None:
                    break

                await human_delay(*PAGINATION_CLICK_DELAY)
                await human_move_and_click(page, next_button)
                await page.wait_for_timeout(500)
                await page.wait_for_selector(REVIEW_CARD_SELECTOR, timeout=15000)
                await maybe_reading_pause(page_index + 1)

        finally:
            await context.close()
            await browser.close()

    return ScrapeResult(reviews=reviews, thumbnail_url=thumbnail_url)
