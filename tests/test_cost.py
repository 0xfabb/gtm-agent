import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from cost import CostTracker


def test_record_computes_usd_from_pricing_table():
    tracker = CostTracker()
    tracker.record("gpt-5.6-luna", input_tokens=1_000_000, output_tokens=1_000_000)
    assert tracker.total_usd == 1.40


def test_record_accumulates_across_calls():
    tracker = CostTracker()
    tracker.record("gpt-5.6-luna", 500_000, 0)
    tracker.record("gpt-5.6-luna", 500_000, 0)
    assert tracker.calls == 2
    assert tracker.input_tokens == 1_000_000
    assert round(tracker.total_usd, 4) == 0.20


def test_unknown_model_contributes_zero_cost_but_still_counts_tokens():
    tracker = CostTracker()
    tracker.record("some-future-model", 1000, 1000)
    assert tracker.total_usd == 0.0
    assert tracker.input_tokens == 1000


def test_record_response_reads_responses_api_usage_shape():
    tracker = CostTracker()
    response = SimpleNamespace(usage=SimpleNamespace(input_tokens=100, output_tokens=50))
    tracker.record_response("gpt-5.6-terra", response)
    assert tracker.input_tokens == 100
    assert tracker.output_tokens == 50


def test_record_response_reads_embeddings_usage_shape():
    tracker = CostTracker()
    response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=200))
    tracker.record_response("text-embedding-3-small", response)
    assert tracker.input_tokens == 200
    assert tracker.output_tokens == 0


def test_record_response_tolerates_missing_usage():
    tracker = CostTracker()
    tracker.record_response("gpt-5.6-luna", SimpleNamespace(usage=None))
    assert tracker.calls == 0


def test_summary_rounds_and_groups_by_model():
    tracker = CostTracker()
    tracker.record("gpt-5.6-luna", 1_000_000, 0)
    tracker.record("gpt-5.6-terra", 1_000_000, 0)
    summary = tracker.summary()
    assert summary["calls"] == 2
    assert summary["usd"] == round(0.20 + 2.00, 4)
    assert set(tracker.by_model.keys()) == {"gpt-5.6-luna", "gpt-5.6-terra"}
