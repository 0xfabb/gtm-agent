import { Ban, Gauge, Globe, Layers, Sparkles, StickyNote, Tag, Users } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { StructuredQuery } from "@/lib/types";

function Group({
  icon: Icon,
  label,
  values,
  variant = "secondary",
}: {
  icon: typeof Tag;
  label: string;
  values: string[];
  variant?: "secondary" | "outline";
}) {
  if (values.length === 0) return null;
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </span>
      {values.map((v, i) => (
        <Badge key={`${v}-${i}`} variant={variant} className="capitalize">
          {v}
        </Badge>
      ))}
    </div>
  );
}

function followerBand(min: number | null, max: number | null): string | null {
  if (min && max) return `${min.toLocaleString()} – ${max.toLocaleString()} followers`;
  if (max) return `under ${max.toLocaleString()} followers`;
  if (min) return `at least ${min.toLocaleString()} followers`;
  return null;
}

export function StructuredQueryChips({ query }: { query: StructuredQuery }) {
  const audience: string[] = [];
  if (query.audience_age_min || query.audience_age_max) {
    audience.push(`${query.audience_age_min ?? "?"}-${query.audience_age_max ?? "?"} yrs`);
  }
  if (query.audience_gender_skew) audience.push(query.audience_gender_skew);

  const band = followerBand(query.follower_min, query.follower_max);
  const limits: string[] = band ? [band] : [];
  if (query.max_results) limits.push(`top ${query.max_results}`);

  const references = query.reference_accounts ?? [];

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 rounded-xl border border-border/60 bg-card/40 p-4 duration-500">
      <p className="text-xs font-semibold tracking-wide text-primary uppercase">Understood as</p>
      <div className="space-y-2.5">
        {references.length > 0 && (
          <Group
            icon={Sparkles}
            label="Similar to"
            variant="outline"
            values={references.map((r) => `@${r.handle} · ${r.platform}`)}
          />
        )}
        <Group icon={Layers} label="Platforms" values={query.platforms} />
        <Group icon={Tag} label="Niche" values={query.niche_keywords} />
        <Group icon={Users} label="Audience" values={audience} />
        {query.audience_geo && (
          <Group icon={Globe} label="Geo" values={[query.audience_geo]} />
        )}
        <Group icon={Gauge} label="Limits" values={limits} />
        {query.exclude_keywords?.length > 0 && (
          <Group icon={Ban} label="Exclude" variant="outline" values={query.exclude_keywords} />
        )}
        {query.other_notes && (
          <Group icon={StickyNote} label="Notes" values={[query.other_notes]} />
        )}
      </div>
    </div>
  );
}
