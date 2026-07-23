import { useEffect, useMemo, useState } from "react";
import { format, startOfWeek } from "date-fns";
import { Area, AreaChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "./Card";
import { fetchReviews } from "../api/dashboard";
import type { ReviewItem } from "../types/dashboard";

interface TrendChartProps {
  propertyId: number | null;
  title?: string;
}

interface WeekPoint {
  week: string;
  avgRating: number;
  liked: number;
  disliked: number;
}

type MetricKey = "avgRating" | "liked" | "disliked";

const METRICS: { key: MetricKey; label: string; color: string; axis: "rating" | "count" }[] = [
  { key: "avgRating", label: "Avg rating", color: "#2680ea", axis: "rating" },
  { key: "liked", label: "Liked mentions", color: "#10b981", axis: "count" },
  { key: "disliked", label: "Disliked mentions", color: "#f43f5e", axis: "count" },
];

function bucketReviews(reviews: ReviewItem[]): WeekPoint[] {
  const buckets = new Map<string, { ratings: number[]; liked: number; disliked: number }>();

  for (const review of reviews) {
    if (!review.review_date) continue;
    const weekStart = format(startOfWeek(new Date(review.review_date), { weekStartsOn: 1 }), "MMM d");
    const bucket = buckets.get(weekStart) ?? { ratings: [], liked: 0, disliked: 0 };
    bucket.ratings.push(review.rating);
    if (review.positive_text) bucket.liked += 1;
    if (review.negative_text) bucket.disliked += 1;
    buckets.set(weekStart, bucket);
  }

  return Array.from(buckets.entries())
    .map(([week, b]) => ({
      week,
      avgRating: Math.round((b.ratings.reduce((a, r) => a + r, 0) / b.ratings.length) * 10) / 10,
      liked: b.liked,
      disliked: b.disliked,
    }))
    .sort((a, b) => (a.week > b.week ? 1 : -1));
}

export function TrendChart({ propertyId, title }: TrendChartProps) {
  const [data, setData] = useState<WeekPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<Set<MetricKey>>(new Set(["avgRating", "liked", "disliked"]));

  useEffect(() => {
    setLoading(true);
    fetchReviews({ propertyId: propertyId ?? undefined, limit: 200 })
      .then((res) => setData(bucketReviews(res.items)))
      .finally(() => setLoading(false));
  }, [propertyId]);

  const toggle = (key: MetricKey) => {
    setActive((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        if (next.size === 1) return prev; // keep at least one series visible
        next.delete(key);
      } else {
        next.add(key);
      }
      return next;
    });
  };

  const hasCountSeries = useMemo(() => active.has("liked") || active.has("disliked"), [active]);
  const hasRatingSeries = active.has("avgRating");

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm font-semibold text-slate-700">
          {title ?? (propertyId ? "Review trend for this property" : "Review trend across all properties")}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {METRICS.map((m) => {
            const isActive = active.has(m.key);
            return (
              <button
                key={m.key}
                type="button"
                onClick={() => toggle(m.key)}
                className="rounded-full px-3 py-1 text-xs font-medium transition-colors"
                style={
                  isActive
                    ? { backgroundColor: m.color, color: "white" }
                    : { backgroundColor: "#f1f5f9", color: "#64748b" }
                }
              >
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      <div className="mt-4 h-64">
        {loading ? (
          <p className="text-sm text-slate-500">Loading trend…</p>
        ) : data.length === 0 ? (
          <p className="text-sm text-slate-500">Not enough dated reviews yet to chart a trend.</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ left: -12, right: 8, top: 8 }}>
              <defs>
                {METRICS.map((m) => (
                  <linearGradient key={m.key} id={`grad-${m.key}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={m.color} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={m.color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid vertical={true} horizontal={false} stroke="#eef2f7" strokeDasharray="4 4" />
              <XAxis
                dataKey="week"
                tick={{ fontSize: 12, fill: "#94a3b8" }}
                axisLine={{ stroke: "#e2e8f0" }}
                tickLine={false}
              />
              {hasCountSeries && (
                <YAxis
                  yAxisId="count"
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                  width={28}
                />
              )}
              {hasRatingSeries && (
                <YAxis
                  yAxisId="rating"
                  orientation="right"
                  domain={[0, 10]}
                  tick={{ fontSize: 12, fill: "#94a3b8" }}
                  axisLine={false}
                  tickLine={false}
                  width={28}
                />
              )}
              <Tooltip
                contentStyle={{ borderRadius: 10, border: "1px solid #e2e8f0", fontSize: 13, boxShadow: "0 4px 12px rgba(0,0,0,0.06)" }}
              />
              <Legend
                verticalAlign="bottom"
                height={28}
                iconType="circle"
                iconSize={8}
                wrapperStyle={{ fontSize: 12, color: "#64748b" }}
              />
              {METRICS.filter((m) => active.has(m.key)).map((m) => (
                <Area
                  key={m.key}
                  yAxisId={m.axis}
                  type="monotone"
                  dataKey={m.key}
                  name={m.label}
                  stroke={m.color}
                  strokeWidth={2.5}
                  fill={`url(#grad-${m.key})`}
                  dot={{ r: 3, fill: m.color, strokeWidth: 0 }}
                  activeDot={{ r: 5 }}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </Card>
  );
}
