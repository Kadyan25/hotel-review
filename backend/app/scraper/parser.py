"""Parses one review card into a plain dict.

Selectors are the data-testid attributes confirmed by live DOM inspection
against the Surry Hills property page (see architecture.md "Confirmed DOM
structure"). Isolated here so markup drift only requires touching this file.
"""

import re
from datetime import date, datetime

from patchright.async_api import Locator

_SCORE_RE = re.compile(r"(\d+(?:\.\d+)?)")
_NIGHTS_RE = re.compile(r"(\d+)")
_DATE_PREFIX_RE = re.compile(r"^Reviewed:\s*")
# The avatar block briefly renders a placeholder ("7 reviews", "Active since
# 2018") before its flag+country element finishes loading -- confirmed live
# that reviewers we scraped with these values have real countries in the
# DOM moments later. Timing issue, not a selector issue; rather than retry
# (adds scrape time for a cosmetic field), reject the placeholder and store
# None -- wrong data is worse than missing data.
_NOT_A_COUNTRY_RE = re.compile(r"^\d+ reviews?$|^Active since \d{4}$", re.IGNORECASE)


def _parse_stay_month(raw: str | None) -> date | None:
    """Booking only gives month + year for the stay ("July 2026"), never a
    day. Approximated as the 1st of that month -- exact day isn't available
    and isn't needed for the trend-level use this field serves.
    """
    if not raw:
        return None
    try:
        return datetime.strptime(raw.strip(), "%B %Y").date().replace(day=1)
    except ValueError:
        return None


async def _text_or_none(card: Locator, testid: str) -> str | None:
    loc = card.locator(f'[data-testid="{testid}"]').first
    if await loc.count() == 0:
        return None
    text = (await loc.inner_text()).strip()
    return text or None


_REVIEW_DATE_FORMATS = (
    "%d %B %Y",  # en-AU/en-GB rendering: "9 July 2026" -- our session locale
    "%B %d, %Y",  # en-US rendering: "July 9, 2026" -- kept as a fallback
)


def _parse_review_date(raw: str | None) -> date | None:
    if not raw:
        return None
    cleaned = _DATE_PREFIX_RE.sub("", raw).strip()
    for fmt in _REVIEW_DATE_FORMATS:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue
    return None


def _parse_score(raw: str | None) -> float | None:
    if not raw:
        return None
    match = _SCORE_RE.search(raw)
    return float(match.group(1)) if match else None


def _parse_nights(raw: str | None) -> int | None:
    if not raw:
        return None
    match = _NIGHTS_RE.search(raw)
    return int(match.group(1)) if match else None


async def parse_review_card(card: Locator) -> dict:
    avatar_text = await _text_or_none(card, "review-avatar")
    avatar_lines = [line.strip() for line in (avatar_text or "").split("\n") if line.strip()]
    reviewer_name = avatar_lines[0] if avatar_lines else None
    reviewer_country = avatar_lines[1] if len(avatar_lines) > 1 else None
    if reviewer_country and _NOT_A_COUNTRY_RE.match(reviewer_country):
        reviewer_country = None

    positive_text = await _text_or_none(card, "review-positive-text")
    negative_text = await _text_or_none(card, "review-negative-text")
    full_text = "\n".join(t for t in (positive_text, negative_text) if t) or None

    review_date_raw = await _text_or_none(card, "review-date")
    review_date = _parse_review_date(review_date_raw)

    return {
        "reviewer_name": reviewer_name,
        "reviewer_country": reviewer_country,
        "rating": _parse_score(await _text_or_none(card, "review-score")),
        "review_date": review_date,
        "review_date_iso": review_date.isoformat() if review_date else None,
        "stay_date": _parse_stay_month(await _text_or_none(card, "review-stay-date")),
        "room_type": await _text_or_none(card, "review-room-name"),
        "length_of_stay": _parse_nights(await _text_or_none(card, "review-num-nights")),
        "positive_text": positive_text,
        "negative_text": negative_text,
        "full_text": full_text,
        "title": await _text_or_none(card, "review-title"),
        "traveler_type": await _text_or_none(card, "review-traveler-type"),
        "source": "patchright",
    }
