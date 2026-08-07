import time
import uuid
from dataclasses import dataclass, field

from schemas import RankedCandidate, StructuredQuery

RUN_CACHE_MAX_ENTRIES = 200
RUN_CACHE_TTL_SECONDS = 6 * 3600


@dataclass
class RunEntry:
    run_id: str
    structured_query: StructuredQuery
    ranked_all: list[RankedCandidate]
    created_at: float = field(default_factory=time.time)


_entries: dict[str, RunEntry] = {}


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def _evict_if_needed() -> None:
    now = time.time()
    expired = [k for k, v in _entries.items() if now - v.created_at > RUN_CACHE_TTL_SECONDS]
    for key in expired:
        _entries.pop(key, None)
    while len(_entries) >= RUN_CACHE_MAX_ENTRIES:
        oldest = min(_entries, key=lambda k: _entries[k].created_at)
        _entries.pop(oldest, None)


def store_run(
    run_id: str, structured_query: StructuredQuery, ranked_all: list[RankedCandidate]
) -> None:
    _evict_if_needed()
    _entries[run_id] = RunEntry(
        run_id=run_id, structured_query=structured_query, ranked_all=ranked_all
    )


def get_run(run_id: str) -> RunEntry | None:
    return _entries.get(run_id)
