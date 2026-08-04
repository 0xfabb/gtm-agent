
from typing import Literal, Optional

from pydantic import BaseModel


class ResearchRequest(BaseModel):
    prompt: str


class StructuredQuery(BaseModel):
    platforms: list[Literal["tiktok", "youtube", "instagram"]]
    niche_keywords: list[str]
    audience_age_min: Optional[int] = None
    audience_age_max: Optional[int] = None
    audience_gender_skew: Optional[str] = None
    follower_max: Optional[int] = None
    growth_rate_min_pct: Optional[int] = None
    other_notes: Optional[str] = None


class Candidate(BaseModel):
    handle: str
    platform: Literal["tiktok", "youtube", "instagram"]
    url: str
    follower_count: Optional[int] = None
    bio_snippet: Optional[str] = None
    growth_signal: Optional[str] = None
    source_evidence: str


class RankedCandidate(Candidate):
    score: int
    rationale: str
