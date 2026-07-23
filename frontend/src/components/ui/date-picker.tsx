import { useState } from "react";
import { format, parseISO } from "date-fns";
import { CalendarIcon } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "./popover";
import { Calendar } from "./calendar";
import { cn } from "@/lib/utils";

interface DatePickerProps {
  value: string; // YYYY-MM-DD or ""
  onChange: (value: string) => void;
  placeholder?: string;
}

export function DatePicker({ value, onChange, placeholder = "Any date" }: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const selectedDate = value ? parseISO(value) : undefined;

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          type="button"
          className={cn(
            "flex h-9 w-[10.5rem] items-center gap-2 rounded-lg border border-slate-300 bg-white px-3 text-sm shadow-sm transition-colors hover:border-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-400",
            !value && "text-slate-400"
          )}
        >
          <CalendarIcon className="h-4 w-4 text-slate-400" />
          {value ? format(selectedDate!, "d MMM yyyy") : placeholder}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-auto">
        <Calendar
          mode="single"
          selected={selectedDate}
          onSelect={(date) => {
            onChange(date ? format(date, "yyyy-MM-dd") : "");
            setOpen(false);
          }}
        />
        {value && (
          <button
            type="button"
            onClick={() => {
              onChange("");
              setOpen(false);
            }}
            className="mt-1 w-full rounded-md py-1.5 text-center text-xs font-medium text-slate-500 hover:bg-slate-100"
          >
            Clear
          </button>
        )}
      </PopoverContent>
    </Popover>
  );
}
