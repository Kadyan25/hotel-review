export interface PropertyItem {
  id: number;
  name: string;
  slug: string;
  city: string;
  booking_url: string;
  thumbnail_url: string | null;
}

export interface PropertySummary {
  property: PropertyItem;
  review_count: number;
  avg_rating: number | null;
  latest_review_date: string | null;
}

export interface ReviewTopicItem {
  topic: string;
  sentiment: "positive" | "negative";
  confidence: number | null;
  source: "keyword" | "llm";
}

export interface ReviewItem {
  id: number;
  property_id: number;
  reviewer_name: string | null;
  reviewer_country: string | null;
  rating: number;
  review_date: string | null;
  stay_date: string | null;
  room_type: string | null;
  length_of_stay: number | null;
  positive_text: string | null;
  negative_text: string | null;
  full_text: string | null;
  topics: ReviewTopicItem[];
}

export interface ReviewListResponse {
  total: number;
  items: ReviewItem[];
}

export interface WeeklySummary {
  current_week_avg_rating: number | null;
  current_week_review_count: number;
  previous_week_avg_rating: number | null;
  previous_week_review_count: number;
  delta: number | null;
}

export interface TopicInsightItem {
  topic: string;
  negative_count: number;
  positive_count: number;
  negative_pct_of_total_negative: number;
}

export interface TopicInsightsResponse {
  period_days: number;
  items: TopicInsightItem[];
}

export interface ClassifyLLMResponse {
  enabled: boolean;
  classified_count: number;
  message: string;
}
