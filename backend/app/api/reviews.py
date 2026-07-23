from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models import Review, ReviewTopic
from app.schemas.review import ReviewListOut, ReviewOut

router = APIRouter()


@router.get("/reviews", response_model=ReviewListOut)
async def list_reviews(
    db: AsyncSession = Depends(get_db),
    property_id: int | None = None,
    date_from: date | None = Query(None, alias="from"),
    date_to: date | None = Query(None, alias="to"),
    topic: str | None = None,
    sentiment: str | None = None,
    min_rating: float | None = None,
    max_rating: float | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
):
    stmt = select(Review).options(selectinload(Review.topics))

    if property_id is not None:
        stmt = stmt.where(Review.property_id == property_id)
    if date_from is not None:
        stmt = stmt.where(Review.review_date >= date_from)
    if date_to is not None:
        stmt = stmt.where(Review.review_date <= date_to)
    if min_rating is not None:
        stmt = stmt.where(Review.rating >= min_rating)
    if max_rating is not None:
        stmt = stmt.where(Review.rating <= max_rating)
    if topic is not None:
        # Subquery instead of a join -- a join here would duplicate Review
        # rows per matching topic and skew both the page and the count.
        topic_subq = select(ReviewTopic.review_id).where(ReviewTopic.topic == topic)
        if sentiment is not None:
            topic_subq = topic_subq.where(ReviewTopic.sentiment == sentiment)
        stmt = stmt.where(Review.id.in_(topic_subq))

    total = (await db.execute(select(func.count()).select_from(stmt.subquery()))).scalar_one()

    stmt = stmt.order_by(Review.review_date.desc().nulls_last()).limit(limit).offset(offset)
    reviews = (await db.execute(stmt)).unique().scalars().all()

    return ReviewListOut(total=total, items=[ReviewOut.model_validate(r) for r in reviews])
