import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enrichment import (
    dedupe_candidates,
    drop_excluded,
    enrich_all,
    enrich_candidate,
    select_shortlist,
)
from schemas import Candidate, EnrichedCandidate, RankedCandidate, ReferenceAccount, StructuredQuery

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
    base = dict(
        handle="someone",
        platform="tiktok",
        url="https://x",
        follower_count=20000,
        stat_source="parsed",
    )
    base.update(overrides)
    return EnrichedCandidate(**base)


def _ranked(**overrides) -> RankedCandidate:
    base = dict(
        handle="someone",
        platform="tiktok",
        url="https://x",
        follower_count=20000,
        stat_source="parsed",
        score=8,
        rationale="good fit",
    )
    base.update(overrides)
    return RankedCandidate(**base)


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


def test_drop_excluded_removes_candidates_with_no_follower_count():
    kept = drop_excluded([_enriched(follower_count=None, stat_source="none")], _query())
    assert kept == []


def test_drop_excluded_removes_reference_accounts():
    query = _query(
        reference_accounts=[
            ReferenceAccount(
                platform="tiktok",
                handle="deltatrendtrading",
                url="https://www.tiktok.com/@deltatrendtrading",
            )
        ]
    )
    kept = drop_excluded([_enriched(handle="DeltaTrendTrading")], query)
    assert kept == []


def test_drop_excluded_filters_by_bio_and_handle_keywords():
    query = _query(exclude_keywords=["crypto"])
    kept = drop_excluded(
        [
            _enriched(handle="cryptoguy"),
            _enriched(handle="stockguy", bio_snippet="Crypto signals"),
            _enriched(handle="cleanguy", bio_snippet="stocks"),
        ],
        query,
    )
    assert [c.handle for c in kept] == ["cleanguy"]


def test_select_shortlist_enforces_follower_band():
    query = _query(follower_min=5000, follower_max=100000)
    verified, cached = select_shortlist(
        [
            _ranked(handle="toosmall", follower_count=36, stat_source="verified"),
            _ranked(handle="toobig", follower_count=5_000_000, stat_source="verified"),
            _ranked(handle="justright", follower_count=40100, stat_source="verified"),
        ],
        query,
    )
    assert [c.handle for c in verified] == ["justright"]
    assert cached == []


def test_select_shortlist_enforces_score_threshold():
    query = _query()
    verified, _ = select_shortlist(
        [
            _ranked(handle="weak", score=3, stat_source="verified"),
            _ranked(handle="strong", score=9, stat_source="verified"),
        ],
        query,
        min_score=6,
    )
    assert [c.handle for c in verified] == ["strong"]


def test_select_shortlist_splits_by_stat_tier():
    query = _query()
    verified, cached = select_shortlist(
        [
            _ranked(handle="apiconfirmed", stat_source="verified"),
            _ranked(handle="pageparsed", stat_source="parsed"),
            _ranked(handle="modelclaimed", stat_source="model"),
        ],
        query,
    )
    assert {c.handle for c in verified} == {"apiconfirmed", "pageparsed"}
    assert [c.handle for c in cached] == ["modelclaimed"]


def test_select_shortlist_caps_each_tier_at_max_results():
    query = _query(max_results=2)
    verified, cached = select_shortlist(
        [_ranked(handle=f"v{i}", score=9, stat_source="verified") for i in range(5)]
        + [_ranked(handle=f"c{i}", score=9, stat_source="model") for i in range(5)],
        query,
    )
    assert len(verified) == 2
    assert len(cached) == 2


def test_select_shortlist_is_reapplicable_for_a_wider_band():
    ranked = [
        _ranked(handle="within", follower_count=50000, stat_source="verified"),
        _ranked(handle="outside", follower_count=150000, stat_source="verified"),
    ]
    narrow, _ = select_shortlist(ranked, _query(follower_min=0, follower_max=100000))
    assert [c.handle for c in narrow] == ["within"]

    wide, _ = select_shortlist(ranked, _query(follower_min=0, follower_max=200000))
    assert {c.handle for c in wide} == {"within", "outside"}


class _Observation:
    def __init__(self, url, text=None):
        self.url = url
        self.text = text


def test_enrich_all_uses_page_text_keyed_by_handle():
    enriched = enrich_all(
        [_candidate(follower_count=24_700_000)],
        {
            "tiktok|sayhey_rey": _Observation(
                "https://www.tiktok.com/@sayhey_rey", REAL_PROFILE_TEXT
            )
        },
    )
    assert enriched[0].follower_count == 40100


def test_observed_url_beats_a_model_mangled_url():
    mangled = Candidate(
        handle="uck7zurybxxuoq_uxvr5yoaa",
        platform="youtube",
        url="https://www.youtube.com/channel/uck7zurybxxuoq_uxvr5yoaa",
        source_evidence="",
    )
    observed = _Observation("https://www.youtube.com/channel/UCk7ZURybXXuoQ_UXvR5YoAA")
    enriched = enrich_candidate(mangled, observed_url=observed.url)
    assert enriched.handle == "UCk7ZURybXXuoQ_UXvR5YoAA"
    assert enriched.url.endswith("UCk7ZURybXXuoQ_UXvR5YoAA")


def test_enrich_all_restores_case_via_observations():
    mangled = Candidate(
        handle="uck7zurybxxuoq_uxvr5yoaa",
        platform="youtube",
        url="https://www.youtube.com/channel/uck7zurybxxuoq_uxvr5yoaa",
        source_evidence="",
    )
    enriched = enrich_all(
        [mangled],
        {
            "youtube|uck7zurybxxuoq_uxvr5yoaa": _Observation(
                "https://www.youtube.com/channel/UCk7ZURybXXuoQ_UXvR5YoAA"
            )
        },
    )
    assert enriched[0].handle == "UCk7ZURybXXuoQ_UXvR5YoAA"
