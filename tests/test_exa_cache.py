import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import exa_cache


class _FakeExa:
    def __init__(self):
        self.search_calls = 0
        self.contents_calls = 0

    async def search(self, query, **kwargs):
        self.search_calls += 1
        return f"results-for-{query}"

    async def get_contents(self, urls, **kwargs):
        self.contents_calls += 1
        return f"contents-for-{urls}"


def _install_fake(monkey_target):
    exa_cache.reset_cache()
    exa_cache.exa_client = monkey_target


def test_identical_search_is_served_from_cache():
    fake = _FakeExa()
    _install_fake(fake)

    async def run():
        a = await exa_cache.search("finance creators", num_results=5)
        b = await exa_cache.search("finance creators", num_results=5)
        return a, b

    a, b = asyncio.run(run())
    assert a == b
    assert fake.search_calls == 1
    assert exa_cache.cache_stats() == {"hits": 1, "misses": 1}


def test_different_params_are_separate_entries():
    fake = _FakeExa()
    _install_fake(fake)

    async def run():
        await exa_cache.search("finance creators", num_results=5)
        await exa_cache.search("finance creators", num_results=15)

    asyncio.run(run())
    assert fake.search_calls == 2


def test_kwarg_order_does_not_change_the_key():
    fake = _FakeExa()
    _install_fake(fake)

    async def run():
        await exa_cache.search("q", num_results=5, include_domains=["tiktok.com"])
        await exa_cache.search("q", include_domains=["tiktok.com"], num_results=5)

    asyncio.run(run())
    assert fake.search_calls == 1


def test_contents_are_cached_regardless_of_url_order():
    fake = _FakeExa()
    _install_fake(fake)

    async def run():
        await exa_cache.get_contents(["b", "a"])
        await exa_cache.get_contents(["a", "b"])

    asyncio.run(run())
    assert fake.contents_calls == 1


def test_expired_entries_are_refetched(monkeypatch):
    fake = _FakeExa()
    _install_fake(fake)
    monkeypatch.setattr(exa_cache, "EXA_CACHE_TTL_SECONDS", 0)

    async def run():
        await exa_cache.search("q")
        await exa_cache.search("q")

    asyncio.run(run())
    assert fake.search_calls == 2


def test_cache_evicts_when_full(monkeypatch):
    fake = _FakeExa()
    _install_fake(fake)
    monkeypatch.setattr(exa_cache, "EXA_CACHE_MAX_ENTRIES", 2)

    async def run():
        await exa_cache.search("one")
        await exa_cache.search("two")
        await exa_cache.search("three")
        await exa_cache.search("one")

    asyncio.run(run())
    assert fake.search_calls == 4
