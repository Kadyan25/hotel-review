const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function extractErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body?.detail === "string") return body.detail;
  } catch {
    // response wasn't JSON -- fall through to the generic message
  }
  return `Request failed (${response.status})`;
}

export async function apiGet<T>(path: string): Promise<T> {
  // The API sends no Cache-Control header, so browsers/edge proxies are free
  // to reuse a cached response for an identical URL -- fatal for anything
  // polled (scrape-status, llm-status): every poll hits the exact same URL,
  // so a single cached hit would freeze the displayed state forever even
  // though the server has long since moved on. Force a real network fetch.
  const response = await fetch(`${API_BASE_URL}${path}`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }
  return response.json() as Promise<T>;
}

export async function apiPost<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "POST", cache: "no-store" });
  if (!response.ok) {
    throw new Error(await extractErrorMessage(response));
  }
  return response.json() as Promise<T>;
}
