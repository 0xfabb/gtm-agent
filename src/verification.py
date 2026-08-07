from typing import Awaitable, Callable, Optional, Protocol

import httpx

from config import YOUTUBE_API_KEY, YOUTUBE_API_URL, YOUTUBE_BATCH_SIZE
from schemas import EnrichedCandidate

EmitFn = Callable[[dict], Awaitable[None]]


class PlatformVerifier(Protocol):
    async def verify(
        self, candidates: list[EnrichedCandidate]
    ) -> dict[str, EnrichedCandidate]: ...


async def _noop_emit(event: dict) -> None:
    return None


def _channel_lookup_params(candidates: list[EnrichedCandidate]) -> list[tuple[str, str]]:
    lookups: list[tuple[str, str]] = []
    for candidate in candidates:
        handle = candidate.handle
        if handle[:2].upper() == "UC" and len(handle) > 20:
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
    candidates: list[EnrichedCandidate], emit: EmitFn = _noop_emit
) -> list[EnrichedCandidate]:
    if not candidates:
        return candidates

    if not YOUTUBE_API_KEY:
        await emit(
            {
                "type": "agent_step",
                "agent": "verification",
                "action": "skipped",
                "result": {"note": "no YOUTUBE_API_KEY configured"},
            }
        )
        return candidates

    await emit(
        {
            "type": "agent_step",
            "agent": "verification",
            "action": "verifying",
            "query": f"confirming subscriber counts for {len(candidates)} YouTube channels",
        }
    )

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
        try:
            ids = list(by_id)
            for start in range(0, len(ids), YOUTUBE_BATCH_SIZE):
                items = await _fetch_channels(
                    client, "id", ids[start : start + YOUTUBE_BATCH_SIZE]
                )
                for item in items:
                    candidate = by_id.get(item.get("id", ""))
                    if candidate is not None:
                        updated = _apply_channel(candidate, item)
                        resolved[index_of[id(candidate)]] = updated
                        await emit(
                            {
                                "type": "agent_step",
                                "agent": "verification",
                                "action": "found",
                                "result": {
                                    "url": updated.url,
                                    "title": f"{updated.handle} — {updated.follower_count:,} subscribers"
                                    if updated.follower_count is not None
                                    else updated.handle,
                                },
                            }
                        )

            for handle, candidate in by_handle.items():
                items = await _fetch_channels(client, "forHandle", [handle])
                if items:
                    updated = _apply_channel(candidate, items[0])
                    resolved[index_of[id(candidate)]] = updated
                    await emit(
                        {
                            "type": "agent_step",
                            "agent": "verification",
                            "action": "found",
                            "result": {
                                "url": updated.url,
                                "title": f"{updated.handle} — {updated.follower_count:,} subscribers"
                                if updated.follower_count is not None
                                else updated.handle,
                            },
                        }
                    )
                else:
                    await emit(
                        {
                            "type": "agent_step",
                            "agent": "verification",
                            "action": "skipped",
                            "result": {"note": f"@{handle} not found via API — using cached stats"},
                        }
                    )
        except Exception as exc:
            await emit(
                {
                    "type": "agent_step",
                    "agent": "verification",
                    "action": "skipped",
                    "result": {"note": f"YouTube API error — using cached stats ({exc})"},
                }
            )

    return [resolved.get(i, candidate) for i, candidate in enumerate(candidates)]


async def verify_candidates(
    candidates: list[EnrichedCandidate], emit: EmitFn = _noop_emit
) -> list[EnrichedCandidate]:
    youtube = [c for c in candidates if c.platform == "youtube"]
    if not youtube:
        return candidates

    verified = await verify_youtube(youtube, emit)
    replacements = dict(zip((id(c) for c in youtube), verified))
    return [replacements.get(id(c), c) for c in candidates]
