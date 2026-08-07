from typing import Optional, Protocol

import httpx

from config import YOUTUBE_API_KEY, YOUTUBE_API_URL, YOUTUBE_BATCH_SIZE
from schemas import EnrichedCandidate


class PlatformVerifier(Protocol):
    async def verify(
        self, candidates: list[EnrichedCandidate]
    ) -> dict[str, EnrichedCandidate]: ...


def _channel_lookup_params(candidates: list[EnrichedCandidate]) -> list[tuple[str, str]]:
    lookups: list[tuple[str, str]] = []
    for candidate in candidates:
        handle = candidate.handle
        if handle.startswith("UC") and len(handle) > 20:
            lookups.append(("id", handle))
        else:
            lookups.append(("forHandle", f"@{handle}"))
    return lookups


async def _fetch_channels(
    client: httpx.AsyncClient, param: str, values: list[str]
) -> list[dict]:
    if not values:
        return []
    response = await client.get(
        YOUTUBE_API_URL,
        params={
            "part": "snippet,statistics",
            param: ",".join(values),
            "key": YOUTUBE_API_KEY,
        },
        timeout=15.0,
    )
    response.raise_for_status()
    return response.json().get("items", [])


def _apply_channel(candidate: EnrichedCandidate, item: dict) -> EnrichedCandidate:
    stats = item.get("statistics", {})
    snippet = item.get("snippet", {})

    raw_subscribers = stats.get("subscriberCount")
    subscribers = int(raw_subscribers) if raw_subscribers is not None else None

    title = snippet.get("title")
    description = snippet.get("description")

    return candidate.model_copy(
        update={
            "handle": title or candidate.handle,
            "follower_count": subscribers if subscribers is not None else candidate.follower_count,
            "stat_source": "verified" if subscribers is not None else candidate.stat_source,
            "stat_confidence": "youtube_api" if subscribers is not None else candidate.stat_confidence,
            "bio_snippet": candidate.bio_snippet or (description or "")[:200] or None,
        }
    )


async def verify_youtube(
    candidates: list[EnrichedCandidate],
) -> list[EnrichedCandidate]:
    if not YOUTUBE_API_KEY or not candidates:
        return candidates

    by_handle: dict[str, EnrichedCandidate] = {}
    by_id: dict[str, EnrichedCandidate] = {}
    for candidate, (param, value) in zip(candidates, _channel_lookup_params(candidates)):
        if param == "id":
            by_id[value] = candidate
        else:
            by_handle[value.lower()] = candidate

    resolved: dict[int, EnrichedCandidate] = {}
    index_of = {id(c): i for i, c in enumerate(candidates)}

    async with httpx.AsyncClient() as client:
        ids = list(by_id)
        for start in range(0, len(ids), YOUTUBE_BATCH_SIZE):
            items = await _fetch_channels(client, "id", ids[start : start + YOUTUBE_BATCH_SIZE])
            for item in items:
                candidate = by_id.get(item.get("id", ""))
                if candidate is not None:
                    resolved[index_of[id(candidate)]] = _apply_channel(candidate, item)

        for handle, candidate in by_handle.items():
            items = await _fetch_channels(client, "forHandle", [handle])
            if items:
                resolved[index_of[id(candidate)]] = _apply_channel(candidate, items[0])

    return [resolved.get(i, candidate) for i, candidate in enumerate(candidates)]


async def verify_candidates(
    candidates: list[EnrichedCandidate],
) -> list[EnrichedCandidate]:
    youtube = [c for c in candidates if c.platform == "youtube"]
    if not youtube:
        return candidates

    verified = await verify_youtube(youtube)
    replacements = dict(zip((id(c) for c in youtube), verified))
    return [replacements.get(id(c), c) for c in candidates]
