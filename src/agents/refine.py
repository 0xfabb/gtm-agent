from config import STRUCTURING_MODEL, openai_client
from cost import CostTracker
from schemas import RefineDecision, StructuredQuery

SYSTEM_PROMPT = """You classify a follow-up request against an already-completed \
creator research run.

Decide between two kinds:

"filter" — the request only tightens or loosens numeric constraints already \
present on the run: follower range, or how many results to show. The platforms, \
niche, reference accounts and audience described in the original brief are \
unchanged. These can be served instantly from already-researched candidates, \
no new search needed.

"new_run" — anything else: a different platform, a different niche or topic, \
a new reference account, a different audience, or any other change that would \
require actually searching again.

If "filter": set follower_min/follower_max/max_results to the NEW absolute \
values implied (not deltas). Leave a field null if the request doesn't touch it.

If "new_run": write combined_prompt as a complete, standalone brief that a \
research system can run from scratch — merge whatever from the original brief \
still applies with the new request. Do not reference "the original" or "same as \
before"; make it self-contained.

Always include a one-sentence explanation of your classification."""


async def classify_refinement(
    original: StructuredQuery, text: str, tracker: CostTracker | None = None
) -> RefineDecision:
    response = await openai_client.responses.parse(
        model=STRUCTURING_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Original run's filters: {original.model_dump_json()}\n\n"
                    f"Follow-up request: {text}"
                ),
            },
        ],
        text_format=RefineDecision,
    )
    if tracker:
        tracker.record_response(STRUCTURING_MODEL, response)
    return response.output_parsed
