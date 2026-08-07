"use client";

import { useState } from "react";
import {
  BadgeCheck,
  ChevronDown,
  Check,
  Copy,
  ExternalLink,
  Heart,
  ScanSearch,
  ShieldQuestion,
  Sparkle,
  Users,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import type { Candidate, FilterSummary, RankedCandidate, StatSource } from "@/lib/types";

const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  youtube: "YouTube",
  instagram: "Instagram",
};

const STAT_SOURCE_LABEL: Record<StatSource, string> = {
  verified: "Verified via platform API",
  parsed: "Read from the profile page",
  model: "Claimed by the research agent, unconfirmed",
  none: "No follower count found",
};

function StatSourceBadge({ source }: { source: StatSource }) {
  if (source === "none") return null;
  const Icon = source === "verified" ? BadgeCheck : source === "parsed" ? ScanSearch : ShieldQuestion;
  return (
    <Tooltip>
      <TooltipTrigger
        render={
          <span
            className={cn(
              "inline-flex items-center gap-1 text-[11px]",
              source === "verified" && "text-primary",
              source === "parsed" && "text-muted-foreground",
              source === "model" && "text-amber-500/80"
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

function Stats({ candidate }: { candidate: Candidate }) {
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
      <Badge variant="secondary">
        {PLATFORM_LABEL[candidate.platform] ?? candidate.platform}
      </Badge>
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
            {candidate.likes_per_follower}× likes/follower
          </TooltipTrigger>
          <TooltipContent>
            Lifetime likes divided by followers — not a per-post engagement rate.
            Band: {candidate.engagement_band}.
          </TooltipContent>
        </Tooltip>
      )}
      {candidate.similarity != null && (
        <Tooltip>
          <TooltipTrigger render={<span className="inline-flex items-center gap-1" />}>
            <Sparkle className="size-3" />
            {Math.round(candidate.similarity * 100)}% similar
          </TooltipTrigger>
          <TooltipContent>
            Cosine similarity between this creator and a profile of the reference
            accounts, measured on their bio and page text.
          </TooltipContent>
        </Tooltip>
      )}
      <StatSourceBadge source={candidate.stat_source} />
    </div>
  );
}

function Evidence({ text }: { text: string }) {
  const [open, setOpen] = useState(false);
  if (!text) return null;
  return (
    <Collapsible open={open} onOpenChange={setOpen}>
      <CollapsibleTrigger className="inline-flex items-center gap-1 text-[11px] text-muted-foreground hover:text-foreground">
        <ChevronDown
          className={cn("size-3 transition-transform", open && "rotate-180")}
        />
        evidence
      </CollapsibleTrigger>
      <CollapsibleContent>
        <p className="mt-1.5 rounded-md border border-border/60 bg-background/60 p-2 font-mono text-[11px] leading-relaxed text-muted-foreground">
          {text}
        </p>
      </CollapsibleContent>
    </Collapsible>
  );
}

function toCsv(rows: RankedCandidate[]): string {
  const header = "score,platform,handle,url,followers,likes_per_follower,stat_source,rationale";
  const escape = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = rows.map((r) =>
    [
      r.score,
      r.platform,
      r.handle,
      r.url,
      r.follower_count ?? "",
      r.likes_per_follower ?? "",
      r.stat_source,
      r.rationale,
    ]
      .map(escape)
      .join(",")
  );
  return [header, ...lines].join("\n");
}

function CopyCsvButton({ shortlist }: { shortlist: RankedCandidate[] }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      variant="ghost"
      size="sm"
      className="gap-1.5 text-xs"
      onClick={async () => {
        await navigator.clipboard.writeText(toCsv(shortlist));
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      {copied ? "Copied" : "Copy CSV"}
    </Button>
  );
}

function CandidateCard({
  candidate,
  rank,
  highlight,
}: {
  candidate: RankedCandidate;
  rank: number;
  highlight: boolean;
}) {
  return (
    <Card
      className={cn(
        "animate-in fade-in slide-in-from-bottom-2 gap-3 border-border/60 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5",
        highlight && "border-primary/40 ring-1 ring-primary/20"
      )}
    >
      <CardHeader>
        <div className="flex items-center justify-between gap-2">
          <span className="flex min-w-0 items-center gap-2">
            <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-bold text-muted-foreground">
              {rank}
            </span>
            <CardTitle className="truncate">
              <a
                href={candidate.url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 hover:text-primary hover:underline"
              >
                {candidate.handle}
                <ExternalLink className="size-3 shrink-0 opacity-50" />
              </a>
            </CardTitle>
          </span>
          <div className="flex shrink-0 items-center gap-1.5">
            <div className="h-1 w-10 overflow-hidden rounded-full bg-muted">
              <div
                className="h-full rounded-full bg-primary"
                style={{ width: `${Math.min(100, candidate.score * 10)}%` }}
              />
            </div>
            <span className="text-xs font-semibold tabular-nums">{candidate.score}/10</span>
          </div>
        </div>
        <Stats candidate={candidate} />
      </CardHeader>
      <CardContent className="space-y-2">
        {candidate.bio_snippet && (
          <p className="line-clamp-2 text-sm text-muted-foreground">{candidate.bio_snippet}</p>
        )}
        <p className="text-sm">{candidate.rationale}</p>
        <Evidence text={candidate.source_evidence} />
      </CardContent>
    </Card>
  );
}

function UnverifiedSection({ candidates }: { candidates: Candidate[] }) {
  const [open, setOpen] = useState(false);
  if (candidates.length === 0) return null;

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="rounded-xl border border-border/60 bg-card/20">
      <CollapsibleTrigger className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left">
        <span className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldQuestion className="size-4" />
          Unverified — no follower count found ({candidates.length})
        </span>
        <ChevronDown className={cn("size-4 text-muted-foreground transition-transform", open && "rotate-180")} />
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="space-y-1.5 border-t border-border/60 px-4 py-3">
          <p className="pb-1 text-xs text-muted-foreground">
            Matched the niche but we could not confirm audience size, so they are not ranked.
          </p>
          {candidates.map((c) => (
            <div key={`${c.platform}-${c.handle}`} className="flex items-center gap-2 text-sm">
              <Badge variant="outline" className="shrink-0">
                {PLATFORM_LABEL[c.platform] ?? c.platform}
              </Badge>
              <a
                href={c.url}
                target="_blank"
                rel="noreferrer"
                className="truncate hover:text-primary hover:underline"
              >
                {c.handle}
              </a>
            </div>
          ))}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

export function ShortlistResults({
  shortlist,
  unverified = [],
  summary,
}: {
  shortlist: RankedCandidate[];
  unverified?: Candidate[];
  summary?: FilterSummary | null;
}) {
  if (shortlist.length === 0 && unverified.length === 0) {
    return <p className="text-sm text-muted-foreground">No candidates matched the brief.</p>;
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 duration-500">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold tracking-wide text-primary uppercase">
          Shortlist
          {summary && (
            <span className="ml-2 font-normal text-muted-foreground normal-case">
              {shortlist.length} of {summary.seen} considered
              {summary.verified > 0 && ` · ${summary.verified} verified`}
            </span>
          )}
        </p>
        {shortlist.length > 0 && <CopyCsvButton shortlist={shortlist} />}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {shortlist.map((candidate, i) => (
          <CandidateCard
            key={`${candidate.platform}-${candidate.handle}`}
            candidate={candidate}
            rank={i + 1}
            highlight={i === 0}
          />
        ))}
      </div>

      <UnverifiedSection candidates={unverified} />
    </div>
  );
}
