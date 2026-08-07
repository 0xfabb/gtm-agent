import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from schemas import EnrichedCandidate
from verification import _apply_channel, _channel_lookup_params, verify_candidates

CHANNELS_LIST_ITEM = {
    "kind": "youtube#channel",
    "id": "UCa5hPmX8q03fxDYLi9XM7wA",
    "snippet": {
        "title": "PJ Trades",
        "description": "Futures and NQ day trading breakdowns for retail traders.",
        "customUrl": "@pjtrades_nq",
    },
    "statistics": {
        "viewCount": "1200000",
        "subscriberCount": "48300",
        "hiddenSubscriberCount": False,
        "videoCount": "412",
    },
}


def _candidate(**overrides) -> EnrichedCandidate:
    base = dict(handle="PJTrades_NQ", platform="youtube", url="https://youtube.com/@PJTrades_NQ")
    base.update(overrides)
    return EnrichedCandidate(**base)


def test_handles_are_looked_up_by_handle_and_ids_by_id():
    lookups = _channel_lookup_params(
        [_candidate(handle="PJTrades_NQ"), _candidate(handle="UCa5hPmX8q03fxDYLi9XM7wA")]
    )
    assert lookups == [
        ("forHandle", "@PJTrades_NQ"),
        ("id", "UCa5hPmX8q03fxDYLi9XM7wA"),
    ]


def test_lowercased_channel_id_is_still_routed_as_an_id():
    lookups = _channel_lookup_params([_candidate(handle="uc9ezpy5muv7zzcrlndaijww")])
    assert lookups == [("id", "uc9ezpy5muv7zzcrlndaijww")]


def test_verified_subscriber_count_replaces_unknown_count():
    result = _apply_channel(_candidate(follower_count=None), CHANNELS_LIST_ITEM)
    assert result.follower_count == 48300
    assert result.stat_source == "verified"
    assert result.stat_confidence == "youtube_api"


def test_verification_overrides_a_wrong_parsed_count():
    result = _apply_channel(
        _candidate(follower_count=999, stat_source="parsed"), CHANNELS_LIST_ITEM
    )
    assert result.follower_count == 48300
    assert result.stat_source == "verified"


def test_raw_channel_id_is_replaced_with_the_real_title():
    result = _apply_channel(_candidate(handle="UCa5hPmX8q03fxDYLi9XM7wA"), CHANNELS_LIST_ITEM)
    assert result.handle == "PJ Trades"


def test_description_backfills_a_missing_bio():
    result = _apply_channel(_candidate(bio_snippet=None), CHANNELS_LIST_ITEM)
    assert "day trading" in result.bio_snippet


def test_hidden_subscriber_count_leaves_candidate_unverified():
    item = {**CHANNELS_LIST_ITEM, "statistics": {"hiddenSubscriberCount": True}}
    result = _apply_channel(_candidate(follower_count=None), item)
    assert result.follower_count is None
    assert result.stat_source != "verified"


def test_non_youtube_candidates_are_passed_through_untouched():
    tiktok = _candidate(platform="tiktok", handle="sayhey_rey", follower_count=40100)
    result = asyncio.run(verify_candidates([tiktok]))
    assert result == [tiktok]
