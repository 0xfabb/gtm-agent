import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agents.research_agent import SEARCH_TOOL, SUBMIT_TOOL, TOOLS, build_search_query


class _FakeResult:
    def __init__(self, url):
        self.url = url


def test_query_is_framed_for_each_platform():
    assert build_search_query("tiktok", "options educator").startswith(
        "TikTok profile page of a"
    )
    assert build_search_query("youtube", "options educator").startswith(
        "YouTube channel homepage of a"
    )
    assert build_search_query("instagram", "options educator").startswith(
        "Instagram profile page of a"
    )


def test_query_framing_trims_description():
    assert build_search_query("tiktok", "  x  ") == "TikTok profile page of a x"


def test_search_tool_takes_a_description_not_a_raw_query():
    assert "description" in SEARCH_TOOL["function"]["parameters"]["properties"]
    assert "query" not in SEARCH_TOOL["function"]["parameters"]["properties"]


def test_final_iteration_tool_set_cannot_search():
    assert SUBMIT_TOOL["function"]["name"] == "submit_candidates"
    assert [t["function"]["name"] for t in TOOLS] == ["search_creators", "submit_candidates"]


def test_usable_results_drops_pages_without_a_handle_and_prefers_profiles():
    from agents.research_agent import _usable_results

    results = [
        _FakeResult("https://www.tiktok.com/discover/finance-creators"),
        _FakeResult("https://www.tiktok.com/@someone/video/12345"),
        _FakeResult("https://www.tiktok.com/@profileguy"),
    ]
    usable = _usable_results(results)
    assert [r.url for r in usable] == [
        "https://www.tiktok.com/@profileguy",
        "https://www.tiktok.com/@someone/video/12345",
    ]
