import { Link } from "react-router-dom";
import { Card } from "./Card";
import { PropertyThumbnail } from "./PropertyThumbnail";
import type { PropertySummary } from "../types/dashboard";

interface PropertyBreakdownProps {
  summaries: PropertySummary[];
}

// Rotating accent used only when a property has no thumbnail (fallback icon).
const ACCENTS = [
  { bg: "bg-brand-50", icon: "text-brand-600" },
  { bg: "bg-sky-50", icon: "text-sky-600" },
  { bg: "bg-cyan-50", icon: "text-cyan-600" },
  { bg: "bg-indigo-50", icon: "text-indigo-600" },
];

export function PropertyBreakdown({ summaries }: PropertyBreakdownProps) {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {summaries.map((s, index) => {
        const accent = ACCENTS[index % ACCENTS.length];
        return (
          <Link key={s.property.id} to={`/properties/${s.property.slug}`}>
            <Card className="overflow-hidden transition hover:border-slate-300 hover:shadow-md">
              <PropertyThumbnail
                src={s.property.thumbnail_url}
                alt={s.property.name}
                accentBg={accent.bg}
                accentIcon={accent.icon}
                className="h-28 w-full rounded-none"
                iconClassName="h-9 w-9"
              />
              <div className="p-4">
                <div className="flex items-start justify-between">
                  <p className="truncate text-sm font-medium text-slate-900">{s.property.name}</p>
                  <p className="ml-2 shrink-0 text-lg font-semibold text-slate-900">
                    {s.avg_rating !== null ? s.avg_rating.toFixed(1) : "—"}
                  </p>
                </div>
                <p className="mt-0.5 text-xs text-slate-500">{s.review_count} reviews</p>
              </div>
            </Card>
          </Link>
        );
      })}
    </div>
  );
}
