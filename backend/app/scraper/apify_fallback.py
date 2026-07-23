import httpx

from app.config import Settings

ACTOR_ID = "reviewly~booking-reviews-scraper"
APIFY_RUN_SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
COST_PER_REVIEW_USD = 0.001


async def fetch_reviews_via_apify(property_url: str, max_reviews: int, settings: Settings) -> list[dict]:
    """Fallback review fetch when the Playwright scraper gets blocked.

    Only called after the primary scraper has demonstrably failed for a
    property (see scraper/booking_scraper.py + scrape_runs logging).
    Actor input schema is documented at apify.com/reviewly/booking-reviews-scraper
    and should be re-checked against the live actor before first real use —
    Apify actor input fields can change between actor versions.
    """
    if not settings.apify_configured:
        return []

    capped = min(max_reviews, settings.max_reviews_per_property_apify)
    estimated_cost = capped * COST_PER_REVIEW_USD
    print(f"[apify_fallback] requesting up to {capped} reviews for {property_url} (~${estimated_cost:.3f})")

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            APIFY_RUN_SYNC_URL,
            params={"token": settings.apify_api_token},
            json={"startUrls": [{"url": property_url}], "maxReviews": capped},
        )
        response.raise_for_status()
        return response.json()
