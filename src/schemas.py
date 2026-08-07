from typing import Literal, Optional

from pydantic import BaseModel

Platform = Literal["tiktok", "youtube", "instagram"]


class ResearchRequest(BaseModel):
    prompt: str


class ReferenceAccount(BaseModel):
    platform: Platform
    handle: str
    url: str


class StructuredQuery(BaseModel):
    platforms: list[Platform]
    niche_keywords: list[str]
    reference_accounts: list[ReferenceAccount] = []
    audience_age_min: Optional[int] = None
    audience_age_max: Optional[int] = None
    audience_gender_skew: Optional[str] = None
    audience_geo: Optional[str] = None
    follower_min: Optional[int] = None
    follower_max: Optional[int] = None
    exclude_keywords: list[str] = []
    max_results: Optional[int] = None
    other_notes: Optional[str] = None


class SeedProfile(BaseModel):
    summary: str
    niche_keywords: list[str]
    content_format: Optional[str] = None
    audience: Optional[str] = None
    search_descriptions: list[str] = []


class Candidate(BaseModel):
    handle: str
    platform: Platform
    url: str
    follower_count: Optional[int] = None
    bio_snippet: Optional[str] = None
    growth_signal: Optional[str] = None
    source_evidence: str


class EnrichedCandidate(BaseModel):
    handle: str
    platform: Platform
    url: str
    follower_count: Optional[int] = None
    likes_count: Optional[int] = None
    likes_per_follower: Optional[float] = None
    engagement_band: str = "unknown"
    stat_source: str = "none"
    stat_confidence: str = "none"
    bio_snippet: Optional[str] = None
    growth_signal: Optional[str] = None
    source_evidence: str = ""


class RankedCandidate(EnrichedCandidate):
    score: int
    rationale: str
