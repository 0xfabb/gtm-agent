"use client";

import { useEffect, useState } from "react";
import { Check, ChevronRight, Search, X } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { AgentStatus, AgentStep, CostSummary } from "@/lib/types";

const STATUS_DOT: Record<AgentStatus, string> = {
  active: "bg-blue-400",
  done: "bg-primary",
  failed: "bg-destructive",
  pending: "bg-muted-foreground/30",
};

function formatElapsed(ms: number): string {
  const totalSeconds = Math.max(0, Math.round(ms / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${minutes}:${String(seconds).padStart(2, "0")}`;
}

function StepGlyph({ action }: { action: AgentStep["action"] }) {
  if (action === "skipped") return <X className="size-2.5" />;
  if (action === "found") return <Check className="size-2.5" />;
  return <Search className="size-2.5" />;
}

function stepText(step: AgentStep): string {
  if (step.action === "searching" || step.action === "verifying") return step.query ?? "";
  if (step.action === "skipped") return step.result?.note ?? "skipped";
  return step.result?.title || step.result?.url || "";
}

function AgentThread({
  agent,
  steps,
  status,
}: {
  agent: string;
  steps: AgentStep[];
  status: AgentStatus;
}) {
  const [open, setOpen] = useState(true);
  const found = steps.filter((s) => s.action === "found").length;
  const lastStep = steps[steps.length - 1];

  return (
    <div className="flex flex-col gap-1">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex items-center gap-2 text-left"
      >
        <span
          className={cn(
            "size-1.75 shrink-0 rounded-full",
            STATUS_DOT[status],
            status === "active" && "status-live"
          )}
        />
        <span className="text-[13px] font-semibold text-foreground/90">{agent}</span>
        <ChevronRight
          className={cn(
            "size-3 shrink-0 text-muted-foreground/50 transition-transform",
            open && "rotate-90"
          )}
        />
        <span className="flex-1" />
        <span className="tabular font-mono text-[11px] text-muted-foreground/60">
          {status === "pending" ? "queued" : status === "active" ? `${found} found` : `${steps.length} steps`}
        </span>
      </button>

      {open && steps.length > 0 && (
        <div className="ml-0.75 flex max-h-56 flex-col overflow-y-auto border-l border-border/60 pl-3">
          {steps.map((step, i) => {
            const isLast = i === steps.length - 1;
            const emphasize = isLast && status === "active";
            const isError = step.action === "skipped";
            const url = step.action === "found" ? step.result?.url : undefined;

            const row = (
              <div
                key={i}
                className={cn(
                  "trace-step flex items-baseline gap-2 rounded px-1.5 py-0.75",
                  emphasize && "bg-white/2"
                )}
              >
                <span
                  className={cn(
                    "flex size-3 shrink-0 items-center justify-center",
                    isError ? "text-amber-500" : "text-primary"
                  )}
                >
                  <StepGlyph action={step.action} />
                </span>
                <span
                  className={cn(
                    "truncate font-mono text-[12px] leading-relaxed",
                    isError
                      ? "text-amber-500/80"
                      : emphasize
                        ? "text-foreground/90"
                        : "text-muted-foreground"
                  )}
                >
                  {stepText(step)}
                </span>
              </div>
            );

            if (!url) return row;
            return (
              <Tooltip key={i}>
                <TooltipTrigger render={<div />}>{row}</TooltipTrigger>
                <TooltipContent>{url}</TooltipContent>
              </Tooltip>
            );
          })}
        </div>
      )}
      {!open && lastStep && (
        <p className="ml-4.75 truncate font-mono text-[11px] text-muted-foreground/50">
          {stepText(lastStep)}
        </p>
      )}
    </div>
  );
}

function agentStatus(
  steps: AgentStep[],
  live: boolean,
  hasError: boolean
): AgentStatus {
  if (hasError) return "failed";
  if (steps.length === 0) return "pending";
  return live ? "active" : "done";
}

export function ResearchTrace({
  trace,
  live,
  errors,
  startedAt,
  finishedAt,
  cost,
}: {
  trace: Record<string, AgentStep[]>;
  live: boolean;
  errors: { agent: string; message: string }[];
  startedAt: number | null;
  finishedAt: number | null;
  cost: CostSummary | null;
}) {
  const [override, setOverride] = useState<boolean | null>(null);
  const expanded = override ?? live;
  const agents = Object.keys(trace);

  const [now, setNow] = useState<number | null>(null);
  useEffect(() => {
    if (!live) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [live]);

  if (agents.length === 0) return null;

  const allSteps = agents.flatMap((a) => trace[a]);
  const searches = allSteps.filter((s) => s.action === "searching").length;
  const errorAgents = new Set(errors.map((e) => e.agent));
  const clock = live ? now : finishedAt;
  const elapsed = startedAt != null && clock != null ? formatElapsed(clock - startedAt) : null;

  if (!expanded) {
    return (
      <button
        type="button"
        onClick={() => setOverride(true)}
        className="flex w-full items-center gap-2.5 rounded-lg border border-border/60 bg-card/40 px-3.5 py-2.5 text-left transition-colors hover:bg-white/2"
      >
        <Check className="size-3.5 shrink-0 text-primary" />
        <span className="font-mono text-[12.5px] text-foreground/80">
          Research trace · {agents.length} agents · {searches} searches
          {elapsed && ` · ${elapsed}`}
        </span>
        <span className="flex-1" />
        {cost && (
          <span className="tabular font-mono text-[11px] text-muted-foreground/60">
            ${cost.usd.toFixed(4)}
          </span>
        )}
        <ChevronRight className="size-3.5 shrink-0 text-muted-foreground/50" />
      </button>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-border/60 bg-card/40 px-4 py-3.5">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
          Research trace{live ? " — live" : ""}
        </span>
        <span className="flex items-center gap-2">
          {elapsed && (
            <span className="tabular font-mono text-[11px] text-muted-foreground/50">
              {elapsed} elapsed
            </span>
          )}
          {!live && (
            <button
              type="button"
              onClick={() => setOverride(false)}
              className="text-[11px] text-muted-foreground hover:text-foreground"
            >
              collapse
            </button>
          )}
        </span>
      </div>
      <div className="flex flex-col gap-3">
        {agents.map((agent) => (
          <AgentThread
            key={agent}
            agent={agent}
            steps={trace[agent]}
            status={agentStatus(trace[agent], live, errorAgents.has(agent))}
          />
        ))}
      </div>
    </div>
  );
}
