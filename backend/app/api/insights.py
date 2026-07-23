import logging
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.classification.keyword_classifier import has_any_match
from app.classification.llm_client import classify_snippet_with_llm, generate_manager_briefing
from app.config import Settings, get_settings
from app.db.session import get_db
from app.models import LlmInsightRun, Review, ReviewTopic
from app.schemas.insights import (
    ClassifyLLMResponse,
    LlmStatusOut,
    TopicInsightItem,
    TopicInsightsOut,
    WeeklySummaryOut,
)

BRIEFING_PERIOD_DAYS = 30
BRIEFING_QUOTE_LIMIT = 8
BRIEFING_QUOTE_MAX_CHARS = 220


async def _latest_llm_run(db: AsyncSession, property_id: int | None) -> LlmInsightRun | None:
    stmt = (
        select(LlmInsightRun)
        .where(LlmInsightRun.property_id == property_id)
        .order_by(LlmInsightRun.run_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalars().first()


async def _negative_topic_counts(db: AsyncSession, property_id: int | None, period_days: int) -> list[tuple[str, int]]:
    cutoff = date.today() - timedelta(days=period_days)
    stmt = (
        select(ReviewTopic.topic, func.count())
        .join(Review, Review.id == ReviewTopic.review_id)
        .where(Review.review_date >= cutoff, ReviewTopic.sentiment == "negative")
        .group_by(ReviewTopic.topic)
    )
    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    rows = (await db.execute(stmt)).all()
    return sorted(rows, key=lambda r: -r[1])


async def _recent_negative_quotes(db: AsyncSession, property_id: int | None, period_days: int) -> list[str]:
    cutoff = date.today() - timedelta(days=period_days)
    stmt = (
        select(Review.negative_text)
        .where(Review.negative_text.isnot(None), Review.review_date >= cutoff)
        .order_by(Review.review_date.desc())
        .limit(BRIEFING_QUOTE_LIMIT)
    )
    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    rows = (await db.execute(stmt)).scalars().all()
    return [r[:BRIEFING_QUOTE_MAX_CHARS] for r in rows if r]

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
    source: str | None = None,
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
    if source is not None:
        stmt = stmt.where(ReviewTopic.source == source)

    rows = (await db.execute(stmt)).all()

    counts: dict[str, dict[str, int]] = {}
    for topic, sent, cnt in rows:
        counts.setdefault(topic, {"positive": 0, "negative": 0})[sent] = cnt

    total_negative = sum(c["negative"] for c in counts.values()) or 1
    total_positive = sum(c["positive"] for c in counts.values()) or 1

    items = [
        TopicInsightItem(
            topic=topic,
            negative_count=c["negative"],
            positive_count=c["positive"],
            negative_pct_of_total_negative=round(100 * c["negative"] / total_negative, 1),
            positive_pct_of_total_positive=round(100 * c["positive"] / total_positive, 1),
        )
        # Rank by total mentions, not negative-only -- a topic guests praise
        # a lot (e.g. location) is just as much "an insight" as one they
        # complain about, and shouldn't be buried at the bottom of the list.
        for topic, c in sorted(counts.items(), key=lambda kv: -(kv[1]["negative"] + kv[1]["positive"]))
    ]

    return TopicInsightsOut(period_days=period_days, items=items)


@router.get("/insights/llm-status", response_model=LlmStatusOut)
async def llm_status(
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
    property_id: int | None = None,
):
    if not settings.llm_configured:
        return LlmStatusOut(enabled=False, last_run_at=None, can_run_today=False, briefing_text=None)

    last_run = await _latest_llm_run(db, property_id)
    ran_today = last_run is not None and last_run.run_at.date() == datetime.now(last_run.run_at.tzinfo).date()
    return LlmStatusOut(
        enabled=True,
        last_run_at=last_run.run_at if last_run else None,
        can_run_today=not ran_today,
        briefing_text=last_run.briefing_text if last_run else None,
    )


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

    # Cap to once per calendar day per scope (property, or collective if
    # property_id is absent) -- re-running against the same reviews can
    # yield different results from Claude on identical input, which would
    # be confusing to show as "the" insight, and it burns budget for no
    # new information since a scrape (which is what actually changes the
    # candidate set) doesn't happen more than once a day either.
    existing_run = await _latest_llm_run(db, property_id)
    if existing_run is not None and existing_run.run_at.date() == datetime.now(existing_run.run_at.tzinfo).date():
        return ClassifyLLMResponse(
            enabled=True,
            classified_count=0,
            message="AI insights already generated today for this scope.",
            already_run_today=True,
            last_run_at=existing_run.run_at,
            briefing_text=existing_run.briefing_text,
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

    # Manager's briefing: synthesis over the aggregated picture (all sources,
    # not just what this run classified), grounded in real counts and
    # verbatim quotes -- this is the part keyword matching can't do at all.
    briefing_text = None
    try:
        topic_counts = await _negative_topic_counts(db, property_id, BRIEFING_PERIOD_DAYS)
        quotes = await _recent_negative_quotes(db, property_id, BRIEFING_PERIOD_DAYS)
        briefing_text = await generate_manager_briefing(topic_counts, quotes, settings)
    except Exception:
        logger.exception("Manager briefing generation failed, continuing without it")

    run = LlmInsightRun(
        property_id=property_id,
        classified_count=classified_count,
        failed_count=failed_count,
        briefing_text=briefing_text,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    message = f"Classified {classified_count} review(s) via Claude Haiku."
    if failed_count:
        message += f" {failed_count} failed and were skipped."

    return ClassifyLLMResponse(
        enabled=True,
        classified_count=classified_count,
        message=message,
        already_run_today=False,
        last_run_at=run.run_at,
        briefing_text=briefing_text,
    )
