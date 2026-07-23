export interface HealthResponse {
  status: string;
  database: string;
  llm_classification_enabled: boolean;
  apify_fallback_configured: boolean;
  scrape_endpoint_enabled: boolean;
}
