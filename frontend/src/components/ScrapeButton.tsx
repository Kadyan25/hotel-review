import { useEffect, useRef, useState } from "react";
import { RefreshCw, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import {
  fetchPropertyScrapeStatus,
  fetchScrapeAllStatus,
  triggerPropertyScrape,
  triggerScrapeAll,
} from "../api/dashboard";

interface ScrapeButtonProps {
  scrapeEnabled: boolean;
  propertyId?: number; // omit for "scrape all properties"
}

const POLL_INTERVAL_MS = 5000;

export function ScrapeButton({ scrapeEnabled, propertyId }: ScrapeButtonProps) {
  const [running, setRunning] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [isError, setIsError] = useState(false);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  const startPolling = () => {
    pollRef.current = window.setInterval(async () => {
      try {
        if (propertyId) {
          const status = await fetchPropertyScrapeStatus(propertyId);
          if (status.status !== "running") {
            window.clearInterval(pollRef.current!);
            setRunning(false);
            setIsError(status.status === "failed");
            setMessage(
              status.status === "success"
                ? `Done — ${status.reviews_new ?? 0} new review(s).`
                : status.status === "failed"
                  ? `Scrape failed: ${status.error ?? "unknown error"}`
                  : "No scrape has run yet."
            );
          }
        } else {
          const status = await fetchScrapeAllStatus();
          if (!status.running) {
            window.clearInterval(pollRef.current!);
            setRunning(false);
            setMessage("Done — all properties refreshed.");
          }
        }
      } catch (err) {
        window.clearInterval(pollRef.current!);
        setRunning(false);
        setIsError(true);
        setMessage(err instanceof Error ? err.message : "Status check failed");
      }
    }, POLL_INTERVAL_MS);
  };

  const handleClick = async () => {
    setMessage(null);
    setIsError(false);
    try {
      if (propertyId) {
        await triggerPropertyScrape(propertyId);
      } else {
        await triggerScrapeAll();
      }
      setRunning(true);
      startPolling();
    } catch (err) {
      setIsError(true);
      setMessage(err instanceof Error ? err.message : "Could not start scrape");
    }
  };

  return (
    <div className="flex flex-col items-end gap-1.5">
      <Button
        variant="secondary"
        onClick={handleClick}
        disabled={!scrapeEnabled || running}
        title={
          scrapeEnabled
            ? propertyId
              ? "Scrape new reviews for this property now"
              : "Scrape new reviews for all properties now"
            : "Manual scrape trigger is disabled on this deployment -- see README"
        }
      >
        {running ? <Loader2 className="animate-spin" /> : <RefreshCw />}
        {running ? "Scraping…" : propertyId ? "Refresh reviews" : "Refresh all"}
      </Button>
      {message && (
        <p className={`max-w-xs text-right text-xs ${isError ? "text-red-600" : "text-slate-500"}`}>{message}</p>
      )}
    </div>
  );
}
