import asyncio

from agents.ranking import rank_candidates
from agents.reference_resolver import resolve_references
from agents.research_agent import run_platform_agent
from agents.structuring import structure_query
from cost import CostTracker
from enrichment import drop_excluded, enrich_all, select_shortlist
from run_cache import new_run_id, store_run
from schemas import Candidate
from rerank import rerank_by_similarity
from verification import verify_candidates

_QUEUE_DONE = object()


async def _drain(queue: asyncio.Queue):
    while True:
        event = await queue.get()
        if event is _QUEUE_DONE:
            return
        yield event


async def run_pipeline(prompt: str):
    tracker = CostTracker()
    run_id = new_run_id()
    yield {"type": "run_started", "run_id": run_id}

    try:
        structured_query = await structure_query(prompt, tracker)
    except Exception as exc:
        yield {"type": "error", "agent": "structuring", "message": str(exc)}
        yield {"type": "done", "run_id": run_id, "shortlist": [], "cached": [], "cost": tracker.summary()}
        return

    yield {"type": "structured_query", "data": structured_query.model_dump()}

    queue: asyncio.Queue = asyncio.Queue()

    async def emit(event: dict) -> None:
        await queue.put(event)

    seed_profile = None
    if structured_query.reference_accounts:

        async def run_resolver():
            result = await resolve_references(structured_query.reference_accounts, emit, tracker)
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
            run_platform_agent(
                platform, structured_query_json, seed_profile_json, emit, tracker
            )
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
    observations: dict = {}
    for finding in findings:
        observations.update(finding.observations)

    enriched = enrich_all(all_candidates, observations)

    verify_queue: asyncio.Queue = asyncio.Queue()

    async def verify_emit(event: dict) -> None:
        await verify_queue.put(event)

    async def run_verification():
        result = await verify_candidates(enriched, verify_emit)
        await verify_queue.put(_QUEUE_DONE)
        return result

    verify_task = asyncio.create_task(run_verification())
    async for event in _drain(verify_queue):
        yield event
    try:
        enriched = await verify_task
    except Exception as exc:
        yield {"type": "error", "agent": "verification", "message": str(exc)}

    keep = drop_excluded(enriched, structured_query)

    if seed_profile is not None:
        try:
            keep = await rerank_by_similarity(keep, seed_profile, tracker)
        except Exception as exc:
            yield {"type": "error", "agent": "rerank", "message": str(exc)}

    try:
        ranked_all = await rank_candidates(structured_query, keep, tracker)
    except Exception as exc:
        yield {"type": "error", "agent": "ranking", "message": str(exc)}
        ranked_all = []

    store_run(run_id, structured_query, ranked_all)

    verified_tier, cached_tier = select_shortlist(ranked_all, structured_query)

    yield {
        "type": "filtered",
        "data": {
            "seen": len(all_candidates),
            "ranked": len(ranked_all),
            "verified_shown": len(verified_tier),
            "cached_shown": len(cached_tier),
        },
    }

    verified_dicts = [c.model_dump() for c in verified_tier]
    cached_dicts = [c.model_dump() for c in cached_tier]

    yield {"type": "ranking_complete", "data": verified_dicts + cached_dicts}
    yield {
        "type": "done",
        "run_id": run_id,
        "shortlist": verified_dicts,
        "cached": cached_dicts,
        "considered": len(all_candidates),
        "cost": tracker.summary(),
    }
