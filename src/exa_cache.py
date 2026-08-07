import hashlib
import json
import time
from typing import Any, Optional

from config import EXA_CACHE_MAX_ENTRIES, EXA_CACHE_TTL_SECONDS, exa_client

_entries: dict[str, tuple[float, Any]] = {}
_stats = {"hits": 0, "misses": 0}


def _make_key(kind: str, payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str)
    digest = hashlib.sha256(encoded.encode()).hexdigest()[:32]
    return f"{kind}:{digest}"


def _get(key: str) -> Optional[Any]:
    entry = _entries.get(key)
    if entry is None:
        _stats["misses"] += 1
        return None
    stored_at, value = entry
    if time.time() - stored_at > EXA_CACHE_TTL_SECONDS:
        _entries.pop(key, None)
        _stats["misses"] += 1
        return None
    _stats["hits"] += 1
    return value


def _put(key: str, value: Any) -> None:
    if len(_entries) >= EXA_CACHE_MAX_ENTRIES:
        oldest = min(_entries, key=lambda k: _entries[k][0])
        _entries.pop(oldest, None)
    _entries[key] = (time.time(), value)


def cache_stats() -> dict:
    return dict(_stats)


def reset_cache() -> None:
    _entries.clear()
    _stats["hits"] = 0
    _stats["misses"] = 0


async def search(query: str, **kwargs):
    key = _make_key("search", {"query": query, **kwargs})
    cached = _get(key)
    if cached is not None:
        return cached
    response = await exa_client.search(query, **kwargs)
    _put(key, response)
    return response


async def get_contents(urls: list[str], **kwargs):
    key = _make_key("contents", {"urls": sorted(urls), **kwargs})
    cached = _get(key)
    if cached is not None:
        return cached
    response = await exa_client.get_contents(urls, **kwargs)
    _put(key, response)
    return response
