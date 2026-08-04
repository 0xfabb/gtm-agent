from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pipeline import run_pipeline
from schemas import ResearchRequest
from sse import sse_event

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["POST"],
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
