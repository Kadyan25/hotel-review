from datetime import date, datetime

import httpx

from app.config import Settings

ACTOR_ID = "reviewly~booking-reviews-scraper"
APIFY_RUN_SYNC_URL = f"https://api.apify.com/v2/acts/{ACTOR_ID}/run-sync-get-dataset-items"
COST_PER_REVIEW_USD = 0.001


def _map_apify_review(raw: dict) -> dict:
    """Normalizes one Apify review object onto the same dict shape
    app.scraper.parser.parse_review_card() produces, so run_scrape.py's
    ingestion code doesn't need to know which source produced a row.

    Confirmed by live testing (2026-07-23) that this actor's schema is
    LOWER FIDELITY than our own DOM scrape -- it has no reviewer country and
    no length-of-stay, unlike the Playwright path. Those fields are always
    None for Apify-sourced rows; the nullable schema already tolerates that.
    It does provide a genuine reviewId, which our own DOM scrape doesn't
    expose at all -- used directly as external_review_id instead of the
    hash-based fallback.
    """
    text = raw.get("text") or {}
    positive_text = text.get("positive") or None
    negative_text = text.get("negative") or None

    review_dt = raw.get("datetime")
    review_date = datetime.fromisoformat(review_dt.replace("Z", "+00:00")).date() if review_dt else None

    stay_dt = raw.get("dateOfExperience")
    stay_date = datetime.fromisoformat(stay_dt.replace("Z", "+00:00")).date() if stay_dt else None

    return {
        "reviewer_name": raw.get("consumerName"),
        "reviewer_country": None,  # not exposed by this actor
        "rating": float(raw["rating"]) if raw.get("rating") is not None else None,
        "review_date": review_date,
        "review_date_iso": review_date.isoformat() if review_date else None,
        "stay_date": stay_date,
        "room_type": raw.get("room_name"),
        "length_of_stay": None,  # not exposed by this actor
        "positive_text": positive_text,
        "negative_text": negative_text,
        "full_text": "\n".join(t for t in (positive_text, negative_text) if t) or None,
        "title": raw.get("title"),
        "traveler_type": None,  # not exposed by this actor
        "external_review_id": raw["reviewId"],
        "source": "apify",
    }


async def fetch_reviews_via_apify(
    property_url: str,
    max_reviews: int,
    settings: Settings,
    cutoff_date: date | None = None,
) -> list[dict]:
    """Fallback review fetch when the Playwright scraper gets blocked.

    Only called after the primary scraper has demonstrably failed for a
    property (see scraper/booking_scraper.py + scrape_runs logging).

    Input schema confirmed against the actor's live docs
    (apify.com/reviewly/booking-reviews-scraper/input-schema):
      - startUrls: [{url}] -- required
      - maxNumberOfReviews: int, 0 = no limit -- NOT "maxReviews", that was
        wrong in an earlier draft of this function
      - targetDate: ISO date string, "stop collecting reviews older than
        this" -- maps directly onto our recent-window cutoff_date, same
        reasoning as SCRAPE_LOOKBACK_DAYS for the Playwright path
    """
    if not settings.apify_configured:
        return []

    capped = min(max_reviews, settings.max_reviews_per_property_apify)
    estimated_cost = capped * COST_PER_REVIEW_USD
    print(f"[apify_fallback] requesting up to {capped} reviews for {property_url} (~${estimated_cost:.3f})")

    run_input = {"startUrls": [{"url": property_url}], "maxNumberOfReviews": capped}
    if cutoff_date is not None:
        run_input["targetDate"] = cutoff_date.isoformat()

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            APIFY_RUN_SYNC_URL,
            params={"token": settings.apify_api_token},
            json=run_input,
        )
        response.raise_for_status()
        items = response.json()

    # Actor returns one dataset item per run containing {entity, reviews:[...]}
    # -- confirmed by live testing, not what the input-schema docs implied.
    raw_reviews = items[0].get("reviews", []) if items else []
    return [_map_apify_review(r) for r in raw_reviews]
