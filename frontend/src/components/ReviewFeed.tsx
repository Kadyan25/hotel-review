import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Card } from "./Card";
import { StatusPill } from "./StatusPill";
import { Button } from "./ui/button";
import { fetchReviews } from "../api/dashboard";
import { formatTopic, topicColor } from "../constants/topicColors";
import type { ReviewItem } from "../types/dashboard";

interface ReviewFeedProps {
  propertyId: number | null;
  dateFrom: string;
  dateTo: string;
  topic: string;
}

const PAGE_SIZE = 8;

function ratingTone(rating: number): "ok" | "error" | "neutral" {
  if (rating >= 7) return "ok";
  if (rating <= 4) return "error";
  return "neutral";
}

export function ReviewFeed({ propertyId, dateFrom, dateTo, topic }: ReviewFeedProps) {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Any filter change resets back to page 1 -- otherwise you can land on a
  // now-empty page 4 of a filtered set that only has 2 pages.
  useEffect(() => setPage(0), [propertyId, dateFrom, dateTo, topic]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchReviews({
      propertyId: propertyId ?? undefined,
      from: dateFrom || undefined,
      to: dateTo || undefined,
      topic: topic || undefined,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    })
      .then((res) => {
        setReviews(res.items);
        setTotal(res.total);
      })
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, [propertyId, dateFrom, dateTo, topic, page]);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  if (loading) return <p className="text-sm text-slate-500">Loading reviews…</p>;
  if (error) return <p className="text-sm text-red-600">Couldn't load reviews: {error}</p>;
  if (reviews.length === 0) return <p className="text-sm text-slate-500">No reviews match these filters.</p>;

  return (
    <div>
      <ul className="space-y-3">
        {reviews.map((review) => (
          <li key={review.id}>
            <Card className="p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-slate-900">
                    {review.reviewer_name ?? "Guest"}
                    {review.reviewer_country && (
                      <span className="font-normal text-slate-500"> · {review.reviewer_country}</span>
                    )}
                  </p>
                  <p className="text-xs text-slate-500">
                    {review.review_date ?? "unknown date"}
                    {review.room_type && ` · ${review.room_type}`}
                  </p>
                </div>
                <StatusPill label={review.rating.toFixed(1)} tone={ratingTone(review.rating)} />
              </div>

              {review.positive_text && (
                <p className="mt-3 text-sm text-slate-700">
                  <span className="font-medium text-emerald-700">Liked: </span>
                  {review.positive_text}
                </p>
              )}
              {review.negative_text && (
                <p className="mt-1 text-sm text-slate-700">
                  <span className="font-medium text-red-700">Disliked: </span>
                  {review.negative_text}
                </p>
              )}

              {review.topics.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {review.topics.map((t, i) => {
                    const color = topicColor(t.topic);
                    return (
                      <span
                        key={i}
                        className="rounded-full px-2 py-0.5 text-xs font-medium"
                        style={{ backgroundColor: `${color}1a`, color }}
                      >
                        {formatTopic(t.topic)}
                      </span>
                    );
                  })}
                </div>
              )}
            </Card>
          </li>
        ))}
      </ul>

      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-slate-500">
          Page {page + 1} of {totalPages} · {total} reviews
        </p>
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" disabled={page === 0} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft />
            Prev
          </Button>
          <Button
            variant="secondary"
            size="sm"
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
          >
            Next
            <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  );
}
