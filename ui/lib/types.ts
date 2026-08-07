export type Platform = "tiktok" | "youtube" | "instagram";

export interface ReferenceAccount {
  platform: Platform;
  handle: string;
  url: string;
}

export interface StructuredQuery {
  platforms: Platform[];
  niche_keywords: string[];
  reference_accounts: ReferenceAccount[];
  audience_age_min: number | null;
  audience_age_max: number | null;
  audience_gender_skew: string | null;
  audience_geo: string | null;
  follower_min: number | null;
  follower_max: number | null;
  exclude_keywords: string[];
  max_results: number | null;
  other_notes: string | null;
}

export interface SeedProfile {
  summary: string;
  niche_keywords: string[];
  content_format: string | null;
  audience: string | null;
  search_descriptions: string[];
}

export type StatSource = "verified" | "parsed" | "model" | "none";
export type EngagementBand = "low" | "healthy" | "very_high" | "unknown";

export interface Candidate {
  handle: string;
  platform: Platform;
  url: string;
  follower_count: number | null;
  likes_count: number | null;
  likes_per_follower: number | null;
  engagement_band: EngagementBand;
  stat_source: StatSource;
  stat_confidence: string;
  similarity: number | null;
  bio_snippet: string | null;
  growth_signal: string | null;
  source_evidence: string;
}

export interface RankedCandidate extends Candidate {
  score: number;
  rationale: string;
}

export interface FilterSummary {
  seen: number;
  ranked: number;
  verified_shown: number;
  cached_shown: number;
}

export interface CostSummary {
  calls: number;
  input_tokens: number;
  output_tokens: number;
  usd: number;
}

export type StepAction = "searching" | "found" | "verifying" | "skipped";

export interface AgentStep {
  agent: string;
  action: StepAction;
  query?: string;
  result?: { url?: string; title?: string | null; note?: string };
  at: number;
}

export type AgentStatus = "pending" | "active" | "done" | "failed";

export type ResearchEvent =
  | { type: "run_started"; run_id: string }
  | { type: "structured_query"; data: StructuredQuery }
  | { type: "seed_profile"; data: SeedProfile }
  | {
      type: "agent_step";
      agent: string;
      action: StepAction;
      query?: string;
      result?: { url?: string; title?: string | null; note?: string };
    }
  | { type: "error"; agent: string; message: string }
  | { type: "filtered"; data: FilterSummary }
  | { type: "ranking_complete"; data: RankedCandidate[] }
  | {
      type: "done";
      run_id: string;
      shortlist: RankedCandidate[];
      cached: RankedCandidate[];
      considered: number;
      cost: CostSummary;
    };

export interface RefilterResponse {
  shortlist: RankedCandidate[];
  cached: RankedCandidate[];
  considered: number;
}

export interface RefineResponse {
  kind: "filter" | "new_run";
  follower_min: number | null;
  follower_max: number | null;
  max_results: number | null;
  combined_prompt: string | null;
  explanation: string;
  cost: CostSummary;
}
