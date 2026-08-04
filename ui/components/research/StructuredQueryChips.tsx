import { Gauge, Layers, StickyNote, Tag, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { StructuredQuery } from "@/lib/types";

function Group({
  icon: Icon,
  label,
  values,
}: {
  icon: typeof Tag;
  label: string;
  values: string[];
}) {
  if (values.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </span>
      {values.map((v, i) => (
        <Badge key={`${v}-${i}`} variant="secondary" className="capitalize">
          {v}
        </Badge>
      ))}
    </div>
  );
}

export function StructuredQueryChips({ query }: { query: StructuredQuery }) {
  const audience: string[] = [];
  if (query.audience_age_min || query.audience_age_max) {
    audience.push(`${query.audience_age_min ?? "?"}-${query.audience_age_max ?? "?"} yrs`);
  }
  if (query.audience_gender_skew) audience.push(query.audience_gender_skew);

  const limits: string[] = [];
  if (query.follower_max) limits.push(`< ${query.follower_max.toLocaleString()} followers`);
  if (query.growth_rate_min_pct) limits.push(`growth ≥ ${query.growth_rate_min_pct}%`);

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 rounded-xl border border-border/60 bg-card/40 p-4 duration-500">
      <p className="text-xs font-semibold tracking-wide text-primary uppercase">Understood as</p>
      <div className="space-y-2.5">
        <Group icon={Layers} label="Platforms" values={query.platforms} />
        <Group icon={Tag} label="Niche" values={query.niche_keywords} />
        <Group icon={Users} label="Audience" values={audience} />
        <Group icon={Gauge} label="Limits" values={limits} />
        {query.other_notes && (
          <Group icon={StickyNote} label="Notes" values={[query.other_notes]} />
        )}
      </div>
    </div>
  );
}
