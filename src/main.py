from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.refine import classify_refinement
from config import FRONTEND_ORIGIN
from cost import CostTracker
from enrichment import select_shortlist
from pipeline import run_pipeline
from run_cache import get_run
from schemas import RefilterRequest, RefineRequest, ResearchRequest
from sse import sse_event

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["content-type"],
)


@app.get("/health")
def healthroute():
    return {"status": "ok"}


@app.post("/api/research")
async def research(request: ResearchRequest):
    async def event_stream():
        async for event in run_pipeline(request.prompt):
            yield sse_event(event)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/refilter")
def refilter(request: RefilterRequest):
    entry = get_run(request.run_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Run not found or expired")

    updated_query = entry.structured_query.model_copy(
        update={
            k: v
            for k, v in {
                "follower_min": request.follower_min,
                "follower_max": request.follower_max,
                "max_results": request.max_results,
            }.items()
            if v is not None
        }
    )

    verified, cached = select_shortlist(entry.ranked_all, updated_query)
    return {
        "shortlist": [c.model_dump() for c in verified],
        "cached": [c.model_dump() for c in cached],
        "considered": len(entry.ranked_all),
    }


@app.post("/api/refine")
async def refine(request: RefineRequest):
    entry = get_run(request.run_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Run not found or expired")

    tracker = CostTracker()
    decision = await classify_refinement(entry.structured_query, request.text, tracker)
    return {**decision.model_dump(), "cost": tracker.summary()}
