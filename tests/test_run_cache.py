import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import run_cache
from run_cache import get_run, new_run_id, store_run
from schemas import StructuredQuery


def _query() -> StructuredQuery:
    return StructuredQuery(platforms=["tiktok"], niche_keywords=["finance"])


def setup_function():
    run_cache._entries.clear()


def test_stored_run_is_retrievable():
    run_id = new_run_id()
    store_run(run_id, _query(), [])
    entry = get_run(run_id)
    assert entry is not None
    assert entry.run_id == run_id


def test_unknown_run_id_returns_none():
    assert get_run("does-not-exist") is None


def test_run_ids_are_unique():
    assert new_run_id() != new_run_id()


def test_eviction_drops_oldest_when_over_capacity(monkeypatch):
    monkeypatch.setattr(run_cache, "RUN_CACHE_MAX_ENTRIES", 2)
    first = new_run_id()
    store_run(first, _query(), [])
    time.sleep(0.01)
    store_run(new_run_id(), _query(), [])
    time.sleep(0.01)
    store_run(new_run_id(), _query(), [])
    assert get_run(first) is None
    assert len(run_cache._entries) <= 2


def test_expired_entries_are_evicted(monkeypatch):
    monkeypatch.setattr(run_cache, "RUN_CACHE_TTL_SECONDS", 0)
    run_id = new_run_id()
    store_run(run_id, _query(), [])
    store_run(new_run_id(), _query(), [])
    assert get_run(run_id) is None
