from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import Property, Review
from app.schemas.property import PropertyOut, PropertySummaryOut

router = APIRouter()


@router.get("/properties", response_model=list[PropertyOut])
async def list_properties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Property).order_by(Property.name))
    return result.scalars().all()


@router.get("/properties/{property_id}/summary", response_model=PropertySummaryOut)
async def property_summary(property_id: int, db: AsyncSession = Depends(get_db)):
    prop = await db.get(Property, property_id)
    if prop is None:
        raise HTTPException(status_code=404, detail="property not found")

    stmt = select(func.count(Review.id), func.avg(Review.rating), func.max(Review.review_date)).where(
        Review.property_id == property_id
    )
    count, avg_rating, latest_date = (await db.execute(stmt)).one()

    return PropertySummaryOut(
        property=PropertyOut.model_validate(prop),
        review_count=count or 0,
        avg_rating=round(avg_rating, 2) if avg_rating is not None else None,
        latest_review_date=latest_date,
    )
