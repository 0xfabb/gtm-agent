import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agents.structuring import apply_defaults, extract_reference_accounts
from config import DEFAULT_FOLLOWER_MIN, DEFAULT_MAX_RESULTS
from schemas import StructuredQuery

AARON_PROMPT = (
    "Find YouTube, TikTok, and Instagram creators similar to these two: "
    "https://www.tiktok.com/@valatility and https://www.tiktok.com/@deltatrendtrading "
    "(also on Instagram: instagram.com/deltatrendtrading). Match their content style "
    "and niche. Prioritize accounts under 100k followers."
)


def test_extracts_every_reference_from_real_prompt():
    refs = extract_reference_accounts(AARON_PROMPT)
    assert [(r.platform, r.handle) for r in refs] == [
        ("tiktok", "valatility"),
        ("tiktok", "deltatrendtrading"),
        ("instagram", "deltatrendtrading"),
    ]


def test_same_handle_on_two_platforms_is_kept_separate():
    refs = extract_reference_accounts(
        "tiktok.com/@deltatrendtrading and instagram.com/deltatrendtrading"
    )
    assert len(refs) == 2


def test_duplicate_reference_is_collapsed():
    refs = extract_reference_accounts(
        "https://www.tiktok.com/@valatility and tiktok.com/@valatility again"
    )
    assert len(refs) == 1


def test_no_references_in_plain_prompt():
    assert extract_reference_accounts("find finance tiktok creators") == []


def _query(**overrides) -> StructuredQuery:
    base = {"platforms": ["tiktok"], "niche_keywords": ["finance"]}
    base.update(overrides)
    return StructuredQuery(**base)


def test_applies_follower_floor_and_result_cap_when_unspecified():
    result = apply_defaults(_query())
    assert result.follower_min == DEFAULT_FOLLOWER_MIN
    assert result.max_results == DEFAULT_MAX_RESULTS


def test_does_not_override_explicit_values():
    result = apply_defaults(_query(follower_min=500, max_results=3))
    assert result.follower_min == 500
    assert result.max_results == 3


def test_backfills_platforms_when_model_returns_none():
    result = apply_defaults(_query(platforms=[]))
    assert set(result.platforms) == {"tiktok", "youtube", "instagram"}
