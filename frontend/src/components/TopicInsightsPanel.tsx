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
      <p className="text-sm font-semibold text-slate-700">Negative review topics — last {periodDays} days</p>
      <ul className="mt-4 space-y-3">
        {items.map((item) => {
          const color = topicColor(item.topic);
          return (
            <li key={item.topic}>
              <div className="flex items-center justify-between text-sm">
                <span className="flex items-center gap-2 font-medium text-slate-700">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: color }} />
                  {formatTopic(item.topic)}
                </span>
                <span className="text-slate-500">
                  {item.negative_pct_of_total_negative}% ({item.negative_count})
                </span>
              </div>
              <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full transition-all"
                  style={{ width: `${Math.min(100, item.negative_pct_of_total_negative)}%`, backgroundColor: color }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </Card>
  );
}
