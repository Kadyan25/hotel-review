from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("property_id", "external_review_id", name="uq_review_property_external_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int] = mapped_column(ForeignKey("properties.id"), index=True)
    external_review_id: Mapped[str] = mapped_column(String(255), index=True)

    reviewer_name: Mapped[str | None] = mapped_column(String(255))
    reviewer_country: Mapped[str | None] = mapped_column(String(100))
    rating: Mapped[float] = mapped_column(Float)
    review_date: Mapped[date | None] = mapped_column(Date, index=True)
    stay_date: Mapped[date | None] = mapped_column(Date)
    room_type: Mapped[str | None] = mapped_column(String(255))
    length_of_stay: Mapped[int | None] = mapped_column(Integer)

    positive_text: Mapped[str | None] = mapped_column(Text)
    negative_text: Mapped[str | None] = mapped_column(Text)
    full_text: Mapped[str | None] = mapped_column(Text)

    scraped_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    raw_json: Mapped[dict | None] = mapped_column(JSON)

    property: Mapped["Property"] = relationship(back_populates="reviews")
    topics: Mapped[list["ReviewTopic"]] = relationship(back_populates="review", cascade="all, delete-orphan")
