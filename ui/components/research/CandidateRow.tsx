"use client";

import { useSyncExternalStore } from "react";
import { ChevronDown, ChevronUp, ThumbsDown } from "lucide-react";

import { cn } from "@/lib/utils";
import {
  candidateKey,
  getFeedbackSnapshot,
  getServerFeedbackSnapshot,
  subscribeFeedback,
  toggleDown,
} from "@/lib/feedback";
import type { RankedCandidate } from "@/lib/types";

const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  youtube: "YouTube",
  instagram: "Instagram",
};

const PLATFORM_DOMAIN: Record<string, string> = {
  tiktok: "tiktok.com",
  youtube: "youtube.com",
  instagram: "instagram.com",
};

function initials(handle: string): string {
  return handle.replace(/[^a-zA-Z0-9]/g, "").slice(0, 2).toUpperCase() || "??";
}

function statsLine(candidate: RankedCandidate): string {
  const parts: string[] = [];
  if (candidate.follower_count != null) {
    parts.push(`${candidate.follower_count.toLocaleString()} followers`);
  }
  if (candidate.likes_per_follower != null) {
    parts.push(`${candidate.likes_per_follower}× likes/follower`);
  }
  if (candidate.stat_source !== "verified") parts.push("cached");
  return parts.join(" · ");
}

function sourcesFor(candidate: RankedCandidate): string[] {
  const list = [PLATFORM_DOMAIN[candidate.platform] ?? candidate.platform];
  list.push(candidate.stat_source === "verified" ? "platform API" : "exa.ai");
  return list;
}

export function CandidateRow({
  candidate,
  verified,
  expanded,
  onToggleExpand,
}: {
  candidate: RankedCandidate;
  verified: boolean;
  expanded: boolean;
  onToggleExpand: () => void;
}) {
  const feedback = useSyncExternalStore(
    subscribeFeedback,
    getFeedbackSnapshot,
    getServerFeedbackSnapshot
  );
  const rejected = Boolean(feedback[candidateKey(candidate.platform, candidate.handle)]);

  return (
    <div
      className={cn(
        "flex flex-col gap-2 rounded-lg border bg-[#1c1c1f] p-3.5 transition-opacity",
        verified ? "border-border/60" : "border-dashed border-border",
        !verified && "opacity-90",
        rejected && "opacity-40"
      )}
    >
      <div className="flex items-center gap-2.5">
        <span className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border/60 bg-card text-xs font-semibold text-foreground/70">
          {initials(candidate.handle)}
        </span>
        <a
          href={candidate.url}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 text-[15px] font-semibold text-foreground/95 hover:text-primary hover:underline"
        >
          {candidate.handle}
        </a>
        <span className="shrink-0 rounded border border-border/60 bg-card px-1.5 py-0.5 font-mono text-[11px] font-medium tracking-wide text-foreground/60 uppercase">
          {PLATFORM_LABEL[candidate.platform] ?? candidate.platform}
        </span>
        {verified ? (
          <span
            title="Verified"
            className="flex size-4 shrink-0 items-center justify-center rounded-full bg-primary/15 text-[10px] text-primary"
          >
            ✓
          </span>
        ) : (
          <span className="shrink-0 rounded border border-border/60 px-1.5 py-0.5 font-mono text-[10.5px] text-muted-foreground">
            unverified
          </span>
        )}

        <span className="flex-1" />

        <div className="flex w-14 shrink-0 flex-col items-end gap-1">
          <span
            className={cn(
              "tabular font-mono text-[15px] font-semibold",
              verified ? "text-foreground/90" : "text-muted-foreground"
            )}
          >
            {candidate.score}
          </span>
          <div className="h-1 w-13.5 overflow-hidden rounded-full bg-white/8">
            <div
              className={cn("h-full", verified ? "bg-primary" : "bg-white/25")}
              style={{ width: `${candidate.score * 10}%` }}
            />
          </div>
        </div>

        <button
          type="button"
          onClick={() => toggleDown(candidate.platform, candidate.handle)}
          aria-label="Not a good match"
          className={cn(
            "flex size-6 shrink-0 items-center justify-center rounded-full border transition-colors",
            rejected
              ? "border-destructive/45 bg-destructive/15 text-destructive"
              : "border-border/60 text-muted-foreground hover:text-destructive"
          )}
        >
          <ThumbsDown className="size-3" />
        </button>

        <button
          type="button"
          onClick={onToggleExpand}
          aria-label={expanded ? "Collapse" : "Expand"}
          className="flex size-5 shrink-0 items-center justify-center text-muted-foreground/60 hover:text-foreground"
        >
          {expanded ? <ChevronUp className="size-3.5" /> : <ChevronDown className="size-3.5" />}
        </button>
      </div>

      <div className="flex items-baseline gap-2.5 pl-10.5">
        <span className="tabular shrink-0 font-mono text-[12.5px] text-muted-foreground">
          {statsLine(candidate)}
        </span>
        {!expanded && (
          <span className="min-w-0 flex-1 truncate text-[13px] text-foreground/60">
            {candidate.rationale}
          </span>
        )}
      </div>

      {expanded && (
        <div className="ml-10.5 flex flex-col gap-1.5 border-t border-border/40 pt-2.5">
          <p className="text-[13px] leading-relaxed text-foreground/75">{candidate.rationale}</p>
          <p className="font-mono text-[11px] text-muted-foreground/60">
            Sources: {sourcesFor(candidate).join(" · ")}
          </p>
          {candidate.source_evidence && (
            <p className="rounded border border-border/50 bg-background/60 p-2 font-mono text-[11px] leading-relaxed text-muted-foreground">
              {candidate.source_evidence}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
