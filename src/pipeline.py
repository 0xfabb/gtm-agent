import asyncio

from agents.ranking import rank_candidates
from agents.research_agent import run_platform_agent
from agents.structuring import structure_query
from schemas import Candidate

_QUEUE_DONE = object()


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

    structured_query_json = structured_query.model_dump_json()
    agent_tasks = [
        asyncio.create_task(run_platform_agent(platform, structured_query_json, emit))
        for platform in structured_query.platforms
    ]

    async def run_all_agents() -> list[list[Candidate]]:
        results = await asyncio.gather(*agent_tasks)
        await queue.put(_QUEUE_DONE)
        return results

    collector = asyncio.create_task(run_all_agents())

    while True:
        event = await queue.get()
        if event is _QUEUE_DONE:
            break
        yield event

    all_candidates: list[Candidate] = [c for batch in await collector for c in batch]

    try:
        ranked = await rank_candidates(structured_query, all_candidates)
    except Exception as exc:
        yield {"type": "error", "agent": "ranking", "message": str(exc)}
        ranked = []

    ranked_dicts = [r.model_dump() for r in ranked]
    yield {"type": "ranking_complete", "data": ranked_dicts}
    yield {"type": "done", "shortlist": ranked_dicts}
