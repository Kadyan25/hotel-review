import { TOPICS } from "../constants/topics";
import { DatePicker } from "./ui/date-picker";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";

interface FilterBarProps {
  dateFrom: string;
  dateTo: string;
  topic: string;
  onDateFromChange: (value: string) => void;
  onDateToChange: (value: string) => void;
  onTopicChange: (value: string) => void;
}

export function FilterBar({
  dateFrom,
  dateTo,
  topic,
  onDateFromChange,
  onDateToChange,
  onTopicChange,
}: FilterBarProps) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-xs font-medium text-slate-500">From</span>
        <DatePicker value={dateFrom} onChange={onDateFromChange} />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-xs font-medium text-slate-500">To</span>
        <DatePicker value={dateTo} onChange={onDateToChange} />
      </label>
      <label className="flex flex-col gap-1 text-sm">
        <span className="text-xs font-medium text-slate-500">Topic</span>
        <Select value={topic || "all"} onValueChange={(v) => onTopicChange(v === "all" ? "" : v)}>
          <SelectTrigger className="w-[10.5rem]">
            <SelectValue placeholder="All topics" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All topics</SelectItem>
            {TOPICS.map((t) => (
              <SelectItem key={t} value={t}>
                {t.replace(/_/g, " ")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </label>
    </div>
  );
}
