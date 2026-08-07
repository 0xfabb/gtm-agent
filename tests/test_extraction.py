import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from extraction import (
    engagement_band,
    extract_profile_stats,
    likes_per_follower,
    parse_stat_number,
    strip_recommendation_chrome,
)

REAL_SAYHEY_REY = (
    "Reymar (@sayhey_rey) | TikTok  #### TikTok Shop is now available on web!  "
    "Browse your favorite items.  Skip to content feed  TikTok  Log in  TikTok  "
    "Search  For You  Shop  Explore  Following  LIVE  Upload  Profile  More  Log in  "
    "#### Company  #### Program  #### Terms & Policies  © 2026 TikTok  # sayhey_rey  "
    "## Reymar  Follow  Message  ### 912Following40.1KFollowers368.5KLikes  "
    "## \U0001f1fa\U0001f1f8 Forex trader digital marketer  Suggested accounts  View all  "
    "tate mcrae  13.7M followers  Follow  Bad Bunny  41.3M followers  Follow  "
    "The Rock  79.7M followers  Follow  Olivia Rodrigo  24.7M followers  Follow"
)

REAL_CHAD_SARTIN = (
    "chad.sartin.comx (@chad.sartin.comx) | TikTok  Skip to content feed  Log in  "
    "Search  More  Log in  © 2026 TikTok  # chad.sartin.comx  ## chad.sartin.comx  "
    "### 87Following36Followers114Likes  Follow  ## One on one coaching Spirituality "
    "|Finance | LLC Creating Trust  Suggested accounts  View all  162.1M followers  "
    "Follow  158.4M followers  Follow  128.7M followers  Follow  94.5M followers"
)

REAL_OFFICIAL_SUNNEI = (
    "TikTok - Make Your Day  # official.sunnei  ## SUNNEI  "
    "### 20Following9327Followers121.8KLikes  "
    "## Memecoin Trader | Crypto Investor Link to the insiders group  "
    "sol.trading  182.7KPinned  147.8KPinned  2199  4046  19.2K  Log in  Log in"
)

REAL_SEANRETHINKMONEY = (
    "seanrethinkmoney (@seanrethinkmoney) | TikTok  Skip to content feed  TikTok  "
    "Log in  Search  For You  Explore  Following  LIVE  Upload  Profile  More  "
    "# seanrethinkmoney  ## seanrethinkmoney  Follow  Message  "
    "### 195Following3048Followers11.8KLikes  ## Keep it simple  "
    "linktr.ee/rethinkmoneyie  Suggested accounts  View all  "
    "BAYRAM GÜLTEKİN RESMİ  10.1M followers  Follow  filmlerkulubu  9.7M followers"
)


def test_parses_plain_integer():
    assert parse_stat_number("2102", None) == 2102


def test_parses_comma_separated_integer():
    assert parse_stat_number("1,575", None) == 1575


def test_parses_abbreviated_units():
    assert parse_stat_number("40.4", "K") == 40400
    assert parse_stat_number("8.6", "M") == 8_600_000
    assert parse_stat_number("1.2", "B") == 1_200_000_000


def test_parses_lowercase_unit():
    assert parse_stat_number("13.8", "m") == 13_800_000


def test_rejects_non_numeric():
    assert parse_stat_number("abc", None) is None


def test_parses_unspaced_stat_block_and_ignores_suggested_accounts():
    stats = extract_profile_stats(REAL_SAYHEY_REY)
    assert stats.followers == 40100
    assert stats.likes == 368500
    assert stats.following == 912
    assert stats.confidence == "triplet"


def test_tiny_account_is_not_inflated_by_decoys():
    stats = extract_profile_stats(REAL_CHAD_SARTIN)
    assert stats.followers == 36
    assert stats.likes == 114
    assert stats.confidence == "triplet"


def test_parses_profile_without_suggested_accounts_block():
    stats = extract_profile_stats(REAL_OFFICIAL_SUNNEI)
    assert stats.followers == 9327
    assert stats.likes == 121800


def test_parses_profile_with_nav_following_link():
    stats = extract_profile_stats(REAL_SEANRETHINKMONEY)
    assert stats.followers == 3048
    assert stats.likes == 11800


def test_suggested_accounts_block_is_removed_before_parsing():
    stripped = strip_recommendation_chrome(REAL_SAYHEY_REY)
    assert "Olivia Rodrigo" not in stripped
    assert "40.1KFollowers" in stripped


def test_falls_back_to_followers_likes_pair():
    stats = extract_profile_stats("someone 8,061 Followers 23K Likes")
    assert stats.followers == 8061
    assert stats.likes == 23000
    assert stats.confidence == "pair"


def test_falls_back_to_lone_followers():
    stats = extract_profile_stats("creator page 12.5K Followers")
    assert stats.followers == 12500
    assert stats.confidence == "weak"


def test_skips_followers_inside_suggested_accounts_chrome():
    stats = extract_profile_stats("Suggested accounts for you 13.8M Followers")
    assert stats.followers is None
    assert stats.confidence == "none"


def test_rejects_implausible_follower_count():
    stats = extract_profile_stats("9 Following 900M Followers 10 Likes")
    assert stats.followers is None


def test_handles_missing_text():
    assert extract_profile_stats(None).confidence == "none"
    assert extract_profile_stats("").confidence == "none"
    assert extract_profile_stats("no stats on this page").followers is None


def test_likes_per_follower_ratio():
    assert likes_per_follower(9145, 2102) == 4.35
    assert likes_per_follower(None, 2102) is None
    assert likes_per_follower(9145, 0) is None


def test_engagement_bands():
    assert engagement_band(None) == "unknown"
    assert engagement_band(0.5) == "low"
    assert engagement_band(9.2) == "healthy"
    assert engagement_band(213.0) == "very_high"
