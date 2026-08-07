"use client";

import { useState } from "react";
import { ChevronRight, Search, SearchCheck } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { AgentStep } from "@/lib/types";

function AgentThread({
  agent,
  steps,
  live,
}: {
  agent: string;
  steps: AgentStep[];
  live: boolean;
}) {
  const [open, setOpen] = useState(true);
  const found = steps.filter((s) => s.action === "found").length;
  const searches = steps.filter((s) => s.action === "searching").length;

  return (
    <div className="overflow-hidden rounded-lg border border-border/60 bg-card/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left transition-colors hover:bg-white/2"
      >
        <span className="flex items-center gap-2">
          <ChevronRight
            className={cn(
              "size-3.5 shrink-0 text-muted-foreground transition-transform duration-200",
              open && "rotate-90"
            )}
          />
          <span
            className={cn(
              "size-1.5 shrink-0 rounded-full",
              live ? "status-live bg-primary" : "bg-muted-foreground/40"
            )}
          />
          <span className="font-mono text-sm">{agent}</span>
        </span>
        <span className="tabular font-mono text-[11px] text-muted-foreground">
          {searches}s · {found} seen
        </span>
      </button>
      {open && (
        <ol className="max-h-64 space-y-1.5 overflow-y-auto border-t border-border/60 px-3 py-2.5 font-mono text-[11px]">
          {steps.map((step, i) => (
            <li key={i} className="trace-step flex items-start gap-1.5 text-muted-foreground">
              {step.action === "searching" ? (
                <>
                  <Search className="mt-0.5 size-3 shrink-0 text-primary" />
                  <span>{step.query}</span>
                </>
              ) : (
                <>
                  <SearchCheck className="mt-0.5 size-3 shrink-0 text-primary/60" />
                  <Tooltip>
                    <TooltipTrigger
                      render={
                        <a
                          href={step.result?.url}
                          target="_blank"
                          rel="noreferrer"
                          className="truncate text-foreground/80 hover:text-primary"
                        />
                      }
                    >
                      {step.result?.title || step.result?.url}
                    </TooltipTrigger>
                    <TooltipContent>{step.result?.url}</TooltipContent>
                  </Tooltip>
                </>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}

export function ResearchTrace({
  trace,
  live,
}: {
  trace: Record<string, AgentStep[]>;
  live: boolean;
}) {
  const [override, setOverride] = useState<boolean | null>(null);
  const expanded = override ?? live;
  const agents = Object.keys(trace);

  if (agents.length === 0) return null;

  const allSteps = agents.flatMap((a) => trace[a]);
  const searches = allSteps.filter((s) => s.action === "searching").length;
  const seen = allSteps.filter((s) => s.action === "found").length;

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setOverride(true)}
        className="flex w-full items-center gap-2 rounded-lg border border-border/60 bg-card/30 px-3 py-2 text-left transition-colors hover:bg-white/2"
      >
        <ChevronRight className="size-3.5 shrink-0 text-muted-foreground" />
        <span className="tabular font-mono text-[11px] text-muted-foreground">
          {agents.length} agents · {searches} searches · {seen} pages seen
        </span>
      </button>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold tracking-wide text-primary uppercase">
          Research trace
        </p>
        {!live && (
          <button
            type="button"
            onClick={() => setOverride(false)}
            className="text-[11px] text-muted-foreground hover:text-foreground"
          >
            collapse
          </button>
        )}
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {agents.map((agent) => (
          <AgentThread key={agent} agent={agent} steps={trace[agent]} live={live} />
        ))}
      </div>
    </div>
  );
}
