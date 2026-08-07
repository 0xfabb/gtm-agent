import { Fingerprint } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { SeedProfile } from "@/lib/types";

export function SeedProfileCard({ profile }: { profile: SeedProfile }) {
  return (
    <div className="animate-in fade-in slide-in-from-bottom-2 space-y-3 rounded-xl border border-primary/25 bg-primary/5 p-4 duration-500">
      <p className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-primary uppercase">
        <Fingerprint className="size-3.5" />
        What we understood the references to be
      </p>

      <p className="text-sm leading-relaxed text-foreground/90">{profile.summary}</p>

      {profile.niche_keywords.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {profile.niche_keywords.slice(0, 10).map((keyword) => (
            <Badge key={keyword} variant="secondary" className="capitalize">
              {keyword}
            </Badge>
          ))}
        </div>
      )}

      {profile.search_descriptions.length > 0 && (
        <div className="space-y-1 border-t border-primary/15 pt-2.5">
          <p className="text-[11px] font-medium tracking-wide text-muted-foreground uppercase">
            Searching for
          </p>
          <ul className="space-y-1">
            {profile.search_descriptions.map((description, i) => (
              <li key={i} className="font-mono text-[11px] leading-relaxed text-muted-foreground">
                → {description}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
