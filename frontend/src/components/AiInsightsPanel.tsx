import { Sparkles, NotebookPen, ThumbsUp, ThumbsDown } from "lucide-react";
import { Card } from "./Card";
import { formatTopic, topicColor } from "../constants/topicColors";
import type { TopicInsightItem } from "../types/dashboard";

interface AiInsightsPanelProps {
  items: TopicInsightItem[] | null;
  periodDays: number;
  briefingText?: string | null;
  briefingGeneratedAt?: string | null;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

// Distinct from TopicInsightsPanel (keyword-matched, always-on, every
// review) -- this one shows only what the AI pass actually classified, so
// operations staff can tell "the system found this automatically" apart
// from "an AI read this and concluded that." The topic narrative line is
// computed from the real counts (not a second AI call, so it can't drift
// from the bars below it); the briefing block above it is the one part
// that's genuinely AI-written synthesis, not a re-derived statistic.
export function AiInsightsPanel({ items, periodDays, briefingText, briefingGeneratedAt }: AiInsightsPanelProps) {
  const hasData = items !== null && items.length > 0 && items.some((i) => i.negative_count + i.positive_count > 0);

  return (
    <Card className="border-violet-200 bg-violet-50/40 p-5">
      <div className="flex items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-100 text-violet-600">
          <Sparkles className="h-3.5 w-3.5" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-700">AI-Generated Insights</p>
          <p className="text-xs text-slate-500">AI-powered · last {periodDays} days</p>
        </div>
      </div>

      {briefingText && (
        <div className="mt-4 rounded-lg border border-violet-200 bg-white p-3.5">
          <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-violet-600">
            <NotebookPen className="h-3.5 w-3.5" /> Manager's briefing
            {briefingGeneratedAt && <span className="font-normal normal-case text-slate-400">· {formatDate(briefingGeneratedAt)}</span>}
          </p>
          <p className="mt-2 text-sm leading-relaxed text-slate-700">{briefingText}</p>
        </div>
      )}

      {!hasData ? (
        <p className="mt-4 text-sm text-slate-500">
          No AI-classified insights yet. Click "Get AI Insights" above to have AI analyse reviews the
          keyword pass couldn't confidently tag.
        </p>
      ) : (
        <>
          <p className="mt-4 text-sm text-slate-700">{buildNarrative(items!)}</p>
          <ul className="mt-4 space-y-4">
            {items!
              .filter((item) => item.negative_count + item.positive_count > 0)
              .map((item) => {
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
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white">
                        <div
                          className="h-full rounded-full bg-emerald-400 transition-all"
                          style={{ width: `${Math.min(100, item.positive_pct_of_total_positive)}%` }}
                        />
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white">
                        <div
                          className="h-full rounded-full transition-all"
                          style={{
                            width: `${Math.min(100, item.negative_pct_of_total_negative)}%`,
                            backgroundColor: color,
                          }}
                        />
                      </div>
                    </div>
                  </li>
                );
              })}
          </ul>
        </>
      )}
    </Card>
  );
}

function buildNarrative(items: TopicInsightItem[]): string {
  const topNegative = [...items].filter((i) => i.negative_count > 0).sort((a, b) => b.negative_count - a.negative_count)[0];
  const topPositive = [...items].filter((i) => i.positive_count > 0).sort((a, b) => b.positive_count - a.positive_count)[0];

  const negativePart = topNegative
    ? `${topNegative.negative_pct_of_total_negative}% of AI-classified negative reviews mentioned ${formatTopic(topNegative.topic).toLowerCase()}-related issues`
    : null;
  const positivePart = topPositive
    ? `${formatTopic(topPositive.topic)} was the most praised topic (${topPositive.positive_pct_of_total_positive}% of positive mentions)`
    : null;

  if (negativePart && positivePart) return `${negativePart}. ${positivePart}.`;
  if (negativePart) return `${negativePart}.`;
  if (positivePart) return `${positivePart}.`;
  return "No topics found among the AI-classified reviews yet.";
}
