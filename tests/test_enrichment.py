import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enrichment import (
    dedupe_candidates,
    enrich_and_filter,
    enrich_candidate,
    partition_candidates,
)
from schemas import Candidate, EnrichedCandidate, ReferenceAccount, StructuredQuery

REAL_PROFILE_TEXT = (
    "Reymar (@sayhey_rey) | TikTok  # sayhey_rey  ## Reymar  "
    "### 912Following40.1KFollowers368.5KLikes  ## Forex trader  "
    "Suggested accounts  View all  Olivia Rodrigo  24.7M followers"
)


def _candidate(**overrides) -> Candidate:
    base = dict(
        handle="sayhey_rey",
        platform="tiktok",
        url="https://www.tiktok.com/@sayhey_rey?_t=abc123",
        source_evidence="some quote",
    )
    base.update(overrides)
    return Candidate(**base)


def _query(**overrides) -> StructuredQuery:
    base = {"platforms": ["tiktok"], "niche_keywords": ["finance"]}
    base.update(overrides)
    return StructuredQuery(**base)


def _enriched(**overrides) -> EnrichedCandidate:
    base = dict(handle="someone", platform="tiktok", url="https://x", follower_count=20000)
    base.update(overrides)
    return EnrichedCandidate(**base)


def test_page_text_overrides_model_supplied_follower_count():
    result = enrich_candidate(_candidate(follower_count=24_700_000), REAL_PROFILE_TEXT)
    assert result.follower_count == 40100
    assert result.likes_count == 368500
    assert result.stat_source == "parsed"
    assert result.stat_confidence == "triplet"


def test_engagement_ratio_is_computed():
    result = enrich_candidate(_candidate(), REAL_PROFILE_TEXT)
    assert result.likes_per_follower == 9.19
    assert result.engagement_band == "healthy"


def test_url_is_canonicalised_and_tracking_stripped():
    result = enrich_candidate(_candidate(), REAL_PROFILE_TEXT)
    assert result.url == "https://www.tiktok.com/@sayhey_rey"


def test_falls_back_to_model_count_when_text_has_no_stats():
    result = enrich_candidate(_candidate(follower_count=8000), "no stats here")
    assert result.follower_count == 8000
    assert result.stat_source == "model"


def test_records_no_stat_source_when_nothing_is_known():
    result = enrich_candidate(_candidate(follower_count=None), "no stats here")
    assert result.follower_count is None
    assert result.stat_source == "none"


def test_dedupe_prefers_the_entry_that_has_a_follower_count():
    kept = dedupe_candidates(
        [
            _enriched(handle="Dup", follower_count=None),
            _enriched(handle="dup", follower_count=12345),
        ]
    )
    assert len(kept) == 1
    assert kept[0].follower_count == 12345


def test_same_handle_on_different_platforms_is_not_deduped():
    kept = dedupe_candidates(
        [_enriched(handle="x", platform="tiktok"), _enriched(handle="x", platform="instagram")]
    )
    assert len(kept) == 2


def test_follower_band_is_enforced():
    query = _query(follower_min=5000, follower_max=100000)
    in_band, unverified = partition_candidates(
        [
            _enriched(handle="toosmall", follower_count=36),
            _enriched(handle="toobig", follower_count=5_000_000),
            _enriched(handle="justright", follower_count=40100),
        ],
        query,
    )
    assert [c.handle for c in in_band] == ["justright"]
    assert unverified == []


def test_unknown_follower_count_goes_to_unverified_not_dropped():
    in_band, unverified = partition_candidates(
        [_enriched(handle="mystery", follower_count=None)], _query(follower_min=5000)
    )
    assert in_band == []
    assert [c.handle for c in unverified] == ["mystery"]


def test_reference_accounts_are_never_returned_as_candidates():
    query = _query(
        reference_accounts=[
            ReferenceAccount(
                platform="tiktok",
                handle="deltatrendtrading",
                url="https://www.tiktok.com/@deltatrendtrading",
            )
        ]
    )
    in_band, _ = partition_candidates(
        [_enriched(handle="DeltaTrendTrading", follower_count=50000)], query
    )
    assert in_band == []


def test_exclusion_keywords_filter_by_bio_and_handle():
    query = _query(exclude_keywords=["crypto"])
    in_band, _ = partition_candidates(
        [
            _enriched(handle="cryptoguy", follower_count=20000),
            _enriched(handle="stockguy", follower_count=20000, bio_snippet="Crypto signals"),
            _enriched(handle="cleanguy", follower_count=20000, bio_snippet="stocks"),
        ],
        query,
    )
    assert [c.handle for c in in_band] == ["cleanguy"]


def test_end_to_end_uses_page_text_keyed_by_handle():
    in_band, _ = enrich_and_filter(
        [_candidate(follower_count=24_700_000)],
        _query(follower_min=5000, follower_max=100000),
        {"tiktok|sayhey_rey": REAL_PROFILE_TEXT},
    )
    assert len(in_band) == 1
    assert in_band[0].follower_count == 40100
