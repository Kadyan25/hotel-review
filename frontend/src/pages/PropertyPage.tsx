import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ExternalLink, Star, MessageSquare } from "lucide-react";
import { Card } from "../components/Card";
import { KpiCard } from "../components/KpiCard";
import { PropertyThumbnail } from "../components/PropertyThumbnail";
import { TrendChart } from "../components/TrendChart";
import { TopicInsightsPanel } from "../components/TopicInsightsPanel";
import { AiInsightsPanel } from "../components/AiInsightsPanel";
import { FilterBar } from "../components/FilterBar";
import { ReviewFeed } from "../components/ReviewFeed";
import { AiInsightsButton } from "../components/AiInsightsButton";
import { ScrapeButton } from "../components/ScrapeButton";
import { fetchHealth } from "../api/health";
import {
  fetchLlmStatus,
  fetchProperties,
  fetchPropertySummary,
  fetchTopicInsights,
  fetchWeeklySummary,
} from "../api/dashboard";
import type {
  ClassifyLLMResponse,
  PropertyItem,
  PropertySummary,
  TopicInsightsResponse,
  WeeklySummary,
} from "../types/dashboard";

function formatDelta(delta: number | null): { label: string; tone: "up" | "down" | "flat" } {
  if (delta === null) return { label: "no prior data", tone: "flat" };
  if (delta > 0) return { label: `+${delta.toFixed(2)} vs last week`, tone: "up" };
  if (delta < 0) return { label: `${delta.toFixed(2)} vs last week`, tone: "down" };
  return { label: "flat vs last week", tone: "flat" };
}

export function PropertyPage() {
  const { slug } = useParams<{ slug: string }>();
  const [property, setProperty] = useState<PropertyItem | null>(null);
  const [summary, setSummary] = useState<PropertySummary | null>(null);
  const [weekly, setWeekly] = useState<WeeklySummary | null>(null);
  const [topics, setTopics] = useState<TopicInsightsResponse | null>(null);
  const [aiTopics, setAiTopics] = useState<TopicInsightsResponse | null>(null);
  const [briefingText, setBriefingText] = useState<string | null>(null);
  const [briefingGeneratedAt, setBriefingGeneratedAt] = useState<string | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [llmEnabled, setLlmEnabled] = useState(false);
  const [scrapeEnabled, setScrapeEnabled] = useState(false);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [topicFilter, setTopicFilter] = useState("");

  useEffect(() => {
    fetchHealth().then((h) => {
      setLlmEnabled(h.llm_classification_enabled);
      setScrapeEnabled(h.scrape_endpoint_enabled);
    });
    fetchProperties().then((props) => {
      const match = props.find((p) => p.slug === slug);
      if (!match) {
        setNotFound(true);
        return;
      }
      setProperty(match);
      fetchPropertySummary(match.id).then(setSummary);
      fetchWeeklySummary(match.id).then(setWeekly);
      fetchTopicInsights(match.id).then(setTopics);
      fetchTopicInsights(match.id, "llm").then(setAiTopics);
      fetchLlmStatus(match.id).then((s) => {
        setBriefingText(s.briefing_text);
        setBriefingGeneratedAt(s.last_run_at);
      });
    });
  }, [slug]);

  const handleClassified = (result: ClassifyLLMResponse) => {
    if (!property) return;
    fetchTopicInsights(property.id).then(setTopics);
    fetchTopicInsights(property.id, "llm").then(setAiTopics);
    setBriefingText(result.briefing_text);
    setBriefingGeneratedAt(result.last_run_at);
  };

  if (notFound) {
    return (
      <div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700">
          <ArrowLeft className="h-4 w-4" /> Back to overview
        </Link>
        <p className="mt-6 text-sm text-slate-500">No property found for "{slug}".</p>
      </div>
    );
  }

  if (!property) return <p className="text-sm text-slate-500">Loading…</p>;

  const delta = formatDelta(weekly?.delta ?? null);

  return (
    <>
      <Link to="/" className="inline-flex items-center gap-1.5 text-sm font-medium text-brand-600 hover:text-brand-700">
        <ArrowLeft className="h-4 w-4" /> Back to overview
      </Link>

      <Card className="mt-4 overflow-hidden">
        <PropertyThumbnail
          src={property.thumbnail_url}
          alt={property.name}
          accentBg="bg-brand-50"
          accentIcon="text-brand-600"
          className="h-40 w-full rounded-none sm:h-48"
          iconClassName="h-12 w-12"
        />
        <div className="flex flex-wrap items-start justify-between gap-4 p-5">
          <div>
            <h1 className="text-xl font-semibold text-slate-900">{property.name}</h1>
            <p className="mt-1 text-sm text-slate-500">{property.city}</p>
          </div>
          <div className="flex items-start gap-2">
            <a
              href={property.booking_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-slate-700"
            >
              View on Booking.com <ExternalLink className="h-3.5 w-3.5" />
            </a>
            <ScrapeButton scrapeEnabled={scrapeEnabled} propertyId={property.id} />
            <AiInsightsButton llmEnabled={llmEnabled} propertyId={property.id} onClassified={handleClassified} />
          </div>
        </div>
      </Card>

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
          label="Overall avg rating"
          value={summary?.avg_rating?.toFixed(1) ?? "—"}
          sublabel={`${summary?.review_count ?? 0} total reviews`}
          icon={MessageSquare}
          accent="#8b5cf6"
        />
        <Card className="p-5">
          <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Latest review</p>
          <p className="mt-2 text-lg font-semibold text-slate-900">{summary?.latest_review_date ?? "—"}</p>
        </Card>
      </div>

      <div className="mt-6">
        <TrendChart propertyId={property.id} title="Review trend" />
      </div>

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1 space-y-6">
          {topics && <TopicInsightsPanel items={topics.items} periodDays={topics.period_days} />}
          <AiInsightsPanel
            items={aiTopics?.items ?? null}
            periodDays={aiTopics?.period_days ?? 30}
            briefingText={briefingText}
            briefingGeneratedAt={briefingGeneratedAt}
          />
        </div>

        <div className="lg:col-span-2">
          <h2 className="text-sm font-semibold text-slate-700">Review feed</h2>
          <div className="mt-3 mb-4">
            <FilterBar
              dateFrom={dateFrom}
              dateTo={dateTo}
              topic={topicFilter}
              onDateFromChange={setDateFrom}
              onDateToChange={setDateTo}
              onTopicChange={setTopicFilter}
            />
          </div>
          <ReviewFeed propertyId={property.id} dateFrom={dateFrom} dateTo={dateTo} topic={topicFilter} />
        </div>
      </div>
    </>
  );
}
