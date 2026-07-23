type Tone = "ok" | "error" | "neutral";

const TONE_STYLES: Record<Tone, string> = {
  ok: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  error: "bg-red-50 text-red-700 ring-red-600/20",
  neutral: "bg-slate-100 text-slate-600 ring-slate-500/20",
};

const DOT_STYLES: Record<Tone, string> = {
  ok: "bg-emerald-500",
  error: "bg-red-500",
  neutral: "bg-slate-400",
};

interface StatusPillProps {
  label: string;
  tone: Tone;
}

export function StatusPill({ label, tone }: StatusPillProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${TONE_STYLES[tone]}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${DOT_STYLES[tone]}`} />
      {label}
    </span>
  );
}
