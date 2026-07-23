from datetime import date

from pydantic import BaseModel, ConfigDict


class ReviewTopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    topic: str
    sentiment: str
    confidence: float | None
    source: str


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    property_id: int
    reviewer_name: str | None
    reviewer_country: str | None
    rating: float
    review_date: date | None
    stay_date: date | None
    room_type: str | None
    length_of_stay: int | None
    positive_text: str | None
    negative_text: str | None
    full_text: str | None
    topics: list[ReviewTopicOut] = []


class ReviewListOut(BaseModel):
    total: int
    items: list[ReviewOut]
