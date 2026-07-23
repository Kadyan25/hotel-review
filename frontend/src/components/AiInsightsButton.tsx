import { useState } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { classifyWithLLM } from "../api/dashboard";

interface AiInsightsButtonProps {
  llmEnabled: boolean;
  propertyId?: number; // omit for "classify across all properties"
}

export function AiInsightsButton({ llmEnabled, propertyId }: AiInsightsButtonProps) {
  const [status, setStatus] = useState<"idle" | "running" | "done" | "error">("idle");
  const [message, setMessage] = useState<string | null>(null);

  const handleClick = async () => {
    setStatus("running");
    setMessage(null);
    try {
      const result = await classifyWithLLM(propertyId);
      setMessage(result.message);
      setStatus("done");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Request failed");
      setStatus("error");
    }
  };

  return (
    <div className="flex flex-col items-end gap-1.5">
      <Button
        onClick={handleClick}
        disabled={!llmEnabled || status === "running"}
        title={llmEnabled ? "Classify ambiguous reviews with Claude Haiku" : "AI classification is not configured"}
      >
        {status === "running" ? <Loader2 className="animate-spin" /> : <Sparkles />}
        {status === "running" ? "Classifying…" : "Get AI Insights"}
      </Button>
      {message && (
        <p className={`max-w-xs text-right text-xs ${status === "error" ? "text-red-600" : "text-slate-500"}`}>
          {message}
        </p>
      )}
    </div>
  );
}
