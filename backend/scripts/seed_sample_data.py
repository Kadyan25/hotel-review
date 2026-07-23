"""One-time seed for a fresh database (e.g. a new Railway Postgres instance):
creates the 4 properties and loads data/sample_reviews.json, then backfills
keyword classification. Safe to re-run -- skips reviews whose
external_review_id already exists.

Usage: python scripts/seed_sample_data.py
(point DATABASE_URL at the target DB via env var/.env before running)
"""

import asyncio
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.classification.keyword_classifier import classify_review_keyword
from app.db.session import async_session_maker
from app.models import Property, Review, ReviewTopic
from app.scraper.properties import PROPERTIES

DATA_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "sample_reviews.json"

# Captured live during the original scrape (side effect of the scraper
# already being on the property page) -- carried over here since the sample
# dataset export only includes reviews, not property metadata.
THUMBNAILS = {
    "darling-harbour": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/836420405.jpg?k=1677be7823b651afad60f378f5e72d1d4a3694e4f593cac17b731e712156837c&o=",
    "surry-hills": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/896224442.jpg?k=41bd83198044f8eb2a2bd3a6a9c2f6f2d7e32d093ba117406386262318b01f6e&o=",
    "potts-point": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/836420451.jpg?k=6d17b6a6cc099ff5ae76ae008cbf483c792d4465bb21eeafff37a426aa962272&o=",
    "central-sydney": "https://cf.bstatic.com/xdata/images/hotel/max1024x768/896335236.jpg?k=09fead949e68c9f404ea91ea9a508b76114f926ebf12bf7d1cee2165ed520390&o=",
}


async def main() -> None:
    async with async_session_maker() as session:
        slug_to_id: dict[str, int] = {}
        for prop_def in PROPERTIES:
            existing = (await session.execute(select(Property).where(Property.slug == prop_def.slug))).scalar_one_or_none()
            if existing is None:
                existing = Property(
                    slug=prop_def.slug,
                    name=prop_def.name,
                    city=prop_def.city,
                    booking_url=prop_def.booking_url,
                    thumbnail_url=THUMBNAILS.get(prop_def.slug),
                )
                session.add(existing)
                await session.flush()
                print(f"created property {prop_def.slug}")
            slug_to_id[prop_def.slug] = existing.id
        await session.commit()

        reviews_data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        existing_ids = set((await session.execute(select(Review.external_review_id))).scalars().all())

        inserted = 0
        for row in reviews_data:
            if row["external_review_id"] in existing_ids:
                continue
            review = Review(
                property_id=slug_to_id[row["property"]],
                external_review_id=row["external_review_id"],
                reviewer_name=row["reviewer_name"],
                reviewer_country=row["reviewer_country"],
                rating=row["rating"],
                review_date=date.fromisoformat(row["review_date"]) if row["review_date"] else None,
                stay_date=date.fromisoformat(row["stay_date"]) if row["stay_date"] else None,
                room_type=row["room_type"],
                length_of_stay=row["length_of_stay"],
                positive_text=row["positive_text"],
                negative_text=row["negative_text"],
                full_text=row["full_text"],
            )
            session.add(review)
            inserted += 1
        await session.commit()
        print(f"inserted {inserted} reviews ({len(reviews_data) - inserted} already present)")

        candidates = (
            await session.execute(
                select(Review).outerjoin(ReviewTopic, ReviewTopic.review_id == Review.id).where(ReviewTopic.id.is_(None))
            )
        ).scalars().all()
        topic_rows = 0
        for review in candidates:
            for item in classify_review_keyword(review.positive_text, review.negative_text):
                session.add(
                    ReviewTopic(
                        review_id=review.id,
                        topic=item["topic"],
                        sentiment=item["sentiment"],
                        confidence=item["confidence"],
                        source="keyword",
                    )
                )
                topic_rows += 1
        await session.commit()
        print(f"added {topic_rows} keyword topic rows across {len(candidates)} reviews")


asyncio.run(main())
