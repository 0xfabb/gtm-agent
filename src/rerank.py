import math
from typing import Optional

from config import EMBEDDING_MODEL, openai_client
from schemas import EnrichedCandidate, SeedProfile


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


def seed_text(profile: SeedProfile) -> str:
    parts = [profile.summary, " ".join(profile.niche_keywords)]
    if profile.content_format:
        parts.append(profile.content_format)
    if profile.audience:
        parts.append(profile.audience)
    parts.extend(profile.search_descriptions)
    return "\n".join(part for part in parts if part).strip()


def candidate_text(candidate: EnrichedCandidate) -> str:
    parts = [
        candidate.handle,
        candidate.bio_snippet or "",
        candidate.source_evidence[:400],
    ]
    return " ".join(part for part in parts if part).strip()


async def _embed(texts: list[str]) -> list[list[float]]:
    response = await openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=texts
    )
    return [item.embedding for item in response.data]


async def rerank_by_similarity(
    candidates: list[EnrichedCandidate], profile: Optional[SeedProfile]
) -> list[EnrichedCandidate]:
    if profile is None or len(candidates) < 2:
        return candidates

    target = seed_text(profile)
    if not target:
        return candidates

    texts = [candidate_text(c) for c in candidates]
    embeddings = await _embed([target, *texts])
    seed_vector, candidate_vectors = embeddings[0], embeddings[1:]

    scored = []
    for candidate, vector in zip(candidates, candidate_vectors):
        similarity = round(cosine_similarity(seed_vector, vector), 4)
        scored.append(candidate.model_copy(update={"similarity": similarity}))

    scored.sort(key=lambda c: c.similarity or 0.0, reverse=True)
    return scored
