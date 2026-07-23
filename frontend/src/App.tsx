import { useEffect, useState } from "react";
import { fetchHealth } from "./api/health";
import type { HealthResponse } from "./types/health";
import { Card } from "./components/Card";
import { Header } from "./components/Header";
import { StatusPill } from "./components/StatusPill";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen bg-slate-50">
      <Header />

      <main className="mx-auto max-w-5xl px-6 py-10">
        <h1 className="text-xl font-semibold text-slate-900">System status</h1>
        <p className="mt-1 text-sm text-slate-500">
          Live connectivity check between the dashboard and the backend API.
        </p>

        <Card className="mt-6 max-w-md p-5">
          {error && (
            <div className="flex items-center gap-2 text-sm text-red-600">
              <StatusPill label="unreachable" tone="error" />
              <span>{error}</span>
            </div>
          )}

          {!error && !health && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <StatusPill label="checking" tone="neutral" />
              Connecting to backend…
            </div>
          )}

          {health && (
            <dl className="divide-y divide-slate-100">
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-sm text-slate-600">API</dt>
                <dd>
                  <StatusPill label={health.status} tone={health.status === "ok" ? "ok" : "error"} />
                </dd>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-sm text-slate-600">Database</dt>
                <dd>
                  <StatusPill
                    label={health.database}
                    tone={health.database === "ok" ? "ok" : "error"}
                  />
                </dd>
              </div>
              <div className="flex items-center justify-between py-2.5">
                <dt className="text-sm text-slate-600">AI classification</dt>
                <dd>
                  <StatusPill
                    label={health.llm_classification_enabled ? "enabled" : "keyword-only"}
                    tone={health.llm_classification_enabled ? "ok" : "neutral"}
                  />
                </dd>
              </div>
            </dl>
          )}
        </Card>
      </main>
    </div>
  );
}

export default App;
