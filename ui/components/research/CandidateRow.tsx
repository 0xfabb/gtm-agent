"use client";

import { useState, useSyncExternalStore } from "react";
import {
  BadgeCheck,
  ChevronDown,
  ExternalLink,
  Heart,
  ScanSearch,
  ShieldQuestion,
  Sparkle,
  ThumbsDown,
  Users,
} from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  candidateKey,
  getFeedbackSnapshot,
  getServerFeedbackSnapshot,
  subscribeFeedback,
  toggleDown,
} from "@/lib/feedback";
import type { RankedCandidate, StatSource } from "@/lib/types";

const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  youtube: "YouTube",
  instagram: "Instagram",
};

const STAT_SOURCE_LABEL: Record<StatSource, string> = {
  verified: "Verified via the platform API",
  parsed: "Read from the creator's own profile page",
  model: "Claimed by the research agent, unconfirmed",
  none: "No follower count found",
};

function SourceMark({ source }: { source: StatSource }) {
  if (source === "none") return null;
  const Icon = source === "verified" ? BadgeCheck : source === "parsed" ? ScanSearch : ShieldQuestion;
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            className={cn(
              "inline-flex items-center gap-1",
              source === "verified" ? "text-primary" : "text-muted-foreground"
            )}
          />
        }
      >
        <Icon className="size-3" />
        {source}
      </TooltipTrigger>
      <TooltipContent>{STAT_SOURCE_LABEL[source]}</TooltipContent>
    </Tooltip>
  );
}

function initials(handle: string): string {
  return handle.replace(/[^a-zA-Z0-9]/g, "").slice(0, 2).toUpperCase() || "??";
}

export function CandidateRow({
  candidate,
  rank,
}: {
  candidate: RankedCandidate;
  rank: number;
}) {
  const [open, setOpen] = useState(false);
  const feedback = useSyncExternalStore(
    subscribeFeedback,
    getFeedbackSnapshot,
    getServerFeedbackSnapshot
  );
  const rejected = Boolean(feedback[candidateKey(candidate.platform, candidate.handle)]);

  return (
    <div
      className={cn(
        "group/row border-b border-border/60 px-3 py-3 transition-colors last:border-b-0 hover:bg-white/2",
        rejected && "opacity-40"
      )}
    >
      <div className="flex items-start gap-3">
        <span className="mt-0.5 w-4 shrink-0 text-right font-mono text-[11px] text-muted-foreground tabular">
          {rank}
        </span>

        <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
          {initials(candidate.handle)}
        </span>

        <div className="min-w-0 flex-1 space-y-1">
          <div className="flex items-center gap-2">
            <a
              href={candidate.url}
              target="_blank"
              rel="noreferrer"
              className="truncate text-sm font-medium hover:text-primary hover:underline"
            >
              {candidate.handle}
            </a>
            <ExternalLink className="size-3 shrink-0 text-muted-foreground opacity-0 transition-opacity group-hover/row:opacity-100" />
          </div>

          <div className="stat-row flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
            <span className="rounded bg-white/6 px-1.5 py-0.5">
              {PLATFORM_LABEL[candidate.platform] ?? candidate.platform}
            </span>
            {candidate.follower_count != null && (
              <span className="inline-flex items-center gap-1">
                <Users className="size-3" />
                {candidate.follower_count.toLocaleString()}
              </span>
            )}
            {candidate.likes_per_follower != null && (
              <Tooltip>
                <TooltipTrigger render={<span className="inline-flex items-center gap-1" />}>
                  <Heart className="size-3" />
                  {candidate.likes_per_follower}×
                </TooltipTrigger>
                <TooltipContent>
                  Lifetime likes ÷ followers — not a per-post engagement rate. Band:{" "}
                  {candidate.engagement_band}.
                </TooltipContent>
              </Tooltip>
            )}
            {candidate.similarity != null && (
              <Tooltip>
                <TooltipTrigger render={<span className="inline-flex items-center gap-1" />}>
                  <Sparkle className="size-3" />
                  {Math.round(candidate.similarity * 100)}%
                </TooltipTrigger>
                <TooltipContent>Similarity to the reference accounts.</TooltipContent>
              </Tooltip>
            )}
            <SourceMark source={candidate.stat_source} />
          </div>

          <p className="text-[13px] leading-relaxed text-foreground/80">{candidate.rationale}</p>

          {candidate.source_evidence && (
            <div>
              <button
                type="button"
                onClick={() => setOpen((v) => !v)}
                className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground"
              >
                <ChevronDown className={cn("size-3 transition-transform", open && "rotate-180")} />
                evidence
              </button>
              {open && (
                <p className="mt-1.5 rounded border border-border/60 bg-background/60 p-2 font-mono text-[11px] leading-relaxed text-muted-foreground">
                  {candidate.source_evidence}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <div className="flex items-center gap-1.5">
            <div className="h-1 w-8 overflow-hidden rounded-full bg-white/8">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${Math.min(100, candidate.score * 10)}%` }}
              />
            </div>
            <span className="w-8 text-right text-xs font-semibold tabular">
              {candidate.score}/10
            </span>
          </div>
          <Tooltip>
            <TooltipTrigger
              render={
                <button
                  type="button"
                  onClick={() => toggleDown(candidate.platform, candidate.handle)}
                  className={cn(
                    "rounded p-1 transition-colors",
                    rejected
                      ? "text-destructive"
                      : "text-muted-foreground opacity-0 hover:text-destructive group-hover/row:opacity-100"
                  )}
                />
              }
            >
              <ThumbsDown className="size-3.5" />
            </TooltipTrigger>
            <TooltipContent>
              {rejected ? "Marked as a bad match" : "Not a good match"}
            </TooltipContent>
          </Tooltip>
        </div>
      </div>
    </div>
  );
}
