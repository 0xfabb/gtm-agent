from pydantic import BaseModel

from config import RANKING_MODEL, openai_client
from schemas import Candidate, RankedCandidate, StructuredQuery

SYSTEM_PROMPT = """You are ranking creator candidates against a recruiter's \
structured brief. Score each candidate 1-10 on fit (audience, niche, \
follower ceiling, growth signal) and write a one-sentence rationale. Only \
rank the candidates given to you — never invent new ones. Sort the output \
best-fit first."""


class _RankingResult(BaseModel):
    ranked: list[RankedCandidate]


def _dedupe(candidates: list[Candidate]) -> list[Candidate]:
    seen: dict[str, Candidate] = {}
    for c in candidates:
        key = c.handle.lower().strip("@") + "|" + c.platform
        seen.setdefault(key, c)
    return list(seen.values())


async def rank_candidates(
    structured_query: StructuredQuery, candidates: list[Candidate]
) -> list[RankedCandidate]:
    deduped = _dedupe(candidates)
    if not deduped:
        return []

    response = await openai_client.responses.parse(
        model=RANKING_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Brief filters: {structured_query.model_dump_json()}\n\n"
                    f"Candidates: {[c.model_dump() for c in deduped]}"
                ),
            },
        ],
        text_format=_RankingResult,
    )
    ranked = response.output_parsed.ranked
    return sorted(ranked, key=lambda r: r.score, reverse=True)
