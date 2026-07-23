from datetime import date

from pydantic import BaseModel, ConfigDict


class PropertyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    city: str
    booking_url: str


class PropertySummaryOut(BaseModel):
    property: PropertyOut
    review_count: int
    avg_rating: float | None
    latest_review_date: date | None
