import type { LucideIcon } from "lucide-react";
import { Card } from "./Card";

interface KpiCardProps {
  label: string;
  value: string;
  sublabel?: string;
  deltaLabel?: string;
  deltaTone?: "up" | "down" | "flat";
  icon: LucideIcon;
  accent: string; // hex
}

const DELTA_STYLES: Record<"up" | "down" | "flat", string> = {
  up: "text-emerald-600",
  down: "text-red-600",
  flat: "text-slate-500",
};

export function KpiCard({ label, value, sublabel, deltaLabel, deltaTone = "flat", icon: Icon, accent }: KpiCardProps) {
  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg"
          style={{ backgroundColor: `${accent}1a`, color: accent }}
        >
          <Icon className="h-4 w-4" />
        </div>
      </div>
      <p className="mt-2 text-3xl font-semibold text-slate-900">{value}</p>
      <div className="mt-1 flex items-center gap-2 text-sm">
        {sublabel && <span className="text-slate-500">{sublabel}</span>}
        {deltaLabel && <span className={`font-medium ${DELTA_STYLES[deltaTone]}`}>{deltaLabel}</span>}
      </div>
    </Card>
  );
}
