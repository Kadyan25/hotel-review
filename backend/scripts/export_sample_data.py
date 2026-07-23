"""Exports the current DB contents to data/sample_reviews.json -- the
committed sample-data deliverable. Re-run whenever you want to refresh the
snapshot after a new scrape.

Usage: python scripts/export_sample_data.py
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.session import async_session_maker
from app.models import Property, Review

OUT_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_reviews.json"


def _serialize(review: Review, property_slug: str) -> dict:
    return {
        "property": property_slug,
        "external_review_id": review.external_review_id,
        "reviewer_name": review.reviewer_name,
        "reviewer_country": review.reviewer_country,
        "rating": review.rating,
        "review_date": review.review_date.isoformat() if review.review_date else None,
        "stay_date": review.stay_date.isoformat() if review.stay_date else None,
        "room_type": review.room_type,
        "length_of_stay": review.length_of_stay,
        "positive_text": review.positive_text,
        "negative_text": review.negative_text,
        "full_text": review.full_text,
    }


async def main() -> None:
    async with async_session_maker() as session:
        result = await session.execute(
            select(Review, Property.slug).join(Property, Review.property_id == Property.id)
        )
        rows = result.all()

    data = [_serialize(review, slug) for review, slug in rows]
    data.sort(key=lambda r: (r["property"], r["review_date"] or ""), reverse=True)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"exported {len(data)} reviews to {OUT_PATH}")


asyncio.run(main())
