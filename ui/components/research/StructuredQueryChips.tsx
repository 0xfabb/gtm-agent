import { Chip, FollowerRangeChip, MaxResultsChip } from "@/components/research/ChipControl";
import type { StructuredQuery } from "@/lib/types";

const DEFAULT_FOLLOWER_MIN = 2_000;
const DEFAULT_FOLLOWER_MAX = 10_000_000;
const DEFAULT_MAX_RESULTS = 15;

function audienceLabel(query: StructuredQuery): string | null {
  const parts: string[] = [];
  if (query.audience_age_min || query.audience_age_max) {
    parts.push(`${query.audience_age_min ?? "?"}-${query.audience_age_max ?? "?"}`);
  }
  if (query.audience_gender_skew) parts.push(query.audience_gender_skew);
  if (query.audience_geo) parts.push(query.audience_geo);
  return parts.length > 0 ? parts.join(", ") : null;
}

export function StructuredQueryChips({
  query,
  editable = false,
  onFollowerRangeChange,
  onMaxResultsChange,
}: {
  query: StructuredQuery;
  editable?: boolean;
  onFollowerRangeChange?: (min: number, max: number) => void;
  onMaxResultsChange?: (value: number) => void;
}) {
  const references = query.reference_accounts ?? [];
  const audience = audienceLabel(query);

  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-2 duration-500">
      <p className="text-xs font-semibold tracking-wide text-primary uppercase">Understood as</p>
      <div className="flex flex-wrap items-center gap-2">
        {references.length > 0 && (
          <Chip
            label={
              references.length === 1
                ? `Similar to @${references[0].handle}`
                : `${references.length} reference accounts`
            }
          />
        )}
        {query.platforms.length > 0 && (
          <Chip label={query.platforms.map((p) => p[0].toUpperCase() + p.slice(1)).join(", ")} />
        )}
        {query.niche_keywords.length > 0 && (
          <Chip label={query.niche_keywords.join(", ")} />
        )}
        {audience && <Chip label={audience} />}
        {query.exclude_keywords.length > 0 && (
          <Chip label={`excl. ${query.exclude_keywords.join(", ")}`} />
        )}

        {editable && onFollowerRangeChange ? (
          <FollowerRangeChip
            min={query.follower_min ?? DEFAULT_FOLLOWER_MIN}
            max={query.follower_max ?? DEFAULT_FOLLOWER_MAX}
            onApply={onFollowerRangeChange}
          />
        ) : (
          (query.follower_min || query.follower_max) && (
            <Chip
              label={`${(query.follower_min ?? 0).toLocaleString()} – ${(query.follower_max ?? DEFAULT_FOLLOWER_MAX).toLocaleString()} followers`}
            />
          )
        )}

        {editable && onMaxResultsChange ? (
          <MaxResultsChip
            value={query.max_results ?? DEFAULT_MAX_RESULTS}
            onApply={onMaxResultsChange}
          />
        ) : (
          <Chip label={`Top ${query.max_results ?? DEFAULT_MAX_RESULTS} results`} prominent />
        )}
      </div>
      {query.other_notes && (
        <p className="text-[11px] text-muted-foreground">{query.other_notes}</p>
      )}
    </div>
  );
}
