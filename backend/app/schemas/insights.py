from pydantic import BaseModel


class WeeklySummaryOut(BaseModel):
    current_week_avg_rating: float | None
    current_week_review_count: int
    previous_week_avg_rating: float | None
    previous_week_review_count: int
    delta: float | None


class TopicInsightItem(BaseModel):
    topic: str
    negative_count: int
    positive_count: int
    negative_pct_of_total_negative: float


class TopicInsightsOut(BaseModel):
    period_days: int
    items: list[TopicInsightItem]


class ClassifyLLMResponse(BaseModel):
    enabled: bool
    classified_count: int
    message: str
