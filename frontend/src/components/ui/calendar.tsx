import { DayPicker } from "react-day-picker";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import "react-day-picker/style.css";

export type CalendarProps = React.ComponentProps<typeof DayPicker>;

export function Calendar({ className, ...props }: CalendarProps) {
  return (
    <DayPicker
      className={cn("p-1", className)}
      classNames={{
        months: "flex flex-col",
        month: "space-y-3",
        month_caption: "flex justify-center pt-1 text-sm font-medium text-slate-900",
        nav: "flex items-center justify-between absolute inset-x-1 top-1",
        button_previous:
          "h-7 w-7 rounded-md flex items-center justify-center text-slate-500 hover:bg-slate-100",
        button_next: "h-7 w-7 rounded-md flex items-center justify-center text-slate-500 hover:bg-slate-100",
        month_grid: "w-full border-collapse",
        weekdays: "flex",
        weekday: "text-slate-400 w-8 font-normal text-xs",
        week: "flex w-full mt-1",
        day: "h-8 w-8 text-center text-sm p-0 relative",
        day_button: "h-8 w-8 rounded-md text-slate-700 hover:bg-brand-50 hover:text-brand-700",
        selected: "!bg-brand-600 !text-white rounded-md",
        today: "font-semibold text-brand-600",
        outside: "text-slate-300",
        disabled: "text-slate-300",
      }}
      components={{
        Chevron: ({ orientation }) =>
          orientation === "left" ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />,
      }}
      {...props}
    />
  );
}
