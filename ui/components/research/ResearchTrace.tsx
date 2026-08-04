"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronRight, Search, SearchCheck } from "lucide-react";

import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { AgentStep } from "@/lib/types";

function AgentThread({ agent, steps, live }: { agent: string; steps: AgentStep[]; live: boolean }) {
  const [open, setOpen] = useState(true);
  const found = steps.filter((s) => s.action === "found").length;
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [steps.length]);

  return (
    <Collapsible
      open={open}
      onOpenChange={setOpen}
      className="overflow-hidden rounded-lg border border-border/60 bg-card/30"
    >
      <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 px-3 py-2.5 text-left transition-colors hover:bg-card/60">
        <span className="flex items-center gap-2.5">
          <ChevronRight
            className={`size-3.5 shrink-0 text-muted-foreground transition-transform duration-200 ${open ? "rotate-90" : ""}`}
          />
          <Avatar size="sm" className="ring-1 ring-primary/30">
            <AvatarFallback className="bg-primary/10 text-[10px] font-semibold text-primary uppercase">
              {agent.slice(0, 2)}
            </AvatarFallback>
          </Avatar>
          <span className="font-mono text-sm">{agent}</span>
          {live && (
            <span className="relative flex size-1.5">
              <span className="absolute inline-flex size-full animate-ping rounded-full bg-primary opacity-75" />
              <span className="relative inline-flex size-1.5 rounded-full bg-primary" />
            </span>
          )}
        </span>
        <Badge variant="outline" className="font-mono">
          {found} found
        </Badge>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ScrollArea className="max-h-64 border-t border-border/60">
          <ol className="space-y-1.5 px-3 py-2.5 font-mono text-xs">
            {steps.map((step, i) => (
              <li
                key={i}
                className="animate-in fade-in slide-in-from-bottom-1 flex items-start gap-1.5 text-muted-foreground duration-300"
              >
                {step.action === "searching" ? (
                  <>
                    <Search className="mt-0.5 size-3 shrink-0 text-primary" />
                    <span>&quot;{step.query}&quot;</span>
                  </>
                ) : (
                  <>
                    <SearchCheck className="mt-0.5 size-3 shrink-0 text-primary" />
                    <Tooltip>
                      <TooltipTrigger
                        render={
                          <a
                            href={step.result?.url}
                            target="_blank"
                            rel="noreferrer"
                            className="truncate text-foreground underline decoration-border underline-offset-2 hover:decoration-foreground"
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
            <div ref={bottomRef} />
          </ol>
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function ResearchTrace({
  trace,
  live,
}: {
  trace: Record<string, AgentStep[]>;
  live: boolean;
}) {
  const agents = Object.keys(trace);
  if (agents.length === 0) return null;

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 duration-500">
      <p className="text-xs font-semibold tracking-wide text-primary uppercase">Research trace</p>
      <div className="grid gap-2.5 sm:grid-cols-2">
        {agents.map((agent) => (
          <AgentThread key={agent} agent={agent} steps={trace[agent]} live={live} />
        ))}
      </div>
    </div>
  );
}
