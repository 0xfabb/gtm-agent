"use client";

import { useState } from "react";
import { Check, ChevronDown, Copy, ShieldQuestion } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CandidateRow } from "@/components/research/CandidateRow";
import { cn } from "@/lib/utils";
import type { Candidate, FilterSummary, RankedCandidate } from "@/lib/types";

const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  youtube: "YouTube",
  instagram: "Instagram",
};

function toCsv(rows: RankedCandidate[]): string {
  const header =
    "score,platform,handle,url,followers,likes_per_follower,similarity,stat_source,rationale";
  const escape = (v: unknown) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = rows.map((r) =>
    [
      r.score,
      r.platform,
      r.handle,
      r.url,
      r.follower_count ?? "",
      r.likes_per_follower ?? "",
      r.similarity ?? "",
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
      {copied ? "Copied" : "Export CSV"}
    </Button>
  );
}

function UnverifiedSection({ candidates }: { candidates: Candidate[] }) {
  const [open, setOpen] = useState(false);
  if (candidates.length === 0) return null;

  return (
    <div className="overflow-hidden rounded-xl border border-border/60 bg-card/40">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between gap-2 px-4 py-3 text-left hover:bg-white/2"
      >
        <span className="flex items-center gap-2 text-sm text-muted-foreground">
          <ShieldQuestion className="size-4" />
          Unverified — no follower count found ({candidates.length})
        </span>
        <ChevronDown
          className={cn("size-4 text-muted-foreground transition-transform", open && "rotate-180")}
        />
      </button>
      {open && (
        <div className="space-y-1.5 border-t border-border/60 px-4 py-3">
          <p className="pb-1 text-xs text-muted-foreground">
            On-niche, but we could not confirm audience size, so they are not ranked.
          </p>
          {candidates.map((c) => (
            <div key={`${c.platform}-${c.handle}`} className="flex items-center gap-2 text-sm">
              <span className="shrink-0 rounded bg-white/6 px-1.5 py-0.5 text-[11px] text-muted-foreground">
                {PLATFORM_LABEL[c.platform] ?? c.platform}
              </span>
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
      )}
    </div>
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
    return (
      <div className="rounded-xl border border-dashed border-border/60 px-4 py-10 text-center">
        <p className="text-sm text-muted-foreground">No candidates matched the brief.</p>
        <p className="mt-1 text-xs text-muted-foreground/70">
          Try widening the follower range or loosening the niche.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-semibold tracking-wide text-primary uppercase">
          Shortlist
          {summary && (
            <span className="tabular ml-2 font-normal text-muted-foreground normal-case">
              {shortlist.length} of {summary.seen} considered
              {summary.verified > 0 && ` · ${summary.verified} verified`}
            </span>
          )}
        </p>
        {shortlist.length > 0 && <CopyCsvButton shortlist={shortlist} />}
      </div>

      {shortlist.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border/60 bg-card">
          {shortlist.map((candidate, i) => (
            <CandidateRow
              key={`${candidate.platform}-${candidate.handle}`}
              candidate={candidate}
              rank={i + 1}
            />
          ))}
        </div>
      )}

      <UnverifiedSection candidates={unverified} />
    </div>
  );
}
