import asyncio

from agents.ranking import rank_candidates
from agents.reference_resolver import resolve_references
from agents.research_agent import run_platform_agent
from agents.structuring import structure_query
from enrichment import enrich_and_filter
from schemas import Candidate

_QUEUE_DONE = object()


async def _drain(queue: asyncio.Queue):
    while True:
        event = await queue.get()
        if event is _QUEUE_DONE:
            return
        yield event


async def run_pipeline(prompt: str):
    try:
        structured_query = await structure_query(prompt)
    except Exception as exc:
        yield {"type": "error", "agent": "structuring", "message": str(exc)}
        yield {"type": "done", "shortlist": []}
        return

    yield {"type": "structured_query", "data": structured_query.model_dump()}

    queue: asyncio.Queue = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    seed_profile = None
    if structured_query.reference_accounts:

        async def run_resolver():
            result = await resolve_references(structured_query.reference_accounts, emit)
            await queue.put(_QUEUE_DONE)
            return result

        resolver_task = asyncio.create_task(run_resolver())
        async for event in _drain(queue):
            yield event
        seed_profile = await resolver_task

        if seed_profile is not None:
            yield {"type": "seed_profile", "data": seed_profile.model_dump()}

    structured_query_json = structured_query.model_dump_json()
    seed_profile_json = seed_profile.model_dump_json() if seed_profile else None

    agent_tasks = [
        asyncio.create_task(
            run_platform_agent(platform, structured_query_json, seed_profile_json, emit)
        )
        for platform in structured_query.platforms
    ]

    async def run_all_agents():
        results = await asyncio.gather(*agent_tasks)
        await queue.put(_QUEUE_DONE)
        return results

    collector = asyncio.create_task(run_all_agents())

    async for event in _drain(queue):
        yield event

    findings = await collector
    all_candidates: list[Candidate] = [c for f in findings for c in f.candidates]
    page_texts: dict[str, str] = {}
    for finding in findings:
        page_texts.update(finding.page_texts)

    in_band, unverified = enrich_and_filter(
        all_candidates, structured_query, page_texts
    )

    yield {
        "type": "filtered",
        "data": {
            "seen": len(all_candidates),
            "in_band": len(in_band),
            "unverified": len(unverified),
        },
    }

    try:
        ranked = await rank_candidates(structured_query, in_band)
    except Exception as exc:
        yield {"type": "error", "agent": "ranking", "message": str(exc)}
        ranked = []

    ranked_dicts = [r.model_dump() for r in ranked]
    unverified_dicts = [c.model_dump() for c in unverified]

    yield {"type": "ranking_complete", "data": ranked_dicts}
    yield {
        "type": "done",
        "shortlist": ranked_dicts,
        "unverified": unverified_dicts,
        "considered": len(all_candidates),
    }
