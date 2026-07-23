import { useEffect, useState } from "react";
import { Star, MessageSquare, Building2 } from "lucide-react";
import { KpiCard } from "../components/KpiCard";
import { PropertyBreakdown } from "../components/PropertyBreakdown";
import { TrendChart } from "../components/TrendChart";
import { TopicInsightsPanel } from "../components/TopicInsightsPanel";
import { AiInsightsButton } from "../components/AiInsightsButton";
import { ScrapeButton } from "../components/ScrapeButton";
import { fetchHealth } from "../api/health";
import { fetchProperties, fetchPropertySummary, fetchTopicInsights, fetchWeeklySummary } from "../api/dashboard";
import type { PropertySummary, TopicInsightsResponse, WeeklySummary } from "../types/dashboard";

function formatDelta(delta: number | null): { label: string; tone: "up" | "down" | "flat" } {
  if (delta === null) return { label: "no prior data", tone: "flat" };
  if (delta > 0) return { label: `+${delta.toFixed(2)} vs last week`, tone: "up" };
  if (delta < 0) return { label: `${delta.toFixed(2)} vs last week`, tone: "down" };
  return { label: "flat vs last week", tone: "flat" };
}

export function OverviewPage() {
  const [llmEnabled, setLlmEnabled] = useState(false);
  const [scrapeEnabled, setScrapeEnabled] = useState(false);
  const [summaries, setSummaries] = useState<PropertySummary[]>([]);
  const [weekly, setWeekly] = useState<WeeklySummary | null>(null);
  const [topics, setTopics] = useState<TopicInsightsResponse | null>(null);

  useEffect(() => {
    fetchHealth().then((h) => {
      setLlmEnabled(h.llm_classification_enabled);
      setScrapeEnabled(h.scrape_endpoint_enabled);
    });
    fetchProperties().then(async (props) => {
      const summaryList = await Promise.all(props.map((p) => fetchPropertySummary(p.id)));
      setSummaries(summaryList);
    });
    fetchWeeklySummary().then(setWeekly);
    fetchTopicInsights().then(setTopics);
  }, []);

  const delta = formatDelta(weekly?.delta ?? null);

  return (
    <>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Operations Dashboard</h1>
          <p className="mt-1 text-sm text-slate-500">
            Guest review sentiment across all Azzurro Hotels properties.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <ScrapeButton scrapeEnabled={scrapeEnabled} />
          <AiInsightsButton llmEnabled={llmEnabled} />
        </div>
      </div>

      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <KpiCard
          label="This week's avg rating"
          value={weekly?.current_week_avg_rating?.toFixed(1) ?? "—"}
          sublabel={`${weekly?.current_week_review_count ?? 0} reviews`}
          deltaLabel={delta.label}
          deltaTone={delta.tone}
          icon={Star}
          accent="#2680ea"
        />
        <KpiCard
          label="Last week's avg rating"
          value={weekly?.previous_week_avg_rating?.toFixed(1) ?? "—"}
          sublabel={`${weekly?.previous_week_review_count ?? 0} reviews`}
          icon={MessageSquare}
          accent="#8b5cf6"
        />
        <KpiCard
          label="Properties tracked"
          value={String(summaries.length)}
          sublabel="across Sydney"
          icon={Building2}
          accent="#14b8a6"
        />
      </div>

      <div className="mt-6">
        <TrendChart propertyId={null} />
      </div>

      <h2 className="mt-8 text-sm font-semibold text-slate-700">Properties</h2>
      <p className="text-xs text-slate-500">Click a property to see its full page.</p>
      <div className="mt-3">
        <PropertyBreakdown summaries={summaries} />
      </div>

      <div className="mt-8">
        {topics && <TopicInsightsPanel items={topics.items} periodDays={topics.period_days} />}
      </div>
    </>
  );
}
