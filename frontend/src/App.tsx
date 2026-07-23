import { useEffect, useState } from "react";
import { fetchHealth } from "./api/health";
import type { HealthResponse } from "./types/health";
import "./App.css";

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchHealth()
      .then(setHealth)
      .catch((err: Error) => setError(err.message));
  }, []);

  return (
    <main className="status-page">
      <h1>Azzurro Hotels — Review Insights Dashboard</h1>
      {error && <p className="status-error">Backend unreachable: {error}</p>}
      {!error && !health && <p>Checking backend…</p>}
      {health && (
        <dl className="status-grid">
          <dt>API</dt>
          <dd>{health.status}</dd>
          <dt>Database</dt>
          <dd>{health.database}</dd>
          <dt>AI classification</dt>
          <dd>{health.llm_classification_enabled ? "enabled" : "disabled (keyword-only)"}</dd>
        </dl>
      )}
    </main>
  );
}

export default App;
