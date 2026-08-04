import json
from typing import Awaitable, Callable

from config import (
    AGENT_MODEL,
    MAX_SEARCH_ITERATIONS,
    PLATFORM_DOMAINS,
    RESULTS_PER_SEARCH,
    exa_client,
    openai_client,
)
from schemas import Candidate

EmitFn = Callable[[dict], Awaitable[None]]

TOOLS = [
    {
        "type": "function",
        "name": "search_creators",
        "description": (
            "Search the web, filtered to this platform's domain, for candidate "
            "creators matching a query. Returns raw results with page text "
            "excerpts you can read for follower counts, bio text, and "
            "engagement/growth signals."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query describing the niche/audience to look for.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "submit_candidates",
        "description": (
            "Finish this platform's research and submit the candidates found. "
            "Call this exactly once, when you have enough evidence. Only "
            "include candidates with real evidence from search_creators "
            "results — never invent stats. Omit a field rather than guessing."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "candidates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "handle": {"type": "string"},
                            "url": {"type": "string"},
                            "follower_count": {"type": ["integer", "null"]},
                            "bio_snippet": {"type": ["string", "null"]},
                            "growth_signal": {"type": ["string", "null"]},
                            "source_evidence": {
                                "type": "string",
                                "description": "Short quote from the search result text backing this candidate.",
                            },
                        },
                        "required": [
                            "handle",
                            "url",
                            "follower_count",
                            "bio_snippet",
                            "growth_signal",
                            "source_evidence",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["candidates"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def _build_system_prompt(platform: str) -> str:
    return f"""You are a creator-sourcing researcher focused only on {platform}. \
Use search_creators to find real candidates matching the brief below \
(you may call it up to {MAX_SEARCH_ITERATIONS} times to refine your query). \
When you have enough evidence, call submit_candidates. Ground every \
candidate in text you actually saw in search results — never fabricate \
follower counts or bios. If you can't verify a stat, leave it null."""


async def _do_search(platform: str, query: str, emit: EmitFn) -> list[dict]:
    await emit({"type": "agent_step", "agent": platform, "action": "searching", "query": query})

    results = await exa_client.search(
        query,
        include_domains=PLATFORM_DOMAINS[platform],
        num_results=RESULTS_PER_SEARCH,
        contents={"text": {"maxCharacters": 4000}},
    )

    raw_results = []
    for result in results.results:
        item = {
            "url": result.url,
            "title": result.title,
            "text": result.text,
            "published_date": result.published_date,
            "author": result.author,
        }
        raw_results.append(item)
        await emit(
            {
                "type": "agent_step",
                "agent": platform,
                "action": "found",
                "result": {"url": item["url"], "title": item["title"]},
            }
        )
    return raw_results


async def run_platform_agent(
    platform: str, structured_query_json: str, emit: EmitFn
) -> list[Candidate]:
    messages: list[dict] = [
        {"role": "system", "content": _build_system_prompt(platform)},
        {
            "role": "user",
            "content": f"Structured brief filters (JSON): {structured_query_json}",
        },
    ]

    try:
        for _ in range(MAX_SEARCH_ITERATIONS + 1):
            response = await openai_client.responses.create(
                model=AGENT_MODEL,
                input=messages,
                tools=TOOLS,
            )
            messages += response.output

            function_calls = [item for item in response.output if item.type == "function_call"]
            if not function_calls:
                break

            for call in function_calls:
                args = json.loads(call.arguments)

                if call.name == "search_creators":
                    raw_results = await _do_search(platform, args["query"], emit)
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(raw_results),
                        }
                    )
                elif call.name == "submit_candidates":
                    return [
                        Candidate(platform=platform, **c) for c in args["candidates"]
                    ]

        return []
    except Exception as exc:
        await emit({"type": "error", "agent": platform, "message": str(exc)})
        return []
