import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from urls import (
    dedupe_key,
    find_profile_urls,
    is_profile_url,
    normalize_url,
    parse_profile_url,
)

AARON_PROMPT = (
    "Find YouTube, TikTok, and Instagram creators similar to these two: "
    "https://www.tiktok.com/@valatility and https://www.tiktok.com/@deltatrendtrading "
    "(also on Instagram: instagram.com/deltatrendtrading). Match their content style "
    "and niche. Prioritize accounts under 100k followers."
)


def test_finds_all_urls_in_real_prompt_including_schemeless():
    urls = find_profile_urls(AARON_PROMPT)
    assert urls == [
        "https://www.tiktok.com/@valatility",
        "https://www.tiktok.com/@deltatrendtrading",
        "instagram.com/deltatrendtrading",
    ]


def test_does_not_swallow_trailing_punctuation():
    urls = find_profile_urls("see instagram.com/someone, and more")
    assert urls == ["instagram.com/someone"]


def test_finds_nothing_in_plain_prompt():
    assert find_profile_urls("find finance tiktok creators under 100k") == []


def test_parses_tiktok_handle():
    ref = parse_profile_url("https://www.tiktok.com/@valatility")
    assert ref.platform == "tiktok"
    assert ref.handle == "valatility"
    assert ref.canonical_url == "https://www.tiktok.com/@valatility"


def test_parses_schemeless_instagram_handle():
    ref = parse_profile_url("instagram.com/deltatrendtrading")
    assert ref.platform == "instagram"
    assert ref.handle == "deltatrendtrading"


def test_parses_youtube_handle_and_channel_forms():
    assert parse_profile_url("https://www.youtube.com/@ColdFusion").handle == "ColdFusion"
    assert parse_profile_url("https://www.youtube.com/c/SomeName").handle == "SomeName"
    ref = parse_profile_url("https://www.youtube.com/channel/UCabcdefghijklmnopqrstuv")
    assert ref.handle == "UCabcdefghijklmnopqrstuv"
    assert "/channel/" in ref.canonical_url


def test_extracts_handle_from_video_url():
    ref = parse_profile_url("https://www.tiktok.com/@ry.trades/video/7611520526107954462")
    assert ref.handle == "ry.trades"


def test_rejects_non_profile_landing_pages():
    assert parse_profile_url("https://www.tiktok.com/discover/finance-creators") is None
    assert parse_profile_url("https://www.instagram.com/p/ABC123") is None


def test_video_urls_are_not_profile_urls():
    assert not is_profile_url("https://www.tiktok.com/@ry.trades/video/76115205")
    assert not is_profile_url("https://www.youtube.com/watch?v=5HaW_V3uD0k")
    assert not is_profile_url("https://www.instagram.com/reel/XYZ")


def test_profile_urls_are_recognised():
    assert is_profile_url("https://www.tiktok.com/@valatility")
    assert is_profile_url("instagram.com/deltatrendtrading")
    assert is_profile_url("https://www.youtube.com/@ColdFusion")


def test_normalize_strips_tracking_params_and_case():
    assert (
        normalize_url("https://www.tiktok.com/@sayhey_rey?_t=8WAF5YVKIry&_r=1")
        == "https://www.tiktok.com/@sayhey_rey"
    )
    assert (
        normalize_url("https://www.instagram.com/deltatrendtrading/?hl=en")
        == "https://www.instagram.com/deltatrendtrading"
    )


def test_dedupe_key_is_case_and_at_insensitive():
    assert dedupe_key("tiktok", "@Ry.Trades") == dedupe_key("tiktok", "ry.trades")
    assert dedupe_key("tiktok", "x") != dedupe_key("instagram", "x")
