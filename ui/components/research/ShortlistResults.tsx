"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

import { Button } from "@/components/ui/button";
import { CandidateRow } from "@/components/research/CandidateRow";
import type { RankedCandidate } from "@/lib/types";

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

function CopyCsvButton({ rows }: { rows: RankedCandidate[] }) {
  const [copied, setCopied] = useState(false);
  return (
    <Button
      variant="ghost"
      size="sm"
      className="gap-1.5 text-xs"
      onClick={async () => {
        await navigator.clipboard.writeText(toCsv(rows));
        setCopied(true);
        setTimeout(() => setCopied(false), 1500);
      }}
    >
      {copied ? <Check className="size-3.5" /> : <Copy className="size-3.5" />}
      {copied ? "Copied" : "Export CSV"}
    </Button>
  );
}

export function ShortlistResults({
  shortlist,
  cached = [],
}: {
  shortlist: RankedCandidate[];
  cached?: RankedCandidate[];
}) {
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  function toggle(key: string) {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  if (shortlist.length === 0 && cached.length === 0) {
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
    <div className="space-y-4">
      {shortlist.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between gap-3">
            <p className="font-mono text-[11px] font-semibold tracking-wide text-muted-foreground uppercase">
              Ranked results — top {shortlist.length}
            </p>
            <CopyCsvButton rows={[...shortlist, ...cached]} />
          </div>
          <div className="flex flex-col gap-2">
            {shortlist.map((candidate) => {
              const key = `${candidate.platform}-${candidate.handle}`;
              return (
                <CandidateRow
                  key={key}
                  candidate={candidate}
                  verified
                  expanded={expandedKeys.has(key)}
                  onToggleExpand={() => toggle(key)}
                />
              );
            })}
          </div>
        </div>
      )}

      {cached.length > 0 && (
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <p className="font-mono text-[11px] font-semibold tracking-wide text-muted-foreground/60 uppercase">
              Unverified — cached stats
            </p>
            <span className="h-px flex-1 bg-border/60" />
          </div>
          <div className="flex flex-col gap-2">
            {cached.map((candidate) => {
              const key = `${candidate.platform}-${candidate.handle}`;
              return (
                <CandidateRow
                  key={key}
                  candidate={candidate}
                  verified={false}
                  expanded={expandedKeys.has(key)}
                  onToggleExpand={() => toggle(key)}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
