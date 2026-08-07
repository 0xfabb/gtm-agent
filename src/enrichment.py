from typing import Optional

from extraction import engagement_band, extract_profile_stats, likes_per_follower
from schemas import Candidate, EnrichedCandidate, StructuredQuery
from urls import dedupe_key, normalize_url, parse_profile_url


def _resolve_identity(
    candidate: Candidate, observed_url: Optional[str] = None
) -> tuple[str, str]:
    ref = parse_profile_url(observed_url) if observed_url else None
    if ref is None:
        ref = parse_profile_url(candidate.url)
    if ref is None:
        return candidate.handle.lstrip("@"), normalize_url(candidate.url)
    return ref.handle, ref.canonical_url


def enrich_candidate(
    candidate: Candidate,
    page_text: Optional[str] = None,
    observed_url: Optional[str] = None,
) -> EnrichedCandidate:
    handle, url = _resolve_identity(candidate, observed_url)

    stats = extract_profile_stats(page_text or candidate.source_evidence)
    followers = stats.followers if stats.followers is not None else candidate.follower_count
    stat_source = "parsed" if stats.followers is not None else "model"
    if followers is None:
        stat_source = "none"

    ratio = likes_per_follower(stats.likes, followers)

    return EnrichedCandidate(
        handle=handle,
        platform=candidate.platform,
        url=url,
        follower_count=followers,
        likes_count=stats.likes,
        likes_per_follower=ratio,
        engagement_band=engagement_band(ratio),
        stat_source=stat_source,
        stat_confidence=stats.confidence,
        bio_snippet=candidate.bio_snippet,
        growth_signal=candidate.growth_signal,
        source_evidence=candidate.source_evidence,
    )


def dedupe_candidates(candidates: list[EnrichedCandidate]) -> list[EnrichedCandidate]:
    best: dict[str, EnrichedCandidate] = {}
    for candidate in candidates:
        key = dedupe_key(candidate.platform, candidate.handle)
        existing = best.get(key)
        if existing is None:
            best[key] = candidate
            continue
        if existing.follower_count is None and candidate.follower_count is not None:
            best[key] = candidate
    return list(best.values())


def _is_reference(candidate: EnrichedCandidate, query: StructuredQuery) -> bool:
    key = dedupe_key(candidate.platform, candidate.handle)
    return any(
        dedupe_key(ref.platform, ref.handle) == key for ref in query.reference_accounts
    )


def _matches_exclusions(candidate: EnrichedCandidate, query: StructuredQuery) -> bool:
    haystack = " ".join(
        part.lower()
        for part in (candidate.handle, candidate.bio_snippet or "")
        if part
    )
    return any(
        keyword.lower() in haystack
        for keyword in query.exclude_keywords
        if len(keyword) > 3
    )


def partition_candidates(
    candidates: list[EnrichedCandidate], query: StructuredQuery
) -> tuple[list[EnrichedCandidate], list[EnrichedCandidate]]:
    in_band: list[EnrichedCandidate] = []
    unverified: list[EnrichedCandidate] = []

    for candidate in candidates:
        if _is_reference(candidate, query):
            continue
        if _matches_exclusions(candidate, query):
            continue

        followers = candidate.follower_count
        if followers is None:
            unverified.append(candidate)
            continue
        if query.follower_min is not None and followers < query.follower_min:
            continue
        if query.follower_max is not None and followers > query.follower_max:
            continue
        in_band.append(candidate)

    return in_band, unverified


def enrich_all(
    candidates: list[Candidate], observations: Optional[dict] = None
) -> list[EnrichedCandidate]:
    seen = observations or {}
    enriched = []
    for candidate in candidates:
        ref = parse_profile_url(candidate.url)
        handle = ref.handle if ref else candidate.handle
        observation = seen.get(dedupe_key(candidate.platform, handle))
        enriched.append(
            enrich_candidate(
                candidate,
                page_text=getattr(observation, "text", None),
                observed_url=getattr(observation, "url", None),
            )
        )
    return dedupe_candidates(enriched)


def enrich_and_filter(
    candidates: list[Candidate],
    query: StructuredQuery,
    observations: Optional[dict] = None,
) -> tuple[list[EnrichedCandidate], list[EnrichedCandidate]]:
    return partition_candidates(enrich_all(candidates, observations), query)
