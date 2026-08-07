import asyncio
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import rerank
from rerank import candidate_text, cosine_similarity, rerank_by_similarity, seed_text
from schemas import EnrichedCandidate, SeedProfile


def _profile(**overrides) -> SeedProfile:
    base = dict(
        summary="Quantitative trading educator",
        niche_keywords=["options", "volatility"],
        content_format="short-form explainers",
        audience="retail traders",
        search_descriptions=["creator explaining implied volatility"],
    )
    base.update(overrides)
    return SeedProfile(**base)


def _candidate(handle: str, bio: str = "") -> EnrichedCandidate:
    return EnrichedCandidate(
        handle=handle, platform="tiktok", url=f"https://x/{handle}", bio_snippet=bio
    )


def test_cosine_of_identical_vectors_is_one():
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0]) == pytest.approx(1.0)


def test_cosine_of_orthogonal_vectors_is_zero():
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0


def test_cosine_handles_degenerate_input():
    assert cosine_similarity([], [1.0]) == 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 1.0]) == 0.0
    assert cosine_similarity([1.0], [1.0, 2.0]) == 0.0


def test_seed_text_includes_every_signal():
    text = seed_text(_profile())
    assert "Quantitative trading educator" in text
    assert "options" in text
    assert "implied volatility" in text
    assert "retail traders" in text


def test_candidate_text_combines_handle_and_bio():
    text = candidate_text(_candidate("quantguy", "options and vol"))
    assert "quantguy" in text and "options and vol" in text


def test_reranks_candidates_by_similarity(monkeypatch):
    async def fake_embed(texts):
        vectors = {
            0: [1.0, 0.0],
            1: [0.0, 1.0],
            2: [0.9, 0.1],
        }
        return [vectors[i] for i in range(len(texts))]

    monkeypatch.setattr(rerank, "_embed", fake_embed)
    ordered = asyncio.run(
        rerank_by_similarity([_candidate("far"), _candidate("near")], _profile())
    )
    assert [c.handle for c in ordered] == ["near", "far"]
    assert ordered[0].similarity > ordered[1].similarity


def test_no_seed_profile_leaves_order_untouched():
    candidates = [_candidate("a"), _candidate("b")]
    assert asyncio.run(rerank_by_similarity(candidates, None)) == candidates


def test_single_candidate_skips_the_embedding_call():
    candidates = [_candidate("only")]
    assert asyncio.run(rerank_by_similarity(candidates, _profile())) == candidates
