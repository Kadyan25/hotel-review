import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.classification.keyword_classifier import has_any_match
from app.classification.llm_client import classify_snippet_with_llm
from app.config import Settings, get_settings
from app.db.session import get_db
from app.models import Review, ReviewTopic
from app.schemas.insights import (
    ClassifyLLMResponse,
    TopicInsightItem,
    TopicInsightsOut,
    WeeklySummaryOut,
)

router = APIRouter()


@router.get("/insights/weekly-summary", response_model=WeeklySummaryOut)
async def weekly_summary(db: AsyncSession = Depends(get_db), property_id: int | None = None):
    today = date.today()
    current_start = today - timedelta(days=7)
    previous_start = today - timedelta(days=14)

    async def week_stats(start: date, end: date) -> tuple[float | None, int]:
        stmt = select(func.avg(Review.rating), func.count(Review.id)).where(
            Review.review_date >= start, Review.review_date < end
        )
        if property_id is not None:
            stmt = stmt.where(Review.property_id == property_id)
        avg_rating, count = (await db.execute(stmt)).one()
        return (round(avg_rating, 2) if avg_rating is not None else None), (count or 0)

    current_avg, current_count = await week_stats(current_start, today + timedelta(days=1))
    previous_avg, previous_count = await week_stats(previous_start, current_start)

    delta = round(current_avg - previous_avg, 2) if current_avg is not None and previous_avg is not None else None

    return WeeklySummaryOut(
        current_week_avg_rating=current_avg,
        current_week_review_count=current_count,
        previous_week_avg_rating=previous_avg,
        previous_week_review_count=previous_count,
        delta=delta,
    )


@router.get("/insights/topics", response_model=TopicInsightsOut)
async def topic_insights(
    db: AsyncSession = Depends(get_db),
    property_id: int | None = None,
    sentiment: str | None = None,
    period_days: int = 30,
):
    cutoff = date.today() - timedelta(days=period_days)

    stmt = (
        select(ReviewTopic.topic, ReviewTopic.sentiment, func.count())
        .join(Review, Review.id == ReviewTopic.review_id)
        .where(Review.review_date >= cutoff)
        .group_by(ReviewTopic.topic, ReviewTopic.sentiment)
    )
    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    if sentiment is not None:
        stmt = stmt.where(ReviewTopic.sentiment == sentiment)

    rows = (await db.execute(stmt)).all()

    counts: dict[str, dict[str, int]] = {}
    for topic, sent, cnt in rows:
        counts.setdefault(topic, {"positive": 0, "negative": 0})[sent] = cnt

    total_negative = sum(c["negative"] for c in counts.values()) or 1

    items = [
        TopicInsightItem(
            topic=topic,
            negative_count=c["negative"],
            positive_count=c["positive"],
            negative_pct_of_total_negative=round(100 * c["negative"] / total_negative, 1),
        )
        for topic, c in sorted(counts.items(), key=lambda kv: -kv[1]["negative"])
    ]

    return TopicInsightsOut(period_days=period_days, items=items)


@router.post("/insights/classify-llm", response_model=ClassifyLLMResponse)
async def classify_llm(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    property_id: int | None = None,
):
    if not settings.llm_configured:
        return ClassifyLLMResponse(
            enabled=False, classified_count=0, message="LLM classification is not enabled/configured."
        )

    # Candidates: reviews with no existing LLM-sourced topic row yet, optionally
    # scoped to one property (per-hotel "Get AI Insights" button).
    stmt = (
        select(Review)
        .outerjoin(ReviewTopic, and_(ReviewTopic.review_id == Review.id, ReviewTopic.source == "llm"))
        .where(ReviewTopic.id.is_(None))
    )
    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    candidates = (await db.execute(stmt)).scalars().all()

    # "Ambiguous" = keyword pass found nothing on non-trivial text -- that's
    # the whole point of this being a fallback, not a routine second pass.
    ambiguous = [
        r
        for r in candidates
        if (r.positive_text or r.negative_text) and not has_any_match(r.positive_text, r.negative_text)
    ]
    ambiguous = ambiguous[: settings.max_llm_classifications]

    classified_count = 0
    failed_count = 0
    for review in ambiguous:
        text = "\n".join(t for t in (review.positive_text, review.negative_text) if t)
        try:
            results = await classify_snippet_with_llm(text, settings)
        except Exception:
            # One bad call (rate limit, transient network error) shouldn't
            # lose progress already made on the rest of the batch.
            logger.exception("LLM classification failed for review_id=%d, skipping", review.id)
            failed_count += 1
            continue

        if not results:
            continue
        for item in results:
            db.add(
                ReviewTopic(
                    review_id=review.id,
                    topic=item["topic"],
                    sentiment=item.get("sentiment", "negative"),
                    confidence=item.get("confidence"),
                    source="llm",
                )
            )
        classified_count += 1

    await db.commit()

    message = f"Classified {classified_count} review(s) via Claude Haiku."
    if failed_count:
        message += f" {failed_count} failed and were skipped."

    return ClassifyLLMResponse(enabled=True, classified_count=classified_count, message=message)
