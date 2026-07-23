from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LlmInsightRun(Base):
    """One row per completed classify-llm call -- lets the API enforce
    "at most once per calendar day per scope" without an extra scheduler,
    and gives the frontend a persistent "last generated" timestamp instead
    of a one-off toast message that vanishes on refresh.

    property_id NULL means a collective (all-properties) run, matching how
    the rest of the insights endpoints treat an absent property_id.
    """

    __tablename__ = "llm_insight_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    property_id: Mapped[int | None] = mapped_column(ForeignKey("properties.id"), index=True)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    classified_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    # Short natural-language synthesis ("Manager's Briefing"), separate from
    # the per-review topic tags -- an LLM's actual value-add over keyword
    # matching is synthesis/recommendation, not re-deriving the same counts.
    briefing_text: Mapped[str | None] = mapped_column(Text)
