import { apiGet, apiPost } from "./client";
import type {
  ClassifyLLMResponse,
  PropertyItem,
  PropertySummary,
  ReviewListResponse,
  TopicInsightsResponse,
  WeeklySummary,
} from "../types/dashboard";

export function fetchProperties(): Promise<PropertyItem[]> {
  return apiGet<PropertyItem[]>("/api/properties");
}

export function fetchPropertySummary(propertyId: number): Promise<PropertySummary> {
  return apiGet<PropertySummary>(`/api/properties/${propertyId}/summary`);
}

export interface ReviewFilters {
  propertyId?: number;
  from?: string;
  to?: string;
  topic?: string;
  sentiment?: string;
  limit?: number;
  offset?: number;
}

export function fetchReviews(filters: ReviewFilters = {}): Promise<ReviewListResponse> {
  const params = new URLSearchParams();
  if (filters.propertyId) params.set("property_id", String(filters.propertyId));
  if (filters.from) params.set("from", filters.from);
  if (filters.to) params.set("to", filters.to);
  if (filters.topic) params.set("topic", filters.topic);
  if (filters.sentiment) params.set("sentiment", filters.sentiment);
  params.set("limit", String(filters.limit ?? 20));
  params.set("offset", String(filters.offset ?? 0));
  return apiGet<ReviewListResponse>(`/api/reviews?${params.toString()}`);
}

export function fetchWeeklySummary(propertyId?: number): Promise<WeeklySummary> {
  const params = propertyId ? `?property_id=${propertyId}` : "";
  return apiGet<WeeklySummary>(`/api/insights/weekly-summary${params}`);
}

export function fetchTopicInsights(propertyId?: number): Promise<TopicInsightsResponse> {
  const params = propertyId ? `?property_id=${propertyId}` : "";
  return apiGet<TopicInsightsResponse>(`/api/insights/topics${params}`);
}

export function classifyWithLLM(propertyId?: number): Promise<ClassifyLLMResponse> {
  const params = propertyId ? `?property_id=${propertyId}` : "";
  return apiPost<ClassifyLLMResponse>(`/api/insights/classify-llm${params}`);
}

export interface ScrapeStatus {
  status: "never_run" | "running" | "success" | "failed";
  started_at?: string;
  finished_at?: string | null;
  reviews_new?: number;
  error?: string | null;
}

export function triggerPropertyScrape(propertyId: number): Promise<{ status: string; property: string }> {
  return apiPost(`/api/properties/${propertyId}/scrape`);
}

export function fetchPropertyScrapeStatus(propertyId: number): Promise<ScrapeStatus> {
  return apiGet<ScrapeStatus>(`/api/properties/${propertyId}/scrape-status`);
}

export function triggerScrapeAll(): Promise<{ status: string; properties: string[] }> {
  return apiPost(`/api/scrape-all`);
}

export function fetchScrapeAllStatus(): Promise<{ running: boolean; running_property_ids: number[] }> {
  return apiGet(`/api/scrape-all-status`);
}
