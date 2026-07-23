"""Runs the free keyword classifier against every review that doesn't yet
have a keyword-sourced topic row. Safe to re-run -- skips reviews already
classified.

Usage: python scripts/classify_keyword.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import and_, select

from app.classification.keyword_classifier import classify_review_keyword
from app.db.session import async_session_maker
from app.models import Review, ReviewTopic


async def main() -> None:
    async with async_session_maker() as session:
        stmt = (
            select(Review)
            .outerjoin(ReviewTopic, and_(ReviewTopic.review_id == Review.id, ReviewTopic.source == "keyword"))
            .where(ReviewTopic.id.is_(None))
        )
        candidates = (await session.execute(stmt)).scalars().all()

        classified_reviews = 0
        topic_rows = 0
        for review in candidates:
            results = classify_review_keyword(review.positive_text, review.negative_text)
            for item in results:
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
            if results:
                classified_reviews += 1

        await session.commit()
        print(f"scanned {len(candidates)} reviews, {classified_reviews} had keyword matches, {topic_rows} topic rows added")


asyncio.run(main())
