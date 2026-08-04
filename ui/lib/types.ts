export type Platform = "tiktok" | "youtube" | "instagram";

export interface StructuredQuery {
  platforms: Platform[];
  niche_keywords: string[];
  audience_age_min: number | null;
  audience_age_max: number | null;
  audience_gender_skew: string | null;
  follower_max: number | null;
  growth_rate_min_pct: number | null;
  other_notes: string | null;
}

export interface Candidate {
  handle: string;
  platform: Platform;
  url: string;
  follower_count: number | null;
  bio_snippet: string | null;
  growth_signal: string | null;
  source_evidence: string;
}

export interface RankedCandidate extends Candidate {
  score: number;
  rationale: string;
}

export interface AgentStep {
  agent: string;
  action: "searching" | "found";
  query?: string;
  result?: { url: string; title: string | null };
  at: number;
}

export type ResearchEvent =
  | { type: "structured_query"; data: StructuredQuery }
  | { type: "agent_step"; agent: string; action: "searching"; query: string }
  | {
      type: "agent_step";
      agent: string;
      action: "found";
      result: { url: string; title: string | null };
    }
  | { type: "error"; agent: string; message: string }
  | { type: "ranking_complete"; data: RankedCandidate[] }
  | { type: "done"; shortlist: RankedCandidate[] };
