import { useEffect, useState } from "react";
import { Sparkles, Loader2, CheckCircle2 } from "lucide-react";
import { Button } from "./ui/button";
import { classifyWithLLM, fetchLlmStatus } from "../api/dashboard";
import type { ClassifyLLMResponse } from "../types/dashboard";

interface AiInsightsButtonProps {
  llmEnabled: boolean;
  propertyId?: number; // omit for "classify across all properties"
  onClassified?: (result: ClassifyLLMResponse) => void; // parent refetches topics + briefing
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function AiInsightsButton({ llmEnabled, propertyId, onClassified }: AiInsightsButtonProps) {
  const [status, setStatus] = useState<"idle" | "running" | "error">("idle");
  const [error, setError] = useState<string | null>(null);
  const [lastRunAt, setLastRunAt] = useState<string | null>(null);
  const [canRunToday, setCanRunToday] = useState(true);

  useEffect(() => {
    if (!llmEnabled) return;
    fetchLlmStatus(propertyId).then((s) => {
      setLastRunAt(s.last_run_at);
      setCanRunToday(s.can_run_today);
    });
  }, [llmEnabled, propertyId]);

  const handleClick = async () => {
    setStatus("running");
    setError(null);
    try {
      const result = await classifyWithLLM(propertyId);
      setLastRunAt(result.last_run_at);
      setCanRunToday(false); // either we just used today's run, or the API says one already happened
      setStatus("idle");
      onClassified?.(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
      setStatus("error");
    }
  };

  const disabled = !llmEnabled || status === "running" || !canRunToday;
  const title = !llmEnabled
    ? "AI classification is not configured"
    : !canRunToday
      ? "Already generated today — reviews are re-classified once per day"
      : "Classify ambiguous reviews with AI";

  return (
    <div className="flex flex-col items-end gap-1.5">
      <Button onClick={handleClick} disabled={disabled} title={title}>
        {status === "running" ? (
          <Loader2 className="animate-spin" />
        ) : !canRunToday ? (
          <CheckCircle2 />
        ) : (
          <Sparkles />
        )}
        {status === "running" ? "Classifying…" : !canRunToday ? "Generated today" : "Get AI Insights"}
      </Button>
      {error && <p className="max-w-xs text-right text-xs text-red-600">{error}</p>}
      {!error && lastRunAt && (
        <p className="text-right text-xs text-slate-400">Last generated {formatTime(lastRunAt)}</p>
      )}
    </div>
  );
}
