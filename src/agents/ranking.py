from typing import Optional

from pydantic import BaseModel

from config import RANKING_MODEL, openai_client
from cost import CostTracker
from schemas import EnrichedCandidate, Platform, RankedCandidate, StructuredQuery
from urls import dedupe_key

SYSTEM_PROMPT = """You are ranking creator candidates against a recruiter's \
structured brief.

Every follower count and engagement figure you are given was measured \
deterministically. Treat them as facts; do not restate or recompute them.

When similarity_to_references is present it is a cosine similarity between \
the candidate and a profile of the reference accounts, on a 0-1 scale where \
higher is closer. Weight it heavily — the brief asked for creators like those \
references — but override it when the text clearly shows a poor niche fit.

Score each candidate 1-10 on how well they fit the brief's niche, audience and \
positioning, and write one sentence explaining the score.

Score purely on niche and positioning fit. Some candidates you are given may \
fall outside the brief's stated follower range — score them on fit anyway; \
whether they are shown is decided separately from your score. Do not penalise \
a candidate for a missing or unverified stat either.

A 6 means a useful, on-niche creator worth a look; 8-10 means a clear match. \
Reserve 1-5 for creators who are genuinely off-niche or wrong for the audience.

Return every candidate you were given, identified by handle and platform. \
Never invent a candidate that was not in the list."""


class _Score(BaseModel):
    handle: str
    platform: Platform
    score: int
    rationale: str


class _RankingResult(BaseModel):
    ranked: list[_Score]


def _payload(candidate: EnrichedCandidate) -> dict:
    return {
        "handle": candidate.handle,
        "platform": candidate.platform,
        "follower_count": candidate.follower_count,
        "likes_per_follower": candidate.likes_per_follower,
        "engagement_band": candidate.engagement_band,
        "similarity_to_references": candidate.similarity,
        "bio_snippet": candidate.bio_snippet,
        "evidence": candidate.source_evidence[:300],
    }


async def rank_candidates(
    structured_query: StructuredQuery,
    candidates: list[EnrichedCandidate],
    tracker: Optional[CostTracker] = None,
) -> list[RankedCandidate]:
    if not candidates:
        return []

    response = await openai_client.chat.completions.parse(
        model=RANKING_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Brief filters: {structured_query.model_dump_json()}\n\n"
                    f"Candidates: {[_payload(c) for c in candidates]}"
                ),
            },
        ],
        response_format=_RankingResult,
    )
    if tracker:
        tracker.record_response(RANKING_MODEL, response)

    by_key = {dedupe_key(c.platform, c.handle): c for c in candidates}

    ranked: list[RankedCandidate] = []
    for scored in response.choices[0].message.parsed.ranked:
        candidate = by_key.get(dedupe_key(scored.platform, scored.handle))
        if candidate is None:
            continue
        ranked.append(
            RankedCandidate(
                **candidate.model_dump(),
                score=scored.score,
                rationale=scored.rationale,
            )
        )

    ranked.sort(key=lambda r: r.score, reverse=True)
    return ranked
