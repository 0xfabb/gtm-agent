import { Check, ListFilter, Search, Trophy } from "lucide-react";
import { cn } from "@/lib/utils";
import type { ResearchStatus } from "@/lib/useResearchStream";

const STEPS: { key: ResearchStatus; label: string; icon: typeof Search }[] = [
  { key: "structuring", label: "Structure", icon: ListFilter },
  { key: "researching", label: "Research", icon: Search },
  { key: "ranking", label: "Rank", icon: Trophy },
  { key: "done", label: "Done", icon: Check },
];

const ORDER: ResearchStatus[] = ["structuring", "researching", "ranking", "done"];

export function PipelineStepper({ status }: { status: ResearchStatus }) {
  const activeIndex = ORDER.indexOf(status);

  return (
    <div className="flex items-center">
      {STEPS.map((step, i) => {
        const isComplete = activeIndex > i;
        const isActive = activeIndex === i;
        const Icon = step.icon;

        return (
          <div key={step.key} className="flex flex-1 items-center last:flex-none">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={cn(
                  "flex size-8 shrink-0 items-center justify-center rounded-full border transition-colors duration-300",
                  isComplete && "border-primary bg-primary text-primary-foreground",
                  isActive && "border-primary text-primary ring-4 ring-primary/15 animate-pulse",
                  !isComplete && !isActive && "border-border text-muted-foreground"
                )}
              >
                <Icon className="size-3.5" />
              </div>
              <span
                className={cn(
                  "text-[11px] font-medium tracking-wide uppercase",
                  isActive || isComplete ? "text-foreground" : "text-muted-foreground"
                )}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={cn(
                  "mx-2 mb-5 h-px flex-1 transition-colors duration-500",
                  isComplete ? "bg-primary" : "bg-border"
                )}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
