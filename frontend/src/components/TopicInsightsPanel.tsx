import { ThumbsUp, ThumbsDown } from "lucide-react";
import { Card } from "./Card";
import { formatTopic, topicColor } from "../constants/topicColors";
import type { TopicInsightItem } from "../types/dashboard";

interface TopicInsightsPanelProps {
  items: TopicInsightItem[];
  periodDays: number;
}

export function TopicInsightsPanel({ items, periodDays }: TopicInsightsPanelProps) {
  if (items.length === 0) {
    return (
      <Card className="p-5">
        <p className="text-sm text-slate-500">No topic-tagged reviews in the last {periodDays} days yet.</p>
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <p className="text-sm font-semibold text-slate-700">Review topics — last {periodDays} days</p>
      <ul className="mt-4 space-y-4">
        {items.map((item) => {
          const color = topicColor(item.topic);
          return (
            <li key={item.topic}>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium text-slate-700">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {formatTopic(item.topic)}
                </span>
                <span className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1 text-emerald-600">
                    <ThumbsUp className="h-3 w-3" /> {item.positive_pct_of_total_positive}% ({item.positive_count})
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsDown className="h-3 w-3" /> {item.negative_pct_of_total_negative}% ({item.negative_count})
                  </span>
                </span>
              </div>
              <div className="mt-1.5 space-y-1">
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-emerald-400 transition-all"
                    style={{ width: `${Math.min(100, item.positive_pct_of_total_positive)}%` }}
                  />
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full transition-all"
                    style={{ width: `${Math.min(100, item.negative_pct_of_total_negative)}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
