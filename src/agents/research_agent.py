import json
from dataclasses import dataclass
from typing import Awaitable, Callable, Optional

from config import (
    AGENT_MODEL,
    MAX_SEARCH_ITERATIONS,
    PLATFORM_DOMAINS,
    PLATFORM_QUERY_FRAME,
    RESULTS_PER_SEARCH,
    exa_client,
    openai_client,
)
from schemas import Candidate
from urls import dedupe_key, is_profile_url, parse_profile_url

EmitFn = Callable[[dict], Awaitable[None]]


@dataclass
class PageObservation:
    url: str
    text: Optional[str]
    is_profile: bool


@dataclass
class PlatformFindings:
    candidates: list[Candidate]
    observations: dict[str, PageObservation]

SEARCH_TOOL = {
        "type": "function",
        "name": "search_creators",
        "description": (
            "Search this platform for creator profiles. Provide only a plain "
            "description of the kind of creator you want; the platform name and "
            "page framing are added automatically. Returns page text you can "
            "read for follower counts, bio text and engagement signals."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "description": {
                    "type": "string",
                    "description": (
                        "Description of the creator to find, e.g. 'finance creator "
                        "explaining options trading to beginners'. No search "
                        "operators, no platform name, no follower numbers."
                    ),
                }
            },
            "required": ["description"],
            "additionalProperties": False,
        },
        "strict": True,
}

SUBMIT_TOOL = {
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
}

TOOLS = [SEARCH_TOOL, SUBMIT_TOOL]


def _build_system_prompt(platform: str) -> str:
    return f"""You are a creator-sourcing researcher focused only on {platform}. \
Call search_creators with a plain description of the kind of creator to find \
(up to {MAX_SEARCH_ITERATIONS} times, varying the angle each time). Never use \
search operators such as site: — the platform is already constrained for you.

When you have enough evidence, call submit_candidates. Ground every candidate \
in text you actually saw in the results, and prefer candidates whose own \
profile page you saw. Never fabricate follower counts or bios; if a stat is \
not visible in the text, leave it null rather than estimating."""


def build_search_query(platform: str, description: str) -> str:
    frame = PLATFORM_QUERY_FRAME[platform]
    return f"{frame} {description.strip()}"


def _usable_results(results) -> list:
    usable = [r for r in results if parse_profile_url(r.url) is not None]
    usable.sort(key=lambda r: not is_profile_url(r.url))
    return usable


async def _do_search(
    platform: str,
    description: str,
    emit: EmitFn,
    observations: dict[str, PageObservation],
) -> list[dict]:
    query = build_search_query(platform, description)
    await emit({"type": "agent_step", "agent": platform, "action": "searching", "query": query})

    response = await exa_client.search(
        query,
        include_domains=PLATFORM_DOMAINS[platform],
        num_results=RESULTS_PER_SEARCH,
        contents={"text": {"maxCharacters": 4000}},
    )

    raw_results = []
    for result in _usable_results(response.results):
        ref = parse_profile_url(result.url)
        is_profile = is_profile_url(result.url)
        key = dedupe_key(platform, ref.handle)
        existing = observations.get(key)
        if existing is None or (is_profile and not existing.is_profile):
            observations[key] = PageObservation(
                url=result.url, text=result.text, is_profile=is_profile
            )

        item = {
            "url": result.url,
            "handle": ref.handle,
            "is_profile_page": is_profile,
            "title": result.title,
            "text": result.text,
        }
        raw_results.append(item)
        await emit(
            {
                "type": "agent_step",
                "agent": platform,
                "action": "found",
                "result": {"url": result.url, "title": result.title},
            }
        )
    return raw_results


def _build_task_message(
    structured_query_json: str, seed_profile_json: Optional[str]
) -> str:
    if seed_profile_json:
        return (
            f"Structured brief filters (JSON): {structured_query_json}\n\n"
            f"Seed profile describing the reference creators (JSON): {seed_profile_json}\n\n"
            "Search for creators matching the seed profile's search_descriptions. "
            "Do not return the reference accounts themselves."
        )
    return f"Structured brief filters (JSON): {structured_query_json}"


async def run_platform_agent(
    platform: str,
    structured_query_json: str,
    seed_profile_json: Optional[str],
    emit: EmitFn,
) -> PlatformFindings:
    messages: list[dict] = [
        {"role": "system", "content": _build_system_prompt(platform)},
        {
            "role": "user",
            "content": _build_task_message(structured_query_json, seed_profile_json),
        },
    ]
    observations: dict[str, PageObservation] = {}

    try:
        for iteration in range(MAX_SEARCH_ITERATIONS + 1):
            is_final = iteration == MAX_SEARCH_ITERATIONS
            if is_final:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Search budget exhausted. Call submit_candidates now "
                            "with the best candidates you have gathered so far."
                        ),
                    }
                )

            response = await openai_client.responses.create(
                model=AGENT_MODEL,
                input=messages,
                tools=[SUBMIT_TOOL] if is_final else TOOLS,
            )
            messages += response.output

            function_calls = [item for item in response.output if item.type == "function_call"]
            if not function_calls:
                break

            for call in function_calls:
                args = json.loads(call.arguments)

                if call.name == "search_creators":
                    raw_results = await _do_search(
                        platform, args["description"], emit, observations
                    )
                    messages.append(
                        {
                            "type": "function_call_output",
                            "call_id": call.call_id,
                            "output": json.dumps(raw_results),
                        }
                    )
                elif call.name == "submit_candidates":
                    return PlatformFindings(
                        candidates=[
                            Candidate(platform=platform, **c)
                            for c in args["candidates"]
                        ],
                        observations=observations,
                    )

        return PlatformFindings(candidates=[], observations=observations)
    except Exception as exc:
        await emit({"type": "error", "agent": platform, "message": str(exc)})
        return PlatformFindings(candidates=[], observations=observations)
