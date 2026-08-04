import { ExternalLink, TrendingUp, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import type { RankedCandidate } from "@/lib/types";

const PLATFORM_LABEL: Record<string, string> = {
  tiktok: "TikTok",
  youtube: "YouTube",
  instagram: "Instagram",
};

function ScoreBar({ score }: { score: number }) {
  return (
    <div className="flex items-center gap-1.5">
      <div className="h-1 w-10 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary transition-all"
          style={{ width: `${Math.min(100, score * 10)}%` }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums text-foreground">{score}/10</span>
    </div>
  );
}

export function ShortlistResults({ shortlist }: { shortlist: RankedCandidate[] }) {
  if (shortlist.length === 0) {
    return <p className="text-sm text-muted-foreground">No candidates matched the brief.</p>;
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 duration-500">
      <p className="text-xs font-semibold tracking-wide text-primary uppercase">Shortlist</p>
      <div className="grid gap-3 sm:grid-cols-2">
        {shortlist.map((c, i) => (
          <Card
            key={`${c.platform}-${c.handle}`}
            className={cn(
              "animate-in fade-in slide-in-from-bottom-2 relative gap-3 border-border/60 transition-all duration-300 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/5",
              i === 0 && "border-primary/40 ring-1 ring-primary/20"
            )}
            style={{ animationDelay: `${i * 60}ms` }}
          >
            <CardHeader>
              <div className="flex items-center justify-between gap-2">
                <span className="flex items-center gap-2">
                  <span className="flex size-5 items-center justify-center rounded-full bg-muted text-[10px] font-bold text-muted-foreground">
                    {i + 1}
                  </span>
                  <CardTitle>
                    <a
                      href={c.url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 hover:text-primary hover:underline"
                    >
                      {c.handle}
                      <ExternalLink className="size-3 opacity-50" />
                    </a>
                  </CardTitle>
                </span>
                <ScoreBar score={c.score} />
              </div>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <Badge variant="secondary">{PLATFORM_LABEL[c.platform] ?? c.platform}</Badge>
                {c.follower_count != null && (
                  <span className="inline-flex items-center gap-1">
                    <Users className="size-3" />
                    {c.follower_count.toLocaleString()}
                  </span>
                )}
                {c.growth_signal && (
                  <span className="inline-flex items-center gap-1">
                    <TrendingUp className="size-3" />
                    growth signal
                  </span>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-2">
              {c.bio_snippet && (
                <p className="line-clamp-2 text-sm text-muted-foreground">{c.bio_snippet}</p>
              )}
              <p className="text-sm">{c.rationale}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
